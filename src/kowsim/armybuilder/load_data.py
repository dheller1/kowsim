# -*- coding: utf-8 -*-

# armybuilder/load_data.py
#===============================================================================
import os
from collections import deque

from PySide.QtCore import QSettings

import globals
from parsers import ForceListCsvParser as Flcp
from parsers import ItemCsvParser as Icp

#===============================================================================
# DataManager
#===============================================================================
class DataManager(object):
   DefaultNumRecentFiles = 5
   
   def __init__(self):
      self._forceChoices = []
      self._forceChoicesByName = {}
      
   def LoadForceChoices(self):
      self._forceChoices = []
      self._forceChoicesByName = {}
      
      pars = Flcp()
      
      for fn in os.listdir(os.path.join(globals.BASEDIR, "data", "kow", "forces")):
         if fn.startswith(".") or fn.endswith("#") or not fn.endswith(".csv"): # skip temporary lock files and unknown files
            continue
         pars.ReadLinesFromFile(os.path.join(globals.BASEDIR, "data", "kow", "forces", fn))
         force = pars.Parse()
         print "Parsed %s (%d units)." % (force.Name(), force.NumUnits())
         
         self._forceChoices.append(force)
         self._forceChoicesByName[force.Name()] = force
         
   def LoadItems(self):
      self._items = []
      self._itemsByName = {}
      
      pars = Icp()
      pars.ReadLinesFromFile(os.path.join(globals.BASEDIR, "data", "kow", "items", "items.csv"))
      
      self._items = pars.Parse()
      self._itemsByName = { i.Name():i for i in self._items }
      print "Parsed %d magical items." % len(self._items)

   def ForceChoicesByName(self, name): return self._forceChoicesByName[name]
   def ItemByName(self, name): return self._itemsByName[name]
   def ListForceChoices(self): return self._forceChoices
   def ListItems(self): return self._items
   
   def AddRecentFile(self, filename):
      settings = QSettings("NoCompany", "KowArmyBuilder")
      recent = deque()
      
      numRecent = int( settings.value("Recent/NumRecent") )
      for i in range(numRecent):
         val = settings.value("Recent/%d" % (i+1))
         if not val: break
         recent.append(val)

      if filename in recent: recent.remove(filename)
      elif len(recent)==numRecent: recent.pop()
      recent.appendleft(filename)

      i = 0
      for filename in recent:
         settings.setValue("Recent/%d" % (i+1), filename)
         i+=1