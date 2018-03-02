# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.conf.urls import url
from users.views import RegisterView, LoginView, ActivateView, AddressView,LogoutView,InfoView

app_name = 'users'
urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),
    url(r'^activate/(?P<token>.+)$', ActivateView.as_view(), name='active'),
    url(r'^info$', InfoView.as_view(), name='info'),
    url(r'^address$', AddressView.as_view(), name='address'),
]
