# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.conf.urls import url
from goods.views import IndexView
app_name='goods'
urlpatterns=[
    url(r'^$',IndexView.as_view(),name='index')
]