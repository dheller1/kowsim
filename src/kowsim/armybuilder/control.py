# -*- coding: utf-8 -*-

# armybuilder/control.py
#===============================================================================
from PySide import QtCore
from kowsim.kow.unit import UnitInstance
from command import RenameArmyListCmd
from mvc.models import ArmyListModel
import kowsim.mvc.mvcbase as MVC
import kowsim.armybuilder.views

#===============================================================================
# ArmyListCtrl
#===============================================================================
class ArmyListCtrl(MVC.Controller):
   def __init__(self, model):
      MVC.Controller.__init__(self, model)
      self.model = model
      self.attachedPreview = None
            
   def AddUnitToDetachment(self, unitname, detachment):
      try: self.model.data.ListDetachments().index(detachment)
      except ValueError:
         raise ValueError("Can't add unit to a detachment not belonging to my armylist!")
      
      if unitname is None:
         profile = detachment.Choices().ListUnits()[0]
      else:
         profile = detachment.Choices().GroupByName(unitname).Default()
      detachment.AddUnit(UnitInstance(profile, detachment))
      self.model.Touch()
      self.NotifyModelChanged(ArmyListModel.MODIFY_DETACHMENT)
   
   def AttachView(self, view):
      self._views.add(view)
      if isinstance(view, kowsim.armybuilder.views.ArmyListOutputView) and self.attachedPreview is None:
            self.attachedPreview = view
            
   def ChangeUnitSize(self, unit, sizeType):
      unitname = unit.Profile().Name()
      newProfile = unit.Detachment().Choices().GroupByName(unitname).ProfileForSize(sizeType)
      
      unit.SetProfile(newProfile)
      self.model.Touch()
      self.NotifyModelChanged(ArmyListModel.MODIFY_UNIT, unit)
   
   def DetachView(self, view):
      self._views.remove(view)
      if self.attachedPreview is view:
         self.attachedPreview = None
         
   def ProcessHints(self, hints):
      # Currently, all hints are forwarded. As soon as commands which do not modify a model
      # are introduced (e.g. printing), these should be filtered and ignored here.
      self.NotifyModelChanged(hints)
      
   def Revalidate(self):
      self.NotifyModelChanged(ArmyListModel.REVALIDATE)
   
   def RenameArmyList(self, name):
      print "ArmyListCtrl.RenameArmyList('%s')" % name
      self.ExecuteCmd(RenameArmyListCmd(name, self.model.Data()))
      self.NotifyModelChanged(ArmyListModel.CHANGE_NAME)
      self.model.Touch()
      
   def SetPrimaryDetachment(self, detachment, makePrimary):
      try: self._model.ListDetachments().index(detachment)
      except ValueError:
         raise ValueError("Can't modify a detachment not belonging to my armylist!")
      
      detachment._isPrimary = makePrimary
      self.Revalidate()