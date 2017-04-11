#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from django.db import connection

def logging(msg, lv):
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MASSAGE", "WARNING", "ERROR  "]
    print lvstr[lv], logtime, ":", msg


class User():
    """docstring for user"""
    def __init__(self):
        self.ac = []
        self.rating = 1500


class Status():
    """docstring for status"""
    def __init__(self, item):
        self.isac = item[4]
        self.run_id = item[0]
        self.username = item[1]
        self.submitcount = item[3]
        self.problem_id = int(item[2])


class ProblemRatingCal(object):

    def __init__(self, repo='Pku', data_len=0):
        super
        (ProblemRatingCal, self).__init__()
        self.USR = {}
        self.REPO = repo
        self.MAX_RED = 0
        self.MIN_RED = 100000
        self.DATA_LEN = data_len
        self.PROBLEM_RATING = [1500 for i in range(0, 10000)]

    def fetch_data(self, start, limit):
        result = []
        logging("Fetching Data from %d to %d Start..." % (start, start + limit), 0)
        with connection.cursor() as ues_con:
            sql = """SELECT `runid`, `user`, `label`, `submitcount`, `isac`
                    FROM ues_ojstatus WHERE `repo`=%s LIMIT %s, %s"""
            ues_con.execute(sql, (self.REPO, start, start + limit))
            result = ues_con.fetchall()
        logging("Fetching Data from %d to %d Finish" % (start, start + limit), 0)
        return result

    def status_filter(self, data):
        logging("Data Cleaning Start", 0)
        data_arr = []
        for item in data:
            sta = Status(item)
            if not self.USR.get(sta.username):
                self.USR[sta.username] = User()
                data_arr.append(sta)
            else:
                if sta.problem_id not in self.USR[sta.username].ac:
                    self.USR[sta.username].ac.append(sta.problem_id)
                    data_arr.append(sta)
        logging("Data Cleaning Finish", 0)
        return data_arr

    def cal_elo(self, ra, rb, res):
        EA = 1 / (1 + 10 ** ((rb - ra) / 400.0))
        EB = 1 / (1 + 10 ** ((ra - rb) / 400.0))
        KA = KB = SA = SB = 0
        if ra > 2400:
            KA = 10
        elif ra > 1800:
            KA = 15
        else:
            KA = 30
        if rb > 2400 or rb < 600:
            KB = 10
        elif rb > 1900 or rb < 1100:
            KB = 15
        else:
            KB = 30
        if res:
            SA = 1
            SB = 0
            factor = 1
        else:
            SA = 0
            SB = 1
            factor = 0.35
        RA = ra + KA * (SA - EA) * factor
        RB = rb + KB * (SB - EB)
        return RA, RB


    def elo_pro(self):
        step = 500000
        for i in range(0, self.DATA_LEN / step + 1):
            start_ptr = i * step
            datas = self.fetch_data(start_ptr, step)
            datas = self.status_filter(datas)
            logging("Computing the Problem Rating...", 0)
            for sta in datas:
                self.MIN_RED = min(self.MIN_RED, sta.problem_id)
                self.MAX_RED = max(self.MAX_RED, sta.problem_id)
                for sub in range(0, sta.submitcount):
                    try:
                        self.USR[sta.username].rating, self.PROBLEM_RATING[sta.problem_id] =\
                            self.cal_elo(
                                self.USR[sta.username].rating,
                                self.PROBLEM_RATING[sta.problem_id],
                                sta.isac and sub == sta.submitcount - 1
                            )
                    except Exception, ex:
                        print 'sta.runid =', sta.run_id
                        logging(ex, 2)
            logging("Computing the Problem Rating Finish", 0)
        # print PROBLEM_RATING
        pass

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
    logging("ELO Rating System Start", 0)
    logging("Getting the Amount of Data...", 0)

    with connection.cursor() as ues_con:
        sql = "SELECT COUNT(*) FROM `ues_ojstatus` WHERE `repo` = %s"
        ues_con.execute(sql, (repo,))
        data_len = ues_con.fetchone()[0]
        logging("There are %d records in the DataBase" % data_len, 0)

        problem_rating_cal = ProblemRatingCal(repo=repo, data_len=data_len)

        problem_rating_cal.elo_pro()
        problem_rating_cal.write_to_db()

    logging("ELO Rating System Finish", 0)
