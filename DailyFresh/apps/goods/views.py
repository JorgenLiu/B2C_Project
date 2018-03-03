from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.views import View
from goods.models import Goods, GoodsSKU, GoodsCategory, IndexCategoryGoodsBanner, \
    IndexPromotionBanner, IndexGoodsBanner


class IndexView(View):
    def get(self, request):
        categorys = GoodsCategory.objects.all()
        for category in categorys:
            category.title_banners = IndexCategoryGoodsBanner. \
                objects.filter(category=category, display_type=0)
            category.image_banners = IndexCategoryGoodsBanner. \
                objects.filter(category=category, display_type=1)
        promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
        goods_banners = IndexGoodsBanner.objects.all().order_by('index')
        contex={
            'categorys':categorys,
            'promotion_banners':promotion_banners,
            'goods_banners':goods_banners
        }
        return render(request,'index.html',contex)


class DetailView(View):
    def get(self, request):
        pass


class ListView(View):
    def get(self, request):
        pass
