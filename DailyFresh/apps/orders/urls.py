# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.conf.urls import url
from orders.views import PlaceOrderView
app_name='orders'
urlpatterns=[
    url(r'^place$', PlaceOrderView.as_view(), name='place'),
]