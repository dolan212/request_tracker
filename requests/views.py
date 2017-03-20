from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View
from django.views import generic

from requests.forms import UserForm


class IndexView(generic.TemplateView):
    template_name = 'requests/index.html'

class LoginView(View):
    form_class = UserForm
    template_name = 'requests/login.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        print form.is_valid()
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('requests:index')

            else: return render(request, self.template_name, {'form': form, 'error': 'Invalid username or password'})
        else: return render(request, self.template_name, {'form': form})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('requests:login')
