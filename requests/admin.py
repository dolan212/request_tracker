from django.contrib import admin
from .models import Queue, Ticket, Update

# Register your models here.

admin.site.register(Queue)
admin.site.register(Ticket)
admin.site.register(Update)
