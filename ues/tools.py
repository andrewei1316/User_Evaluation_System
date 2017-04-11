#!/usr/bin/env python
# -*- coding: utf-8 -*-

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb, time
from django.db import connection
from django.db import connections
from squads.models import Squads, SquadsUser


def logging(msg, lv):
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MASSAGE", "WARNING", "ERROR  "]
    print lvstr[lv], logtime, ":", msg
    pass


class MigrateFromOJDATA(object):
    def __init__(self, arg=None, MySQL_info=None, quiet=False):
        super
        (MigrateFromOJDATA, self).__init__()
        self.arg = arg
        self.con_ues = connection.cursor()
        self.con = MySQLdb.connect(
            host=MySQL_info["host"],
            user=MySQL_info["user"],
            passwd=MySQL_info["passwd"],
            db=MySQL_info["db"],
            charset=MySQL_info["charset"]
        )
        self.DB = {
            'POJ': 'poj',
            'HDU': 'hdu'
        }
        self.OJ = {
            'POJ': 'Pku',
            'HDU': 'Hdu'
        }
        self.AC = {
            'POJ': 'Accepted',
            'HDU': 'Accepted'
        }


    def insert_data(self, status_data_list, uach_data_list):
        # logging('Insert %s records' % len(status_data_list), 0)
        with connection.cursor() as con_ues:
            # sql = "REPLACE INTO ues_oj_status VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            # con_ues.executemany(sql, status_data_list)
            sql = """INSERT INTO ues_ojstatus (
                        `id`, `runid`, `user`, `repo`, `label`, `submitcount`, `isac`, `submittime`
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE
                    `runid` = IF(`isac`=0, VALUES(`runid`), `runid`),
                    `submitcount` = IF(`isac`=0, `submitcount`+1, `submitcount`),
                    `submittime` = IF(`isac`=0, VALUES(`submittime`), `submittime`),
                    `isac` = IF(`isac`=0, VALUES(`isac`), `isac`)"""
            con_ues.executemany(sql, uach_data_list)
        # logging('Insert %s records Done!' % len(status_data_list), 0)

    def fetch_data(self, start, limit, repo):
        cu = self.con.cursor()
        sql = "select * from `%s_data` limit %d,%d" % (self.DB[repo], start, limit)
        logging("Fetching Data from %d to %d Start..." % (start, start + limit), 0)
        cu.execute(sql)
        logging("Fetching Data from %d to %d Finish" % (start, start + limit), 0)
        return cu.fetchall()

    def read_save_data(self, repo):
        step = 500000
        cu = self.con.cursor()
        logging("Start Migrate Data From %s_data" % self.DB[repo], 0)
        cu.execute("select count(RunID) from `%s_data`" % self.DB[repo])
        DATA_LEN = cu.fetchall()[0][0]
        logging("There are %d records in the DataBase" % DATA_LEN, 0)
        for i in range(0, DATA_LEN / step + 1):
            start_ptr = i * step
            datas = self.fetch_data(start_ptr, step, repo)[:]
            curcnt = 0
            uach_data_list = []
            status_data_list = []
            logging("Start Insert Data!", 0)
            for res in datas:
                is_ac = 1 if res[3] == self.AC[repo] else 0
                uach_data = (0, res[0], res[1], self.OJ[repo], res[2], 1, is_ac, res[8])
                uach_data_list.append(uach_data)

                # status_data = (0, int(res[0]), self.OJ[repo], res[2], res[1], res[6],
                #     res[3], res[5], res[4], res[7], res[8])
                # status_data_list.append(status_data)

                curcnt += 1
                if curcnt == 50:
                    self.insert_data(status_data_list, uach_data_list)
                    curcnt = 0
                    uach_data_list = []
                    status_data_list = []
            if curcnt:
                self.insert_data(status_data_list, uach_data_list)
            logging("Insert Data Finish", 0)
        logging("Migrate Data From %s_data Finish!" % self.DB[repo], 0)
        logging("DELETE Data From %s_data!" % self.DB[repo], 0)
        try:
            cu.execute("DELETE FROM `%s_data`" % self.DB[repo])
        except Exception, ex:
            logging(ex, 2)
        logging("DELETE Finish!", 0)
        pass

def init_cf_problem_rating():
    with connections['onlinejudge_db'].cursor() as oj_con:
        sql = 'SELECT * FROM `fishteam_problems` WHERE `repo`=%s'
        oj_con.execute(sql, ('CF',))
        cf_rating_list = []
        rating_dict = {'A': 1200, 'B': 1400, 'C': 1700, 'D': 2200, 'E': 2600, 'F': 2900}
        for pro in oj_con.fetchall():
            label = pro[2]
            rating = rating_dict[label[-1:]] if label[-1:] in rating_dict else 1500
            cf_rating_list.append((0, 'CF', label, rating))

        with connection.cursor() as ues_con:
            sql = """INSERT INTO `ues_material`(`id`, `repo`, `label`, `rating`)
                    VALUES(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE
                    `rating`=VALUES(`rating`)"""
            ues_con.executemany(sql, cf_rating_list)
    logging('EveryThing Done!', 0)

def init_squads_users():
    users = [
        {'squads': 1L, 'nickname': u'ICErupt', 'user': u'ICErupt', 'name': u'ICErupt'},
        {'squads': 1L, 'nickname': u'Andrewei', 'user': u'DATASOURCE', 'name': u'\u548c\u6811\u4f1f'},
        {'squads': 1L, 'nickname': u'myt', 'user': u'myt', 'name': u'myt'},
        {'squads': 1L, 'nickname': u'MrBird', 'user': u'MrBird', 'name': u'MrBird'},
        {'squads': 1L, 'nickname': u'Baileys', 'user': u'Baileys', 'name': u'Baileys'},
        {'squads': 1L, 'nickname': u'bryant03', 'user': u'bryant03', 'name': u'bryant03'},
        {'squads': 1L, 'nickname': u'fp', 'user': u'fp', 'name': u'fp'},
        {'squads': 1L, 'nickname': u'ShengRang', 'user': u'ShengRang', 'name': u'ShengRang'},
        {'squads': 1L, 'nickname': u'starry2024', 'user': u'starry2024', 'name': u'starry2024'},
        {'squads': 1L, 'nickname': u'undersky', 'user': u'undersky', 'name': u'undersky'}
    ]
    squads = Squads()
    squads.name = 'NJUST_ACM'
    squads.create_user = 'fishhead'
    squads.description = '南京理工大学集训队'
    squads.save()
    for user in users:
        squads_user = SquadsUser()
        squads_user.user = user['user']
        squads_user.name = user['name']
        squads_user.nickname = user['nickname']
        squads_user.squads = squads
        squads_user.save()

def main():
    mig = MigrateFromOJDATA(
        MySQL_info={
            "host": "localhost",
            "user": "root",
            "passwd": "root",
            "db": "OJ_data",
            "charset": "utf8"
        }
    )
    # mig.read_save_data('POJ')
    mig.read_save_data('HDU')
    print 'Everything is Done!'
