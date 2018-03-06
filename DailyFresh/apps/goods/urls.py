# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.conf.urls import url
from goods.views import IndexView, ListView, DetailView

app_name = 'goods'
urlpatterns = [
    url(r'^index$', IndexView.as_view(), name='index'),
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)$', ListView.as_view(), name='list'),
    url(r'^detail/(?P<sku_id>\d+)$', DetailView.as_view(), name='detail')
]
