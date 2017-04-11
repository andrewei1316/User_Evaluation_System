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
        # self.PAR = [i for i in range(self.MAX_COUNT)]
        self.PROBLEM_AC_COUNT = [0 for i in range(self.MAX_COUNT)]
        self.PROBLEM_RELATION = [{} for i in range(self.MAX_COUNT)]


    def fetch_data(self, user):
        result = []
        with connection.cursor() as ues_con:
            sql = """SELECT `runid`, `user`, `label`, `submitcount`, `isac`
                    FROM ues_ojstatus WHERE `repo`=%s AND `user`=%s ORDER BY `submittime`"""
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
            last_label = -1;
            for sta in datas:
                if last_label != -1:
                    if sta.label in self.PROBLEM_RELATION[last_label]:
                        self.PROBLEM_RELATION[last_label][sta.label] += 1
                    else:
                        self.PROBLEM_RELATION[last_label][sta.label] = 1
                    # if last_label < sta.label:
                    #     self.PROBLEM_RELATION[last_label][sta.label][1] += 1
                    # else:
                    #     self.PROBLEM_RELATION[sta.label][last_label][1] += 1
                last_label = sta.label
                self.PROBLEM_AC_COUNT[sta.label] += 1
            logging("Statistice user %s status finish..." % (user, ), 0)


    def classify_problem(self):
        classify = Classify.objects.all()
        Material.classify.through.objects.all().delete()
        for cla in classify:
            print 'chinese =', cla.chinesename
            bks = BackgroundKnowledge.objects.filter(classify__id=cla.id, repo=self.REPO)
            bks_count = bks.count()
            pro_cnt = {}
            print '========== bk ============='
            for bk in bks:
                label = int(bk.label)
                print label
                pro_list = sorted(self.PROBLEM_RELATION[label].iteritems(), key=lambda x: x[1], reverse=True)
                for i in range(min(100, len(pro_list))):
                    if pro_list[i][1] == 0:
                        break
                    if pro_list[i][0] not in pro_cnt:
                        pro_cnt[pro_list[i][0]] = 1
                    else:
                        pro_cnt[pro_list[i][0]] += 1
            print '========== bk ============='
            pro_cnt_res = sorted(pro_cnt.iteritems(), key=lambda x: x[1], reverse=True)
            for pro in pro_cnt_res:
                if pro[1] < bks_count * 0.65:
                    break
                print '(', pro[0], ', ', pro[1], ')'
                material = Material.objects.get(repo=self.REPO, label=pro[0])
                material.classify.add(cla)
                material.save()
            print '\n\n\n\n'


    def read_result(self):
        file = open("problem_relation1.txt")
        for line in file:
            match = re.search(r'\((\d+), (\d+)\) = (\d+)', line)
            x = int(match.group(1))
            y = int(match.group(2))
            v = int(match.group(3))
            self.PROBLEM_RELATION[x][y] = v
            self.PROBLEM_AC_COUNT[x] += v
        file.close()


    def find_and_union(self):
        logging("Start union problem classify...", 0)

        def Find(x):
            # print 'x =', x
            if self.PAR[x] != x:
                self.PAR[x] = Find(self.PAR[x])
            return self.PAR[x]

        def Union(x, y):
            # print 'x =', x, ',y =', y
            fx = Find(x)
            fy = Find(y)
            if fx != fy:
                self.PAR[fy] = fx

        for i in range(1000, self.MAX_COUNT):
            pro_list = sorted(self.PROBLEM_RELATION[i], key=lambda x: x[1], reverse=True)
            # print 'i =', i
            # print pro_list[0:10]
            for j in range(5):
                if (pro_list[j][0] < 1000 or pro_list[j][0] > self.MAX_COUNT) or pro_list[j][1] == 0:
                    continue
                if pro_list[j][1] < self.PROBLEM_AC_COUNT[pro_list[j][0]] / 20:
                    continue
                Union(i, pro_list[j][0])

        logging("Union problem classify finish", 0)


    def write_result_to_file(self):
        # def Find(x):
        #     if self.PAR[x] != x:
        #         self.PAR[x] = Find(self.PAR[x])
        #     return self.PAR[x]

        logging("Start write result to file...", 0)
        file = open("problem_relation1.txt", "wb")
        for i in range(1000, self.MAX_COUNT):
            pro_list = sorted(self.PROBLEM_RELATION[i].iteritems(), key=lambda x: x[1], reverse=True)
            for pro in pro_list:
                file.write("(%d, %d) = %d\n" % (i, pro[0], pro[1]))
        file.close()
        # problem_set = [[] for i in range(self.MAX_COUNT)]
        # for i in range(1000, self.MAX_COUNT):
        #     fi = Find(i)
        #     problem_set[fi].append(i)
        # file = open("problem_classify1.txt", "wb")
        # for i in range(1000, self.MAX_COUNT):
        #     fi = Find(i)
        #     if fi == i:
        #         for j in problem_set[i]:
        #             file.write(str(j) + ' ')
        #         file.write('\n\n\n\n')
        # file.close()
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
        # problem_classify.find_and_union()
        # problem_classify.write_result_to_file()

    logging("Problem Classify Program Finish", 0)
