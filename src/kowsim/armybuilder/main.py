# -*- coding: utf-8 -*-

# armybuilder/main.py
#===============================================================================
import os, sys
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from ..kow.force import ArmyList, Detachment
from ..kow.unit import UnitProfile
from ..kow import unittype as KUT
from load_data import DataManager
from ui import UnitOptionsDialog
from views import ArmyListView
from command import SaveArmyListCmd
from dialogs import NewArmyListDialog


#===============================================================================
# MainWindow
#===============================================================================
class MainWindow(QtGui.QMainWindow):
   def __init__(self):
      super(MainWindow, self).__init__()
      
      #=========================================================================
      # Load data
      #=========================================================================
      QtGui.qApp.DataManager = DataManager()
      QtGui.qApp.DataManager.LoadForceChoices()
      QtGui.qApp.DataManager.LoadItems()
      
      #=========================================================================
      # Init main window
      #=========================================================================
      self.resize(1280, 800)
      self.setWindowTitle("Army Builder")
      
      #=========================================================================
      # Init child widgets and menus
      #=========================================================================
      self.mdiArea = MdiArea()
      self.setCentralWidget(self.mdiArea)
      
      #self.setStatusBar(QtGui.QStatusBar())
      #self.statusBar().showMessage("Ready.")
      self.setMenuBar(MainMenu())
      
      
      self.toolBar = QtGui.QToolBar(self)
      self.toolBar.addAction(QtGui.QIcon(os.path.join("..","data","icons","new.png")), "New army list", self.NewArmyList)
      self.openAction = self.toolBar.addAction(QtGui.QIcon(os.path.join("..","data","icons","open.png")), "Open", self.OpenArmyList)
      self.saveAction = self.toolBar.addAction(QtGui.QIcon(os.path.join("..","data","icons","save.png")), "Save", self.SaveArmyList)
      self.saveAction.setEnabled(False)
      
      self.addToolBar(self.toolBar)
      
      self.InitConnections()
      
   def InitConnections(self):
      self.menuBar().newArmyAct.triggered.connect(self.NewArmyList)
      self.menuBar().openAct.triggered.connect(self.OpenArmyList)
      self.menuBar().saveAct.triggered.connect(self.SaveArmyList)
      self.menuBar().saveAsAct.triggered.connect(self.SaveArmyListAs)
      self.menuBar().exitAct.triggered.connect(self.close)
      self.mdiArea.subWindowActivated.connect(self.CurrentWindowChanged)
      
   def CurrentWindowChanged(self, wnd):
      if wnd: self.saveAction.setEnabled(True)
      else: self.saveAction.setEnabled(False)
   
   def NewArmyList(self):
      self.mdiArea.AddArmySubWindow()
      
   def OpenArmyList(self):
      filenames, filter = QtGui.QFileDialog.getOpenFileNames(self, "Open army list(s)", "..", "Army lists (*.lst);;All files (*.*)")
      
      for f in filenames:
         sub = self.mdiArea.AddArmySubWindow()
         sub.OpenFromFile(f)
      
   def SaveArmyList(self, saveAs=False):
      l = len(self.mdiArea.subWindowList())
      # somehow if there's only one subwindow it is not registered as active,
      # so do this as a workaround.
      if l == 0: return
      elif l == 1: view = self.mdiArea.subWindowList()[0].widget()
      else: view = self.mdiArea.activeSubWindow().widget()
      
      cmd = SaveArmyListCmd(view._model, view)
      cmd.Execute(saveAs)
      
   def SaveArmyListAs(self):
      self.SaveArmyList(saveAs=True)
   
#===============================================================================
# MainMenu
#===============================================================================
class MainMenu(QtGui.QMenuBar):
   def __init__(self, *args):
      super(MainMenu, self).__init__(*args)
      
      self.fileMenu = self.addMenu("&File")
      self.newArmyAct = self.fileMenu.addAction("&New army")
      self.newArmyAct.setShortcut("Ctrl+N")
      self.openAct = self.fileMenu.addAction("&Open file")
      self.fileMenu.addSeparator()
      self.openAct.setShortcut("Ctrl+O")
      self.saveAct = self.fileMenu.addAction("&Save")
      self.saveAct.setShortcut("Ctrl+S")
      self.saveAsAct = self.fileMenu.addAction("Save &as")
      self.saveAsAct.setShortcut("Ctrl+Shift+S")
      self.fileMenu.addSeparator()
      self.exitAct = self.fileMenu.addAction("&Exit")
      
      
#===============================================================================
# MdiArea
#===============================================================================
class MdiArea(QtGui.QMdiArea):
   def __init__(self, *args):
      super(MdiArea, self).__init__(*args)
      self.setViewMode(QtGui.QMdiArea.TabbedView)
      self.setTabsClosable(True)
      self.setTabsMovable(True)
      #self.AddArmySubWindow()
      
   def AddArmySubWindow(self):
      dlg = NewArmyListDialog()
      if QtGui.QDialog.Accepted == dlg.exec_():
         # number of unnamed armies
         num = len(self.subWindowList())
         if num==0: name = "Unnamed army"
         else: name = "Unnamed army (%d)" % (num+1)
         
         armyList = ArmyList(name, dlg.PointsLimit())
         armyList.AddDetachment( Detachment(dlg.PrimaryForce(), None, [], True) )
         
         #sub = ArmyMainWidget(name)
         sub = ArmyListView(armyList)
         self.addSubWindow(sub)
         sub.show() # important!
         sub.showMaximized()
         return sub
      
      return None
      
            
#===============================================================================
# ArmyMainWidget
#===============================================================================
class ArmyMainWidget(QtGui.QWidget):
   siPointsChanged = QtCore.Signal(int, int)
   siModified = QtCore.Signal(bool)
   
   def __init__(self, name="Unnamed army"):
      super(ArmyMainWidget, self).__init__()
      
      self.lastFilename = None
      
      self.setMinimumSize(400,300)
      self.setWindowTitle(("*" + name))
      self.armyList = ArmyList(name, points=2000)
      
      self._MapRowToUnitId = {}
      self._MapUnitIdToRow = {}
      
      #=========================================================================
      # child widgets
      #=========================================================================
      self.armyNameLe = QtGui.QLineEdit(name)
         
      self.pointsLimitSb = QtGui.QSpinBox()
      self.pointsLimitSb.setRange(1, 1000000)
      self.pointsLimitSb.setValue(2000)
      self.pointsLimitSb.setSingleStep(50)
      
      self.armyNameLe.selectAll()
      self.unitTable = QtGui.QTableWidget()
      self.unitTable.setColumnCount(13)
      self.unitTable.verticalHeader().hide()
      self.unitTable.setHorizontalHeaderLabels(("Unit", "Type", "Size", "Sp", "Me", "Ra", "De", "At", "Ne", "Points", "Special", "Magic item", "Options"))
      colWidths = [170, 90, 80, 30, 30, 30, 30, 30, 45, 45, 350, 200, 50]
      for i in range(len(colWidths)):
         self.unitTable.setColumnWidth(i, colWidths[i])
      self.unitTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            
      self.addUnitPb = QtGui.QPushButton(QtGui.QIcon(os.path.join("..", "data","icons","plus.png")), "&Add")
      self.duplicateUnitPb = QtGui.QPushButton(QtGui.QIcon(os.path.join("..", "data","icons","copy.png")), "Dupli&cate")
      self.duplicateUnitPb.setEnabled(False)
      self.deleteUnitPb = QtGui.QPushButton(QtGui.QIcon(os.path.join("..", "data","icons","delete.png")), "&Delete")
      self.deleteUnitPb.setEnabled(False)
      self.optionsPb = QtGui.QPushButton(QtGui.QIcon(os.path.join("..", "data","icons","options.png")), "&Options")
      self.optionsPb.setEnabled(False)
      
      self.validationWdg = ValidationWidget(parent=self)
      
      #=========================================================================
      # group boxes
      #=========================================================================
      self.generalGb = QtGui.QGroupBox("General")
      self.unitGb = QtGui.QGroupBox("Units")
      self.valGb = QtGui.QGroupBox("Validation")
      
      #=========================================================================
      # layout
      #=========================================================================
      genlay = QtGui.QGridLayout()
      
      row = 0
      genlay.addWidget(QtGui.QLabel("Army name:"), row, 0)
      genlay.addWidget(self.armyNameLe, row, 1)
      row += 1
      genlay.addWidget(QtGui.QLabel("Points limit:"), row, 0)
      genlay.addWidget(self.pointsLimitSb, row, 1)
      row += 1
      self.generalGb.setLayout(genlay)
      
      self.unitGb.setLayout(QtGui.QVBoxLayout())
      unitButtonsLay = QtGui.QHBoxLayout()
      unitButtonsLay.addWidget(self.addUnitPb)
      unitButtonsLay.addWidget(self.duplicateUnitPb)
      unitButtonsLay.addWidget(self.deleteUnitPb)
      unitButtonsLay.addWidget(self.optionsPb)
      unitButtonsLay.addStretch(1)
      self.unitGb.layout().addLayout(unitButtonsLay)
      self.unitGb.layout().addWidget(self.unitTable)
      
      vallay = QtGui.QVBoxLayout()
      vallay.addWidget(self.validationWdg)
      self.valGb.setLayout(vallay)
      
      mainlay = QtGui.QGridLayout()
      mainlay.addWidget(self.generalGb, 0, 0)
      mainlay.addWidget(self.valGb, 0, 1)
      mainlay.addWidget(self.unitGb, 1, 0, 1, 2)
      self.setLayout(mainlay)
      
      #=========================================================================
      # connections
      #=========================================================================
      self.armyNameLe.textChanged.connect(self.DataChanged)
      self.addUnitPb.clicked.connect(self.AddUnit)
      self.deleteUnitPb.clicked.connect(self.DeleteUnit)
      self.duplicateUnitPb.clicked.connect(self.DuplicateUnit)
      self.optionsPb.clicked.connect(self.OptionsForUnit)
      
      self.unitTable.itemSelectionChanged.connect(self.UpdateButtons)
      self.pointsLimitSb.valueChanged.connect(self.PointsLimitChanged)
      
      self.siPointsChanged.connect(self.validationWdg.UpdateTotalPoints)
      
      #=========================================================================
      # Final init, full update
      #=========================================================================
      pass
      
   def AddUnit(self):
      rowNum = self.unitTable.rowCount()
      self.unitTable.insertRow(rowNum) 
      self.unitTable.setRowHeight(rowNum, 22)
      
      # cell items
      cb = QtGui.QComboBox()
      for unit in self.armyList.PrimaryForce().Choices().ListGroups():
         cb.addItem(unit.Name())
      self.unitTable.setCellWidget(rowNum, 0, cb)
      
      cbOpt = QtGui.QComboBox()
      self.unitTable.setCellWidget(rowNum, 2, cbOpt) # size type
      
      for col in (1, 3, 4, 5, 6, 7, 8, 9, 10): # profile stats
         self.unitTable.setItem(rowNum, col, QtGui.QTableWidgetItem(""))
         self.unitTable.item(rowNum, col).setFlags(self.unitTable.item(rowNum, col).flags() ^ Qt.ItemIsEditable) # remove editable flag
         if col != 10: self.unitTable.item(rowNum, col).setTextAlignment(Qt.AlignCenter)
         
      cbItem = QtGui.QComboBox()
      self.unitTable.setCellWidget(rowNum, 11, cbItem) # magic item
      cbItem.addItem("-")
      cbItem.addItems(["%s (%dp)" % (itm.Name(), itm.PointsCost()) for itm in QtGui.qApp.DataManager.ListItems()])
            
      # connections
      mapper = QtCore.QSignalMapper(self) # set mapping to identify combobox by its row
      mapper.setMapping(cb, rowNum)
      cb.currentIndexChanged.connect(mapper.map)
      
      mapperOpt = QtCore.QSignalMapper(self)
      mapperOpt.setMapping(cbOpt, rowNum)
      cbOpt.currentIndexChanged.connect(mapperOpt.map)
      
      mapperItm = QtCore.QSignalMapper(self)
      mapperItm.setMapping(cbItem, rowNum)
      cbItem.currentIndexChanged.connect(mapperItm.map)
      
      mapper.mapped[int].connect(self.UnitGroupChanged)
      mapperOpt.mapped[int].connect(self.UnitOptionChanged)
      mapperItm.mapped[int].connect(self.UnitItemChanged)
      
      # register a default unit in armyList and store its index in the armyList._units array
      index = self.armyList.PrimaryForce().AddUnit(UnitProfile())
      self._MapRowToUnitId[rowNum] = index
      self._MapUnitIdToRow[index] = rowNum
      
      self.unitTable.selectRow(rowNum)
      self.unitTable.setFocus()
      
      # update everything
      self.UnitGroupChanged(rowNum)
      
      self.SetModified(True)
            
   def DataChanged(self):
      self.SetModified(True)
      
      name = self.armyNameLe.text()
      self.armyList.SetName(name)
      self.setWindowTitle("*%s" % name)
      
   def DeleteUnit(self):
      if QtGui.QMessageBox.Yes != QtGui.QMessageBox.warning(self, "Delete unit", "This will delete the current unit(s).<br />Are you sure?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel):
         return
      
      rowsToDelete = []
      for itm in self.unitTable.selectedItems():
         if itm.row() not in rowsToDelete:
            rowsToDelete.append(itm.row())
            
      # sort in descending order to not interfere with higher row IDs
      rowsToDelete.sort(reverse=True)
      #print "Deleting rows: ", rowsToDelete      

      for row in rowsToDelete:
         # remove unit from armylist
         unitIdx = self._MapRowToUnitId[row]
         #print "Deleting unit %d (%s)" % (unitIdx, self.armyList.PrimaryForce().ListUnits()[unitIdx].Name())
         self.armyList.PrimaryForce().RemoveUnit(unitIdx)
         
         # delete row
         self.unitTable.removeRow(row)
         
         # assemble new mapping dict
         # all IDs > unitIdx decrease by 1
         # all row numbers > row decrease by 1
         newUnitIdToRow = {}
         for myId, myRow in self._MapUnitIdToRow.iteritems():
            if myId == unitIdx or myRow == row: continue # skip the deleted unit and row
            
            if myId > unitIdx: myId -= 1
            if myRow > row: myRow -= 1
            
            newUnitIdToRow[myId] = myRow 
         
         # replace mapping dicts
         self._MapUnitIdToRow = newUnitIdToRow
         self._MapRowToUnitId = {v:k for k, v in self._MapUnitIdToRow.iteritems()}
         
      #print "Done."
      #print "Units in army list:", self.armyList.PrimaryForce().ListUnits()
      #print "Mappings: _UnitIdToRow", self._MapUnitIdToRow
      #print "Mappings: _RowToUnitId", self._MapRowToUnitId
      
      self.siPointsChanged.emit(self.armyList.PrimaryForce().PointsTotal(), self.armyList.PointsLimit())
      self.SetModified(True)
      
   def DuplicateUnit(self):
      selRow = self.unitTable.selectedItems()[0].row()
      unitName, unitSize = self.unitTable.cellWidget(selRow, 0).currentText(), self.unitTable.cellWidget(selRow, 2).currentText()
       
      self.AddUnit()
      row = self.unitTable.rowCount()-1
      # temporarily block signals from QComboBoxes for unit type and size
      #self.unitTable.cellWidget(row, 0).blockSignals(True) # unit choice
      #self.unitTable.cellWidget(row, 2).blockSignals(True) # size type
      
      # set correct choices
      unitCb = self.unitTable.cellWidget(row, 0)
      idx = unitCb.findText(unitName)
      if idx < 0:
         QtGui.QMessageBox.warning(self, "Duplicate unit", "Warning: Can't duplicate unit,<br>please switch back to the correct primary force.<br>Adding default unit for current force.")
         return
      unitCb.setCurrentIndex(idx)
      
      sizeCb = self.unitTable.cellWidget(row, 2)
      idx = sizeCb.findText(unitSize)
      if idx < 0:
         QtGui.QMessageBox.warning(self, "Duplicate unit", "Warning: Can't duplicate unit,<br>please switch back to the correct primary force.<br>Adding default unit for current force.")
         return
      sizeCb.setCurrentIndex(idx)
      self.SetModified(True)
      
   def PointsLimitChanged(self):
      self.armyList.SetPointsLimit(self.pointsLimitSb.value())
      self.siPointsChanged.emit(self.armyList._primaryForce.PointsTotal(), self.pointsLimitSb.value())
      self.SetModified(True)
      
   def OpenFromFile(self, filename):
      self.armyList = ArmyList("blank")
      self.armyList.LoadFromFile(filename, QtGui.qApp.DataManager)
      self.UpdateUi()
      self.lastFilename = filename
      self.SetModified(False)
      
   def OptionsForUnit(self):
      selRow = self.unitTable.selectedItems()[0].row()
      selUnit = self.armyList.PrimaryForce().ListUnits()[self._MapRowToUnitId[selRow]]
      
      dlg = UnitOptionsDialog()
      dlg.InitWithData(selUnit)
      ret = dlg.exec_()
      
      if ret == QtGui.QDialog.Accepted:
         self.UpdateRow(selRow)
         self.siPointsChanged.emit(self.armyList.PrimaryForce().PointsTotal(), self.armyList.PointsLimit())
         self.SetModified()
   
   def SaveArmyList(self, saveAs=False):
      if (not self.lastFilename) or saveAs:
         filename, filter = QtGui.QFileDialog.getSaveFileName(self, "Save army list as", "../%s.lst" % self.armyList.Name(), "Army lists (*.lst);;All files (*.*)")
         print filename
         if filename == "": return
         else: self.lastFilename = filename
      else:
         filename = self.lastFilename
      
      self.armyList.SaveToFile(filename)
      self.SetModified(False)
      
   def SetModified(self, modified=True):
      self.wasModified = modified
      
      if self.lastFilename:
         showName = " (%s)" % os.path.basename(self.lastFilename)
      else: showName = ""
      modified = "*" if self.wasModified else ""
      
      self.setWindowTitle("%s%s%s" % (modified, self.armyList.Name(), showName))
      self.siModified.emit(modified)
      
   def SetRowToUnit(self, row, unit, unitid):
      """ Set row to reflect an already existing unit. """
      if row >= self.unitTable.rowCount():
         self.unitTable.setRowCount(row+1)
      self.unitTable.setRowHeight(row, 22)
      
      # cell items
      cb = QtGui.QComboBox()
      for choice in self.armyList.PrimaryForce().Choices().ListGroups():
         cb.addItem(choice.Name())
      self.unitTable.setCellWidget(row, 0, cb)
      
      cbOpt = QtGui.QComboBox()
      self.unitTable.setCellWidget(row, 2, cbOpt) # size type
      
      for col in (1, 3, 4, 5, 6, 7, 8, 9, 10): # profile stats
         self.unitTable.setItem(row, col, QtGui.QTableWidgetItem(""))
         self.unitTable.item(row, col).setFlags(self.unitTable.item(row, col).flags() ^ Qt.ItemIsEditable) # remove editable flag
         if col != 10: self.unitTable.item(row, col).setTextAlignment(Qt.AlignCenter)
         
      cbItem = QtGui.QComboBox()
      self.unitTable.setCellWidget(row, 11, cbItem) # magic item
      cbItem.addItem("-")
      cbItem.addItems(["%s (%dp)" % (itm.Name(), itm.PointsCost()) for itm in QtGui.qApp.DataManager.ListItems()])
      
      # set cell items to correct contents
      cb.setCurrentIndex(cb.findText(unit.Name()))
      
      # add and set size option(s)
      for so in self.armyList.PrimaryForce().Choices().GroupByName(unit.Name()).ListOptions():
         cbOpt.addItem(so.SizeType().Name())
      cbOpt.setCurrentIndex(cbOpt.findText(unit.SizeType().Name()))
      
      cbOpt.setEnabled( len(self.armyList.PrimaryForce().Choices().GroupByName(unit.Name()).ListOptions()) > 1 )
      
      # set item
      if unit.Item():
         itemString = "%s (%dp)" % (unit.Item().Name(), unit.Item().PointsCost())
         cbItem.setCurrentIndex(cbItem.findText(itemString)) 
      
      # afterwards, do connections
      mapper = QtCore.QSignalMapper(self) # set mapping to identify combobox by its row
      mapper.setMapping(cb, row)
      cb.currentIndexChanged.connect(mapper.map)
      
      mapperOpt = QtCore.QSignalMapper(self)
      mapperOpt.setMapping(cbOpt, row)
      cbOpt.currentIndexChanged.connect(mapperOpt.map)
      
      mapperItm = QtCore.QSignalMapper(self)
      mapperItm.setMapping(cbItem, row)
      cbItem.currentIndexChanged.connect(mapperItm.map)
      
      mapper.mapped[int].connect(self.UnitGroupChanged)
      mapperOpt.mapped[int].connect(self.UnitOptionChanged)
      mapperItm.mapped[int].connect(self.UnitItemChanged)
      
      # update mappings
      self._MapRowToUnitId[row] = unitid
      self._MapUnitIdToRow[unitid] = row
      
      # update everything
      self.UnitOptionChanged(row)
      self.UnitItemChanged(row)
      self.siPointsChanged.emit(self.armyList.PrimaryForce().PointsTotal(), self.armyList.PointsLimit())
   
   @QtCore.Slot(int)
   def UnitGroupChanged(self, row):
      # update this row
      grpname = unicode( self.unitTable.cellWidget(row, 0).currentText() )
      grp = self.armyList.PrimaryForce().Choices().GroupByName(grpname)
      
      option = grp.Default()
      self.unitTable.item(row, 1).setText(option.UnitType().Name()) # unit type
      
      # size options
      sizeOptWdg = self.unitTable.cellWidget(row, 2)
      sizeOptWdg.clear()
      for o in grp.ListOptions():
         sizeOptWdg.addItem(o.SizeType().Name())
      
      sizeOptWdg.setEnabled( (len(grp.ListOptions())>1) )
         
      self.unitTable.item(row, 3).setText("%d" % option.Sp())
      self.unitTable.item(row, 4).setText(option.MeStr())
      self.unitTable.item(row, 5).setText(option.RaStr())
      self.unitTable.item(row, 6).setText(option.DeStr())
      self.unitTable.item(row, 7).setText(option.AtStr())
      self.unitTable.item(row, 8).setText(option.NeStr())
      self.unitTable.item(row, 9).setText("%d" % option.PointsCost())
      self.unitTable.item(row, 10).setText(", ".join(option.ListSpecialRules()))
      
      # can it have a magical item?
      if option.UnitType() in (KUT.UT_MON, KUT.UT_WENG):
         self.unitTable.cellWidget(row, 11).setEnabled(False)
         self.unitTable.cellWidget(row, 11).setCurrentIndex(0)
      else: self.unitTable.cellWidget(row, 11).setEnabled(True)
      
      # replace unit in armylist
      newUnit = option.CreateInstance()
      self.armyList.PrimaryForce().ReplaceUnit(self._MapRowToUnitId[row], newUnit)
      self.siPointsChanged.emit(self.armyList.PrimaryForce().PointsTotal(), self.armyList.PointsLimit())
      self.SetModified()
      
   @QtCore.Slot(int)
   def UnitOptionChanged(self, row):
      # update this row
      grpname = unicode( self.unitTable.cellWidget(row, 0).currentText() )
      grp = self.armyList.PrimaryForce().Choices().GroupByName(grpname)
      
      optTxt = self.unitTable.cellWidget(row, 2).currentText()
      if optTxt == "": return # this can occur when the unit group has been changed but the option combo box has not been updated yet. do nothing
      
      option = grp.OptionByName(optTxt)
      
      self.unitTable.item(row, 1).setText(option.UnitType().Name()) # unit type
      
      # size options left untouched, do nothing
      self.unitTable.item(row, 3).setText("%d" % option.Sp())
      self.unitTable.item(row, 4).setText(option.MeStr())
      self.unitTable.item(row, 5).setText(option.RaStr())
      self.unitTable.item(row, 6).setText(option.DeStr())
      self.unitTable.item(row, 7).setText(option.AtStr())
      self.unitTable.item(row, 8).setText(option.NeStr())
      self.unitTable.item(row, 9).setText("%d" % option.PointsCost())
      self.unitTable.item(row, 10).setText(", ".join(option.ListSpecialRules()))
      
      # can it have a magical item?
      if option.UnitType() in (KUT.UT_MON, KUT.UT_WENG):
         self.unitTable.cellWidget(row, 11).setEnabled(False)
         self.unitTable.cellWidget(row, 11).setCurrentIndex(0)
      else: self.unitTable.cellWidget(row, 11).setEnabled(True)
      
      # replace unit in armylist
      newUnit = option.CreateInstance()
      self.armyList.PrimaryForce().ReplaceUnit(self._MapRowToUnitId[row], newUnit)
      self.siPointsChanged.emit(self.armyList.PrimaryForce().PointsTotal(), self.armyList.PointsLimit())
      self.SetModified()
      
   @QtCore.Slot(int)
   def UnitItemChanged(self, row):
      # update this unit
      uid = self._MapRowToUnitId[row]
      itmName = self.unitTable.cellWidget(row, 11).currentText()
      unit = self.armyList.PrimaryForce()._units[uid] 
      if itmName == "-":
         unit.SetItem(None)
      else:
         # extract item name by stripping the points cost (e.g. 'Brew of Strength (30p)')
         leftBracket = itmName.index('(')
         itmName = itmName[:leftBracket-1]
         unit.SetItem(QtGui.qApp.DataManager.ItemByName(itmName))
         
      # update unit points cost
      self.unitTable.item(row, 9).setText("%d" % unit.PointsCost())
      font = self.unitTable.item(row, 9).font()
      font.setBold( True if unit.ItemCost()>0 else False )
      self.unitTable.item(row, 9).setFont(font)
      
      self.siPointsChanged.emit(self.armyList.PrimaryForce().PointsTotal(), self.armyList.PointsLimit())
      self.SetModified()
      
   def UpdateButtons(self):
      if len(self.unitTable.selectedItems())>0:
         self.deleteUnitPb.setEnabled(True)
         self.duplicateUnitPb.setEnabled(True)
         self.optionsPb.setEnabled(True)
      else:
         self.deleteUnitPb.setEnabled(False)
         self.optionsPb.setEnabled(False)
         self.duplicateUnitPb.setEnabled(False)
         
   def UpdateRow(self, row):
      if row >= self.unitTable.rowCount():
         raise ValueError("Row number too high - does not exist!")
      
      unitid = self._MapRowToUnitId[row]
      unit = self.armyList.PrimaryForce()._units[unitid]
      
      self.unitTable.item(row, 1).setText(unit.UnitType().Name()) # unit type
      
      # size options left untouched, do nothing
      self.unitTable.item(row, 3).setText("%d" % unit.Sp())
      self.unitTable.item(row, 4).setText(unit.MeStr())
      self.unitTable.item(row, 5).setText(unit.RaStr())
      self.unitTable.item(row, 6).setText(unit.DeStr())
      self.unitTable.item(row, 7).setText(unit.AtStr())
      self.unitTable.item(row, 8).setText(unit.NeStr())
      self.unitTable.item(row, 9).setText("%d" % unit.PointsCost())
      self.unitTable.item(row, 10).setText(", ".join(unit.ListSpecialRules()))
         
   def UpdateUi(self):
      """ This is called when an army list has been set (e.g. by loading a file) and the UI elements must be updated
         to reflect its state. """
      self.armyNameLe.setText(self.armyList.Name())
      # temporarily disconnect
      self.primaryForceCb.currentIndexChanged.disconnect(self.PrimaryForceChanged)
      self.primaryForceCb.setCurrentIndex(self.primaryForceCb.findText(self.armyList._primaryForce.Choices().Name()))
      self.primaryForceCb.currentIndexChanged.connect(self.PrimaryForceChanged)
      
      self.pointsLimitSb.setValue(self.armyList.PointsLimit())
      
      units = self.armyList._primaryForce.ListUnits()
      self.unitTable.setRowCount(0)
      self.unitTable.clear()
      self.unitTable.setRowCount(len(units))
      
      for unitId in range(len(units)):
         row = unitId
         unit = units[unitId]
         self.SetRowToUnit(row, unit, unitId)
         
      self.unitTable.setHorizontalHeaderLabels(("Unit", "Type", "Size", "Sp", "Me", "Ra", "De", "At", "Ne", "Points", "Special", "Magic item", "Options"))
         
#===============================================================================
# main - entry point
#===============================================================================
def main():
   app = QtGui.QApplication(sys.argv)

   w = MainWindow()
   w.show()

   sys.exit(app.exec_())
   return

if __name__=='__main__':
   main()