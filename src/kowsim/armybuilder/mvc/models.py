# -*- coding: utf-8 -*-

# mvc/models.py
#===============================================================================
from kowsim.kow.force import ArmyList
from kowsim.mvc.mvcbase import Model

#===============================================================================
# ArmyListModel
#===============================================================================
class ArmyListModel(Model):   
   def __init__(self, *args):
      if len(args)==1 and isinstance(args[0], ArmyList):
         armylist = args[0]
         Model.__init__(self, armylist)
      else:
         name, points = args
         Model.__init__(self, ArmyList(name, points))
