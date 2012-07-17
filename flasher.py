
import os, time, sys, re, subprocess, string,stat,commands,tarfile,shutil
from device_management import *
from global_var import *
import common
from FindRegression import *
#import chilkat
from tools import *
from cardhu2 import *
#import UnRAR2
BAT_FILE = "flash.bat"
ATDBG_BAT = "at_debug.bat"

escape_dict={'\a':r'\a',
           '\b':r'\b',
           '\c':r'\c',
           '\f':r'\f',
           '\n':r'\n',
           '\r':r'\r',
           '\t':r'\t',
           '\v':r'\v',
           '\'':r'\'',
           '\"':r'\"',
           '\0':r'\0',
           '\1':r'\1',
           '\2':r'\2',
           '\3':r'\3',
           '\4':r'\4',
           '\5':r'\5',
           '\6':r'\6',
           '\7':r'\7',
           '\8':r'\8',
           '\9':r'\9'}

def raw(text):
    """Returns a raw string representation of text"""
    new_string=''
    for char in text:
        try: new_string+=escape_dict[char]
        except KeyError: new_string+=char
    return new_string

class Untar:

    def untar(self,dst,file_name):
        os.chdir(dst)
        tar = tarfile.open(file_name,'r:gz')#sys.argv[1] + '.tar.gz', 'r:gz')
        for item in tar:
            tar.extract(item)
            #print 'Done.'

    def file_search(self,rootdir,file_name):
        fileList = []
        f = ""
        print rootdir
        for root, subFolders, files in os.walk(rootdir):
            for file in files:
                fileList.append(os.path.join(root,file))

        for f in fileList:
            if re.search(re.compile(r"%s(\S+)"%file_name),f):
                loc = f
                break

        print f
        return f

    def remove_readonly(self,fn, path, excinfo):
        if fn is os.rmdir:
            os.chmod(path, stat.S_IWRITE)
            os.rmdir(path)
        elif fn is os.remove:
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)

    def unrar(self,dst,file_name):
        return
        #os.chdir(dst)
        #UnRAR2.RarFile(file_name).extract()
        #return
##        rar = chilkat.CkRar()
##        success = rar.Open(file_name)
##        if (success != True):
##            print rar.lastErrorText()
##            sys.exit(-1)
##
##        success = rar.Unrar(dst)
##        if (success != True):
##            print rar.lastErrorText()
##        else:
##            print "Success."


    def main(self,src):
        tmp = 'C:\\tmpgz\\'
        tmp_gz =tmp+ 'xyz.gz'
        tmp_rar = tmp+ 'xyz.rar'
        name = "99999.zlib.wrapped"
        try:
            os.mkdir(tmp)
        except:
            shutil.rmtree(tmp, onerror=self.remove_readonly)
            os.mkdir(tmp)


        src = raw(src)
        if re.search(".wrapped",src):
            print "Modem.wrapped found"
            shutil.copy2(src,BINARY_LIB+name)
            return
        elif re.search(".rar",src):
            print "Rar Found"
            shutil.copy2(src,tmp_rar)
            self.unrar(tmp,tmp_rar)
        elif re.search(".gz",src):
            print "GZ Found"
            shutil.copy2(src,tmp_gz)
            self.untar(tmp,tmp_gz)

        modem_file = self.file_search(tmp,'modem-rsa')
        if not re.search("modem",modem_file):
            modem_file = self.file_search(tmp,'modem')
        print "Modem File",modem_file

        try:
            shutil.copy2(modem_file,BINARY_LIB+name)
        except:
            pass

        os.chdir(auto_callbox_loc)

class At_debug:
    def get_coredump(self,branch,cl,scen_name,option):
##        if(int(idev.get_download_port())!=0):
##            port = idev.get_download_port()
##        else:
        port = common.MODEM_PORT

        download = []
        #download.append("pushd \\\serv2.icerasemi.com\home\gcflab\workspace\callbox-test\software\main.br\\tools")
        download.append(r"pushd \\%s\software\main.br\tools"%wwin)
        if option == 'clear_history':
            download.append("at_debug.py -d %s %s"%(str(port),option))
        else:
            download.append("at_debug.py -d %s -p coredump\%s_%s %s"%(str(port),scen_name,option,option))
        download.append("popd")
        download.append("echo download > endBatch")

        if os.path.exists(ATDBG_BAT) :
            os.remove(ATDBG_BAT)

        for i in range(0,3) :
            cmd = "echo "+download[i]+" >> " + ATDBG_BAT
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            print cmd
            time.sleep(1)

        print "\Getting ",option
        os.system(ATDBG_BAT)
        os.system("endFlash.bat")
        flash = Flash()
        flash.check_end_batch()

        #move modem.exe file
        if option == 'fullcoredump':
            try:
                i = Tools().find_index(BRANCH_ALLOWED,branch)
                if not os.path.exists('\\\\'+COREDUMP_LOC+'\\'+str(cl)+'.exe') :
                    shutil.copy2(MODEM_BINARY_LOC[i]+"modem.exe",'\\\\'+COREDUMP_LOC+'\\'+str(cl)+'.exe')
            except:
                pass
                #Tools().sendMail("Error in COpying "+MODEM_BINARY_LOC[i]+"modem.exe"+'\\\\'+COREDUMP_LOC+'\\'+cl+'.exe')

class Flash:
    def init(self):
        self.cl = 0
        self.branch = "cr3"
        self.port = common.MODEM_PORT

    def parseArgs(self,args):
        print "\nParsing the arguments..."
        idxArg = 0
        # Parse arguments
        while idxArg < len(args):
            if args[idxArg] in ("-help", "--help", "-h"):
                sys.exit(-1)
            elif args[idxArg] in ("-c"):
                idxArg += 1
                self.cl = int(args[idxArg])
            elif args[idxArg] in ("-main"):
                self.branch = "main"
            elif args[idxArg] in ("-cr3"):
                self.branch = "cr3"
            elif args[idxArg] in ("-p"):
                idxArg += 1
                self.port = args[idxArg]
            else:
                print "ERROR: Unknown parameter: %s" %args[idxArg]
                sys.exit(-1)
            idxArg += 1

    def batch_init(self):
        download = []
        idev = device_management()
        #if(int(idev.get_download_port())!=0):
        self.port = common.MODEM_PORT

        #download.append("pushd \\\\%s\software\main.br\\tools"%wwin)
        download.append(r"pushd \\%s\software\main.br\tools"%wwin)
        #if self.branch == "main" :
        #download.append("pushd \\\serv2.icerasemi.com\home\gcflab\workspace\callbox-test\software\main.br\\tools")
        #else:
        #download.append("pushd \\\serv2.icerasemi.com\home\gcflab\workspace\callbox-test_cr3\software\\releases\core\cr3.br\\tools")

        if self.cl == 0 :
            download.append(("download_all.exe -v 3 -d %s --mass_storage=None --factory_tests=None --secondary_boot=None --loader=None --iso=None --customConfig=None --deviceConfig=None --productConfig=None --modem=modem-rsa-key0.zlib.wrapped ..\product\datacard\modem\\build\dxp-tango-internal-obj\EV4"%self.port))
        else:
            #download.append( ("download_all.exe -v 3 -d %s --mass_storage=None --factory_tests=None --secondary_boot=None --loader=None --iso=None --customConfig=None --deviceConfig=None --productConfig=None --modem=%d.zlib.wrapped ..\product\datacard\modem\\build\dxp-tango-internal-obj\EV4\old_binary"% (self.port,int(self.cl))) )
            # download.append( ("download_all.exe -v 3 -d %s --mass_storage=None --factory_tests=None --secondary_boot=None --loader=None --iso=None --customConfig=None --deviceConfig=None --productConfig=None --modem=%d.zlib.wrapped \\\serv2.icerasemi.com\home\gcflab\workspace\\binary_lib "% (self.port,int(self.cl))) )
            download.append( ("download_all.exe -v 3 -d %s --mass_storage=None --factory_tests=None --secondary_boot=None --loader=None --iso=None --customConfig=None --deviceConfig=None --productConfig=None --modem=%d.zlib.wrapped %s "% (self.port,int(self.cl),BINARY_LIB)) )

        download.append("popd")
        download.append("echo download > endBatch")

        if os.path.exists(BAT_FILE) :
            os.remove(BAT_FILE)

        for i in range(0,3) :
            cmd = "echo "+download[i]+" >> " + BAT_FILE
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            print cmd
            time.sleep(1)

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


    def download(self):
        print "\nFlashing board..."
        os.system(BAT_FILE)
        os.system("endFlash.bat")
        self.check_end_batch()
        return

    def _flash(self):
        self.init()
        #self.parseArgs(sys.argv[1:])
        self.cl = 1
        #self.batch_init()
        #self.download()
        common.CARDHU = True
        print Cardh_ctrl().send_cmd('alive')
        Flash().flash_modem(473984,'main')
        return

    def cardhu_flash(self,cl):
        if  os.path.exists(BINARY_LIB+"cardhu_modem.wrapped"):
            os.remove(BINARY_LIB+"cardhu_modem.wrapped")
        shutil.copy2(BINARY_LIB+str(cl)+".zlib.wrapped",BINARY_LIB+"cardhu_modem.wrapped")
        print "sending firmware_upgrade"
        if Cardh_ctrl().send_cmd('firmware_upgrade'):
            print "Cardhu Firmware Upgrade done"
            return True
        else:
            return False

##        print "Flash End checking ...."
##        max_wait = 25
##        while max_wait and not Cardh_ctrl().send_cmd('alive'):
##            print Cardh_ctrl().send_cmd('alive')
##            print "Checking Flash End ...",max_wait
##            time.sleep(10)
##            max_wait = max_wait - 1
##        return


    def flash_modem(self,cl,branch):
        self.init()
        self.cl = cl
        self.branch = branch
        if self.cl != 0 :
            if not os.path.exists(BINARY_LIB+str(self.cl)+".zlib.wrapped"):
                Tools().build(branch,self.cl)
                #Regression().build_cl(branch,self.cl)

##        if common.CARDHU:
##            #if not self.cardhu_flash(self.cl):
##            self.cardhu_flash(self.cl)
##            return

        self.batch_init()
        self.download()

if __name__ == '__main__':
    #At_debug().get_coredump("xx",'minicoredump')
    Flash()._flash()