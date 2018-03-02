# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.conf.urls import url
from users.views import RegisterView, LoginView

app_name = 'users'
urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^login$', LoginView.as_view(), name='login'),
]
