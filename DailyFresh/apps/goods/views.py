from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.views import View
from django.core.cache import cache
from django_redis import get_redis_connection
from goods.models import Goods, GoodsSKU, GoodsCategory, IndexCategoryGoodsBanner, \
    IndexPromotionBanner, IndexGoodsBanner


class IndexView(View):
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
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')
            context = {
                'categorys': categorys,
                'promotion_banners': promotion_banners,
                'goods_banners': goods_banners
            }
            cache.set('index_context_data', context, 3600)
        cart_num = 0
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_dict = conn.hgetall('cart_%s' % user.id)
            for number in cart_dict.values():
                cart_num += int(number)
        context.update(cart_num=cart_num)
        return render(request, 'index.html', context)


class DetailView(View):
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
        return render(request, 'detail.html', context)


class ListView(View):
    def get(self, request):
        pass
