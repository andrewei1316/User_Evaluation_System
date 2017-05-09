#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import re, time, math
from django.db import connection
from material.models import Material, Classify, BackgroundKnowledge

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
        self.run_id = item[0]
        self.username = item[1]
        self.label = int(item[2])
        self.submitcount = item[3]
        self.submittime = int((item[5]).strftime('%s'))


class ProblemClassify(object):

    def __init__(self, classify, knowledge, repo='Pku', users_list=[], max_label=10000):
        super
        (ProblemClassify, self).__init__()
        self.REPO = repo
        self.KNOWLEDGE = {}
        self.REKNOWLEDGE = {}
        self.USER = users_list
        self.CLASSIFY_DICT = {}
        self.CLASSIFY = classify
        self.MAX_COUNT = max_label
        self.PROBLEM_VECTOR = [[] for i in range(self.MAX_COUNT)]
        self.PROBLEM_RELATION = [{} for i in range(self.MAX_COUNT)]

        for cla in classify:
            self.CLASSIFY_DICT[cla.chinesename] = cla

        for know in knowledge:
            self.REKNOWLEDGE[know.label] = []
            for cla in know.classify.all():
                if cla.chinesename not in self.KNOWLEDGE:
                    self.KNOWLEDGE[cla.chinesename] = []
                self.KNOWLEDGE[cla.chinesename].append(know.label)
                self.REKNOWLEDGE[know.label].append(cla.chinesename)

        from core.classify.verify.verify_data import PROBLEM_CLASSIFY
        for cla in PROBLEM_CLASSIFY[self.REPO]:
            self.KNOWLEDGE[cla] = []
            for label in PROBLEM_CLASSIFY[self.REPO][cla]:
                self.KNOWLEDGE[cla].append(str(label))
                if str(label) not in self.REKNOWLEDGE:
                    self.REKNOWLEDGE[str(label)] = []
                self.REKNOWLEDGE[str(label)].append(cla)

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
        for i in range(1000, self.MAX_COUNT):
            file.write("%d %d\n" % (i, len(list(self.PROBLEM_RELATION[i]))))
            for val in self.PROBLEM_RELATION[i]:
                file.write("%d %.5f %.5f %d\n" % (val, self.PROBLEM_RELATION[i][val][0],
                    self.PROBLEM_RELATION[i][val][1], self.PROBLEM_RELATION[i][val][2]))
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
                label = int(sub_line[0])
                count = int(sub_line[1])
                if count != 0:
                    opt = 2
                    cnt = 0
            else:
                sub_line = line.split(' ')
                tar = int(sub_line[0])
                time_rat = float(sub_line[1])
                dex_rat = float(sub_line[2])
                rat_cnt = int(sub_line[3])
                self.PROBLEM_RELATION[label][tar] = [time_rat, dex_rat, rat_cnt]
                cnt += 1
                if cnt == count:
                    opt = 1
        file.close()
        logging("Read problem relation file finish", 0)


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
                rela_cnt = 0
                rela_rat = 0
                for k in range(cla_bks_count):
                    if int(cla_bks[k]) not in self.PROBLEM_RELATION[j]:
                        continue
                    time_rat = self.PROBLEM_RELATION[j][int(cla_bks[k])][0]
                    dex_rat = self.PROBLEM_RELATION[j][int(cla_bks[k])][1]
                    rela_rat += time_rat * 0.5 + dex_rat * 0.5
                    rela_cnt += self.PROBLEM_RELATION[j][int(cla_bks[k])][2]
                self.PROBLEM_VECTOR[j][i] = rela_rat / rela_cnt if rela_cnt else 0.0001
        logging("Make problem vector finish", 0)


    def read_problem_vector(self):
        logging("Start read the problem relation file...", 0)
        file = open("problem_vector.txt")
        for line in file:
            sub_line = line.split(' :  ')
            label = int(sub_line[0])
            self.PROBLEM_VECTOR[label] = []
            for val in sub_line[1].split(' '):
                self.PROBLEM_VECTOR[label].append(float(val))
        file.close()
        logging("Read the problem relation file finish", 0)


    def write_problem_vector(self):
        logging("Start write problem vector to file...", 0)
        file = open("problem_vector.txt", "wb")
        for i in range(1000, self.MAX_COUNT):
            file.write("%d : " % (i))
            for val in self.PROBLEM_VECTOR[i]:
                file.write(" %.5f" % (val))
            file.write("\n");
        file.close()
        logging("Write problem vector to file finish", 0)


    def print_problem_vector(self):
        logging("Start make problem vector...", 0)
        bks = self.KNOWLEDGE
        classify_count = self.CLASSIFY.count()
        classify_list = list(self.CLASSIFY)
        print '=================', 'background', '===================='
        for i in range(classify_count):
            cla = classify_list[i]
            print '======', i, ': ', cla.chinesename, '======'
            cla_bks = bks[cla.chinesename]
            for cla_bk in cla_bks:
                print cla_bk, self.PROBLEM_VECTOR[int(cla_bk)]
        print '=================', 'problem', '===================='
        for l in range(1000, self.MAX_COUNT):
            print l, self.PROBLEM_VECTOR[l]

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
            # if max_rat >= 0.88 and str(i) not in self.REKNOWLEDGE:
            #     increase_cnt += 1
            #     self.REKNOWLEDGE[str(i)] = []
            #     if classify_list[rat_idx].chinesename not in self.KNOWLEDGE:
            #         self.KNOWLEDGE[classify_list[rat_idx].chinesename] = []
            #     self.KNOWLEDGE[classify_list[rat_idx].chinesename].append(str(i))
            #     self.REKNOWLEDGE[str(i)].append(classify_list[rat_idx].chinesename)
        # print 'label cnt =', len(self.REKNOWLEDGE.keys())
        # for key in self.REKNOWLEDGE:
        #     print 'key =', key, 'cla =', self.REKNOWLEDGE[key]
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
        problem_classify.read_problem_relation()
        # problem_classify.read_problem_vector()
        # problem_classify.print_problem_vector()
        problem_classify.classify_problem()
        # problem_classify.write_problem_vector()

        # problem_classify.update_problem_classify_use_verify_data()

    logging("Problem Classify Program Finish", 0)
