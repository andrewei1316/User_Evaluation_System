#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Celery initialize."""
from __future__ import absolute_import
import os

import django
from celery import Celery

from celery.schedules import crontab

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ues.settings')

broker_url = 'amqp://guest:guest@127.0.0.1:5672'

app = Celery('ues', broker=broker_url)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'update_poj_status': {
            'task': 'ojstatus.tasks.update_poj_status',
            'schedule': crontab(hour=2, minute=0),
        },
        'update_hdu_status': {
            'task': 'ojstatus.tasks.update_hdu_status',
            'schedule': crontab(hour=2, minute=0),
        },
        'update_squads_user_rating': {
            'task': 'ojstatus.tasks.update_squads_user_rating',
            'schedule': crontab(hour=5, minute=0),
        },
    },
    CELERY_TIMEZONE=settings.TIME_ZONE,
    CELERY_ACCEPT_CONTENT=['pickle', 'json', 'msgpack', 'yaml'],
)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == '__main__':
    django.setup()
    app.start()
