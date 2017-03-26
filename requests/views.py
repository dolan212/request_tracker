from itertools import chain

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.views import View
from django.views import generic

from request_tracker import settings
from requests.forms import UserForm, AddTicketForm, UpdateForm
from requests.models import Queue, Ticket


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

class TicketView(generic.ListView):
    template_name = 'requests/tickets.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        users_tickets = self.request.user.created_tickets.all()
        return users_tickets

class WorkView(generic.ListView):
    template_name = 'requests/work.html'
    context_object_name = 'queues'

    def get_queryset(self):
        user = User.objects.get(pk=self.request.user.id)
        users_queues = user.work_queues.all()
        if user.is_staff: users_queues = Queue.objects.all()
        return users_queues


class AddView(generic.FormView):
    form_class = AddTicketForm
    template_name = 'requests/addticket.html'

    def get(self, request):
        everyone = Queue.objects.filter(everybody=True)
        user = self.request.user
        users_queues = user.create_queues.all() | everyone
        if user.is_staff: users_queues = Queue.objects.all()
        #result_list = queryset(everyone) + list(set(users_queues) - set(everyone))

        form = self.form_class(qset=users_queues)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        everyone = Queue.objects.filter(everybody=True)
        user = self.request.user
        users_queues = user.create_queues.all() | everyone
        if user.is_staff: users_queues = Queue.objects.all()
        #result_list = queryset(everyone) + list(set(users_queues) - set(everyone))

        form = self.form_class(qset=users_queues, data=request.POST)

        if(form.is_valid()):
            ticket = form.save(commit=False)
            ticket.creator = User.objects.get(pk=request.user.id)

            ticket.save()

            notify_workers(ticket)

            return redirect('requests:tickets')

        return render(request, self.template_name, {'form': form})


def notify_workers(ticket):
    worker_list = []
    for u in ticket.queue.workers.all():
        worker_list.append(u.email)

    send_mail('Ticket [' + str(ticket.id) + '] - ' + ticket.subject,
              'Problem description:\n' + ticket.description + "\nFrom queue: " + ticket.queue.__str__(),
              settings.EMAIL_HOST_USER,
              worker_list,
              fail_silently=False)

class TicketDetailView(generic.DetailView):
    model = Ticket
    form_class = UpdateForm
    template_name = 'requests/ticket_view.html'

    def get(self, request, pk):
        ticket = Ticket.objects.get(pk=pk)
        if(ticket.status == 'N'):
            ticket.status = 'O'
            ticket.save()

        form = self.form_class(None)

        return render(request, self.template_name, {'ticket': ticket, 'form' : form})

    def post(self, request, pk):
        ticket = Ticket.objects.get(pk=pk)
        user = request.user
        form = self.form_class(request.POST)

        if(form.is_valid()):
            update = form.save(commit=False)
            update.user = user;
            update.ticket = ticket;

            if not form.data['status']:
                update.status = ticket.status

            if update.status != ticket.status:
                ticket.status = update.status
                ticket.save()

            update.save()
            if ticket.creator.email:
                send_mail('Ticket [' + str(ticket.id) + '] - ' + ticket.subject,
                        update.user.username + ":\n" +update.comment,
                        settings.EMAIL_HOST_USER,
                        [ticket.creator.email],
                        fail_silently=False)

        return render(request, self.template_name, {'ticket': ticket, 'form': form})