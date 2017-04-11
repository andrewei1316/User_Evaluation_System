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
                    self.PROBLEM_RELATION[datas[i].label][datas[j].label][0] += ((j - i) / pro_cnt)
                    self.PROBLEM_RELATION[datas[i].label][datas[j].label][1] += 1
            logging("Statistice user %s status finish" % (user, ), 0)


    def read_result(self):
        logging("Start read the problem relation file...", 0)
        file = open("problem_relation.txt")
        for line in file:
            match = re.search(r'\((\d+), (\d+)\) = (\d+\.\d+)', line)
            x = int(match.group(1))
            y = int(match.group(2))
            v = float(match.group(3))
            self.PROBLEM_RELATION[x][y] = [v, 1]
            # self.PROBLEM_AC_COUNT[x] += v
        file.close()
        logging("Read the problem relation file finish", 0)


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
                if pro[1] < bks_count * 0.65:
                    break
                # print '(', pro[0], ', ', pro[1], ')'
                material = Material.objects.get(repo=self.REPO, label=str(pro[0]))
                material.classify.add(cla)
                # cla.material_set.add(Material.objects.get(repo=self.REPO, label=pro[0]))
            # print '\n\n\n\n'


    def write_result_to_file(self):
        logging("Start write result to file...", 0)
        # file = open("problem_relation.txt", "wb")
        # for i in range(1000, self.MAX_COUNT):
        #     for j in range(i + 1, self.MAX_COUNT):
        #         if self.PROBLEM_RELATION[i][j][1]:
        #             file.write("(%d, %d) = %f\n" % (i, j,
        #                 self.PROBLEM_RELATION[i][j][1] / self.PROBLEM_RELATION[i][j][2]))
        # file.close()
        problem_set = [[] for i in range(self.MAX_COUNT)]
        for i in range(1000, self.MAX_COUNT):
            fi = Find(i)
            problem_set[fi].append(i)
        file = open("problem_classify.txt", "wb")
        for i in range(1000, self.MAX_COUNT):
            fi = Find(i)
            if fi == i:
                for j in problem_set[i]:
                    file.write(str(j) + ' ')
                file.write('\n\n\n\n')
        file.close()
        logging("Write result to file finish", 0)


    def write_to_db(self):
        logging('Update DB Start!', 0)
        with connection.cursor() as ues_con:
            rating_data_list = []
            for label in range(self.MIN_RED, self.MAX_RED + 1):
                rating_data = (0, self.REPO, label, self.PROBLEM_RATING[label])
                rating_data_list.append(rating_data)
                logging('repo: %s, lable: %s, rating: %s' % (
                    self.REPO, label, self.PROBLEM_RATING[label]
                ), 0)

            sql = """INSERT INTO ues_material(`id`, `repo`, `label`, `rating`)
                    VALUES(%s, %s, %s, %s)  ON DUPLICATE KEY UPDATE
                    `rating` = VALUES(`rating`)"""
            ues_con.executemany(sql, rating_data_list)
        logging('Update DB Finish!', 0)


def main(repo='Pku'):
    logging("Problem Classify Program Start", 0)

    with connection.cursor() as ues_con:
        logging("Get all users in %s" % (repo, ), 0)
        # sql = "SELECT `user` FROM `ues_ojstatus` where `repo`=%s group by `user`"
        # ues_con.execute(sql, (repo,))
        # users_tuple = ues_con.fetchall()
        # users_list = list(user[0] for user in users_tuple)
        # sql = "SELECT Max(label) FROM `ues_ojstatus` WHERE `repo`=%s"
        # ues_con.execute(sql, (repo, ))
        # max_label = ues_con.fetchone()[0]
        # logging("There are %d users in the %s DataBase" % (len(users_list), repo), 0)

        users_list = []
        max_label = 4063

        problem_classify = ProblemClassify(repo, users_list, int(max_label)+10)
        # problem_classify.problem_relation()
        problem_classify.read_result()
        problem_classify.classify_problem()
        # problem_classify.write_result_to_file()

    logging("Problem Classify Program Finish", 0)
