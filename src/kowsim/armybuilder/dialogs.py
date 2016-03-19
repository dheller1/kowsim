# -*- coding: utf-8 -*-

# kow/dialogs.py
#===============================================================================
#import os

from PySide import QtGui#, QtCore
from PySide.QtCore import Qt

#===============================================================================
# NewArmyListDialog
#===============================================================================
class NewArmyListDialog(QtGui.QDialog):
   def __init__(self):
      QtGui.QDialog.__init__(self)
      self._initChildren()
      self._initLayout()
      self._initConnections()
   
   def _initChildren(self):
      #self.primaryForceCb = QtGui.QComboBox()
      #for fc in QtGui.qApp.DataManager.ListForceChoices():
      #   self.primaryForceCb.addItem(fc.Name())
      self.primaryForceLw = QtGui.QListWidget()
      for fc in QtGui.qApp.DataManager.ListForceChoices():
         self.primaryForceLw.addItem(fc.Name())
      
      # points limit spinbox
      self.pointsLimitSb = QtGui.QSpinBox()
      self.pointsLimitSb.setRange(1, 1000000)
      self.pointsLimitSb.setValue(2000)
      self.pointsLimitSb.setSingleStep(50)
      
      self.cancelBtn = QtGui.QPushButton("Cancel")
      self.acceptBtn = QtGui.QPushButton("Ok")
      self.acceptBtn.setDefault(True)
      self.acceptBtn.setEnabled(False)
      
      self.primaryForceLw.setFocus()
      
   def _initLayout(self):
      self.setWindowTitle("New army list...")
      mainlay = QtGui.QHBoxLayout()
      contentlay = QtGui.QGridLayout()
      
      row = 0
      contentlay.addWidget(QtGui.QLabel("Primary force:"), row, 0, 1, 2)
      row += 1
      contentlay.addWidget(self.primaryForceLw, row, 0, 1, 2)
      row += 1
      contentlay.addWidget(QtGui.QLabel("Points limit:"), row, 0)
      contentlay.addWidget(self.pointsLimitSb, row, 1)
      
      btnlay = QtGui.QVBoxLayout()
      btnlay.addWidget(self.acceptBtn)
      btnlay.addWidget(self.cancelBtn)
      btnlay.addStretch(1)
      
      mainlay.addLayout(contentlay)
      mainlay.addLayout(btnlay)
      
      self.setLayout(mainlay)
      
   def _initConnections(self):
      self.primaryForceLw.itemSelectionChanged.connect(self.SelectionChanged)
      self.primaryForceLw.itemDoubleClicked.connect(self.accept)
      self.cancelBtn.clicked.connect(self.reject)
      self.acceptBtn.clicked.connect(self.accept)
      
   def SelectionChanged(self):
      if len(self.primaryForceLw.selectedItems())==0:
         self.acceptBtn.setEnabled(False)
      else:
         self.acceptBtn.setEnabled(True)
      
   def PrimaryForce(self): return QtGui.qApp.DataManager.ForceChoicesByName(self.primaryForceLw.currentItem().text())
   def PointsLimit(self): return self.pointsLimitSb.value()
   
#===============================================================================
# AddDetachmentDialog
#===============================================================================
class AddDetachmentDialog(QtGui.QDialog):
   def __init__(self):
      QtGui.QDialog.__init__(self)
      self._initChildren()
      self._initLayout()
      self._initConnections()
   
   def _initChildren(self):
      self.forceCb = QtGui.QComboBox()
      for fc in QtGui.qApp.DataManager.ListForceChoices():
         self.forceCb.addItem(fc.Name())
      
      self.makePrimaryCb = QtGui.QCheckBox("Make primary")
      
      self.cancelBtn = QtGui.QPushButton("Cancel")
      self.acceptBtn = QtGui.QPushButton("Ok")
      self.acceptBtn.setDefault(True)
      
      self.forceCb.setFocus()
      
   def _initLayout(self):
      self.setWindowTitle("Add detachment...")
      mainlay = QtGui.QHBoxLayout()
      contentlay = QtGui.QGridLayout()
      
      row = 0
      contentlay.addWidget(QtGui.QLabel("Force:"), row, 0)
      contentlay.addWidget(self.forceCb, row, 1)
      row += 1
      contentlay.addWidget(self.makePrimaryCb, row, 0, 1, 2)
      
      btnlay = QtGui.QVBoxLayout()
      btnlay.addWidget(self.acceptBtn)
      btnlay.addWidget(self.cancelBtn)
      btnlay.addStretch(1)
      
      mainlay.addLayout(contentlay)
      mainlay.addLayout(btnlay)
      
      self.setLayout(mainlay)
      
   def _initConnections(self):
      self.cancelBtn.clicked.connect(self.reject)
      self.acceptBtn.clicked.connect(self.accept)

   def Force(self): return QtGui.qApp.DataManager.ForceChoicesByName(self.forceCb.currentText())
   def MakePrimary(self): return self.makePrimaryCb.isChecked()