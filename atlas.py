#!/usr/bin/env python
# coding=utf-8

import os
import threading
from vavava import util
from vavava import json_config
from vavava import httputil as http
from vavava.spiderutil import SpiderUtil

LOG = util.get_logger()
class Config(json_config.SimpleJsonConfig):
    def __init__(self, path):
        path = os.path.abspath(path)
        json_config.SimpleJsonConfig.__init__(self, path)
        LOG.info("load config file:%s", path)
        if not hasattr(self, "http_proxy") or len(self.http_proxy)==0:
            self.http_proxy = None
CONFIG = None

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
        from vavava import threadpool
        self.pool = threadpool.ThreadPool(thread_number)
        requests = threadpool.makeRequests(lambda x: self.target(x), arg_list)
        [self.pool.putRequest(req) for req in requests]
        self.pool.wait()
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
        achived_tasks = os.listdir(CONFIG.save_path)
        for id in xrange(CONFIG.deapth):
            if self.event.isSet(): break
            LOG.info("==> deapth %d", id)
            if id == 0:
                curr_items = self._get_index_page()
            else:
                curr_items = self._get_index_page(id, curr_items[:1][0][0])
            for item in curr_items:
                if item[0] not in achived_tasks:
                    self.get_data(self._get_item_metadata(item[1], item[0]))
            LOG.info("<== deapth %d", id)
        LOG.info("== end all ==")

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

    def _get_item_metadata(self, url, item_id):
        return [
            {
                'url': x,
                'referer': CONFIG.format_referer % (item_id),
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
                html = http.HttpUtil()
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
    global CONFIG
    if os.path.isfile(__file__[0: __file__.rfind('.')] + r'.json'):
        cfg_file = __file__[0: __file__.rfind('.')] + r'.json'
    else:
        cfg_file = None
    CONFIG = Config.parse_config_file_from_argv(Config, cfg_file)
    spider = Spider()
    util.SignalHandlerBase(callback=lambda: spider.stop())
    try:
        spider.get_all()
    except Exception as e:
        LOG.exception(e)
        spider.stop()

