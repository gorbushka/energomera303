#!/usr/bin/python
# coding: utf-8
#fork from https://github.com/sinyawskiy/energomera102m
#https://github.com/velsi/rs485/blob/master/counter.py
# Semikin@powernet
import re
import socket
import time
import sys


def upper_hex(byte):
    r"""
    >>> upper_hex('\x00')
    '00'
    >>> upper_hex(0x0)
    '00'
    >>> upper_hex(5)
    '05'
    """
    if isinstance(byte, str):
        byte = ord(byte)
    return '%02X' % byte


def pretty_hex(byte_string):
    r"""
    >>> pretty_hex('Python')
    '50 79 74 68 6F 6E'
    >>> pretty_hex('\x00\xa1\xb2')
    '00 A1 B2'
    >>> pretty_hex([1, 2, 3, 5, 8, 13])
    '01 02 03 05 08 0D'
    """
    return ' '.join(upper_hex(c) for c in byte_string)



def decode(result_byte_array):
    result = ''
    for item in result_byte_array:
        bit = bin(item)[2:].zfill(8)[1:]
        result += chr(int(bit, 2))
    return result


class Counter:
    #Init string for Energomera's counter
    _CMD_INIT = [0x2F, 0x3F] # / ?
    _CMD_POST_INIT = [0x21] # !
    _CMD_SOHR= [0x01, 0x52, 0x31, 0x02] # SOH R 1 STX
    
    _CMD_CLOSE = [0x1, 0x42, 0x30, 0x3] # '\x01B0\x03'

    #End of line \r\n
    _EOL = [0x0D, 0x0A]
    _ETX = [0x03]

    # Brand of counter
    brand = ''

    # Debug flag
    debug = False

    # Init flag
    _init = ''

    def __init__(self, host, port, timeout=5, debug=False):
        self.Z = 5
        #self.address = list(bytearray(b'%d'%address)) if address else []
        self.port = port
        self.host = host
        self.timeout = timeout
        self.debug = debug
        # 8-n => 7-1
        self.parity_lookup = [self.parallel_swar(i) for i in range(256)]
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
    

    # Needed for parity
    def parallel_swar(self, i):
        i = i - ((i >> 1) & 0x55555555)
        i = (i & 0x33333333) + ((i >> 2) & 0x33333333)
        i = (((i + (i >> 4)) & 0x0F0F0F0F) * 0x01010101) >> 24
        return int(i % 2)

    # Count parity
    def parity(self, v):
        v = int(v)
        v ^= v >> 16
        v ^= v >> 8
        return str(self.parity_lookup[v & 0xff])

    # Add parity bit to 7-bit data
    def encode(self, data):
        return int(self.parity(data) + bin(int(data))[2:].zfill(7), 2)

    # Remove patity bit
    def decode(self, ch):
        bit = bin(ord(ch))[2:].zfill(8)[1:]
        return chr(int(bit, 2))

    # Write-mode cmd
    def getCmdWriteMode(self):
        return [0x06, 0x30, 0x35, 0x31] + self._EOL # ACK 0 Z 1 CR LF

    # Read-mode cmd
    def getCmdReadMode(self):
        return [0x06, 0x30, self.Z, 0x30] + self._EOL # ACK 0 Z 0 CR LF считывания данных

    def getCmdModReadMode(self):
        return [0x06, 0x30, 0x35, 0x30] + self._EOL # ACK 0 Z 0 CR LF считывания данных

    # Quick-mode cmd (Energomera only ??)
    def getCmdQuickReadMode(self):
        return [0x06, 0x30, self.Z, 0x36] + self._EOL # ACK 0 Z 6 CR LF чтения фиксированного набора параметров

    def getTest(self):
        #              01 52 31 02 49 44 45 4E 54 28 29 03 4D
        return [0x01, 0x52, 0x31, 0x02,0x49, 0x44, 0x45, 0x4E, 0x54, 0x28, 0x29, 0x03, 0x4D] # ACK 0 Z 6 CR LF чтения фиксированного набора параметров


    def close(self):
        return self._CMD_CLOSE + self.get_lrc(self._CMD_CLOSE)

    def readSocket(self, incmd, getflag=0):
        #print getflag
        _encoded_cmd = ''
        _encoded = []
        _cmd = ''
        _response = []
        for bit in incmd:
            _encoded.append(self.encode(bit))
            _cmd += chr(int(bit))

        for bit in _encoded:
            _encoded_cmd += chr(int(bit))

        if self.debug:
            print '>> request', pretty_hex(incmd), _cmd
            print '>> encoded7', pretty_hex(_encoded), _encoded_cmd

        self.socket.sendall(_encoded_cmd)
        _data = ''
        _decoded_data = ''
        _buffer = ''
        try:
            while True:
                self.socket.settimeout(self.timeout)
                _data = self.socket.recv(1)
                if _data:
                    _decoded_data = self.decode(_data)
                    _buffer += _decoded_data
                    #print _cmd, len(_buffer), _buffer[-2:-1],pretty_hex(_buffer), str(bytearray(self._EOL))
                    if getflag==1:
                        if len(_buffer)>11 and _buffer[-2:] == str(bytearray(self._EOL)):
                            break
                    else:
                        if len(_buffer)>2:
                            if (bytearray(_cmd)==bytearray(self.getCmdWriteMode()) and _buffer[-2:-1] == str(bytearray(self._ETX))):
                                break
                            if _buffer[-4:-1] == str(bytearray(self._EOL+self._ETX)):
                                break
                            if (bytearray(_cmd)==bytearray(self.close()) and _buffer[-2:-1] == str(bytearray(self._ETX))):    
                                break
                                self.socket.close()
 
        except Exception, error:
            print 'Read data', error

        self.socket.settimeout(None)

        if self.debug:
            print '<< response', pretty_hex(_buffer),_buffer
        return _buffer

    def get_lrc(self, message_byte_array):
        message = str(bytearray(message_byte_array))
        lrc = 0x00
        lrc_add = False
        for i in range(0, len(message)):
            if message[i] == '\x01':
                lrc_add = True
            elif message[i] == '\x02':
                if lrc_add:
                    lrc = (lrc + ord(message[i])) & 0x7f
                else:
                    lrc_add = True
            elif message[i] == '\x03':
                lrc_add = False
                lrc = (lrc + ord(message[i])) & 0x7f
            else:
                if lrc_add:
                    lrc = (lrc + ord(message[i])) & 0x7f
        return [lrc]

    # Init connection
    def init(self, address=True):
        bitaddress=[]
        for ch in address:
             bitaddress.append(ord(ch))
        self.address=list(bytearray(bitaddress))
        if address:
            init = self.readSocket(self._CMD_INIT + self.address + self._CMD_POST_INIT + self._EOL,1)
        else:
            init = self.readSocket(self._CMD_INIT + self._CMD_POST_INIT + self._EOL)
        if init:
            self._init = True
            self.brand = init[1:4]
            self.Z = ord(str(init[4]))
        else:
            self._init = False

    # Get value of some counters
    def get(self):
        #res1 = self.readSocket(self.getCmdReadMode()) # init read mode
        #self.init()
        #cmd_close = self.close()
        #print cmd_close, pretty_hex(cmd_close)
        #res2 = self.readSocket(self.getCmdQuickReadMode()) # quick read
        #self.init()
        #res2 = self.readSocket(self.getCmdModReadMode()) # read
        res2 = self.readSocket(self.getCmdWriteMode()) # write
        #res2 = self.readSocket(self.getTest()) # read
        return res2
    def get_close(self):
        res = self.readSocket(self.close())
        return res
    # Parse value from answer (xx.xx)
    def getValue(self, answer):
        try:
            #value = map(float, re.findall('\((\d+.\d+)', answer))
            value = map(str, re.findall('\((-?\d+.\d+)', answer)) #work with positive
            #value = map(str, re.findall('\((.*)\)', answer))
        except:
            value=answer  
        #value = map(float, re.findall('\((\d+.\d+)', answer))
        #value=answer
        if len(value) == 1:
            value = value[0]
        return value

    # Command mode
    def cmd(self, incmd):
        _cmd = [0x01, 0x52, 0x31, 0x02]  # SOH R 1 STX
        for ch in incmd:
            _cmd.append(ord(ch))
        _cmd += self._ETX
        _cmd += self.get_lrc(_cmd)
        answer = self.readSocket(_cmd)
        res = self.getValue(answer)
#         pprint(res)
        return res
    # out off session read
    def cmd_read(self, cmd):
        _cmd =  self._CMD_INIT 
        _cmd += self.address
        _cmd += self._CMD_POST_INIT    
        _cmd += self._CMD_SOHR # SOH R 1 STX
        for ch in cmd:
            _cmd.append(ord(ch))
        _cmd += self._ETX
        _cmd += self.get_lrc(_cmd)
        answer = self.readSocket(_cmd)
        res = self.getValue(answer)
#         pprint(res)
        return res
    
     
    # Switch mode
    def mode(self, mode):
        if (mode == 'w'):
            confirm = self.readSocket(self.getCmdWriteMode())

