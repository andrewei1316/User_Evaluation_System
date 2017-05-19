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

    def __init__(self, classify, repo='Pku', users_list=[], max_label=10000):
        super
        (ProblemClassify, self).__init__()
        self.REPO = repo
        self.USER = users_list
        self.CLASSIFY = classify
        self.MAX_COUNT = max_label
        self.CLASSIFY_RATIO = []
        self.CLASSIFY_PROBABILITY = []
        self.PROBLEM_VECTOR = [[] for i in range(self.MAX_COUNT)]
        self.PROBLEM_RELATION = [{} for i in range(self.MAX_COUNT)]


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
                self.PROBLEM_RELATION[label][tar] = [time_rat, dex_rat, rat_cnt]
                cnt += 1
                if cnt == count:
                    opt = 1
        file.close()
        logging("Read problem relation file finish", 0)


    def problem_vector(self):
        logging("Start make problem vector...", 0)
        bks = BackgroundKnowledge.objects.all()
        mucnt = len(self.USER) * 0.001
        classify_count = self.CLASSIFY.count()
        classify_list = list(self.CLASSIFY)
        for i in range(self.MAX_COUNT):
            self.PROBLEM_VECTOR[i] = [0] * classify_count
        for i in range(classify_count):
            cla = classify_list[i]
            cla_bks = bks.filter(classify=cla)
            cla_bks_count = cla_bks.count()
            cla_bks_list = list(cla_bks)
            for j in range(1000, self.MAX_COUNT):
                rela_cnt = 0
                rela_rat = 0
                for k in range(cla_bks_count):
                    if int(cla_bks_list[k].label) not in self.PROBLEM_RELATION[j]:
                        continue
                    time_rat = self.PROBLEM_RELATION[j][int(cla_bks[k].label)][0]
                    dex_rat = self.PROBLEM_RELATION[j][int(cla_bks[k].label)][1]
                    rela_rat += time_rat * 0.5 + dex_rat * 0.5
                    rela_cnt += self.PROBLEM_RELATION[j][int(cla_bks[k].label)][2]
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


    def print_problem_vector(self):
        logging("Start make problem vector...", 0)
        bks = BackgroundKnowledge.objects.all()
        classify_count = self.CLASSIFY.count()
        classify_list = list(self.CLASSIFY)
        print '=================', 'background', '===================='
        for i in range(classify_count):
            cla = classify_list[i]
            print '======', i, ': ', cla.chinesename, '======'
            cla_bks = bks.filter(classify=cla)
            for cla_bk in cla_bks:
                print cla_bk.label, self.PROBLEM_VECTOR[int(cla_bk.label)]
        print '=================', 'problem', '===================='
        for l in range(1000, self.MAX_COUNT):
            print l, self.PROBLEM_VECTOR[l]

    def calculate_probability(self):
        logging("Start calculate problem classify probability...", 0)
        classify_count = self.CLASSIFY.count()
        classify_list = list(self.CLASSIFY)
        bks = BackgroundKnowledge.objects.all()
        bks_count = bks.count()
        for classify in classify_list:
            cla = classify.chinesename
            cla_bks = bks.filter(classify=classify)
            cla_bks_count = cla_bks.count()
            self.CLASSIFY_RATIO.append(cla_bks_count / bks_count if bks_count else 0)
            rating_sd = 0
            rating_avg = 0
            classify_probability = []
            rating_sum = [0] * classify_count
            for bk in cla_bks:
                for i in range(classify_count):
                    rating_sum[i] += self.PROBLEM_VECTOR[int(bk.label)][i]
            for i in range(classify_count):
                square_sum = 0
                rating_avg = rating_sum[i] / cla_bks_count if rating_sum[i] else 0.0001
                for bk in cla_bks:
                    square_sum += ((self.PROBLEM_VECTOR[int(bk.label)][i] - rating_avg)
                        * (self.PROBLEM_VECTOR[int(bk.label)][i] - rating_avg))
                square_sum = square_sum / cla_bks_count if square_sum else 0.999
                rating_sd = math.sqrt(square_sum)
                classify_probability.append({
                    'sd': rating_sd,
                    'avg': rating_avg,
                })
            self.CLASSIFY_PROBABILITY.append(classify_probability)

        # print 'cla_ratio =', self.CLASSIFY_RATIO
        # for i in range(classify_count):
        #     print '=============', classify_list[i].chinesename, '=================='
        #     for j in range(classify_count):
        #         print 'cla =', classify_list[j].chinesename, ', avg =', self.CLASSIFY_PROBABILITY[i][j]['avg'], ', sd =', self.CLASSIFY_PROBABILITY[i][j]['sd']
        logging("Calculate problem classify probability finish", 0)

    def classify_problem(self):
        def get_vec_probability(x, item):
            sd = item['sd']
            avg = item['avg']
            coe = 1 / (math.sqrt(2 * math.pi * sd))
            ind = (math.e)**(-((x-avg)*(x-avg)) / (2 * sd * sd))
            return coe * ind

        logging("Start classify problems...", 0)
        classify_list = list(self.CLASSIFY)
        Material.classify.through.objects.all().delete()
        other_index = 0
        for i in range(len(classify_list)):
            if classify_list[i].chinesename == u'其他':
                other_index = i
                break
        for i in range(1000, self.MAX_COUNT):
            max_rat = 0
            rat_idx = other_index
            for j in range(len(classify_list)):
                tmp_rat = 1
                for k in range(len(classify_list)):
                    cla_rating = get_vec_probability(self.PROBLEM_VECTOR[i][k],
                        self.CLASSIFY_PROBABILITY[j][k])
                    tmp_rat *= cla_rating
                if max_rat < tmp_rat * self.CLASSIFY_RATIO[j]:
                    max_rat = tmp_rat * self.CLASSIFY_RATIO[j]
                    rat_idx = j
            #     print 'cla =', classify_list[j], ', tmp_rat =', tmp_rat
            # print 'cla =', classify_list[other_index], ', max_rat =', max_rat
            if max_rat < 1000000:
                rat_idx = other_index
            try:
                material = Material.objects.get(repo=self.REPO, label=str(i))
                material.classify.add(classify_list[rat_idx])
                # logging("label = %d, classify = %s, Done!" %(i, classify_list[rat_idx].chinesename), 0)
            except:
                logging("error: %d DoesNotExist" % (i), 2)
        logging("Classify problems finish", 0)


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

        users_list = []
        max_label = 4054

        classify = Classify.objects.filter(children=None)
        problem_classify = ProblemClassify(classify, repo, users_list, int(max_label)+1)
        # problem_classify.problem_relation()
        # problem_classify.write_problem_relation()
        problem_classify.read_problem_relation()
        problem_classify.problem_vector()
        # problem_classify.write_problem_vector()
        # problem_classify.read_problem_vector()
        # problem_classify.print_problem_vector()
        problem_classify.calculate_probability()
        problem_classify.classify_problem()

        # problem_classify.update_problem_classify_use_verify_data()

    logging("Problem Classify Program Finish", 0)
