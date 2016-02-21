# -*- coding: utf-8 -*-

# armybuilder/main.py
#===============================================================================
import os, sys
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from ..kow.force import KowArmyList, KowForce
from ..kow.unit import KowUnitProfile
from load_data import DataManager


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
      
      self.InitConnections()
      
   def InitConnections(self):
      self.menuBar().newArmyAct.triggered.connect(self.mdiArea.AddArmySubWindow)
      self.menuBar().exitAct.triggered.connect(self.close)
   
#===============================================================================
# MainMenu
#===============================================================================
class MainMenu(QtGui.QMenuBar):
   def __init__(self, *args):
      super(MainMenu, self).__init__(*args)
      
      self.fileMenu = self.addMenu("&File")
      self.newArmyAct = self.fileMenu.addAction("&New army")
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
      self.AddArmySubWindow()
      
   def AddArmySubWindow(self):
      num = len(self.subWindowList())
      if num==0: name = "Unnamed army"
      else: name = "Unnamed army (%d)" % (num+1)
      sub = ArmyMainWidget(name)
      self.addSubWindow(sub)
      sub.show() # important!
      sub.showMaximized()
      
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
            
#===============================================================================
# ArmyMainWidget
#===============================================================================
class ArmyMainWidget(QtGui.QWidget):
   siPointsChanged = QtCore.Signal(int, int)
   
   def __init__(self, name="Unnamed army"):
      super(ArmyMainWidget, self).__init__()
      
      self.changedSinceSave = True
      
      self.setMinimumSize(400,300)
      self.setWindowTitle(("*" + name))
      self.armyList = KowArmyList(name, points=2000)
      
      self._MapRowToUnitId = {}
      self._MapUnitIdToRow = {}
      
      #=========================================================================
      # child widgets
      #=========================================================================
      self.armyNameLe = QtGui.QLineEdit(name)
      self.primaryForceCb = QtGui.QComboBox()
      for f in QtGui.qApp.DataManager.ListForceChoices():
         self.primaryForceCb.addItem(f.Name())
         
      self.pointsLimitSb = QtGui.QSpinBox()
      self.pointsLimitSb.setRange(1, 1000000)
      self.pointsLimitSb.setValue(2000)
      self.pointsLimitSb.setSingleStep(50)
      
      self.armyNameLe.selectAll()
      self.unitTable = QtGui.QTableWidget()
      self.unitTable.setColumnCount(12)
      self.unitTable.verticalHeader().hide()
      self.unitTable.setHorizontalHeaderLabels(("Unit", "Type", "Size", "Sp", "Me", "Ra", "De", "At", "Ne", "Points", "Special", "Options"))
      colWidths = [170, 90, 80, 30, 30, 30, 30, 30, 45, 45, 350, 150]
      for i in range(len(colWidths)):
         self.unitTable.setColumnWidth(i, colWidths[i])
            
      self.addUnitPb = QtGui.QPushButton("&Add")
      
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
      genlay.addWidget(QtGui.QLabel("Primary force:"), row, 0)
      genlay.addWidget(self.primaryForceCb, row, 1)
      row += 1
      genlay.addWidget(QtGui.QLabel("Points limit:"), row, 0)
      genlay.addWidget(self.pointsLimitSb, row, 1)
      row += 1
      self.generalGb.setLayout(genlay)
      
      self.unitGb.setLayout(QtGui.QVBoxLayout())
      self.unitGb.layout().addWidget(self.unitTable)
      unitButtonsLay = QtGui.QHBoxLayout()
      unitButtonsLay.addWidget(self.addUnitPb)
      self.unitGb.layout().addLayout(unitButtonsLay)
      
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
      self.primaryForceCb.currentIndexChanged.connect(self.PrimaryForceChanged)
      
      self.siPointsChanged.connect(self.validationWdg.UpdateTotalPoints)
      
      #=========================================================================
      # Final init, full update
      #=========================================================================
      self.PrimaryForceChanged()
      
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
      
      for col in (1, 3, 4, 5, 6, 7, 8, 9, 10, 11): # profile stats
         self.unitTable.setItem(rowNum, col, QtGui.QTableWidgetItem(""))
         self.unitTable.item(rowNum, col).setFlags(self.unitTable.item(rowNum, col).flags() ^ Qt.ItemIsEditable) # remove editable flag
         if col not in (10, 11): self.unitTable.item(rowNum, col).setTextAlignment(Qt.AlignCenter)
      
      # connections
      mapper = QtCore.QSignalMapper(self) # set mapping to identify combobox by its row
      mapper.setMapping(cb, rowNum)
      cb.currentIndexChanged.connect(mapper.map)
      
      mapperOpt = QtCore.QSignalMapper(self)
      mapperOpt.setMapping(cbOpt, rowNum)
      cbOpt.currentIndexChanged.connect(mapperOpt.map)
      
      mapper.mapped[int].connect(self.UnitGroupChanged)
      mapperOpt.mapped[int].connect(self.UnitOptionChanged)
      
      # register a default unit in armyList and store its index in the armyList._units array
      index = self.armyList.PrimaryForce().AddUnit(KowUnitProfile())
      self._MapRowToUnitId[rowNum] = index
      self._MapUnitIdToRow[index] = rowNum
      
      # update everything
      self.UnitGroupChanged(rowNum)
      
   def DataChanged(self):
      self.changedSinceSave = True
      
      name = self.armyNameLe.text()
      self.armyList.SetName(name)
      self.setWindowTitle("*%s" % name)
   
   def PrimaryForceChanged(self):
      #if (self.unitTable.rowCount()>0):
      #   if QtGui.QMessageBox.Yes != QtGui.QMessageBox.warning(self, "Switch primary force", "This will delete all current units.<br />Are you sure?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel):
      #      self.primaryForceCb.setCurrentIndex(self.primaryForceCb.findText(self.armyList.PrimaryForce().Choices().Name()))
      #      return
      
      #self.unitTable.setRowCount(0)
      pfn = self.primaryForceCb.currentText()
      pfc = QtGui.qApp.DataManager.ForceChoicesByName(pfn)
      self.armyList.SetPrimaryForce(KowForce(pfc))
   
   @QtCore.Slot(int)
   def UnitGroupChanged(self, row):
      # update this row
      grpname = unicode( self.unitTable.cellWidget(row, 0).currentText() )
      grp = self.armyList.PrimaryForce().Choices().GroupByName(grpname)
      
      option = grp.Default()
      self.unitTable.item(row, 1).setText(option.UnitType().Name()) # unit type
      
      # size options
      self.unitTable.cellWidget(row, 2).clear()
      for o in grp.ListOptions():
         self.unitTable.cellWidget(row, 2).addItem(o.SizeType().Name())
         
      self.unitTable.item(row, 3).setText("%d" % option.Sp())
      self.unitTable.item(row, 4).setText(option.MeStr())
      self.unitTable.item(row, 5).setText(option.RaStr())
      self.unitTable.item(row, 6).setText(option.DeStr())
      self.unitTable.item(row, 7).setText(option.AtStr())
      self.unitTable.item(row, 8).setText(option.NeStr())
      self.unitTable.item(row, 9).setText("%d" % option.PointsCost())
      self.unitTable.item(row, 10).setText(", ".join(option.SpecialRules()))
      
      # replace unit in armylist
      self.armyList.PrimaryForce().ReplaceUnit(self._MapRowToUnitId[row], option)
      self.siPointsChanged.emit(self.armyList.PrimaryForce().PointsTotal(), self.armyList.PointsLimit())
      
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
      self.unitTable.item(row, 10).setText(", ".join(option.SpecialRules()))
      
      # replace unit in armylist
      self.armyList.PrimaryForce().ReplaceUnit(self._MapRowToUnitId[row], option)
      self.siPointsChanged.emit(self.armyList.PrimaryForce().PointsTotal(), self.armyList.PointsLimit())
      
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