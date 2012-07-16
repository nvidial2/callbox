#-------------------------------------------------------------------------------
# Name:        Cardhu
# Purpose:
#
# Author:      Administrator
#
# Created:     10/07/2012
# Copyright:   (c) Administrator 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import sys, time, os, os.path, threading, subprocess, re, locale,shutil
import common
import socket

class Cardhu():

    def send_cmd(self,cmd,dev = 'at'):
        try:
            if dev == 'modem':
                port = common.CARDHU_MODEM_PORT
            else:
                port = common.CARDHU_AT_PORT

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((common.CARDHU_IP_ADDR,int(port)))
            self.sock.send(cmd+'\r\n')
            time.sleep(1)
            data = self.sock.recv(1024)
            if data:
                if re.search(re.compile(r'OK'),data):
                    return data
        except:
            pass

        return "ERROR"


    def sendhidden(self,cmd):
        self.sock.send(cmd+'\r\n')
        #time.sleep(0.3)
        data = self.sock.recv(1024)
        if data:
            #print cmd
            print data
            return data
        else:
            return "ERROR"

    def send(self,cmd):
        self.sock.send(cmd+'\r\n')
        #time.sleep(0.3)
        data = self.sock.recv(1024)
        if data:
            #print cmd
            print data
            return data
        else:
            return "ERROR"

    def close(self):
        self.sock.close()

    def is_open(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((common.CARDHU_IP_ADDR,int(common.AT_PORT)))
            self.sock.send('AT\r\n')
            print "send AT Command"
            time.sleep(1)
            data = self.sock.recv(1024)
            if data:
                if re.search(re.compile(r'OK'),data):
                    print "Open Socket Success"
                    print data
                    return True
        except:
            pass

        return False

    def openhidden(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((common.CARDHU_IP_ADDR,int(common.AT_PORT)))
        self.sock.send('AT\r\n')
        print "send AT Command"
        time.sleep(1)
        data = self.sock.recv(1024)
        if data:
            if re.search(re.compile(r'OK'),data):
                print "Open Socket Success"
                print data

class Cardh_ctrl :

    def send_cmd(self,cmd):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((common.CARDHU_IP_ADDR,common.CARDHU_CTRL_PORT))
            sock.send(cmd+'\r\n')
            time.sleep(0.3)
            data = sock.recv(1024)
            sock.close()
            #print "Response",data
            if data == 'True':
                return True
            if data == 'False':
                return False
            return data
        except:
            return False


def main():
    iCtrl = Cardh_ctrl()
    #iCtrl.open_socket()
    #iCtrl.send_cmd('ftp_downlink_stream1')
   # time.sleep(30)
    #print int(float(iCtrl.send_cmd('get_throughput_dl_stream1')))

    iCtrl.send_cmd('restart')
    return
    throughput_DL= float(iCtrl.send_cmd('get_throughput_dl_stream1'))
    print "self.throughput_DL",throughput_DL
    size_DL = float(iCtrl.send_cmd('get_size_dl_stream1'))
    print "self.size_DL",size_DL
    time.sleep(5)
    throughput_DL += float(iCtrl.send_cmd('get_throughput_dl_stream2'))
    size_DL += float(iCtrl.send_cmd('get_size_dl_stream2'))
    throughput_DL =  throughput_DL * 8
    size_DL = size_DL / 1024
    throughput_DL = round(float(throughput_DL)/1024, 1)
    print "Throughput DL",throughput_DL



if __name__ == '__main__':
    main()
