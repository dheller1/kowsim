# -*- coding: utf-8 -*-

# armybuilder/load_data.py
#===============================================================================
import os
from parsers import ForceListCsvParser as Flcp

#===============================================================================
# DataManager
#===============================================================================
class DataManager(object):
   def __init__(self):
      self._forces = []
      self._forcesByName = {}
      
   def LoadForces(self):
      self._forces = []
      self._forcesByName = {}
      
      pars = Flcp()
      
      for fn in os.listdir(os.path.join("data", "kow", "forces")):
         if fn.startswith(".") or fn.endswith("#"): # skip temporary lock files
            continue
         pars.ReadLinesFromFile(os.path.join("data", "kow", "forces", fn))
         force = pars.Parse()
         print "Parsed %s (%d units)." % (force.Name(), force.NumUnits())
         
         self._forces.append(force)
         self._forcesByName[force.Name()] = force

   def ForceByName(self, name): return self._forcesByName[name]
   def ListForces(self): return self._forces