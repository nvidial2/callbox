#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Administrator
#
# Created:     11/07/2012
# Copyright:   (c) Administrator 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import socket
from global_cardhu import *
import sys, time, os, os.path, threading, subprocess, re, locale,shutil
from ftplib import FTP

class File_download (threading.Thread):
    def set_file(self, file_downlink):
        self.file_downlink = file_downlink

    def run(self):
        self.throughput = 0
        print "\nStarting DL FTP transfer: %s" % self.file_downlink
        # print "current patch:", os.getcwd()
        if os.path.exists(self.file_downlink):
            os.remove(self.file_downlink)
        ftp = FTP(FTP_SERVER_ADDRESS, FTP_SERVER_USER,' ')
        try:
            ftp.cwd(directory_downlink)
        except:
            print "Cannot connect to server %s" % FTP_SERVER_ADDRESS
            sys.exit()
        starttimer = time.time()
        try:
            ftp.retrbinary("RETR " + self.file_downlink, open(self.file_downlink, 'wb').write)
        except:
            message = "DL FTP server transfer broken"
            print message
            raise
        duration = time.time() - starttimer
        dl_size = (os.path.getsize(self.file_downlink))/1024
        self.throughput = float(dl_size / duration)
        print "FTP DL get %d kB at %g kbps (%.2f sec)" % (dl_size, self.throughput*8, duration)
        ftp.quit()

    def get_throughput(self):
        return self.throughput

    def get_dl_size(self):
        dl_size = 0
        try:
            dl_size = (os.path.getsize(self.file_downlink))/1024
        except:
            pass
        return dl_size


class File_upload (threading.Thread):
    def set_file(self, file_uplink):
        self.file_uplink = file_uplink

    def run(self):
        self.throughput = 0
        print "\nStarting UL FTP transfer: %s" % self.file_uplink
        ftp = FTP(FTP_SERVER_ADDRESS, FTP_SERVER_USER, '')
        try:
            ftp.cwd(directory_uplink)
        except:
            print "Cannot connect to server %s" % FTP_SERVER_ADDRESS
            Tools().sendMail("[FTP] Cannot connect to server %s"%FTP_SERVER_ADDRESS)
            sys.exit()
        starttimer = time.time()
        try:
            ul_size = round((ftp.size(self.file_uplink))/1024)
            message = "previous size for %s is: %d" % (self.file_uplink, round(ul_size/1024))
            print message
        except:
            print "Can't get previous file size"
            pass

        try:
            ftp.delete(self.file_uplink)
        except:
            print "The file %s does not exist on FTP server, OK" % self.file_uplink
            pass
        try:
            ftp.storbinary("STOR " + self.file_uplink, open(self.file_uplink, 'rb'), 49152) #was 32768 / 49152
        except:
            # Add message in file
            message = "UL FTP server transfer broken"
            print message
            pass
        duration = time.time() - starttimer
        ul_size = (ftp.size(self.file_uplink))/1024
        self.throughput = float(ul_size / duration)
        print "FTP UL get %d kB at %g kbps (%.2f sec)" % (ul_size, self.throughput*8, duration)
        ftp.quit()

    def get_throughput(self):
        return self.throughput

    def get_ul_size(self):
        ul_size = 0
        try:
            ftp = FTP(FTP_SERVER_ADDRESS, FTP_SERVER_USER,' ')
            ftp.cwd(directory_uplink)
        except:
            print "Cannot connect to server %s to retrieve uploaded file size!" % FTP_SERVER_ADDRESS
            pass
        try:
            ul_size = (ftp.size(self.file_uplink))/1024
        except:
            pass
        return ul_size


class Cardhu_plat:

    def start_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((MASTER_IP, PORT))
        s.listen(1)
        self.conn, addr = s.accept()
        print 'Connected by', addr
        while 1:
            data = self.conn.recv(1024)
            if not data:
                break
            print data
            self.message(data)
        self.conn.close()

    def message(self,msg):
        if equal(msg,'ftp_downlink_stream1'):
            self.ftp_downlink_stream1(500)
        elif equal(msg,'ftp_downlink_stream2'):
            self.ftp_downlink_stream2(500)
        elif equal(msg,'ftp_thread_active'):
            self.ftp_thread_active()

    def restart(self):
        print "Cardhu Restart"

    def ftp_downlink_stream1(self, dl_file_size):
        self.File_DL = File_download()
        self.File_DL.set_file("%dMo.txt" % dl_file_size)
        self.File_DL.set_info(self.cl, int(self.band), self.scen_name)
        self.File_DL.start()

    def ftp_downlink_stream2(self,dl_file_size):
        self.File_DL2 = File_download()
        self.File_DL2.set_file("%dMo.txt" % dl_file_size)
        self.File_DL2.start()

    def ftp_uplink_stream1(self,ul_file_size):
        self.File_UL1 = File_upload()
        self.File_UL1.set_file("%dMo_1.txt" % ul_file_size)
        self.File_UL1.start()

    def ftp_uplink_stream2(self,ul_file_size):
        self.File_UL2 = File_upload()
        self.File_UL2.set_file("%dMo_2.txt" % ul_file_size)
        self.File_UL2.start()

    def ftp_uplink_stream3(self,ul_file_size):
        self.File_UL3 = File_upload()
        self.File_UL3.set_file("%dMo_3.txt" % ul_file_size)
        self.File_UL3.start()

    def ftp_thread_active(self):
        try:
            if self.File_DL.isAlive():
                return True
        except:
            pass
        try:
            if 'File_DL2' in locals():
                if self.File_DL2.isAlive():
                            return True
        except:
            pass
        try:
            if self.File_UL1.isAlive():
                return True
        except:
            pass
        try:
            if self.File_UL2.isAlive():
                return True
        except:
            pass
        try:
            if self.File_UL3.isAlive():
                return True
        except:
            pass

        return False

    def main(self):
        self.start_server()


def main():
    Cardhu_plat().main()

def equal(msg,strin):
    if msg == strin:
        return True
    return False

if __name__ == '__main__':
    main()