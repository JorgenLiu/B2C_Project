from django.shortcuts import render, redirect
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from django.views import View
from django.http import JsonResponse
import json


# Create your views here.
class CartInfoView(View):
    def get(self, request):
        cart_info = dict()
        total_count = 0
        total_amount = 0
        if not request.user.is_authenticated:
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
        else:
            conn = get_redis_connection('default')
            cart_dict = conn.hgetall('cart_%s' % request.user.id)
        skus = []
        for sku_id, count in cart_dict.items():
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except:
                continue
            count = int(count)
            sku.amount = count * sku.price
            total_count += count
            total_amount += sku.amount
            sku.count = count
            skus.append(sku)
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount
        }
        return render(request, 'cart.html', context)


class AddCartView(View):
    def post(self, request):
        count = request.POST.get('count')
        sku_id = request.POST.get('sku_id')
        if not all([count, sku_id]):
            return JsonResponse({"code": 2, "message": "参数不完整"})
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({"code": 3, "message": "商品不存在"})
        try:
            count = int(count)
        except Exception:
            return JsonResponse({"code": 4, "message": "参数错误"})

        if not request.user.is_authenticated:
            cart_json = request.COOKIES.get('cart')
            if not cart_json:
                cart_dict = {}
            else:
                cart_dict = json.loads(cart_json)
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return JsonResponse({'code': 3, 'message': '商品不存在'})
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]
                count += origin_count
            if count > sku.stock:
                return JsonResponse({'code': 6, 'message': '库存不足'})
            cart_dict[sku_id] = count
            cart_num = sum([num for num in cart_dict.values()])
            cart_str = json.dumps(cart_dict)
            response = JsonResponse({"code": 0, "message": "添加购物车成功", 'cart_num': cart_num})
            response.set_cookie('cart', cart_str)
            return response
        else:
            conn = get_redis_connection('default')
            origin_count = conn.hget('cart_%s' % request.user.id, sku_id)
            if origin_count is not None:
                count += int(origin_count)
            if count > sku.stock:
                return JsonResponse({'code': 6, 'message': '库存不足'})
            conn.hset('cart_%s' % request.user.id, sku_id, count)
            cart_dict = conn.hgetall('cart_%s' % request.user.id)
            cart_num = sum([int(num) for num in cart_dict.values()])
            return JsonResponse({"code": 0, "message": "添加购物车成功", 'cart_num': cart_num})


class UpdateCartView(View):
    def post(self, request):
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        if not all([sku_id, count]):
            return JsonResponse({'code': 1, 'message': '参数不完整'})
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 2, 'message': '商品不存在'})
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 3, 'message': '数量有误'})
        if count > sku.stock:
            return JsonResponse({'code': 4, 'message': '库存不足'})
        if request.user.is_authenticated:
            conn = get_redis_connection('default')
            conn.hset('cart_%s' % request.user.id, sku_id, count)
            return JsonResponse({'code': 0, 'message': '添加购物车成功'})
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
            cart_dict[sku_id] = count
            cart_json = json.dumps(cart_dict)
            response = JsonResponse({'code': 0, 'message': '添加购物车成功'})
            response.set_cookie('cart', cart_json)
            return response


class DeleteCartView(View):
    def post(self, request):
        sku_id = request.POST.get('sku_id')
        if not sku_id:
            return JsonResponse({'code': 1, 'message': '参数不完整'})
        if request.user.is_authenticated:
            conn = get_redis_connection('default')
            conn.hdel('cart_%s' % request.user.id, sku_id)
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
                if sku_id in cart_dict.keys():
                    del cart_dict[sku_id]
                response = JsonResponse({'code': 0, 'message': '删除成功'})
                cart_json = json.dumps(cart_dict)
                response.set_cookie('cart', cart_json)
                return response
        return JsonResponse({'code': 0, 'message': '删除成功'})
