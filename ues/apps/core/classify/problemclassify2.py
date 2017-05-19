#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import re, time
from django.db import connection
from material.models import Material, Classify, BackgroundKnowledge

def logging(msg, lv):
    # pass
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MASSAGE", "WARNING", "ERROR  "]
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


class ProblemClassify(object):

    def __init__(self, repo='Pku', users_list=[], max_label=10000):
        super
        (ProblemClassify, self).__init__()
        self.REPO = repo
        self.USER = users_list
        self.MAX_COUNT= max_label
        # self.PROBLEM_AC_COUNT = [0 for i in range(self.MAX_COUNT)]
        self.PROBLEM_RELATION = [{} for i in range(self.MAX_COUNT)]


    def fetch_data(self, user):
        result = []
        with connection.cursor() as ues_con:
            sql = """SELECT `runid`, `user`, `label`, `submitcount`, `isac`
                    FROM ues_ojstatus WHERE `repo`=%s AND `user`=%s AND `isac`=1 ORDER BY `submittime`"""
            ues_con.execute(sql, (self.REPO, user))
            result = ues_con.fetchall()
        return result


    def status_filter(self, data):
        data_arr = []
        for item in data:
            sta = Status(item)
            if sta.isac:
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
                        self.PROBLEM_RELATION[datas[i].label][datas[j].label] = [0, 0]
                    if datas[i].label not in self.PROBLEM_RELATION[datas[j].label]:
                        self.PROBLEM_RELATION[datas[j].label][datas[i].label] = [0, 0]
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
                self.PROBLEM_RELATION[label][tar] = [dex_rat, rat_cnt]
                cnt += 1
                if cnt == count:
                    opt = 1
        file.close()
        logging("Read problem relation file finish", 0)



    def classify_problem(self):
        classify = Classify.objects.all()
        Material.classify.through.objects.all().delete()
        for cla in classify:
            # print 'chinese =', cla.chinesename
            bks = BackgroundKnowledge.objects.filter(classify=cla, repo=self.REPO)
            bks_count = bks.count()
            pro_cnt = {}
            # print '========== bk ============='
            for bk in bks:
                label = int(bk.label)
                material = Material.objects.get(repo=self.REPO, label=label)
                material.classify.add(cla)
                # print label
                pro_list = sorted(
                    self.PROBLEM_RELATION[label].iteritems(), key=lambda x: (x[1][0] / x[1][1]) if x[1][0] else 1)
                for i in range(min(200, len(pro_list))):
                    if pro_list[i][1][0] == 0 or pro_list[i][1][0] / pro_list[i][1][1] > 0.3:
                        break
                    if pro_list[i][0] not in pro_cnt:
                        pro_cnt[pro_list[i][0]] = 1
                    else:
                        pro_cnt[pro_list[i][0]] += 1
            # print '========== bk ============='
            pro_cnt_res = sorted(pro_cnt.iteritems(), key=lambda x: x[1], reverse=True)
            for pro in pro_cnt_res:
                # if pro[1] < bks_count * 0.65:
                #     break
                # print '(', pro[0], ', ', pro[1], ')'
                material = Material.objects.get(repo=self.REPO, label=str(pro[0]))
                material.classify.add(cla)
                # cla.material_set.add(Material.objects.get(repo=self.REPO, label=pro[0]))
            # print '\n\n\n\n'


def main(repo='Pku'):
    logging("Problem Classify Program Start", 0)

    with connection.cursor() as ues_con:
        logging("Get all users in %s" % (repo, ), 0)
        sql = "SELECT `user` FROM `ues_ojstatus` where `repo`=%s group by `user`"
        ues_con.execute(sql, (repo,))
        users_tuple = ues_con.fetchall()
        users_list = list(user[0] for user in users_tuple)
        sql = "SELECT Max(label) FROM `ues_ojstatus` WHERE `repo`=%s"
        ues_con.execute(sql, (repo, ))
        max_label = ues_con.fetchone()[0]
        logging("There are %d users in the %s DataBase" % (len(users_list), repo), 0)

        problem_classify = ProblemClassify(repo, users_list, int(max_label)+1)
        # problem_classify.problem_relation()
        problem_classify.read_problem_relation()
        problem_classify.classify_problem()
        # problem_classify.write_result_to_file()

    logging("Problem Classify Program Finish", 0)
