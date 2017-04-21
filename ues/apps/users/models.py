#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re, hashlib, urllib
from django.db import models
from django.db.models import F
from django.db import connection
from django.utils import timezone
from django.core import validators
from django.db.models import Count
from django.contrib.auth.models import UserManager
from core.rating.userrating import get_user_rating_by_repo
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=30, unique=True, help_text='小写字母或者数字',
                    validators=[
                        validators.RegexValidator(re.compile('^[\w.@+-]+$'),
                        '请输入一个合法的用户名', 'invalid')
                    ])
    email = models.EmailField(blank=True)
    nickname = models.CharField(max_length=50, default='')
    school = models.CharField(max_length=50, default='')
    description = models.CharField(max_length=250, default='', blank=True)
    is_active = models.BooleanField(default=True, help_text='用户是否可用')
    is_staff = models.BooleanField(default=False, help_text='决定是否可以进入后台管理界面')
    date_joined = models.DateTimeField(default=timezone.now)
    code_privacy = models.CharField(max_length=20, default='private')
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    objects = UserManager()

    class Meta:
        app_label = 'users'
        verbose_name = u"用户列表"
        db_table = 'fishteam_users'

    @classmethod
    def get_gravatar_url(cls, email, size=460):
        url = "https://cdn.v2ex.com/gravatar/" + hashlib.md5(
            email.lower()).hexdigest() + "?"
        url += urllib.urlencode({'s': str(size)})
        return url

    def gravatar_url(self, size=460):
        return self.get_gravatar_url(email=self.email, size=size)

    def gravatar_url_40(self):
        return self.gravatar_url(size=40)

    def gravatar_url_460(self):
        return self.gravatar_url(size=460)

    def get_short_name(self):
        return self.nickname

    def get_ac_list_json(self, repo=None):
        return AC_Achievement.get_user_ac_list(self, repo)

    def get_user_rating_json_by_repo(self, repo=None):
        if repo is None:
            repo = ['Hdu', 'Pku']
        result = {}
        if isinstance(repo, list) or isinstance(repo, set):
            for r in repo:
                username = AccountBind.get_oj_handle_by_user_oj(self, r)
                rating, ac_rating_arr, rating_arr = get_user_rating_by_repo(
                    user=username, repo=r)
                result[r] = rating_arr
        else:
            username = AccountBind.get_oj_handle_by_user_oj(self, repo)
            rating, ac_rating_arr, rating_arr = get_user_rating_by_repo(
                user=username, repo=repo)
            result[repo] = rating_arr
        return result


    @classmethod
    def get_user_by_username(cls, username):
        try:
            user = cls.objects.get(username=username)
        except User.DoesNotExist, ex:
            user = None
        return user

    @classmethod
    def get_users_by_usernames(cls, usernames):
        return cls.objects.filter(username__in=usernames)

    @classmethod
    def create_user(cls, username, password, email):
        user = cls.objects.create_user(username=username, password=password,
            email=email, last_login=timezone.now())
        return user


class AccountBind(models.Model):
    ojs = ['Zju', 'Pku', 'Hdu', 'CF', 'PAT', 'USACO']
    Auth_OK = 1
    Auth_Fail = 2
    Auth_Not_Yet = 3
    auth_state = (
        (Auth_OK, 'Auth_OK'),
        (Auth_Fail, 'Auth_Fail'),
        (Auth_Not_Yet, 'Auth_Not_Yet'),
    )

    user = models.ForeignKey(User)
    oj = models.CharField(max_length=10)
    handle = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    authenticated = models.IntegerField(default=Auth_Not_Yet, choices=auth_state)

    class Meta:
        verbose_name = u"OJ绑定信息"
        unique_together = ("user", "oj")
        index_together = [["user", "oj"],]
        db_table = 'fishteam_users_ojbind'

    @classmethod
    def get_oj_handle_by_user_oj(cls, user, oj):
        if not isinstance(user, User):
            user = User.get_user_by_username(user)
        try:
            obj = cls.objects.get(user=user, oj=oj, authenticated=cls.Auth_OK)
        except AccountBind.DoesNotExist, ex:
            return None
        return obj.handle


class AC_Achievement(models.Model):
    user = models.ForeignKey(User)
    oj = models.CharField(max_length=10)
    pid = models.CharField(max_length=15)
    date_ac = models.DateTimeField(auto_now_add=True)

    @property
    def repo(self):
        return self.oj

    @property
    def label(self):
        return self.pid

    class Meta:
        app_label='users'
        unique_together = ("user", "oj", "pid")
        db_table = 'fishteam_users_ac_list'

    def as_dict(self):
        return {
            "repo": self.oj,
            "label": self.pid,
            "user": self.user.username,
            "actime": str(self.date_ac)
        }

    def __getitem__(self, key):
        """
            解决历史遗留问题的兼容性配置
        """
        if key == 'repo':
            return self.oj
        elif key == 'label':
            return self.pid
        elif key == 'date_ac':
            return self.date_ac
        raise KeyError(key)

    @classmethod
    def get_users_ac_list(cls, usernames, repo=None):
        users = User.get_users_by_usernames(usernames)
        if repo is not None:
            if isinstance(repo, list) or isinstance(repo, set):
                ac_list = cls.objects.filter(user__in=users, oj__in=repo)
            else:
                ac_list = cls.objects.filter(user__in=users, oj=repo)
        else:
            ac_list = cls.objects.filter(user__in=users)
        ac_list = ac_list.order_by('date_ac').annotate(repo=F('oj'),
            label=F('pid'), actime=F('date_ac')).values('user__username',
            'repo', 'label', 'actime')
        return list(ac_list)

    @classmethod
    def get_user_ac_list(cls, user, repo):
        ac_list = cls.get_user_achievement_list(user, repo).annotate(
                repo=F('oj'), label=F('pid'), actime=F('date_ac')
            ).values('repo', 'label', 'actime')
        return list(ac_list)

    @classmethod
    def get_user_achievement_list(cls, user, repo=None):
        if not isinstance(user, User):
            user = User.get_user_by_username(user)
        if repo is not None:
            if isinstance(repo, list) or isinstance(repo, set):
                return cls.objects.filter(user=user, oj__in=repo)
            else:
                return cls.objects.filter(user=user, oj=repo)
        else:
            return cls.objects.filter(user=user)

