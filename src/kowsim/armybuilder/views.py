# -*- coding: utf-8 -*-

# kow/views.py
#===============================================================================
import os

from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from widgets import UnitTable, ValidationWidget
from command import AddDetachmentCmd, DeleteUnitCmd, RenameDetachmentCmd, AddDefaultUnitCmd, DuplicateUnitCmd, SaveArmyListCmd, \
                    SetPrimaryDetachmentCmd, RenameArmyListCmd, RemoveDetachmentCmd, AddSpecificUnitCmd, SetModelSettingCmd
from dialogs import AddDetachmentDialog
from kowsim.mvc.mvcbase import View, TextEditView
import mvc.hints as ALH
from kowsim.kow.force import Detachment
import globals

class ArmyListView(View):
   """ Widget showing a complete kow.ArmyList instance and allowing to edit it.
   
   Will contain one or more DetachmentViews which in turn contain a UnitTable
   each.
   """
   siRecentFilesChanged = QtCore.Signal()
   siCurrentDetachmentChanged = QtCore.Signal()
   
   def __init__(self, ctrl, parent=None):
      View.__init__(self, ctrl, parent)
      self._attachedPreview = None
      self._lastIndex = 0
      self._lastFilename = None
      self.setWindowTitle((self.ctrl.model.Data().CustomName() + "*"))
      self._initChildren()
      self._initLayout()
      self._initConnections()
      self.detachmentsTw.setCurrentIndex(0)
      self.ctrl.Revalidate()
      
   def __repr__(self):
      return "ArmyListView(%s,%s)" % (self.ctrl.model.Data().CustomName(), self._lastFilename)
      
   def _initChildren(self):
      """ Initialize child widgets, particularly the detachments tabwidget. """
      md = self.ctrl.model.Data()
      self.customNameLe = QtGui.QLineEdit(md.CustomName())
      
      # points limit spinbox
      self.pointsLimitSb = QtGui.QSpinBox()
      self.pointsLimitSb.setRange(1, 1000000)
      self.pointsLimitSb.setValue(md.PointsLimit())
      self.pointsLimitSb.setSingleStep(50)
      
      self.validationWdg = ValidationWidget(self.ctrl, parent=self)
      
      self.detachmentsTw = QtGui.QTabWidget(parent=self)
      self.detachmentsTw.setTabsClosable(True)
      self.detachmentsTw.addTab(QtGui.QWidget(), "+")
      
      self.useCokValidationCb = QtGui.QCheckBox("Use Clash of Kings validation rules")
      
      # remove close button for '+'-pseudo tab
      self.detachmentsTw.tabBar().setTabButton(0, QtGui.QTabBar.RightSide, None)
      
      for det in md.ListDetachments():
         self.AddDetachmentView(det)
      
      self.generalGb = QtGui.QGroupBox("General")
      self.detachmentsGb = QtGui.QGroupBox("Detachments")
      self.valGb = QtGui.QGroupBox("Validation")
      
   def _initLayout(self):
      genlay = QtGui.QGridLayout()
      row = 0
      genlay.addWidget(QtGui.QLabel("Army name:"), row, 0)
      genlay.addWidget(self.customNameLe, row, 1)
      row += 1
      genlay.addWidget(QtGui.QLabel("Points limit:"), row, 0)
      genlay.addWidget(self.pointsLimitSb, row, 1)
      row += 1
      genlay.addWidget(QtGui.QLabel("Options:"), row, 0)
      genlay.addWidget(self.useCokValidationCb, row, 1)
      row += 1
      genlay.addWidget(QtGui.QLabel(), row, 0)
      genlay.setRowStretch(row, 10)
      self.generalGb.setLayout(genlay)
      
      self.detachmentsGb.setLayout(QtGui.QVBoxLayout())
      self.detachmentsGb.layout().addWidget(self.detachmentsTw)
            
      vallay = QtGui.QVBoxLayout()
      vallay.addWidget(self.validationWdg)
      self.valGb.setLayout(vallay)
      
      vSplitter = QtGui.QSplitter(Qt.Vertical, self)
      vSplitter.setChildrenCollapsible(False)
      vSplitter.setHandleWidth(10)
      vSplitter.setStyle(QtGui.QStyleFactory.create('Plastique'))
      hSplitterTop = QtGui.QSplitter(Qt.Horizontal, self)
      hSplitterTop.setChildrenCollapsible(False)
      hSplitterTop.setHandleWidth(10)
      hSplitterTop.setStyle(QtGui.QStyleFactory.create('Plastique'))
      hSplitterTop.addWidget(self.generalGb)
      hSplitterTop.addWidget(self.valGb)
      vSplitter.addWidget(hSplitterTop)
      vSplitter.addWidget(self.detachmentsGb)
      vSplitter.setSizes([0,999])
      
      mainLay = QtGui.QVBoxLayout()
      mainLay.addWidget(vSplitter)
      self.setLayout(mainLay)
      
   def _initConnections(self):
      self.detachmentsTw.currentChanged.connect(self.DetachmentTabChanged)
      self.customNameLe.editingFinished.connect(self._HandleArmyNameEdited)
      self.detachmentsTw.tabCloseRequested.connect(self.RemoveDetachmentRequested)
      self.useCokValidationCb.toggled[bool].connect(self.ToggleCokValidation)
   
   #============================================================================
   # "SLOTS" ('private' event handlers)
   #============================================================================
   def _HandleArmyNameEdited(self):
      newName = self.customNameLe.text()
      if len(newName.strip())==0: # don't accept, revert
         self.customNameLe.setText(self.ctrl.model.Data().CustomName())
      elif newName != self.ctrl.model.Data().CustomName():
         cmd = RenameArmyListCmd(self.ctrl.model, newName)
         self.ctrl.AddAndExecute(cmd)
   
   def closeEvent(self, e):
      """ Allows to save changes to the document before closing. """
      if self.ctrl.model.modified:
         res = QtGui.QMessageBox.question(self, "Close army list", "You have unsaved changes in this army list.\nDo you want to save before closing?", 
                                          QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Yes)         
         if res == QtGui.QMessageBox.Cancel:
            e.ignore()
            return
         elif res == QtGui.QMessageBox.Yes:
            cmd = SaveArmyListCmd(self.ctrl.model, self)
            self.ctrl.AddAndExecute(cmd)
            if self.ctrl.model.modified: # if it is still modified, saving was not successful (could be an aborted filename dialog)
               e.ignore()                # don't close the window in this case
               return
      
      super(ArmyListView, self).closeEvent(e)

   def AddDetachmentView(self, detachment):
      """ Add a new detachment view to the ArmyListView.
      
      :param detachment: Detachment object to be added.
      :type detachment: kow.Detachment """
      dv = DetachmentView(detachment, self.ctrl)
      self.detachmentsTw.insertTab(self.detachmentsTw.count()-1, dv, detachment.CustomName())
      self.detachmentsTw.setCurrentIndex(self.detachmentsTw.count()-2) # switch to new tab
      dv.siNameChanged.connect(self.DetachmentNameChanged)
      dv.siModified.connect(self.SetModified)
      
   def DetachmentNameChanged(self, name):
      """ Update a detachment's name in corresponding the tab header.
      
      Qt's sender() method is used to determine which specific detachment was changed.
      """
      sender = self.sender()
      index = self.detachmentsTw.indexOf(sender)
      self.detachmentsTw.setTabText(index, name)
   
   def DetachmentTabChanged(self):
      # determine if the '+' was clicked
      tw = self.detachmentsTw
      if tw.currentIndex() == tw.count()-1:
         tw.setCurrentIndex(self._lastIndex)
         
         dlg = AddDetachmentDialog()
         if QtGui.QDialog.Accepted == dlg.exec_():
            detachment = Detachment(dlg.Force(), isPrimary=dlg.MakePrimary())
            cmd = AddDetachmentCmd(self.ctrl.model, detachment)
            self.ctrl.AddAndExecute(cmd)

      else:
         self._lastIndex = tw.currentIndex()
         self.siCurrentDetachmentChanged.emit()
   
   def RemoveDetachmentRequested(self, index):
      if len(self.ctrl.model.data.ListDetachments())<=1:
         QtGui.QMessageBox.critical(self, "Error", "Unable to remove detachment:\nYou can not remove the last detachment in the army list.", QtGui.QMessageBox.Ok)
         return
      
      res = QtGui.QMessageBox.warning(self, "Remove detachment", "Do you really want to remove this detachment?", 
                                          QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Yes)
      if res == QtGui.QMessageBox.Yes:
         if(index>=1): # set index to not end up on the '+' tab accidentally. 
            self.detachmentsTw.setCurrentIndex(index-1)
         else:
            self.detachmentsTw.setCurrentIndex(0)
         cmd = RemoveDetachmentCmd(self.ctrl.model, self.ctrl.model.data.ListDetachments()[index])
         self.ctrl.AddAndExecute(cmd)
         self.detachmentsTw.removeTab(index) # FIXME: This might be better situated within the command(?)
         print self.ctrl._views
         self.ctrl.DetachView(self.detachmentsTw.widget(index))
         
   def SetLastFilename(self, name):
      self._lastFilename = name
      self.UpdateTitle()
   
   def SetModified(self):
      self.UpdateTitle()
      
   def ToggleCokValidation(self, checked):
      cmd = SetModelSettingCmd(self.ctrl.model, "UseCokValidation", checked, (ALH.RevalidateHint(), ))
      self.ctrl.AddAndExecute(cmd)
   
   def UpdateContent(self, hints=None):
      """ Update content after being notified about changes in the model.
      
      A partial update might be sufficient if every hint in 'hints'
      can be handled.
      
      :param hints: Update hints used to determine if a full update is needed.
      :type hints: list of ArmyListHint objects
      """
      md = self.ctrl.model.Data()
      
      self.UpdateTitle()
      for hint in hints:
         if hint.IsType(ALH.ChangeNameHint) and hint.which is self.ctrl.model:
            self.customNameLe.setText(md.CustomName())
         elif hint.IsType(ALH.AddDetachmentHint):
            self.AddDetachmentView(hint.which)
         else:
            continue # ignore hint
      
   def UpdateDetachment(self, index):
      """ Triggers UpdateContent() in the detachment view given by *index*.
      
      :param index: Index of detachment/detachment view to be updated.
      :type index: int 
      """
      # detachment index is always the tab index in self.detachmentsTw
      self.detachmentsTw.widget(index).UpdateContent()
      
   def UpdateTitle(self):
      title = self.ctrl.model.Data().CustomName()
      if self._lastFilename: title += " (%s)" % os.path.basename(self._lastFilename)
      if self.ctrl.model.modified: title += "*"
      self.setWindowTitle(title)
         

#===============================================================================
# DetachmentView(QWidget)
#===============================================================================
class DetachmentView(View):
   """ Widget showing a single kow.Detachment instance and allowing to edit it.
   
   Usually used within an ArmyListView, which will show each of its DetachmentViews
   in a TabWidget.
   """
   siModified = QtCore.Signal(bool)
   siNameChanged = QtCore.Signal(str)
   
   def __init__(self, model, ctrl, parent=None):
      View.__init__(self, ctrl, parent) # ctrl is an ArmyListCtrl
      self._model = model # Detachment
      self._initChildren()
      self._initLayout()
      self._initConnections()
      self.UpdateContent()
      
   def _initChildren(self):
      self.customNameLe = QtGui.QLineEdit(self._model.CustomName())
      
      self.isPrimaryDetachmentCb = QtGui.QCheckBox()
      if self._model.IsPrimary(): self.isPrimaryDetachmentCb.setChecked(True)
      
      self.unitTable = UnitTable(self._model, self.ctrl)
      self.pointsLbl = QtGui.QLabel("<b>0</b>")
            
      self.addUnitPb = QtGui.QPushButton(QtGui.QIcon(os.path.join(globals.BASEDIR, "data","icons","plus.png")), "&Add")
      self.duplicateUnitPb = QtGui.QPushButton(QtGui.QIcon(os.path.join(globals.BASEDIR, "data","icons","copy.png")), "Dupli&cate")
      self.duplicateUnitPb.setEnabled(False)
      self.deleteUnitPb = QtGui.QPushButton(QtGui.QIcon(os.path.join(globals.BASEDIR, "data","icons","delete.png")), "&Delete")
      self.deleteUnitPb.setEnabled(False)
      
      #=========================================================================
      # group boxes
      #=========================================================================
      self.generalGb = QtGui.QGroupBox("General")
      self.detailsGb = QtGui.QGroupBox("Details")
      self.detailsGb.setMinimumWidth(400)
      self.unitGb = QtGui.QGroupBox("Units")
      
   def _initLayout(self):
      #self.setWindowTitle(("*" + name))
      
      # general gb
      genlay = QtGui.QGridLayout()
      row = 0
      genlay.addWidget(QtGui.QLabel("Detachment name:"), row, 0)
      genlay.addWidget(self.customNameLe, row, 1)
      row += 1
      genlay.addWidget(QtGui.QLabel("Primary detachment:"), row, 0)
      genlay.addWidget(self.isPrimaryDetachmentCb, row, 1)
      row += 1
      self.generalGb.setLayout(genlay)
      
      # units gb
      self.unitGb.setLayout(QtGui.QVBoxLayout())
      unitButtonsLay = QtGui.QHBoxLayout()
      unitButtonsLay.addWidget(self.addUnitPb)
      unitButtonsLay.addWidget(self.duplicateUnitPb)
      unitButtonsLay.addWidget(self.deleteUnitPb)
      #unitButtonsLay.addWidget(self.optionsPb)
      unitButtonsLay.addStretch(1)
      self.unitGb.layout().addLayout(unitButtonsLay)
      self.unitGb.layout().addWidget(self.unitTable)
      
      # details gb
      detlay = QtGui.QGridLayout()
      self.detailsGb.setLayout(detlay)
      row = 0
      detlay.addWidget(QtGui.QLabel("Force:"), row, 0)
      detlay.addWidget(QtGui.QLabel("<b>%s</b>" % self._model.Choices().Name()), row, 1)
      row += 1
      detlay.addWidget(QtGui.QLabel("Alignment:"), row, 0)
      detlay.addWidget(QtGui.QLabel("<b>%s</b>" % self._model.Choices().AlignmentName()), row, 1)
      row += 1
      detlay.addWidget(QtGui.QLabel("Total points:"), row, 0)
      detlay.addWidget(self.pointsLbl)
      row += 1
      
      mainlay = QtGui.QGridLayout()
      mainlay.addWidget(self.generalGb, 0, 0)
      mainlay.addWidget(self.detailsGb, 0, 1)
      mainlay.addWidget(self.unitGb, 1, 0, 1, 2)
      self.generalGb.setFixedHeight(150)
      self.detailsGb.setFixedHeight(150)
      mainlay.setRowStretch(0, 0)
      mainlay.setRowStretch(1, 1)
      mainlay.setRowMinimumHeight(1, 400)
      self.setLayout(mainlay)
   
   def _initConnections(self):
      self.customNameLe.editingFinished.connect(self.RenameDetachment)
      self.addUnitPb.clicked.connect(self.AddUnit)
      self.deleteUnitPb.clicked.connect(self.DeleteUnit)
      self.duplicateUnitPb.clicked.connect(self.DuplicateUnit)
      self.unitTable.itemSelectionChanged.connect(self.UnitSelectionChanged)
      self.unitTable.siModified.connect(self.SetModified)
      self.unitTable.siAddUnitRequested.connect(self.AddUnitDragAndDrop)
      self.isPrimaryDetachmentCb.clicked.connect(self.TogglePrimary)
      
   def AddUnit(self):
      cmd = AddDefaultUnitCmd(self.ctrl.model, self._model)
      self.ctrl.AddAndExecute(cmd)
      
   def AddUnitDragAndDrop(self, unitname):
      cmd = AddSpecificUnitCmd(self.ctrl.model, self._model, unitname)
      self.ctrl.AddAndExecute(cmd)
      
   def DeleteUnit(self):
      delUnits = self.unitTable.SelectedUnits()
      if len(delUnits)==1:
         confirm="This will delete the current unit.<br />Are you sure?"
      elif len(delUnits)>1:
         confirm="This will delete %d units.<br />Are you sure?" % len(delUnits)
      if QtGui.QMessageBox.Yes != QtGui.QMessageBox.warning(self, "Delete unit(s)", confirm, QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel):
         return
      
      cmd = DeleteUnitCmd(self.ctrl.model, self._model, delUnits)
      self.ctrl.AddAndExecute(cmd)
      self.unitTable.clearSelection()
      
   def DuplicateUnit(self):
      cmd = DuplicateUnitCmd(self.ctrl.model, self._model, self.unitTable.SelectedUnits())
      self.ctrl.AddAndExecute(cmd)
   
   def RenameDetachment(self):
      newName = self.customNameLe.text()
      if newName != self._model.CustomName():
         cmd = RenameDetachmentCmd(self.ctrl.model, self._model, newName)
         self.ctrl.AddAndExecute(cmd)
      
   def SetModified(self, modified=True):
      self.siModified.emit(modified)
      
   def TogglePrimary(self):
      det = self._model
      makePrimary = self.isPrimaryDetachmentCb.isChecked()
      cmd = SetPrimaryDetachmentCmd(self.ctrl.model, det, makePrimary)
      self.ctrl.AddAndExecute(cmd)
            
   def UnitSelectionChanged(self):
      rows = self.unitTable.SelectedRows()
      
      if len(rows)>0:
         self.duplicateUnitPb.setEnabled(True)
         self.deleteUnitPb.setEnabled(True)
      else:
         self.duplicateUnitPb.setEnabled(False)
         self.deleteUnitPb.setEnabled(False)
         
   def UpdateContent(self, hints=None):
      self.isPrimaryDetachmentCb.setChecked(self._model.IsPrimary())
      self._UpdatePoints()
      
      # check if unit table must be updated
      if hints is None or len(hints) == 0:
         updateUnitTable = True # no hints ^= global update
      else:
         updateUnitTable = False
         for hint in hints:
            if (hint.IsType(ALH.ModifyDetachmentHint) and hint.which is self._model) \
                  or  (hint.IsType(ALH.ModifyUnitHint) and hint.which in self._model.ListUnits()):
               updateUnitTable = True
               break
      
      if updateUnitTable:
         if self.unitTable.rowCount() > self._model.NumUnits():
            self.unitTable.setRowCount(self._model.NumUnits())
         for i in range(self._model.NumUnits()):
            self._UpdateUnit(i)
      
   # "private" functions
   def _UpdatePoints(self):
      pts = self._model.PointsTotal()
      self.pointsLbl.setText("<b>%d</b>" % pts)
   
   def _UpdateUnit(self, index):
      self.unitTable.SetRow(index, self._model.ListUnits()[index])
      
      
#===============================================================================
# ArmyListOutputView
#===============================================================================
class ArmyListOutputView(TextEditView):
   """ View for an **ArmyListModel** acting as a read-only HTML/PDF style export/print preview. """
   def __init__(self, ctrl, parent=None):
      super(ArmyListOutputView, self).__init__(ctrl, parent)
      self.setReadOnly(True)
      self.UpdateContent()
      
   def closeEvent(self, e):
      """ Close view and detach from controller. """
      self.ctrl.DetachView(self)
      QtGui.QWidget.closeEvent(self, e)
            
   def UpdateContent(self, hints=None):
      """ Update view content upon model changes. """
      self.setHtml(self.ctrl.model.GenerateHtml())
      self.setWindowTitle("Preview: " + self.ctrl.model.Data().CustomName())
