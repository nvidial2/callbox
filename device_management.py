#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Administrator
#
# Created:     27/06/2012
# Copyright:   (c) Administrator 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import sys, time,  os, os.path, subprocess, re
from global_var import *
import common
from cardhu2 import *

class device_management():
    def get_at_port(self):
        #CARDHU_CODE
        if common.CARDHU:
            status = Cardhu().send_cmd('at')
            if re.search('OK',status):
                return 10 # dummy value , for cardhu simulation
            else:
                return 0
        #CARDHU_END

        self.at_port = 0
        sys.stdout.flush()
        cmd = "devcon find *" + common.VID + "*"
        #print cmd
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        for list in p.stdout:
            list_icera = re.search("AT Device", list)
            if list_icera != None:
                try:
                    self.at_port = re.search('COM(\d+)',list).group(1)
                except:
                    self.at_port = 8
               
                #print "FOUND AT PORT : COM", self.at_port
                break

        sys.stdout.flush()
        return self.at_port

    def get_download_port(self):
        return (int(self.get_at_port())-1)

    def get_modem_status(self):
        #CARDHU_CODE
        if common.CARDHU:
            status = Cardhu().send_cmd('at','modem')
            if re.search('OK',status):
                return True # dummy value , for cardhu simulation
            else:
                return False
        #CARDHU_END

        sys.stdout.flush()
        cmd = "devcon find *" + common.VID + "*"
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        l_split = [None]
        for list in p.stdout:
            list_icera = re.search("Modem Device", list)
            if list_icera != None:
                #print "FOUND MODEM"
                sys.stdout.flush()
                return True

        sys.stdout.flush()
        return False

    def crash_occured(self):
        self.at_port = self.get_at_port()
        if(self.at_port!=0):
            return False

        modem_stat = self.get_modem_status()
        if(modem_stat == True ) :
            return True
        else:
            return False

    def sys_status(self,power_cycle=True):
        # return either OK , DOWNLOAD ONLY , ERROR
        time.sleep(2)
        if (self.get_at_port() != 0) and (self.get_modem_status() == True):
            return SYS_STATUS[0] #OK
        if power_cycle == True :
            self.power_cycle()
        time.sleep(2)
        if (self.get_at_port() != 0) and (self.get_modem_status() == True):
            return SYS_STATUS[0] #OK
        elif (self.get_at_port() == 0) and (self.get_modem_status() == True):
            return SYS_STATUS[1] #DOWNLOAD_ONLY
        elif (self.get_at_port() == 0) and (self.get_modem_status() == False):
            return SYS_STATUS[2] #ERROR


    def restart_cardhu(self):
        print "Cardhu Restarting ...."
        Cardh_ctrl().send_cmd('restart')
        time.sleep(5)
        max_wait = 25
        while max_wait and not Cardh_ctrl().send_cmd('alive'):
            print Cardh_ctrl().send_cmd('alive')
            print "Restarting ...",max_wait
            time.sleep(10)
            max_wait = max_wait - 1
        return

    def power_cycle(self):
        #CARDHU_CODE
        if common.CARDHU:
            self.restart_cardhu()
            return
        #CARDHU_END

        print "\nUSB Relay power cycle..."
        os.system("batch\\relay_OFF.bat")
        self.check_end_batch()
        time.sleep(2)
        os.system("batch\\relay_ON.bat")
        self.check_end_batch()
        time.sleep(5)

    def check_end_batch(self):
        secondCount = 0
        max_second_wait = 300
        while secondCount <= max_second_wait: # wait 5 minutes at the most
            time.sleep(1) # number of second to suspend before next check
            secondCount += 1
            if os.path.exists("endBatch"):
                print "Batch executed in", secondCount, "second(s)"
                os.remove("endBatch")
                return 0
        print "Error: Batch execution not finished within the", secondCount, "second(s)"
        return 1

def main():
    pass

if __name__ == '__main__':
    main()
