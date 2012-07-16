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
import sys, visa, time, icera.datacard, os, os.path, threading, subprocess, re, locale,ssh,shutil
from ftplib import FTP
from xlwt import Workbook, easyxf
from xlrd import open_workbook, cellname
from xlutils.copy import copy
from flasher import *
from chart import *
from global_var import *
from device_management import *
from tools import *
import common
import socket

class Cardhu():

    def config_init(self):
        self.remark = ""
        self.cl = 0
        self.band = 4
        self.scen_name = "FTP_DL_SISO_AM_RB50_TBS25"
        self.comport = common.PORT_COM_TANGO
        file = 'status.txt'
        if os.path.exists(file):
            os.remove(file)

    def init_param_for_startup(self):
        # Init to error state by default
        self.status = STATUS_ERROR
        self.error  = ERROR_NO_INIT_YET


    def run_campaign(self, campaign):
        if os.path.isfile(campaign+'.ini'):
            self.init_param_for_startup()
            print "The campaign %s is found" % campaign
            count_scen = 0
            camp_file = open(campaign+'.ini', 'r')
            camp_file_r = camp_file.read()
            for scen_name in camp_file_r.split('\n'):
                print "\n\nScenario: %s" % scen_name
                if self.run_reg_now:
                    # regression asked to be run now -> skip all other remaining test
                    print "Run Reg now so skip all remaining test"
                    return
                if scen_name in scenario_implemented:
                    if self.available_scenario_name(scen_name):
                        if self.scen_not_pass_yet(): # Check that the test is not already pass for this CL
                            print "\n--->Start scenario: %s (in Band%d)" % (scen_name, int(self.band))
                            # Start Sequence
                            self.test_sequence()
                            count_scen += 1
                        else:
                            self.log_status("ALREADY_DONE")
                            print "%s already done" % scen_name
                else:
                    print "%s not in test plan" % scen_name
            camp_file.close()
            # Close AT Port
            self.close_connection()
        else:
            print "\nError: The campaign %s is not valid" % campaign

    def log_status(self,status):
        FILE = open('status.txt','a')
        FILE.write("[CL%d Branch:%s Band:%d Test:%s Status:%s] \n" % (self.cl,branch,int(self.band),self.scen_name,status))
        FILE.close()

    def run_scenario(self, scen_name,Forced=False):
        if self.available_scenario_name(scen_name):
            self.init_param_for_startup()
            if self.scen_not_pass_yet() or Forced: # Check that the test is not already pass for this CL
                print "--->Start scenario: %s (in Band%d)" % (scen_name, int(self.band))
                #Info in Status.txt
                # Start Sequence
                self.test_sequence()
                # Close AT Port
                self.close_connection()
            else:
                self.log_status("ALREADY_DONE")
                print "%s already done" % scen_name

    # RV - Simplify the function
    def scen_not_pass_yet(self):
        print "\nChecking if scenario already pass.."
        # Check that the excel file exist
        if not os.path.isfile(EXCEL_FILE):
            print "Test to run -> excel file does not exist"
            return True
        read_book = open_workbook(EXCEL_FILE, formatting_info=True)
        read_sheet = read_book.sheet_by_name("Band%d" % int(self.band))
        # Check that the last CL corresponds to the CL tested
        line = self.get_line_with_CL(read_sheet, self.cl)
        if not line:
            print "Test to run -> the CL%d was never performerd" % self.cl
            return True
        current_col, status_col = self.get_column_for_test(read_sheet)
        # Check that the test was never performed
        if current_col == 0 or status_col == 0:
            print "Test to run -> the test was never performed"
            return True
        # Check that the Status is not OK
        status = read_sheet.cell(line,status_col-1).value
        print "The Status is: %s" % status
        if status == STATUS_OK:
            print "Test already run -> the Status is OK"
            return False
        if status in (STATUS_REGRESSION, STATUS_ASSERT):
            if not force_retest_when_regression_or_assert:
                print "No re-test for this regression or assert (set by parameters)"
                return False
        print "Test to run -> no other condition to check"
        return True

    def available_scenario_name(self, scen_name):
        self.find_max_dl_rate = 0
        self.dl = 0
        self.ul = 0
        if self.band is None:
            self.band = 1
        # self.tm = 1
        # self.test_cpuload = 0
        # self.dl = 0
        # self.ul = 0
        # self.dl_file_size = 500
        # self.ul_file_size = 50
        # self.ltemeas = 0
        # self.clock = 0
        # Check Band
        if re.search("BAND17_", scen_name):
            self.band = 17
            scen_name = scen_name.replace("BAND17_", "")
        elif re.search("BAND4_", scen_name):
            self.band = 4
            scen_name = scen_name.replace("BAND4_", "")
        elif re.search("BAND1_", scen_name):
            self.band = 1
            scen_name = scen_name.replace("BAND1_", "")
        # # Check Cell
        # if re.search("SISO"):
        #     self.tm = 1
        # elif re.search("SIMO"):
        #     self.tm = 2
        # elif re.search("MIMO"):
        #     self.tm = 3
        # else:
        #     print "Warning: No Cell defined - SISO(default), SIMO or MIMO"
        # # Check Test Type
        # if re.search("ATTACH"):
        #     self.test_cpuload = 0
        # elif re.search("PING"):
        #     self.test_cpuload = 0
        # elif re.search("FTP"):
        #     self.test_cpuload = 1
        # else:
        #     self.test_cpuload = 0
        #     print "Warning: No test type defined - ATTACH(default), PING or FTP"
        # Check Test Type
        if re.search("FTP_DL_", scen_name):
            self.dl = 1
            self.regression_delta = REGRESSION_DELTA_DOWNLINK
        elif re.search("FTP_UL_", scen_name):
            self.ul = 1
            self.regression_delta = REGRESSION_DELTA_UPLINK
        elif re.search("FTP_COMB_DLUL_", scen_name):
            self.dl = 1
            self.ul = 1
            self.regression_delta = REGRESSION_DELTA_UPLINK
        else:
            self.regression_delta = REGRESSION_DELTA_DOWNLINK
            print "ERROR: test not conformed"
            assert(False)
        # # Check Test Type
        # if re.search("_1_FILE"):
        #     self.num_files_in_ul = 1
        # elif re.search("_2_FILES"):
        #     self.num_files_in_ul = 2
        # elif re.search("_3_FILES"):
        #     self.num_files_in_ul = 3
        # # Check Measurement and Dxp Clock
        # if re.search("_MEAS_1"):
        #     self.ltemeas = 1
        # self.dl_file_size = 500
        self.dl_file_size = 1000
        self.ul_file_size = 50
        self.test_cpuload = 1
        self.tm = 1
        self.rlc_mode = "UM"
        self.ltemeas = -1        ##### CHECK THAT DISABLE on main.br
        self.clock = 0
        if re.search("FTP_DL_SISO_AM_RB50_TBS25_", scen_name):
            self.tm = 1 # self.tm = 2
            self.dl_rb     = 50
            self.dl_tbsidx = 25
            self.ul_rb     = 3
            self.ul_tbsidx = 15
            self.rlc_mode = "AM"
            self.dl_file_size = 1000
        elif re.search("FTP_DL_SISO_AM_RB50_TBS26_", scen_name):
            self.tm = 1 # self.tm = 2
            self.dl_rb     = 50
            self.dl_tbsidx = 26
            self.ul_rb     = 3
            self.ul_tbsidx = 15
            self.rlc_mode = "AM"
            self.dl_file_size = 1000
        elif re.search("FTP_DL_MIMO_AM_RB39_TBS25_", scen_name):
            self.tm = 3
            self.rlc_mode = "AM"
            self.dl_rb     = 39
            self.dl_tbsidx = 25
            self.ul_rb     = 4
            self.ul_tbsidx = 16
            self.dl_file_size = 1000
        elif re.search("FTP_DL_MIMO_AM_RB42_TBS24_", scen_name):
            print "Inside FTP_DL_MIMO_AM_RB42_TBS24_"
            self.tm = 3
            self.rlc_mode = "AM"
            self.dl_rb     = 42
            self.dl_tbsidx = 24
            self.ul_rb     = 4
            self.ul_tbsidx = 16
            self.dl_file_size = 1000
        elif scen_name == "ATTACH_SISO":
            self.test_cpuload = 0
        elif scen_name == "ATTACH_MIMO":
            self.test_cpuload = 0
            self.tm = 3
        elif scen_name == "PING_SISO":
            self.test_cpuload = 0
        elif scen_name == "PING_MIMO":
            self.test_cpuload = 0
            self.tm = 3
        elif scen_name == "FTP_DL_SISO_AM_RB50_TBS25":
            self.tm = 1 # self.tm = 2
            self.dl_rb     = 50
            self.dl_tbsidx = 25
            self.ul_rb     = 3
            self.ul_tbsidx = 15
            self.rlc_mode = "AM"
        elif scen_name == "FTP_DL_SISO_AM_RB50_TBS26":
            self.tm = 1 # self.tm = 2
            self.dl_rb     = 50
            self.dl_tbsidx = 26
            self.ul_rb     = 4
            self.ul_tbsidx = 16
            self.rlc_mode = "AM"
        elif scen_name == "FTP_DL_AM_RB45_TBSIDX24":
            self.dl_rb     = 45
            self.dl_tbsidx = 24
            self.ul_rb     = 10
            self.ul_tbsidx = 10
            self.rlc_mode = "AM"
        elif scen_name == "FTP_UL_UM_MAX_1_FILE":
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 50
            self.ul_tbsidx = 19
            self.num_files_in_ul = 1
        elif scen_name == "FTP_UL_UM_MAX_2_FILES":
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 50
            self.ul_tbsidx = 19
            self.num_files_in_ul = 2
        elif scen_name == "FTP_UL_UM_MAX_3_FILES":
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 50
            self.ul_tbsidx = 19
            self.num_files_in_ul = 3
        elif scen_name == "FTP_UL_UM_RB45_TBSIDX18_1_FILE":
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 45
            self.ul_tbsidx = 18
            self.num_files_in_ul = 1
        elif scen_name == "FTP_UL_AM_RB45_TBSIDX18_2_FILES":
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 45
            self.ul_tbsidx = 18
            self.num_files_in_ul = 2
            self.rlc_mode = "AM"
            self.ul_file_size = 500
        elif scen_name == "FTP_UL_AM_RB40_TBSIDX16_2_FILES":
            self.dl_rb     = 4
            self.dl_tbsidx = 15
            self.ul_rb     = 40
            self.ul_tbsidx = 16
            self.num_files_in_ul = 2
            self.rlc_mode = "AM"
            self.ul_file_size = 500
        elif re.search("FTP_UL_AM_RB50_TBSIDX18_2_FILES_", scen_name):
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 50
            self.ul_tbsidx = 18
            self.num_files_in_ul = 2
            self.rlc_mode = "AM"
            self.ul_file_size = 500
        elif scen_name == "FTP_UL_AM_RB45_TBSIDX18_2_FILES":
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 45
            self.ul_tbsidx = 18
            self.num_files_in_ul = 2
            self.rlc_mode = "AM"
            self.ul_file_size = 500 # Added since around CL453170
        elif re.search("FTP_UL_AM_OOS_SEARCH_RB45_TBS18_2_FILES_", scen_name):
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 45
            self.ul_tbsidx = 18
            self.num_files_in_ul = 2
            self.rlc_mode = "AM"
            self.ul_file_size = 500
        elif re.search("FTP_UL_AM_OOS_SEARCH_RB50_TBS18_2_FILES_", scen_name):
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 50
            self.ul_tbsidx = 18
            self.num_files_in_ul = 2
            self.rlc_mode = "AM"
            self.ul_file_size = 500
        elif scen_name == "FTP_UL_AM_MAX_2_FILES":
            self.dl_rb     = 4
            self.dl_tbsidx = 16
            self.ul_rb     = 50
            self.ul_tbsidx = 19
            self.num_files_in_ul = 2
            self.rlc_mode = "AM"
        elif scen_name == "FTP_UL_UM_RB45_TBSIDX18_2_FILES":
            self.dl_rb     = 10
            self.dl_tbsidx = 9
            self.ul_rb     = 45
            self.ul_tbsidx = 18
            self.num_files_in_ul = 2
        elif scen_name == "FTP_COMB_DLUL_1_FILE_UL":
            self.dl_rb     = 25
            self.dl_tbsidx = 24
            self.ul_rb     = 25
            self.ul_tbsidx = 16
            self.num_files_in_ul = 1
            self.dl_file_size = 100   # Special Tune to be sure that the DL and UL transfer will terminate at the same time
        elif scen_name == "FTP_COMB_DLUL_2_FILES_UL":
            self.dl_rb     = 25
            self.dl_tbsidx = 24
            self.ul_rb     = 25
            self.ul_tbsidx = 16
            self.num_files_in_ul = 2
            self.dl_file_size = 200   # Special Tune to be sure that the DL and UL transfer will terminate at the same time
        elif scen_name == "FTP_DL_MIMO_AM_RB39_TBS24":
            self.tm = 3
            self.rlc_mode = "AM"
            self.dl_rb     = 39
            self.dl_tbsidx = 24
            self.ul_rb     = 4
            self.ul_tbsidx = 16
        elif scen_name == "FTP_DL_MIMO_AM_RB39_TBS25":
            self.tm = 3
            self.rlc_mode = "AM"
            self.dl_rb     = 39
            self.dl_tbsidx = 25
            self.ul_rb     = 4
            self.ul_tbsidx = 16
        elif scen_name == "FTP_DL_MIMO_AM_RB42_TBS24":
            print "Inside FTP_DL_MIMO_AM_RB42_TBS24_"
            self.tm = 3
            self.rlc_mode = "AM"
            self.dl_rb     = 42
            self.dl_tbsidx = 24
            self.ul_rb     = 4
            self.ul_tbsidx = 16
        elif scen_name == "FTP_DL_MIMO_AM_FIND_MAX_DEFAULT":
            self.tm = 3
            self.rlc_mode = "AM"
            # self.dl_rb     = 39
            # self.dl_tbsidx = 24
            self.find_max_dl_rate = 1
            self.dl_rb     = RB_START
            self.dl_tbsidx = TBSIDX_START
            self.ul_rb     = 4
            self.ul_tbsidx = 16
            # self.dl_file_size = 1000
        elif scen_name == "DEBUG":
            self.tm = 3
            self.dl_rb     = RB_START
            self.dl_tbsidx = TBSIDX_START
            self.ul_rb     = 3
            self.ul_tbsidx = 16
            self.clock   = 1400
            self.find_max_dl_rate = 1
        else:
            print "\nThe scenario is not implemented yet"
            self.scen_name = ""
            return False
        self.scen_name = scen_name
        return True

    ########################################################
    ##               CALLBOX functions for start up
    ########################################################
    def callbox_comm(self):
        print "\nGetting Callbox communication..."
        from visa import instrument
        try:
            command = "TCPIP0::" + FTP_ADDRESS + "::inst0::INSTR"
            # print "command=", command
            self.callbox = instrument(command)        # RV - SHOULD GET A FIXED DOMAIN
        except:
            Tools().sendMail(r"TCPIP error - Check instruments")
            print 'TCPIP error - Check instruments'
            raise

    def callbox_reset(self):
        print "\nResetting Callbox..."
        # Reset the CALLBOX
        # self.callbox.write("*RST;*OPC?")    # RV - OPC (Operation Complete) return "1" as soon as all precedings commands have been executed
        time.sleep(1)
        self.callbox.write("*CLS;*OPC?")    # RV - (need send and read)
        # Allow to observe the screen in remote control (the front panel are still disabled).
        self.callbox.write("SYSTem:DISPlay:UPDate ON")

    def cell_setup(self):
        print "\nSetup the Cell..."
        # Config the Cell to SISO or MIMO ?
        if self.tm > 2:
            self.cell_mimo()
        elif self.tm == 2:
            self.cell_simo()
        else:
            self.cell_siso()
        # Specify general setting
        self.cell_init()
        # Check if MIMO is enabled
        if self.tm > 1:
            self.cell_setup_mimo()
        # Configure the band
        self.config_band()
        # Configure DL power
        self.config_dl_power()
        # Configure Network settings
        self.config_network_settings()
        # Configure Connection settings
        if self.tm == 1:
            self.user_def_channel_siso()
        else:
            self.user_def_channel_mimo()
        # Get theorical throughput retrieved from Callbox
        self.get_theorical_throughput()

    def cell_siso(self):
        self.callbox.write("ROUTe:LTE:SIGN<i>:SCENario:SCELl")

    def cell_simo(self):
        self.callbox.write("ROUTe:LTE:SIGN<i>:SCENario:TRO")
        self.callbox.write("CONFigure:LTE:SIGN<i>:CONNection:TSCHeme SIMO")

    def cell_mimo(self):
        self.callbox.write("ROUTe:LTE:SIGN<i>:SCENario:TRO")
        self.callbox.write("CONFigure:LTE:SIGN<i>:CONNection:TSCHeme OLSMultiplex")

    def cell_init(self):
        # Define input and output path for a standard cell, including
        # signal routing and external attenuation.
        self.callbox.write("ROUTe:LTE:SIGN:SCENario:SCELl RF1C,RX1,RF1C,TX1")
        # self.callbox.write("CONFigure:LTE:SIGN:RFSettings:EATTenuation:OUTPut 2") # NEEDED ?
        # self.callbox.write("CONFigure:LTE:SIGN:RFSettings:EATTenuation:INPut 2") # NEEDEED ?

    def cell_setup_mimo(self):
        # Define paths for MIMO.
        self.callbox.write("ROUTe:LTE:SIGN:SCENario:MIMO22 RF1C,RX1,RF1C,TX1,RF3C,TX2")

    def config_band(self):
        # Define channel bandwidth 10 MHz (by default)
        self.callbox.write("CONFigure:LTE:SIGN:CELL:BANDwidth:DL B100")
        if self.band == 1:
            self.callbox.write("CONFigure:LTE:SIGN:BAND OB1")
            self.callbox.write("CONFigure:LTE:SIGN:RFSettings:CHANnel:DL 300 ;UL?")
        elif self.band == 4:
            self.callbox.write("CONFigure:LTE:SIGN:BAND OB4")
            self.callbox.write("CONFigure:LTE:SIGN:RFSettings:CHANnel:DL 2175 ;UL?")
        elif self.band == 17:
            self.callbox.write("CONFigure:LTE:SIGN:BAND OB17")
            self.callbox.write("CONFigure:LTE:SIGN:RFSettings:CHANnel:DL 5790 ;UL?")
        else:
            print "Error: the band is not valid"
            assert(False)

    def config_dl_power(self):
        # Define the RS EPRE level
        self.callbox.write("CONFigure:LTE:SIGN:DL:RSEPre:LEVel -80")

    def config_network_settings(self):
        # Enable authentication, NAS security, AS security.
        self.callbox.write("CONFigure:LTE:SIGN:CELL:SECurity:AUTHenticat ON")
        self.callbox.write("CONFigure:LTE:SIGN:CELL:SECurity:NAS ON")
        self.callbox.write("CONFigure:LTE:SIGN:CELL:SECurity:AS ON")
        # Define integrity algorithm.
        self.callbox.write("CONFigure:LTE:SIGN:CELL:SECurity:IALGorithm S3G")
        # Disable DL padding
        self.callbox.write("CONFigure:LTE:SIGN:CONNection:DLPadding OFF")
        # Data Application mode
        self.callbox.write("CONFigure:LTE:SIGN:CONNection:CTYPe DAPPlication")

    def config_rlc_mode(self):
        # Set RLC mode
        if self.rlc_mode in ("AM", "UM"):
            command = "CONFigure:LTE:SIGN:CONNection:RLCMode " + self.rlc_mode
            self.callbox.write(command)

    def user_def_channel_siso(self):
        # Select user defined channels as scheduling type
        self.callbox.write("CONFigure:LTE:SIGN:CONNection:UETerminate UDCH")
        # DL channel with 50 RBs starting with RB number 0 and 64-QAM modulation
        # UL channel with 10 RBs starting with RB number 0 and QPSK modulation.
        # The transport block size index is selected automatically.
        self.modif_dl_throughput(self.dl_rb,self.dl_tbsidx)
        self.modif_ul_throughput(self.ul_rb,self.ul_tbsidx)

    def user_def_channel_mimo(self):
        # Select user defined channels as scheduling type
        self.callbox.write("CONFigure:LTE:SIGN:CONNection:UETerminate UDCH")
        # Define the same user defined channel for the second MIMO downlink stream.
        self.modif_dl_throughput(self.dl_rb,self.dl_tbsidx, "DL1")
        self.modif_dl_throughput(self.dl_rb,self.dl_tbsidx, "DL2")
        self.modif_ul_throughput(self.ul_rb,self.ul_tbsidx)

    def ftp_settings(self):
        print "\nSetup FTP server..."
        # Specify the FTP service type
        self.callbox.write("CONFigure:DATA:CONTrol:FTP:STYPE SERVer")
        self.callbox.write("CONFigure:DATA:CONTrol:FTP:AUSer ON")
        self.callbox.write("CONFigure:DATA:CONTrol:FTP:DUPLoad ON")
        self.callbox.write("CONFigure:DATA:CONTrol:FTP:IPVSix OFF")
        # Switch the FTP service on, signal available
        self.callbox.write("SOURce:DATA:CONTrol:FTP:STATe ON")

    def cell_on(self):
        print "\nSwitching to cell ON..."
        # Handle the timeout delay
        a = time.time()
        b = time.time()
        # Switch on the DL signal.
        self.callbox.write("1;SOURce:LTE:SIGNaling:CELL:STATe ON")
        # Query the cell state until it equals ON,ADJ (DL signal available at RF connector).
        status = self.callbox.ask("1;SOURce:LTE:SIGNaling:CELL:STATe:ALL?")
        print "Status:", status
        if status != CELL_STATUS_ON:
            print "[Info]timeout is %s sec" % TIMEOUT_DELAY
            while status != CELL_STATUS_ON and (b-a) <= TIMEOUT_DELAY:
                b = time.time()
                print "[Info]delay:", int(b-a), "s"
                status = self.callbox.ask("1;SOURce:LTE:SIGNaling:CELL:STATe:ALL?")
                time.sleep(3)
            print "Status:", status
        if status != CELL_STATUS_ON:
            print "ERROR! LTE SIGNaling CELL status is incorrect"
            Tools().sendMail("ERROR! LTE SIGNaling CELL status is incorrect")
            sys.exit(-1)
        time.sleep(2)

    def config_meas_report(self): ########## RV - NOT USED
        # Disable measurement reports.
        self.callbox.write("CONFigure:LTE:SIGN:UEReport:ENABle OFF")

    def get_ue_ipv4_address(self):
        time.sleep(2)
        # Get the IPv4 address assigned by the UE by the R&S Callbox.
        self.ue_addr_ipv4 = self.callbox.ask("SENSe:LTE:SIGN:UEADdress:IPV4?")
        print "UE address is", self.ue_addr_ipv4
        # Check that the IPv4 is compatible with the internal FTP server address (starting with 172.22.1.x)
        try:
            self.ue_addr_ipv4 = re.sub("\"", "", self.ue_addr_ipv4)
            if not re.search("172\.22\.1\.", self.ue_addr_ipv4):
                print "Warning: The IPv4 is not compatible with the internal FTP server address (starting with 172.22.1.x)"
        except:
            print "Warning: Not possible to check if the UE has a correct IPv4 address"

    ########################################################
    ##               CALLBOX functions utils
    ########################################################
    def check_cell_mimo_siso(self): # NOT WORKING YET
        cell_scenario = self.callbox.ask("ROUTe:LTE:SIGN<i>:SCENario?")
        print "cell_scenario=", cell_scenario

    def get_theorical_throughput(self):
        # Query the resulting maximum expected throughput.
        ulThoughput  = self.callbox.ask("CONFigure:LTE:SIGN:CONNection:ETHRoughput:UL?")
        dlThoughput1 = self.callbox.ask("CONFigure:LTE:SIGN:CONNection:ETHRoughput:DL:STReam1?")
        print "DL throughput: (stream1)", dlThoughput1
        if self.tm > 1:
            # Query the resulting maximum expected throughput for that stream and for all downlink streams together.
            dlThoughput2 = self.callbox.ask("CONFigure:LTE:SIGN:CONNection:ETHRoughput:DL:STReam2?")
            dlThoughput  = self.callbox.ask("CONFigure:LTE:SIGN:CONNection:ETHRoughput:DL:ALL?")
            print "DL throughput (stream2):", dlThoughput2
            print "DL throughput:", dlThoughput
        print "UL throughput:", ulThoughput

    def modif_dl_throughput(self, rb, tbsidx, stream="DL"):
        if not stream in ("DL", "DL1", "DL2"):
             print "Error: the stream %s is not valid. Required DL, DL1 or DL2" % stream
        if rb > 50:
            print "Error: the rb (%s) in DL must be set up to 50" % rb
            return
        if tbsidx <= 9 :
            modulation = "QPSK"
        elif tbsidx <= 15:
            modulation = "Q16"
        elif tbsidx <= 26:
            modulation = "Q64"
        else:
            print "Error: the tbsidx (%s) in DL must be set up to 26" % tbsidx
            return
        # The transport block size index is selected automatically.
        config_udch_dl = "CONFigure:LTE:SIGN:CONNection:UDCHannels:%s %d,0,%s,%d" % (stream, rb, modulation, tbsidx)
        # Got once a python issue with visa module to write the following line.
        self.callbox.write(config_udch_dl)

    def modif_ul_throughput(self, rb, tbsidx):
        if rb > 50:
            print "Error: the rb (%s) in UL must be set up to 50" % rb
            return
        if tbsidx <= 10 :
            modulation = "QPSK"
        elif tbsidx <= 19:
            modulation = "Q16"
        else:
            print "Error: the tbsidx (%s) in UL must be set up to 19" % tbsidx
            return
        # The transport block size index is selected automatically.
        config_udch_ul = "CONFigure:LTE:SIGN:CONNection:UDCHannels:UL %s,0,%s,%s" % (rb, modulation, tbsidx)
        self.callbox.write(config_udch_ul)

    ########################################################
    ##               CALLBOX functions for init
    ########################################################
    def checking_cfun(self, wait_condition):
        # return True         ###################################### PATCH HERE FOR WRITEFILE ERROR
        # cfun = self.at.sendhidden('at+cfun?')
        # print "cfun=", cfun
        search_cfun = 'CFUN: %d' % wait_condition
        print "search_cfun=", search_cfun
        # match=re.search(search_cfun, cfun)
        match, cfun = self.check_at_command(search_cfun, 'at+cfun?')
        print "cfun=", cfun
        return (match != None)

    def ue_startup(self):
        # Starting the UE
        print "\nStarting UE..."
        self.send_cmd('at+cfun=0')
        self.send_cmd('at%debug=99')
        self.send_cmd('at%ifullcoredump=1') # activate full coredump
        time.sleep(10)              # RV - Tune Value need to automate that
        # Set RLC mode here                 # RV - CHANGE THE PLACE
        self.config_rlc_mode()
        self.send_cmd('at%icpuload=0')
        self.send_cmd('at%isimemu=1')
        time.sleep(3)
        # self.at.send('at%isdns') ### RV - Current workaround to avoid attach issue due to information transfer flag enabled
        # time.sleep(3)
        self.send_cmd('at+cfun=1')
        self.send_cmd('at%ifullcoredump=1') # activate full coredump
        time.sleep(5)

    def active_pdpcontext(self):
        self.send_cmd('at%ipdpact=5,1') # CHECK THAT the action is OK
        time.sleep(2)
        self.apm = self.send_cmd('at%iapm?')

    def set_lte_only(self):
        self.send_cmd('at%inwmode=1,E4E17,1')
        self.send_cmd('at%inwmode=0,E,1,2,1')
        time.sleep(2)

    def wait_attach(self):
        return True
        print "\nWaiting for UE attach..."
        # Handle the timeout delay
        a = time.time()
        b = time.time()
        # Switch on the DL signal.
        self.callbox.write("1;SOURce:LTE:SIGNaling:CELL:STATe ON")
        # Switch on the UE and wait until it is attached (connection state = ATT).
        status = self.callbox.ask("1;FETCh:LTE:SIGN:PSWitched:STATe?")
        print "Status:", status
        if status != ATTACH_STATUS:
            print "[Info]timeout is %s sec" % TIMEOUT_DELAY
            while status != ATTACH_STATUS and (b-a) <= TIMEOUT_DELAY:
                b = time.time()
                print "[Info]delay:", int(b-a), "s"
                status = self.callbox.ask("1;FETCh:LTE:SIGN:PSWitched:STATe?")
                time.sleep(3)
            print "Status:", status
        time.sleep(2)
        if status != ATTACH_STATUS:
            print "ERROR! LTE SIGNaling UE status is incorrect"
            return False
        return True

    def cardhu_alive(self):
        time.sleep(2)
        return True

    def restart_cardhu(self):
        time.sleep(10)
        return True

    def send_cmd(self,cmd):
        self.sock.send(cmd+'\r\n')
        time.sleep(1)
        data = self.sock.recv(1024)
        if data:
            return data
        else:
            return "ERROR"

    def get_ue_port(self):
        print "\nGetting UE port..."
        attemptIdx = 0
        success = False
        power_used = False
        while success == False and attemptIdx < UE_STARTUP_ATTEMPT_MAX:
            time.sleep(UE_STARTUP_DELAY)
            print "Attempt number:", attemptIdx
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
                        success = True
                        return success
            except:
                print "exception"
                raise

            print "Cannot open port "+common.AT_PORT+", restarting..."
            attemptIdx += 1
            if not power_used and attemptIdx > (UE_STARTUP_ATTEMPT_MAX/2):
                print "Warning: No UE port found -> use power cycle"
                self.power_cycle()
                power_used = True
        if success != True:
            print "ERROR (even after power cycle): CHECK YOUR SETUP!!!"
            Tools().sendMail(r"ERROR (even after power cycle): CHECK YOUR SETUP!!!")
            sys.exit()

    def get_cl(self):
        print "\nRetrieving CL to test..."
        # Necessary to flush the AT reply
        self.send_cmd('at')
        time.sleep(2)
        # self.p4_cl = self.at.sendhidden('at+gmr')
        # print self.p4_cl
        match, self.p4_cl = self.check_at_command('P4 rev: CL(\d+)', 'at+gmr')
        # match=re.search('P4 rev: CL(\d+)',self.p4_cl)
        if match:
            self.cl = int(match.group(1))
            print "CL revision found:", self.cl
            self.send_cmd('at%ifullcoredump=1')

        else:
            print "CL not found --- > Power Cycling"
            self.power_cycle()
            self.get_ue_port()
            self.send_cmd('at')
            time.sleep(2)
            match, self.p4_cl = self.check_at_command('P4 rev: CL(\d+)', 'at+gmr')
            if match:
                self.cl = int(match.group(1))
                print "CL revision found:", self.cl
                self.send_cmd('at%ifullcoredump=1')
            else:
                print "CL not found "
                assert(False)

    # Increase the chance to get the write response since a delay of response can happen
    def check_at_command(self, search_pattern, command):
        if self.send_cmd == "ERROR":
            print "Error: AT not open when checking at Command"
            return None, ""
        response_to_check = self.send_cmd(command)
        match=re.search(search_pattern,response_to_check)
        # return match, response_to_check
        if match == None:
            if command == 'at':
                return None, response_to_check
            time.sleep(2)
            print "Second attempt to get good pattern", search_pattern
            match, response_to_check = self.check_at_command(search_pattern, 'at')
        return match, response_to_check

    def clean_assert_report(self):
        print "\nCleaning assert report..."
        time.sleep(2)
        self.send_cmd('at%debug=99')

    def download_coredump(self,forced=False):
        time.sleep(2)
        if device_management().sys_status(False) == "DOWNLOAD_ONLY" or forced == True:
            at_debug=At_debug()
            at_debug.get_coredump(branch,self.cl,"CL"+str(self.cl)+"_BRANCH_"+branch+self.scen_name+"_Band"+str(self.band)+"_"+time.strftime("%d_%b_%Y_%H_%M_%S", time.gmtime()),"minicoredump")
            at_debug.get_coredump(branch,self.cl,"CL"+str(self.cl)+"_BRANCH_"+branch+self.scen_name+"_Band"+str(self.band)+"_"+time.strftime("%d_%b_%Y_%H_%M_%S", time.gmtime()),"fullcoredump")
            # at_debug.get_coredump(branch,self.cl,"CL"+str(self.cl)+"_BRANCH_"+branch+self.scen_name+"_Band"+str(self.band)+"_"+time.strftime("%d_%b_%Y_%H_%M_%S", time.gmtime()),"clear_history")

    def check_assert_report(self, dl_rb, dl_tbsidx):
        print "\nChecking for Assert/Afault..."
        self.download_coredump()
        if self.status == STATUS_ASSERT:
            print "Already in ASSERT state -> no check for assert again"
            return False
        time.sleep(2)
        self.assert_report = self.get_full_reply('at%debug')
        match=re.search('No Crash History Stored',self.assert_report)
        if match:
            print "No Assert/Afault"
            return False
        match=re.search('Boot Counter:.*(\d+)', self.assert_report)
        if match:
            self.download_coredump(forced=True)
            # print self.assert_report
            number_assert = match.group(1)
            if number_assert > 1:
                print "Warning: more than one Assert/Afault fired since the begining of the test"
            self.generate_assert_file(dl_rb, dl_tbsidx)
            self.status = STATUS_ASSERT
            # Clean Assert report again
            self.clean_assert_report()
            return True
        else:
            print "Warning: No match to retreive Assert"
        return False

    def get_full_reply(self, command):
        is_not_finished = True
        count = 0
        # Get full replay when at command speak a lot
        reply = self.add_robustness(command)
        while is_not_finished and count < 6:
            time.sleep(1)
            # Ask with
            at = self.send_cmd('at')
            if re.search("at(\s+)OK", at):
                is_not_finished = False
            reply += at
            count += 1
        reply = reply.replace("at(\s+)OK","")     # RV - Remove after being sure that no incidence
        return reply

    def add_robustness(self, command):
        is_not_finished = True
        count = 0
        while count < 6:
            try:
                reply = self.send_cmd(command)
                return reply
            except:
                # second attempt
                self.get_ue_port()
            count += 1
        print "Not Found"
        return ""

    def generate_assert_file(self, dl_rb, dl_tbsidx):
        # Create assert file
        file_name = "ASSERT_%s_CL%d.txt" % (self.scen_name, self.cl)
        FILE = open("./assert/"+file_name,'a')
        FILE.write("Test: %s\n" % self.scen_name)
        FILE.write("Callbox config: DL(%dRB,%dTBSidx) and UL(%dRB,%dTBSidx)\n" % (dl_rb, dl_tbsidx, self.ul_rb, self.ul_tbsidx))
        FILE.write("Band%d, tm%d, dxp_clock=%d, ltemeas=%d\n\n" % (int(self.band), self.tm, self.clock, self.ltemeas))
        FILE.write(self.assert_report+"\n")
        FILE.close()
        msg = r"[Assert Triggered]\n Test:%s\n CL%d Callbox Config :DL(%dRB,%dTBSidx) and UL(%dRB,%dTBSidx)\n"%(self.scen_name,self.cl,dl_rb, dl_tbsidx, self.ul_rb, self.ul_tbsidx)
        Tools().sendMail(msg)
        msg += r"%s"%(self.assert_report)
        Tools().sendMail(msg)

    def log_msg(self, message):
        # Add message in file
        print message
        FILE = open(file_log_message,'a')
        FILE.write("[CL%d Band%d Test:%s] %s\n" % (self.cl, int(self.band), self.scen_name, message))
        FILE.close()

    ########################################################
    ##               CALLBOX functions for sequence
    ########################################################
    def change_throughput(self, dl_rb, dl_tbsidx):
        self.modif_dl_throughput(dl_rb,dl_tbsidx)
        if self.tm > 1:
            self.modif_dl_throughput(dl_rb,dl_tbsidx, "DL2")

    def set_throughput(self):
        self.modif_dl_throughput(self.dl_rb,self.dl_tbsidx)
        self.modif_ul_throughput(self.ul_rb,self.ul_tbsidx)
        if self.tm > 1:
            self.modif_dl_throughput(self.dl_rb,self.dl_tbsidx, "DL2")


    def get_cpuload(self, time_cpuload):
        print "\nGetting cpuload..."
        # RV - Init param at init before each test scenario run
        self.cpu_dxp1 = 0
        self.cpu_dxp0 = 0
        self.cpu_dl_rate = [0, 0, 0]
        self.cpu_ul_rate = [0, 0, 0]
        dxp1_list, dxp0_list, dl_rate_list, ul_rate_list, bler_list, dropped_tti_list = ([], [], [], [], [], [])
        count_no_display = 0
        self.counter_sec = 0
        check_rate_while_runing = False
        try:
            # Start CPU load display
            self.send_cmd('at%icpuload=1,1,1')
        except:
            self.log_msg("Warning: icpuload AT command can not be run")
            pass
        # Wait that all thread finished
        q =  0
        while True:#threading.activeCount()>1: # FTP_DL1.isActive() so on
            q += 1
            if q == 100:
                break
            time.sleep(1)
            self.counter_sec += 1
            try:
                # Retrieve CPU load information
                ave_cpuload = self.send_cmd('at')
                # ave_cpuload = self.at.send('at')
                print "ave_cpuload=", ave_cpuload

                if len(ave_cpuload) < 50:
                    self.log_msg("Warning: no output of icpuload")
                    count_no_display += 1
                    if count_no_display > 20:
                        self.log_msg("Error: no output of icpuload at a row -> Restart Test")
                        self.restart_ftp()
                        dxp1_list, dxp0_list, dl_rate_list, ul_rate_list, bler_list, dropped_tti_list = ([], [], [], [], [], [])
                        check_rate_while_runing = False
                        count_no_display = 0
                        continue
                else:
                    count_no_display = 0
                dxp1_list  += [int(i) for i in re.findall('DXP1=\s*(\d+) D',ave_cpuload)]   # Add ' D' to be sure to get complete value since there is a left shifting character
                dxp0_list  += [int(i) for i in re.findall('DXP0=\s*(\d+),',ave_cpuload)]    # Add ',' to be sure to get complete value since there is a left shifting character
                if self.dl:
                    dl_rate_list += [int(i) for i in re.findall('DL_RATE=\s*(\d+),',ave_cpuload)] # Add ',' to be sure to get complete value since there is a left shifting character
                if self.ul:
                    ul_rate_list += [int(i) for i in re.findall('UL_RATE=\s*(\d+),',ave_cpuload)] # Add ',' to be sure to get complete value since there is a left shifting character
                bler_list    += [float(i) for i in re.findall('BLER=(\d+\.\d+)%',ave_cpuload)]
                dropped_tti_list += [int(i) for i in re.findall('DROPPED_TTI=\s*(\d+),',ave_cpuload)] # Add ',' to be sure to get complete value since there is a left shifting character
                # Check that no stuck -> TO FINALIZE
                if self.dl and len(dl_rate_list)>2:
                    if dl_rate_list[-1] == 0 and dl_rate_list[-2] == 0:
                        if self.find_max_dl_rate:
                            print "FIND MAX DL ACTIVATED"
                            if len(self.max_stable_dl_rb):
                                print "Still connected but no more transfer with RB", self.dl_rb, "and TBSidx", self.dl_tbsidx, "-> Reset to check other config"
                                self.dl_rb = self.max_stable_dl_rb.pop()
                                self.dl_tbsidx = self.max_stable_dl_tbsidx.pop()
                                self.restart_ftp()
                                dxp1_list, dxp0_list, dl_rate_list, ul_rate_list, bler_list, dropped_tti_list = ([], [], [], [], [], [])
                                check_rate_while_runing = False
                                count_no_display = 0
                            else:
                                self.log_msg("No other RB and TBS to test")
                                self.wait_end_ftp()
                                break
                        else:
                            print "Rate goes to zero -> Restart"
                            self.restart_ftp()
                            dxp1_list, dxp0_list, dl_rate_list, ul_rate_list, bler_list, dropped_tti_list = ([], [], [], [], [], [])
                            check_rate_while_runing = False
                            count_no_display = 0
                if self.ul and len(ul_rate_list)>3:
                    if ul_rate_list[-1] == 0 and ul_rate_list[-2] == 0 and ul_rate_list[-3] == 0:
                        if re.search("OOS_SEARCH", self.scen_name):
                            self.log_msg("Still connected but no more transfer -> Wait for issue with FTP server...")
                        else:
                            self.log_msg("Still connected but no more transfer -> Reset to check other config")
                            self.restart_ftp()
                            print "Reset cpu value"
                            dxp1_list, dxp0_list, dl_rate_list, ul_rate_list, bler_list, dropped_tti_list = ([], [], [], [], [], [])
                            count_no_display = 0
                # In case of very low rate, the transfer can run for ages -> limit that
                if self.counter_sec > 120 and not check_rate_while_runing: # Check after 2 minutes
                    print "check rate after 120 sec"
                    check_rate_while_runing = True
                    if self.dl:
                        dl_rate_theorical = int(self.get_therical_throughput("DL"))
                        ave_dl_rate = int(sum(dl_rate_list)/len(dl_rate_list))
                        print "dl_rate_theorical=", dl_rate_theorical
                        print "ave_dl_rate=", ave_dl_rate
                        if ave_dl_rate < int(dl_rate_theorical*0.4):
                            self.log_msg("the DL rate is not suffisant -> power cycle the board")
                            self.download_coredump()
                            self.power_cycle()
                    if self.ul:
                        ul_rate_theorical = int(self.get_therical_throughput("UL"))
                        ave_ul_rate = int(sum(ul_rate_list)/len(ul_rate_list))
                        print "ul_rate_theorical=", ul_rate_theorical
                        print "ave_ul_rate=", ave_ul_rate
                        if ave_ul_rate < int(ul_rate_theorical*0.4):
                            self.log_msg("the UL rate is not suffisant -> power cycle the board")
                            self.download_coredump()
                            self.power_cycle()
            except:
                print "Exception here"
                if self.check_assert_report(self.dl_rb, self.dl_tbsidx):
                    self.log_msg("ASSERT detected with RB%d and TBSidx%d" % (self.dl_rb, self.dl_tbsidx))
                    if self.find_max_dl_rate:
                        print "FIND MAX DL ACTIVATED"
                        if len(self.max_stable_dl_rb):
                            print "ASSERT with RB", self.dl_rb, "and TBSidx", self.dl_tbsidx
                            self.dl_rb = self.max_stable_dl_rb.pop()
                            self.dl_tbsidx = self.max_stable_dl_tbsidx.pop()
                            self.restart_ftp()
                            dxp1_list, dxp0_list, dl_rate_list, ul_rate_list, bler_list, dropped_tti_list = ([], [], [], [], [], [])
                            count_no_display = 0
                        else:
                            self.log_msg("No other RB and TBS to test under exception")
                            #self.wait_end_ftp()
                            break
                    else:
                        #self.wait_end_ftp()
                        break
                else:
                    self.log_msg("What is the issue??? -> Break")
                    # self.wait_end_ftp()
                    # RV - Try to restart the Callbox instead of waiting finishing the FTP transfer in case of error
                    break
        # Stop icpuload display
        try:
            self.send_cmd('at%icpuload=0')
        except:
            self.log_msg("Warning: Can not send at%icpuload=0")
            pass
        print "Start computing rate and CPU load"
        # Remove the extremities of rates and dxp loads values for more accuracy
        try:
            if self.dl:
                dl_rate_list.pop(0); dl_rate_list.pop(0); dl_rate_list.pop();
            if self.ul:
                ul_rate_list.pop(0); ul_rate_list.pop(0); ul_rate_list.pop();
            dxp1_list.pop(0); dxp1_list.pop(); dxp0_list.pop(0); dxp0_list.pop();
        except:
            self.log_msg("Can not remove extremities of rates and dxp loads values for more accuracy")
            pass
        # Get useful params
        try:
            self.cpu_dxp1 = round(float(sum(dxp1_list)/len(dxp1_list))/100,1)
        except:
            self.log_msg("Warning: Can not compute Dxp1 CPU Load")
            pass
        try:
            self.cpu_dxp0 = round(float(sum(dxp0_list)/len(dxp0_list))/100,1)
        except:
            self.log_msg("Warning: Can not compute Dxp0 CPU Load")
            pass
        if self.dl:
            try:
                self.cpu_dl_rate = [round(float(min(dl_rate_list))/1024,NB_PRECISION), round(float(sum(dl_rate_list)/len(dl_rate_list))/1024,NB_PRECISION), round(float(max(dl_rate_list))/1024,NB_PRECISION)]
            except:
                self.log_msg("Warning: Can not compute DL CPU rate")
                pass
        if self.ul:
            try:
                self.cpu_ul_rate = [round(float(min(ul_rate_list))/1024,NB_PRECISION), round(float(sum(ul_rate_list)/len(ul_rate_list))/1024,NB_PRECISION), round(float(max(ul_rate_list))/1024,NB_PRECISION)]
            except:
                self.log_msg("Warning: Can not compute UL CPU rate")
                pass
        self.log_msg("Transfer in %d second" % self.counter_sec)
        # Need to flush the AT buffer
        time.sleep(2)
        try:
            self.send_cmd('at')
        except:
            pass

    def restart_ftp():
        self.retrieve_after_assert()
        self.start_ftp(self.dl_file_size)
        self.change_throughput(self.dl_rb, self.dl_tbsidx)

    def wait_end_ftp(self):
        if threading.activeCount()>1:
            print "Warning: FTP not finished -> wait for it!!!"
            while threading.activeCount()>1:
                time.sleep(1)

    def send_at_critical(self, command, dl_rb, dl_tbsidx):
        if self.status == STATUS_ASSERT:
            return 0
        try:
            return self.send_cmd(command)
        except:
            print "Error: can't send AT command:", command
            print "Try to reopen UE Port COM to check for assert"
            # Try to open the port com again
            self.get_ue_port()
            try:
                if self.check_assert_report(dl_rb, dl_tbsidx):
                    # Check if assert happen
                    print "Assert Detected before sending AT command:", command
                else:
                    print "No Assert ???!!!"
            except:
                print "Can't check for ASSERT when sending AT command:", command
        return 0

    def finish(self):                   # RV - UNCALLLLLLLLLLLLLLLLLL
        # Best to restore the display when finishing remote control
        self.callbox.write("SYSTem:DISPlay:UPDate OFF")

    def close_connection(self):
        print "\nClosing connection..."
        print "***STOP PROTOCOL STACK***"
        try:
            self.send_cmd('at+cfun=0')
            time.sleep(8)
            self.sock.close()
        except:
            print "AT Port already closed"

    def change_clock_and_ltemeas(self):
        if self.ltemeas == 1:
            self.send_cmd('at%iltemeas=1')
        elif self.ltemeas == 0:
            self.send_cmd('at%iltemeas=0')
        time.sleep(2)
        if self.clock:
            clock_command = "5,%d" % self.clock
            self.send_cmd("at%iapm=" + clock_command) # CHECK THAT the action is OK

    ########################################################
    ##               Copy results into file
    ########################################################
    def compute_throughput(self):
        # Retrieve throughput
        if self.dl:
            try:
                self.throughput_DL = self.File_DL.get_throughput()*8
                self.size_DL = round(self.File_DL.get_dl_size()/1024)
                if re.search("MIMO",self.scen_name):
                    self.throughput_DL +=  self.File_DL2.get_throughput()*8
                    self.size_DL += round(self.File_DL2.get_dl_size()/1024)
                    #self.throughput_DL +=  self.File_DL3.get_throughput()*8
                    #self.size_DL += round(self.File_DL3.get_dl_size()/1024)
                self.throughput_DL = round(float(self.throughput_DL)/1024, NB_PRECISION)
            except:
                pass
        if self.ul:
            try:
                throughput_UL_total = self.File_UL1.get_throughput()*8
                self.size_UL_total = round(self.File_UL1.get_ul_size()/1024)
                if self.num_files_in_ul > 1:
                    throughput_UL_total += self.File_UL2.get_throughput()*8
                    self.size_UL_total += round(self.File_UL2.get_ul_size()/1024)
                if self.num_files_in_ul > 2:
                    throughput_UL_total += self.File_UL3.get_throughput()*8
                    self.size_UL_total += round(self.File_UL3.get_ul_size()/1024)
                self.throughput_UL_total = round(float(throughput_UL_total)/1024, NB_PRECISION)
            except:
                pass

    ########################################################
    ##               Start Callbox and Init Sequence
    ########################################################
    def start_callbox_and_init_sequence(self):
        print "\nStarting Callbox and initiating sequence..."
        attempt_attach = 0
        while attempt_attach < ATTEMPT_ATTACH_MAX:
            print "\nAttempt attach (%s/%s) for scenario: %s" % (attempt_attach, ATTEMPT_ATTACH_MAX, self.scen_name)
            attempt_attach += 1
            ### Start Callbox ###
            try:
                # Get the communication with the Callbox
                self.callbox_comm()
                # Reset the Callbox
                self.callbox_reset()
                # Setup the Cell
                self.cell_setup()
                # Set up the FTP server
                self.ftp_settings()
                # Switch on the cell
                self.cell_on()
                # Check cell scenario
                # self.check_cell_mimo_siso()   ### RV - NOT WORKING YET
            except:
                Tools().sendMail(r"Callbox Communication problem , Callbox Reset Required")
                sys.exit(1)
            ### Init Sequence ###
            self.get_ue_port()
            # Start up the UE
            self.ue_startup()
            # Wait for attach
            if not self.wait_attach():
                if self.check_assert_if_start_reg():
                    # Assert detected -> Start Reg now
                    return False
                self.error = ERROR_NO_ATTACH
                self.download_coredump()
                self.power_cycle()
                continue
            # Active the PDP context
            self.active_pdpcontext()
            # Retrieve UE IPv4 address
            #self.get_ue_ipv4_address()
            # Check for UE address
            return True
            if self.check_ipconfig():
                # Add route packet
                self.route()        # RV - Required only once -> move it.
                self.status = STATUS_OK
                self.error = NO_ERROR
                return True
            if self.check_assert_if_start_reg():
                # Assert detected -> Start Reg now
                return False
            print "Warning: No UE IP address and no Assert ???!!!"
            self.power_cycle()
        # Error to attach (no Assert detected) if going to this point
        self.status = STATUS_ERROR
        if force_find_reg_after_attach_fail:
            print "-> Force detection now"
            self.run_reg_now = True
        self.error = ERROR_NO_IP_ADDRESS
        return False

    def check_assert_if_start_reg(self):
        if self.check_assert_report(self.dl_rb, self.dl_tbsidx):
            # Check if assert happen
            print "Assert Detected before ATTACH"
            if force_find_reg_after_attach_fail:
                print "-> Force detection now"
                self.run_reg_now = True
                return True
        return False

    def retrieve_changelist(self):
        print "\nRetrieving changelist..."
        # self.power_cycle()   # Added when first Run after PC reboot
        # Getting the UE com port
        self.get_ue_port()
        # Get CL number
        self.get_cl()
        print "Current CL flashed on board", self.cl
        # Clean Assert report
        self.clean_assert_report()

    def init_var(self):
        # Remove potential existant global variables for good excel sheet results
        # Delete only 1st variables from each try-except block in excel function
        self.cpu_dxp1 = None
        self.size_DL = None
        self.size_UL_total = None
        del self.cpu_dxp1
        del self.size_DL
        del self.size_UL_total

    ########################################################
    ##               Start Sequence
    ########################################################
    def test_sequence(self):
        self.log_status('Testing')
        self.init_var()
        if self.status == STATUS_ERROR: # RV - make a diff between no init yet and attach
            # Start Callbox and init sequence
            self.start_callbox_and_init_sequence()
        print "STATUS =", self.status
        self.status = STATUS_OK
        if not self.status in (STATUS_ERROR, STATUS_ASSERT):
            self.ftp_sequence()
        self.terminate_sequence()
        if self.status == STATUS_ASSERT:
            print "STATUS =", self.status
            # Switch to ERROR state to init the callbox again
            self.status = STATUS_ERROR
        if self.status == STATUS_REGRESSION:
            self.status = STATUS_OK


    def ftp_sequence(self):
        print "\nStarting FTP sequence..."
        # Change Clock and LTE measurement if needed
        self.change_clock_and_ltemeas()
        ########### HANDLE FIND MAX THROUGHPUT
        if self.find_max_dl_rate:
            self.find_max_dl_throughput()
            if self.status != STATUS_OK:
                return
        # Set the throughput corresponding to the test performed
        self.set_throughput()
        # Start FTP transfer
        self.start_ftp(self.dl_file_size)
        # Get Cpuload
        if self.test_cpuload:
            self.get_cpuload(NB_CPULOAD_LINES_DISP)
            # RV - Restart transfer if no CPULOAD info save -> this is an unknown issue for now
            if not self.cpu_dxp1 or not self.cpu_dxp0 and self.status != STATUS_ASSERT:
                self.log_msg("Warning: Restart transfer to get new cpuload info")
                self.get_cpuload(NB_CPULOAD_LINES_DISP)
        else:
            # Wait that all thread finished
            while threading.activeCount()>1:
                time.sleep(1)

    def terminate_sequence(self):
        print "\nTerminating sequence..."
        # Checking for assert/Afault
        self.check_assert_report(self.dl_rb, self.dl_tbsidx)
        if not self.status == STATUS_ERROR:
            # Compute throughputs and size
            self.compute_throughput()
        # Update excel file
        self.excel()
        os.system("copy "+ EXCEL_FILE + " \\\\serv2.icerasemi.com\\eng\\nsait\\") # get test results after each scenario

    def config_allowed_for_cat2(self, rb, tbsidx):
        if tbsidx > 25 or rb > 50:
            # Limitation for our software
            return False
        if self.tm > 1:
            if tbsidx == 22 and rb > 48:
                return False
            elif tbsidx == 23 and rb > 45:
                return False
            elif tbsidx == 24 and rb > 42:
                return False
            elif tbsidx == 25 and rb > 39:
                return False
        return True

    def find_max_dl_throughput(self):
        self.assert_when_finding_max = 0
        # Start FTP transfer
        (dl_rb, dl_tbsidx) = (RB_START, TBSIDX_START)
        # Store Max Stable Rate
        self.max_stable_dl_rb, self.max_stable_dl_tbsidx = ([dl_rb], [dl_tbsidx])
        last_stable_dxp0, last_stable_dl_rate, last_stable_bler = (0, 0, 0)

        print "NEW setting RB", dl_rb, "and TBSidx", dl_tbsidx
        while self.config_allowed_for_cat2(dl_rb, dl_tbsidx) and not (self.status in (STATUS_ASSERT, STATUS_ERROR)):
            self.start_ftp(300)
            while (threading.activeCount()>1) and not (self.status in (STATUS_ASSERT, STATUS_ERROR)):
                if self.config_allowed_for_cat2(dl_rb, dl_tbsidx):
                    self.change_throughput(dl_rb, dl_tbsidx)
                    skip_next_tbsidx_for_optim = False
                    # CPULOAD
                    dl_rate_theorical = self.get_therical_throughput("DL")
                    time.sleep(3)
                    self.send_at_critical('at%icpuload=1,'+str(TIME_CPULOAD_FIND)+',0', dl_rb, dl_tbsidx)
                    time.sleep(TIME_CPULOAD_FIND+2)
                    ave_cpuload = self.send_at_critical('at', dl_rb, dl_tbsidx)
                    if not self.status in (STATUS_ASSERT, STATUS_ERROR):
                        if not threading.activeCount()>1:
                            print "CPUload value not taken due to end of transfer -> restart transfer then redo"
                            # Be sure that the cpuload is not taken when ftp end
                            break
                        match=re.search('LOAD: DXP1=\s*(\d+) DXP0=\s*(\d+).+DL_RATE=\s*(\d+).+UL_RATE=\s*(\d+).+BLER=(\d+\.\d+)\%.+DROPPED_TTI=\s*(\d+)',ave_cpuload)
                        if match:
                            dxp0, dl_rate, bler, dropped_tti = (int(match.group(2)), int(match.group(3)), float(match.group(5)), int(match.group(6)))
                            print " -> CPUload: dxp0=", dxp0, "dl_rate=", dl_rate, "bler=", bler, "dropped_tti=", dropped_tti
                            # Check if DL rate is better
                            print " dl_rate=%d > dl_rate_theorical=%d (%d)" % (dl_rate, int(dl_rate_theorical), int(dl_rate_theorical*0.7))
                            # if (dl_rate > last_stable_dl_rate) and (dl_rate > int(dl_rate_theorical*0.7)) and (bler < 0.5) and (dropped_tti < 2):
                            # if (dl_rate > last_stable_dl_rate) and (dl_rate > int(dl_rate_theorical*0.7)) and (bler < 4) and (dropped_tti < 20):
                            if (dl_rate > last_stable_dl_rate) and (dl_rate > int(dl_rate_theorical*0.7)) and (bler < 3) and (dropped_tti < 15):
                                print " -> NEW MAX STABLE DL Rate=", dl_rate, "for RB", dl_rb, "for TBSidx", dl_tbsidx, " OLD stable DL Rate=", last_stable_dl_rate
                                last_stable_dl_rate, last_stable_bler, last_stable_dxp0 = (dl_rate, bler, dxp0)
                                self.max_stable_dl_rb.append(dl_rb)
                                self.max_stable_dl_tbsidx.append(dl_tbsidx)
                            # Special case when loss transmission
                            if dl_rate == 0:
                                print "Still connected but no more transfer -> Reset to check other config"
                                self.retrieve_after_assert()
                            # Optimize search by skipping next TBSIDX if no good results with this RB
                            if dl_rate < 9000:
                                skip_next_tbsidx_for_optim = True
                        else:
                            print "Error: No CPUload match"
                            self.check_assert_report(dl_rb, dl_tbsidx)
                            self.retrieve_after_assert()
                    else:
                        print "ASSERT with RB", dl_rb, "and TBSidx", dl_tbsidx
                        self.retrieve_after_assert()
                    # Get next config in order to parse all DL parameters.
                    dl_rb, dl_tbsidx = self.set_next_config(dl_rb, dl_tbsidx, skip_next_tbsidx_for_optim)
                    ###  OPTIMIZATION : avoid unecessary config giving less DL rate
                    while (dl_rb != RB_END):
                        self.change_throughput(dl_rb, dl_tbsidx)
                        dl_rate_theorical = self.get_therical_throughput("DL")
                        if int(dl_rate_theorical) < last_stable_dl_rate:
                            # No need to try this config since it will gives less throughput
                            print "NO TEST WITH setting RB %d and TBSidx %d -> would give less DL rate" % (dl_rb, dl_tbsidx)
                            # dl_rb, dl_tbsidx = self.set_next_config(dl_rb, dl_tbsidx, skip_next_tbsidx_for_optim)
                            dl_rb, dl_tbsidx = self.set_next_config(dl_rb, dl_tbsidx)
                        else:
                            break
                    ##########################################
                    print "NEW setting RB", dl_rb, "and TBSidx", dl_tbsidx
                else:
                    print "Finish Test -> Setting %dRB and %dTBSidx to max" % (self.max_stable_dl_rb[-1], self.max_stable_dl_tbsidx[-1])
                    self.change_throughput(self.max_stable_dl_rb[-1], self.max_stable_dl_tbsidx[-1])
                    print "Finish Test -> Waiting for end of transfer"
                    # Wait to finish transfert
                    while threading.activeCount()>1:
                        time.sleep(2)
        # Check that no assert append with assert
        print "max_stable_dl_rb=", self.max_stable_dl_rb
        print "max_stable_dl_tbsidx=", self.max_stable_dl_tbsidx
        last_dl_rb = self.max_stable_dl_rb.pop()
        last_dl_tbsidx = self.max_stable_dl_tbsidx.pop()
        while self.check_assert_report(last_dl_rb, last_dl_tbsidx) and len(self.max_stable_dl_rb):
            print "ASSERT detected with RB", last_dl_rb, "and TBSidx", last_dl_tbsidx
            last_dl_rb = self.max_stable_dl_rb.pop()
            last_dl_tbsidx = self.max_stable_dl_tbsidx.pop()
            self.retrieve_after_assert()
            self.start_ftp(200)
            self.change_throughput(last_dl_rb, last_dl_tbsidx)
            while threading.activeCount()>1:
                time.sleep(2)
        print "STATUS=", self.status
        # Restart callbox after assert to continue ftp transfer
        if self.status == STATUS_ASSERT:
            self.assert_when_finding_max = 1
            self.assert_dl_rb, self.assert_dl_tbsidx = (last_dl_rb, last_dl_tbsidx)
            self.retrieve_after_assert()
        # RV - Continue HERE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        print "STATUS=", self.status
        # Store Max Stable Rate
        print "max_stable_dl_rb=", last_dl_rb
        print "max_stable_dl_tbsidx=", last_dl_tbsidx
        print "last_stable_dxp0=%d,  last_stable_dl_rate=%d,  last_stable_bler=%d" % (last_stable_dxp0, last_stable_dl_rate, last_stable_bler)
        # New setting for DL param
        self.dl_rb, self.dl_tbsidx = (last_dl_rb, last_dl_tbsidx)
        # Adding the parameters used to the test name
        # self.scen_name += "_RB_%d_TBSIDX_%d" % (self.dl_rb, self.dl_tbsidx)       # To write on same column

    def set_next_config(self, dl_rb, dl_tbsidx, skip_next_tbsidx=False):
        if (dl_rb < RB_END) and (dl_tbsidx == TBSIDX_END or skip_next_tbsidx): # or (bler > 0.7 or dropped_tti > 15): # RV - increase speed to remove none interresting case
            # Increase RB and reset TBSIDX
            if self.tm > 1:
                dl_rb += 3
            else:
                dl_rb += 1
            if dl_rb > RB_END:
                dl_rb = RB_END
            dl_tbsidx = TBSIDX_START
        else:
            # Increase TBSIDX
            dl_tbsidx += 1
        # Check that the config is allowed for cat 2
        if (dl_rb < RB_END) and not self.config_allowed_for_cat2(dl_rb, dl_tbsidx):
            # Working for MIMO only
            dl_rb += 3
            if dl_rb > RB_END:
                dl_rb = RB_END
            dl_tbsidx = TBSIDX_START
        return (dl_rb, dl_tbsidx)

    def retrieve_after_assert(self):
        self.download_coredump()
        print "Retrieve after ASSERT -> Restart callbox after assert to continue ftp transfer"
        # Power cycle to reset board
        self.power_cycle()
        # Start Callbox and init sequence
        self.start_callbox_and_init_sequence()
        # Change Clock and LTE measurement if needed
        self.change_clock_and_ltemeas()

    ########################################################
    ##               Excel Part
    ########################################################
    def get_CL_idx2(self, nrows):
        # Read each CL starting from the last one. Should all be order in increasing value -> MANDATORY -> RV - Need to check that
        for line in range (nrows-1, LIN_INFO, -1):    # RV - Verify that LIN_INFO
            last_read_cl = int(self.read_sheet.cell(line,COL_CL).value)
            if last_read_cl == self.cl:
                print "CL%d found with line %d" % (self.cl, line)
                return True, line
            if last_read_cl < self.cl:
                print "Last CL%d is older than the CL%d -> return new line", line, "found for", int(self.read_sheet.cell(line,COL_CL).value)
                return False, line+1
        # Weird case: a very old CL is tested
        print "Warning: Weird case, a very old CL is tested"
        return False, nrows

    def get_CL_idx(self, nrows):
        # Read each CL starting from the last one. Should all be order in increasing value -> MANDATORY -> RV - Need to check that
        for line in range (nrows-1, LIN_INFO, -1):    # RV - Verify that LIN_INFO
            if self.read_sheet.cell(line,COL_CL).value != "" :
                last_read_cl = int(self.read_sheet.cell(line,COL_CL).value)
                if last_read_cl == self.cl:
                    print "CL%d found with line %d" % (self.cl, line)
                    return True, line
                if last_read_cl < self.cl:
                    print "Last CL%d is older than the CL%d -> return new line", line, "found for", int(self.read_sheet.cell(line,COL_CL).value)
                    return False, line+1
        # Weird case: a very old CL is tested
        print "Warning: Weird case, a very old CL is tested"
        return False, nrows

    def excel_head(self):
        print "\nWriting results in Excel sheet..."

        read_book = open_workbook(EXCEL_FILE, formatting_info=True)
        write_book = Workbook();
        write_book = copy(read_book);
        for self.band in BAND_TANGO_ALLOWED :
            self.read_sheet = read_book.sheet_by_name("Band%d" % int(self.band))
            if self.band == 1:
                write_sheet = write_book.get_sheet(0)
            elif self.band == 4:
                write_sheet = write_book.get_sheet(1)
            else:
                write_sheet = write_book.get_sheet(2)

            nrows = self.read_sheet.nrows
            CL_found, current_row = self.get_CL_idx(nrows)
            self.insert_new_CL(CL_found, current_row, nrows, write_sheet)
            write_row = write_sheet.row(current_row)
            write_row.write(COL_CL,self.cl, changelist_style)
            write_row.write(COL_TIME, time.strftime("%d %b %Y %H:%M:%S", time.gmtime()), time_style)
            write_row.write(COL_CL+2,branch,changelist_style)

            for self.scen_name in scenario_implemented :
                current_col, status_col = self.get_column_for_test(self.read_sheet)
                write_row.write(status_col,STATUS_ASSERT,status_ASSERT_style)

        write_book.save(EXCEL_FILE)


    def excel(self):
        print "\nWriting results in Excel sheet..."
        ###################################################
        # 1) - Open Excel file Read/Write permissions.
        read_book = open_workbook(EXCEL_FILE, formatting_info=True)
        write_book = Workbook();
        write_book = copy(read_book);
        self.read_sheet = read_book.sheet_by_name("Band%d" % int(self.band))
        if self.band == 1:
            write_sheet = write_book.get_sheet(0)
        elif self.band == 4:
            write_sheet = write_book.get_sheet(1)
        else:
            write_sheet = write_book.get_sheet(2)
        nrows = self.read_sheet.nrows
        ###################################################
        # 2) - Get line index with same CL or create it
        # print "Last revision line in excel sheet is: ", int(self.read_sheet.cell(nrows-1,COL_CL).value)
        CL_found, current_row = self.get_CL_idx(nrows)
        overall_status = self.get_overall_status(CL_found, self.read_sheet, current_row)
        self.insert_new_CL(CL_found, current_row, nrows, write_sheet)
        write_row = write_sheet.row(current_row)
        # Get first column corresponding to the test
        self.current_col, self.status_col = self.get_column_for_test(self.read_sheet)
        if self.current_col == 0:
            # If nothing is found -> First time this test is performed -> Create new Column in excel sheet
            print "Check Disabled since first time run for this test"
            self.ref_line = 0
            self.current_col, self.status_col = self.create_columns_for_new_test(write_sheet)
        else:
            # Get reference CL for this test (check only the status value)
            self.ref_line = self.get_reference_CL(current_row)
        ###################################################
        # 3) - Write Callbox config
        if self.find_max_dl_rate:
            current = self.current_col
            try:
                self.write_value_in_row_and_check(write_row, self.dl_rb, cell_style, NO_CHECK) # For full check use: CHECK_HIGH)
                self.write_value_in_row_and_check(write_row, self.dl_tbsidx, cell_style, NO_CHECK) # For full check use: CHECK_HIGH)
            except:
                self.current_col = current + 2
                pass
        ###################################################
        # 3) - Write CPU load and Rate results
        if self.test_cpuload:
            current = self.current_col
            try:
                # Write all result values
                self.write_value_in_row_and_check(write_row, self.cpu_dxp1, cell_style, CHECK_HIGH) # For full check use: CHECK_HIGH)
                self.write_value_in_row_and_check(write_row, self.cpu_dxp0, cell_style, CHECK_HIGH) # For full check use: CHECK_HIGH)
                if self.dl:
                    print "throughput_DL=", self.throughput_DL, " cpu_dl_rate_ave=", self.cpu_dl_rate[1]
                    self.write_value_in_row_and_check(write_row, self.cpu_dl_rate[0], cell_style, NO_CHECK) # For full check use: CHECK_LOW)
                    self.write_value_in_row_and_check(write_row, self.cpu_dl_rate[1], cell_style, CHECK_LOW) # For full check use: CHECK_LOW)
                    self.write_value_in_row_and_check(write_row, self.cpu_dl_rate[2], cell_style, NO_CHECK) # For full check use: CHECK_LOW)
                if self.ul:
                    print "throughput_UL=", self.throughput_UL_total, " cpu_ul_rate_ave=", self.cpu_ul_rate[1]
                    self.write_value_in_row_and_check(write_row, self.cpu_ul_rate[0], cell_style, NO_CHECK) # For full check use: CHECK_LOW)
                    self.write_value_in_row_and_check(write_row, self.cpu_ul_rate[1], cell_style, CHECK_LOW) # For full check use: CHECK_LOW)
                    self.write_value_in_row_and_check(write_row, self.cpu_ul_rate[2], cell_style, NO_CHECK) # For full check use: CHECK_LOW)
            except:
                self.current_col = current + 2 + 3 * self.dl + 3 * self.ul
                pass
        # 4) - Write total rate and size transfered
        if self.dl:
            current = self.current_col
            try:
                self.write_value_in_row_and_check(write_row, self.size_DL, cell_style, NO_CHECK) #CHECK_SAME
                self.write_value_in_row_and_check(write_row, self.throughput_DL, cell_style, CHECK_LOW)
            except:
                self.current_col = current + 2
        if self.ul:
            current = self.current_col
            try:
                if self.size_UL_total == 0:
                    self.write_value_in_row_and_check(write_row, self.counter_sec, cell_style, CHECK_LOW) # For full check use: CHECK_LOW)
                else:
                    self.write_value_in_row_and_check(write_row, self.size_UL_total, cell_style, NO_CHECK)#CHECK_SAME
                self.write_value_in_row_and_check(write_row, self.throughput_UL_total, cell_style, CHECK_LOW) #CHECK_LOW
            except:
                self.current_col = current + 2
        #########################################################
        # 5) - Add CL and update general status...
        write_row.write(COL_CL, self.cl, changelist_style)
        write_row.write(COL_CL+2,branch,changelist_style)
        #write_row.wrtie(COL_CL+3,self.remark,changelist_style) #NSAIT DEBUG
        if self.status == STATUS_ASSERT:
            write_row.write(self.status_col-1, self.status, status_ASSERT_style)
            write_row.write(COL_OVERALL_STATUS, self.status, status_ASSERT_style)
        elif self.status == STATUS_REGRESSION:
            write_row.write(self.status_col-1, self.status, status_REG_style)
            if overall_status != STATUS_ASSERT:
                write_row.write(COL_OVERALL_STATUS, self.status, status_REG_style)
        elif self.status == STATUS_ERROR:
            write_row.write(self.status_col-1, self.status, status_ERROR_style)
            if not overall_status in (STATUS_ASSERT, STATUS_REGRESSION):
                write_row.write(COL_OVERALL_STATUS, self.status, status_ERROR_style)
        else:
            write_row.write(self.status_col-1, self.status, status_OK_style)
            if not overall_status in (STATUS_ASSERT, STATUS_REGRESSION, STATUS_ERROR):
                write_row.write(COL_OVERALL_STATUS, self.status, status_OK_style)
        write_row.write(COL_TIME, time.strftime("%d %b %Y %H:%M:%S", time.gmtime()), time_style)
        write_row.write(COL_CL+3,self.remark)

        #########################################################
        # 6) - Once everything is done ->Save excel file...
        write_book.save(EXCEL_FILE);
        #Generating Charts After Each Scenario
        if self.scen_name != "" :
            Chart().chart_scenario(self.band,self.cl,5,self.scen_name,branch)

        self.log_status(self.status)

    def insert_new_CL(self, CL_found, current_row, nrows, write_sheet):
        if (not CL_found) and (current_row < nrows):
            # Empty line inserted
            for i,cell in enumerate(self.read_sheet.row(current_row)):
                write_sheet.write(current_row,i,"")
            # Shift down all rows from current_row to nrows-1 (all included)
            for rowx in range(current_row, nrows, 1):
                # write_row = write_sheet.row(current_row)
                for i,cell in enumerate(self.read_sheet.row(rowx)):
                    if i == COL_TIME:
                        write_sheet.write(rowx+1,i,cell.value, time_style)
                    elif i == COL_CL:
                        write_sheet.write(rowx+1,i,cell.value, changelist_style)
                    elif i == COL_BRANCH:
                        write_sheet.write(rowx+1,i,cell.value, branch_style)
                    elif cell.value == STATUS_ASSERT:
                        write_sheet.write(rowx+1,i,cell.value, status_ASSERT_style)
                    elif cell.value == STATUS_REGRESSION:
                        write_sheet.write(rowx+1,i,cell.value, status_REG_style)
                    elif cell.value == STATUS_ERROR:
                        write_sheet.write(rowx+1,i,cell.value, status_ERROR_style)
                    elif cell.value == STATUS_OK:
                        write_sheet.write(rowx+1,i,cell.value, status_OK_style)
                    else:
                        write_sheet.write(rowx+1,i,cell.value)

    def get_overall_status(self, CL_found, read_sheet, line):
        if not CL_found:
            return STATUS_OK
        overall_status = read_sheet.cell(line,COL_OVERALL_STATUS).value
        #assert(overall_status in (STATUS_REGRESSION, STATUS_ASSERT, STATUS_OK, STATUS_ERROR)) #NSAIT
        print "overall status is", overall_status
        return overall_status

    def write_value_in_row_and_check(self, write_row, value, style, comparator=NO_CHECK):
        if self.ref_line and comparator != NO_CHECK and self.status != STATUS_ASSERT:
            self.check_regression_value(value, comparator)
        write_row.write(self.current_col, value, style)
        self.current_col += 1

    def check_regression_value(self, val, comparator):
        # print "Start Reg for", val, comparator, self.read_sheet.cell(self.ref_line,self.current_col).value
        assert(comparator in (CHECK_LOW, CHECK_HIGH, CHECK_SAME))
        modif = 0
        if comparator in (CHECK_LOW, CHECK_SAME):
            if float(val) < float(self.read_sheet.cell(self.ref_line,self.current_col).value)*(1-self.regression_delta):
                self.status = STATUS_REGRESSION
                modif = 1
        if comparator in (CHECK_HIGH, CHECK_SAME): # Only for Dxp load
            if float(val) > float(self.read_sheet.cell(self.ref_line,self.current_col).value)*(1+REGRESSION_DELTA_DXP):
            #if float(val) > float(self.read_sheet.cell(self.ref_line,self.current_col).value)*(1+self.regression_delta):
                self.status = STATUS_REGRESSION
                modif = 1
        if modif:
            print "Regression detected for", val, comparator, self.read_sheet.cell(self.ref_line,self.current_col).value

    def get_reference_CL(self, current_row):
        for line in range (current_row-1, LIN_INFO, -1):
            # print "Check", self.read_sheet.cell(line,self.status_col-1).value
            if self.read_sheet.cell(line,self.status_col-1).value == STATUS_OK:
                print "line", line, "found for", int(self.read_sheet.cell(line,COL_CL).value)
                return line
        # Disable the regression if no reference CL is found
        return 0

    def get_line_with_CL2(self, read_sheet, current_cl):
        print "Founding line for CL%d in excel sheet..." % current_cl
        nrows = read_sheet.nrows-1
        for line in range (nrows, LIN_INFO, -1):
            print "Check CL%d" % int(read_sheet.cell(line,COL_CL).value)
            if int(read_sheet.cell(line,COL_CL).value) == current_cl:
                print "CL%s found at line %d" % (int(read_sheet.cell(line,COL_CL).value), line)
                return line
            elif int(read_sheet.cell(line,COL_CL).value) < current_cl:
                print "CL%d not found since line %d (CL%d) is smaller" % (current_cl, line, int(read_sheet.cell(line,COL_CL).value))
                return 0
        # Disable the regression if no reference CL is found
        return 0

    def get_line_with_CL(self, read_sheet, current_cl):
        print "Founding line for CL%d in excel sheet..." % current_cl
        nrows = read_sheet.nrows-1

        for line in range (nrows, LIN_INFO, -1):
            if read_sheet.cell(line,COL_CL).value != "" :
                print "Check CL%d" % int(read_sheet.cell(line,COL_CL).value)
                if int(read_sheet.cell(line,COL_CL).value) == current_cl:
                    print "CL%s found at line %d" % (int(read_sheet.cell(line,COL_CL).value), line)
                    return line
                elif int(read_sheet.cell(line,COL_CL).value) < current_cl:
                    print "CL%d not found since line %d (CL%d) is smaller" % (current_cl, line, int(read_sheet.cell(line,COL_CL).value))
                    return 0
        # Disable the regression if no reference CL is found
        return 0

    def get_column_for_test(self, read_sheet):
        for crange in read_sheet.merged_cells:
            rlo, rhi, clo, chi = crange
            # Get only Cell starting to the first line
            if rlo == LIN_NAME:
                if read_sheet.cell(rlo,clo).value == self.scen_name:
                    print "Cell found for %s (clo=%d chi=%d)" % (read_sheet.cell(rlo,clo).value, clo, chi)
                    return (clo, chi)
        # If nothing is found -> First time this test is performed -> Create new Column in excel sheet
        return (0, 0)

    def create_columns_for_new_test(self, write_sheet):
        merge_style = easyxf('alignment: horizontal center;'
                             'border: left thin, right thin;')
        style = easyxf('alignment: horizontal center;'
                       'border: top thin, bottom thin;')
        ncols = self.read_sheet.ncols
        write_ncol = ncols
        if self.find_max_dl_rate:
            write_sheet.write(LIN_INFO, write_ncol, "RB", style)
            write_sheet.write(LIN_INFO, write_ncol+1, "TBS", style)
            write_ncol += 2
        if self.test_cpuload:
            write_sheet.write(LIN_INFO, write_ncol, "DXP1(%)", style)
            write_sheet.write(LIN_INFO, write_ncol+1, "DXP0(%)", style)
            write_ncol += 2
            if self.dl:
                write_sheet.write(LIN_INFO, write_ncol, "Min", style)
                write_sheet.write(LIN_INFO, write_ncol+1, "Ave", style)
                write_sheet.write(LIN_INFO, write_ncol+2, "Max", style)
                write_ncol += 3
            if self.ul:
                write_sheet.write(LIN_INFO, write_ncol, "Min", style)
                write_sheet.write(LIN_INFO, write_ncol+1, "Ave", style)
                write_sheet.write(LIN_INFO, write_ncol+2, "Max", style)
                write_ncol += 3
        if self.dl:
            write_sheet.write(LIN_INFO, write_ncol, "File", style)
            write_sheet.write(LIN_INFO, write_ncol+1, "Ave", style)
            write_ncol += 2
        if self.ul:
            write_sheet.write(LIN_INFO, write_ncol, "File", style)
            write_sheet.write(LIN_INFO, write_ncol+1, "Ave", style)
            write_ncol += 2
        write_sheet.write(LIN_INFO, write_ncol, "Status", style)
        write_sheet.write_merge(LIN_NAME, LIN_NAME, ncols, write_ncol, merge_style)
        return (ncols, write_ncol+1)

    ########################################################
    ##               Build Part
    ########################################################
    def build_with_autoIT(self):
        # Notify AutoIt for starting build
        self.notify_autoit(file_build_command)

    def Run_Branch_Test(self,flash=False,Reg=False,Forced=False,CL=0):
        global branch , EXCEL_FILE
        #i = 0
        for branch in self.branch_4test :
            #if branch in BRANCH_4TEST :
            i = Tools().find_index(BRANCH_ALLOWED,branch)
            self.config_init()
            EXCEL_FILE = EXCEL_FLIST[i]
            if not self.cardhu_alive():
                print "Cardhu is not alive"
                sys.exit(1)
            self.retrieve_changelist()
            if flash == True :
                if int(self.cl) != int(CL) :
                    Flash().flash_modem(CL,branch)
                    self.retrieve_changelist()

            self.set_lte_only()
            for self.band in BAND_TANGO_ALLOWED :
                for scen in scenario_implemented:
                    self.run_scenario(scen,Forced)

            self.ReTest_Regression() #only Reg Cases
            if Reg == True :
                Regression()._run(branch,BAND_TANGO_ALLOWED,scenario_implemented,self.cl)

    def Init_Auto(self,branch4test,band4test,scenario4test):
        global  BAND_TANGO_ALLOWED , scenario_implemented
        self.branch_4test = Tools().string_array(branch4test)
        #BRANCH_ALLOWED = branch4test
        scenario_implemented = Tools().string_array(scenario4test)
        BAND_TANGO_ALLOWED = Tools().string_array(band4test)
        self.band_allowed = BAND_TANGO_ALLOWED
        self.comport = common.PORT_COM_TANGO
        self.config_init()

    def start(self):
        global branch , EXCEL_FILE , callbox_path , callbox_ssh
        timer = time.time()
        SCHEDULED_BUILD_TIME = 3600*4
        timer = 0
        self.remark = " "
        while True:
            duration = time.time() - timer
            if duration > SCHEDULED_BUILD_TIME:
                timer = time.time()
                #i = 0
                for branch in self.branch_4test :
                    i = Tools().find_index(BRANCH_ALLOWED,branch)
                    EXCEL_FILE = EXCEL_FLIST[i]
                    self.config_init()
                    self.test_branch2(branch)

                time_left = SCHEDULED_BUILD_TIME - ( time.time() - timer )
                self.print_with_time("Next build in %s sec..." % time_left )
                print " TIME LEFT : "

            time.sleep(10)

    def test_branch2(self,branch):
        if not os.path.exists(branch):
            (status,self.build_cl) = Tools()._build(branch)
            if status == BUILD_FAILED :
                return
            Tools().generateBuildReady(branch,self.build_cl)
            print "BUILD_OK , CL:",self.build_cl
        else:
            self.get_param_from_buildx(branch)


        if device_management().sys_status() == "OK" :
            self.retrieve_changelist()
            if self.cl != self.build_cl :
                Flash().flash_modem(self.build_cl,branch)
            #self.flash_board()
        elif device_management().sys_status() == "DOWNLOAD_ONLY" :
            Flash().flash_modem(self.build_cl,branch)
        elif device_management().sys_status() == "ERROR" :
            print "Not Recoverable Error Detected"
            self.log_msg("Not Recoverable Error Detected")
            Tools().sendMail("No AT / Modem Port Available")
            sys.exit(-1)

        #SYS STATUS AFTER FLASH

        if device_management().sys_status() == "ERROR" :
            print "Not Recoverable Error Detected"
            self.log_msg("Not Recoverable Error Detected")
            Tools().sendMail(r"No AT / Modem Port Available")
            sys.exit(-1)

        elif device_management().sys_status() == "DOWNLOAD_ONLY" :
            self.log_msg("Modem Crashed after flashing / AT PORT CLOSED ")
            self.band = 4
            self.scen_name = scenario_implemented[0]
            self.excel_head() # FORCING BAND 4 #Write Assert in Excel Sheet

        elif device_management().sys_status() == "OK" :
            self.retrieve_changelist()
            if self.cl != self.build_cl :
                Tools().sendMail(r"Modem Binary is not updated after Flashing BUILD CL %s, FLASHED CL %s"%(str(self.build_cl),str(self.cl)))
                sys.exit(1)

            self.set_lte_only()
            for self.band in BAND_TANGO_ALLOWED :
                for scen in scenario_implemented:
                    self.run_scenario(scen)

            #self.get_scenario_and_campaign_from_build()
            # ReTest Regression Cases
            self.ReTest_Regression()
            Regression()._run(branch,BAND_TANGO_ALLOWED,scenario_implemented,self.cl)

        os.system("copy "+ EXCEL_FILE + "\\\\" +RESULT_LOC)
        if os.path.exists(branch):
            os.remove(branch)
        #os.system("copy "+ EXCEL_FILE + " \\\\"+ callbox_path + "\\")
        #os.system("copy "+ EXCEL_FILE + " \\\\serv2.icerasemi.com\\home\\renaud\\Callbox_LTE_Test_main.br\\")

        return

    def ReTest_Regression(self):
        print "ReTesting Regression / Assert cases up to %d times " % MAX_REG_RETEST
        self.nb_run = 1
        for r in range(0,MAX_REG_RETEST) :
            self.nb_run += 1
            reg_cases_4 = []
            reg_cases_17 = []

            if not os.path.isfile(EXCEL_FILE):
                print "Test to run -> excel file does not exist"
                return (reg_cases_4,reg_cases_17)

            for self.band in BAND_TANGO_ALLOWED :
                #print "BAND %d"% self.band
                for self.scen_name in scenario_implemented :
                    #print "SCENARIO %s" % self.scen_name
                    read_book = open_workbook(EXCEL_FILE, formatting_info=True)
                    read_sheet = read_book.sheet_by_name("Band%d" % int(self.band))
                    line = self.get_line_with_CL(read_sheet, self.cl)

                    if not line:
                        print "Test to run -> the CL%d was never performerd" % self.cl
                        return

                    current_col, status_col = self.get_column_for_test(read_sheet)

                    if current_col == 0 or status_col == 0:
                        print "Test to run -> the test was never performed"
                        return

                    status = read_sheet.cell(line,status_col-1).value

                    if status in (STATUS_REGRESSION):#, STATUS_ASSERT):
                        if self.band == 4 :
                            reg_cases_4.append(self.scen_name)
                        else :
                            reg_cases_17.append(self.scen_name)
                    #k+=1
                # END OF BAND LOOP

            if reg_cases_4 == [] :
                print "No Regression / Assert for Band 4 "
            else :
                for scen in reg_cases_4 :
                    print "REGRESSION RE-TEST CASE [ Band 4 ] : %s" % scen
                    self.band = 4
                    #msg =  scen+" , NB_OF_RUN: "+str(self.nb_run)
                    #self.log_msg(msg)
                    self.run_scenario(scen,True)
            if reg_cases_17 == [] :
                print "No Regression / Assert for Band 17 "
            else :
                for scen in reg_cases_17 :
                    self.band = 17
                    print "REGRESSION RE-TEST CASE [ Band 17 ] : %s" % scen
                    #msg = scen+" BAND 17 , NB_OF_RUN: "+str(self.nb_run)
                    #self.log_msg(msg)
                    self.run_scenario(scen,True)

    def print_with_time(self, string):
        print "%s: SCHEDULER - %s" % (time.strftime("%d %b %Y %H:%M:%S", time.gmtime()), string)

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

    def power_cycle(self):
        #restart Cardhu
        #wait for response
        return True

    def get_param_from_buildx(self,branch):
        file_build = branch
        if os.path.exists(file_build):
            build_file = open(file_build, 'r')
            build_file_r = build_file.read()
            for line in build_file_r:
                if(re.search('(CL(\d+))',build_file_r)) != None:
                    self.build_cl = int(re.search('CL(\d+)',build_file_r).group(1)) #NSAIT
                    break

            build_file.close()


    def get_therical_throughput(self, param):
        if param == "DL":
            thoughput = self.callbox.ask("CONFigure:LTE:SIGN:CONNection:ETHRoughput:DL:ALL?")
        elif param == "UL":
            thoughput = self.callbox.ask("CONFigure:LTE:SIGN:CONNection:ETHRoughput:UL?")
        else:
            assert(0)
        match=re.search('(\d+.\d+)E([+-])(\d+)',thoughput)
        print "Thoughput %s from Callbox %s" % (param, thoughput)
        if match:
            if match.group(2) == "+":
                theorical_throughput = float(match.group(1))*(pow(10,int(match.group(3))))
            else:
                theorical_throughput = float(match.group(1))*(pow(10,-int(match.group(3))))
        theorical_throughput *= 1024
        print " Thoughput %s is %s (kbit)" % (param, theorical_throughput)
        return theorical_throughput


    def debug(self):
        return

    def get_sheet_by_band(self, book):      # RV - REMOVE IT -> NOT USED
        print book.sheet_names()
        for sheet_name in book.sheet_names():
            if sheet_name == "Band"+self.band:
                print book.sheet_by_name(sheet_name)

    ########################################################
    ##               Main
    ########################################################
    def main(self,argv=sys.argv[1:]):
        # Set by default the serial Port
        self.comport = common.PORT_COM_TANGO
        # Remove
        if os.path.exists(file_temp):
            os.remove(file_temp)
        # Parse the arguments
        self.config_init() #NSAIT
        self.parseArgs(argv)


def main():
    pass

if __name__ == '__main__':
    main()
