#!/usr/bin/env python
# coding: utf-8
__author__ = 'whoami'

"""
@version: 1.0
@author: whoami
@license: Apache Licence 2.0
@contact: skyneteye@gmail.com
@site: http://www.itweet.cn
@software: PyCharm Community Edition
@file: agent.py
@time: 2015-11-28 下午12:44
"""

import threading
from msgpackclient import MsgpackClient
import pickle
import time
from plugins import plugin_api
from log import skynetLog

host_ip = '127.0.0.1'

class MonitorClient(object):

    def __init__(self,server,port):
        self.server = server
        self.prot = port
        self.configs = {}
        self.msgpack = MsgpackClient()
        self.Log = skynetLog()

    def get_configs(self):
        config = self.msgpack.getConfig('HostConfig::%s' % host_ip)
        if config:
            self.configs = pickle.loads(config)
            return True

    def format_msg(self,key,value):
        msg = {key: value}
        return pickle.dumps(msg)

    def handle(self):
        self.report_service_data = {}

        if self.get_configs():
            a = time.time()
            #print 'going to monitor services--',self.configs
            while True:
                for service_name,val in self.configs['services'].items():

                    interval,plugin_name,last_check_time = val

                    if time.time() - last_check_time >= interval:
                        #need to check off the next run
                        t = threading.Thread(target=self.task,args=[service_name,plugin_name])
                        t.start()

                        #update last check time
                        self.configs['services'][service_name][2] = time.time()

                    else:
                        next_run_time = interval-(time.time() - last_check_time)
                        self.Log.info('\033[32;1m %s \033[0m will be run in next \033[32;1m %s \033[0m seconds' %(service_name,next_run_time))

                time.sleep(5)
                if self.report_service_data:

                    print {'report_service_data::%s' %time.strftime('%Y%m%d%H%M') : self.report_service_data.values()}

                    msg = self.format_msg('report_service_data::%s' %time.strftime('%Y%m%d%H%M'),self.report_service_data.values())
                    flag = self.msgpack.push(msg)

                    if flag:
                        self.Log.info('push data success ...')
                    self.report_service_data.clear()
        else:
            self.Log.error('--could not found any configurations for this host....')

    def task(self,service_name,plugin_name):
        self.Log.info('going to run service: %s %s ' %(service_name,plugin_name))
        func = getattr(plugin_api,plugin_name)
        result = func()

        # msg = self.format_msg('report_service_data',
        #                       {'ip':host_ip,
        #                        'service_name':service_name,
        #                         'data':result
        #                         })

        self.report_service_data[service_name]={
                                'ip':host_ip,
                                'service_name':service_name,
                                'data':result
                                }

    def run(self):
        self.handle()


if __name__ == '__main__':
    cli = MonitorClient('yourMonitorServerIp','port')
    cli.run()
