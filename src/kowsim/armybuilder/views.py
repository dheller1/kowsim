# -*- coding: utf-8 -*-

# kow/views.py
#===============================================================================
import os

from PySide import QtGui, QtCore
from widgets import ValidationWidget
from kowsim.armybuilder.dialogs import AddDetachmentDialog
from command import AddDetachmentCmd
from kowsim.armybuilder.command import RenameDetachmentCmd, AddDefaultUnitCmd
from kowsim.armybuilder.widgets import UnitTable
from pip.models import index
#from PySide.QtCore import Qt

#from ..kow.force import ArmyList 

#===============================================================================
# ArmyListView(QWidget)
#   Widget showing a complete kow.ArmyList instance and allowing to edit it.
#===============================================================================
class ArmyListView(QtGui.QWidget):
   def __init__(self, model, parent=None):
      QtGui.QWidget.__init__(self, parent)
      self._model = model
      self._lastIndex = 0
      self._initChildren()
      self._initLayout()
      self._initConnections()
      
   def _initChildren(self):
      self.customNameLe = QtGui.QLineEdit(self._model.CustomName())
      
      # points limit spinbox
      self.pointsLimitSb = QtGui.QSpinBox()
      self.pointsLimitSb.setRange(1, 1000000)
      self.pointsLimitSb.setValue(self._model.PointsLimit())
      self.pointsLimitSb.setSingleStep(50)
      
      self.validationWdg = ValidationWidget(parent=self)
      
      self.detachmentsTw = QtGui.QTabWidget(parent=self)
      #self.addDetachmentPb = QtGui.QPushButton(QtGui.QIcon(os.path.join("..", "data","icons","plus.png")), "&Add detachment")
      for det in self._model.ListDetachments():
         dv = DetachmentView(det)
         dv.siNameChanged.connect(self.DetachmentNameChanged)
         self.detachmentsTw.addTab(dv, det.CustomName())
      self.detachmentsTw.addTab(QtGui.QWidget(), "+")
      
      self.generalGb = QtGui.QGroupBox("General")
      self.detachmentsGb = QtGui.QGroupBox("Detachments")
      self.valGb = QtGui.QGroupBox("Validation")
      
   def _initLayout(self):
      self.setWindowTitle(("*" + self._model.CustomName()))
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
      
      #detButtonsLay = QtGui.QHBoxLayout()
      #detButtonsLay.addWidget(self.addDetachmentPb)
      #detButtonsLay.addStretch(1)
      #self.detachmentsGb.layout().addLayout(detButtonsLay)
      
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
      
   def AddDetachmentView(self, detachment):
      dv = DetachmentView(detachment)
      self.detachmentsTw.insertTab(self.detachmentsTw.count()-1, dv, detachment.CustomName())
      self.detachmentsTw.setCurrentIndex(self.detachmentsTw.count()-2) # switch to new tab
      
   def DetachmentNameChanged(self, name):
      sender = self.sender()
      index = self.detachmentsTw.indexOf(sender)
      self.detachmentsTw.setTabText(index, name)
   
   def DetachmentTabChanged(self):
      # determine if the '+' was clicked
      tw = self.detachmentsTw
      if tw.currentIndex() == tw.count()-1:
         tw.setCurrentIndex(self._lastIndex)
         cmd = AddDetachmentCmd(self._model, self)
         cmd.Execute()
      else:
         self._lastIndex = tw.currentIndex()
         

#===============================================================================
# DetachmentView(QWidget)
#   Widget showing a single kow.Detachment instance and allowing to edit it. 
#===============================================================================
class DetachmentView(QtGui.QWidget):
   siNameChanged = QtCore.Signal(str)
   
   def __init__(self, model, parent=None):
      QtGui.QWidget.__init__(self, parent)
      self._model = model
      self._initChildren()
      self._initLayout()
      self._initConnections()
      print "Initializing view for detachment %s." % self._model
      
   def _initChildren(self):
      self.customNameLe = QtGui.QLineEdit(self._model.CustomName())
      
      self.isPrimaryDetachmentCb = QtGui.QCheckBox()
      if self._model.IsPrimary(): self.isPrimaryDetachmentCb.setChecked(True)
      
      self.unitTable = UnitTable(self._model)
            
      self.addUnitPb = QtGui.QPushButton(QtGui.QIcon(os.path.join("..", "data","icons","plus.png")), "&Add")
      self.duplicateUnitPb = QtGui.QPushButton(QtGui.QIcon(os.path.join("..", "data","icons","copy.png")), "Dupli&cate")
      self.duplicateUnitPb.setEnabled(False)
      self.deleteUnitPb = QtGui.QPushButton(QtGui.QIcon(os.path.join("..", "data","icons","delete.png")), "&Delete")
      self.deleteUnitPb.setEnabled(False)
      self.optionsPb = QtGui.QPushButton(QtGui.QIcon(os.path.join("..", "data","icons","options.png")), "&Options")
      self.optionsPb.setEnabled(False)
      
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
      unitButtonsLay.addWidget(self.optionsPb)
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
      detlay.addWidget(QtGui.QLabel("<b>0</b>"))
      row += 1
      
      mainlay = QtGui.QGridLayout()
      mainlay.addWidget(self.generalGb, 0, 0)
      mainlay.addWidget(self.detailsGb, 0, 1)
      mainlay.addWidget(self.unitGb, 1, 0, 1, 2)
      self.setLayout(mainlay)
   
   def _initConnections(self):
      self.customNameLe.editingFinished.connect(self.RenameDetachment)
      self.addUnitPb.clicked.connect(self.AddUnit)
   
   def AddUnit(self):
      cmd = AddDefaultUnitCmd(self._model, self)
      cmd.Execute()
   
   def RenameDetachment(self):
      cmd = RenameDetachmentCmd(self._model, self)
      cmd.Execute(name=self.customNameLe.text())
   
   def UpdateUnit(self, index):
      self.unitTable.SetRow(index, self._model.ListUnits()[index])