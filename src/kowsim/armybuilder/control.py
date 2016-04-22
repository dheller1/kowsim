# -*- coding: utf-8 -*-

# armybuilder/control.py
#===============================================================================
from PySide import QtCore
from kowsim.kow.unit import UnitInstance
from command import RenameArmyListCmd
import kowsim.mvc.mvcbase as MVC
import kowsim.armybuilder.views

#===============================================================================
# ArmyListCtrl
#===============================================================================
class ArmyListCtrl(MVC.Controller):
   #HINTS:
   # TODO: move hints to Model instead of Controller?
   REVALIDATE              = 10001
   CHANGE_NAME             = 10002
   
   def __init__(self, model):
      MVC.Controller.__init__(self, model)
      self._model = model
      self._modified = False
      self.attachedPreview = None
            
   def AddUnitToDetachment(self, unitname, detachment):
      try: index = self._model.ListDetachments().index(detachment)
      except ValueError:
         raise ValueError("Can't add to a detachment not belonging to my armylist!")
      
      profile = detachment.Choices().GroupByName(unitname).Default()
      detachment.AddUnit(UnitInstance(profile, detachment, None, [], None))
      self.SetModified(True)
      self.siDetachmentModified.emit(index)
   
   def AttachView(self, view):
      self._views.add(view)
      if isinstance(view, kowsim.armybuilder.views.ArmyListOutputView) and self.attachedPreview is None:
            self.attachedPreview = view
   
   def DetachView(self, view):
      self._views.remove(view)
      if self.attachedPreview is view:
         self.attachedPreview = None
      
   def Revalidate(self):
      self.NotifyModelChanged(ArmyListCtrl.REVALIDATE)
   
   def RenameArmyList(self, name):
      print "ArmyListCtrl.RenameArmyList('%s')" % name
      self.ExecuteCmd(RenameArmyListCmd(name, self.Model().Data()))
      self.NotifyModelChanged(ArmyListCtrl.CHANGE_NAME)
   
   def SetModified(self, modified=True):
      self._modified = modified
      
   def SetPrimaryDetachment(self, detachment, makePrimary):
      try: self._model.ListDetachments().index(detachment)
      except ValueError:
         raise ValueError("Can't modify a detachment not belonging to my armylist!")
      
      detachment._isPrimary = makePrimary
      self.Revalidate()