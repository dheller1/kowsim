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
from kowsim.armybuilder.command import LoadArmyListCmd


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
      
      self._InitConnections()
      
   def _InitConnections(self):
      self.menuBar().newArmyAct.triggered.connect(self.NewArmyList)
      self.menuBar().openAct.triggered.connect(self.OpenArmyList)
      self.menuBar().saveAct.triggered.connect(self.SaveArmyList)
      self.menuBar().saveAsAct.triggered.connect(self.SaveArmyListAs)
      self.menuBar().exitAct.triggered.connect(self.close)
      self.mdiArea.subWindowActivated.connect(self.CurrentWindowChanged)
      
   def closeEvent(self, e):
      abortClose = False
      
      while len(self.mdiArea.subWindowList())>0:
         view = self.mdiArea.subWindowList()[0]
         if not view.close():
            abortClose = True
            break
      if abortClose:
         e.ignore()
      else:
         super(MainWindow, self).closeEvent(e)
         
      
   def CurrentWindowChanged(self, wnd):
      if wnd: self.saveAction.setEnabled(True)
      else: self.saveAction.setEnabled(False)
   
   def NewArmyList(self):
      self.mdiArea.AddArmySubWindow()
      
   def OpenArmyList(self):
      filenames, filter = QtGui.QFileDialog.getOpenFileNames(self, "Open army list(s)", "..", "Army lists (*.lst);;All files (*.*)")
      
      for f in filenames:
         cmd = LoadArmyListCmd(self.mdiArea)
         cmd.Execute(f)
      
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
      
   def AddArmySubWindow(self, armyList=None):
      if armyList is None:
         dlg = NewArmyListDialog()
         if not (QtGui.QDialog.Accepted == dlg.exec_()):
            return
         num = len(self.subWindowList()) # number of unnamed armies
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