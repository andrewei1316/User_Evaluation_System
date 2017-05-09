#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np
import re, time, math
from django.db import connection
from material.models import Material
from material.models import BackgroundKnowledge
from material.models import Classify as ClassifyModel
from core.classify.verify.verify_data import PROBLEM_CLASSIFY

def logging(msg, lv):
    # pass
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MESSAGE", "WARNING", "ERROR  "]
    print lvstr[lv], logtime, ":", msg


class Status():
    """docstring for status"""
    def __init__(self, item):
        self.isac = item[4]
        self.run_id = item[0]
        self.username = item[1]
        self.label = int(item[2])
        self.submitcount = item[3]
        self.submittime = int((item[5]).strftime('%s'))

class Knowledge():
    def __init__(self, item):
        self.repo = item[0]
        self.label = item[1]
        self.classify = item[2]

class Classify():
    def __init__(self, item):
        self.codename = item[0]
        self.chinesename = item[1]
        self.classify_model = item[3]
        self.children_classify = item[2]


class ProblemClassify(object):

    def __init__(self, classify, knowledge, classify_p, repo):
        super
        (ProblemClassify, self).__init__()
        self.REPO = repo
        self.VEC_CNT = 0
        self.CLASSIFY = {}
        self.KNOWLEDGE = {}
        self.CLASSIFY_RES = {}
        self.CLASSIFY_LIST = []
        self.PROBLEM_VECTOR = {}
        self.CLASSIFY_P = classify_p

        # self.CLASSIFY_AVG_SD = {
        #     'class1': [{
        #             'avg': xxx,
        #             'sd'
        #         },
        #         {
        #         ...
        #         }
        #     ],
        #     'class2': [{
        #         }
        #     ]
        # }
        self.CLASSIFY_AVG_SD = {}

        for cla in classify:
            self.CLASSIFY[cla.codename] = cla
            for sub_cla in cla.children_classify:
                self.CLASSIFY[sub_cla.codename] = sub_cla

        for know in knowledge:
            for cla in know.classify:
                if cla not in self.CLASSIFY_LIST:
                    self.KNOWLEDGE[cla] = []
                    self.CLASSIFY_LIST.append(cla)
                self.KNOWLEDGE[cla].append(know.label)


    def read_problem_vector(self):
        logging("Start read the problem vector file...", 0)

        with open("vector.txt", 'r') as file:
            self.PROBLEM_VECTOR = {}
            pro_cnt, vec_cnt = map(int, file.readline().split(" "))
            self.VEC_CNT = vec_cnt
            for i in range(0, pro_cnt):
                raw_data = file.readline().split(" ")
                if(len(raw_data) == 1 and raw_data[0] == ""):
                    continue
                self.PROBLEM_VECTOR[raw_data[0]] = map(float, raw_data[1: -1])

        logging("Read the problem vector file finish", 0)

    def calculate_knowledge_avg_sd(self):
        logging('Start calculate knowledge avg sd...', 0)
        for cla in self.KNOWLEDGE:
            self.CLASSIFY_AVG_SD[cla] = []
            for i in range(0, self.VEC_CNT):
                cla_xi = []
                for label in self.KNOWLEDGE[cla]:
                    try:
                        cla_xi.append(self.PROBLEM_VECTOR[label][i])
                    except Exception, ex:
                        logging("cla:%s, label:%s, error:%s" %(cla, label, ex), 2)
                cla_xi = np.array(cla_xi)
                data = {'avg': np.mean(cla_xi), 'sd': np.std(cla_xi)}
                self.CLASSIFY_AVG_SD[cla].append(data)
        logging('Calculate knowledge avg sd finish', 0)


    def classify_problem(self):
        def __get_gp(x, item):
            sd = item['sd']
            avg = item['avg']
            coe = 1 / (math.sqrt(2 * math.pi) * sd)
            ind = (math.e)**(-((x-avg)*(x-avg)) / (2 * sd * sd))
            return coe * ind

        logging("Start classify problems...", 0)
        for label in self.PROBLEM_VECTOR:
            max_cla = ""
            max_val = 0
            for cla in self.CLASSIFY_AVG_SD:
                if cla == u'others_sub':
                    continue
                cla_p = 1.0
                for i in range(0, self.VEC_CNT):
                    x = self.PROBLEM_VECTOR[label][i]
                    try:
                        p = __get_gp(x, self.CLASSIFY_AVG_SD[cla][i])
                    except Exception, ex:
                        print 'label =', label, ', cla =', cla, 'i =', i
                    if p == 0: p = 0.00001
                    cla_p *= p
                try:
                    cla_p *= self.CLASSIFY_P[cla]
                except:
                    cla_p = 0
                if cla_p > max_val:
                    max_val = cla_p
                    max_cla = cla
            # print 'label =', label, ', cla =', max_cla, ', max_val =', max_val
            if label not in self.CLASSIFY_RES:
                self.CLASSIFY_RES[label] = []
            self.CLASSIFY_RES[label].append(max_cla)
        # print self.CLASSIFY_RES
        logging("Classify problems finish", 0)

    def update_problem_classify_in_db(self):
        logging("Start update problem classify...", 0)
        others_cla = self.CLASSIFY['others_sub'].classify_model
        Material.classify.through.objects.all().delete()
        for mate in Material.objects.filter(repo=self.REPO):
            if mate.label in self.CLASSIFY_RES:
                for cla in self.CLASSIFY_RES[mate.label]:
                    classify = self.CLASSIFY[cla].classify_model
                    mate.classify.add(classify)
            else:
                mate.classify.add(others_cla)
        logging("Update problem classify finish", 0)

    def update_problem_classify_use_verify_data(self):
        logging('Start update problem classify use verify data...', 0)
        from core.classify.verify.verify_data import PROBLEM_CLASSIFY
        problem_classify = {}
        for repo in PROBLEM_CLASSIFY:
            problem_classify[repo] = {}
            for cla in PROBLEM_CLASSIFY[repo]:
                for label in PROBLEM_CLASSIFY[repo][cla]:
                    problem_classify[repo][label] = cla

        problem_material = Material.objects.filter(repo=self.REPO)
        for pro in problem_material:
            try:
                cla = Classify.objects.get(chinesename=problem_classify[pro.repo][int(pro.label)])
                pro.classify.clear()
                pro.classify.add(cla)
            except Exception, ex:
                logging(ex, 2)
            else:
                logging('Update problem '+ pro.label +' Done!', 0)
        logging('Update problem classify use verify data finish!', 0)


def main(repo='Pku'):
    logging("Problem Classify Program Start", 0)
    classify = []
    classify_p = {}
    verify_data_cnt = 0
    classify_model = ClassifyModel.objects.exclude(children=None)
    for cla in classify_model:
        child_cla = []
        children = cla.children.all()
        for child in children:
            child_item = Classify([child.codename, child.chinesename, [], child])
            child_cla.append(child_item)
            if child.codename not in classify_p:
                try:
                    verify_data_cnt += len(PROBLEM_CLASSIFY[repo][child.chinesename])
                    classify_p[child.codename] = len(PROBLEM_CLASSIFY[repo][child.chinesename])
                except Exception, ex:
                    print child.chinesename, ex
                    classify_p[child.codename] = 0

        item = Classify([cla.codename, cla.chinesename, child_cla, cla])
        classify.append(item)

    knowledge = []
    knowledge_model = BackgroundKnowledge.objects.filter(repo=repo)
    for know in knowledge_model:
        know_cla = []
        for cla in know.classify.all():
            know_cla.append(cla.codename)
        knowledge.append(Knowledge([know.repo, know.label, know_cla]))

    problem_classify = ProblemClassify(classify, knowledge, classify_p, repo)
    problem_classify.read_problem_vector()
    problem_classify.calculate_knowledge_avg_sd()
    problem_classify.classify_problem()
    problem_classify.update_problem_classify_in_db()

    logging("Problem Classify Program Finish", 0)

