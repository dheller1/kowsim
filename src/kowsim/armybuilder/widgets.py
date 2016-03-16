# -*- coding: utf-8 -*-

# kow/widgets.py
#===============================================================================
#import os

from PySide import QtGui#, QtCore
from PySide.QtCore import Qt
from command import ChangeUnitCmd

#===============================================================================
# UnitTable
#===============================================================================
class UnitTable(QtGui.QTableWidget):
   DefaultRowHeight = 22
   
   def __init__(self, model):
      QtGui.QTableWidget.__init__(self)
      self._model = model # detachment object
      self._columns = ("Unit", "Type", "Size", "Sp", "Me", "Ra", "De", "At", "Ne", "Points", "Special", "Magic item", "Options")
      self._colWidths = {"Unit": 170, "Type": 90, "Size": 80, "Sp": 30, "Me": 30, "Ra": 30, "De": 30, "At": 30, "Ne": 45, "Points": 45, "Special": 350, "Magic item": 200, "Options": 50}
      self.setColumnCount(len(self._columns))
      self.verticalHeader().hide()
      self.setHorizontalHeaderLabels(self._columns)
      for idx, col in enumerate(self._columns):
         self.setColumnWidth(idx, self._colWidths[col])
      self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
      
   def ChangeUnit(self, newindex):
      sender = self.sender() # determine which exact combobox was changed
      row = sender.rowForWidget
      
      newUnitName = self.cellWidget(row, self._columns.index("Unit")).currentText()
      cmd = ChangeUnitCmd(self._model, self)
      cmd.Execute(row, newUnitName)
      
   def ChangeSize(self, newindex):
      pass
   def ChangeItem(self, newindex):
      pass
      
   def SetRow(self, row, unit):
      if row>=self.rowCount():
         self.insertRow(row)
      
      for col in range(self.columnCount()):
         olditm = self.item(row, col)
         if olditm is not None:
            del olditm
         oldwdg = self.cellWidget(row, col)
         if oldwdg is not None:
            del oldwdg
            
      self.setRowHeight(row, UnitTable.DefaultRowHeight)
            
      self.setItem(row, self._columns.index("Unit"), QtGui.QTableWidgetItem(unit.Name()))
      self.setItem(row, self._columns.index("Type"), QtGui.QTableWidgetItem(unit.UnitType().Name()))
      self.setItem(row, self._columns.index("Sp"), QtGui.QTableWidgetItem("%d" % unit.Sp()))
      self.setItem(row, self._columns.index("Me"), QtGui.QTableWidgetItem(unit.MeStr()))
      self.setItem(row, self._columns.index("Ra"), QtGui.QTableWidgetItem(unit.RaStr()))
      self.setItem(row, self._columns.index("De"), QtGui.QTableWidgetItem(unit.DeStr()))
      self.setItem(row, self._columns.index("At"), QtGui.QTableWidgetItem(unit.AtStr()))
      self.setItem(row, self._columns.index("Ne"), QtGui.QTableWidgetItem(unit.NeStr()))
      self.setItem(row, self._columns.index("Points"), QtGui.QTableWidgetItem("%d" % unit.PointsCost()))
      self.setItem(row, self._columns.index("Special"), QtGui.QTableWidgetItem(", ".join(unit.ListSpecialRules())))
      
      for col in [self._columns.index(s) for s in ("Type", "Sp", "Me", "Ra", "De", "At", "Ne", "Points", "Special")]:
         self.item(row, col).setFlags(self.item(row, col).flags() ^ Qt.ItemIsEditable) # remove editable flag)
      
      for col in [self._columns.index(s) for s in ("Type", "Sp", "Me", "Ra", "De", "At", "Ne", "Points")]:   
         self.item(row, col).setTextAlignment(Qt.AlignCenter)
      
      # unit options
      self.unitCb = QtGui.QComboBox()
      for unitgroup in unit.Detachment().Choices().ListGroups():
         self.unitCb.addItem(unitgroup.Name())
      self.setCellWidget(row, self._columns.index("Unit"), self.unitCb)
      self.unitCb.rowForWidget = row
      self.unitCb.setCurrentIndex(self.unitCb.findText(unit.Profile().Name()))
      
      # size type options
      self.sizeCb = QtGui.QComboBox()
      for profile in unit.Detachment().Choices().GroupByName(unit.Profile().Name()).ListOptions():
         self.sizeCb.addItem(profile.SizeType().Name())
      self.setCellWidget(row, self._columns.index("Size"), self.sizeCb)
      self.sizeCb.rowForWidget = row
      self.sizeCb.setCurrentIndex(self.sizeCb.findText(unit.SizeType().Name()))
      
      # magic item
      self.itemCb = QtGui.QComboBox()
      self.itemCb.rowForWidget = row
      self.itemCb.addItem("-")
      if unit.CanHaveItem():
         self.itemCb.addItems(["%s (%dp)" % (itm.Name(), itm.PointsCost()) for itm in QtGui.qApp.DataManager.ListItems()])
         self.itemCb.setEnabled(True)
      else:
         self.itemCb.setEnabled(False)
      self.setCellWidget(row, self._columns.index("Magic item"), self.itemCb)
      if unit.Item(): self.itemCb.setCurrentIndex(self.itemCb.findText(unit.Item().Name()))
      
      # options
      self.optPb = QtGui.QPushButton("...")
      optMenu = QtGui.QMenu(self.optPb)
      self.optPb.setMenu(optMenu)
      a1 = optMenu.addAction("Bla 1")
      a2 = optMenu.addAction("Opt 2")
      a1.setCheckable(True)
      a2.setCheckable(True)
      self.setCellWidget(row, self._columns.index("Options"), self.optPb)
      
      
      # after everything has been set, register connections
      self.unitCb.currentIndexChanged.connect(self.ChangeUnit)
      self.sizeCb.currentIndexChanged.connect(self.ChangeSize)
      self.itemCb.currentIndexChanged.connect(self.ChangeItem)
      

#===============================================================================
# ValidationWidget
#===============================================================================
class ValidationWidget(QtGui.QWidget):
   def __init__(self, parent=None):
      super(ValidationWidget, self).__init__(parent)
      
      self.setMinimumWidth(300)
      
      # child widgets
      self.pointsTotalLbl = QtGui.QLabel("Total points: <b>0</b>/2000")
      
      # layout
      lay = QtGui.QGridLayout()
      lay.addWidget(self.pointsTotalLbl)
      self.setLayout(lay)
      
   def UpdateTotalPoints(self, points, pointsLimit):
      if points <= pointsLimit:
         self.pointsTotalLbl.setText("Total points: <b>%d</b>/%d" % (points, pointsLimit))
      else:
         self.pointsTotalLbl.setText("Total points: <b><span style='color:#ff0000;'>%d</span></b>/%d" % (points, pointsLimit))