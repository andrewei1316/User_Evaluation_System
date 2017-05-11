#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np
import os, re, time, math
from django.db import connection
from ues.settings import TMP_CHDIR
from material.models import Material
from material.models import BackgroundKnowledge
from core.classify.problem_classifier import logging
from material.models import Classify as ClassifyModel


class ProblemClassify(object):

    def __init__(self, repo, classify_list, classify_p, knowledge, vector_file):
        super
        (ProblemClassify, self).__init__()
        self.REPO = repo
        self.VEC_CNT = 0
        self.CLASSIFY_RES = {}
        self.PROBLEM_VECTOR = {}
        self.KNOWLEDGE = knowledge
        self.CLASSIFY_P = classify_p
        self.CLASSIFY_LIST = classify_list
        self.PROBLEM_VECTOR_FILE = vector_file

        # {
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


    def read_problem_vector(self):
        logging("Start read the problem vector file...", 0)
        with open(self.PROBLEM_VECTOR_FILE, 'r') as file:
            self.PROBLEM_VECTOR = {}
            pro_cnt, vec_cnt = map(int, file.readline().split(" "))
            self.VEC_CNT = vec_cnt
            for i in range(0, pro_cnt):
                raw_data = file.readline().split(" ")
                if(len(raw_data) == 1 and raw_data[0] == ""):
                    continue
                self.PROBLEM_VECTOR[raw_data[0]] = map(float, raw_data[1:])

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
                        logging("label: %s, cla: %s, dx: %s, error: %s" %(
                            label, cla, i), 2)
                    if p == 0: p = 0.00001
                    cla_p *= p
                try:
                    cla_p *= self.CLASSIFY_P[cla]
                except:
                    cla_p = 0
                if cla_p > max_val:
                    max_val = cla_p
                    max_cla = cla
            if label not in self.CLASSIFY_RES:
                self.CLASSIFY_RES[label] = []
            self.CLASSIFY_RES[label].append(max_cla)
        # print self.CLASSIFY_RES
        logging("Classify problems finish", 0)

def naive_bayes_classifier(repo, classify_list, classify_p, knowledge, vector_file):
    logging("Problem Classify Program Start", 0)
    problem_classify = ProblemClassify(repo, classify_list, classify_p, knowledge, vector_file)
    problem_classify.read_problem_vector()
    problem_classify.calculate_knowledge_avg_sd()
    problem_classify.classify_problem()
    logging("Problem Classify Program Finish", 0)
    return problem_classify.CLASSIFY_RES

