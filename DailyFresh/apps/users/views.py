from django.shortcuts import render
from django.shortcuts import redirect, reverse
from django.http.response import HttpResponse
from django.views import View
from utils.views import LoginMixin


class RegisterView(View):
    def get(self,request):
        return HttpResponse('register')