# -*- coding: utf-8 -*-

# kow/widgets.py
#===============================================================================
#import os

from PySide import QtGui, QtCore
from PySide.QtCore import Qt
from command import ChangeUnitCmd, ChangeUnitSizeCmd, ChangeUnitItemCmd
from kowsim.armybuilder.command import SetUnitOptionsCmd
import kowsim.kow.stats as st

#===============================================================================
# UnitTable
#===============================================================================
class UnitTable(QtGui.QTableWidget):
   siPointsChanged = QtCore.Signal()
   siModified = QtCore.Signal(bool)
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
      
   def SelectedRows(self):
      rows = []
      for itm in self.selectedItems():
         if itm.row() not in rows:
            rows.append(itm.row())
      return rows
      
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
      unitCb = QtGui.QComboBox()
      for unitgroup in unit.Detachment().Choices().ListGroups():
         unitCb.addItem(unitgroup.Name())
      self.setCellWidget(row, self._columns.index("Unit"), unitCb)
      unitCb.rowForWidget = row
      unitCb.setCurrentIndex(unitCb.findText(unit.Profile().Name()))
   
      # size type options
      sizeCb = QtGui.QComboBox()
      for profile in unit.Detachment().Choices().GroupByName(unit.Profile().Name()).ListOptions():
         sizeCb.addItem(profile.SizeType().Name())
      self.setCellWidget(row, self._columns.index("Size"), sizeCb)
      sizeCb.rowForWidget = row
      sizeCb.setCurrentIndex(sizeCb.findText(unit.SizeType().Name()))
      if sizeCb.count()==1:
         sizeCb.setEnabled(False)
      
      # magic item
      itemCb = QtGui.QComboBox()
      itemCb.rowForWidget = row
      itemCb.addItem("-")
      if unit.CanHaveItem():
         itemCb.addItems(["%s (%dp)" % (itm.Name(), itm.PointsCost()) for itm in QtGui.qApp.DataManager.ListItems()])
         itemCb.setEnabled(True)
      else:
         itemCb.setEnabled(False)
      self.setCellWidget(row, self._columns.index("Magic item"), itemCb)
      if unit.Item(): itemCb.setCurrentIndex(itemCb.findText(unit.Item().StringWithPoints()))
      
      # options
      self.UpdateUnitOptions(row)
      
      # after everything has been set, register connections
      unitCb.currentIndexChanged.connect(self.ChangeUnit)
      sizeCb.currentIndexChanged.connect(self.ChangeSize)
      itemCb.currentIndexChanged.connect(self.ChangeItem)
   
   def SetModified(self, modified=True):
      self.siModified.emit(modified)
      
   def UpdateUnitOptions(self, row):
      unit = self._model.Unit(row)
      
      # overwrite old options pb
      optPb = QtGui.QPushButton("...")
      self.setCellWidget(row, self._columns.index("Options"), optPb)
      optPb.setStyleSheet("border-style: none;")
      
      if len(unit.Profile().ListOptions())==0:
         optPb.setEnabled(False)
         optPb.setText("-")
      else:
         optMenu = QtGui.QMenu(optPb)
         optMenu.rowForWidget = row
         optPb.setMenu(optMenu)
         for opt in unit.Profile().ListOptions():
            act = optMenu.addAction(opt.DisplayStr())
            act.setCheckable(True)
            act.option = opt # just save corresponding UnitOption object inside the QAction
            if opt in unit.ListChosenOptions():
               act.setChecked(True)
         optMenu.triggered.connect(self.ChangeOptions)
      
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
      
      # determine font weight
      normalFont = self.item(row, self._columns.index("Special")).font()
      boldFont = QtGui.QFont(normalFont)
      boldFont.setWeight(QtGui.QFont.Bold)
      
      self.item(row, self._columns.index("Sp")).setFont( boldFont if unit.HasStatModifier(st.ST_SPEED) else normalFont )
      self.item(row, self._columns.index("Me")).setFont( boldFont if unit.HasStatModifier(st.ST_MELEE) else normalFont )
      self.item(row, self._columns.index("Ra")).setFont( boldFont if unit.HasStatModifier(st.ST_RANGED) else normalFont )
      self.item(row, self._columns.index("De")).setFont( boldFont if unit.HasStatModifier(st.ST_DEFENSE) else normalFont )
      self.item(row, self._columns.index("At")).setFont( boldFont if unit.HasStatModifier(st.ST_ATTACKS) else normalFont )
      self.item(row, self._columns.index("Points")).setFont( boldFont if unit.HasPointsCostModifier() else normalFont )
      
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