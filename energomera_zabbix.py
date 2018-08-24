#!/usr/bin/python
# coding: utf-8
#https://github.com/adubkov/py-zabbix
from pyzabbix import ZabbixMetric, ZabbixSender
import sys,time
sys.path.append('/home/gorbushka/energomera/')
from energomera303 import Counter


PORT = 4001
HOST =  '10.137.154.143'
TIMEOUT = 10
ADDRESS = '000013'
list_addresses=['000013','000004']
en = Counter(HOST, PORT, TIMEOUT, False)
f3=['A','B','C']
f4=['module','A','B','C']
fIO=['I','O']
#list_cmds={'VOLTA()':f3,'CURRE()':f3,'POWPP()':f3,'POWPQ()':f3,'COS_f()':f4,'POWEP()':fIO,'POWEQ()':fIO}
list_cmds={'VOLTA()':f3,'CURRE()':f3,'POWPP()':f3,'POWPQ()':f3,'COS_f()':f4}
oarray=[]

def zabbix_packet(array):
    packet=[]
    for item in array:
        try:
            host=item[0]
            key=item[1]
            value=item[2]
            packet.append(ZabbixMetric('Energomera_' + host,key,value))
        except Exception, error:
            print 'Error array', error
            pass
#    print packet
    return packet

def get_param(n_arg,param):
    try:
        result = en.cmd(param)
        d=dict(zip(n_arg,result))
    except Exception, error:
        print 'not connect', error
    return d

def result2array(list_cmd):
    for param_cmd in list_cmd.items():
        param=param_cmd[0]
        num_arg=param_cmd[1]
        out=get_param(num_arg,param)
        print out
        if len(out) > 0:
            for ph in num_arg:
                try: 
                    z_key=param[:len(param)-2].lower()+'['+ph+']'
                    oarray.append([addr,z_key,out[ph]])
                except Exception, error:
                    print 'Error array', error    

for addr in list_addresses:
    en.init(addr)
    en.get()
    oarray.append(result2array(list_cmds))
    en.get_close()
    time.sleep(1)
    
#oarray=[[addr,'CURR[A]',dict_curr['A']],
#       [addr,'CURR[B]',dict_curr['B']],
#       [addr,'CURR[C]',dict_curr['C']],
#       ]

#print oarray
pack=zabbix_packet(oarray)
sender = ZabbixSender(use_config=True)
sender.send(pack)
