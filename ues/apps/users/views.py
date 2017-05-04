#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, json, datetime
from django.contrib import auth
from django.views.generic import View
from django.contrib.auth import authenticate
from django.shortcuts import render, HttpResponse, redirect

from users.models import User
from users.forms import ChangeUserInfoForm
from django.core.urlresolvers import reverse
from users.forms import LoginForm, RegisterForm

# Create your views here.

class Profile(View):
    def get(self, request):
        request.user.get_user_rating_json_by_repo()
        return render(request, 'users/profile.html')

    def post(self, request):
        user_info_form = ChangeUserInfoForm(request.POST)
        user = request.user
        if user_info_form.is_valid():
            cd = user_info_form.cleaned_data
            username = cd['username']
            if username != user.username:
                return render(request, 'users/profile.html')
            user.nickname = cd['nickname']
            user.email = cd['email']
            user.school = cd['school']
            user.description = cd['description']
            user.save()
            new_password = cd['new_password']
            if new_password:
                user.set_password(new_password)
                user.save()
                auth.logout(request)
            return redirect(reverse('users_profile'))
        else:
            return render(request, 'users/profile.html', {
                'form': user_info_form
            })

def logout(request):
    auth.logout(request)
    return redirect(reverse('users_login'))

class Login(View):
    def get(self, request):
        login_form = LoginForm(initial={
            'username': '',
            'password': '',
            'redirect_to': reverse('users_profile')
        })
        return render(request, 'users/login.html',{
            'login_form': login_form
        })

    def post(self, request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            cd = login_form.cleaned_data
            user = authenticate(username=cd['username'], password=cd['password'])
            auth.login(request, user)
            redirect_to = cd['redirect_to']
            return redirect(redirect_to)
        else:
            return render(request, 'users/login.html', {
                    'login_form': login_form,
                },
            )

class Register(View):
    def get(self, request):
        redirect_to = request.META.get('HTTP_REFERER', reverse('users_profile'))
        register_form = RegisterForm(initial={
            'username': '',
            'email': '',
            'password': '',
            'password_rep': '',
            'redirect_to': redirect_to
        })
        return render(request, 'users/register.html', {
            'register_form': register_form
        })

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            cd = register_form.cleaned_data
            User.create_user(username=cd['username'], email=cd['email'],
                password=cd['password'])
            user = authenticate(username=cd['username'], password=cd['password'])
            auth.login(request, user)
            redirect_to = cd['redirect_to']
            if re.match(r'.*/register/$', redirect_to):
                redirect_to = reverse('users_profile')
            return redirect(redirect_to)
        else:
            return render(request, 'users/register.html', {
                    'register_form': register_form,
            })

        return render(request, 'users/profile.html')


class DateTimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def get_user_ac_list_json(request):
    user = request.user
    ac_list = user.get_ac_list_json()
    return HttpResponse(json.dumps(ac_list, ensure_ascii=False, cls=DateTimeEncoder))

def get_user_rating_json(request):
    user = request.user
    user_rating = user.get_user_rating_json_by_repo()
    return HttpResponse(json.dumps(user_rating, ensure_ascii=False))

def get_all_user_name(request):
    user_names = User.get_all_username()
    result = {'data': list(user_names)}
    return HttpResponse(json.dumps(result, ensure_ascii=False))
