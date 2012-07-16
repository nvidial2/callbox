import win32con
from win32file import CreateFile, CloseHandle, WriteFile, ReadFile, DeviceIoControl
from win32file import GENERIC_READ, GENERIC_WRITE, OPEN_EXISTING, PURGE_RXCLEAR
from win32file import SetCommTimeouts, SetCommState, BuildCommDCB, GetCommState, GetCommTimeouts, PurgeComm
from win32api import RegOpenKeyEx, RegCloseKey, RegQueryValueEx, RegSetValueEx, RegEnumValue, RegEnumKeyEx
from win32api import GetFileVersionInfo
import os, sys, string, time, threading, traceback, struct, ctypes, re
import unittest

from util import *

FC_NO = 0
FC_XO = 1
FC_HW = 2

CR_LF = '\r\n'
OK = 'OK' 
ERROR = 'ERROR'
FLAG = '\xF9'
FLAGS = FLAG  * 4
DEFAULT_RESP    = (OK, ERROR)
FLAGS_RESP      = (FLAGS, ERROR)

DEFAULT_TIMEOUT = (10,0,100,0,5000) #(RI, RM, RC, WM, WC)

loop = False

def __callback():
    global loop
    loop = False

    
class SerialPort:
    def __init__(self, port):
        self.__port = port
        self.__handle = None
        
    def initPort(self, rate=115200, bits=8, parity='n', stop=1, timeOuts=DEFAULT_TIMEOUT, flow=FC_HW):
        # timeOuts is tuple(RI, RM, RC, WM, WC):
        # ReadIntervalTimeout, ReadTotalTimeoutMultiplier, ReadTotalTimeoutConstant
        # WriteTotalTimeoutMultiplier, WriteTotalTimeoutConstant
        assert(type(timeOuts) == type(()) and len(timeOuts) == 5)
        ##timeOuts = list(GetCommTimeouts(handle))
        SetCommTimeouts(self.__handle, timeOuts)
        config = str(rate) + ',' + parity + ',' + str(bits) + ',' + str(stop)
        # dcb structure fields:
        # BaudRate, XonLim, XoffLim, ByteSize, Parity, Parity, StopBits, XonChar, XoffChar
        # ErrorChar, EofChar, EvtChar, fBinary, fParity, fOutxCtsFlow, fOutxDsrFlow, fDtrControl 
        # fDsrSensitivity, fTXContinueOnXoff, fOutX, fInX, fErrorChar, fNull, fRtsControl, fAbortOnError
        dcb = GetCommState(self.__handle)
        BuildCommDCB(config, dcb)
        if flow == FC_HW:
            dcb.fOutxCtsFlow = 1
            dcb.fOutxDsrFlow = 0
            dcb.fRtsControl = 2
            dcb.fOutX = 0
            dcb.fInX = 0
        elif flow == FC_XO:
            dcb.fOutxCtsFlow = 0
            dcb.fOutxDsrFlow = 0
            dcb.fOutX = 1
            dcb.fInX = 1
            dcb.XonChar = chr(0x11)
            dcb.XoffChar = chr(0x13)
            dcb.XoffLim = 100
            dcb.XonLim = 100
        else:
            dcb.fOutxCtsFlow = 0
            dcb.fOutxDsrFlow = 0
            dcb.fOutX = 0
            dcb.fInX = 0
        SetCommState(self.__handle, dcb)

    def is_open(self):
        if self.__handle != None:
            return True
        return False

    def open(self):
        log("%s-- Open" % (self.__port))
        if self.__handle != None:
            log('Port \"' + self.__port + '\" already opened!')
            #Alex:
            log("%s-- Force Closing" % (self.__port))            
            CloseHandle(self.__handle)
            self.__handle = None
            raise ERR_OPEN_PORT
        self.__handle = CreateFile('\\\\.\\' + self.__port, GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
        self.initPort(rate=115200)

    def openhidden(self):
        if self.__handle != None:
            CloseHandle(self.__handle)
            self.__handle = None
            raise ERR_OPEN_PORT
        self.__handle = CreateFile('\\\\.\\' + self.__port, GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
        self.initPort(rate=115200)

    def close(self):
        
        if self.__handle == None:
            log("%s-- Al ready closed" % (self.__port))            
        else:
            log("%s-- Close" % (self.__port))            
            CloseHandle(self.__handle)
        self.__handle = None

    def waitResponse(self, hasResponse=DEFAULT_RESP, timeOut=10.0):
        data = ''
        loop = True
        StartTime = time.time()
        TraceTime = StartTime + 1
        StopTime = StartTime + timeOut
        while loop:
            error, byte = ReadFile(self.__handle, 80, None)
            data += byte
            for resp in hasResponse:
                if resp in data:
                    loop = False
            if time.time()>StopTime:
                    loop = False
            if loop and (time.time()>TraceTime):
                sys.stdout.write(".")
                sys.stdout.flush()                    
                TraceTime = TraceTime + 1
        return data

    def sendAT(self, command, hasResponse, timeOut):
        data = ''
        loop = True
        
        if command == '':
            data = self.waitResponse(hasResponse, timeOut)
        else:
            command += CR_LF
            # Turn-around for "at+cmux=0", send byte per byte
            for byte in command:
                error, nbBytes = WriteFile(self.__handle, byte, None)
                if nbBytes != 1:
                    log('Write error!')
                    raise ERR_WRITE_PORT
            if len(hasResponse) > 0:
                data = self.waitResponse(hasResponse, timeOut)
        return data

    def send(self, command, hasResponse=DEFAULT_RESP, timeOut=10.0):
        prefix =  "%s-> " % (self.__port)
        for line in command.splitlines(False):            
            log(prefix+line)
        res = self.sendAT(command, hasResponse, timeOut)
        prefix =  "%s<- " % (self.__port)
        for line in res.splitlines(False):            
            log(prefix+line)
        return res

    def sendhidden(self, command, hasResponse=DEFAULT_RESP, timeOut=10.0):
        #prefix =  "%s-> " % (self.__port)
        #for line in command.splitlines(False):
        #    log(prefix+line)
        res = self.sendAT(command, hasResponse, timeOut)
        #prefix =  "%s<- " % (self.__port)
        #for line in res.splitlines(False):
        #    log(prefix+line)
        return res

    def sendAndCheck(self, command, response_pattern, timeOut=10.0):
        res = self.send(command, hasResponse=DEFAULT_RESP, timeOut=timeOut)
        match = re.search(response_pattern, res)
        res = re.sub('\n', '_n', res)
        res = re.sub('\r', '_r', res)
        if not match:
            errMsg = "ERROR: response '%s' is not matching '%s'" % \
                      (res, response_pattern)
            log(errMsg)
            raise unittest.TestCase.failureException, errMsg #AssertionError, errMsg
        return match

    def sendAndCheckNotPresent(self, command, response_pattern, timeOut=60.0):
        res = self.send(command, hasResponse=DEFAULT_RESP, timeOut=timeOut)
        match = re.search(response_pattern, res)
        res = re.sub('\n', '_n', res)
        res = re.sub('\r', '_r', res)
        position = res.find(response_pattern)
        print position
        if position>0:
            errMsg = "ERROR: response '%s' is  matching '%s'" % \
                      (res, response_pattern)
            log(errMsg)
            raise unittest.TestCase.failureException, errMsg #AssertionError, errMsg
        return match

    def wait_psattach_psdetach(self,type=1,timeout=60):
        #type == 1 to wait for PS attachment
        #        0 to wait for PS detachement
        comment="Failed"
        index=0
        a=time.time()
        b=time.time()
        while (b-a)<=timeout:
            index+=1
            if type==1 and self.is_psattach():
                b=time.time()
                comment="Attach (%d sec)" % (b-a,)
                return True
                break
            elif type==0 and not self.is_psattach():
                b=time.time()
                comment="Detach (%d sec)" % (b-a,)
                return True
                break
            else:
                b=time.time()
                wait(1)
        
        log(comment)
        return False

    def is_psattach(self):
        reponse=self.send('at+cgatt?')
        
        if re.search('CGATT: 1',reponse):
            return True
        else:
            return False

