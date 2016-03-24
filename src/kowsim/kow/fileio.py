# -*- coding: utf-8 -*-

# kow/fileio.py
#===============================================================================
import codecs
#from unit import UnitProfile

#===============================================================================
# ArmyListWriter
#===============================================================================
class ArmyListWriter:
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
            f.write("%d\n" % len(d.ListUnits()))
            for u in d.ListUnits():
               cols = [u.Profile().Name(), u.CustomName(), u.ItemName()]
               cols.extend([o.Name() for o in u.ListChosenOptions()])
               f.write(";".join(cols) + "\n")