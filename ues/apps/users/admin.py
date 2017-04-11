#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin

from users.models import User
from users.models import AccountBind

# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'nickname', 'school',
                    'date_joined', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'nickname')
    list_filter = ('is_active', 'is_staff')
    ordering = ('id',)
    actions = ['reset_password']

    def reset_password(self, request, queryset):
        for u in queryset:
            u.set_password("12345678")
            u.save()
        self.message_user(request, u"重置成功")
    reset_password.short_description = u"重置密码为 12345678"


class AccountBindAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'oj', 'handle', 'authenticated')
    search_fields = ('user',)
    list_filter = ('oj',)
    ordering = ('id',)


admin.site.register(User, UserAdmin)
admin.site.register(AccountBind, AccountBindAdmin)
