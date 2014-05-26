#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import urllib
import re
from time import sleep
from vavava.httputil import HttpUtil
from vavava.httputil import DownloadStreamHandler
from vavava import util

util.set_default_utf8()
LOG = util.get_logger()
pjoin = os.path.join
CHARSET = "utf-8"


# # depends on xbmc_5ivdo.py
url_m3u8 = r'http://live.3gv.ifeng.com/live/zhongwen.m3u8'
url_root = r'http://live.3gv.ifeng.com/'

def get_m3u8_list(m3u8, host):
    results = []
    urls = m3u8.splitlines(False)
    for url in urls:
        if not url.startswith('#'):
            print '===?', url
            results.append(urllib.basejoin(host, url))
    return results

class DownloadLiveStream:
    def _init(self, m3u8_url, duration, output):
        self.m3u8_url = m3u8_url
        self.host = re.match('(^http[s]?://[^/?]*/)', m3u8_url).group(0)
        self.duration = duration
        self.odir = output
        self.start = util.get_time_string()
        self.filter = dict()

    def _recode(self, duration, ofp):
        http = HttpUtil(charset="utf-8")
        m3u8 = http.get(url_m3u8)
        urls = get_m3u8_list(m3u8, host=self.host)
        count = 0
        for url in urls:
            if not self.filter.has_key(url):
                download_handle = DownloadStreamHandler(ofp, duration)
                http.fetch(url, download_handle)
                self.filter[url] = ''
                count += 1
        return count


    def recode(self, url, duration, output):
        self._init(url, duration, output)
        LOG.info("[start.... ] %s", util.get_time_string())
        print '\n'
        try:
            start = time.time()
            stop = 0
            if duration > 0:
                stop = duration + start
            outfile = pjoin(self.odir, util.get_time_string() + ".flv")
            ofp = open(outfile, 'w')
            while True:
                curr = time.time()
                tt = stop - curr
                if duration > 0 and tt < 0:
                    break
                count = self._recode(duration, ofp)
                print 'sleep==>', abs(5-count)*12
                sleep(abs(5-count)*12)
                print '\r==+%5f:-%5f'%(curr-start, tt)
            LOG.info("[stop..... ] %s", util.get_time_string())
        except:
            LOG.info("[stop1..... ] %s", util.get_time_string())
        finally:
            pass

if __name__ == "__main__":
    import getopt
    import sys
    duration = 0
    path = os.path.join(os.environ['HOME'], 'Downloads')
    opts, args = getopt.getopt(sys.argv[1:], "d:p:j:")
    for k, v in opts:
        if k in ("-d"):
            duration = float(v)
        elif k in ("-p"):
            path = os.path.abspath(v)
    DownloadLiveStream().recode(url_m3u8, duration, path)
