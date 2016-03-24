# -*- coding: utf-8 -*-

# armybuilder/command.py
#===============================================================================
from PySide import QtGui#, QtCore
from kowsim.command.command import ModelViewCommand, ReversibleCommandMixin
from kowsim.kow.force import Detachment
from dialogs import AddDetachmentDialog
from kowsim.kow.unit import UnitInstance
from kowsim.kow.fileio import ArmyListWriter
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
      self._model.AddUnit(UnitInstance(self._model.Choices().ListUnits()[0], self._model, None, []))
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
      self._view.UpdateUnitOptions(row)
      self._view.siPointsChanged.emit()
      

#===============================================================================
# ChangeUnitItemCmd
#===============================================================================
class ChangeUnitItemCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, unit, unittable):
      ModelViewCommand.__init__(self, model=unit, view=unittable, name="ChangeUnitSizeCmd")
      ReversibleCommandMixin.__init__(self)
   
   def Execute(self, row, item):
      self._model.SetItem(item)
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


#===============================================================================
# DeleteUnitCmd
#===============================================================================
class DeleteUnitCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, detachment, unittable):
      ModelViewCommand.__init__(self, model=detachment, view=unittable, name="DeleteUnitCmd")
      ReversibleCommandMixin.__init__(self)
   
   def Execute(self):
      rowsToDelete = self._view.unitTable.SelectedRows()
      
      if len(rowsToDelete)==1:
         confirm="This will delete the current unit.<br />Are you sure?"
      elif len(rowsToDelete)>1:
         confirm="This will delete %d units.<br />Are you sure?" % len(rowsToDelete)
      
      if QtGui.QMessageBox.Yes != QtGui.QMessageBox.warning(self._view, "Delete unit", confirm, QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel):
         return
      
      # sort in descending order to not interfere with higher row IDs when popping from list
      rowsToDelete.sort(reverse=True)
      #print "Deleting rows: ", rowsToDelete

      for row in rowsToDelete:
         print "Deleting unit %d (%s)" % (row, self._model.Unit(row))
         self._model.RemoveUnit(row)
         self._view.unitTable.removeRow(row)
      
      self._view.UpdatePoints()
      

#===============================================================================
# DuplicateUnitCmd
#===============================================================================
class DuplicateUnitCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, detachment, unittable):
      ModelViewCommand.__init__(self, model=detachment, view=unittable, name="DuplicateUnitCmd")
      ReversibleCommandMixin.__init__(self)
   
   def Execute(self):
      rows = self._view.unitTable.SelectedRows()
      
      for row in rows:
         oldUnit = self._model.Unit(row)
         newUnit = oldUnit.Profile().CreateInstance(self._model)
         for o in oldUnit.ListChosenOptions():
            newUnit.ChooseOption(o)
         index = self._model.AddUnit(newUnit)
         self._view.UpdateUnit(index)
      
      self._view.UpdatePoints()
      

#===============================================================================
# SaveArmyListCmd
#===============================================================================
class SaveArmyListCmd(ModelViewCommand):
   def __init__(self, armylist, armylistview):
      ModelViewCommand.__init__(self, model=armylist, view=armylistview, name="SaveArmyListCmd")
   
   def Execute(self, saveAs=False):
      if (not self._view._lastFilename) or saveAs:
         filename, filter = QtGui.QFileDialog.getSaveFileName(self._view, "Save army list as", "../%s.lst" % self._model.CustomName(), "Army lists (*.lst);;All files (*.*)")
         if filename == "": return
         else: self._view._lastFilename = filename
      else:
         filename = self._view._lastFilename
      
      alw = ArmyListWriter(self._model)
      alw.SaveToFile(filename)
      self._view.SetModified(False)