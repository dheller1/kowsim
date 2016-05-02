# -*- coding: utf-8 -*-

# kow/views.py
#===============================================================================
import os

from PySide import QtGui, QtCore

from widgets import UnitTable, ValidationWidget
from command import AddDetachmentCmd, DeleteUnitCmd, RenameDetachmentCmd, AddDefaultUnitCmd, DuplicateUnitCmd, SaveArmyListCmd, SetPrimaryDetachmentCmd, RenameArmyListCmd
from dialogs import AddDetachmentDialog
from kowsim.mvc.mvcbase import View
from mvc.models import ArmyListModel
import mvc.hints as ALH
from kowsim.kow.force import Detachment
import globals

#===============================================================================
# ArmyListView(QWidget)
#   Widget showing a complete kow.ArmyList instance and allowing to edit it.
#   Will contain one or more DetachmentViews which in turn contain a UnitTable
#   each.
#===============================================================================
class ArmyListView(QtGui.QWidget, View):
   siRecentFilesChanged = QtCore.Signal()
   siCurrentDetachmentChanged = QtCore.Signal()
   
   def __init__(self, ctrl, parent=None):
      QtGui.QWidget.__init__(self, parent)
      View.__init__(self, ctrl)
      self._attachedPreview = None
      self._lastIndex = 0
      self._lastFilename = None
      self.setWindowTitle((self.ctrl.model.Data().CustomName() + "*"))
      self._initChildren()
      self._initLayout()
      self._initConnections()
      self.detachmentsTw.setCurrentIndex(0)
      self.ctrl.Revalidate()
      
   def _initChildren(self):
      md = self.ctrl.model.Data()
      self.customNameLe = QtGui.QLineEdit(md.CustomName())
      
      # points limit spinbox
      self.pointsLimitSb = QtGui.QSpinBox()
      self.pointsLimitSb.setRange(1, 1000000)
      self.pointsLimitSb.setValue(md.PointsLimit())
      self.pointsLimitSb.setSingleStep(50)
      
      self.validationWdg = ValidationWidget(self.ctrl, parent=self)
      
      self.detachmentsTw = QtGui.QTabWidget(parent=self)
      self.detachmentsTw.addTab(QtGui.QWidget(), "+")
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
      self.generalGb.setLayout(genlay)
      
      self.detachmentsGb.setLayout(QtGui.QVBoxLayout())
      self.detachmentsGb.layout().addWidget(self.detachmentsTw)
            
      vallay = QtGui.QVBoxLayout()
      vallay.addWidget(self.validationWdg)
      self.valGb.setLayout(vallay)
      
      mainlay = QtGui.QGridLayout()
      mainlay.addWidget(self.generalGb, 0, 0)
      mainlay.addWidget(self.valGb, 0, 1)
      mainlay.addWidget(self.detachmentsGb, 1, 0, 1, 2)
      self.setLayout(mainlay)
   
   def _initConnections(self):
      self.detachmentsTw.currentChanged.connect(self.DetachmentTabChanged)
      self.customNameLe.editingFinished.connect(self._HandleArmyNameEdited)
   
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
   
   #============================================================================
   # Qt event handler overrides
   #============================================================================
   def closeEvent(self, e):
      if self.ctrl.model.modified:
         res = QtGui.QMessageBox.question(self, "Close army list", "You have unsaved changes in this army list.\nDo you want to save before closing?", 
                                          QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Yes)
         
         if res == QtGui.QMessageBox.Cancel:
            e.ignore()
            return
         elif res == QtGui.QMessageBox.Yes:
            cmd = SaveArmyListCmd(self._model, self) # TODO: If Save is actually SaveAs and the Dialog is aborted, abort the close event!
            cmd.Execute()                            # (e.g. check if document is still in modified status after the Save command)
      
      super(ArmyListView, self).closeEvent(e)
      
   def AddDetachmentView(self, detachment):
      dv = DetachmentView(detachment, self.ctrl)
      self.detachmentsTw.insertTab(self.detachmentsTw.count()-1, dv, detachment.CustomName())
      self.detachmentsTw.setCurrentIndex(self.detachmentsTw.count()-2) # switch to new tab
      dv.siNameChanged.connect(self.DetachmentNameChanged)
      dv.siModified.connect(self.SetModified)
      dv.siPrimaryToggled.connect(self.TogglePrimaryDetachment)
      
   def DetachmentNameChanged(self, name):
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
         
   def SetLastFilename(self, name):
      self._lastFilename = name
      self.UpdateTitle()
   
   def SetModified(self):
      self.UpdateTitle()

   def TogglePrimaryDetachment(self, makePrimary):
      sender = self.sender()
      det = sender._model
      cmd = SetPrimaryDetachmentCmd(det, self)
      cmd.Execute(makePrimary)
      
   # Update content after being notified about changes in the model.
   # A partial update might be sufficient if every hint in 'hints'
   # can be handled.
   def UpdateContent(self, hints=None):
      md = self.ctrl.model.Data()
      unknownHints = False
      
      print hints
      if hints:
         for hint in hints:
            if hint.IsType(ALH.ChangeNameHint):
               self.customNameLe.setText(md.CustomName())
            elif hint.IsType(ALH.AddDetachmentHint):
               self.AddDetachmentView(hint.which)
            else:
               unknownHints = True
      
      if hints is None or len(hints)==0 or unknownHints:
         self.UpdateTitle()
      
   def UpdateDetachment(self, index):
      # detachment index is always the tab index in self.detachmentsTw
      self.detachmentsTw.widget(index).UpdateContent()
      
   def UpdateTitle(self):
      title = self.ctrl.model.Data().CustomName()
      if self._lastFilename: title += " (%s)" % os.path.basename(self._lastFilename)
      if self.ctrl.model.modified: title += "*"
      self.setWindowTitle(title)
         

#===============================================================================
# DetachmentView(QWidget)
#   Widget showing a single kow.Detachment instance and allowing to edit it.
#   Usually used within an ArmyListView, which will show each of its DetachmentViews
#   in a TabWidget.
#===============================================================================
class DetachmentView(QtGui.QWidget, View):
   siModified = QtCore.Signal(bool)
   siNameChanged = QtCore.Signal(str)
   siPrimaryToggled = QtCore.Signal(bool)
   
   def __init__(self, model, ctrl, parent=None):
      QtGui.QWidget.__init__(self, parent)
      View.__init__(self, ctrl) # ctrl is an ArmyListCtrl
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
      self.isPrimaryDetachmentCb.stateChanged.connect(self.TogglePrimary)
      
   def AddUnit(self):
      cmd = AddDefaultUnitCmd(self.ctrl, self._model)
      cmd.Execute()
      
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
      cmd = RenameDetachmentCmd(self.ctrl.model, self._model, self)
      cmd.Execute(name=self.customNameLe.text())
      
   def SetModified(self, modified=True):
      self.siModified.emit(modified)
      
   def TogglePrimary(self):
      self.siPrimaryToggled.emit(self.isPrimaryDetachmentCb.isChecked())
            
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
class ArmyListOutputView(QtGui.QTextEdit, View):      
   def __init__(self, ctrl, parent=None):
      QtGui.QTextEdit.__init__(self, parent)
      View.__init__(self, ctrl)
      self.setReadOnly(True)
      self.UpdateContent()
      
   def _UnitTable(self, unit):
      specialText = ", ".join(unit.ListSpecialRules())
      if len(unit.ListChosenOptions())>0:
         optsText = ", ".join(["<b>%s</b>" % o.Name() for o in unit.ListChosenOptions()])
         specialText += ", " + optsText
      
      tableStyle = "{ border: #000000 1px solid; }"
      
      pre = "<table style='%s'>\n" % tableStyle
      post = "</table>\n\n"
      name = "%s (%s)" % (unit.CustomName(), unit.Profile().Name()) if len(unit.CustomName())>0 else unit.Profile().Name()
      headRow = "<tr><td colspan='7'><b>%s</b></td><td colspan='2' align='right'><b>%s</b></td></tr>\n" % (name, unit.UnitType().Name())
      labelsRow="""<tr><td width='120'>Unit Size</td>
                       <td width='40'>Sp</td>
                       <td width='40'>Me</td>
                       <td width='40'>Ra</td>
                       <td width='40'>De</td>
                       <td width='40'>At</td>
                       <td width='55'>Ne</td>
                       <td width='55'>Pts</td>
                       <td width='250'>Special</td></tr>\n"""
      profileRow="""<tr><td width='120'>%s</td>
                       <td width='40'>%d</td>
                       <td width='40'>%s</td>
                       <td width='40'>%s</td>
                       <td width='40'>%s</td>
                       <td width='40'>%s</td>
                       <td width='55'>%s</td>
                       <td width='55'>%d</td>
                       <td width='250'>%s</td></tr>\n""" % (unit.SizeType().Name(), unit.Sp(), unit.MeStr(), unit.RaStr(), unit.DeStr(), unit.AtStr(),
                                                            unit.NeStr(), unit.PointsCost(), specialText)
      return pre+headRow+labelsRow+profileRow+post
      
   def UpdateContent(self, hints=None):
      al = self.ctrl.model.Data()
      self.setWindowTitle("Preview: " + al.CustomName())
      
      header = """<html>\n
      <head>\n
         <title>%s (%dp)</title>\n
      </head>\n
      <body>\n""" % (al.CustomName(), al.PointsLimit())
      
      footer = """</body>\n
      </html>\n"""
      
      content  = "   <h1>%s (%dp)</h1>\n" % (al.CustomName(), al.PointsLimit())
      content += "   <h4>%d detachment%s</h4>\n" % (al.NumDetachments(), "s" if al.NumDetachments()>1 else "")
      
      for det in al.ListDetachments():
         content += "   <h2>%s (%s)</h2>\n" % (det.CustomName(), det.Choices().Name())
         content += "   <h4>%d units, %d points</h4>\n" % (det.NumUnits(), det.PointsTotal())
         content += "</p>\n".join([self._UnitTable(unit) for unit in det.ListUnits()])
               
      self.setHtml(header + content + footer)