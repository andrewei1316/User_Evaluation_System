#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

# Create your models here.

class Material(models.Model):
    id = models.AutoField(primary_key=True)
    repo = models.CharField(max_length=20, verbose_name=_(u"题目类型"))
    label = models.CharField(max_length=45, verbose_name=_(u"题目编号"))
    rating = models.FloatField(default=1, verbose_name=_(u"题目难度"))
    classify = models.ManyToManyField('material.Classify', default=None,
                                        blank=True, verbose_name=_(u"题目分类"))

    class Meta:
        app_label = 'material'
        db_table = 'ues_material'
        verbose_name = u"题目属性"
        unique_together = (('repo', 'label'),)
        index_together = [['repo', 'label'],]


    @classmethod
    def get_all_problem_rating_json(cls):
        cache_str = 'all_problem_rating_json'
        result = cache.get(cache_str)
        if result is None:
            material = cls.objects.all()
            repos = set(material.values_list('repo', flat=True))
            result = {}
            for repo in repos:
                result[repo] = {}
            for mate in material:
                result[mate.repo][mate.label] = mate.rating
            cache.set(cache_str, result, None)
        return result


    @classmethod
    def get_all_problem_classify_json(cls):
        cache_str = 'all_problem_classify_json'
        result = cache.get(cache_str)
        result = None
        if result is None:
            material = cls.objects.all().values(
                'repo', 'label', 'classify__chinesename')
            problem_classify = {}
            all_classify = {}
            for mate in material:
                if mate['repo'] not in problem_classify:
                    problem_classify[mate['repo']] = {}
                if mate['label'] not in problem_classify[mate['repo']]:
                    problem_classify[mate['repo']][mate['label']] = []
                problem_classify[mate['repo']][mate['label']].append(
                    (mate['classify__chinesename'] or u'其他'))
            classify = Classify.objects.all()
            for cla in classify:
                for child in cla.children.all():
                    all_classify[child.chinesename] = cla.chinesename
            result = {'problem_classify': problem_classify, 'all_classify': all_classify}
            cache.set(cache_str, result, None)
        return result


    @classmethod
    def update_create_problem_rating_by_repo_label(cls, repo, label, rating):
        update_values = {
            "repo": repo,
            "label": label,
            "rating": rating
        }
        cls.objects.update_or_create(repo=repo, label=label, rating=rating,
            defaults=update_values)


class BackgroundKnowledge(models.Model):
    id = models.AutoField(primary_key=True)
    repo = models.CharField(max_length=20, verbose_name=_(u"题目类型"))
    label = models.CharField(max_length=45, verbose_name=_(u"题目编号"))
    classify = models.ManyToManyField('material.Classify', default=None,
                                        blank=True, verbose_name=_(u"题目分类"))

    class Meta:
        app_label = 'material'
        db_table = 'ues_background_knowledge'
        verbose_name = u"背景知识"
        unique_together = (('repo', 'label'),)
        index_together = [['repo', 'label'],]


class Classify(models.Model):
    id = models.AutoField(primary_key=True)
    codename = models.CharField(max_length=50, default='others', verbose_name=_(u"英文名称"))
    chinesename = models.CharField(max_length=50, default='其他', verbose_name=_(u"中文名称"))
    children = models.ManyToManyField('self', default=None, blank=True,
                                        symmetrical=False, verbose_name=_(u"子类"))

    def __unicode__(self):
        return u"%s | %s" % (unicode(self.codename), unicode(self.chinesename))

    class Meta:
        verbose_name = u"题目分类"
        unique_together = (('codename'),)
        app_label = 'material'
        db_table = 'ues_classify'
