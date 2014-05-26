#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import urllib
from vavava.httputil import HttpUtil
from vavava.httputil import DownloadStreamHandler
from vavava import util

util.set_default_utf8()
LOG = util.get_logger()
CHARSET = "utf-8"


# # depends on xbmc_5ivdo.py
url_m3u8 = r'http://live.3gv.ifeng.com/live/zhongwen.m3u8'
url_root = r'http://live.3gv.ifeng.com/'

def get_location(m3u8):
    results = []
    urls = m3u8.splitlines(False)
    for url in urls:
        if not url.startswith('#'):
            results.append(urllib.basejoin(url_root, url))
    return results

def _recode(duration, o):
    http = HttpUtil(charset="utf-8")
    m3u8 = http.get(url_m3u8)
    urls = get_location(m3u8)
    for url in urls:
        download_handle = DownloadStreamHandler(o, duration)
        http.fetch(url, download_handle)

def start_recode(duration, output):
    LOG.info("[start.... ] %s", util.get_time_string())
    print '\n'
    outfile = os.path.join(output, util.get_time_string() + ".mp4")
    flvfile = open(outfile,"w")
    try:
        start = time.time()
        stop = 0
        if duration > 0:
            stop = duration + start
        while True:
            curr = time.time()
            tt = stop - curr
            if duration > 0 and tt < 0:
                break
            _recode(duration, flvfile)
            print '\r==+%5f:-%5f'%(curr-start, tt)
        LOG.info("[stop..... ] %s", util.get_time_string())
    except:
        LOG.info("[stop1..... ] %s", util.get_time_string())
    finally:
        flvfile.close()

if __name__ == "__main__":
    import getopt
    import sys
    duration = 0
    path = os.path.join(os.environ['HOME'], 'Downloads')
    opts, args = getopt.getopt(sys.argv[1:], "d:p:")
    for k, v in opts:
        if k in ("-d"):
            duration = float(v)
        elif k in ("-p"):
            path = os.path.abspath(v)
    start_recode(duration, path)
