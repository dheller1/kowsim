# -*- coding: utf-8 -*-

# armybuilder/ui.py
#===============================================================================
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

#===============================================================================
# UnitOptionsDialog
#===============================================================================
class UnitOptionsDialog(QtGui.QDialog):
   def __init__(self, *args):
      super(UnitOptionsDialog, self).__init__(*args)
      
      self._unit = None
      self.setWindowTitle("Edit unit options")
      
      # child widgets
      self.checkOptionsList = QtGui.QListWidget(self)
      
      self.okBtn = QtGui.QPushButton("&Ok")
      self.okBtn.setDefault(True)
      
      self.cancelBtn = QtGui.QPushButton("&Cancel")
      
      # layout
      lay = QtGui.QVBoxLayout()
      btnLay = QtGui.QHBoxLayout()
      
      btnLay.addWidget(self.okBtn)
      btnLay.addWidget(self.cancelBtn)
      btnLay.addStretch(1)
      
      lay.addWidget(self.checkOptionsList)
      lay.addLayout(btnLay)
      self.setLayout(lay)
      
      # connections
      self.cancelBtn.clicked.connect(self.reject)
      self.okBtn.clicked.connect(self.Accept)
      
   def Accept(self):
      """ Careful, this assumes that the unit option list and the ListWidget entries are exactly in the same order. """
      if self._unit:
         self._unit._activeOptions = []
         for row in range(self.checkOptionsList.count()):
            if self.checkOptionsList.item(row).checkState() == Qt.Checked:
               self._unit._activeOptions.append(self._unit.ListOptions()[row])
               print self._unit.ListOptions()[row]._effects[0]

      super(UnitOptionsDialog, self).accept()
            
   def InitWithData(self, unit):
      self._unit = unit
      
      for opt in unit.ListOptions():
         lwi = QtGui.QListWidgetItem("%s (%dp)" % (opt.Name(), opt.PointsCost()))
         lwi.setFlags(lwi.flags() | Qt.ItemIsUserCheckable)
         lwi.setCheckState( Qt.Checked if opt in unit.ListActiveOptions() else Qt.Unchecked )
         self.checkOptionsList.addItem(lwi)