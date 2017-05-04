#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from material.models import Material, Classify
from django.shortcuts import render, HttpResponse

# Create your views here.

def get_problem_rating_json(request):
    result = Material.get_all_problem_rating_json()
    return HttpResponse(json.dumps(result, ensure_ascii=False))

def get_problem_classify_json(request):
    result = Material.get_all_problem_classify_json()
    return HttpResponse(json.dumps(result, ensure_ascii=False))

def get_all_problem_material(request):
    material = Material.objects.all()
    repo = material.values_list('repo', flat=True)
    repo = list(set(repo))
    classify = Classify.objects.exclude(children=None)

    search_repos = request.REQUEST.getlist('search-repos')
    search_labels = request.GET.get('search-labels')

    print search_labels
    print search_repos

    if search_repos is not None and search_repos != []:
        material = material.filter(repo__in=search_repos)
    if search_labels is not None and search_labels != '':
        search_labels = filter(None, search_labels.split(' '))
        material = material.filter(label__in=search_labels)

    return render(request, 'material/material.html', {
        'repo': repo,
        'material': material,
        'classify': classify,
    })

def update_material(request):
    repo = request.POST['mate-repo']
    label = request.POST['mate-label']
    classify_str = request.REQUEST.getlist('mate-classify')
    result = {'status': 'success', 'message': '操作成功'}
    try:
        mate = Material.objects.get(repo=repo, label=label)
    except Material.DoesNotExist:
        result['status'] = 'failure'
        result['message'] = '题目来源为 %s, 标号为 %s 的题目不存在' %(repo, label)
    else:
        mate.classify.clear()
        try:
            cla_id = [int(i) for i in classify_str]
            mate.classify = cla_id
        except Exception, ex:
            result['status'] = 'failure'
            result['message'] = '添加分类出现错误'

    return HttpResponse(json.dumps(result, ensure_ascii=False))

