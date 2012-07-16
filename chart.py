
#Niyas Sait
#NVIDIA
#Graph Generator For Callbox Throughput Testing Setup
#2012

import sys,time, os, os.path, threading, subprocess, re, locale , shutil
from ftplib import FTP
from xlwt import Workbook, easyxf
from xlrd import open_workbook, cellname
from xlutils.copy import copy

from pygooglechart import StackedHorizontalBarChart, StackedVerticalBarChart, \
    GroupedHorizontalBarChart, GroupedVerticalBarChart ,Axis , SimpleLineChart

from random import randint, uniform
from global_var import *
from tools import *

class Chart:
    def init(self):
        self.cl = 463254
        self.band = 4
        self.scen_name = "FTP_DL_SISO_AM_RB50_TBS25"

    def _chart(self) :
        self.init()
        #self.chart_scenario(4,465871,5,branch='cr3')
        #self.chart_scenario(17,465871,5,self.scen_name,'cr3')
        # self.chart_overall(4,465871,5,scenario_implemented)
        # self.chart_overall(17,470549,1,scenario_implemented)
        #dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul = self.Get_CL_Values("4","470175",scenario_implemented[1],'cr3')
        print self.get_scenario_status('cr3',4,scenario_implemented[2],470820)
        print self.good_cl('cr3',4,scenario_implemented[len(scenario_implemented)-1],466921)

    def chart_scenario(self,band,cl,no=5,scen=scenario_implemented,branch='main'):
        i = Tools().find_index(BRANCH_ALLOWED,branch)
        self.excel = EXCEL_FLIST[i] 
        (found,cl_list,dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul)=self.get_value(band,cl,no,scenario_implemented)
        if found != True :
            return

        self.draw_scenario(dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul,cl_list,band,100,scen,branch)

    def Get_CL_Values(self,band,cl,scen=scenario_implemented,branch='main'):
 
        i = Tools().find_index(BRANCH_ALLOWED,branch)
        
        self.excel = EXCEL_FLIST[i] 


        (found,cl_list,dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul)=self.get_value_scenario(band,cl,scen)
        if found != True :
            return

        return dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul


    def chart_overall(self,band,cl,no=5,scen=scenario_implemented):
        (found,cl_list,dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul)=self.get_value(band,cl,no,scen)
        if found != True :
            return

        self.draw_overall(dxp0,cl_list,"DXP0",band,100)
        self.draw_overall(dxp1,cl_list,"DXP1",band,100)
        self.draw_overall(cpu_dl,cl_list,"CPU_DL",band,51)
        self.draw_overall(cpu_ul,cl_list,"CPU_UL",band,20)
        self.draw_overall(ftp_dl,cl_list,"FTP_DL",band,51)
        self.draw_overall(ftp_ul,cl_list,"FTP_UL",band,20)



    def triplet(self,rgb0,rgb1,rgb2):
        return hex(rgb0)[2:] + hex(rgb1)[2:] + hex(rgb2)[2:]


    def draw_scenario(self,dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul,cl_list,band,max_y,scen,branch):

        chart = GroupedVerticalBarChart(1000,300,
                                        y_range=(0,max_y))

        fixed_color =['ff154d', '7fff00' ,'0000ff','db7093','9f9f5f']

        color = []
        for i in range(0,len(cl_list)):
            if i < 5 :
                color.append(fixed_color[i])
            else:
                color.append(self.triplet(randint(100, 255), randint(100, 255), randint(100, 255)))

        chart.set_colours(color)

        #chart.set_colours(['76A4FB', '224499','208020', '80C65A','FF0000'])
        chart.set_legend(cl_list)
        chart.set_grid(0,5, 5, 5)
        #print scen
        if re.search('DL',scen) and re.search('UL',scen) :
            for j in range(0,len(scenario_implemented)):
                if scen == scenario_implemented[j] :
                    for i in range(0,len(cl_list)):
                        chart.add_data([dxp0[i][j],dxp1[i][j],cpu_dl[i][j],ftp_dl[i][j],cpu_ul[i][j],ftp_ul[i][j]])
                    index=chart.set_axis_labels(Axis.BOTTOM,["dxp0","dxp1","CPU_DL","FTP_DL","CPU_UL","FTP_UL"])
                    chart.set_bar_width(18)

        elif re.search('DL',scen):
            for j in range(0,len(scenario_implemented)):
                if scen == scenario_implemented[j] :
                    for i in range(0,len(cl_list)):
                        chart.add_data([dxp0[i][j],dxp1[i][j],cpu_dl[i][j],ftp_dl[i][j]])

                    index=chart.set_axis_labels(Axis.BOTTOM,["dxp0","dxp1","CPU_DL","FTP_DL"])
                    if(len(cl_list)<5):
                        chart.set_bar_width(36)
                    else:
                        chart.set_bar_width(18)

        elif re.search('UL',scen):
            for j in range(0,len(scenario_implemented)):
                if scen == scenario_implemented[j] :
                    for i in range(0,len(cl_list)):
                        chart.add_data([dxp0[i][j],dxp1[i][j],cpu_ul[i][j],ftp_ul[i][j]])

                    index=chart.set_axis_labels(Axis.BOTTOM,["dxp0","dxp1","CPU_UL","FTP_UL"])
                    if(len(cl_list)<5):
                        chart.set_bar_width(36)
                    else:
                        chart.set_bar_width(18)


        chart.set_axis_range(Axis.LEFT,0,max_y)
        chart.set_axis_style(index, colour='000000', \
                font_size= 12)

        chart_dir = 'chart\\'
        file = scen+"_"+"Band"+str(band)+"_"+branch+".jpeg"
        #print "src",chart_dir+file
        #print "dest",CHART_LOC+'\\\\'+file
        chart.download(chart_dir+file)
        #shutil.copy2(chart_dir+file,'\\\\'+CHART_LOC+'\\\\'+file)


    def draw_overall(self,data,cl_list,title,band,max_y):
        self.init()
        chart = GroupedVerticalBarChart(1000,300,
                                        y_range=(0,max_y))


        for i in range(0,len(data)) :
            chart.add_data(data[i])

        chart.set_bar_width(18)
        chart.set_colours(['76A4FB', '224499','208020', '80C65A','FF0000'])

        chart.set_legend(cl_list)

        index=chart.set_axis_labels(Axis.BOTTOM, scenario_implemented)
        chart.set_axis_range(Axis.LEFT,0,max_y)
        chart.set_axis_style(index, colour='000000', \
                font_size= 6)

        chart.set_grid(0,5, 5, 5)
        IMG_DIR = os.path.join("serv2.icerasemi.com", "eng", "nsait", "img\\")
        IMG_DIR = 'serv2.icerasemi.com\eng\nsait\img\\'
        #dir = '\\serv2.nvidia.com\eng\nsait\img'
        dir = 'chart\\'
        chart.download(dir+title+str(band)+'.jpeg')
        #shutil.copy2('img\dxp04.jpeg', self.callbox_path+'\dxp04.jpeg')


    def init_2d(self,x,y):
        foo = 0
        return [[foo for i in range(x)] for j in range(y)]

    def get_value(self,band,cl,no,scenes):

        k=10
        dxp = self.init_2d(len(scenes),no)
        dxp0 = self.init_2d(len(scenes),no)
        dxp1 = self.init_2d(len(scenes),no)
        cpu_dl = self.init_2d(len(scenes),no)
        cpu_ul = self.init_2d(len(scenes),no)
        ftp_dl = self.init_2d(len(scenes),no)
        ftp_ul = self.init_2d(len(scenes),no)
        cl_list = [] # self.init_2d(len(scenario_implemented),5)
        i = 0
        j = 0

        read_book = open_workbook(self.excel, formatting_info=True)
        self.read_sheet = read_book.sheet_by_name("Band%d" % int(band))
        nrows = self.read_sheet.nrows
        CL_found, _current_row = self.get_CL_idx(nrows,cl)

        if CL_found == False :
            return False,cl_list,dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul


        for current_row in range(_current_row,_current_row-no,-1):
            j = 0
            if(current_row) > LIN_INFO :
                cl_list.append(str(int(self.read_sheet.cell(current_row,COL_CL).value)))

            for scen_name in scenes :
                if(current_row) > LIN_INFO :
                    #cl_list.append(int(self.read_sheet.cell(current_row,COL_CL).value))

                    self.current_col, self.status_col = self.get_column_for_test(self.read_sheet,scen_name)

                    cpu_lo,cpu_hi = self.get_column_for_test(self.read_sheet,"CPU",self.current_col,self.status_col,1)

                    try:
                        if self.read_sheet.cell(current_row,cpu_lo).value != "" :
                            dxp1[i][j] = (float(self.read_sheet.cell(current_row,cpu_lo).value))
                    except:
                        print " "

                        #dxp0.append(float(self.read_sheet.cell(current_row,cpu_lo).value))

                    try:
                        if self.read_sheet.cell(current_row,cpu_lo+1).value != "" :
                        # dxp1[i][j].append(float(self.read_sheet.cell(current_row,cpu_lo+1).value))
                            dxp0[i][j] = (float(self.read_sheet.cell(current_row,cpu_lo+1).value))
                    except:
                        print " "

                    dl_lo,dl_hi = self.get_column_for_test(self.read_sheet,"DL Rate (Mb/s)",self.current_col,self.status_col,2)

                    if dl_lo !=0 :
                        if self.read_sheet.cell(current_row,dl_lo+1).value != "" :
                           # cpu_dl.append(float(self.read_sheet.cell(current_row,dl_lo+1).value))
                            try:
                                cpu_dl[i][j]=(float(self.read_sheet.cell(current_row,dl_lo+1).value))
                            except:
                                print " "
                    ul_lo,ul_hi = self.get_column_for_test(self.read_sheet,"UL Rate (Mb/s)",self.current_col,self.status_col,2)

                    if ul_lo !=0 :
                        if self.read_sheet.cell(current_row,ul_lo+1).value != "" :
                            # cpu_ul.append(float(self.read_sheet.cell(current_row,ul_lo+1).value))
                            try:
                                cpu_ul[i][j]=(float(self.read_sheet.cell(current_row,ul_lo+1).value))
                            except:
                                print " "

                    ftp_lo,ftp_hi =  self.get_column_for_test(self.read_sheet,"FTP",self.current_col,self.status_col,1)

                    ftp_cdl =  self.get_column_for_ftp(self.read_sheet,"DL(Mb/s)",ftp_lo,ftp_hi,1)

                    if ftp_cdl !=0 :
                        if self.read_sheet.cell(current_row,ftp_cdl).value != "" :
                            # ftp_dl.append(float(self.read_sheet.cell(current_row,ftp_cdl).value))
                            try:
                                ftp_dl[i][j]=(float(self.read_sheet.cell(current_row,ftp_cdl).value))
                            except:
                                print ""
                    ftp_cul =  self.get_column_for_ftp(self.read_sheet,"UL(Mb/s)",ftp_lo,ftp_hi,1)

                    if ftp_cul !=0 :
                        if self.read_sheet.cell(current_row,ftp_cul).value != "" :
                            # ftp_ul.append(float(self.read_sheet.cell(current_row,ftp_cul).value))
                            try:
                                ftp_ul[i][j]=(float(self.read_sheet.cell(current_row,ftp_cul).value))
                            except:
                                print ""
                j += 1

            i += 1

            #chart.add_data(dxp0)
        return True,cl_list,dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul


    def get_value_scenario(self,band,cl,scen_name):

        k=10
        cpu_dl = 0
        cpu_ul = 0
        ftp_dl = 0
        ftp_ul = 0
        cl_list = 0
        dxp0 = 0
        dxp1= 0
        read_book = open_workbook(self.excel, formatting_info=True)
        self.read_sheet = read_book.sheet_by_name("Band%d" % int(band))
        nrows = self.read_sheet.nrows
        CL_found, _current_row = self.get_CL_idx(nrows,int(cl))

        if CL_found == False :
            return False,cl_list,dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul

        current_row = _current_row
        #for current_row in range(_current_row,_current_row-no,-1):
        if(_current_row) > LIN_INFO :
            cl_list=(str(int(self.read_sheet.cell(_current_row,COL_CL).value)))

            #for scen_name in scenes :
                #print scen_name
        if(current_row) > LIN_INFO :
            #cl_list=(int(self.read_sheet.cell(current_row,COL_CL).value))

            self.current_col, self.status_col = self.get_column_for_test(self.read_sheet,scen_name)

            cpu_lo,cpu_hi = self.get_column_for_test(self.read_sheet,"CPU",self.current_col,self.status_col,1)

            try:
                if self.read_sheet.cell(current_row,cpu_lo).value != "" :
                    dxp1=(float(self.read_sheet.cell(current_row,cpu_lo).value))
            except:
                pass

                #dxp0=(float(self.read_sheet.cell(current_row,cpu_lo).value))

            try:
                if self.read_sheet.cell(current_row,cpu_lo+1).value != "" :
                # dxp1[i][j]=(float(self.read_sheet.cell(current_row,cpu_lo+1).value))
                    dxp0=(float(self.read_sheet.cell(current_row,cpu_lo+1).value))
            except:
                pass

            dl_lo,dl_hi = self.get_column_for_test(self.read_sheet,"DL Rate (Mb/s)",self.current_col,self.status_col,2)

            if dl_lo !=0 :
                if self.read_sheet.cell(current_row,dl_lo+1).value != "" :
                   # cpu_dl=(float(self.read_sheet.cell(current_row,dl_lo+1).value))
                    try:
                        cpu_dl=(float(self.read_sheet.cell(current_row,dl_lo+1).value))
                    except:
                        pass
            ul_lo,ul_hi = self.get_column_for_test(self.read_sheet,"UL Rate (Mb/s)",self.current_col,self.status_col,2)

            if ul_lo !=0 :
                if self.read_sheet.cell(current_row,ul_lo+1).value != "" :
                    # cpu_ul=(float(self.read_sheet.cell(current_row,ul_lo+1).value))
                    try:
                        cpu_ul=(float(self.read_sheet.cell(current_row,ul_lo+1).value))
                    except:
                        pass

            ftp_lo,ftp_hi =  self.get_column_for_test(self.read_sheet,"FTP",self.current_col,self.status_col,1)

            ftp_cdl =  self.get_column_for_ftp(self.read_sheet,"DL(Mb/s)",ftp_lo,ftp_hi,1)

            if ftp_cdl !=0 :
                if self.read_sheet.cell(current_row,ftp_cdl).value != "" :
                    # ftp_dl=(float(self.read_sheet.cell(current_row,ftp_cdl).value))
                    try:
                        ftp_dl=(float(self.read_sheet.cell(current_row,ftp_cdl).value))
                    except:
                        print ""
            ftp_cul =  self.get_column_for_ftp(self.read_sheet,"UL(Mb/s)",ftp_lo,ftp_hi,1)

            if ftp_cul !=0 :
                if self.read_sheet.cell(current_row,ftp_cul).value != "" :
                    # ftp_ul=(float(self.read_sheet.cell(current_row,ftp_cul).value))
                    try:
                        ftp_ul=(float(self.read_sheet.cell(current_row,ftp_cul).value))
                    except:
                        pass

            #chart.add_data(dxp0)
        return True,cl_list,dxp0,dxp1,cpu_dl,cpu_ul,ftp_dl,ftp_ul


    def get_scenario_status(self,branch,band,scen_name,cl):
        i = Tools().find_index(BRANCH_ALLOWED,branch)
        self.excel = EXCEL_FLIST[i]
        read_book = open_workbook(self.excel, formatting_info=True)
        self.read_sheet = read_book.sheet_by_name("Band%d" % int(band))
        nrows = self.read_sheet.nrows
        CL_found, current_row = self.get_CL_idx(nrows,int(cl))

        if CL_found == False :
            return "ERROR"

        current_col, status_col = self.get_column_for_test(self.read_sheet,scen_name)
        status = self.read_sheet.cell(current_row,status_col-1).value
        print "get scneario status",status
        print current_row
        return status


    def good_cl(self,branch,band,scen_name,cl):

        i = Tools().find_index(BRANCH_ALLOWED,branch)
        self.excel = EXCEL_FLIST[i]

        read_book = open_workbook(self.excel, formatting_info=True)
        self.read_sheet = read_book.sheet_by_name("Band%d" % int(band))
        nrows = self.read_sheet.nrows
        CL_found, _current_row = self.get_CL_idx(nrows,int(cl))
        if CL_found == False :
            return "ERROR"
            #_current_row = nrows - 1

        for current_row in range(_current_row,LIN_INFO,-1):
           #print current_row
           current_col, status_col = self.get_column_for_test(self.read_sheet,scen_name)
           status = self.read_sheet.cell(current_row,status_col-1).value
           if status == STATUS_OK :
                return int(self.read_sheet.cell(current_row,COL_CL).value)

        return "ERROR"
        
        
    def previous_cl_status(self,branch,band,scen_name,cl):

        i = Tools().find_index(BRANCH_ALLOWED,branch)
        self.excel = EXCEL_FLIST[i]

        read_book = open_workbook(self.excel, formatting_info=True)
        self.read_sheet = read_book.sheet_by_name("Band%d" % int(band))
        nrows = self.read_sheet.nrows
        CL_found, _current_row = self.get_CL_idx(nrows,int(cl))
        if CL_found == False :
            return "ERROR"
            #_current_row = nrows - 1

        for current_row in range(_current_row,LIN_INFO,-1):#from previous cl
           #print current_row
            current_col, status_col = self.get_column_for_test(self.read_sheet,scen_name)
            status = self.read_sheet.cell(current_row,status_col-1).value
            if status in EXCEL_STATUS and int(cl) != int(self.read_sheet.cell(current_row,COL_CL).value) :
                return int(self.read_sheet.cell(current_row,COL_CL).value),status

        return "ERROR"

    def last_build_success(self,branch,cl,band=4):
       i = Tools().find_index(BRANCH_ALLOWED,branch)
       self.excel = EXCEL_FLIST[i]
       print self.excel
       read_book = open_workbook(self.excel, formatting_info=True)
       self.read_sheet = read_book.sheet_by_name("Band%d" % int(band))
       nrows = self.read_sheet.nrows
       print nrows
       print cl
       #CL_found, _current_row = self.get_CL_idx(nrows,int(cl))
##       if CL_found == False :
##            print "Error"
##            return "ERROR"

       for current_row in range(nrows,LIN_INFO,-1):
            try:
                cl = self.read_sheet.cell(current_row,COL_CL).value
                print "Good_CL",cl
                print current_row
                if cl != "" :
                    return int(cl)
            except:
                pass
       return "ERROR"


    def get_column_for_ftp(self,read_sheet,title,iclo=0,ichi=100000,level=0):
        for cl in range(iclo,ichi):
            if self.read_sheet.cell(LIN_NAME+2,cl).value == title:
                return cl

        return 0

    def get_column_for_test(self, read_sheet,title,iclo=0,ichi=100000,level=0):
        for crange in read_sheet.merged_cells:
            rlo, rhi, clo, chi = crange
            # Get only Cell starting to the first line
            if clo >= iclo and chi <= ichi :
                if rlo == (LIN_NAME+level):
                    if read_sheet.cell(rlo,clo).value == title:
                        # print "Cell found for %s (clo=%d chi=%d)" % (read_sheet.cell(rlo,clo).value, clo, chi)
                        return (clo, chi)
            # If nothing is found -> First time this test is performed -> Create new Column in excel sheet
        return (0, 0)


    def get_overall_status(self, CL_found, read_sheet, line):
        if not CL_found:
            return STATUS_OK
        overall_status = read_sheet.cell(line,COL_OVERALL_STATUS).value
        #assert(overall_status in (STATUS_REGRESSION, STATUS_ASSERT, STATUS_OK, STATUS_ERROR)) #NSAIT
        #print "overall status is", overall_status
        return overall_status

    def get_CL_idx(self, nrows,cl):
        # Read each CL starting from the last one. Should all be order in increasing value -> MANDATORY -> RV - Need to check that
        for line in range (nrows-1, LIN_INFO, -1):    # RV - Verify that LIN_INFO
            if self.read_sheet.cell(line,COL_CL).value != "" :
                last_read_cl = int(self.read_sheet.cell(line,COL_CL).value)
                if last_read_cl == cl:
                    #print "CL%d found with line %d" % (cl, line)
                    return True, line
                if last_read_cl < cl:
                    #print "Last CL%d is older than the CL%d -> return new line", line, "found for", int(self.read_sheet.cell(line,COL_CL).value)
                    return False, line+1
        # Weird case: a very old CL is tested
        #print "Warning: Weird case, a very old CL is tested"
        return False, nrows




if __name__ == '__main__':
    Chart()._chart()