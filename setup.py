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

# setup.py

from distutils.core import setup
import py2exe, sys, os
import glob

sys.argv.append('py2exe')

setup(
    name = 'iTester',
    version='3.00',
    author='Niyas Sait',
    description = 'NVIDIA',
    console=[{'script':'gui2.py'}],
    data_files=[('.', glob.glob('*.dll')),
                  ('.', glob.glob('*.pyd'))],
    zipfile=None,
    options = {"py2exe": {
##          'compressed': 1,
##          'optimize': 2,
##          'ascii': 1,
   ##       'bundle_files': 1,
    ##      'packages' : ['chilkat','_chilkat'],
          'dll_excludes': ['javax.comm', 'mswsock.dll', 'powrprof.dll', 'MSVCP90.dll','MSVCR80.dll'],
##          'typelibs' : [("{EAB22AC0-30C1-11CF-A7EB-0000C05BAE0B}", 0, 1, 1)],
          }}
    )


##setup(console=["gui2.py"])