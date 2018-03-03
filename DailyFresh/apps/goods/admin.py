from django.contrib import admin
from goods.models import GoodsSKU,GoodsCategory,Goods
# Register your models here.
admin.site.register(GoodsCategory)
admin.site.register(GoodsSKU)
admin.site.register(Goods)