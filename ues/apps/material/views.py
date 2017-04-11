#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from material.models import Material
from django.shortcuts import render, HttpResponse

# Create your views here.

def get_problem_rating_json(request):
    result = Material.get_all_problem_rating_json()
    return HttpResponse(json.dumps(result, ensure_ascii=False))

def get_problem_classify_json(request):
    result = Material.get_all_problem_classify_json()
    return HttpResponse(json.dumps(result, ensure_ascii=False))
