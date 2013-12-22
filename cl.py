#!/usr/bin/env python
# coding=utf-8

from lxml import etree
import clutil
from vavava import httputil as http
from vavava import util
from vavava import sqliteutil

CONFIG = util.JsonConfig()

class Spider:
    def __init__(self, db_path):
        self.log = util.get_logger(level=CONFIG.log_level)
        self.categries = {}
        self.pool = None
        self.dbpool = sqliteutil.dbpool(path=db_path, cls=clutil.DBUrl)

    def get_page_list(self):
        ht = http.HttpUtil(charset=CONFIG.charset, proxy=CONFIG.proxy)
        html = ht.get(CONFIG.url_indexpage).decode(CONFIG.charset)
        ids = util.reg_helper(html, CONFIG.regular_index)
        for id in ids:
            self.categries[int(id[0])] = id[1]
            self.dbpool.queue_work(clutil.InsertCagegory(int(id[0]), id[1]))
        return self.categries

    def get_pages(self, category, pn):
        self.log.debug('[page] cid=%s pn=%s', category, pn)
        ht = http.HttpUtil(charset=CONFIG.charset, proxy=CONFIG.proxy)
        url = CONFIG.format_infourl % (category, pn)
        html = ht.get(url).decode(CONFIG.charset)
        tree = etree.HTML(html)
        nodes = tree.xpath(r'//*[@id="ajaxtable"]/tbody[1]/tr/td/h3/a')
        for i in xrange(len(nodes)):
            try:
                node = nodes[i]
                post = self.get_post_time(CONFIG.host + node.attrib['href'])
                self.dbpool.queue_work(
                    clutil.Insert(
                        url=clutil.DBRowUrl(
                            node.text, node.attrib['href'], post, int(category)
                        )
                    )
                )
                self.log.debug('[new] %s %s %s %s',
                               node.text, node.attrib['href'], post, category)
            except Exception as e:
                self.log.exception(e)

    def get_post_time(self, url):
        html = http.HttpUtil(proxy=CONFIG.proxy).get(url).decode(CONFIG.charset)
        reg = r'Posted:\s*(?P<tt>\d*[--|-]\d*[--|-]\d*[\s|@]\d*:\d*)'
        return util.reg_helper(html, reg)[0].replace('--', '-').replace('@', ' ')

    def main(self):
        self.get_page_list()
        for cid, name in self.categries.items():
            for i in xrange(CONFIG.page_min, CONFIG.page_max):
                self.get_pages(cid, i)

    def mains(self, thread_number):
        self.get_page_list()
        arglist = []
        for cid, name in self.categries.items():
            for i in xrange(CONFIG.page_min, CONFIG.page_max):
                arglist.append([cid, i])
        from vavava import threadpool
        self.pool = threadpool.ThreadPool(thread_number)
        requests = threadpool.makeRequests(
            lambda argv: self.get_pages(argv[0], argv[1]),
            arglist
        )
        [self.pool.putRequest(req) for req in requests]
        self.pool.wait()
        print "========== EOF ==========="

    def stop(self):
        if self.pool:
            self.pool.dismissedWorkers()
        if self.dbpool:
            self.dbpool.stop()

if __name__ == "__main__":
    cfg_file = __file__[0: __file__.rfind('.')] + r'.json'
    CONFIG = util.JsonConfig(cfg_file, attrs=["proxy"])
    cl = Spider(CONFIG.db_file)
    util.SignalHandlerBase(callback=lambda cl: cl.stop())
    try:
        if CONFIG.task_number == 1:
            cl.main()
        else:
            cl.mains(CONFIG.task_number)
    except Exception as e:
        print e
        cl.stop()

