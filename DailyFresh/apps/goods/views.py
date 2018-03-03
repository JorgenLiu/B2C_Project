from django.shortcuts import render,redirect,reverse
from django.http import HttpResponse
from django.views import View
# Create your views here.
class IndexView(View):
    def get(self,request):
        return HttpResponse('index')

class DetailView(View):
    def get(self,request):
        pass

class ListView(View):
    def get(self,request):
        pass

