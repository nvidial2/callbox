import os
from xlwt import Workbook, easyxf

BAND_TANGO_ALLOWED = [4,17]
BRANCH_ALLOWED = ['main','cr3','ST']
#wlinux = "/home/gcflab/workspace/callbox-test/"
wlinux = "/eng/nsait/workspace/nsait-main/"
#wwin = os.path.join("serv2", "home", "gcflab","workspace","callbox-test")
wwin = os.path.join("serv2", "eng", "nsait","workspace","nsait-main")
variant ="tango-internal"
build_dir = []
p4path = []
MODEM_BINARY_LOC = []
EXCEL_FLIST = []

for branch in BRANCH_ALLOWED:
    build_dir.append(wlinux+"software/%s.br/product/datacard/modem/build/"%branch)
    MODEM_BINARY_LOC.append(r"\\%s\software\%s.br\product\datacard\modem\build\dxp-%s-obj\EV4\\"%(wwin,branch,variant))
    EXCEL_FLIST.append('Results_%s.xls'%branch)
    #EXCEL_FLIST.append(r'\\serv2\eng\nsait\workspace\Results_%s.xls'%branch)


P4BRANCH = []
P4BRANCH.append("//software/main.br/")
P4BRANCH.append("//software/releases/core/cr3.br/")

COREDUMP_LOC = os.path.join("serv2", "eng", "nsait","workspace","nsait-main","software","main.br","tools","coredump")
#CHART_LOC = os.path.join("serv2.icerasemi.com", "home", "gcflab","workspace","callbox-test","chart")
#CHART_LOC ='\\\\serv2.icerasemi.com\home\gcflab\workspace\callbox-test\chart\\'

auto_callbox_loc = r"C:\Users\nsait\Desktop\auto_gui"
SYS_STATUS = ['OK','DOWNLOAD_ONLY','ERROR']
BINARY_LIB = "\\\\serv2\\eng\\nsait\\workspace\\binary_lib\\"
RESULT_LOC = "\\\\serv2\\home\\gcflab\\workspace\\"

#################################################################################################
# Globals
#################################################################################################
# Tune behavior
force_retest_when_regression_or_assert = False

SCHEDULE_BUILD_TIME   = 28800 # Start new build every 8 hours.

# Constants
# TIMEOUT_DELAY          = 60   # 60 second delay -> RV - Increase value ?????
TIMEOUT_DELAY          = 120   # 120 second delay -> RV - Increase value ?????
UE_STARTUP_ATTEMPT_MAX = 10
UE_STARTUP_DELAY       =  7
NB_CPULOAD_LINES_DISP  = 20
ATTEMPT_ATTACH_MAX     =  2
MAX_REG_RETEST = 1
# Status constants
CELL_STATUS_ON = "ON,ADJ"
ATTACH_STATUS  = "ATT"

# Connection params
#PORT_COM_TANGO     = "COM5"#34"#5
PORT_COM_E410      = "COM22"
FTP_ADDRESS        = '10.21.158.87'   # RV - Not a fixed address (change after each reboot) -> Need to fix that
FTP_SERVER_ADDRESS = '172.22.1.201'
FTP_SERVER_USER    = 'anonymous'
directory_downlink = "ftp_downlink"
directory_uplink   = "ftp_uplink"


ROUTE_DISPLAY = "route PRINT"
ROUTE_ADD = "route ADD 172.22.1.0 MASK 255.255.255.0 "

ITF_REGULAR        = "Regular"
ITF_REGRESSION     = "Regression"
ITF_TANGO_VARIANT  = "tango-internal"
ITF_E410_VARIANT   = "e410-98"
BAND_E410_ALLOWED  = [1]

EXCEL_FILE = 'track_results.xls'

COL_TIME = 0; COL_CL = 1; COL_OVERALL_STATUS = 2; COL_BRANCH = 3
LIN_NAME = 0; LIN_CPU_FTP_INFO = 1; LIN_WEIGHT_INFO = 2; LIN_INFO = 3
STATUS_OK = "Ok"; STATUS_REGRESSION = "Reg"; STATUS_ASSERT = "Assert"; STATUS_ERROR = "Error" ; STATUS_CRASH = "Crash"
EXCEL_STATUS = [STATUS_OK,STATUS_REGRESSION,STATUS_ASSERT,STATUS_ERROR]
CHECK_LOW = "<"; CHECK_HIGH = ">"; CHECK_SAME = "="; NO_CHECK = ""  # NO_CHECK, CHECK_LOW, CHECK_HIGH, CHECK_SAME = range(4)
NO_ERROR, ERROR_NO_INIT_YET, ERROR_NO_ATTACH, ERROR_NO_IP_ADDRESS = range(4)

file_log_message = "log_message.txt"
branch = "main"

REGRESSION_DELTA_DOWNLINK = 0.1  # 10% of acceptable variation for test comparison in DL
REGRESSION_DELTA_UPLINK = 0.15  # 15% of acceptable variation for test comparison in UL and combDLUL
REGRESSION_DELTA_DXP = 0.07 #
NB_PRECISION = 2


TIME_CPULOAD_FIND = 5
RB_START     = 36 # RV - RB_START Should not be upper than 39
TBSIDX_START = 20
RB_END = 50
TBSIDX_END = 25

campaign_implemented = ["FTP_SISO_DL_AM", "FTP_SISO_UL_UM", "FTP_SISO_UL_AM", "FTP_SISO_COMB_DLUL", "FTP_MIMO_DL_AM"]


scenario_implemented = [
    "FTP_DL_SISO_AM_RB50_TBS25",
     "FTP_DL_SISO_AM_RB50_TBS26",
     "FTP_UL_AM_RB45_TBSIDX18_2_FILES",
     "FTP_UL_AM_RB40_TBSIDX16_2_FILES",
     # "FTP_UL_AM_MAX_2_FILES",
     # "FTP_UL_UM_RB45_TBSIDX18_1_FILE",
     "FTP_UL_UM_RB45_TBSIDX18_2_FILES",
     # "FTP_COMB_DLUL_1_FILE_UL",
     "FTP_COMB_DLUL_2_FILES_UL",
    "FTP_DL_MIMO_AM_RB39_TBS25",
      "FTP_DL_MIMO_AM_RB42_TBS24",
    #"FTP_DL_MIMO_AM_FIND_MAX_DEFAULT"
    ]


force_find_reg_after_attach_fail = False

MAX_TEST_TIME = 3600 * 2
MAX_BUILD_TIME = 3600 * .7

BUILD_OK = "OK"
BUILD_FAILED = "Failed"

cell_style = easyxf('alignment: horizontal right;')
status_OK_style     = easyxf('alignment: horizontal center;'
                             'font: colour lime, bold True;'
                             'border: right thin;')
status_REG_style    = easyxf('alignment: horizontal center;'
                             'font: colour light_orange, bold True;'
                             'border: right thin;')
status_ASSERT_style = easyxf('alignment: horizontal center;'
                             'font: colour red, bold True;'
                             'border: right thin;')
status_ERROR_style  = easyxf('alignment: horizontal center;'
                             'font: colour yellow, bold True;'
                             'border: right thin;')
changelist_style    = easyxf('alignment: horizontal center;'
                             'font: colour blue, bold True;'
                             'border: right thin;')
time_style          = easyxf('alignment: horizontal left;'
                             'border: right thin;')
branch_style        = easyxf('alignment: horizontal center;'
                             'border: right thin;')

