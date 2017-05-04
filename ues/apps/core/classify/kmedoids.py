#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import re, time, math
from django.db import connection
from material.models import BackgroundKnowledge
from material.models import Material as MaterialModel
from material.models import Classify as ClassifyModel

def logging(msg, lv):
    # pass
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MESSAGE", "WARNING", "ERROR  "]
    print "%s %s : %s" %(lvstr[lv], logtime, msg)


class Status():
    """docstring for status"""
    def __init__(self, item):
        self.isac = item[4]
        self.label = item[2]
        self.run_id = item[0]
        self.username = item[1]
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

    def __init__(self, classify, knowledge, repo='Pku', users_list=[], label_list=[], max_label=10000):
        super
        (ProblemClassify, self).__init__()
        self.REPO = repo
        self.CLASSIFY = {}
        self.CLASSIFY_RES = {}
        self.USER = users_list
        self.MEDOIDS_LIST = []
        self.CLASSIFY_LIST = []
        self.PROBLEM_RELATION = {}
        self.LABEL_LIST = label_list

        for cla in classify:
            self.CLASSIFY[cla.codename] = cla
            for sub_cla in cla.children_classify:
                self.CLASSIFY[sub_cla.codename] = sub_cla

        for know in knowledge:
            for cla in know.classify:
                if cla not in self.CLASSIFY_LIST:
                    self.CLASSIFY_LIST.append(cla)
                    self.MEDOIDS_LIST.append(know.label)
                    self.CLASSIFY_RES[know.label] = [know.label]
                else:
                    idx = self.CLASSIFY_LIST.index(cla)
                    medo = self.MEDOIDS_LIST[idx]
                    self.CLASSIFY_RES[medo].append(know.label)

    def fetch_data(self, user):
        result = []
        with connection.cursor() as ues_con:
            sql = """SELECT `runid`, `user`, `label`, `submitcount`, `isac`, `submittime`
                    FROM ues_ojstatus WHERE `repo`=%s AND `user`=%s AND `isac`=1 ORDER BY `submittime`"""
            ues_con.execute(sql, (self.REPO, user))
            result = ues_con.fetchall()
        return result

    def status_filter(self, data):
        data_arr = []
        for item in data:
            sta = Status(item)
            data_arr.append(sta)
        return data_arr

    def problem_relation(self):
        for user in self.USER:
            logging("Statistice user %s status..." % (user, ), 0)
            datas = self.fetch_data(user)
            datas = self.status_filter(datas)
            pro_cnt = len(datas)
            for i in range(pro_cnt):
                for j in range(i + 1, pro_cnt):
                    if datas[j].label not in self.PROBLEM_RELATION[datas[i].label]:
                        self.PROBLEM_RELATION[datas[i].label][datas[j].label] = [0, 0, 0]
                    if datas[i].label not in self.PROBLEM_RELATION[datas[j].label]:
                        self.PROBLEM_RELATION[datas[j].label][datas[i].label] = [0, 0, 0]
                    try:
                        time_rat = 1 - (datas[j].submittime - datas[i].submittime) / (
                            datas[pro_cnt - 1].submittime - datas[0].submittime)
                    except:
                        time_rat = 1
                    dex_rat = 1 - (j - i) / pro_cnt
                    self.PROBLEM_RELATION[datas[i].label][datas[j].label][0] += time_rat
                    self.PROBLEM_RELATION[datas[i].label][datas[j].label][1] += dex_rat
                    self.PROBLEM_RELATION[datas[i].label][datas[j].label][2] += 1
                    self.PROBLEM_RELATION[datas[j].label][datas[i].label][0] += time_rat
                    self.PROBLEM_RELATION[datas[j].label][datas[i].label][1] += dex_rat
                    self.PROBLEM_RELATION[datas[j].label][datas[i].label][2] += 1
            logging("Statistice user %s status finish" % (user, ), 0)

    def write_problem_relation(self):
        logging("Start write problem relation to file...", 0)
        file = open("problem_relation.txt", "wb")
        for label in self.LABEL_LIST:
            if label in self.PROBLEM_RELATION:
                tar_labels = self.PROBLEM_RELATION[label].keys()
                tar_labels.sort()
                file.write("%d %d\n" % (label, len(tar_labels)))
                for tar in tar_labels:
                    file.write("%d %.5f %.5f %d\n" % (tar, self.PROBLEM_RELATION[label][tar][0],
                        self.PROBLEM_RELATION[label][tar][1], self.PROBLEM_RELATION[label][tar][2]))
        file.close()
        logging("Write problem relation to file finish", 0)

    def read_problem_relation(self):
        logging("Start read problem relation file...", 0)
        file = open("problem_relation.txt")
        opt = 1
        cnt = 0
        count = 0
        label = 1000
        for line in file:
            if opt == 1:
                sub_line = line.split(' ')
                label = sub_line[0]
                count = int(sub_line[1])
                if count != 0:
                    opt = 2
                    cnt = 0
            else:
                sub_line = line.split(' ')
                tar = sub_line[0]
                time_rat = float(sub_line[1])
                dex_rat = float(sub_line[2])
                rat_cnt = int(sub_line[3])
                if label not in self.PROBLEM_RELATION:
                    self.PROBLEM_RELATION[label] = {}
                self.PROBLEM_RELATION[label][tar] = [time_rat, dex_rat, rat_cnt]
                cnt += 1
                if cnt == count:
                    opt = 1
        file.close()
        logging("Read problem relation file finish", 0)

    def __calculate_total_cost(self):
        totalcost = 0.0
        classify_res = {}
        for medo in self.MEDOIDS_LIST:
            classify_res[medo] = []
        for label in self.LABEL_LIST:
            min_medo = None
            min_cost = 100000
            for medo in self.MEDOIDS_LIST:
                try:
                    pro_cnt = self.PROBLEM_RELATION[medo][label][2]
                    dex_rat = self.PROBLEM_RELATION[medo][label][1]
                    time_rat = self.PROBLEM_RELATION[medo][label][0]
                    cost = 1 - (time_rat * 0.5 + dex_rat * 0.5) / pro_cnt
                except Exception, ex:
                    cost = 100000
                if cost < min_cost:
                    min_medo = medo
                    min_cost = cost
            if min_medo == None:
                continue
            classify_res[min_medo].append(label)
            totalcost += min_cost
        return totalcost, classify_res

    def classify_problem(self):
        def __save_temp_result_to_file():
            file = open("k-medoids.txt", "wb")
            file.write("%d\n" % (len(self.CLASSIFY_LIST)))
            for i in range(len(self.CLASSIFY_LIST)):
                medo = self.MEDOIDS_LIST[i]
                length = len(self.CLASSIFY_RES[medo])
                file.write("%s %s %d\n" %(self.CLASSIFY_LIST[i], medo, length))
                for j in range(length):
                    file.write("%s " %(self.CLASSIFY_RES[medo][j]))
                file.write("\n")
            file.close()

        logging("Start classify problems...", 0)
        # pre_cost, self.CLASSIFY_RES = self.__calculate_total_cost(self.MEDOIDS_LIST)
        pre_cost = 100000
        medoids_res = []
        classify_res = {}
        cur_cost = 100000
        loop_cnt = 0
        medo_len = len(self.MEDOIDS_LIST)
        while True:
            for idx in range(medo_len):
                medo = self.MEDOIDS_LIST[idx]
                for label in self.CLASSIFY_RES[medo]:
                    if medo == label: continue
                    self.MEDOIDS_LIST[idx] = label
                    tmp_cost, medoids_ = self.__calculate_total_cost()
                    logging("idx = %02d, label = %s, cost = %03d" % (idx, label, tmp_cost), 0)
                    if tmp_cost < cur_cost:
                        cur_cost = tmp_cost
                        classify_res = dict(medoids_)
                        medoids_res = list(self.MEDOIDS_LIST)
                    self.MEDOIDS_LIST[idx] = medo
            loop_cnt += 1
            __save_temp_result_to_file()
            if medoids_res == self.MEDOIDS_LIST:
                logging("Loop %d, loop end!" %(loop_cnt, ), 0)
                break
            if cur_cost <= pre_cost:
                pre_cost = cur_cost
                self.CLASSIFY_RES = classify_res
                self.MEDOIDS_LIST = medoids_res
            logging("Loop %d, cost = %d" %(loop_cnt, pre_cost), 0)

        logging("Classify problems finish", 0)

    def read_classify_from_file_update_db(self):
        file = open("k-medoids.txt", "r")
        self.MEDOIDS_LIST = []
        self.CLASSIFY_LIST = []
        classify_cnt = int(file.readline())
        for i in range(classify_cnt):
            line = file.readline()[:-1]
            data = line.split(' ')
            if data == ['']: continue
            self.CLASSIFY_LIST.append(data[0])
            self.MEDOIDS_LIST.append(data[1])
            label_cnt = int(data[2])
            if not label_cnt: continue
            self.CLASSIFY_RES[data[1]] = file.readline()[:-1].split(' ')
            self.CLASSIFY_RES[data[1]].append(data[1])
        file.close()
        self.update_problem_classify()


    def update_problem_classify(self):
        logging("Start update problem classify...", 0)
        problem_classify = {}
        for cla in self.CLASSIFY_LIST:
            idx = self.CLASSIFY_LIST.index(cla)
            medo = self.MEDOIDS_LIST[idx]
            classify = self.CLASSIFY[cla].classify_model
            for label in self.CLASSIFY_RES[medo]:
                problem_classify[label] = classify

        MaterialModel.classify.through.objects.all().delete()
        other_classify = self.CLASSIFY['others_sub'].classify_model
        for meta in MaterialModel.objects.filter(repo=self.REPO):
            try:
                classify = problem_classify[meta.label]
            except Exception, ex:
                classify = other_classify
            meta.classify.add(classify)

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

    with connection.cursor() as ues_con:
        logging("Get all users in %s" % (repo, ), 0)
        sql = "SELECT `user` FROM `ues_ojstatus` where `repo`=%s group by `user`"
        ues_con.execute(sql, (repo,))
        users_tuple = ues_con.fetchall()
        users_list = list(user[0] for user in users_tuple)
        sql = "SELECT `label` FROM `ues_ojstatus` WHERE `repo`=%s group by `label`"
        ues_con.execute(sql, (repo, ))
        label_tuple = ues_con.fetchall()
        label_list = sorted(list(label[0] for label in label_tuple))
        logging("There are %d users and %d labels in the %s DataBase" % (
            len(users_list), len(label_list), repo), 0)

        classify = []
        classify_model = ClassifyModel.objects.exclude(children=None)
        for cla in classify_model:
            child_cla = []
            children = cla.children.all()
            for child in children:
                child_item = Classify([child.codename, child.chinesename, [], child])
                child_cla.append(child_item)
            item = Classify([cla.codename, cla.chinesename, child_cla, cla])
            classify.append(item)

        knowledge = []
        knowledge_model = BackgroundKnowledge.objects.filter(repo=repo)
        for know in knowledge_model:
            know_cla = []
            for cla in know.classify.all():
                know_cla.append(cla.codename)
            knowledge.append(Knowledge([know.repo, know.label, know_cla]))

        problem_classify = ProblemClassify(classify, knowledge, repo, users_list, label_list)
        # problem_classify.problem_relation()
        # problem_classify.write_problem_relation()
        # problem_classify.read_problem_relation()
        # problem_classify.read_problem_vector()
        # problem_classify.print_problem_vector()
        # problem_classify.classify_problem()
        # problem_classify.write_problem_vector()

        problem_classify.read_classify_from_file_update_db()

        # problem_classify.update_problem_classify_use_verify_data()

    logging("Problem Classify Program Finish", 0)


