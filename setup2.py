#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Administrator
#
# Created:     02/07/2012
# Copyright:   (c) Administrator 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

# Setup Script - <a title="How to rotate an Ellipse?" href="http://mycola.info/2012/04/29/how-to-rotate-an-ellipse/" target="_blank">For ellipse rotation program</a>
# www.mycola.info
#Samitha Ransara - The University of Auckland
from distutils.core import setup
import py2exe
from distutils.filelist import findall
import os
import chilkat
import py2exe, sys
import glob

matplotlibdatadir = r"C:\Documents and Settings\Administrator\Desktop\auto_callbox"    #find the data directories
matplotlibdata = findall(matplotlibdatadir)            #find all files
matplotlibdata_files = []
for f in matplotlibdata:
    dirname = os.path.join('matplotlibdata', f[len(matplotlibdatadir)+1:])
    matplotlibdata_files.append((os.path.split(dirname)[0], [f]))
#include all dependency packages and exclude troublesome DLL s, you might need to exclude more or less DLL
#files based on your operating system.

setup(
    name = 'iTester',
    version='3.00',
    author='Niyas Sait',
    description = 'NVIDIA',
    console=[{'script':'gui2.py',
            'icon_resources':[(1,'icera.ico')]}],
    data_files=[('.', glob.glob('*.dll')),
                  ('.', glob.glob('*.pyd'))],
    zipfile=None,
    options = {"py2exe": {
##          'compressed': 1,
##          'optimize': 2,
##          'ascii': 1,
         'bundle_files': 1,
         ##'packages' : ['chilkat','_chilkat'],
          'dll_excludes': ['javax.comm', 'mswsock.dll', 'powrprof.dll', 'MSVCP90.dll','MSVCR80.dll'],
##          'typelibs' : [("{EAB22AC0-30C1-11CF-A7EB-0000C05BAE0B}", 0, 1, 1)],
          }}
    )

def main():
    pass

if __name__ == '__main__':
    main()
