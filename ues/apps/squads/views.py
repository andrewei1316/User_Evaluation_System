#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, datetime
from squads.models import Squads, SquadsUser
from users.models import User, AC_Achievement
from django.shortcuts import get_object_or_404
from django.shortcuts import render, HttpResponse

# Create your views here.

def get_squads_info(request, squads_id):
    squads = get_object_or_404(Squads, id=squads_id)
    return render(request, 'squads/squads.html', {
        'squads': squads,
    })

def get_squads_users_info(request, squads_id):
    squads = get_object_or_404(Squads, id=squads_id)
    users_info = squads.get_users_info()
    return HttpResponse(json.dumps(users_info, ensure_ascii=False))


class DateTimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def get_squads_users_aclist(request, squads_id):
    squads = get_object_or_404(Squads, id=squads_id)
    ac_list = squads.get_users_aclist()
    return HttpResponse(json.dumps(ac_list, ensure_ascii=False, cls=DateTimeEncoder))

def get_squads_users_rating(request, squads_id):
    squads = get_object_or_404(Squads, id=squads_id)
    users_rating = squads.get_squads_users_rating_json(None)
    return HttpResponse(json.dumps(users_rating, ensure_ascii=False, cls=DateTimeEncoder))
