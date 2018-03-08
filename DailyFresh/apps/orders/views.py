from django.shortcuts import render, redirect, reverse
from django.views import View
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage
from utils.views import LoginMixin, JsonLoginMixin, TransactionSupportedMixin
from goods.models import GoodsSKU
from users.models import Address
from orders.models import OrderGoods, OrderInfo
from django_redis import get_redis_connection
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.cache import cache
from alipay import AliPay


class OrderInfoView(LoginMixin, View):
    def get(self, request, page):
        user = request.user
        orders = user.orderinfo_set.all()
        pages = Paginator(orders, 2)
        for order in orders:
            order.status_name = OrderInfo.ORDER_STATUS[order.status]
            order.pay_method_name = OrderInfo.PAY_METHODS[order.pay_method]
            order.skus = []
            for order_goods in order.ordergoods_set.all():
                sku = order_goods.sku
                sku.count = order_goods.count
                sku.amount = sku.price * sku.count
                order.skus.append(sku)
        page = int(page)
        try:
            page_orders = pages.page(page)
        except EmptyPage:
            page_orders = pages.page(1)
            page = 1
        page_list = pages.page_range
        context = {
            "orders": page_orders,
            "page": page,
            "page_list": page_list,
        }
        return render(request, 'user_center_order.html', context)


class PlaceOrderView(LoginMixin, View):
    def post(self, request):
        sku_ids = request.POST.getlist('sku_ids')
        count = request.POST.get('count')
        if not sku_ids:
            return redirect(reverse('cart:info'))
        skus = []
        total_count = 0
        total_sku_amount = 0
        trans_cost = 10
        conn = get_redis_connection('default')
        if not count:
            cart_dict = conn.hgetall('cart_%s' % request.user.id)
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except:
                    return redirect(reverse('cart:info'))
                skus.append(sku)
                count = cart_dict.get(sku_id.encode())
                count = int(count)
                sku.count = count
                sku.amount = count * sku.price
                total_count += count
                total_sku_amount += count * sku.price
        else:
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except:
                    return redirect(reverse('goods:index'))
                try:
                    sku_count = int(count)
                except:
                    return redirect(reverse('goods:detail', args=sku_id))
                if sku_count > sku.stock:
                    return redirect(reverse('goods:detail', args=sku_id))
                conn.hset('cart_%s' % request.user.id, sku_id, sku_count)
                skus.append(sku)
                amount = sku.price * sku_count
                sku.count = sku_count
                sku.amount = amount
                total_sku_amount += amount
                total_count += sku_count
        total_amount = total_sku_amount + trans_cost
        try:
            address = Address.objects.filter(user=request.user).latest('create_time')
        except Address.DoesNotExist:
            address = None
        context = {
            'address': address,
            'skus': skus,
            'total_amount': total_amount,
            'total_count': total_count,
            'total_sku_amount': total_sku_amount,
            'trans_cost': trans_cost,
            'sku_ids': ','.join(sku_ids)
        }
        return render(request, 'place_order.html', context)


class CommitOrderView(JsonLoginMixin, TransactionSupportedMixin, View):
    def post(self, request):
        address_id = request.POST.get('address_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        sku_ids = sku_ids.split(',')
        if not all([address_id, pay_method, sku_ids]):
            return JsonResponse({'code': 2, 'message': '缺少参数'})
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code': 3, 'message': '地址不存在'})
        if int(pay_method) not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'code': 4, 'message': '支付方式错误'})
        conn = get_redis_connection('default')
        user = request.user
        cart_dict = conn.hgetall('cart_%s' % user.id)
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        total_amount = 10
        total_count = 10
        safe_point = transaction.savepoint()
        try:
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_amount=0,
                trans_cost=10,
                pay_method=pay_method
            )
            for sku_id in sku_ids:
                for i in range(3):
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(safe_point)
                        return JsonResponse({'code': 5, 'message': '商品不存在'})
                    count = int(cart_dict.get(sku_id.encode()))
                    if count > sku.stock:
                        transaction.savepoint_rollback(safe_point)
                        return JsonResponse({'code': 6, 'message': '库存不足'})
                    origin_stock = sku.stock
                    new_sales = sku.sales + count
                    new_stock = sku.stock - count
                    result = GoodsSKU.objects.filter(stock=origin_stock, id=sku_id).update(stock=new_stock,
                                                                                           sales=new_sales)
                    if result == 0 and i < 2:
                        continue
                    elif result == 0 and i == 2:
                        transaction.savepoint_rollback(safe_point)
                        return JsonResponse({'code': 8, 'message': '下单失败'})
                    sku.save()
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=count,
                        price=sku.price,
                    )
                    total_count += count
                    total_amount += count * sku.price
                    break
            order.total_count = total_count
            order.total_amount = total_amount
            order.save()
        except Exception:
            transaction.savepoint_rollback(safe_point)
            return JsonResponse({'code': 7, 'message': '下单失败'})
        transaction.savepoint_commit(safe_point)
        conn.hdel('cart_%s' % user.id, *sku_ids)
        return JsonResponse({'code': 0, 'message': '订单创建成功'})


class PaymentView(LoginMixin, View):
    """
    买家账号kblrqs5230@sandbox.com
    登录密码111111
    支付密码111111
    """

    def post(self, request):
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'code': 2, 'message': '订单id错误'})
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,
                user=request.user,
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
                pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY']
            )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code': 3, 'message': '订单错误'})
        payment_client = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            sign_type="RSA2",
            debug=True
        )
        order_url = payment_client.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject='头条生鲜',
            return_url=None,
            notify_url=None
        )
        url = settings.ALIPAY_URL + '?' + order_url
        return JsonResponse({'code': 0, 'message': '支付成功', 'url': url})


class CheckStatusView(LoginMixin, View):
    def get(self, request):
        order_id = request.GET.get('order_id')
        if not order_id:
            return JsonResponse(({'code': 2, 'message': '订单id错误'}))
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,
                user=request.user,
                status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"],
                pay_method=OrderInfo.PAY_METHODS_ENUM["ALIPAY"]
            )
        except OrderInfo.DoesNotExist:
            return JsonResponse(({'code': 3, 'message': '订单错误'}))
        check_client = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            sign_type="RSA2",
            debug=True
        )
        while True:
            response = check_client.api_alipay_trade_query(order_id)
            print(response)
            code = response.get('code')
            trade_status = response.get('trade_status')
            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                order.status = OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT']
                order.trade_id = response.get('trade_no')
                order.save()
                return JsonResponse({'code': 0, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and trade_status == 'WAIT_BUYER_PAY'):
                continue
            else:
                return JsonResponse({'code': 4, 'message': '支付失败'})


class CommentView(LoginMixin, View):
    def get(self, request, order_id):
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('orders:info'))
        order.status_name = OrderInfo.ORDER_STATUS[order.status]
        order.skus = []
        order_goods = order.ordergoods_set.all()
        for order_sku in order_goods:
            sku = order_sku.sku
            sku.count = order_sku.count
            sku.amount = order_sku.count * sku.price
            order.skus.append(sku)
        context = {
            'order': order
        }
        return render(request, 'order_comment.html', context)

    def post(self, request, order_id):
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=request.user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('orders:info'))
        order.status_name = OrderInfo.ORDER_STATUS[order.status]
        total_count = int(request.POST.get('total_count'))
        for i in range(1, total_count + 1):
            sku_id = request.POST.get('sku_%s' % i)
            content = request.POST.get('content_%s' % i)
            try:
                order_sku = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue
            order_sku.comment = content
            order_sku.save()
            cache.delete('details_%s' % sku_id)
        order.status = OrderInfo.ORDER_STATUS_ENUM['FINISHED']
        order.save()
        return redirect(reverse('orders:info', kwargs={'page': 1}))
