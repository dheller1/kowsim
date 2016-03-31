# -*- coding: utf-8 -*-

# armybuilder/control.py
#===============================================================================
from PySide import QtCore
from kowsim.kow.unit import UnitInstance

#===============================================================================
# ArmyListCtrl
#===============================================================================
class ArmyListCtrl(QtCore.QObject):
   siDetachmentModified = QtCore.Signal(int)
   
   def __init__(self, model, view):
      super(ArmyListCtrl, self).__init__()
      self._model = model
      self._view = view
      self._modified = False
      
      self._ConnectToView()
      
   def _ConnectToView(self):
      self.siDetachmentModified[int].connect(self._view.UpdateDetachment)
      
   def AddUnitToDetachment(self, unitname, detachment):
      try: index = self._model.ListDetachments().index(detachment)
      except ValueError:
         raise ValueError("Can't add to a detachment not belonging to my armylist!")
      
      profile = detachment.Choices().GroupByName(unitname).Default()
      detachment.AddUnit(UnitInstance(profile, detachment, None, [], None))
      self.SetModified(True)
      self.siDetachmentModified.emit(index)
      
   def SetModified(self, modified=True):
      self._modified = modified
      