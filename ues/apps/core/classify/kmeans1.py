#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import os, re, time, math
from django.db import connection
from ues.settings import TMP_CHDIR
from material.models import Material, Classify, BackgroundKnowledge

def logging(msg, lv):
    # pass
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MESSAGE", "WARNING", "ERROR  "]
    print "%s %s : %s" %(lvstr[lv], logtime, msg)


class ProblemClassify(object):

    def __init__(self, classify, knowledge, repo='Pku', users_list=[], max_label=10000):
        super
        (ProblemClassify, self).__init__()
        self.VEC_CNT = 0
        self.REPO = repo
        self.KNOWLEDGE = {}
        self.REKNOWLEDGE = {}
        self.USER = users_list
        self.CLASSIFY_DICT = {}
        self.CLASSIFY = classify
        self.PROBLEM_RELATION = {}
        self.MAX_COUNT = max_label
        self.PROBLEM_VECTOR = [[] for i in range(self.MAX_COUNT)]
        self.PROBLEM_VECTOR_FILE = os.path.join(TMP_CHDIR, '%s_problem_vector.txt'%(repo, ))

        for cla in classify:
            self.CLASSIFY_DICT[cla.chinesename] = cla

        for know in knowledge:
            self.REKNOWLEDGE[know.label] = []
            for cla in know.classify.all():
                if cla.chinesename not in self.KNOWLEDGE:
                    self.KNOWLEDGE[cla.chinesename] = []
                self.KNOWLEDGE[cla.chinesename].append(know.label)
                self.REKNOWLEDGE[know.label].append(cla.chinesename)

        # from core.classify.verify.verify_data import PROBLEM_CLASSIFY
        # for cla in PROBLEM_CLASSIFY[self.REPO]:
        #     self.KNOWLEDGE[cla] = []
        #     for label in PROBLEM_CLASSIFY[self.REPO][cla]:
        #         self.KNOWLEDGE[cla].append(str(label))
        #         if str(label) not in self.REKNOWLEDGE:
        #             self.REKNOWLEDGE[str(label)] = []
        #         self.REKNOWLEDGE[str(label)].append(cla)

    def read_problem_vector(self):

        def __cal_dis(veca, vecb):
            sum_val = 0
            for i in range(0, self.VEC_CNT):
                sum_val += (veca[i] - vecb[i]) ** 2
            return math.sqrt(sum_val)

        logging("Start read the problem vector file...", 0)
        problem_vector = {}
        with open(self.PROBLEM_VECTOR_FILE, 'r') as file:
            pro_cnt, vec_cnt = map(int, file.readline().split(" "))
            self.VEC_CNT = vec_cnt
            for i in range(0, pro_cnt):
                raw_data = file.readline().split(" ")
                if(len(raw_data) == 1 and raw_data[0] == ""):
                    continue
                problem_vector[raw_data[0]] = map(float, raw_data[1:])

        label_list = problem_vector.keys()
        for label1 in label_list:
            for label2 in label_list:
                if label1 not in self.PROBLEM_RELATION:
                    self.PROBLEM_RELATION[label1] = {}
                dis = __cal_dis(problem_vector[label1], problem_vector[label2])
                self.PROBLEM_RELATION[label1][label2] = dis
                # self.PROBLEM_RELATION[label1][label2] = 0


        logging("Read the problem vector file finish", 0)

    def problem_vector(self):
        logging("Start make problem vector...", 0)
        bks = self.KNOWLEDGE
        mucnt = len(self.USER) * 0.001
        classify_count = self.CLASSIFY.count()
        classify_list = list(self.CLASSIFY)
        for i in range(self.MAX_COUNT):
            self.PROBLEM_VECTOR[i] = [0 for j in range(classify_count)]
        for i in range(classify_count):
            cla = classify_list[i]
            if cla.chinesename in bks:
                cla_bks = bks[cla.chinesename]
            else:
                cla_bks = []
            cla_bks_count = len(cla_bks)
            for j in range(1000, self.MAX_COUNT):
                rela_rat = 0
                rela_cnt = 0
                if str(j) not in self.PROBLEM_RELATION:
                    continue
                for k in range(cla_bks_count):
                    if str(cla_bks[k]) not in self.PROBLEM_RELATION[str(j)]:
                        continue
                    rela_cnt += 1
                    rela_rat += self.PROBLEM_RELATION[str(j)][str(cla_bks[k])]
                self.PROBLEM_VECTOR[j][i] = rela_rat / rela_cnt if rela_cnt else 0.0001
        logging("Make problem vector finish", 0)


    def update_knowledge_dict(self):
        logging("Start update knowledge dict...", 0)
        increase_cnt = 0
        classify_list = list(self.CLASSIFY)
        other_index = 0
        for i in range(len(classify_list)):
            if classify_list[i].chinesename == u'其他':
                other_index = i
                break
        for i in range(1000, self.MAX_COUNT):
            max_rat = 0
            rat_idx = other_index
            for j in range(len(classify_list)):
                if max_rat < self.PROBLEM_VECTOR[i][j]:
                    max_rat = self.PROBLEM_VECTOR[i][j]
                    rat_idx = j
            # print 'label =', i, ', max_rat =', max_rat
            if max_rat >= 0.84:
                if str(i) not in self.REKNOWLEDGE:
                    increase_cnt += 1
                    self.REKNOWLEDGE[str(i)] = []
                if classify_list[rat_idx].chinesename not in self.KNOWLEDGE:
                    self.KNOWLEDGE[classify_list[rat_idx].chinesename] = []
                if str(i) not in self.KNOWLEDGE[classify_list[rat_idx].chinesename]:
                    self.KNOWLEDGE[classify_list[rat_idx].chinesename].append(str(i))
                if classify_list[rat_idx].chinesename not in self.REKNOWLEDGE[str(i)]:
                    self.REKNOWLEDGE[str(i)].append(classify_list[rat_idx].chinesename)

        logging("Update knowledge dict finish", 0)
        return increase_cnt

    def update_problem_classify(self):
        logging("Start update problem classify...", 0)
        Material.classify.through.objects.all().delete()
        for mate in Material.objects.filter(repo=self.REPO):
            if mate.label in self.REKNOWLEDGE:
                for cla in self.REKNOWLEDGE[mate.label]:
                    mate.classify.add(self.CLASSIFY_DICT[cla])
            else:
                mate.classify.add(self.CLASSIFY_DICT[u'其他'])
        logging("Update problem classify finish", 0)


    def classify_problem(self):
        logging("Start classify problems...", 0)
        loop_cnt = 0
        while True:
            self.problem_vector()
            increase_cnt = self.update_knowledge_dict()
            loop_cnt += 1
            logging("loop %d, increase %d problem(s)" %(loop_cnt, increase_cnt), 0)
            if not increase_cnt:
                break
        logging("There are %d problems have been classify" %(len(self.REKNOWLEDGE.keys())), 0)
        self.update_problem_classify()
        logging("Classify problems finish", 0)


def main(repo='Pku'):
    logging("Problem Classify Program Start", 0)

    with connection.cursor() as ues_con:
        # logging("Get all users in %s" % (repo, ), 0)
        # sql = "SELECT `user` FROM `ues_ojstatus` where `repo`=%s group by `user`"
        # ues_con.execute(sql, (repo,))
        # users_tuple = ues_con.fetchall()
        # users_list = list(user[0] for user in users_tuple)
        # sql = "SELECT Max(label) FROM `ues_ojstatus` WHERE `repo`=%s"
        # ues_con.execute(sql, (repo, ))
        # max_label = ues_con.fetchone()[0]
        # logging("There are %d users in the %s DataBase" % (len(users_list), repo), 0)

        # users_list = users_list[0:10]
        users_list = []
        max_label = 4054

        classify = Classify.objects.filter(children=None)
        knowledge = BackgroundKnowledge.objects.filter(repo=repo)
        problem_classify = ProblemClassify(classify, knowledge, repo, users_list, int(max_label)+1)
        # problem_classify.problem_relation()
        # problem_classify.write_problem_relation()
        problem_classify.read_problem_vector()
        # problem_classify.read_problem_vector()
        # problem_classify.print_problem_vector()
        problem_classify.classify_problem()
        # problem_classify.write_problem_vector()

        # problem_classify.update_problem_classify_use_verify_data()

    logging("Problem Classify Program Finish", 0)
