# -*- coding: utf-8 -*-

# armybuilder/command.py
#===============================================================================
from PySide import QtGui#, QtCore
from kowsim.command.command import ModelViewCommand, ReversibleCommandMixin
from kowsim.kow.force import Detachment
from dialogs import AddDetachmentDialog
from kowsim.kow.unit import UnitInstance
import kowsim.kow.sizetype

#===============================================================================
# AddDetachmentCmd
#===============================================================================
class AddDetachmentCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, armylist, armylistview):
      ModelViewCommand.__init__(self, model=armylist, view=armylistview, name="AddDetachmentCmd")
      ReversibleCommandMixin.__init__(self)
      
   def Execute(self):
      dlg = AddDetachmentDialog()
      
      if QtGui.QDialog.Accepted == dlg.exec_():
         ## BUG: WTF - This will initialize units with something != [] !?!?!?!?
         ##detachment = Detachment(dlg.Force(), isPrimary=dlg.MakePrimary())
         ## use this instead:
         detachment = Detachment(dlg.Force(), None, [], dlg.MakePrimary())
         self._model.AddDetachment(detachment)
         self._view.AddDetachmentView(detachment)
         
         
#===============================================================================
# RenameDetachmentCmd
#===============================================================================
class RenameDetachmentCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, detachment, detachmentview):
      ModelViewCommand.__init__(self, model=detachment, view=detachmentview, name="RenameDetachmentCmd")
      ReversibleCommandMixin.__init__(self)
      
   def Execute(self, name):
      oldname = self._model.CustomName()
      
      if name!=oldname:
         self._model.SetCustomName(name)
         self._view.siNameChanged.emit(name)

         
#===============================================================================
# AddDefaultUnitCmd
#===============================================================================
class AddDefaultUnitCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, detachment, detachmentview):
      ModelViewCommand.__init__(self, model=detachment, view=detachmentview, name="AddDefaultUnitCmd")
      ReversibleCommandMixin.__init__(self)
   
   def Execute(self):
      self._model.AddUnit(UnitInstance(self._model.Choices().ListUnits()[0], self._model))
      index = self._model.NumUnits()-1
      self._view.UpdateUnit(index)
      self._view.UpdatePoints()
      
      
#===============================================================================
# ChangeUnitCmd
#===============================================================================
class ChangeUnitCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, detachment, unittable):
      ModelViewCommand.__init__(self, model=detachment, view=unittable, name="ChangeUnitCmd")
      ReversibleCommandMixin.__init__(self)
   
   def Execute(self, row, newUnitName):
      newProfile = self._model.Choices().GroupByName(newUnitName).ListOptions()[0]
      newUnit = newProfile.CreateInstance(self._model)
      
      self._model.ReplaceUnit(row, newUnit)
      self._view.SetRow(row, newUnit)
      self._view.siPointsChanged.emit()
      

#===============================================================================
# ChangeUnitSizeCmd
#===============================================================================
class ChangeUnitSizeCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, detachment, unittable):
      ModelViewCommand.__init__(self, model=detachment, view=unittable, name="ChangeUnitSizeCmd")
      ReversibleCommandMixin.__init__(self)
   
   def Execute(self, row, sizeStr):
      newSize = kowsim.kow.sizetype.Find(sizeStr).Name()
      
      unitname = self._model.Unit(row).Profile().Name()
      newProfile = self._model.Choices().GroupByName(unitname).ProfileForSize(newSize)
      self._model.Unit(row).SetProfile(newProfile)
      self._view.UpdateTextInRow(row)
      self._view.siPointsChanged.emit()
      

#===============================================================================
# SetUnitOptionsCmd
#===============================================================================
class SetUnitOptionsCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, unit, unittable):
      ModelViewCommand.__init__(self, model=unit, view=unittable, name="SetUnitOptionsCmd")
      ReversibleCommandMixin.__init__(self)
   
   def Execute(self, row, options):
      self._model.ClearChosenOptions()
      for opt in options:
         self._model.ChooseOption(opt)
      
      self._view.UpdateTextInRow(row)
      self._view.siPointsChanged.emit()
