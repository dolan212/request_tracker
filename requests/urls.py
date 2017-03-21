from django.conf.urls import url
from . import views

app_name = 'requests'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),

    #user's created tickets
    url(r'^tickets/$', views.TicketView.as_view(), name='tickets'),

    #user's tickets to be worked on
    url(r'^work/$', views.WorkView.as_view(), name='work'),

    #create a ticket
    url(r'^addticket/$', views.AddView.as_view(), name='addticket')

]