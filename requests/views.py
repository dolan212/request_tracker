from itertools import chain

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views import View
from django.views import generic

from requests.forms import UserForm, AddTicketForm
from requests.models import Queue


class IndexView(generic.ListView):
    template_name = 'requests/index.html'
    context_object_name = 'all_queues'

    def get_queryset(self):
        #everyone = Queue.objects.filter(everybody=True)
        user = User.objects.get(pk=self.request.user.id)
        users_queues = user.work_queues.all();
        if user.is_staff: users_queues = Queue.objects.all()
        #result_list = list(everyone) + list(set(users_queues) - set(everyone))
        return users_queues

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
                else: return render(request, self.template_name, {'form': form, 'error': 'Your account has been disabled'})

            else: return render(request, self.template_name, {'form': form, 'error': 'Invalid username or password'})
        else: return render(request, self.template_name, {'form': form})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('requests:login')

class TicketView(generic.TemplateView):
    template_name = 'requests/tickets.html'

class WorkView(generic.ListView):
    template_name = 'requests/work.html'
    context_object_name = 'queues';

    def get_queryset(self):
        user = User.objects.get(pk=self.request.user.id)
        users_queues = user.work_queues.all();
        if user.is_staff: users_queues = Queue.objects.all()
        return users_queues;


class AddView(generic.FormView):
    form_class = AddTicketForm
    template_name = 'requests/addticket.html'

    def get(self, request):
        everyone = Queue.objects.filter(everybody=True)
        user = User.objects.get(pk=self.request.user.id)
        users_queues = user.create_queues.all();
        #if user.is_staff: users_queues = Queue.objects.all()
        #result_list = queryset(everyone) + list(set(users_queues) - set(everyone))

        form = self.form_class(qset=users_queues)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        everyone = Queue.objects.filter(everybody=True)
        user = User.objects.get(pk=self.request.user.id)
        users_queues = user.create_queues.all();
        #if user.is_staff: users_queues = Queue.objects.all()
        #result_list = queryset(everyone) + list(set(users_queues) - set(everyone))

        form = self.form_class(qset=users_queues, data=request.POST)


