# -*- coding: utf-8 -*-

# globals.py
#===============================================================================
from PySide import QtCore

#===============================================================================
# BASEDIR
#===============================================================================
BASEDIR = None
_BASEDIR_LOADED = False

def LoadSettings():
   global BASEDIR, _BASEDIR_LOADED
   
   if not _BASEDIR_LOADED:
      #print "Loading Basedir setting"
      settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
      BASEDIR = settings.value("Basedir")
      #print BASEDIR
      _BASEDIR_LOADED = True