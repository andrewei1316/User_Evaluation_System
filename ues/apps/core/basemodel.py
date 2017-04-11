#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models

class BaseModel(models.Model):
    create_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True