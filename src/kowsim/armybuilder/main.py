# -*- coding: utf-8 -*-

# armybuilder/main.py
#===============================================================================
import os, sys
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from ..kow.force import ArmyList, Detachment
from load_data import DataManager
from views import ArmyListView
from command import SaveArmyListCmd, LoadArmyListCmd
from dialogs import NewArmyListDialog
from kowsim.armybuilder.command import PreviewArmyListCmd
from kowsim.armybuilder.views import ArmyListOutputView
from kowsim.armybuilder.widgets import UnitBrowserWidget


#===============================================================================
# MainWindow
#===============================================================================
class MainWindow(QtGui.QMainWindow):
   def __init__(self):
      super(MainWindow, self).__init__()
      QtGui.qApp.MainWindow = self # this is dirty .. make a proper singleton or don't be so lazy ..
      
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
      self.unitBrowser = UnitBrowserWidget(None)
      self.addDockWidget(Qt.LeftDockWidgetArea, self.unitBrowser)
      self.unitBrowser.hide()
      
      self.mdiArea = MdiArea()
      self.setCentralWidget(self.mdiArea)
      self.unitChoiceWidget = None
      
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
      self.menuBar().previewAct.triggered.connect(self.PreviewArmyList)
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
         
   def CurrentDetachmentChanged(self):
      sub = self.mdiArea.currentSubWindow()
      if sub:
         if type(sub.widget()) != ArmyListView:
            return # just ignore when non-armylist view windows are select (such as previews)
         detView = sub.widget().detachmentsTw.currentWidget()
         if detView:
            choices = detView._model.Choices()
            self.unitBrowser.Update(choices)
         else:
            self.unitBrowser.Update(None)
      else:
         self.unitBrowser.Update(None)
      
   def CurrentWindowChanged(self, wnd):
      if wnd: self.saveAction.setEnabled(True)
      else: self.saveAction.setEnabled(False)
   
   def NewArmyList(self):
      self.mdiArea.AddArmySubWindow()
      
   def OpenArmyList(self):
      cmd = LoadArmyListCmd(self.mdiArea)
      cmd.Execute()
      
   def PreviewArmyList(self):
      sub = self.mdiArea.currentSubWindow()
      if not sub: return
      if type(sub.widget()) != ArmyListView: return
      
      armylist = sub.widget()._model
      cmd = PreviewArmyListCmd(self.mdiArea)
      cmd.Execute(armylist)
   
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
      
      QtGui.qApp.MainMenu = self # this is dirty .. make a proper singleton or don't be so lazy ..
      self.recentActs = []
      
      # file menu
      self.fileMenu = self.addMenu("&File")
      self.newArmyAct = self.fileMenu.addAction("&New army")
      self.newArmyAct.setShortcut("Ctrl+N")
      self.openAct = self.fileMenu.addAction("&Open file...")
      self.fileMenu.addSeparator()
      self.openAct.setShortcut("Ctrl+O")
      self.saveAct = self.fileMenu.addAction("&Save")
      self.saveAct.setShortcut("Ctrl+S")
      self.saveAsAct = self.fileMenu.addAction("Save &as...")
      self.saveAsAct.setShortcut("Ctrl+Shift+S")
      self.fileMenu.addSeparator()
      self.recentSep = self.fileMenu.addSeparator()
      self.UpdateRecent()
      self.exitAct = self.fileMenu.addAction("&Exit")
      
      # army list menu
      self.armyMenu = self.addMenu("&Army list")
      self.previewAct = self.armyMenu.addAction("&Preview")
      
      # view menu
      self.viewMenu = self.addMenu("&View")
      self.viewUnitBrowserAct = self.viewMenu.addAction("&Unit browser")
      self.viewUnitBrowserAct.setCheckable(True)
      
      # init from settings
      settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
      showUnitBrowser = bool(settings.value("View/UnitBrowser"))
      if showUnitBrowser:
         self.viewUnitBrowserAct.setChecked(True)
         QtGui.qApp.MainWindow.unitBrowser.show()
      
      self._initConnections()
   
   def _initConnections(self):
      self.viewUnitBrowserAct.triggered[bool].connect(self.ViewUnitBrowserTriggered)
   
   def OpenRecent(self):
      sender = self.sender()
      filename = sender.filename
      cmd = LoadArmyListCmd(QtGui.qApp.MainWindow.mdiArea)
      cmd.Execute(filename)
      
   def UpdateRecent(self):
      settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
      numRecent = int(settings.value("Recent/NumRecent"))
      
      for act in self.recentActs:
         if act in self.fileMenu.actions():
            self.fileMenu.removeAction(act)
      
      self.recentActs = []
      for i in range(numRecent):
         filename = settings.value("Recent/%d" % (i+1))
         if filename is None:
            break
         basename = os.path.basename(filename)
         act = QtGui.QAction("%s" % (basename), self.fileMenu)
         act.setToolTip(filename)
         act.filename = filename
         act.triggered.connect(self.OpenRecent)
         self.fileMenu.insertAction(self.recentSep, act)
         self.recentActs.append(act)
         
   def ViewUnitBrowserTriggered(self, checked):
      settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
      settings.setValue("View/UnitBrowser", int(checked))
      if checked: QtGui.qApp.MainWindow.unitBrowser.show()
      else: QtGui.qApp.MainWindow.unitBrowser.hide()
      
      
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
      self.subWindowActivated.connect(QtGui.qApp.MainWindow.CurrentDetachmentChanged)
      
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
      
      # connect
      sub.siRecentFilesChanged.connect(QtGui.qApp.MainMenu.UpdateRecent)
      sub.siCurrentDetachmentChanged.connect(QtGui.qApp.MainWindow.CurrentDetachmentChanged)
      
      QtGui.qApp.MainWindow.CurrentDetachmentChanged()
      return sub
   
   def AddPreviewSubWindow(self, armyList):
      #sub = ArmyMainWidget(name)
      sub = ArmyListOutputView(armyList)
      self.addSubWindow(sub)
      sub.show() # important!
      sub.showMaximized()
      return sub


#===============================================================================
# initDefaultSettings
#===============================================================================
def initDefaultSettings():
   defaultSettings = [ ("Recent/NumRecent", 5)
                      ]
   
   settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
   for name, value in defaultSettings:
      if not settings.value(name):
         settings.setValue(name, value)
      
         
#===============================================================================
# main - entry point
#===============================================================================
def main():
   app = QtGui.QApplication(sys.argv)
   initDefaultSettings()

   w = MainWindow()
   w.show()

   sys.exit(app.exec_())
   return

if __name__=='__main__':
   main()