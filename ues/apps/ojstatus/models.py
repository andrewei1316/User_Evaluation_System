#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.db.models import Max
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _

# Create your models here.

class OJStatus(models.Model):
    runid = models.IntegerField(verbose_name=_(u"运行编号"))
    user = models.CharField(max_length=50, verbose_name=_(u'提交用户'))
    repo = models.CharField(max_length=50, verbose_name=_(u"OJ类型"))
    label = models.CharField(max_length=50, verbose_name=_(u"题目编号"))
    submitcount = models.IntegerField(verbose_name=_(u'提交次数'))
    isac = models.BooleanField(default=False, verbose_name=_(u'是否AC'))
    submittime = models.DateTimeField(blank=True, null=True, verbose_name=_(u"提交时间"))

    class Meta:
        app_label = 'ojstatus'
        verbose_name = u"提交信息"
        db_table = 'ues_ojstatus'
        unique_together = (('repo', 'label', 'user'),)
        index_together = [['user'], ['repo', 'label', 'isac'],]

    @classmethod
    def update_or_create_object(cls, user, repo, label, submittime, is_ac):
        actime = submittime if is_ac else None
        try:
            uach = cls.objects.get(user=user, repo=repo, label=label)
        except UserAchievement.DoesNotExist, ex:
            uach = cls(user=user, repo=repo, label=label,
                submitcount=1, isac=is_ac, actime=actime)
            uach.save()
        else:
            if not uach.isac:
                uach.isac = is_ac
                uach.actime = actime
                uach.submitcount += 1
                uach.save()
        return uach

    @classmethod
    def get_max_runid_by_repo(cls, repo):
        runid = cls.objects.filter(repo=repo).aggregate(Max('runid'))['runid__max']
        if runid is None:
            runid = 0
        return runid
