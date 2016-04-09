# -*- coding: utf-8 -*-

# mvc/models.py
#===============================================================================
from kowsim.kow.force import ArmyList
from kowsim.mvc.mvcbase import Model

#===============================================================================
# ArmyListModel
#===============================================================================
class ArmyListModel(Model):
   def __init__(self, name, points):
      Model.__init__(self, ArmyList(name, points))
      
   def AddDetachment(self, *args):
      self.Data().AddDetachment(*args)
      self._NotifyChanges()