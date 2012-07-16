#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Administrator
#
# Created:     04/07/2012
# Copyright:   (c) Administrator 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python


import ssh,os,re,subprocess,time
from global_var import *
import chart
#from auto_gui2 import *
import auto_gui2
from tools import *

class Regression:

    def compare_values(self,ref,chk,comparator=CHECK_LOW):
        if comparator == CHECK_LOW :
            if ref == 0 :
                return STATUS_OK
            elif (chk>ref):
                return STATUS_OK
            elif ((ref-chk)/ref) < REGRESSION_DELTA_DOWNLINK :
                return STATUS_OK
            else:
                return STATUS_REGRESSION
        elif comparator == CHECK_HIGH :
            if ref == 0 :
                return STATUS_OK
            elif (chk<ref):
                return STATUS_OK
            elif (chk)>(ref*(1+REGRESSION_DELTA_DXP)):#((chk-ref)/ref) < REGRESSION_DELTA_DOWNLINK :
                return STATUS_REGRESSION
            else:
                return STATUS_OK

    def check_regression(self,ref,chk):
        print self.band_4test,ref,1,self.scenario_4test,self.branch_4test
        
        band_4test = Tools().string_array(self.band_4test)
        scenario_4test = Tools().string_array(self.scenario_4test)
        branch_4test = Tools().string_array(self.branch_4test)
        
        dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul = chart.Chart().Get_CL_Values(band_4test[0],int(ref),scenario_4test[0],branch_4test[0])
        print dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul

        dxp0x,dxp1x,cpu_dlx,cpu_ulx,ftp_dlx,ftp_ulx = chart.Chart().Get_CL_Values(band_4test[0],int(chk),scenario_4test[0],branch_4test[0])
        print dxp0x,dxp1x,cpu_dlx,cpu_ulx,ftp_dlx,ftp_ulx

        # dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul = chart.Chart().Get_CL_Values(self.band_4test[0],int(ref),self.scenario_4test[0],self.branch_4test[0])
        # print dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul

        # dxp0x,dxp1x,cpu_dlx,cpu_ulx,ftp_dlx,ftp_ulx = chart.Chart().Get_CL_Values(self.band_4test[0],int(chk),self.scenario_4test[0],self.branch_4test[0])
        # print dxp0x,dxp1x,cpu_dlx,cpu_ulx,ftp_dlx,ftp_ulx

        if  self.compare_values(cpu_dl,cpu_dlx) == STATUS_REGRESSION or \
            self.compare_values(cpu_ul,cpu_ulx) == STATUS_REGRESSION or \
            self.compare_values(ftp_dl,ftp_dlx) == STATUS_REGRESSION or \
            self.compare_values(ftp_ul,ftp_ulx) == STATUS_REGRESSION or \
            self.compare_values(dxp0,dxp0x,CHECK_HIGH) == STATUS_REGRESSION or \
            self.compare_values(dxp1,dxp1x,CHECK_HIGH) == STATUS_REGRESSION :
                return STATUS_REGRESSION

        else:
            return STATUS_OK

    def string_array(self,element):
        #element = str(element)
        if isinstance(element, basestring):
            scarray = []
            scarray.append(element)
            element = scarray
        return element

    def _run(self,branch,band,scenario,cl):
        band = Tools().string_array(band)
        scenario = Tools().string_array(scenario)
        branch = Tools().string_array(branch)
        branch = branch[0]
        
        print "[FR][_run] band",band
        print "[FR][_run] scenario",scenario
        for b in band :
            for scen in scenario:
                print "Regression Run ", branch,band,scenario,cl
                status = chart.Chart().get_scenario_status(branch,b,scen,cl)
                print "Status for the scenario",status
                if status in EXCEL_STATUS and status != STATUS_OK :
                    (prev_cl,prev_stat) =  chart.Chart().previous_cl_status(branch,b,scen,cl)
                    if str(prev_stat) != str(status) :    
                        ref_cl = chart.Chart().good_cl(branch,b,scen,cl)
                        print "Ref_CL",ref_cl
                        print branch , b , scen , ref_cl , cl
                        if ref_cl != "ERROR" :
                            ko_cl,ok_cl=self.find_regression(branch,b,scen,ref_cl,cl)
                            print "[REG][CL%s][BRANCH:%s][BAND:%s][SCEN:%s] KO_CL %s , OK_CL %s"%(str(cl),branch,str(b),scen,str(ko_cl),str(ok_cl))
                            Tools().sendMail(r"[REG][CL%s][BRANCH:%s][BAND:%s][SCEN:%s] KO_CL %s , OK_CL %s"%(str(cl),branch,str(b),scen,str(ko_cl),str(ok_cl)))
                            file_name = "Reg_%s_%d_%s_KOCL%d_OKCL_%d.txt" % (branch,int(b),scen, int(ko_cl),int(ok_cl))
                            FILE = open('regression\\'+file_name,'a')
                            FILE.write(r"[REG][CL%s][BRANCH:%s][BAND:%s][SCEN:%s] KO_CL %s , OK_CL %s"%(str(cl),branch,str(b),scen,str(ko_cl),str(ok_cl)))
                            FILE.close()
                    else:
                        print "No need to find Regression , Regression already found"
                        

    def selemet(self,element):
        try:
            if not isinstance(element,basestring):
                element = element[0]
                return element
        except:
            return element

    def find_regression(self,branch_4test,band_4test,scenario_4test,ok_cl,ko_cl):
        
        branch_4test = (Tools().string_array(branch_4test))[0]
        scenario_4test = (Tools().string_array(scenario_4test))[0]
        band_4test = (Tools().string_array(band_4test))[0]
        
        print branch_4test , band_4test, scenario_4test , ok_cl,ko_cl
        
        Tools().sendMail(r"Find Regression For Branch %s , Band %s , Scen %s , OK_CL %s , KO_CL %s"%(branch_4test,str(band_4test),scenario_4test,str(ok_cl),str(ko_cl)))
        self.init()
        self.branch_4test = branch_4test
        self.band_4test = band_4test
        self.scenario_4test = (scenario_4test)

        iCT = auto_gui2.CallboxTest()
        
        i = self.find_index(BRANCH_ALLOWED,branch_4test)

        print "[FR][f_r] Block 1 "
        while True :
            cl_list = self.get_CL_list(build_dir[i],P4BRANCH[i],ok_cl,ko_cl)
            print "[FR][f_r] cl_list ",cl_list
            if(len(cl_list)) == 2 :
                print "Final OK ",cl_list[1]
                print "Final KO",cl_list[0]
                return cl_list[0],cl_list[1]

            if(len(cl_list)) == 0 :
                print "End"
                return

            nxt_cl = self.next_test_cl(cl_list)
            print nxt_cl
            build_status = Tools().build(branch_4test,nxt_cl)
            if build_status == BUILD_OK :
                iCT.Init_Auto(branch_4test,int(band_4test),scenario_4test)
                iCT.Run_Branch_Test(Forced=False,flash=True,Reg=False,CL=nxt_cl)
                if self.check_regression(ok_cl,nxt_cl) == STATUS_OK :
                    ok_cl = nxt_cl
                else:
                    ko_cl = nxt_cl
            elif build_status == BUILD_FAILED :
                self.build_failure.append(nxt_cl)
            else:
                pass

    def init(self):
##        self.ko = "470897"
##        self.ok = "470870"
##        self.ref_value =  10
##        self.demo_cl= ['470897', '470892', '470886', '470885', '470884', '470883', '470870']
##        self.demo_val = [5,5,5,5,5,5,10]
        self.build_failure = []
        self.build_failure.append("0")

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

    def failed_build(self,cl):
        for i in self.build_failure:
            if cl == i :
                return True

        return False

    def get_CL_list(self,br,p4br,startCl,endCl):
        cl_list = []
        cmd = "cd %s;p4 changes %s...@%s,@%s" % (br,p4br, startCl, endCl)
        print "[FR][get_CL_list] cmd",cmd
        result = Tools().ssh_client(cmd)
        print "[FR][get_CL_list] Result",result
        for line in result:
            print "[FR][get_CL_list] line",line
            try:
                cl = re.search(re.compile(r'Change (\S+) on'),line).group(1)
                if self.failed_build(cl) == False :
                    cl_list.append(cl)
            except:
                pass

        print cl_list
        return cl_list


    def build_cl(self,br,cl):
        i = 0
        for branchx in BRANCH_ALLOWED :
            if branchx in br :
                break
            i += 1

        if os.path.exists(BINARY_LIB+cl+".zlib.wrapped"):
            return True

        if os.path.exists(file_bld_ready[i]):
            os.remove(file_bld_ready[i])

        #server = ssh.Connection(host='sxdbld02', username='gcflab', password='LG!)67wn')
        cmd = "cd %s;echo CL%s > run_buildx" %(build_dir[i],cl)
        result = Tools().ssh_client(cmd) #server.execute(cmd)

        timer = time.time()

        while True:
            duration = time.time() - timer
            if duration > MAX_BUILD_TIME:
                return False
            if os.path.exists(file_bld_ready[i]):
                os.remove(file_bld_ready[i])
                return True

    def next_test_cl(self,cl_list):
        return cl_list[len(cl_list)/2]

    def main(self):
        self.ok_cl= "470175"#self.tOk_cl.GetLabel()#"470175"
        self.ko_cl = "470820"#self.tKo_cl.GetLabel()#"470820"
        #['main'] [4] ['FTP_DL_SISO_AM_RB50_TBS25']
        #['main'] [4] ['FTP_DL_SISO_AM_RB50_TBS25'] 470175 470820
        #self.find_regression('cr3','4','FTP_DL_SISO_RB50_TBS25',self.ok_cl,self.ko_cl)
        #return
        cl = 100
        branch = 'cr3'
        b = 4
        scen = scenario_implemented[0]
        ko_cl = 22
        ok_cl = 20
        Tools().sendMail(r"[REG][CL%s][BRANCH:%s][BAND:%s][SCEN:%s] KO_CL %s , OK_CL %s\n 2nd Line \n 3rd Line"%(str(cl),branch,str(b),scen,str(ko_cl),str(ok_cl)))
        #self._run('cr3','4',scenario_implemented[0],471068)
        return
        self.build_cl('cr3','470897')
        return
        self.init()

if __name__ == '__main__':
    Regression().main()
