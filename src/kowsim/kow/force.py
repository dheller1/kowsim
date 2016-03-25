# -*- coding: utf-8 -*-

# kow/force.py
#===============================================================================
import codecs
#from unit import UnitProfile

#===============================================================================
# ArmyList
#   Specific army list for a KoW army, may contain several KowForces (one primary
#   and up to multiple allied forces).
#===============================================================================
class ArmyList(object):
   def __init__(self, name, points):
      self._customName = name

      self._detachments = []
      self._pointsLimit = points
   
   # getters/setters
   def CustomName(self): return self._customName
   def ListDetachments(self): return self._detachments
   def PointsLimit(self): return self._pointsLimit
   def PointsTotal(self):
      s = 0
      for det in self._detachments: s += det.PointsTotal()
      return s
   def SetCustomName(self, name): self._customName = name
   def SetPointsLimit(self, pts): self._pointsLimit = pts
   
   # routines
   def AddDetachment(self, detachment):
      self._detachments.append(detachment)
   

#===============================================================================
# KowUnitGroup
#===============================================================================
class KowUnitGroup(object):
   def __init__(self, name, default=None):
      self._customName = name
      self._defaultOption = default
      self._sizeOptions = [] # list of KowUnitProfiles
      self._optionsByName = {}
      if default is not None:
         self.AddSizeOption(default)
         
   def Default(self): return self._defaultOption
   def ListOptions(self): return self._sizeOptions
   def Name(self): return self._customName
   def ProfileForSize(self, size): return self._optionsByName[size]
      
   def AddSizeOption(self, opt):
      if len(self._sizeOptions)==0:
         self._defaultOption = opt
      self._sizeOptions.append(opt)
      self._optionsByName[opt.SizeType().Name()] = opt


#===============================================================================
# KowForceChoices
#   e.g. Elves, Dwarves, a single KoW army force with all of its unit choices.
#   This is static data, to generate a specific army list with some incorporated
#   units, use Detachment instead
#===============================================================================
class KowForceChoices(object):
   def __init__(self, name, alignment, units=[]):
      self._customName = name
      self._alignment = alignment
      self._units = units
      self._groups = []
      self._groupsByName = {}
   
   def AlignmentName(self): return self._alignment.Name()
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
   def Name(self): return self._customName
   def NumUnits(self): return len(self._units)   


#===============================================================================
# Detachment
#   A specific single KoW detachment such as an Elf detachment in a ArmyList.
#   May contain anything from 0 to 100 units chosen from the associated
#   KowForceChoices representing the army (e.g. Elves).
#===============================================================================
class Detachment(object):
   #def __init__(self, choices, customName=None, units=[], isPrimary=False):
   def __init__(self, choices, customName, units, isPrimary):
      self._choices = choices
      if not customName:
         self._customName = "%s detachment" % choices.Name()
      else: self._customName = customName
      
      self._units = units
      self._isPrimary = isPrimary
      
   def AddUnit(self, unit):
      self._units.append(unit)
      return len(self._units)-1 # return index of new unit
   def Choices(self): return self._choices
   def CustomName(self): return self._customName
   def IsPrimary(self): return self._isPrimary
   def ListUnits(self): return self._units
   def NumUnits(self): return len(self._units)
   def PointsTotal(self):
      s = 0
      for u in self._units: s += u.PointsCost()
      return s
   
   def RemoveUnit(self, index):
      self._units.pop(index)

   def ReplaceUnit(self, index, newUnit):
      if index>=len(self._units): raise IndexError("Can't replace unit %d, only have %d units!" % (index, len(self._units)))
      else:
         self._units[index] = newUnit
         
   def SetCustomName(self, name): self._customName = name
   def Unit(self, index): return self._units[index]
