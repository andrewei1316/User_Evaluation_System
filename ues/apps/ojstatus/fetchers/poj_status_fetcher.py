#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import requests
import datetime
from django.db import connection
from ojstatus.models import OJStatus


def logging(msg, lv):
    ISOTIMEFORMAT = "%Y-%m-%d %X"
    logtime = time.strftime(ISOTIMEFORMAT, time.localtime())
    lvstr = ["MASSAGE", "WARNING", "ERROR  "]
    print 'POJ', lvstr[lv], logtime, ":", msg


class POJ_fetcher(object):
    """docstring for POJ_fetcher"""
    def __init__(self, arg=None, quiet=False):
        super
        (POJ_fetcher, self).__init__()
        self.quiet = quiet
        self.s = requests.Session()
        self.oj = {'POJ': 'Pku', 'AC': 'Accepted', 'CE': 'Compile Error'}
        self.fileds = ['id', 'runid', 'repo', 'label', 'user', 'compiler',
            'status', 'runtime', 'runmemory', 'length', 'submittime']
        self.proxy = ['bnucollect', 'neko13', 'shirin', 'vjudge2', 'vjudge5', 'vjudge1',
            'vjudge3', 'vjudge4', 'do3', 'please3', 'not3', 'me3', 'block3', 'checkoj',
            'username', 'hdujudge6', 'hdujudge7', 'hdujudge4', 'hdujudge2', 'hdujudge10',
            'hdujudge1', 'hdujudge5', 'Longo11070001', 'hdujudge8', 'hdujudge9', 'hdujudge3',
            'nkoj', 'nlgxh0', 'nlgxh1', 'nlgxh2', 'nlgxh3', 'nlgxh4', 'nlgxh5', 'nlgxh6',
            'nlgxh7', 'nlgxh8', 'nlgxh9']
        self.status = ['Compile Error', 'Waiting']

    def fetch_html(self, start_at=1020):
        url = "http://poj.org/status?top=" + str(start_at)
        while True:
            success = True
            logging("Fetch RunID %9d" % start_at, 0)
            try:
                resp = self.s.get(url, timeout=5)
            except Exception, e:
                logging(e, 2)
                success = False
            else:
                logging("status code=%s" % resp.status_code, 0)
                if resp.status_code != 200:
                    success = False
                if re.search(r'Please retry after (?P<time>\d+)ms\.Thank you\.', resp.text):
                    success = False
                    retry_time = re.search(r'Please retry after (?P<time>\d+)ms\.Thank you\.', resp.text).group('time');
                    retry_time = int(retry_time)/1000.0
                    logging("too_often  retry after %.3f s" % retry_time, 1)
                    time.sleep(retry_time)
            if success:
                break
        return resp

    def isLegal(self, data):
        if data['status'] in self.status:
            return False
        if data['user'] in self.proxy:
            return False
        return True

    def fetch(self, start_at=1020):

        resp = self.fetch_html(start_at)
        patternstr = r'''
           <tr\salign=center>
           <td>(?P<runid>\d+)</td>
           <td><a .*?>(?P<user>.*?)</a></td>
           <td><a.*?>(?P<label>\d+)</a></td>
           <td>(<a.*?>)?<font.*?>(?P<status>.*?)</font>(</a>)?</td>
           <td>(?P<runmemory>.*?)</td>
           <td>(?P<runtime>.*?)</td>
           <td>(?P<compiler>.*?)</td>
           <td>(?P<length>.*?)</td>
           <td>(?P<submittime>.*?)</td></tr>
        '''
        pattern = re.compile(patternstr, re.S | re.VERBOSE)
        results = []
        for m in pattern.finditer(resp.text):
            line = {
                'id': 0,
                'runid': int(m.group('runid')),
                'repo': self.oj['POJ'],
                'label': m.group('label'),
                'user': m.group('user'), 
                'status': m.group('status'),
                'runtime': m.group('runtime'),
                'runmemory': m.group('runmemory'),
                'compiler': m.group('compiler'),
                'length': m.group('length'),
                'submittime': m.group('submittime'),
            }
            if self.isLegal(line):
                results.append(line)
        logging("got %d status" % len(results), 0)
        if len(results) == 0:
            return results
        self.insert(results)
        return results

    def insert(self, status):
        status.reverse()
        uach_array = []
        status_array = []
        for s in status:
            # sarr = tuple(s[key] for key in self.fileds)
            is_ac = 1 if s['status'] == self.oj['AC'] else 0
            uarr = (0, s['runid'], s['user'], s['repo'], s['label'], 1, is_ac, s['submittime'])
            uach_array.append(uarr)
            # status_array.append(sarr)
        with connection.cursor() as con_ues:
            # sql = "REPLACE INTO ues_oj_status VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            # con_ues.executemany(sql, status_array)
            sql = """INSERT INTO ues_ojstatus (
                        `id`, `runid`, `user`, `repo`, `label`, `submitcount`, `isac`, `submittime`
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE
                    `runid` = IF(`isac`=0, VALUES(`runid`), `runid`),
                    `submitcount` = IF(`isac`=0, `submitcount`+1, `submitcount`),
                    `submittime` = IF(`isac`=0, VALUES(`submittime`), `submittime`),
                    `isac` = IF(`isac`=0, VALUES(`isac`), `isac`)"""
            con_ues.executemany(sql, uach_array)

    def main(self, begin, end, now_time):
        if begin is None:
            begin = OJStatus.get_max_runid_by_repo(self.oj["POJ"])
            if begin == 0:
                begin = 1020
        if end is None:
            end = begin + 1000 * 10000
        logging(
            'Fetcher begins from runid %s, and will end runid %s or submittime after than now' %
            (begin, end), 0
        )
        for i in xrange(begin, end, 20):
            res = self.fetch(i)
            if len(res) == 0:
                time.sleep(0.5)
                continue
            rcd_time = datetime.datetime.strptime(res[0]["submittime"], "%Y-%m-%d %H:%M:%S")
            logging('Current submittime is %s' % rcd_time, 0)
            if rcd_time >= now_time:
                break
            time.sleep(0.5)

def run_fetcher():
    logging('POJ fetcher start!', 0)
    fetcher = POJ_fetcher(quiet=True)
    fetcher.main(None, None, datetime.datetime.today())
    logging('POJ fetcher stop!', 0)
