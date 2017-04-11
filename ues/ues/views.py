#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render
from material.models import Material
# from core.classify.problemclassify import main
# from core.classify.problemclassify1 import main as main1


# Create your views here.
def index(request):
    result = Material.get_all_problem_classify_json()
    # print result
    return render(request, 'ues/index.html',{'result': result})