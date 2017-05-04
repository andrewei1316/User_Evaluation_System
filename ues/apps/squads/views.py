#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, datetime
from django.http import Http404
from squads.models import Squads, SquadsUser
from users.models import User, AC_Achievement
from django.shortcuts import get_object_or_404
from django.shortcuts import render, HttpResponse

# Create your views here.

def get_squads_info(request, squads_id):
    user = request.user
    squads = get_object_or_404(Squads, id=squads_id)
    try:
        squads_user = SquadsUser.objects.get(user=user.username, squads=squads)
    except SquadsUser.DoesNotExist:
        if not (user.is_staff or user.is_superuser):
            raise Http404('页面不存在')
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

def get_own_squads_info(request):
    squads = Squads.objects.all().order_by('-create_date')
    if not (request.user.is_superuser or request.user.is_staff):
        squads = squads.filter(create_user=request.user.username)
    return render(request, 'squads/squads_manage.html', {
        'squads': squads,
    })

def get_self_squads_info(request):
    user = request.user
    squads_users = SquadsUser.objects.filter(user=user.username)
    return render(request, 'squads/squads_self.html', {
        'squads_users': squads_users,
    })

def create_update_squads(request):
    user = request.user
    submit_type = request.POST['type']
    squad_id = request.POST['squad-id']
    squad_name = request.POST['squad-name']
    squad_create_user = request.POST['create-user']
    squad_description = request.POST['squad-description']
    squad_users = request.REQUEST.getlist('squad-users-select')

    result = {'status': 'success', 'message': '操作成功'}
    if (not (user.is_staff or user.is_superuser)) and user.username != squad_create_user:
        result['status'] = 'failure'
        result['message'] = '您没有权限进行次操作'
        return HttpResponse(json.dumps(result, ensure_ascii=False))       
    if squad_name == '':
        result['status'] = 'failure'
        result['message'] = '小组名称不能为空'
        return HttpResponse(json.dumps(result, ensure_ascii=False))       

    if submit_type == 'update':
        try:
            squad = Squads.objects.get(id=squad_id, create_user=squad_create_user)
        except Squads.DoesNotExist:
            result['status'] = 'failure'
            result['message'] = '未找到编号为%d,创建者为%s的训练小组！' % (squad_id, squad_create_user)
        else:
            squad.name = squad_name
            squad.description = squad_description
            squad.save()
            SquadsUser.objects.filter(squads=squad).exclude(user__in=squad_users).delete()
            cur_user = list(SquadsUser.objects.filter(squads=squad).values_list('user', flat=True))
            add_user = list(set(squad_users).difference(set(cur_user)))
            add_quads_users = []
            for squ_user in add_user:
                squads_user = SquadsUser(user=squ_user, name=squ_user, nickname=squ_user, squads=squad)
                add_quads_users.append(squads_user)
            SquadsUser.objects.bulk_create(add_quads_users)
    else:
        squad = Squads.objects.create(name=squad_name, create_user=squad_create_user, description=squad_description)
        SquadsUser.objects.filter(squads=squad).delete()
        for squ_user in squad_users:
            SquadsUser.objects.create(user=squ_user, name=squ_user, nickname=squ_user, squads=squad)

    return HttpResponse(json.dumps(result, ensure_ascii=False))

def delete_squads(request, squads_id):
    user = request.user

    result = {'status': 'success', 'message': '操作成功'}
    try:
        squad = Squads.objects.get(id=squads_id)
    except Squads.DoesNotExist:
        result['status'] = 'failure'
        result['message'] = '未找到编号为%d的训练小组！' % (squads_id,)
    else:
        if (not (user.is_staff or user.is_superuser)) and user.username != squad.create_user:
            result['status'] = 'failure'
            result['message'] = '您没有权限进行次操作'
        else:
            SquadsUser.objects.filter(squads=squad).delete()
            squad.delete()
    return HttpResponse(json.dumps(result, ensure_ascii=False))

def update_squadsusers(request):
    user = request.user
    squadsusers_id = request.POST['user-id']
    squadsusers_name = request.POST['user-name']
    squadsusers_nickname = request.POST['user-nickname']
    result = {'status': 'success', 'message': '操作成功'}
    try:
        squads_user = SquadsUser.objects.get(id=squadsusers_id)
    except SquadsUser.DoesNotExist:
        result['status'] = 'failure'
        result['message'] = '该小组用户不存在'
    else:
        squads_user.name = squadsusers_name
        squads_user.nickname = squadsusers_nickname
        squads_user.save()
    return HttpResponse(json.dumps(result, ensure_ascii=False))

def delete_squadsusers(request, squadsusers_id):
    user = request.user
    result = {'status': 'success', 'message': '操作成功'}
    try:
        squads_user = SquadsUser.objects.get(id=squadsusers_id)
    except SquadsUser.DoesNotExist:
        result['status'] = 'failure'
        result['message'] = '该小组用户不存在'
    else:
        if (not (user.is_staff or user.is_superuser)) and user.username != squads_user.user:
            result['status'] = 'failure'
            result['message'] = '您没有权限进行次操作'
        else:
            squads_user.delete()
    return HttpResponse(json.dumps(result, ensure_ascii=False))
