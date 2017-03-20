from django.contrib.auth.models import User
from django import forms


class UserForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    username = forms.CharField(widget = forms.TextInput(attrs={'placeholder': 'Username'}))

    class Meta:
        fields = ['username', 'password']