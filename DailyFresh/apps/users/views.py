from django.shortcuts import redirect, reverse, render
from django.http.response import HttpResponse
from django.views import View
from django import db
from django.contrib.auth import logout, login, authenticate
from django.conf import settings
from utils.views import LoginMixin
from users.models import User, Address
from goods.models import GoodsSKU
from celery_tasks.tasks import send_activation_email
import re, json
from django_redis import get_redis_connection
from itsdangerous import JSONWebSignatureSerializer as Serializer


class RegisterView(View):
    def post(self, request):
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        if not all([username, pwd, email, allow]):
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
        user.is_active = False
        user.save()
        token = user.generate_active_token()
        send_activation_email.delay(user.email, username, token)
        return redirect(reverse('users:login'))

    def get(self, request):
        return render(request, 'register.html')


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        user_name = request.POST.get('username')
        pwd = request.POST.get('pwd')
        user = authenticate(username=user_name, password=pwd)
        if user is None:
            return redirect(reverse('users:register'))
        if not user.is_active:
            return redirect(reverse('users:register'))
        login(request, user)
        if not request.POST.get('remembered'):
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)
        cart_json = request.COOKIES.get('cart')
        if cart_json:
            cart_dict = json.loads(cart_json)
        else:
            cart_dict={}
        conn=get_redis_connection('default')
        cart_dict_redis=conn.hgetall('cart_%s'%user.id)
        for sku_id, count in cart_dict.items():
            sku_id=sku_id.encode()
            if sku_id in cart_dict_redis.keys():
                origin_count=int(cart_dict_redis[sku_id])
                count+=origin_count
            cart_dict_redis[sku_id]=count
        if cart_dict_redis:
            conn.hmset('cart_%s'%user.id, cart_dict_redis)
        next = request.GET.get('next')
        if not next:
            response = redirect('goods:index')
        elif next == '/orders/place':
            response = redirect(reverse('cart:info'))
        else:
            response = redirect(next)
        return response


class LogoutView(LoginMixin, View):
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


class ActivateView(View):
    def get(self, request, token):
        return redirect(reverse('users:login'))


class AddressView(LoginMixin, View):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect('users:login')
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None
        context = {
            'address': address
        }
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        user = request.user
        recv_name = request.POST.get("recv_name")
        addr = request.POST.get("addr")
        zip_code = request.POST.get("zip_code")
        recv_mobile = request.POST.get("recv_mobile")
        if all([recv_name, recv_mobile, addr, zip_code]):
            address = Address.objects.create(
                user=user,
                receiver_name=recv_name,
                detail_addr=addr,
                zip_code=zip_code,
                receiver_mobile=recv_mobile
            )
        return redirect(reverse('users:address'))


class InfoView(LoginMixin, View):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect(reverse('users:login'))
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None
        conn = get_redis_connection('default')
        sku_ids = conn.lrange('history_%s' % user.id, 0, 4)
        sku_list = [GoodsSKU.objects.get(id=sku_id) for sku_id in sku_ids]
        context = {
            'address': address,
            'sku_list': sku_list,
        }
        return render(request, 'user_center_info.html', context)
