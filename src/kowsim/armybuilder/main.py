# -*- coding: utf-8 -*-

# armybuilder/main.py
#===============================================================================
import os, sys
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from kowsim.kow.force import Detachment
from mvc.models import ArmyListModel
from load_data import DataManager
from views import ArmyListView, ArmyListOutputView
from command import SaveArmyListCmd, LoadArmyListCmd, PreviewArmyListCmd, ExportAsHtmlCmd
from dialogs import NewArmyListDialog
from control import ArmyListCtrl
from widgets import UnitBrowserWidget
import globals 

#===============================================================================
# MainWindow
#===============================================================================
class MainWindow(QtGui.QMainWindow):
   """ Armybuilder application main window """
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
      self.unitBrowser = UnitBrowserWidget()
      self.addDockWidget(Qt.LeftDockWidgetArea, self.unitBrowser)
      self.unitBrowser.hide()
      
      self.mdiArea = MdiArea()
      self.setCentralWidget(self.mdiArea)
      self.unitChoiceWidget = None
      
      #self.setStatusBar(QtGui.QStatusBar())
      #self.statusBar().showMessage("Ready.")
      self.setMenuBar(MainMenu())
      
      self.toolBar = QtGui.QToolBar(self)
      self.toolBar.setObjectName("ToolBar")
      self.toolBar.addAction(QtGui.QIcon(os.path.join(globals.BASEDIR,"data","icons","new.png")), "New army list", self.NewArmyList)
      self.openAction = self.toolBar.addAction(QtGui.QIcon(os.path.join(globals.BASEDIR,"data","icons","open.png")), "Open", self.OpenArmyList)
      self.saveAction = self.toolBar.addAction(QtGui.QIcon(os.path.join(globals.BASEDIR,"data","icons","save.png")), "Save", self.SaveArmyList)
      self.saveAction.setEnabled(False)
      self.toolBar.addSeparator()
      self.previewAction = self.toolBar.addAction(QtGui.QIcon(os.path.join(globals.BASEDIR,"data","icons","kghostview.png")), "Preview", self.PreviewArmyList)
      self.exportHtmlAction = self.toolBar.addAction(QtGui.QIcon(os.path.join(globals.BASEDIR,"data","icons","html.png")), "Export as HTML", self.ExportHtml)
      
      self.addToolBar(self.toolBar)
      
      #=========================================================================
      # Try to restore state from settings
      #=========================================================================
      settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
      geom = settings.value("Geometry")
      if geom: self.restoreGeometry(geom)
      
      state = settings.value("WindowState")
      if state: self.restoreState(state)
         
      
      self._InitConnections()
      
   def _InitConnections(self):
      self.menuBar().newArmyAct.triggered.connect(self.NewArmyList)
      self.menuBar().openAct.triggered.connect(self.OpenArmyList)
      self.menuBar().saveAct.triggered.connect(self.SaveArmyList)
      self.menuBar().saveAsAct.triggered.connect(self.SaveArmyListAs)
      self.menuBar().exitAct.triggered.connect(self.close)
      self.menuBar().previewAct.triggered.connect(self.PreviewArmyList)
      self.mdiArea.subWindowActivated.connect(self.CurrentWindowChanged)
      self.unitBrowser.siWasClosed.connect(self.UnitBrowserClosed)
      
   def closeEvent(self, e):
      # give each subwindow the chance to close, they might want to save first
      abortClose = False
      while len(self.mdiArea.subWindowList())>0:
         view = self.mdiArea.subWindowList()[0]
         if not view.close():
            abortClose = True
            break
      if abortClose:
         e.ignore()
      else:
         # save mainwindow settings
         settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
         settings.setValue("Geometry", self.saveGeometry())
         settings.setValue("WindowState", self.saveState())
         super(MainWindow, self).closeEvent(e)
         
   def CurrentDetachmentChanged(self):
      sub = self.mdiArea.currentSubWindow()
      if sub:
         if type(sub.widget()) != ArmyListView:
            return # just ignore when non-armylist view windows are select (such as previews)
         alView = sub.widget()
         alCtrl = alView.ctrl
         detView = alView.detachmentsTw.currentWidget()
         if detView:
            self.unitBrowser.Update(detView._model, alCtrl)
         else:
            self.unitBrowser.Update(None, None)
      else:
         self.unitBrowser.Update(None, None)
      
   def CurrentWindowChanged(self, wnd):
      if wnd: self.saveAction.setEnabled(True)
      else: self.saveAction.setEnabled(False)
      
   def ExportHtml(self):
      l = len(self.mdiArea.subWindowList())
      # somehow if there's only one subwindow it is not registered as active,
      # so do this as a workaround.
      if l == 0: return
      elif l == 1: view = self.mdiArea.subWindowList()[0].widget()
      else: view = self.mdiArea.activeSubWindow().widget()
      
      cmd = ExportAsHtmlCmd(view.ctrl.model, view)
      view.ctrl.AddAndExecute(cmd)
   
   def NewArmyList(self):
      self.mdiArea.AddArmySubWindow()
      
   def OpenArmyList(self):
      cmd = LoadArmyListCmd(self.mdiArea)
      cmd.Execute()
      
   def PreviewArmyList(self):
      sub = self.mdiArea.currentSubWindow()
      if not sub: return
      if type(sub.widget()) != ArmyListView: return
      
      cmd = PreviewArmyListCmd(sub.widget().ctrl, self.mdiArea)
      cmd.Execute()
   
   def SaveArmyList(self, saveAs=False):
      l = len(self.mdiArea.subWindowList())
      # somehow if there's only one subwindow it is not registered as active,
      # so do this as a workaround.
      if l == 0: return
      elif l == 1: view = self.mdiArea.subWindowList()[0].widget()
      else: view = self.mdiArea.activeSubWindow().widget()
      
      cmd = SaveArmyListCmd(view.ctrl.model, view, saveAs)
      view.ctrl.AddAndExecute(cmd)
      
   def SaveArmyListAs(self):
      self.SaveArmyList(saveAs=True)
      
   def UnitBrowserClosed(self):
      self.menuBar().viewUnitBrowserAct.setChecked(False)
      self.menuBar().ViewUnitBrowser(False)
   
   
#===============================================================================
# MainMenu
#===============================================================================
class MainMenu(QtGui.QMenuBar):
   """ Armybuilder application main menu """
   def __init__(self, *args):
      super(MainMenu, self).__init__(*args)
      
      QtGui.qApp.MainMenu = self # FIXME: .. this is dirty .. make a proper singleton or don't be so lazy ..
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
      
      # edit menu
      self.editMenu = self.addMenu("&Edit")
      self.undoAct = self.editMenu.addAction("&Undo")
      self.undoAct.setEnabled(False)
      self.redoAct = self.editMenu.addAction("&Redo")
      self.redoAct.setEnabled(False)
      
      # view menu
      self.viewMenu = self.addMenu("&View")
      self.previewAct = self.viewMenu.addAction("&Preview")
      self.viewMenu.addSeparator()
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
      self.viewUnitBrowserAct.triggered[bool].connect(self.ViewUnitBrowser)
   
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
         
   def ViewUnitBrowser(self, checked):
      settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
      settings.setValue("View/UnitBrowser", int(checked))
      if checked: QtGui.qApp.MainWindow.unitBrowser.show()
      else: QtGui.qApp.MainWindow.unitBrowser.hide()
      
      
#===============================================================================
# MdiArea
#===============================================================================
class MdiArea(QtGui.QMdiArea):
   """ Armybuilder application central widget, an MDI area """
   def __init__(self, *args):
      super(MdiArea, self).__init__(*args)
      self.setViewMode(QtGui.QMdiArea.TabbedView)
      self.setTabsClosable(True)
      self.setTabsMovable(True)
      #self.AddArmySubWindow()
      self.subWindowActivated.connect(QtGui.qApp.MainWindow.CurrentDetachmentChanged)
      self.currentFiles = set()
      
   def AddArmySubWindow(self, armyListModel=None):
      if armyListModel is None:
         dlg = NewArmyListDialog()
         if not (QtGui.QDialog.Accepted == dlg.exec_()):
            return
         num = len(self.subWindowList()) # number of unnamed armies
         if num==0: name = "Unnamed army"
         else: name = "Unnamed army (%d)" % (num+1)
         armyListModel = ArmyListModel(name, dlg.PointsLimit())
         armyListModel.data.AddDetachment( Detachment(dlg.PrimaryForce(), isPrimary=True) )
      
      sub = ArmyListView(ArmyListCtrl(armyListModel))
      self.addSubWindow(sub)
      sub.show() # important!
      sub.showMaximized()
      
      # connect
      sub.siRecentFilesChanged.connect(QtGui.qApp.MainMenu.UpdateRecent)
      sub.siCurrentDetachmentChanged.connect(QtGui.qApp.MainWindow.CurrentDetachmentChanged)
      
      QtGui.qApp.MainWindow.CurrentDetachmentChanged()
      return sub
   
   def AddPreviewSubWindow(self, armyListCtrl):
      #sub = ArmyMainWidget(name)
      sub = ArmyListOutputView(armyListCtrl)
      self.addSubWindow(sub)
      sub.show() # important!
      sub.showMaximized()
      return sub


#===============================================================================
# initDefaultSettings
#===============================================================================
def initDefaultSettings():
   """ Initialize default settings possibly needed before the first program start """
   # this file is in subfolder src/kowsim/armybuilder
   basedir = os.path.normpath( os.path.join( os.path.dirname(os.path.realpath(__file__)),"..", "..", "..") )
   #print basedir
   defaultSettings = [ ("Recent/NumRecent", 5),
                       ("Basedir", basedir) ]
   
   settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
   for name, value in defaultSettings:
      if not settings.value(name):
         settings.setValue(name, value)
      
         
#===============================================================================
# main - entry point
#===============================================================================
def main():
   """ Application entry point """
   app = QtGui.QApplication(sys.argv)
   initDefaultSettings()
   globals.LoadSettings()

   w = MainWindow()
   w.show()

   sys.exit(app.exec_())
   return

if __name__=='__main__':
   main()