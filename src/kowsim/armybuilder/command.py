# -*- coding: utf-8 -*-

# armybuilder/command.py
#===============================================================================
import os
import kowsim.kow.sizetype
from PySide import QtGui
from PySide.QtCore import QSettings
from kowsim.command.command import Command, ReversibleCommandMixin
from kowsim.kow.unit import UnitInstance
from kowsim.kow.fileio import ArmyListWriter, ArmyListReader
from mvc.models import ArmyListModel
import mvc.hints as ALH
from kowsim.armybuilder.mvc.hints import ModifyUnitHint, ToggleModifiedHint

#===============================================================================
# AddDetachmentCmd
#===============================================================================
class AddDetachmentCmd(Command, ReversibleCommandMixin):
   """ This command adds a detachment to an army list.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, alModel, detachment):
      Command.__init__(self, name="AddDetachmentCmd")
      ReversibleCommandMixin.__init__(self)
      self._model = alModel
      self._detachment = detachment
      self.hints = (ALH.AddDetachmentHint(self._detachment), )
      
   def Execute(self):
      self._model.data.AddDetachment(self._detachment)
      self._model.Touch()
         
   def Undo(self):
      self._model.data.RemoveDetachment(self._detachment)
      self._model.Touch()


#===============================================================================
# RenameDetachmentCmd
#===============================================================================
class RenameDetachmentCmd(Command, ReversibleCommandMixin):
   """ This command allows to change the name of a detachment.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, alModel, detachment, newName):
      Command.__init__(self, name="RenameDetachmentCmd")
      ReversibleCommandMixin.__init__(self)
      self.alModel = alModel
      self.detachment = detachment
      self.newName = newName
      self.hints = (ALH.ChangeNameHint(self.detachment), )
      
   def Execute(self):
      self.detachment.SetCustomName(self.newName)
      self.alModel.Touch()

         
#===============================================================================
# RenameArmyListCmd
#===============================================================================
class RenameArmyListCmd(Command, ReversibleCommandMixin):
   """ This command allows to change the army list name.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, model, newName):
      Command.__init__(self, name="RenameArmyListCmd")
      ReversibleCommandMixin.__init__(self)
      self._newName = newName
      self._model = model
      self.hints = (ALH.ChangeNameHint(self._model), )

   def Execute(self):
      self._previousName = self._model.data.CustomName()
      self._model.data.SetCustomName(self._newName)
      self._model.Touch()
   
   def Undo(self):
      self._model.data.SetCustomName(self._previousName)
      self._model.Touch()
         
         
#===============================================================================
# AddDefaultUnitCmd
#===============================================================================
class AddDefaultUnitCmd(Command, ReversibleCommandMixin):
   """ This command is invoked when a default unit is added to a detachment.

   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, alModel, detachment):
      Command.__init__(self, name="AddDefaultUnitCmd")
      ReversibleCommandMixin.__init__(self)
      self._alModel = alModel
      self._detachment = detachment
      self.hints = (ALH.ModifyDetachmentHint(detachment), )
   
   def Execute(self):
      profile = self._detachment.Choices().ListUnits()[0]
      self._detachment.AddUnit(UnitInstance(profile, self._detachment))
      self._alModel.Touch()


#===============================================================================
# AddSpecificUnitCmd
#===============================================================================
class AddSpecificUnitCmd(Command, ReversibleCommandMixin):
   """ This command is invoked when a specific unit is added to a detachment.

   Currently, it is only invoked by double-clicking on a unit in the unit browser.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, alModel, detachment, unitname):
      Command.__init__(self, name="AddSpecificUnitCmd")
      ReversibleCommandMixin.__init__(self)
      self._alModel = alModel
      self._unitname = unitname
      self._detachment = detachment
      self.hints = (ALH.ModifyDetachmentHint(detachment), )
   
   def Execute(self):
      profile = self._detachment.Choices().GroupByName(self._unitname).Default()
      self._detachment.AddUnit(UnitInstance(profile, self._detachment))
      self._alModel.Touch()
      
      
#===============================================================================
# ChangeUnitCmd
#===============================================================================
class ChangeUnitCmd(Command, ReversibleCommandMixin):
   """ This command is invoked when a unit is changed by the selection combo box.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, model, detachment, unitIdx, newUnitName):
      Command.__init__(self, name="ChangeUnitCmd")
      ReversibleCommandMixin.__init__(self)
      self._model = model
      self._detachment = detachment
      self._unitIdx = unitIdx
      self._newUnitName = newUnitName
      self.hints = (ALH.ModifyDetachmentHint(self._detachment), )
   
   def Execute(self):
      newProfile = self._detachment.Choices().GroupByName(self._newUnitName).ListOptions()[0]
      newUnit = newProfile.CreateInstance(self._detachment)
      
      self._oldUnit = self._detachment.ListUnits()[self._unitIdx]
      self._detachment.ReplaceUnit(self._unitIdx, newUnit)
      self._model.Touch()
      
   def Undo(self):
      self._detachment.ReplaceUnit(self._unitIdx, self._oldUnit)
      self._model.Touch()
      

#===============================================================================
# ChangeUnitSizeCmd
#===============================================================================
class ChangeUnitSizeCmd(Command, ReversibleCommandMixin):
   """ This command is invoked when a units' size is changed, e.g. from Regiment to Horde.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, alModel, unit, newSize):
      Command.__init__(self, name="ChangeUnitSizeCmd")
      ReversibleCommandMixin.__init__(self)
      
      self._alModel = alModel
      self._unit = unit
      self._newSize = newSize
      self.hints = (ALH.ModifyUnitHint(unit), )
   
   def Execute(self):
      sizeType = kowsim.kow.sizetype.Find(self._newSize).Name()
      unitname = self._unit.Profile().Name()
      newProfile = self._unit.Detachment().Choices().GroupByName(unitname).ProfileForSize(sizeType)
      self._unit.SetProfile(newProfile)
      self._alModel.Touch()
            

#===============================================================================
# ChangeUnitItemCmd
#===============================================================================
class ChangeUnitItemCmd(Command, ReversibleCommandMixin):
   """ This command is invoked when a units' magic artefact is changed.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, unit, item):
      Command.__init__(self, name="ChangeUnitItemCmd")
      ReversibleCommandMixin.__init__(self)
      self._unit = unit
      self._item = item
      self.hints = (ALH.ModifyUnitHint(self._unit), )
   
   def Execute(self):
      self._oldItem = self._unit.Item()
      self._unit.SetItem(self._item)
      
   def Undo(self):
      self._unit.SetItem(self._oldItem)
      
      
#===============================================================================
# SetPrimaryDetachmentCmd
#===============================================================================
class SetPrimaryDetachmentCmd(Command, ReversibleCommandMixin):
   def __init__(self, alModel, detachment, makePrimary):
      Command.__init__(self, name="SetPrimaryDetachmentCmd")
      ReversibleCommandMixin.__init__(self)
      self.alModel = alModel
      self.detachment = detachment
      self.makePrimary = makePrimary
      self.hints = (ALH.ChangePrimaryDetachmentHint(), )
   
   def Execute(self):
      for det in self.alModel.data.ListDetachments():
         if det is self.detachment:
            det._isPrimary = self.makePrimary
         else:
            det._isPrimary = False
      self.alModel.Touch()
      
      
#===============================================================================
# SetUnitOptionsCmd
#===============================================================================
class SetUnitOptionsCmd(Command, ReversibleCommandMixin):
   """ This command modifies the chosen options of a unit, it is triggered by the unit table.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, alModel, unit, options):
      Command.__init__(self, name="SetUnitOptionsCmd")
      ReversibleCommandMixin.__init__(self)
      self._alModel = alModel
      self._unit = unit
      self._options = options
      
      self.hints = (ModifyUnitHint(self._unit), )
   
   def Execute(self):
      self._unit.ClearChosenOptions()
      for opt in self._options:
         self._unit.ChooseOption(opt)
      self._alModel.Touch()


#===============================================================================
# DeleteUnitCmd
#===============================================================================
class DeleteUnitCmd(Command, ReversibleCommandMixin):
   """ This command allows to delete one or several units in a detachment.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, model, detachment, units):
      Command.__init__(self, name="DeleteUnitCmd")
      ReversibleCommandMixin.__init__(self)
      self._model = model
      self._detachment = detachment
      self._delUnits = units
      self.hints = (ALH.ModifyDetachmentHint(self._detachment), )
   
   def Execute(self):
      if len(self._delUnits)==0: return
      for unit in self._delUnits:
         self._detachment.RemoveUnit(unit)
      self._model.Touch()
      
   def Undo(self):
      if len(self._delUnits)==0: return
      for unit in self._delUnits:
         self._detachment.AddUnit(unit)
      self._model.Touch()
      

#===============================================================================
# DuplicateUnitCmd
#===============================================================================
class DuplicateUnitCmd(Command, ReversibleCommandMixin):
   """ This command allows to duplicate one or several units in a detachment.
   
   This is a new-style command, changing data directly upon the model and providing
   any update-hints for views in its 'hints' member variable. It can also be used
   in the controller's command/undo history.
   """
   def __init__(self, model, detachment, units):
      Command.__init__(self, name="DuplicateUnitCmd")
      ReversibleCommandMixin.__init__(self)
      self._model = model
      self._detachment = detachment
      self._dupUnits = units
   
   def Execute(self):
      if len(self._dupUnits) == 0: return
      self._newUnits = [] 
      for unit in self._dupUnits:
         newUnit = unit.Profile().CreateInstance(self._detachment)
         for o in unit.ListChosenOptions():
            newUnit.ChooseOption(o)
         self._detachment.AddUnit(newUnit)
         self._newUnits.append(newUnit)
         
      self.hints = (ALH.ModifyUnitHint(unit) for unit in self._newUnits)
      self._model.Touch()
      
   def Undo(self):
      if len(self._newUnits) == 0: return
      [self._detachment.RemoveUnit(u) for u in self._newUnits]
      self._model.Touch()
      

#===============================================================================
# SaveArmyListCmd
#===============================================================================
class SaveArmyListCmd(Command):
   def __init__(self, alModel, alView, saveAs=False):
      Command.__init__(self, name="SaveArmyListCmd")
      self.saveAs = saveAs
      self.alModel = alModel
      self.alView = alView
   
   def Execute(self):
      defaultName = self.alView._lastFilename if self.alView._lastFilename else "%s.lst" % self.alModel.data.CustomName()
      if (not self.alView._lastFilename) or self.saveAs:
         settings = QSettings("NoCompany", "KowArmyBuilder")
         preferredFolder = settings.value("preferred_folder")
         if preferredFolder is None: preferredFolder = ".."
         
         filename, _ = QtGui.QFileDialog.getSaveFileName(self.alView, "Save army list as", "%s" % (os.path.join(preferredFolder, defaultName)),
                                                      "Army lists (*.lst);;All files (*.*)")
         if filename == "": return
         else: self.alView._lastFilename = filename
         QtGui.qApp.DataManager.AddRecentFile(filename)
         settings.setValue("preferred_folder", os.path.dirname(filename))
         self.alView.siRecentFilesChanged.emit()
      else:
         filename = self.alView._lastFilename
      
      try:
         alw = ArmyListWriter(self.alModel.data)
         alw.SaveToFile(filename)
      except IOError as e:
         QtGui.QMessageBox.critical(self.alView, "Error while saving", "An error occurred while saving the army list:\n  %s" % e)
      else:
         self.alModel.modified = False
         self.hints = (ToggleModifiedHint(), )
      

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
         filename, _ = QtGui.QFileDialog.getOpenFileName(self._mdiArea, "Open army list", preferredFolder, "Army lists (*.lst);;All files (*.*)")
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
         
      view = self._mdiArea.AddArmySubWindow(ArmyListModel(armylist))
      view.SetLastFilename(filename)
      QtGui.qApp.DataManager.AddRecentFile(filename)
      view.siRecentFilesChanged.emit()
      return view
   
   
#===============================================================================
# PreviewArmyListCmd
#===============================================================================
class PreviewArmyListCmd(Command):
   def __init__(self, alctrl, mdiArea):
      Command.__init__(self, name="PreviewArmyListCmd")
      self._ctrl = alctrl
      self._mdiArea = mdiArea
      
   def Execute(self):
      oldPrv = self._ctrl.attachedPreview
      if oldPrv: # try to find mdi subwindow for the old preview and switch to it
         for wnd in self._mdiArea.subWindowList():
            if wnd.widget() is oldPrv:
               self._mdiArea.setActiveSubWindow(wnd)
               return
         # if we're still here, the preview is still linked but has been closed already.
         # thus, just add a new one as if no old one was present.
      self._mdiArea.AddPreviewSubWindow(self._ctrl)
      