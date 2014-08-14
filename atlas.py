#!/usr/bin/env python
# coding=utf-8

import os
import sys
import time
import threading

from vavava import util
from vavava.spiderutil import SpiderUtil
from vavava.vavava import httputil as http


LOG = util.get_logger()
CONFIG = util.JsonConfig()

class threadpoolhelper:
    def __init__(self, target, alist=None, thread_number=None):
        self.pool = None
        self.target = target
        self.alist = alist
        self.thread_number = thread_number

    def process(self, alist=None, thread_number=None):
        if not alist: alist = self.alist
        if not thread_number: thread_number = self.thread_number
        self._run(alist, thread_number)

    def _run(self, arg_list, thread_number):
        from vavava import threadutil
        self.pool = threadutil.ThreadPool(thread_number)
        requests = threadutil.makeRequests(lambda x: self.target(x), arg_list)
        [self.pool.putRequest(req) for req in requests]
        self.pool.waitForStop()
        print "========== EOF ==========="

    def stop(self):
        if self.pool:
            self.pool.dismissedWorkers()

class Spider:
    def __init__(self):
        self.event = threading.Event()

    def stop(self):
        self.event.set()
        if hasattr(self, 'tasks') and self.tasks:
            self.tasks.stop()

    def get_all(self):
        LOG.info("== start all ==")
        curr_items = []
        util.asure_path(CONFIG.save_path)
        achived_tasks = os.listdir(CONFIG.save_path)
        for id in xrange(CONFIG.deapth):
            try:
                if self.event.isSet(): break
                LOG.info("==> deapth %d", id)
                if id == 0:
                    curr_items = self._get_index_page()
                else:
                    curr_items = self._get_index_page(id, curr_items[:1][0][0])
                for item in curr_items:
                    if item[0] not in achived_tasks:
                        self.get_data(self._get_metadata_url(item[1], item[0]))
            except Exception as e:
                LOG.exception(e)
            LOG.info("<== deapth %d", id)
        LOG.info("== end all ==")

    def get_data_by_id(self, item_id):
        LOG.info("== start get_data_by_id(%s) ==", item_id)
        items = self._get_metadata_url(CONFIG.format_referer%(item_id), item_id)
        for item in items:
            LOG.info(item['url'])
            self._get_metadata(item)
        LOG.info("== end get_data_by_id(%s) ==", item_id)


    def _get_index_page(self, id=None, last=None):
        if id:
            url = CONFIG.format_url % (id, last)
        else:
            url = CONFIG.host
            id = 0
        return [
            (x[x.rfind('/')+1:], x)
            for x in SpiderUtil.get_tags(url, CONFIG.xpath1, CONFIG.attribs1)
        ]

    def _get_metadata_url(self, url, item_id):
        return [
            {
                'url': x,
                'referer': url,
                'path': os.path.join(CONFIG.save_path, item_id)
            } for x in SpiderUtil.get_tags(url, CONFIG.xpath2, CONFIG.attribs2)
        ]

    def _get_metadata(self, arg):
        if self.event.isSet(): return
        url = arg['url']
        referer = arg['referer']
        path = arg['path']
        fp = os.path.join(path, CONFIG.name_format%(hash(url)))
        util.asure_path(os.path.dirname(fp))
        handle = http.DownloadStreamHandler(open(fp, 'w'))
        for kk in [1,2,3]:
            try:
                html = http.HttpUtil(proxy=CONFIG.proxy)
                html.add_header('Referer', referer)
                html.fetch(url, handle)
                break
            except Exception as e:
                LOG.exception(e)
                time.sleep(3)

    def get_data(self, items):
        if CONFIG.thread_number == 1:
            for arg in items:
                if self.event.isSet(): break
                self._get_metadata(arg)
        else:
            self.tasks = threadpoolhelper(self._get_metadata, items)
            self.tasks.process(CONFIG.thread_number)

if __name__ == "__main__":
    import getopt
    opts, args = getopt.getopt(sys.argv[1:], "c:i:")
    cfg_file = __file__[0: __file__.rfind('.')] + r'.json'
    spider = Spider()
    util.SignalHandlerBase(callback=lambda: spider.stop())
    try:
        for k, v in opts:
            if k == "-i":
                spider.get_data_by_id(v)
                exit(0)
            if k == "-c":
                cfg_file = os.path.abspath(v)

        CONFIG = util.JsonConfig(cfg_file, attrs=["proxy"])
        spider.get_all()
    except Exception as e:
        spider.stop()

