#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from core.classify.verify.verify_data import PROBLEM_CLASSIFY
from material.models import Material, Classify, BackgroundKnowledge

def logging(msg, lv):
    # pass
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MESSAGE", "WARNING", "ERROR  "]
    print lvstr[lv], logtime, ":", msg


class VerifyProblemClassify(object):

    def __init__(self, verify_data, repo):
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
        self.IGNORED_OTHERS = True

        # 得到正元组和负元组总数
        self.VERIFY_DATA = {} 
        for cla in verify_data:
            for label in verify_data[cla]:
                self.VERIFY_DATA[label] = cla
            self.CASE_CNT += len(verify_data[cla])

        # 处理 material 使其更容易被访问
        # self.MATERIAL = {}
        # pro_mate = Material.object.filter(repo=repo)
        # for mate in pro_mate:
        #     self.MATERIAL[mate.label] = mate
        self.MATERIAL = Material.objects.filter(repo=repo)

        # 初始化所有分类的 P N TP TN FP FN
        self.CLASSIFY = Classify.objects.filter(children=None)
        for cla in self.CLASSIFY:
            try:
                self.P[cla.chinesename] = len(verify_data[cla.chinesename])
                self.N[cla.chinesename] = self.CASE_CNT - len(verify_data[cla.chinesename])
            except Exception, ex:
                logging(ex, 2)
                self.P[cla.chinesename] = 0
                self.N[cla.chinesename] = 0
            self.TP[cla.chinesename] = 0
            self.TN[cla.chinesename] = 0
            self.FP[cla.chinesename] = 0
            self.FN[cla.chinesename] = 0

        # print self.VERIFY_DATA

    def get_classify_TP_TN_FP_FN(self):
        for classify in self.CLASSIFY:
            cla = classify.chinesename
            for mate in self.MATERIAL.filter(classify=classify):
                if int(mate.label) not in self.VERIFY_DATA: continue
                # 属于类cla且被正确分到类cla中
                if cla == self.VERIFY_DATA[int(mate.label)]:
                    self.TP[cla] += 1
                else:
                    # 不属于类cla但是被错误分到类cla中
                    self.FP[cla] += 1
                    # 属于类 cla 但是没有分到类 cla 中
                    self.FN[self.VERIFY_DATA[int(mate.label)]] += 1
                
        # 
        for cla in self.CLASSIFY:
            for c in self.CLASSIFY:
                if cla.chinesename == c.chinesename: continue
                self.TN[cla.chinesename] += self.TP[c.chinesename]


    def print_classify_TP_TN_FP_FN(self):
        print 'classify\tP\tN\tTP\tTN\tFP\tFN'
        for classify in self.CLASSIFY:
            cla = classify.chinesename
            print "%s\t\t%d\t%d\t%d\t%d\t%d\t%d" % (cla[0:3], self.P[cla], self.N[cla],
                self.TP[cla], self.TN[cla], self.FP[cla], self.FN[cla])

    def verify_problem_classify(self):
        pass

def main(repo='Pku'):
    if repo in PROBLEM_CLASSIFY:
        verify_data = PROBLEM_CLASSIFY[repo]
    else:
        verify_data = {}
    verify_problem_classify = VerifyProblemClassify(verify_data, repo)
    verify_problem_classify.get_classify_TP_TN_FP_FN()
    verify_problem_classify.print_classify_TP_TN_FP_FN()
