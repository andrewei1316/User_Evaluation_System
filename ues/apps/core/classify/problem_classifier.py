#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import os, time
from ues.settings import TMP_CHDIR
from material.models import Material
from material.models import BackgroundKnowledge
from material.models import Classify as ClassifyModel


def logging(msg, lv):
    # pass
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MESSAGE", "WARNING", "ERROR  "]
    print lvstr[lv], logtime, ":", msg

def update_problem_classify_in_db(repo, classify_dict, classify_res):
    logging("Start update problem classify...", 0)
    others_cla = ClassifyModel.objects.get(codename='others_sub')
    Material.classify.through.objects.all().delete()
    for mate in Material.objects.filter(repo=repo):
        if mate.label in classify_res:
            for cla in classify_res[mate.label]:
                classify = classify_dict[cla]
                mate.classify.add(classify)
        else:
            mate.classify.add(others_cla)
    logging("Update problem classify finish", 0)

def main(repo='Pku'):
    knowledge = {}
    classify_p = {}
    classify_dict = {}
    classify_list = []
    classify_model = ClassifyModel.objects.filter(children=None)
    bks_count = BackgroundKnowledge.objects.filter(repo=repo).count()
    for cla in classify_model:
        if cla.chinesename == u'其他':
            continue
        classify_dict[cla.id] = cla
        classify_list.append(cla.id)
        bks = BackgroundKnowledge.objects.filter(repo=repo, classify=cla)
        knowledge[cla.id] = bks.values_list('label', flat=True)
        classify_p[cla.id] = bks.count() / bks_count

    aclist_file = os.path.join(TMP_CHDIR, '%s_user_aclist.txt' %(repo, ))
    vector_file = os.path.join(TMP_CHDIR, '%s_problem_vector.txt'%(repo, ))

    try:
        if os.path.exists(TMP_CHDIR):
            os.remove(aclist_file)
            os.remove(vector_file)
        else:
            os.mkdir(TMP_CHDIR)
    except Exception, ex:
        logging('%s'%(ex, ), 2)

    from core.classify.word2vec import make_problems_vector
    from core.classify.naive_bayes_classifier import naive_bayes_classifier

    make_problems_vector(repo, aclist_file, vector_file)
    classify_res = naive_bayes_classifier(
        repo=repo,
        classify_list=classify_list,
        classify_p=classify_p,
        knowledge=knowledge,
        vector_file=vector_file
    )

    update_problem_classify_in_db(repo, classify_dict, classify_res)
