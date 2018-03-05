# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.conf.urls import url
app_name='carts'
from carts.views import CartInfoView, AddCartView, UpdateCartView, DeleteCartView
urlpatterns=[
    url('^$',CartInfoView.as_view(),name='info'),
    url('^add$',AddCartView.as_view(),name='add'),
    url('^update$',UpdateCartView.as_view(),name='update'),
    url('^delete$',DeleteCartView.as_view(),name='delete'),
]