#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, time, math
from django.db import connection
from ues.settings import TMP_CHDIR
from gensim.models import word2vec
from core.classify.problem_classifier import logging


class ProblemVector(object):
    def __init__(self, repo, aclist_file, vector_file):
        super
        (ProblemVector, self).__init__()
        self.REPO = repo
        self.USER_ACLIST_FILE = aclist_file
        self.PROBLEM_VECTOR_FILE = vector_file


    def fetch_user_lables(self, user):
        result = ()
        with connection.cursor() as ues_con:
            sql = """SELECT
                GROUP_CONCAT(`label` ORDER BY `submittime` separator ' ')
                FROM `ues_ojstatus`
                WHERE `repo`=%s AND `user` in %s and `isac`=1
                GROUP BY `user`"""
            ues_con.execute(sql, (self.REPO, user))
            result = ues_con.fetchall()
        return result


    def write_user_aclist(self, users_label, filename):
        with open(filename, 'a') as file:
            for labels in users_label:
                file.write(labels[0] + '\n')

    def get_user_aclist(self, step):
        logging("Get all users in %s" % (self.REPO, ), 0)
        users_list = []
        with connection.cursor() as ues_con:
            sql = "SELECT `user` FROM `ues_ojstatus` where `repo`=%s group by `user`"
            ues_con.execute(sql, (self.REPO,))
            users_tuple = ues_con.fetchall()
            users_list = list(user[0] for user in users_tuple)
            sql = "SET GLOBAL group_concat_max_len=%s"
            ues_con.execute(sql, (step*10000,))
            users_tuple = ues_con.fetchone()
        logging("There are %d users in the %s DataBase" % (len(users_list), self.REPO), 0)
        return users_list

    def get_all_user_aclist(self):
        logging("Start get all user aclist...", 0)
        step = 1000
        filename = os.path.join(TMP_CHDIR, '%s_label_list.txt'%(self.REPO, ))
        user_list = self.get_user_aclist(step)
        for i in range(0, len(user_list), step):
            users = user_list[i: i+step]
            users_label = self.fetch_user_lables(users)
            self.write_user_aclist(users_label, self.USER_ACLIST_FILE)
            logging('Users list %d--%d Done!'%(i, i+step), 0)
        logging("Get all user aclist finish", 0)


    def make_problem_vector(self):
        logging("Start make problem vector...", 0)
        sentences = word2vec.Text8Corpus(self.USER_ACLIST_FILE)
        # sentences = word2vec.LineSentence(input_name)
        model = word2vec.Word2Vec(
            sentences = sentences,
            hs = 0,
            sg = 0,
            iter = 10,
            size = 300,
            window = 5,
            sample = 1e-4,
        )
        model.wv.save_word2vec_format(fname=self.PROBLEM_VECTOR_FILE, binary=False)
        logging("Make problem vector finish", 0)

def make_problems_vector(repo, aclist_file, vector_file):
    logging("Make Problems Vectors Main Program Startup...", 0)
    problem_vector = ProblemVector(repo, aclist_file, vector_file)
    problem_vector.get_all_user_aclist()
    problem_vector.make_problem_vector()
    logging("Make Problems Vectors Finish", 0)
