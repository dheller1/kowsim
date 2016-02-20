# -*- coding: utf-8 -*-

# armybuilder/main.py
#===============================================================================
import sys
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from ..kow.force import KowArmyList
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
      QtGui.qApp.DataManager.LoadForces()
      
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
# ArmyMainWidget
#===============================================================================
class ArmyMainWidget(QtGui.QWidget):
   def __init__(self, name="Unnamed army"):
      super(ArmyMainWidget, self).__init__()
      
      self.changedSinceSave = True
      
      self.setMinimumSize(400,300)
      self.setWindowTitle((name + "*"))
      self.armyList = KowArmyList(name, points=2000)
      
      #=========================================================================
      # child widgets
      #=========================================================================
      self.armyNameLe = QtGui.QLineEdit(name)
      self.primaryForceCb = QtGui.QComboBox()
      for f in QtGui.qApp.DataManager.ListForces():
         self.primaryForceCb.addItem(f.Name())
         
      self.pointsLimitSb = QtGui.QSpinBox()
      self.pointsLimitSb.setRange(1, 1000000)
      self.pointsLimitSb.setValue(2000)
      self.pointsLimitSb.setSingleStep(50)
      
      self.armyNameLe.selectAll()
      self.unitTable = QtGui.QTableWidget()
      self.unitTable.setColumnCount(12)
      self.unitTable.setHorizontalHeaderLabels(("Unit", "Type", "Size", "Sp", "Me", "Ra", "De", "At", "Ne", "Points"))
      
      self.addUnitPb = QtGui.QPushButton("&Add")
      
      #=========================================================================
      # group boxes
      #=========================================================================
      self.generalGb = QtGui.QGroupBox("General")
      self.unitGb = QtGui.QGroupBox("Units")
      
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
      
      mainlay = QtGui.QVBoxLayout()
      mainlay.addWidget(self.generalGb)
      mainlay.addWidget(self.unitGb)
      self.setLayout(mainlay)
      
      #=========================================================================
      # connections
      #=========================================================================
      self.armyNameLe.textChanged.connect(self.DataChanged)
      self.addUnitPb.clicked.connect(self.AddUnit)
      self.primaryForceCb.currentIndexChanged.connect(self.PrimaryForceChanged)
      
      #=========================================================================
      # Final init, full update
      #=========================================================================
      self.selectedForce = QtGui.qApp.DataManager.ForceByName(self.primaryForceCb.currentText())
      self.PrimaryForceChanged()
      
   def AddUnit(self):
      rowNum = self.unitTable.rowCount()
      self.unitTable.insertRow(rowNum)
      
      # cell items
      cb = QtGui.QComboBox()
      for unit in self.selectedForce.ListGroups():
         cb.addItem(unit.Name())
      self.unitTable.setCellWidget(rowNum, 0, cb)
      
      self.unitTable.setItem(rowNum, 1, QtGui.QTableWidgetItem("")) # unit type
      cbOpt = QtGui.QComboBox()
      self.unitTable.setCellWidget(rowNum, 2, cbOpt) # size type
      
      for col in range(3, 12+1): # profile stats
         self.unitTable.setItem(rowNum, col, QtGui.QTableWidgetItem(""))
      
      # connections
      mapper = QtCore.QSignalMapper(self) # set mapping to identify combobox by its row
      mapper.setMapping(cb, rowNum)
      cb.currentIndexChanged.connect(mapper.map)
      
      mapperOpt = QtCore.QSignalMapper(self)
      mapperOpt.setMapping(cbOpt, rowNum)
      cbOpt.currentIndexChanged.connect(mapperOpt.map)
      
      mapper.mapped[int].connect(self.UnitGroupChanged)
      mapperOpt.mapped[int].connect(self.UnitOptionChanged)
      self.UnitGroupChanged(rowNum)
      
   def DataChanged(self):
      self.changedSinceSave = True
      
      name = self.armyNameLe.text()
      self.armyList.SetName(name)
      self.setWindowTitle("%s*" % name)
   
   def PrimaryForceChanged(self):
      pfn = self.primaryForceCb.currentText()
      pf = QtGui.qApp.DataManager.ForceByName(pfn)
      self.armyList.SetPrimaryForce(pf)
   
   @QtCore.Slot(int)
   def UnitGroupChanged(self, row):
      # update this row
      grpname = unicode( self.unitTable.cellWidget(row, 0).currentText() )
      grp = self.armyList.PrimaryForce().GroupByName(grpname)
      
      option = grp.Default()
      self.unitTable.item(row, 1).setText(option.UnitType().Name()) # unit type
      
      # size options
      self.unitTable.cellWidget(row, 2).clear()
      for o in grp.ListOptions():
         self.unitTable.cellWidget(row, 2).addItem(o.SizeType().Name())
         
      self.unitTable.item(row, 3).setText("%d" % option.Sp())
      self.unitTable.item(row, 3).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 4).setText(option.MeStr())
      self.unitTable.item(row, 4).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 5).setText(option.RaStr())
      self.unitTable.item(row, 5).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 6).setText(option.DeStr())
      self.unitTable.item(row, 6).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 7).setText(option.AtStr())
      self.unitTable.item(row, 7).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 8).setText(option.NeStr())
      self.unitTable.item(row, 8).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 9).setText("%d" % option.PointsCost())
      self.unitTable.item(row, 9).setTextAlignment(Qt.AlignCenter)
   
   @QtCore.Slot(int)
   def UnitOptionChanged(self, row):
      # update this row
      grpname = unicode( self.unitTable.cellWidget(row, 0).currentText() )
      grp = self.armyList.PrimaryForce().GroupByName(grpname)
      
      optTxt = self.unitTable.cellWidget(row, 2).currentText()
      if optTxt == "": return # this can occur when the unit group has been changed but the option combo box has not been updated yet. do nothing
      
      option = grp.OptionByName(optTxt)
      
      self.unitTable.item(row, 1).setText(option.UnitType().Name()) # unit type
      
      # size options left untouched, do nothing
      self.unitTable.item(row, 3).setText("%d" % option.Sp())
      self.unitTable.item(row, 3).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 4).setText(option.MeStr())
      self.unitTable.item(row, 4).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 5).setText(option.RaStr())
      self.unitTable.item(row, 5).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 6).setText(option.DeStr())
      self.unitTable.item(row, 6).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 7).setText(option.AtStr())
      self.unitTable.item(row, 7).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 8).setText(option.NeStr())
      self.unitTable.item(row, 8).setTextAlignment(Qt.AlignCenter)
      self.unitTable.item(row, 9).setText("%d" % option.PointsCost())
      self.unitTable.item(row, 9).setTextAlignment(Qt.AlignCenter)

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