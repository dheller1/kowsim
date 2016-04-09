# -*- coding: utf-8 -*-

# armybuilder/control.py
#===============================================================================
from PySide import QtCore
from kowsim.kow.unit import UnitInstance
import kowsim.mvc.mvcbase as MVC

#===============================================================================
# ArmyListCtrl
#===============================================================================
class ArmyListCtrl(MVC.Controller):
   #HINTS:
   REVALIDATE              = 10001
   CHANGE_NAME             = 10002
   
   def __init__(self, model):
      MVC.Controller.__init__(self, model)
      self._model = model
      self._modified = False
            
   def AddUnitToDetachment(self, unitname, detachment):
      try: index = self._model.ListDetachments().index(detachment)
      except ValueError:
         raise ValueError("Can't add to a detachment not belonging to my armylist!")
      
      profile = detachment.Choices().GroupByName(unitname).Default()
      detachment.AddUnit(UnitInstance(profile, detachment, None, [], None))
      self.SetModified(True)
      self.siDetachmentModified.emit(index)
      
   def Revalidate(self):
      self.NotifyModelChanged(ArmyListCtrl.REVALIDATE)
   
   def SetArmyName(self, name):
      print "ArmyListCtrl.SetArmyName('%s')" % name
      self.Model().Data().SetCustomName(name)
      self.NotifyModelChanged(ArmyListCtrl.CHANGE_NAME)
   
   def SetModified(self, modified=True):
      self._modified = modified
      
   def SetPrimaryDetachment(self, detachment, makePrimary):
      try: self._model.ListDetachments().index(detachment)
      except ValueError:
         raise ValueError("Can't modify a detachment not belonging to my armylist!")
      
      detachment._isPrimary = makePrimary
      self.Revalidate()