from django.shortcuts import render, redirect, reverse
from django.views import View
from django.http import JsonResponse
from utils.views import LoginMixin, JsonLoginMixin, TransactionSupportedMixin
from goods.models import GoodsSKU
from users.models import Address
from orders.models import OrderGoods, OrderInfo
from django_redis import get_redis_connection
from django.utils import timezone
from django.db import transaction


class OrderInfoView(LoginMixin, View):
    def get(self, request, page):
        pass


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
