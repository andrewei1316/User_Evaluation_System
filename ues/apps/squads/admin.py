#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from squads.models import Squads, SquadsUser

# Register your models here.

class SquadsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'create_user', 'description', 'create_date')
    search_fields = ('name', 'description', 'create_user')
    list_filter = ('create_user', 'name')
    ordering = ('id',)

class SquadsUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'nickname', 'squads', 'create_date')
    search_fields = ('user', 'name', 'nickname', 'squads')
    list_filter = ('squads',)
    ordering = ('id',)

admin.site.register(Squads, SquadsAdmin)
admin.site.register(SquadsUser, SquadsUserAdmin)
