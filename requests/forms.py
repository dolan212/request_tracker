

from django.contrib.auth.models import User
from django import forms

from requests.models import Ticket, Update


class UserForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    username = forms.CharField(widget = forms.TextInput(attrs={'placeholder': 'Username'}))

    class Meta:
        fields = ['username', 'password']

class AddTicketForm(forms.ModelForm):
    subject = forms.CharField(widget = forms.TextInput(attrs={'placeholder': 'Subject'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Detailed description of problem'}))


    class Meta:
        model = Ticket
        fields = ['subject', 'description', 'queue']

    def __init__(self, *args, **kwargs):
        qset = kwargs.pop('qset')
        super(AddTicketForm, self).__init__(*args, **kwargs)
        self.fields['queue'].queryset = qset


class UpdateForm(forms.ModelForm):
    comment = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Comment', 'style': 'width: 100%; height: 100px;'}))

    class Meta:
        model = Update
        fields = ['comment', 'status']