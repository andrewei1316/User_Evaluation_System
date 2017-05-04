#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.core.cache import cache
from core.basemodel import BaseModel
from core.rating.userrating import get_user_rating_by_repo
from users.models import User, AccountBind, AC_Achievement

# Create your models here.

class Squads(BaseModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, blank=False)
    description = models.TextField(blank=True, default=None)
    create_user = models.CharField(max_length=50, blank=False)

    class Meta:
        app_label = 'squads'
        db_table = 'ues_squads'
        verbose_name = u"训练小组"
        unique_together = (('id',))
        index_together = [['create_user', 'name'],]

    def __unicode__(self):
        return u"%s | %s | %s" % (
            unicode(self.id),
            unicode(self.name),
            unicode(self.create_user))

    def get_users_aclist(self):
        usernames = SquadsUser.get_users_by_squads(self)
        users_name = list(usernames)
        users_aclist = AC_Achievement.get_users_ac_list(users_name)
        return users_aclist

    def get_users_info(self):
        users_list = SquadsUser.get_objects_by_squads(self)
        users_info = users_list.values('user', 'name', 'nickname')
        return list(users_info)

    def get_squads_users_rating_json(self, repo):
        cache_str = 'squads_users_rating_json'
        result = cache.get(cache_str)
        result = None
        if result is None:
            result = {}
            if repo is None:
                repo = ['Pku', 'Hdu']
            usernames = SquadsUser.get_users_by_squads(self)
            users_name = list(usernames)
            if isinstance(repo, list) or isinstance(repo, set):
                for r in repo:
                    for user in users_name:
                        username = AccountBind.get_oj_handle_by_user_oj(user, r)
                        rating, ac_rating_arr, rating_arr = get_user_rating_by_repo(
                            user=user, repo=r)
                        if r not in result:
                            result[r] = {}
                        result[r][user] = rating_arr
            else:
                for user in users_name:
                    username = AccountBind.get_oj_handle_by_user_oj(user, r)
                    rating, ac_rating_arr, rating_arr = get_user_rating_by_repo(
                        user=user, repo=r)
                    if repo not in result:
                        result[repo] = {}
                    result[repo][user] = rating_arr
            cache.set(cache_str, result, None)
        return result

class SquadsUser(BaseModel):
    id = models.AutoField(primary_key=True)
    user = models.CharField(max_length=50, blank=False)
    name = models.CharField(max_length=50, blank=True, default=None)
    nickname = models.CharField(max_length=50, blank=True, default=None)
    squads = models.ForeignKey(Squads, on_delete=models.DO_NOTHING, db_constraint=False)

    class Meta:
        app_label = 'squads'
        db_table = 'ues_squads_user'
        verbose_name = u"小组成员"
        unique_together = (('user', 'squads'),)
        index_together = [['user', 'squads'],]

    @classmethod
    def get_objects_by_squads(cls, squads):
        return cls.objects.filter(squads=squads)

    @classmethod
    def get_users_by_squads(cls, squads):
        return cls.objects.filter(squads=squads).values_list('user', flat=True)
