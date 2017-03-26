from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

class Queue(models.Model):
    name = models.CharField(max_length=50)
    workers = models.ManyToManyField(User, related_name='work_queues', blank=True)
    creators = models.ManyToManyField(User, related_name='create_queues', blank=True)
    everybody = models.BooleanField(default=False)
    mailbox = models.CharField(max_length=50, null=True, blank=True)

    def get_open_tickets(self):
        tickets = self.ticket_set.all().exclude(status='C')
        return tickets

    def __str__(self):
        return self.name

status_choices = (
        ('N', 'New'),
        ('O', 'Open'),
        ('A', 'Assigned'),
        ('C', 'Closed'),
)

class Ticket(models.Model):
    subject = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    time = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, related_name='created_tickets')
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, null=True)

    status = models.CharField(max_length=10, choices=status_choices, default='N')

    def __str__(self):
        return self.creator.username + ": " + self.subject


    def get_lbtype(self):
        if self.status == 'N':
            return 'success'
        else:
            if self.status == 'O':
                return 'info'
            else:
                if self.status == 'A':
                    return 'primary'
                else:
                    if self.status == 'C':
                        return 'default'

class Update(models.Model):
    time = models.DateTimeField(auto_now=True)
    comment = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=1, choices=status_choices, blank=True)
    ticket = models.ForeignKey(Ticket, related_name='updates', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True)

    class Meta:
        ordering = ['-time']

    def __str__(self):
        return self.user.username + " " + self.time.__str__()

    def get_lbtype(self):
        if self.status == 'N':
            return 'success'
        else:
            if self.status == 'O':
                return 'info'
            else:
                if self.status == 'A':
                    return 'primary'
                else:
                    if self.status == 'C':
                        return 'default'
