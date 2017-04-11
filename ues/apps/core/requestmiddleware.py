#!/usr/bin/env python
# -*- coding: utf-8 -*-

from users.forms import LoginForm
from django.shortcuts import render
from django.shortcuts import redirect
from django.core.urlresolvers import reverse


class MyMiddleware(object):
    def process_request(self, request):
        if not hasattr(request, 'user'):
            return
        if not hasattr(request, 'path'):
            return
        user = request.user
        path = request.path
        if path in [reverse('users_login'), reverse('users_register')]:
            if user.is_authenticated():
                return redirect(reverse('users_profile'))
        elif not user.is_authenticated():
            login_form = LoginForm(initial={
                'username': '',
                'password': '',
                'redirect_to': path
            })
            return render(request, 'users/login.html', {
                'login_form': login_form
            })
