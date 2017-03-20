from django.shortcuts import render
from django.views import generic


class IndexView(generic.TemplateView):
    template_name = 'requests/index.html'

class LoginView(generic.View):
    template_name = 'requests/login.html'