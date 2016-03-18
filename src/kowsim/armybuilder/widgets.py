# -*- coding: utf-8 -*-

# kow/widgets.py
#===============================================================================
#import os

from PySide import QtGui, QtCore
from PySide.QtCore import Qt
from command import ChangeUnitCmd, ChangeUnitSizeCmd, ChangeUnitItemCmd
from kowsim.armybuilder.command import SetUnitOptionsCmd

#===============================================================================
# UnitTable
#===============================================================================
class UnitTable(QtGui.QTableWidget):
   siPointsChanged = QtCore.Signal()
   DefaultRowHeight = 22
   
   def __init__(self, model):
      QtGui.QTableWidget.__init__(self)
      self._model = model # Detachment object
      self._columns = ("Unit", "Type", "Size", "Sp", "Me", "Ra", "De", "At", "Ne", "Points", "Special", "Magic item", "Options")
      self._colWidths = {"Unit": 170, "Type": 90, "Size": 80, "Sp": 30, "Me": 30, "Ra": 30, "De": 30, "At": 30, "Ne": 45, "Points": 45, "Special": 350, "Magic item": 200, "Options": 50}
      self.setColumnCount(len(self._columns))
      self.verticalHeader().hide()
      self.setHorizontalHeaderLabels(self._columns)
      for idx, col in enumerate(self._columns):
         self.setColumnWidth(idx, self._colWidths[col])
      self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
   
   def ChangeItem(self):
      sender = self.sender()
      row = sender.rowForWidget
      unit = self._model.Unit(row)
      
      itemName = self.cellWidget(row, self._columns.index("Magic item")).currentText()

      if itemName == "-":
         item = None
      else:
         # extract item name by stripping the points cost (e.g. 'Brew of Strength (30p)')
         leftBracket = itemName.index('(')
         itemName = itemName[:leftBracket].strip()
         item = QtGui.qApp.DataManager.ItemByName(itemName)
         
      cmd = ChangeUnitItemCmd(unit, self)
      cmd.Execute(row, item)
   
   def ChangeOptions(self):
      optMenu = self.sender()
      row = optMenu.rowForWidget
      unit = self._model.Unit(row)
      
      chosenOpts = []
      for act in optMenu.actions():
         opt = act.option # option reference was previously saved in the QAction object
         if act.isChecked():
            chosenOpts.append(opt)
      
      cmd = SetUnitOptionsCmd(unit, self)
      cmd.Execute(row, chosenOpts)
      
   def ChangeUnit(self, newindex):
      sender = self.sender() # determine which exact combobox was changed
      row = sender.rowForWidget
      
      newUnitName = self.cellWidget(row, self._columns.index("Unit")).currentText()
      cmd = ChangeUnitCmd(self._model, self)
      cmd.Execute(row, newUnitName)
      
   def ChangeSize(self, newindex):
      sender = self.sender() 
      row = sender.rowForWidget
      
      newSizeStr = self.cellWidget(row, self._columns.index("Size")).currentText()
      
      cmd = ChangeUnitSizeCmd(self._model, self)
      cmd.Execute(row, newSizeStr)
      
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
            
      for col in [self._columns.index(s) for s in ("Type", "Sp", "Me", "Ra", "De", "At", "Ne", "Points", "Special")]:
         self.setItem(row, col, QtGui.QTableWidgetItem())
         self.item(row, col).setFlags(self.item(row, col).flags() ^ Qt.ItemIsEditable) # remove editable flag)
         
      for col in [self._columns.index(s) for s in ("Type", "Sp", "Me", "Ra", "De", "At", "Ne", "Points")]:   
         self.item(row, col).setTextAlignment(Qt.AlignCenter)
      
      self.UpdateTextInRow(row)
      
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
      optMenu.rowForWidget = row
      self.optPb.setMenu(optMenu)
      self.optPb.setStyleSheet("border-style: none;")
      self.setCellWidget(row, self._columns.index("Options"), self.optPb)
      for opt in unit.Profile().ListOptions():
         act = optMenu.addAction(opt.DisplayStr())
         act.setCheckable(True)
         act.option = opt # just save corresponding UnitOption object inside the QAction
      optMenu.triggered.connect(self.ChangeOptions)
      
      # after everything has been set, register connections
      self.unitCb.currentIndexChanged.connect(self.ChangeUnit)
      self.sizeCb.currentIndexChanged.connect(self.ChangeSize)
      self.itemCb.currentIndexChanged.connect(self.ChangeItem)
      
   def UpdateTextInRow(self, row):
      """ Updates each TableWidgetItem where only text is displayed but
      leaves more complex CellWidgets (e.g. combo boxes) untouched. """
      unit = self._model.Unit(row)
      self.item(row, self._columns.index("Type")).setText(unit.UnitType().Name())
      self.item(row, self._columns.index("Sp")).setText("%d" % unit.Sp())
      self.item(row, self._columns.index("Me")).setText(unit.MeStr())
      self.item(row, self._columns.index("Ra")).setText(unit.RaStr())
      self.item(row, self._columns.index("De")).setText(unit.DeStr())
      self.item(row, self._columns.index("At")).setText(unit.AtStr())
      self.item(row, self._columns.index("Ne")).setText(unit.NeStr())
      self.item(row, self._columns.index("Points")).setText("%d" % unit.PointsCost())
      
      font = self.item(row, self._columns.index("Points")).font()
      font.setBold(unit.HasPointsCostModifier())
      self.item(row, self._columns.index("Points")).setFont(font)
      
      specialText = ", ".join(unit.ListSpecialRules())
      if len(unit.ListChosenOptions())>0:
         optsText = ", ".join(["%s" % o.Name() for o in unit.ListChosenOptions()])
         specialText += ", " + optsText
      self.item(row, self._columns.index("Special")).setText(specialText)
      self.item(row, self._columns.index("Special")).setToolTip(specialText)
            

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