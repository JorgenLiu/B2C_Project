from django.contrib import admin
from django.core.cache import caches
from goods.models import GoodsSKU, GoodsCategory, Goods, IndexCategoryGoodsBanner, IndexPromotionBanner
from celery_tasks.tasks import generate_static_index


# Register your models here.
class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_index.delay()
        caches.delete('index_context_data')

    def delete_model(self, request, obj):
        obj.delete()
        generate_static_index.delay()
        caches.delete('index_context_data')

class IndexPromotionBannerAdmin(BaseAdmin):
    pass

class GoodsCategoryAdmin(BaseAdmin):
    pass

class GoodsAdmin(BaseAdmin):
    pass

class GoodsSKUAdmin(BaseAdmin):
    pass

class IndexCategoryGoodsBannerAdmin(BaseAdmin):
    pass


admin.site.register(GoodsCategory,GoodsCategoryAdmin)
admin.site.register(Goods,GoodsAdmin)
admin.site.register(GoodsSKU,GoodsSKUAdmin)
admin.site.register(IndexPromotionBanner,IndexPromotionBannerAdmin)
admin.site.register(IndexCategoryGoodsBanner,IndexCategoryGoodsBannerAdmin)
