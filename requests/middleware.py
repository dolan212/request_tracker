from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import resolve
from django.urls import reverse
from os import path


class AuthRequiredMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_url = resolve(request.path_info).url_name
        if not request.user.is_authenticated():
            if current_url is not 'login':
                return redirect('requests:login')

        return self.get_response(request);