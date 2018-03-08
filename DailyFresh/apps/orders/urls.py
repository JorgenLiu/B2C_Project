# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.conf.urls import url
from orders.views import PlaceOrderView, CommitOrderView, OrderInfoView, PaymentView, CheckStatusView, CommentView

app_name = 'orders'
urlpatterns = [
    url(r'^(?P<page>\d+)$', OrderInfoView.as_view(), name='info'),
    url(r'^place$', PlaceOrderView.as_view(), name='place'),
    url(r'^commit$', CommitOrderView.as_view(), name='commit'),
    url(r'^pay$', PaymentView.as_view(), name='pay'),
    url(r'^checkpay$', CheckStatusView.as_view(), name='checkpay'),
    url(r'^comment/(?P<order_id>\d+)$', CommentView.as_view(), name='comment')
]
