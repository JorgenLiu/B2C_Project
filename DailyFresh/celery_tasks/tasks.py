# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.core.mail import send_mail
from django.conf import settings
from celery import Celery

app = Celery('celery_tasks.tasks',broker='redis://127.0.0.1:6379/4')

@app.task
def send_activation_email(toEmail,user_name,token):
    subject = '账号激活'
    body = ''
    sender = settings.EMAIL_FROM
    receiver = [toEmail]
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    send_mail(subject,body,sender,receiver,html_message=html_body)