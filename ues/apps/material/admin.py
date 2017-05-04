#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from django.db.models import Avg
from material.models import Material, Classify, BackgroundKnowledge

# Register your models here.
class MaterialAdmin(admin.ModelAdmin):
    ordering = ('id',)
    actions_on_top = True;
    actions_on_bottom = True;
    list_filter = ('repo', 'classify__chinesename')
    search_fields = ('id', 'repo', 'label', 'rating')
    list_display = ('id', 'repo', 'label', 'rating', 'get_classify')

    def get_classify(self, obj):
        return '|'.join([c.chinesename for c in obj.classify.all() ])


class ClassifyAdmin(admin.ModelAdmin):
    ordering = ('id',)
    actions_on_top = True;
    actions_on_bottom = True;
    list_filter = ('codename', 'chinesename')
    list_display = ('id', 'codename', 'chinesename')
    search_fields = ('id', 'codename', 'chinesename')
    filter_horizontal = ('children',)


class BackgroundKnowledgeAdmin(admin.ModelAdmin):
    ordering = ('id',)
    actions_on_top = True;
    actions_on_bottom = True;
    list_filter = ('classify__chinesename',)
    search_fields = ('id', 'repo', 'label', 'classify')
    list_display = ('id', 'repo', 'label', 'get_classify')

    filter_horizontal = ('classify',)

    def get_classify(self, obj):
        return '|'.join([c.chinesename for c in obj.classify.all() ])


admin.site.register(Classify, ClassifyAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(BackgroundKnowledge, BackgroundKnowledgeAdmin)
