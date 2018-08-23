#!/usr/bin/python
# coding: utf-8
import sys 
sys.path.append('/home/gorbushka/energomera/')
from energomera303 import Counter

nportip=sys.argv[1]
counter_addr=sys.argv[2]
param=sys.argv[3] #'CURRE'

PORT = 4001
HOST = str(nportip) # '10.137.154.143'
TIMEOUT = 5
ADDRESS = str(counter_addr) #'000013'
PARAM=str(param+'()') #'CURRE()'


en = Counter(HOST, PORT, TIMEOUT, True)
en.init(ADDRESS)
result = en.cmd_read(PARAM)
print result
