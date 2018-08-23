#!/usr/bin/python
# coding: utf-8
#https://github.com/adubkov/py-zabbix
from pyzabbix import ZabbixMetric, ZabbixSender
import sys,time
sys.path.append('/home/gorbushka/energomera/')
from energomera303 import Counter


PORT = 4001
HOST =  '10.137.154.143'
TIMEOUT = 5
ADDRESS = '000013'
#PARAM=str(param+'()') #'CURRE()'


en = Counter(HOST, PORT, ADDRESS, TIMEOUT, True)
en.get()
result = en.cmd('VOLTA()')
print result
result = en.cmd('CURRE()')
print result
#en.get()
#print result

#time.sleep(1)
#result = en.cmd_read('VOLTA()')
#print result
