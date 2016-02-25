# -*- coding: utf-8 -*-

# armybuilder/load_data.py
#===============================================================================
import os
from parsers import ForceListCsvParser as Flcp
from parsers import ItemCsvParser as Icp

#===============================================================================
# DataManager
#===============================================================================
class DataManager(object):
   def __init__(self):
      self._forceChoices = []
      self._forceChoicesByName = {}
      
   def LoadForceChoices(self):
      self._forceChoices = []
      self._forceChoicesByName = {}
      
      pars = Flcp()
      
      for fn in os.listdir(os.path.join("..", "data", "kow", "forces")):
         if fn.startswith(".") or fn.endswith("#"): # skip temporary lock files
            continue
         pars.ReadLinesFromFile(os.path.join("..", "data", "kow", "forces", fn))
         force = pars.Parse()
         print "Parsed %s (%d units)." % (force.Name(), force.NumUnits())
         
         self._forceChoices.append(force)
         self._forceChoicesByName[force.Name()] = force
         
   def LoadItems(self):
      self._items = []
      self._itemsByName = {}
      
      pars = Icp()
      pars.ReadLinesFromFile(os.path.join("..", "data", "kow", "items", "items.csv"))
      
      self._items = pars.Parse()
      self._itemsByName = { i.Name():i for i in self._items }
      print "Parsed %d magical items." % len(self._items)

   def ForceChoicesByName(self, name): return self._forceChoicesByName[name]
   def ItemByName(self, name): return self._itemsByName[name]
   def ListForceChoices(self): return self._forceChoices
   def ListItems(self): return self._items