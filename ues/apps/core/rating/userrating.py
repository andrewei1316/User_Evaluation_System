#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import numpy as np
from django.db import connection
from material.models import Material
from django.contrib.auth import get_user_model

class status():
    """docstring for status"""
    # `repo`, `label`, `submitcount`, `isac`
    def __init__(self, item):
        self.repo = item[0]
        self.isac = item[3]
        self.time = item[4]
        self.problem_id = item[1]
        self.submitcount = item[2]


class rmd(object):
    def __init__(self):
        self.DB_STR = {
            'CF': 'CF',
            'ZOJ': 'Zju',
            'POJ': 'Pku',
            'HDU': 'Hdu',
            'Pku': 'Pku',
            'Zju': 'Zju',
            'Hdu': 'Hdu',
        }
        self.REPO_SET = ['Pku', 'Hdu', 'Zju', 'CF']
        self.PROBLEM_MAP = {}
        for item in self.REPO_SET:
            self.PROBLEM_MAP[item] = {}
        material_list = Material.objects.all()
        for mate in material_list:
            self.PROBLEM_MAP[mate.repo][mate.label] = mate.rating

    def get_prating(self, repo, pid):
        return self.PROBLEM_MAP[repo][pid].rating

    def get_prating_all(self):
        prating_ret = []
        for item in self.REPO_SET:
            for k in self.PROBLEM_MAP[item]:
                prating_ret.append({
                    'Repo': item,
                    'ID': k,
                    'level': int(self.PROBLEM_MAP[item][k])
                })
        return prating_ret

    def cal_elo(self, ra, rb, res):
        EA = 1 / (1 + 10 ** ((rb - ra) / 400.0))
        EB = 1 / (1 + 10 ** ((ra - rb) / 400.0))
        KA = KB = SA = SB = 0
        if ra > 2400:
            KA = 3
        elif ra > 1800:
            KA = 6
        else:
            KA = 9
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
            factor = 0.05
        RA = ra + KA * (SA - EA) * factor
        RB = rb + KB * (SB - EB)
        return RA, RB

    def get_elo(self, repo, username):
        ac_arr = []
        rating = 1500.0
        black_hole = 1500
        with connection.cursor() as ues_con:
            sql = """SELECT `repo`, `label`, `submitcount`, `isac`, `submittime`
                    FROM `ues_ojstatus` WHERE `repo`=%s and `user`=%s"""
            ues_con.execute(sql, (repo, username,))
            for item in ues_con.fetchall():
                sta = status(item)
                for i in range(0, sta.submitcount):
                    if sta.problem_id in ac_arr:
                        continue
                    if sta.isac and i == sta.submitcount - 1:
                        ac_arr.append(sta.problem_id)
                        rating, black_hole = self.cal_elo(
                            rating,
                            self.PROBLEM_MAP[repo][sta.problem_id],
                            True
                        )
                    else:
                        rating, black_hole = self.cal_elo(
                            rating,
                            self.PROBLEM_MAP[repo][sta.problem_id],
                            False
                        )
        return rating, ac_arr

    def get_user_info(self, repo, username):
        ac_arr = []
        rating_arr = []
        rating = 1500.0
        black_hole = 1500
        with connection.cursor() as ues_con:
            sql = """SELECT `repo`, `label`, `submitcount`, `isac`, `submittime`
                    FROM `ues_ojstatus` WHERE `repo`=%s and `user`=%s order by `submittime`"""
            ues_con.execute(sql, (repo, username,))
            for item in ues_con.fetchall():
                sta = status(item)
                for i in range(0, sta.submitcount):
                    pm_rating = 1500
                    if sta.problem_id in ac_arr:
                        continue
                    if self.PROBLEM_MAP[repo].get(sta.problem_id):
                        pm_rating = self.PROBLEM_MAP[repo][sta.problem_id]
                    if sta.isac and i == sta.submitcount - 1:
                        ac_arr.append(sta.problem_id)
                        rating, black_hole = self.cal_elo(
                            rating,
                            pm_rating,
                            True
                        )
                    else:
                        rating, black_hole = self.cal_elo(
                            rating,
                            pm_rating,
                            False
                        )
                    rating_arr.append({
                        'rating': rating,
                        'date': str(sta.time)
                    })
        ac_rating_arr = []
        for item in ac_arr:
            pm_rating = 1500
            if self.PROBLEM_MAP[repo].get(sta.problem_id):
                pm_rating = self.PROBLEM_MAP[repo][sta.problem_id]
            ac_rating_arr.append([item, pm_rating])
        return rating, ac_rating_arr, rating_arr

    def get_user_info_group(self, repo, group):
        ret_data = []
        for item in group:
            rating, ac_arr, rating_arr = self.get_user_info(repo, item[1])
            ret_data.append({
                'name': item[0],
                'values': rating_arr
            })
        return ret_data

def get_user_rating_by_repo(user, repo):
    User = get_user_model()
    if isinstance(user, User):
        user = user.username
    rmd_sys = rmd()
    return rmd_sys.get_user_info(repo=repo, username=user)
