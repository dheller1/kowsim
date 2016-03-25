# -*- coding: utf-8 -*-

# kow/fileio.py
#===============================================================================
import codecs
from force import ArmyList
from kowsim.kow.force import Detachment
from kowsim.kow.unit import UnitInstance

#===============================================================================
# ArmyListWriter
#===============================================================================
class ArmyListWriter(object):
   def __init__(self, armylist):
      self.armylist = armylist
   
   def SaveToFile(self, filename):
      al = self.armylist
      with codecs.open(filename, 'w', encoding='UTF-8') as f:
         f.write(al._customName + "\n")
         f.write(str(al._pointsLimit) + "\n")
         
         f.write("%d\n" % len(al.ListDetachments())) # number of detachments
         
         for d in al.ListDetachments():
            f.write(d.Choices().Name() + "\n")
            f.write(d.CustomName() + "\n")
            f.write("%d\n" % (int(d.IsPrimary())))
            f.write("%d\n" % len(d.ListUnits()))
            for u in d.ListUnits():
               cols = [u.Profile().Name(), u.SizeType().Name(), u.CustomName(), u.ItemName()]
               cols.extend([o.Name() for o in u.ListChosenOptions()])
               f.write(";".join(cols) + "\n")


#===============================================================================
# ArmyListReader
#===============================================================================
class ArmyListReader(object):
   def __init__(self, dataMgr):
      self._dataMgr = dataMgr
      
   def _ReadInt(self, f, name="line"):
      try: res = int(f.readline().strip())
      except ValueError:
         raise IOError("Invalid file. Can't convert %s to int." % name)
      return res
   
   def LoadFromFile(self, filename):
      warnings = []
      with codecs.open(filename, 'r', encoding='UTF-8') as f:
         customName = f.readline().strip()
         pointsLimit = self._ReadInt(f, "points limit")
         armylist = ArmyList(customName, pointsLimit)
         
         numDetachments = self._ReadInt(f, "number of detachments")
         for i in range(numDetachments):
            choicesName = f.readline().strip()
            detCustomName = f.readline().strip()
            isPrimary = bool(self._ReadInt(f, "is primary detachment"))
            numUnits = self._ReadInt(f, "number of units")
            try: choices = self._dataMgr.ForceChoicesByName(choicesName)
            except KeyError:
               warnings.append("Force %s was not found. Detachment %s omitted." % (choicesName, detCustomName))
               # skip the rest of the lines
               for j in range(numUnits): f.readline()
               continue
            
            det = Detachment(choices, detCustomName, [], isPrimary)
            armylist.AddDetachment(det)
            for j in range(numUnits):
               cols = [col.strip() for col in f.readline().strip().split(";")]
               profileName = cols[0]
               unitSizeStr = cols[1]
               unitCustomName = cols[2]
               itemName = cols[3]
               optionNames = cols[4:] # can be empty
               
               try: unitGroup = det.Choices().GroupByName(profileName)
               except KeyError:
                  warnings.append("Profile for unit %s not found in force %s. Unit omitted." % (profileName, det.Choices().Name()))
                  continue
               
               try: profile = unitGroup.ProfileForSize(unitSizeStr)
               except KeyError:
                  warnings.append("Invalid size %s for unit %s in force %s. Unit omitted." % (unitSizeStr, profileName, det.Choices().Name()))
                  continue
               
               item = None
               if len(itemName)>0:
                  try: item = self._dataMgr.ItemByName(itemName)
                  except KeyError:
                     warnings.append("Item %s for unit %s not found. Unit will have no item." % (itemName, profileName))
               
               optDict = { opt.Name():opt for opt in profile.ListOptions()}
               chosenOptions = []
               for o in optionNames:
                  try: opt = optDict[o]
                  except KeyError:
                     warnings.append("Option %s for unit %s unknown. Option omitted." % (o, profileName))
                     continue
                  chosenOptions.append(opt)
                                 
               unit = UnitInstance(profile, det, unitCustomName, chosenOptions, item)
               det.AddUnit(unit)
      
      return (armylist, warnings)