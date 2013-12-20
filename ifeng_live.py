#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import hashlib
import json
from vavava.httputil import HttpUtil
from vavava.httputil import DownloadStreamHandler
from vavava import util

class Spider:
    
    CHARSET = r"utf-8"
    SCHEDULE_URL = r'http://v.ifeng.com/live/js/scheduleurls.js?37'
    CID = r'270DE943-3CDF-45E1-8445-9403F93E80C4'
    PAGE_LOCATION = r'http://v.ifeng.com/live/#'+CID

    def __init__(self):
        self.__http = HttpUtil()
        self.__http.header_refer_ = "http://v.ifeng.com/include/ifengLivePlayer_v1.40.4.swf"
        self.__http.header_user_agent_ = r"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)"
        self.__http.add_header("x-flash-version", "11,5,502,146")
        self.__http.add_header("Accept-Language", "zh-CN")
        self.__http.add_header("Accept", "*/*")
        self.__http.add_header("Proxy-Connection", "Keep-Alive")
        self.__uuid = ""
        self.__flv_location = ""
        self.__schedule_json = None
        self.__channels = {}
        self.down_handle = None

    def start_recode(self, channel_name, duration, output='./'):
        ofile=''
        output = os.path.abspath(output)
        if not os.path.isdir(output):
            os.mkdir(output)
        ofile = os.path.join(output, util.get_time_string() + ".flv")
        print "[channel]", channel_name
        uuid = self.__get_uuid(channel_name)
        flv_location = self.__get_flv_location(uuid)
        print "[location]", flv_location
        print "[output]", ofile
        print "[start.... ]", util.get_time_string()
        self.download_handle = DownloadStreamHandler(open(ofile,"w"), duration)
        self.__http.fetch(flv_location, self.download_handle)
        print "[stop..... ]", util.get_time_string()

    def get_channel_info(self):
        data = self.__http.get(self.SCHEDULE_URL)
        tmp = util.reg_helper(data,r'g_scheduelUrl\s=\s(?P<f>.*)}')[0] + '}'
        tmp = tmp.replace("\'","\"").decode(encoding="utf-8")
        js = json.loads(s=tmp, encoding="utf-8")
        for uuid, channel in js.items():
            name = channel['name']
            self.__channels[name] = {'uuid': uuid, 'url': channel['url']}
        self.__schedule_json = tmp
        return self.__channels, self.__schedule_json

    def __get_uuid(self,channel_name):
        self.get_channel_info()
        url = self.__channels[channel_name]['url']
        data = self.__http.get(url)
        html = data.decode(self.CHARSET)
        if html.find(r'uuid=') > 0:
            reg_str = r'uuid=(?P<f>[^|]*)'
        else:
            reg_str = r'http://biz.vsdn.tv380.com/playlive.php\?(?P<f>[^|]*)'
        self.__uuid = util.reg_helper(html,reg_str)[0]
        print "[UUID] ", self.__uuid
        return self.__uuid

    def __get_param(self, uuid):
        time_string = str(int(time.time() + 300))
        hash_string = "ifeng" + "7171537bdc0b95c6a23d9e21ea6615ebet720se2zjw" + time_string + uuid + "1" + "ifenuserid="
        hash_result = hashlib.md5(hash_string).hexdigest()
        param = uuid + "&swax_rt=js&ifenai=ifeng&ifenfg=&ifents=" + time_string + "&ifenv=1&ifensg="\
                + hash_result[5:15] + "&ifenuserid="
        return param

    def __get_flv_location(self, uuid):
        param = self.__get_param(uuid)
        url = r'http://ifenglive.soooner.com/?uuid=%s' % (param)
        data = self.__http.get(url)
        html = data.decode(self.CHARSET)
        reg_str = r'playurl="(?P<f>[^"]*)"'
        self.__flv_location = util.reg_helper(html,reg_str)[0]
        self.__flv_location = url.replace("rtmp://", "http://")
        print "[flv]", self.__flv_location
        data = self.__http.get(self.__flv_location)
        html = data.decode(self.CHARSET)
        reg_str = r'playurl="(?P<f>[^"]*)"'
        self.__flv_location = util.reg_helper(html, reg_str)[0]
        self.__flv_location = self.__flv_location.replace("rtmp://", "http://")
        return self.__flv_location

if __name__ == "__main__":
    import sys
    ifeng = Spider()
    try:
        if len(sys.argv) > 1:
            for i in xrange(0, len(sys.argv)):
                if sys.argv[i] == __file__:
                    channel = u"凤凰中文台"
                    path = os.path.join(os.environ['HOME'], 'Downloads')
                    print u"[%s %.2fs %s]" % (channel, float(sys.argv[i+1]), path)
                    util.SignalHandlerBase(callback=lambda : ifeng.download_handle.syn_stop())
                    ifeng.start_recode(channel, float(sys.argv[i+1]), path)
            print 'end of download work'
        else:
            print ifeng.get_channel_info()[1]
    except KeyboardInterrupt as e:
        ifeng.download_handle.syn_stop()
