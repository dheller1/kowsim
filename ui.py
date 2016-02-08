import sys, time, os
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from dice import RollHandler
from battlefield import BattlefieldView, RectBaseUnit
from constants import *
from load_data import DataManager

class MainWindow(QtGui.QMainWindow):
   def __init__(self):
      super(MainWindow, self).__init__()
      
      #=========================================================================
      # Load data
      #=========================================================================
      QtGui.qApp.DataManager = DataManager()
      QtGui.qApp.DataManager.LoadUnitTypes()
      QtGui.qApp.DataManager.LoadBaseSizes()
      QtGui.qApp.DataManager.LoadMarkers()
      QtGui.qApp.DataManager.LoadIcons()
      
      #=========================================================================
      # Init main window
      #=========================================================================
      self.resize(1280, 800)
      self.setWindowTitle("vbattle")
      
      #=========================================================================
      # Init child widgets and menus
      #=========================================================================
      self.setCentralWidget(MainWindowCentralWidget())
      self.setStatusBar(QtGui.QStatusBar())
      self.statusBar().showMessage("Ready.")
      self.setMenuBar(MainMenu())
      
      #self.dockWidget = ToolsDockWidget(self)
      #self.addDockWidget(Qt.TopDockWidgetArea, self.dockWidget)
      self.unitTb = UnitToolBar(self)
      self.addToolBar(self.unitTb)
      
      self.InitConnections()
      
   def InitConnections(self):
      # connect battlefield scene to status bar and text logger
      self.centralWidget().battlefieldView.scene().siStatusMessage.connect(self.HandleStatusMessage)
      self.centralWidget().battlefieldView.scene().siLogEvent.connect(self.centralWidget().chatWidget.AddHistoryItem)
      
      
      # connect battlefield scene to unit toolbar
      self.centralWidget().battlefieldView.scene().siUnitSelected.connect(self.unitTb.rotateAct.setEnabled)
      self.unitTb.rotateAct.triggered.connect(self.centralWidget().battlefieldView.scene().InitRotation)
      
   def HandleStatusMessage(self, msg):
      if len(msg)>0:
         self.statusBar().showMessage(msg)
      else:
         self.statusBar().showMessage("Ready.")
      
class MainWindowCentralWidget(QtGui.QWidget):
   def __init__(self):
      super(MainWindowCentralWidget, self).__init__()
      
      self.chatWidget = ChatWidget()
      self.battlefieldView = BattlefieldView()
      
      self.InitLayout()
      
   def InitLayout(self):
      lay = QtGui.QHBoxLayout()
      
      lay.addWidget(self.battlefieldView, stretch=1)
      lay.addWidget(self.chatWidget)
      
      self.setLayout(lay)
      

class MainMenu(QtGui.QMenuBar):
   def __init__(self):
      super(MainMenu, self).__init__()
      
      self.forcesMenu = QtGui.QMenu("&Forces")
      self.addUnitAct = QtGui.QAction("Add &unit...", self.forcesMenu)
      self.forcesMenu.addAction(self.addUnitAct)
      
      self.addMenu(self.forcesMenu)
      
      
      # connections
      self.addUnitAct.triggered.connect(self.AddUnit)
      
   def AddUnit(self):
      dlg = AddUnitDialog()
      dlg.exec_()
      if dlg.result()==QtGui.QDialog.Accepted:
         self.parent().unitToPlace = dlg.unit
         self.parent().mouseMode = MOUSE_PLACE_UNIT
         

class AddUnitDialog(QtGui.QDialog):
   def __init__(self):
      super(AddUnitDialog, self).__init__()
      
      #=========================================================================
      # member children
      #=========================================================================
      self.unit = RectBaseUnit(baseSize=(100*MM_TO_IN, 40*MM_TO_IN), formation=(5,2))
      
      self.previewGv = QtGui.QGraphicsView()
      self.previewScene = QtGui.QGraphicsScene()
      
      self.unitNameLe = QtGui.QLineEdit("Unnamed unit")
      self.unitTypeCb = QtGui.QComboBox()
      self.unitSizeCb = QtGui.QComboBox()
      self.baseSizeCb = QtGui.QComboBox()
      
      #=========================================================================
      # init self and children
      #=========================================================================
      self.setWindowTitle("Add unit...")
      
      unitTypes = QtGui.qApp.DataManager.GetUnitTypes()
      for ut in unitTypes: self.unitTypeCb.addItem(ut.typeName)
      
      curUt = unitTypes[0]
      for avS in curUt.availableSizes: self.unitSizeCb.addItem(str(avS))
      
      self.baseSizeCb.addItems(["20x20", "25x25", "25x50 (Cav.)", "40x40 (L.Inf.)", "50x50 (L.Cav.)", "50x100 (Chariot)", "75x75 (Monster)", "Custom..."])
      
      self.previewGv.setMinimumSize(200,80)
      self.previewGv.setEnabled(False)
      self.previewGv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      self.previewGv.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      self.previewScene.addItem(self.unit)
      self.previewScene.setBackgroundBrush(QtGui.QColor(121,217,82))
      
      self.previewGv.setScene(self.previewScene)
      self.previewGv.scale(20,20)
      
      self.acceptBtn = QtGui.QPushButton("Add >>")
      self.cancelBtn = QtGui.QPushButton("Cancel")
      
      
      #=========================================================================
      # Init layout
      #=========================================================================
      lay = QtGui.QVBoxLayout()
      mainLay = QtGui.QHBoxLayout()
      btnLay = QtGui.QHBoxLayout()
      
      # general group box
      genGrpBox = QtGui.QGroupBox("General")
      genLay = QtGui.QGridLayout()
      
      # unit name
      genLay.addWidget(QtGui.QLabel("Unit name:"), 0, 0)
      genLay.addWidget(self.unitNameLe, 0, 1)
      
      # unit type
      genLay.addWidget(QtGui.QLabel("Unit type:"), 1, 0)
      genLay.addWidget(self.unitTypeCb, 1, 1)
      
      # unit size
      genLay.addWidget(QtGui.QLabel("Size:"), 2, 0)
      genLay.addWidget(self.unitSizeCb, 2, 1)
      
      # base size
      genLay.addWidget(QtGui.QLabel("Base size [mm]:"), 3, 0)
      genLay.addWidget(self.baseSizeCb, 3, 1)
      
      
      #=========================================================================
      # ASSEMBLE LAYOUTS
      #=========================================================================
      genGrpBox.setLayout(genLay)
      mainLay.addWidget(genGrpBox)
      mainLay.addWidget(self.previewGv, stretch=1)
      
      btnLay.addWidget(self.cancelBtn)
      btnLay.addStretch(1)
      btnLay.addWidget(self.acceptBtn)
      
      lay.addLayout(mainLay)
      lay.addLayout(btnLay)
      
      self.setLayout(lay)
      
      #=========================================================================
      # INIT CONNECTIONS
      #=========================================================================
      self.unitTypeCb.currentIndexChanged.connect(self.UpdateSizeOptions)
      self.unitSizeCb.currentIndexChanged.connect(self.UnitSettingsChanged)
      self.baseSizeCb.currentIndexChanged.connect(self.UnitSettingsChanged)
      
      self.cancelBtn.clicked.connect(self.reject)
      self.acceptBtn.clicked.connect(self.accept)
      
      #=========================================================================
      # FINAL INITIALIZATION
      #=========================================================================
      self.unitNameLe.selectAll()
      self.unitNameLe.setFocus()

      
   def UnitSettingsChanged(self):
      if self.baseSizeCb.currentText() == "" or self.unitSizeCb.currentText() == "":
         return # correct baseSize/unitSize not yet selected, but it will be shortly, just do nothing for now.
      
      singleBaseX, singleBaseY = [int(size) for size in self.baseSizeCb.currentText().split(' ')[0].split('x')]
      
      unitType = QtGui.qApp.DataManager.UnitTypeByName( self.unitTypeCb.currentText() )
      
      unitSize = None
      for avS in unitType.availableSizes:
         if self.unitSizeCb.currentText() == str(avS):
            unitSize = avS
            break
      if unitSize is None: raise ValueError("Invalid unit size selected! '%s'" % self.unitSizeCb.currentText())
      
      formation = unitSize.formation
      unitWidth = singleBaseX * formation[0]
      unitDepth = singleBaseY * formation[1]
      
      self.previewScene.removeItem(self.unit)
      del self.unit      
      self.unit = RectBaseUnit(name = self.unitNameLe.text(), baseSize = (unitWidth * MM_TO_IN, unitDepth * MM_TO_IN), formation=formation)
      
      if unitWidth >= 240 or unitDepth >= 120:
         self.previewGv.setTransform(QtGui.QTransform().scale(10,10))
      else: self.previewGv.setTransform(QtGui.QTransform().scale(20,20))
         
      self.previewScene.addItem(self.unit)
      self.previewGv.ensureVisible(self.unit)
         
   def UpdateSizeOptions(self):
      curUtName = self.unitTypeCb.currentText()
      curUt = QtGui.qApp.DataManager.UnitTypeByName(curUtName)
      
      self.unitSizeCb.clear()
      for avS in curUt.availableSizes:
         self.unitSizeCb.addItem(str(avS))
         
      self.baseSizeCb.clear()
      for avBs in curUt.availableBaseSizes:
         self.baseSizeCb.addItem("%dx%d" % (avBs[0], avBs[1]))
      
      self.UnitSettingsChanged()
      
      
class ChatWidget(QtGui.QWidget):
   _TimestampCss = 'color:#999999;'
   _ErrorCss = 'color:#a0a0a0;font-weight:bold;font-style:italic;'
   
   _SupportedCommands = ("r", "h")
   
   def __init__(self):
      super(ChatWidget, self).__init__()
      
      lay = QtGui.QVBoxLayout()
      
      self.chatHistory = QtGui.QTextBrowser()
      self.chatHistory.setHtml("")
      self.textField = QtGui.QLineEdit()
      
      lay.addWidget(self.chatHistory)
      lay.addWidget(self.textField)
      
      self.setLayout(lay)
      
      self.InitConnections()
      
   def AddHistoryItem(self, text):
      # add timestamp
      timestamp = "<span style=\"%s\">" % ChatWidget._TimestampCss + time.strftime("%H:%M:%S" + "</span> ")
      self.chatHistory.append( timestamp + str(text) )
      
   def InitConnections(self):
      self.textField.returnPressed.connect(self.Submit)
      
   def PrintError(self, text):
      self.chatHistory.append( "<span style=\"%s\">" % ChatWidget._ErrorCss + text + "</span>")
      
   def Submit(self):
      text = self.textField.text()
      self.textField.clear()
      
      if text == "": return # empty?
      
      elif not text.startswith("/"): # no command?
         # add to chat history
         self.AddHistoryItem( text )
         # scroll to last item
         #self.chatHistory.scrollToItem( self.chatHistory.item(self.chatHistory.count()-1) ) 
         
      else: # command
         commandText = text[1:].lower() # no case sensitivity
         
         command = commandText.split()[0]
         if command not in ChatWidget._SupportedCommands:
            self.PrintError("Error: Unknown command '%s'. Type /h for help." % command)
            return
            
         elif command == "r": # Roll
            try:
               rollString = commandText[1:].strip()
               self.AddHistoryItem("<i>%s</i>" % text)
               rollHndlr = RollHandler()
               rollHndlr.InterpretString(rollString)
      
               results = rollHndlr.Roll()
               
               #if rollHndlr.numDice < 10 and len(rollHndlr.individualRolls) <= 1:
               self.AddHistoryItem(rollHndlr.RollModeToString() + " " + rollHndlr.AllResultsToString())
            except ValueError as e:
               self.PrintError(str(e))
               
         elif command == "h": # Help
            helpText = """ <u>Help</u><br> You can use this box to chat with other players or for some functionality in support of the game.<br>
             To send a chat message, simply type in any text.\n Supported commands:<br>   - /r Roll some (virtual) dice. """
            self.AddHistoryItem("<i>%s</i>" % helpText)

#===============================================================================
# UnitToolbar
#   Customized QToolBar containing toolbuttons for the most basic program
#   controls, such as moving/rotating units, declaring attacks, switching
#   phases, etc.
#===============================================================================
class UnitToolBar(QtGui.QToolBar):
   def __init__(self, parent=None):
      super(UnitToolBar, self).__init__("Unit controls", parent)
      
      # add tool buttons
      self.rotateAct = self.addAction(QtGui.qApp.DataManager.IconByName("ICN_ROTATE_UNIT"), "[R]otate unit")
      self.rotateAct.setEnabled(False) # enable only when a unit is selected
      
      #self.rotateBtn = QtGui.QToolButton(self.widget)
      #self.rotateBtn.setIcon(rotateIcn)
      #self.rotateBtn.setIconSize(QtCore.QSize(48, 48))
      
      