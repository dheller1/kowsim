# -*- coding: utf-8 -*-

# kow/force.py
#===============================================================================
import alignment as al
import codecs
from unit import KowUnitProfile

#===============================================================================
# KowArmyList
#   Specific army list for a KoW army, may contain several KowForces (one primary
#   and up to multiple allied forces).
#===============================================================================
class KowArmyList(object):
   def __init__(self, name, points=2000):
      self._name = name

      self._primaryForce = KowDetachment(KowForceChoices("Elves", al.AL_GOOD), "Elf detachment")
      self._alliedForces = []
      self._pointsLimit = points
   
   # getters/setters
   def Name(self): return self._name
   def PointsLimit(self): return self._pointsLimit
   def PrimaryForce(self): return self._primaryForce
   def SetName(self, name): self._name = name
   def SetPointsLimit(self, pts): self._pointsLimit = pts
   def SetPrimaryForce(self, force): self._primaryForce = force
   
   # routines
   def LoadFromFile(self, filename, dataMgr): # dataMgr needed for access to force lists and units by name
      with codecs.open(filename, "r", encoding='UTF-8') as f:
         self._name = f.readline().strip()
         try: self._pointsLimit = int(f.readline().strip())
         except ValueError:
            raise IOError("Invalid file %s. (Can't convert total points cost to int)" % filename)
            return
         
         pfName = f.readline().strip() # e.g. 'My Elf detachment'
         pfArmy = f.readline().strip() # e.g. 'Elves'
         del self._primaryForce
         # somehow, if you don't explicitly set units=[] here, it causes a giant bug where units is a non-empty
         # list of units in the previous army list. should now be fixed.
         self._primaryForce = KowDetachment(dataMgr.ForceChoicesByName(pfArmy), pfName, units=[])
         
         try: numUnits = int(f.readline().strip())
         except ValueError:
            raise IOError("Invalid file %s. (Can't convert number of units to int)" % filename)
            return
         
         for i in range(numUnits):
            cols = [col.strip() for col in f.readline().strip().split(',')]
            
            unitName = cols[0]
            unitSizeType = cols[1]
            unitItem = cols[2]
            try: unitCost = int(cols[3])
            except ValueError:
               raise IOError("Invalid file %s. (Can't convert unit points cost to int)" % filename)
               return
            
            try: unitGroup = self._primaryForce.Choices().GroupByName(unitName)
            except KeyError:
               print "Warning: Invalid unit %s! Skipping unit in army list." % unitName
               print "Groups:", [g.Name() for g in self._primaryForce.Choices().ListGroups()]
               continue
            
            try: unitSizeOpt = unitGroup.OptionByName(unitSizeType)
            except KeyError:
               print "Warning: Unit %s has invalid size %s! Skipping unit in army list." % (unitName, unitSizeType)
               continue
            
            if len(unitItem)>0:
               try: item = dataMgr.ItemByName(unitItem)
               except KeyError:
                  print "Warning: Item %s for unit %s not found. Unit will have no item." % (unitItem, unitName)
                  item = None
            else: item = None
            
            unit = unitSizeOpt.Clone()
            unit.SetItem(item)
            
            if unit.PointsCost() != unitCost:
               print "Warning: Unit %s seems to have invalid points cost (%d should be %d)." % (unitName, unitCost, unit.PointsCost())
               
            self._primaryForce.AddUnit(unit)
            
      print "Successfully loaded army list %s (%s), %d units." % (self._name, filename, self._primaryForce.NumUnits())
   
   def SaveToFile(self, filename):
      with codecs.open(filename, 'w', encoding='UTF-8') as f:
         f.write(self._name + "\n")
         f.write(str(self._pointsLimit) + "\n")
         f.write(self._primaryForce.Name() + "\n") # detachment name
         f.write(self._primaryForce.Choices().Name() + "\n") # detachment army name
         
         f.write(str(self._primaryForce.NumUnits()) + "\n")
         
         for u in self._primaryForce.ListUnits():
            f.write(",".join([u.Name(), u.SizeType().Name(), u.ItemName(), str(u.PointsCost())]) + "\n")

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
# KowForceChoices
#   e.g. Elves, Dwarves, a single KoW army force with all of its unit choices.
#   This is static data, to generate a specific army list with some incorporated
#   units, use KowForce instead
#===============================================================================
class KowForceChoices(object):
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


#===============================================================================
# KowDetachment
#   A specific single KoW detachment such as an Elf detachment in a KowArmyList.
#   May contain anything from 0 to 100 units chosen from the associated
#   KowForceChoices representing the army (e.g. Elves).
#===============================================================================
class KowDetachment(object):
   def __init__(self, choices, name="Unnamed detachment", units=[]):
      self._choices = choices
      self._name = name
      self._units = units
      
   def AddUnit(self, unit):
      self._units.append(unit)
      return len(self._units)-1 # return index of new unit
   def Choices(self): return self._choices
   def ListUnits(self): return self._units
   def Name(self): return self._name
   def NumUnits(self): return len(self._units)
   def PointsTotal(self):
      sum = 0
      for u in self._units: sum += u.PointsCost()
      return sum
   
   def RemoveUnit(self, index):
      self._units.pop(index)

   def ReplaceUnit(self, index, newUnit):
      if index>=len(self._units): raise IndexError("Can't replace unit %d, only have %d units!" % (index, len(self._units)))
      else:
         self._units[index] = newUnit
   