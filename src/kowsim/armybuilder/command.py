# -*- coding: utf-8 -*-

# armybuilder/command.py
#===============================================================================
import os
import kowsim.kow.sizetype
from PySide import QtGui
from PySide.QtCore import QSettings
from dialogs import AddDetachmentDialog
from kowsim.command.command import Command, ModelViewCommand, ReversibleCommandMixin
from kowsim.kow.force import Detachment
from kowsim.kow.unit import UnitInstance
from kowsim.kow.fileio import ArmyListWriter, ArmyListReader

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
         self._view.SetModified(True)
         self._view._ctrl.Revalidate()
         
         
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
         self._view.SetModified(True)

         
#===============================================================================
# RenameArmyListCmd
#===============================================================================
class RenameArmyListCmd(Command, ReversibleCommandMixin):
   def __init__(self, newName, ctrl):
      Command.__init__(self, name="RenameArmyListCmd")
      ReversibleCommandMixin.__init__(self)
      self._newName = newName
      self._previousName = ctrl.Model().Data().CustomName()
      self._ctrl = ctrl
      
   def Execute(self):
      self._ctrl.SetArmyName(self._newName)
   
   def Redo(self):
      self.Execute()
   
   def Undo(self):
      self._ctrl.SetArmyName(self._previousName)
         
         
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
      self._view.SetModified(True)


#===============================================================================
# AddSpecificUnitCmd
#===============================================================================
class AddSpecificUnitCmd(Command, ReversibleCommandMixin):
   def __init__(self, armyCtrl):
      Command.__init__(self, name="AddSpecificUnitCmd")
      ReversibleCommandMixin.__init__(self)
      self._armyCtrl = armyCtrl
   
   def Execute(self, unitname, detachment):
      al = self._armyCtrl._model
      profile = al.Choices().GroupByName(unitname).Default()
      self._armyCtrl.AddUnitToDetachment(UnitInstance(profile, self._model, None, []), detachment)
      
      
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
      self._view.SetModified(True)
      

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
      self._view.SetModified(True)
      

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
      self._view.SetModified(True)
      
      
#===============================================================================
# SetPrimaryDetachmentCmd
#===============================================================================
class SetPrimaryDetachmentCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, detachment, alview):
      ModelViewCommand.__init__(self, model=detachment, view=alview, name="SetPrimaryDetachmentCmd")
      ReversibleCommandMixin.__init__(self)
   
   def Execute(self, makePrimary):
      dets = self._view._model.ListDetachments()
      ctrl = self._view._ctrl
      numPrimary = 0
      for det in dets:
         if det.IsPrimary(): numPrimary += 1
      if makePrimary and numPrimary > 0:
         res = QtGui.QMessageBox.warning(self._view, "Set primary detachment", "You already have a primary detachment.\nDo you want to make %s primary instead?" % self._model.CustomName(),
                                         QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
         if res != QtGui.QMessageBox.Ok:
            return
         for det in self._view._model.ListDetachments():
            ctrl.SetPrimaryDetachment(det, False)

      elif not makePrimary and numPrimary == 1:
         res = QtGui.QMessageBox.warning(self._view, "Set primary detachment", "You are about to remove the primary detachment, invalidating your army list.\nDo you want to proceed?",
                                         QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
         if res != QtGui.QMessageBox.Ok:
            return

      ctrl.SetPrimaryDetachment(self._model, makePrimary)
      self._view.Update()
      
      
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
      self._view.SetModified(True)


#===============================================================================
# DeleteUnitCmd
#===============================================================================
class DeleteUnitCmd(ModelViewCommand, ReversibleCommandMixin):
   def __init__(self, detachment, detview):
      ModelViewCommand.__init__(self, model=detachment, view=detview, name="DeleteUnitCmd")
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
      
      for row in rowsToDelete:
         self._model.RemoveUnit(row)
         self._view.unitTable.removeRow(row)
      
      self._view.UpdatePoints()
      self._view.SetModified(True)
      

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
      self._view.SetModified(True)
      

#===============================================================================
# SaveArmyListCmd
#===============================================================================
class SaveArmyListCmd(ModelViewCommand):
   def __init__(self, armylist, armylistview):
      ModelViewCommand.__init__(self, model=armylist, view=armylistview, name="SaveArmyListCmd")
   
   def Execute(self, saveAs=False):
      defaultName = self._view._lastFilename if self._view._lastFilename else "%s.lst" % self._model.CustomName()
      if (not self._view._lastFilename) or saveAs:
         settings = QSettings("NoCompany", "KowArmyBuilder")
         preferredFolder = settings.value("preferred_folder")
         if preferredFolder is None: preferredFolder = ".."
         
         filename = QtGui.QFileDialog.getSaveFileName(self._view, "Save army list as", "%s" % (os.path.join(preferredFolder, defaultName)),
                                                      "Army lists (*.lst);;All files (*.*)")[0]
         if filename == "": return
         else: self._view._lastFilename = filename
         QtGui.qApp.DataManager.AddRecentFile(filename)
         settings.setValue("preferred_folder", os.path.dirname(filename))
         self._view.siRecentFilesChanged.emit()
      else:
         filename = self._view._lastFilename
      
      alw = ArmyListWriter(self._model)
      alw.SaveToFile(filename)
      self._view.SetModified(False)
      

#===============================================================================
# LoadArmyListCmd
#===============================================================================
class LoadArmyListCmd(Command):
   def __init__(self, mdiArea):
      Command.__init__(self, name="SaveArmyListCmd")
      self._mdiArea = mdiArea
   
   def Execute(self, filename=None):
      if filename is None:
         settings = QSettings("NoCompany", "KowArmyBuilder")
         preferredFolder = settings.value("preferred_folder")
         if preferredFolder is None: preferredFolder = ".."
         filename, fil = QtGui.QFileDialog.getOpenFileName(self._mdiArea, "Open army list", preferredFolder, "Army lists (*.lst);;All files (*.*)")
         if len(filename)==0: return
         else: settings.setValue("preferred_folder", os.path.dirname(filename))
      
      # check if the file is already open
      for wnd in self._mdiArea.subWindowList():
         if hasattr(wnd.widget(), '_lastFilename') and wnd.widget()._lastFilename == filename: # be sure not to check preview or other windows --- this is ugly. TODO: Better solution
            self._mdiArea.setActiveSubWindow(wnd)
            return
      
      alr = ArmyListReader(QtGui.qApp.DataManager)
      
      try: armylist, warnings = alr.LoadFromFile(filename)
      except IOError as e:
         QtGui.QMessageBox.critical(self._mdiArea, "Error loading %s" % filename, "We're sorry, the file could not be loaded.\nError message:\n  %s" % (e))
         return False
      except Exception as e:
         QtGui.QMessageBox.critical(self._mdiArea, "Error loading %s" % filename, "We're sorry, the file could not be loaded.\nAn unknown error occurred. Error message:\n  %s" % (e))
         return False
      
      if warnings != []:
         QtGui.QMessageBox.warning(self._mdiArea, "Warning", "File %s was successfully loaded, but there were warnings:\n" % os.path.basename(filename) + "\n".join(warnings))
         
      view = self._mdiArea.AddArmySubWindow(armylist)
      view.SetLastFilename(filename)
      QtGui.qApp.DataManager.AddRecentFile(filename)
      view.siRecentFilesChanged.emit()
      view.SetModified(False)
      return True
   
   
#===============================================================================
# PreviewArmyListCmd
#===============================================================================
class PreviewArmyListCmd(Command):
   def __init__(self, mdiArea):
      Command.__init__(self, name="PreviewArmyListCmd")
      self._mdiArea = mdiArea
      
   def Execute(self, alview):
      oldPrv = alview._attachedPreview
      if oldPrv: # try to find mdi subwindow for the old preview and switch to it
         for wnd in self._mdiArea.subWindowList():
            if wnd.widget() is oldPrv:
               self._mdiArea.setActiveSubWindow(wnd)
               return
         # if we're still here, the preview is still linked but has been closed already.
         # thus, just add a new one as if no old one was present.
      al = alview._model
      sub = self._mdiArea.AddPreviewSubWindow(al)
      alview._attachedPreview = sub