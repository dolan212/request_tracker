from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

class Queue(models.Model):
    name = models.CharField(max_length=50)
    everybody = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Worker(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username + " works on " + self.queue.name

class Creator(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

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

class Update(models.Model):
    time = models.DateTimeField(auto_now=True)
    comment = models.CharField(max_length=500)
    status = models.CharField(max_length=1, choices=status_choices)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)