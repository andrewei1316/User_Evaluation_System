#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import time
import requests
from django.utils import timezone
from django.core.cache import cache

from squads.models import Squads
from ojstatus.fetchers import poj_status_fetcher as psf
from ojstatus.fetchers import hdu_status_fetcher as hsf

from ues.celery import app

@app.task
def update_poj_status():
    psf.run_fetcher()

@app.task
def update_hdu_status():
    hsf.run_fetcher()

@app.task
def update_squads_user_rating():
    for squ in Squads.objects.all():
        cache_str = 'squads_%d_users_rating_json' % (squ.id, )
        cache.set(cache_str, None, None)
        squ.get_squads_users_rating_json()
