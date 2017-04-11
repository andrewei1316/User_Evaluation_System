#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import hashlib
from django import forms
from django.forms.widgets import *
from django.core import validators
from django.contrib.auth import authenticate

from users.models import User


class LoginForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, widget=PasswordInput)
    redirect_to = forms.CharField(required=False, initial='/', widget=HiddenInput)

    def clean_username(self):
        print "clean_username"
        username = self.cleaned_data['username']
        if not User.objects.filter(username__exact=username).exists():
            raise forms.ValidationError('该用户名不存在')
        return username

    def clean_password(self):

        if 'username' in self._errors:
            return ''
        cd = self.cleaned_data
        user = authenticate(username=cd['username'], password=cd['password'])
        if user is None:
            user = User.objects.get(username__exact=cd['username'])
            if not user.is_active and user.password == hashlib.sha1(
                    cd['password']).hexdigest().upper():
                user.set_password(cd['password'])
                user.is_active = True
                user.save()
            else:
                raise forms.ValidationError('密码不正确')
        elif not user.is_active:
            raise forms.ValidationError('用户已禁用')
        return cd['password']


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=30, required=True, initial='',
        validators=[
            validators.RegexValidator(
                re.compile('^[\w.@+-]+$'), '请输入有效的用户名', 'invalid')
    ])
    email = forms.EmailField(required=True, initial='')
    password = forms.CharField(required=True, widget=PasswordInput)
    password_rep = forms.CharField(required=True, widget=PasswordInput)
    redirect_to = forms.CharField(required=False, initial='/', widget=HiddenInput)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__exact=username).exists():
            raise forms.ValidationError('该用户名已经被占用')
        return username

    def clean_password_rep(self):
        cd = self.cleaned_data
        if cd['password_rep'] != '' and cd['password'] != cd['password_rep']:
            raise forms.ValidationError("两次密码输入不一致")
        return cd['password_rep']


class ChangeUserInfoForm(forms.Form):
    username = forms.CharField(required=True)
    nickname = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    school = forms.CharField(required=False)
    description = forms.CharField(required=False)
    old_password = forms.CharField(required=False, widget=PasswordInput)
    new_password = forms.CharField(required=False, widget=PasswordInput)
    new_password_rep = forms.CharField(required=False, widget=PasswordInput)

    def celan_username(self):
        username = self.cleaned_data['username']
        if not User.objects.filter(username__exact=username).exists():
            raise forms.ValidationError('该用户不存在')
        return username

    def clean_old_password(self):
        cd = self.cleaned_data
        old_password = cd.get('old_password')
        if old_password:
            user = authenticate(username=cd['username'],
                            password=cd['old_password'])
            if user is None:
                raise forms.ValidationError('密码不正确')
        return old_password

    def clean_new_password(self):
        cd = self.cleaned_data
        old_password = cd.get('old_password')
        new_password = cd.get('new_password')
        if new_password:
            if not old_password:
                raise forms.ValidationError("请验证原密码")
        return new_password

    def clean_new_password_rep(self):
        cd = self.cleaned_data
        old_password = cd.get('old_password')
        new_password = cd.get('new_password')
        new_password_rep = cd.get('new_password_rep')
        if new_password_rep:
            if not old_password:
                raise forms.ValidationError("请验证原密码")
        if new_password != new_password_rep:
            raise forms.ValidationError("两次密码输入不一致")
        return new_password_rep

