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
list_addresses=['000013','000004']
#PARAM=str(param+'()') #'CURRE()'

def zabbix_packet(array):
    packet=[]
    for item in array:
        try:
            host,key,value=item.split()
            packet.append(ZabbixMetric(host + mydockerhost,key,value))
        except:
            pass
    #print packet
    return packet

def date_send():
    pack=zabbix_packet(get_metrics(stats2json(c)))
    sender = ZabbixSender(use_config=True)
    sender.send(pack)
en = Counter(HOST, PORT, TIMEOUT, False)
for addr in list_addresses:
    en.init(addr)
    en.get()
    result = en.cmd('VOLTA()')
    print result
    result = en.cmd('CURRE()')
    print result
    en.get_close()


#en.get()
#print result

#time.sleep(1)
#result = en.cmd_read('VOLTA()')
#print result
