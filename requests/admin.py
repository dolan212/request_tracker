from django.contrib import admin
from .models import Queue, Worker, Creator, Ticket, Update

# Register your models here.

admin.site.register(Queue)
admin.site.register(Worker)
admin.site.register(Creator)
admin.site.register(Ticket)
admin.site.register(Update)
