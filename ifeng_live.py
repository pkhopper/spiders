#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import hashlib
import json
from vavava.httputil import HttpUtil
from vavava.httputil import DownloadStreamHandler
from vavava import util

util.set_default_utf8()
LOG = util.get_logger()
CHARSET = "utf-8"

class Spider:

    def __init__(self):
        self.http = HttpUtil(charset="utf-8")
        self.http.header_refer_ = "http://v.ifeng.com/include/ifengLivePlayer_v1.40.4.swf"
        self.http.header_user_agent_ = r"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)"
        self.http.add_header("x-flash-version", "11,5,502,146")
        self.http.add_header("Accept-Language", "zh-CN")
        self.http.add_header("Accept", "*/*")
        self.http.add_header("Proxy-Connection", "Keep-Alive")
        self.uuid = ""
        self.flv_location = ""
        self.schedule_json = None
        self.channels = {}
        self.down_handle = None

    def start_recode(self, channel_name, duration, output='./'):
        output = os.path.abspath(output)
        if not os.path.isdir(output):
            os.mkdir(output)
        outfile = os.path.join(output, util.get_time_string() + ".flv")
        LOG.info("[channel] %s", channel_name)
        uuid = self._get_uuid(channel_name)
        flv_location = self._get_flv_location(uuid)
        LOG.info("[location] %s", flv_location)
        LOG.info("[output] %s", outfile)
        LOG.info("[start.... ] %s", util.get_time_string())
        self.download_handle = DownloadStreamHandler(open(outfile,"w"), duration)
        self.http.fetch(flv_location, self.download_handle)
        LOG.info("[stop..... ] %s", util.get_time_string())

    def get_channel_info(self):
        data = self.http.get(r'http://v.ifeng.com/live/js/scheduleurls.js?37')
        tmp = util.reg_helper(data,r'g_scheduelUrl\s=\s(?P<f>.*)}')[0] + '}'
        tmp = tmp.replace("\'","\"").decode(encoding="utf-8")
        js = json.loads(s=tmp, encoding="utf-8")
        for uuid, channel in js.items():
            name = channel['name']
            self.channels[name] = {'uuid': uuid, 'url': channel['url']}
        self.schedule_json = tmp
        return self.channels, self.schedule_json

    def _get_uuid(self,channel_name):
        self.get_channel_info()
        url = self.channels[channel_name]['url']
        data = self.http.get(url)
        html = data.decode(CHARSET)
        if html.find(r'uuid=') > 0:
            reg_str = r'uuid=(?P<f>[^|]*)'
        else:
            reg_str = r'http://biz.vsdn.tv380.com/playlive.php\?(?P<f>[^|]*)'
        self.uuid = util.reg_helper(html,reg_str)[0]
        LOG.info("[UUID] %s", self.uuid)
        return self.uuid

    def _get_param(self, uuid):
        time_string = str(int(time.time() + 300))
        hash_string = "ifeng" + "7171537bdc0b95c6a23d9e21ea6615ebet720se2zjw" + time_string + uuid + "1" + "ifenuserid="
        hash_result = hashlib.md5(hash_string).hexdigest()
        param = uuid + "&swax_rt=js&ifenai=ifeng&ifenfg=&ifents=" + time_string + "&ifenv=1&ifensg="\
                + hash_result[5:15] + "&ifenuserid="
        return param

    def _get_flv_location(self, uuid):
        param = self._get_param(uuid)
        url = r'http://ifenglive.soooner.com/?uuid=%s' % (param)
        data = self.http.get(url)
        html = data.decode(CHARSET)
        reg_str = r'playurl="(?P<f>[^"]*)"'
        self.flv_location = util.reg_helper(html,reg_str)[0]
        self.flv_location = url.replace("rtmp://", "http://")
        LOG.info("[flv] %s", self.flv_location)
        data = self.http.get(self.flv_location)
        html = data.decode(CHARSET)
        reg_str = r'playurl="(?P<f>[^"]*)"'
        self.flv_location = util.reg_helper(html, reg_str)[0]
        self.flv_location = self.flv_location.replace("rtmp://", "http://")
        return self.flv_location

if __name__ == "__main__":
    import getopt
    import sys

    duration = 0
    channel = u"凤凰中文台"
    path = os.path.join(os.environ['HOME'], 'Downloads')

    opts, args = getopt.getopt(sys.argv[1:], "d:c:p:", [])
    for k, v in opts:
        if k == "-d":
            duration = float(v)
        if k == "-c":
            channel = v
        if k == "-p":
            path = os.path.abspath(v)

    ifeng = Spider()
    try:
        if len(sys.argv) > 1:
            LOG.info(u"[%s %.2fs %s]", channel, duration, path)
            util.SignalHandlerBase(callback=lambda : ifeng.download_handle.syn_stop())
            ifeng.start_recode(channel, duration, path)
            LOG.info(r"end of download work")
        else:
            LOG.info(ifeng.get_channel_info()[1])
    except KeyboardInterrupt as e:
        ifeng.download_handle.syn_stop()
