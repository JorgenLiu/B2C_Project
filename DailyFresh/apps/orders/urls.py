# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.conf.urls import url
from orders.views import PlaceOrderView, CommitOrderView, OrderInfoView
app_name='orders'
urlpatterns=[
    url(r'^info/(?P<page>\d+)$', OrderInfoView.as_view(), name='info'),
    url(r'^place$', PlaceOrderView.as_view(), name='place'),
    url(r'^commit$', CommitOrderView.as_view(), name='commit')
]