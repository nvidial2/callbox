#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Administrator
#
# Created:     29/06/2012
# Copyright:   (c) Administrator 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import os,sys,shutil,subprocess,time,ssh,re
from global_var import *
from FindRegression import *
import chart

class Tools:

    def checkBuild (self,file):
        print "Checking build..."
        FILE_STATUS = open(file,'r')
        # search_for_build_ok = "Wrapped Integrity check successful"
        search_for_build_ok = "build archive with header using"
        for line in reversed(FILE_STATUS.readlines()):
            if re.search(search_for_build_ok, line):
                return BUILD_OK
        return BUILD_FAILED

    def find_index(self,lst,item):

        if not isinstance(item,basestring):
            item = item[0]

        for i in range(0,len(lst)):
            if(lst[i]==item):
                return i
        print "List",lst
        print "item",item
        print "No Item Found"
        return 0

    def build(self,branch,cl,variant="tango-internal"):

        print "Building ",branch,cl,variant
        i = self.find_index(BRANCH_ALLOWED,branch)
        print i

        if os.path.exists(BINARY_LIB+str(cl)+".zlib.wrapped"):
            return BUILD_OK

        if os.path.exists(MODEM_BINARY_LOC[i]+"modem-rsa-key0.zlib.wrapped"):
            os.remove(MODEM_BINARY_LOC[i]+"modem-rsa-key0.zlib.wrapped")

        #cmd = "cd %s ;p4 sync %s...@%s; make -l ncpus=2 -j6 bin VARIANT=%s "%(build_dir[i],P4BRANCH[i],cl,variant)
        cmd = "cd %s ;p4 sync %s...@%s; qjob make -l ncpus=2 -j6 bin VARIANT=%s "%(build_dir[i],P4BRANCH[i],cl,variant)
        result = self.ssh_client(cmd)

##        if self.checkBuild(BUILD_STATUS_LOC[i]+"%s_build_status.txt"%variant) == BUILD_OK :
##            print "Finished"
##            return BUILD_OK

        if os.path.exists(MODEM_BINARY_LOC[i]+"modem-rsa-key0.zlib.wrapped"):
            print "Build Build Successful"
            shutil.copy2(MODEM_BINARY_LOC[i]+"modem-rsa-key0.zlib.wrapped",(BINARY_LIB+str(cl)+".zlib.wrapped"))
            return BUILD_OK
        else:
            print MODEM_BINARY_LOC[i]+"modem-rsa-key0.zlib.wrapped"
            msg = r"BUILD FAILURE FOR CL %s BRANCH %s VARIANT %s\n"%(cl,branch,variant)
            self.sendMail(msg)
            file_name = "BUILD_FAILURE_BRANCH_%s_CL_%s"%(branch,str(cl))
            try:
                FILE = open('regression\\'+file_name,'a')
                for line in result :
                    msg += r'%s'%line
                    FILE.write(line)
                #print msg
                FILE.close()
                #p = subprocess.Popen("echo %s > build_failure_mail"%msg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                self.sendMail(msg)
            except:
                pass
                
            return BUILD_FAILED

    def ssh_client(self,cmd):
        #server = ssh.Connection(host='sxdbld02', username='gcflab', password='LG!)67wn')
        server = ssh.Connection(host='frsys1', username='nsait', password='M@ilhot123')
        result = server.execute(cmd)
        return result

    def get_CL_list(self,br,p4br,startCl,endCl):
        cl_list = []
        cmd = "cd %s;p4 changes %s...@%s,@%s" % (br,p4br, startCl, endCl)
        print "[get_CL_list]",cmd
        result = self.ssh_client(cmd)
        print result
        for line in result:
            #print line
            try:
                cl = re.search(re.compile(r'Change (\S+) on'),line).group(1)
                #if self.failed_build(cl) == False :
                cl_list.append(cl)
            except:
                pass
        #print cl_list
        return cl_list


    def build_regression(self,branch,ko_cl):
        print "[BUILD_REGRESSION]BUILD FAILURE BRANCH %s CL %s"%(branch,str(ko_cl))
        self.sendMail(r"[BUILD_REGRESSION]BUILD FAILURE BRANCH %s CL %s"%(branch,ko_cl))
        i = self.find_index(BRANCH_ALLOWED,branch)
        ok_cl = chart.Chart().last_build_success(branch,ko_cl)
        print "OK_CL",ok_cl
        while True :
            cl_list = self.get_CL_list(build_dir[i],P4BRANCH[i],ok_cl,ko_cl)
            print cl_list
            if(len(cl_list)) == 2 :
                print "Final OK ",cl_list[1]
                print "Final KO",cl_list[0]
                try:
                    self.sendMail(r"BUILD FAILURE BRANCH %s KO_CL %s OK_CL%s"%(branch,cl_list[0],cl_list[1]))
                    file_name = "BUILD_FAILURE_BRANCH_%s_KO_CL_%s_OK_CL%s"%(branch,cl_list[0],cl_list[1])
                    FILE = open('regression\\'+file_name,'a')
                    FILE.write(file_name)
                    FILE.close()
                except:
                    pass
                return cl_list[0],cl_list[1]

            if(len(cl_list)) == 0 :
                print "End"
                return

            nxt_cl = cl_list[len(cl_list)/2]
            print nxt_cl
            build_status = self.build(branch,nxt_cl)
            if build_status == BUILD_OK :
                    ok_cl = nxt_cl
            else:
                    ko_cl = nxt_cl

    def _build(self,branch,cl=0,variant="tango-internal"):
        print "Building Branch : ",branch
        i = self.find_index(BRANCH_ALLOWED,branch)
        if cl == 0:
            cl = self.latest_cl(branch)
        print "CL",cl
        if cl != 0 :
            status = self.build(branch,cl,variant)

            if status == BUILD_OK :
                return BUILD_OK,int(cl)
            else:
                self.build_regression(branch,cl)
                print "Build Regression End"
                return BUILD_FAILED,0

        return BUILD_FAILED,0

    def sendMail(self,msg):
        print "Msg to Send",msg
        cmd = "echo \"%s\" > txt_msg ; cat txt_msg | ssh frlts mail -s \"Test_Issues1\" nsait@nvidia.com " %(msg)
        self.ssh_client(cmd)
        cmd = "echo \"%s\" > txt_msg ; cat txt_msg | mail -s \"Test_Issues2\" nsait@nvidia.com " %(msg)
        self.ssh_client(cmd)
        cmd = "echo \"%s\" > txt_msg ; mail -s \"Test_Issues3\" nsait@nvidia.com < txt_msg" %(msg)
        self.ssh_client(cmd)
      
    def latest_cl(self,branch):
        i = self.find_index(BRANCH_ALLOWED,branch)
        print i
        print "cd %s ; p4 changes -m1 %s..."%(build_dir[i],P4BRANCH[i])
        result =  self.ssh_client("cd %s ; p4 changes -m1 %s..."%(build_dir[i],P4BRANCH[i]))
        print result
        for line in result:
            print line
            try:
                cl = re.search(re.compile(r'Change (\S+) on'),line).group(1)
            except:
                cl = 0
            return cl
            
    def string_array(self,element):
        #element = str(element)
        if isinstance(element, basestring) :#or isinstance(element,int):
            scarray = []
            scarray.append(element)
            element = scarray
        elif isinstance(element,int):
            scarray=[]
            scarray.append(element)
            element = scarray

        return element

    def generateBuildReady (self,branch,cl):
        cmd = "echo \"CL%s\" > %s" % (str(cl),branch)
        p=subprocess.Popen(cmd,stderr=subprocess.PIPE,shell=True) #NSAIT
        #print "Generate Build Ready with type=%s, owner=%s, branch=%s, variant=%s, CL%s, %s, %s" % (type, owner, branch, variant, cl, test, band)
    
def main():
    Tools()._build('main')
    #Tools().sendMail("Hello 2")
    pass

if __name__ == '__main__':
    #main()
    print Tools().get_CL_list(build_dir[0],P4BRANCH[0],472914,472920)#_build('cr3')
