# -*- coding: utf-8 -*-

# kow/force.py
#===============================================================================
import alignment as al

#===============================================================================
# KowArmyList
#   Specific army list for a KoW army, may contain several KowForces (one primary
#   and up to multiple allied forces).
#===============================================================================
class KowArmyList(object):
   def __init__(self, name, points=2000):
      self._name = name

      self._primaryForce = KowForce("Elves", al.AL_GOOD)
      self._alliedForces = []
      self._pointsLimit = points
      
   def Name(self): return self._name
   def PrimaryForce(self): return self._primaryForce
   def SetName(self, name): self._name = name
   def SetPrimaryForce(self, force): self._primaryForce = force 


#===============================================================================
# KowUnitGroup
#===============================================================================
class KowUnitGroup(object):
   def __init__(self, name, default=None):
      self._name = name
      self._defaultOption = default
      self._sizeOptions = [] # list of KowUnitProfiles
      self._optionsByName = {}
      if default is not None:
         self.AddSizeOption(default)
         
   def Default(self): return self._defaultOption
   def ListOptions(self): return self._sizeOptions
   def Name(self): return self._name
   def OptionByName(self, name): return self._optionsByName[name]
      
   def AddSizeOption(self, opt):
      if len(self._sizeOptions)==0:
         self._defaultOption = opt
      self._sizeOptions.append(opt)
      self._optionsByName[opt.SizeType().Name()] = opt


#===============================================================================
# KowForce
#   e.g. Elves, Dwarves, a single KoW army force with its incorporated units
#===============================================================================
class KowForce(object):
   def __init__(self, name, alignment, units=[]):
      self._name = name
      self._alignment = alignment
      self._units = units
      self._groups = []
      self._groupsByName = {}
      
   def GroupUnits(self):
      """ Group units by their type (e.g. Sea Guard) which might have multiple size options
         (e.g. Regiment, Horde). """
      self._groups = []
      self._groupsByName = {}
      
      for u in self._units:
         if u.name not in self._groupsByName.keys():
            grp = KowUnitGroup(u.name, u) # add group with default
            self._groups.append(grp)
            self._groupsByName[grp.Name()] = grp 
         else:
            grp = self._groupsByName[u.name]
            grp.AddSizeOption(u)
   
   def GroupByName(self, name):
      if len(self._groups)==0: self.GroupUnits()
      return self._groupsByName[name]
   def ListGroups(self):
      if len(self._groups)==0: self.GroupUnits()
      return self._groups
   def ListUnits(self): return self._units   
   def Name(self): return self._name
   def NumUnits(self): return len(self._units)
   