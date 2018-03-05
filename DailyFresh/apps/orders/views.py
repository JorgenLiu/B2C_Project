from django.shortcuts import render, redirect, reverse
from django.views import View
from django.http import JsonResponse
from utils.views import LoginMixin, JsonLoginMixin
from goods.models import GoodsSKU
from users.models import Address
from django_redis import get_redis_connection


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
        total_amount = 0
        if not count:
            conn = get_redis_connection('default')
            cart_dict = conn.hgetall('cart_%s' % request.user.id)
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except:
                    return redirect(reverse('cart:info'))
                skus.append(sku)
                count = int(cart_dict[sku_id.encode()])
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
            'trans_cost': trans_cost
        }
        return render(request, 'place_order.html', context)


class CommitOrderView(JsonLoginMixin, View):
    def post(self, request):
        pass
