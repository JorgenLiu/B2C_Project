# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
import functools
class LoginMixin(object):
    @classmethod
    def as_view(cls,**initargs):
        view=super().as_view(**initargs)
        return login_required(view)


def json_login_required(view_func):
    @functools.wraps(view_func)
    def wrapped_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'code': 1, 'message': '用户未登录'})
        else:
            return view_func(request, *args, **kwargs)

    return wrapped_func


class JsonLoginMixin(object):
    @classmethod
    def as_view(cls, **initargs):
        view = super().as_view(**initargs)
        return json_login_required(view)


class TransactionSupportedMixin(object):
    @classmethod
    def as_view(cls, **initargs):
        view = super(TransactionSupportedMixin, cls).as_view(**initargs)
        return transaction.atomic(view)
