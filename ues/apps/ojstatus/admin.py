#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from ojstatus.models import OJStatus

# Register your models here.

class OJStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'runid', 'repo', 'label', 'user', 'submitcount', 'isac', 'submittime')
    search_fields = ('repo', 'label', 'user', 'submittime')
    list_filter = ('repo', 'isac',)
    ordering = ('id',)
    actions_on_top = True;
    actions_on_bottom = True;


admin.site.register(OJStatus, OJStatusAdmin)
