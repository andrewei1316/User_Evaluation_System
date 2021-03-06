#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import time
from material.models import Material, Classify
from core.classify.verify.verify_data import PROBLEM_CLASSIFY

def logging(msg, lv):
    # pass
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MESSAGE", "WARNING", "ERROR  "]
    print lvstr[lv], logtime, ":", msg


class VerifyProblemClassify(object):

    def __init__(self, verify_data, repo, ignored_others):
        super
        (VerifyProblemClassify, self).__init__()
        self.N = {}
        self.P = {}
        self.TP = {}
        self.TN = {}
        self.FP = {}
        self.FN = {}
        self.REPO = repo
        self.CASE_CNT = 0
        self.CON_MATRIX = {}
        self.IGNORED_OTHERS = ignored_others

        # 得到正元组和负元组总数
        # self.VERIFY_DATA = {}
        self.VERIFY_DATA = verify_data
        for cla in verify_data:
            # for label in verify_data[cla]:
            #     self.VERIFY_DATA[label] = cla
            self.CASE_CNT += len(verify_data[cla])

        # 处理 material 使其更容易被访问
        self.MATERIAL = {}
        pro_mate = Material.objects.filter(repo=repo)
        for mate in pro_mate:
            self.MATERIAL[int(mate.label)] = mate
        # self.MATERIAL = Material.objects.filter(repo=repo)

        # 初始化所有分类的 P N TP TN FP FN
        self.CLASSIFY = Classify.objects.filter(children=None)
        for classify in self.CLASSIFY:
            cla = classify.chinesename
            self.CON_MATRIX[cla] = {}
            for classify1 in self.CLASSIFY:
                cla1 = classify1.chinesename
                self.CON_MATRIX[cla][cla1] =0

        # 初始化所有分类的 P N TP TN FP FN
        self.CLASSIFY = Classify.objects.filter(children=None)
        for cla in self.CLASSIFY:
            self.P[cla.chinesename] = 0
            self.N[cla.chinesename] = 0
            self.TP[cla.chinesename] = 0
            self.TN[cla.chinesename] = 0
            self.FP[cla.chinesename] = 0
            self.FN[cla.chinesename] = 0


    # def get_classify_TP_TN_FP_FN(self):
    #     total_cnt = 0
    #     for classify in self.CLASSIFY:
    #         cla = classify.chinesename
    #         for label in self.VERIFY_DATA[cla]:
    #             try:
    #                 pro_cla = self.MATERIAL[label].classify.all()[0].chinesename
    #                 if (pro_cla == u'其他' or cla == u'其他') and self.IGNORED_OTHERS:
    #                     continue
    #                 total_cnt += 1
    #                 self.P[cla] += 1
    #                 if pro_cla == cla:
    #                     self.TP[cla] += 1
    #                 else:
    #                     self.FN[cla] += 1
    #                     self.FP[pro_cla] += 1
    #             except Exception, ex:
    #                 logging(ex, 2)
    #                 continue

    #     for cla in self.CLASSIFY:
    #         for c in self.CLASSIFY:
    #             if cla.chinesename == c.chinesename: continue
    #             self.TN[cla.chinesename] += self.TP[c.chinesename]

    #     for classify in self.CLASSIFY:
    #         cla = classify.chinesename
    #         self.N[cla] = total_cnt - self.P[cla]

    def get_classify_con_matrix(self):
        for classify in self.CLASSIFY:
            cla = classify.chinesename
            for label in self.VERIFY_DATA[cla]:
                try:
                    # for pro_cla in self.MATERIAL[label].classify.all():
                    pro_cla = self.MATERIAL[label].classify.all()[0].chinesename
                except Exception, ex:
                    logging(ex, 2)
                    pro_cla = u'其他'
                if (pro_cla == u'其他' or cla == u'其他') and self.IGNORED_OTHERS:
                    continue
                self.CON_MATRIX[cla][pro_cla] += 1


    def get_classify_TP_TN_FP_FN(self):
        right_cnt = 0
        classify_list = self.CON_MATRIX.keys()
        classify_cnt = len(classify_list)
        for cla in classify_list:
            for cla1 in classify_list:
                self.P[cla] += self.CON_MATRIX[cla][cla1]
                if cla == cla1:
                    right_cnt += self.CON_MATRIX[cla][cla1]
                    self.TP[cla] += self.CON_MATRIX[cla][cla1]
                else:
                    self.FP[cla1] += self.CON_MATRIX[cla][cla1]
                    self.FN[cla] += self.CON_MATRIX[cla][cla1]

        for cla in classify_list:
            self.TN[cla] = right_cnt - self.TP[cla]
            self.N[cla] = self.CASE_CNT - self.P[cla]

    def print_classify_TP_TN_FP_FN(self):
        print 'classify\tP\tN\tTP\tTN\tFP\tFN\t召回率'
        for classify in self.CLASSIFY:
            cla = classify.chinesename
            print "%s\t\t%d\t%d\t%d\t%d\t%d\t%d\t%.5f" % (cla[0:3], self.P[cla], self.N[cla], self.TP[cla],
                self.TN[cla], self.FP[cla], self.FN[cla], self.TP[cla]/self.P[cla] if self.P[cla] else 0)
        print '===================================================='
        print 'P+N =', self.P['2-SAT']+self.N['2-SAT'], ', TP+TN =', self.TP['2-SAT']+self.TN['2-SAT']
        print '准确率: %.5f' % ((self.TP[u'2-SAT'] + self.TN[u'2-SAT']) / (self.P[u'2-SAT'] + self.N[u'2-SAT']),)

    def verify_problem_classify(self):
        pass

def main(ignored_others=True, repo='Pku'):
    if repo in PROBLEM_CLASSIFY:
        verify_data = PROBLEM_CLASSIFY[repo]
    else:
        verify_data = {}
    verify_problem_classify = VerifyProblemClassify(verify_data, repo, ignored_others)
    verify_problem_classify.get_classify_con_matrix()
    verify_problem_classify.get_classify_TP_TN_FP_FN()
    verify_problem_classify.print_classify_TP_TN_FP_FN()
