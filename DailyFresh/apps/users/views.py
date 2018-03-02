from django.shortcuts import redirect, reverse, render
from django.http.response import HttpResponse
from django.views import View
from django import db
from django.contrib.auth import logout,login, authenticate
from django.conf import settings
from utils.views import LoginMixin
from users.models import User
from celery_tasks.tasks import send_activation_email
import re
from itsdangerous import JSONWebSignatureSerializer as Serializer

class RegisterView(View):
    def post(self,request):
        username=request.POST.get('user_name')
        pwd=request.POST.get('pwd')
        email=request.POST.get('email')
        allow=request.POST.get('allow')
        if not all([username,pwd,email,allow]):
            return redirect(reverse('users:register'))
        if not re.match(r"^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$", email):
            print('email format wrong')
            return redirect(reverse('users:register'))
        if allow != 'on':
            print('must allow contract')
            return redirect(reverse('users:register'))
        try:
            user = User.objects.create_user(username, email, pwd)
        except db.IntegrityError:
            return redirect(reverse('users:register'))
        user.is_active=False
        user.save()
        token = user.generate_active_token()
        send_activation_email.delay(user.email,username,token)
        return HttpResponse('register')

    def get(self,request):
        return render(request,'register.html')

class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')
    def post(self,request):
        user_name=request.POST.get('user_name')
        pwd=request.POST.get('pwd')
        user=authenticate(username=user_name, password=pwd)
        if user is None:
            return redirect(reverse('users:login'))
        if not user.is_active:
            return redirect(reverse('users:register'))
        login(request,user)
        if not request.POST.get('remembered'):
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)
        return redirect('goods:index')


class ActivateView(View):
    def get(self,request,token):
        return redirect(reverse('users:login'))

class AddressView(LoginMixin,View):
    def get(self,request):
        pass
    def post(self,request):
        pass