# -*- coding: utf-8 -*-

# mvc/models.py
#===============================================================================
from kowsim.kow.force import ArmyList
from kowsim.mvc.mvcbase import Model

#===============================================================================
# ArmyListModel
#===============================================================================
class ArmyListModel(Model):
   REVALIDATE              = 10001
   CHANGE_NAME             = 10002
   MODIFY_DETACHMENT       = 10003
   
   def __init__(self, *args):
      if len(args)==1 and isinstance(args[0], ArmyList):
         armylist = args[0]
         Model.__init__(self, armylist)
      else:
         name, points = args
         Model.__init__(self, ArmyList(name, points))
      
   def AddDetachment(self, *args):
      self.Data().AddDetachment(*args)
      self._NotifyChanges()