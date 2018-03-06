from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.views import View
from django.core.cache import cache
from django_redis import get_redis_connection
from django.core.paginator import Paginator, EmptyPage
from goods.models import Goods, GoodsSKU, GoodsCategory, IndexCategoryGoodsBanner, \
    IndexPromotionBanner, IndexGoodsBanner
import json


class BaseCartView(View):
    def get_cart_number(self, request):
        cart_num = 0
        if request.user.is_authenticated:
            conn = get_redis_connection('default')
            cart_dict = conn.hgetall('cart_%s' % request.user.id)
        else:
            cart_json=request.COOKIES.get('cart')
            if cart_json:
                cart_dict=json.loads(cart_json)
            else:
                cart_dict={}
        for number in cart_dict.values():
            cart_num += int(number)
        return cart_num


class IndexView(BaseCartView):
    def get(self, request):
        context = cache.get('index_context_data')
        if context is None:
            categorys = GoodsCategory.objects.all()
            for category in categorys:
                category.title_banners = IndexCategoryGoodsBanner. \
                    objects.filter(category=category, display_type=0)
                category.image_banners = IndexCategoryGoodsBanner. \
                    objects.filter(category=category, display_type=1)
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
            index_banners = IndexGoodsBanner.objects.all().order_by('index')
            context = {
                'categorys': categorys,
                'promotion_banners': promotion_banners,
                'index_banners': index_banners
            }
            cache.set('index_context_data', context, 3600)
        cart_num = self.get_cart_number(request)
        context.update(cart_num=cart_num)
        return render(request, 'index.html', context)


class DetailView(BaseCartView):
    def get(self, request, sku_id):
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))
        categorys = GoodsCategory.objects.all()
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[:2]
        sku_orders = sku.ordergoods_set.all().order_by('-create_time')[:30]
        if sku_orders:
            for order in sku_orders:
                order.ctime = order.create_time.strftime('%Y-%m-%d %H:%M:%S')
                order.user_name = order.order.user.username
        else:
            sku_orders = []
        other_skus = sku.goods.goodssku_set.exclude(id=sku_id)
        context = {
            'categorys': categorys,
            'sku': sku,
            'new_skus': new_skus,
            'sku_orders': sku_orders,
            'other_skus': other_skus
        }
        if request.user.is_authenticated:
            conn = get_redis_connection('default')
            conn.lrem('history_%s' % request.user.id, 0, sku_id)
            conn.lpush('history_%s' % request.user.id, sku_id)
            conn.ltrim('history_%s' % request.user.id, 0, 4)
        cart_num = self.get_cart_number(request)
        context.update(cart_num=cart_num)
        return render(request, 'detail.html', context)


class ListView(BaseCartView):
    def get(self, request, category_id, page_num):
        sort_methods={
            'default':'id',
            'hot':'-sales',
            'price':'price'
        }
        sort=request.GET.get('sort', 'default')
        if sort not in sort_methods.keys():
            sort='default'
        categorys=GoodsCategory.objects.all()
        try:
            category=GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return redirect(reverse('goods:index'))
        new_skus=GoodsSKU.objects.filter(category=category)[:2]
        skus=GoodsSKU.objects.filter(category=category).order_by(sort_methods[sort])
        page_num=int(page_num)
        paginator=Paginator(skus,2)
        try:
            page=paginator.page(page_num)
        except EmptyPage:
            page=paginator.page(0)
        page_list=paginator.page_range
        cart_num=self.get_cart_number(request)
        context={
            'sort': sort,
            'category': category,
            'cart_num': cart_num,
            'categorys': categorys,
            'new_skus': new_skus,
            'page_skus': page,
            'page_list': page_list
        }
        return render(request,'list.html',context)