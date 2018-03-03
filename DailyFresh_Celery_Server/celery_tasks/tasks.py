# -*- coding: utf-8 -*-
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "DailyFresh.settings"
import django
django.setup()
_Author_ = 'G.Liu'
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader
from celery import Celery
from goods.models import GoodsCategory, IndexPromotionBanner, IndexGoodsBanner, IndexCategoryGoodsBanner
import os

app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/4')


@app.task
def send_activation_email(toEmail, user_name, token):
    subject = '账号激活'
    body = ''
    sender = settings.EMAIL_FROM
    receiver = [toEmail]
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    send_mail(subject, body, sender, receiver, html_message=html_body)


@app.task
def generate_static_index():
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
    template = loader.get_template('static_index.html')
    html_data = template.render(context)
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'new_index.html')
    print(file_path)
    with open(file_path, 'w', encoding='utf-8')as f:
        f.write(html_data)




