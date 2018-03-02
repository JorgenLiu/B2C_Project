# -*- coding: utf-8 -*-
_Author_ = 'G.Liu'
from django.contrib.auth.decorators import login_required

class LoginMixin(object):
    @classmethod
    def as_view(cls,**initargs):
        view=super().as_view(**initargs)
        return login_required(view)