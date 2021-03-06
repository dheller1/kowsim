# -*- coding: utf-8 -*-

import sys, time, os
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from dice import RollHandler
from battlefield import BattlefieldView, RectBaseUnit
from constants import *
from load_data import DataManager
from game import GameManager
from terrain import TerrainGraphicsItem, TerrainTemplate

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
      QtGui.qApp.DataManager.LoadTerrain()
      
      #=========================================================================
      # Init game manager
      #=========================================================================
      QtGui.qApp.GameManager = GameManager()
      
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
      
      # Forces
      self.forcesMenu = QtGui.QMenu("&Forces")
      self.addUnitAct = QtGui.QAction("Add &unit...", self.forcesMenu)
      self.forcesMenu.addAction(self.addUnitAct)
      
      # Battlefield
      self.bfMenu = QtGui.QMenu("&Battlefield")
      self.addTerrainAct = QtGui.QAction("Add &terrain...", self.bfMenu)
      self.bfMenu.addAction(self.addTerrainAct)
      
      
      self.addMenu(self.forcesMenu)
      self.addMenu(self.bfMenu)
      
      
      # connections
      self.addUnitAct.triggered.connect(self.AddUnit)
      self.addTerrainAct.triggered.connect(self.AddTerrain)
      
   def AddUnit(self):
      scene = self.parent().centralWidget().battlefieldView.scene()
      dlg = AddUnitDialog()
      dlg.exec_()
      if dlg.result()==QtGui.QDialog.Accepted:
         scene.unitToPlace = dlg.unit
         scene.addItem(dlg.unit) # add instantly but hide it first
         dlg.unit.hide()
         dlg.unit.setOpacity(0.5)
         scene.siStatusMessage.emit("Placing %s." % dlg.unit.name)
         scene.mouseMode = MOUSE_PLACE_UNIT
         
   def AddTerrain(self):
      scene = self.parent().centralWidget().battlefieldView.scene()
      dlg = AddTerrainDialog()
      dlg.exec_()
      if dlg.result()==QtGui.QDialog.Accepted:
         scene.terrainToPlace = dlg.previewItem
         scene.addItem(dlg.previewItem) # add instantly but hide it first
         dlg.previewItem.hide()
         dlg.previewItem.setOpacity(0.5)
         scene.siStatusMessage.emit("Placing %s." % dlg.previewItem.name)
         scene.mouseMode = MOUSE_PLACE_TERRAIN
   
class AddTerrainDialog(QtGui.QDialog):
   def __init__(self):
      super(AddTerrainDialog, self).__init__()
      
      self.nameHasBeenChanged = False
      
      #=========================================================================
      # member children
      #=========================================================================
      self.previewGv = QtGui.QGraphicsView()
      self.previewScene = QtGui.QGraphicsScene()
      
      self.resourceCb = QtGui.QComboBox()
      self.movementTypeCb = QtGui.QComboBox()
      self.widthLe = QtGui.QLineEdit()
      self.heightLe = QtGui.QLineEdit()
      for le in self.widthLe, self.heightLe:
         le.setFixedWidth(28)
         le.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("\d{0,}\.\d{0,}")))
      self.lockRatioCb = QtGui.QCheckBox("lock ratio")
      self.lockRatioCb.setChecked(True)
      
      self.nameLe = QtGui.QLineEdit()
      
           
      #=========================================================================
      # init self and children
      #=========================================================================
      self.setWindowTitle("Add terrain...")
      
      trnResources = QtGui.qApp.DataManager.ListTerrainResources()
      for t in trnResources:
         self.resourceCb.addItem(t)
         
      for mtype in TerrainTemplate.MOVEMENT_TYPES:
         self.movementTypeCb.addItem(mtype.text)
      
      self.previewGv.setMinimumSize(320,240)
      self.previewGv.setEnabled(False)
      self.previewGv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      self.previewGv.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      #self.previewScene.addItem(self.unit)
      self.previewScene.setBackgroundBrush(QtGui.QColor(121,217,82))
      
      self.previewGv.setScene(self.previewScene)
      self.previewGv.scale(20,20)
      
      self.cancelBtn = QtGui.QPushButton("Cancel")
      self.acceptBtn = QtGui.QPushButton("Add >>")
      self.acceptBtn.setDefault(True)
      
      
      #=========================================================================
      # Init layout
      #=========================================================================
      lay = QtGui.QVBoxLayout()
      mainLay = QtGui.QGridLayout()
      btnLay = QtGui.QHBoxLayout()
      
      # dimensions sub laoyut
      dimLay = QtGui.QHBoxLayout()
      dimLay.addWidget(self.widthLe)
      dimLay.addWidget(QtGui.QLabel("x"))
      dimLay.addWidget(self.heightLe)
      dimLay.addWidget(self.lockRatioCb)
      
      # general group box
      genGrpBox = QtGui.QGroupBox("General")
      genLay = QtGui.QGridLayout()
      
      row = 0
      # name
      genLay.addWidget(QtGui.QLabel("Name:"), row, 0)
      genLay.addWidget(self.nameLe, row, 1)
      row+=1
      
      # template
      genLay.addWidget(QtGui.QLabel("Template:"), row, 0)
      genLay.addWidget(self.resourceCb, row, 1)
      row+=1
      
      # movement
      genLay.addWidget(QtGui.QLabel("Movement:"), row, 0)
      genLay.addWidget(self.movementTypeCb, row, 1)
      row+=1
      
      # size
      genLay.addWidget(QtGui.QLabel("Size [in]:"), row, 0)
      genLay.addLayout(dimLay, row, 1)
      row+=1
      
      
      #=========================================================================
      # ASSEMBLE LAYOUTS
      #=========================================================================
      genGrpBox.setLayout(genLay)
      mainLay.addWidget(genGrpBox, 0, 0)
      mainLay.addWidget(self.previewGv, 0, 1, 2, 1, stretch=1)
      
      btnLay.addWidget(self.cancelBtn)
      btnLay.addStretch(1)
      btnLay.addWidget(self.acceptBtn)
      
      lay.addLayout(mainLay)
      lay.addLayout(btnLay)
      
      self.setLayout(lay)
      
      #=========================================================================
      # INIT CONNECTIONS
      #=========================================================================
      self.cancelBtn.clicked.connect(self.reject)
      self.acceptBtn.clicked.connect(self.accept)
      
      self.widthLe.textEdited.connect(self.WidthChanged)
      self.heightLe.textEdited.connect(self.HeightChanged)
      self.lockRatioCb.toggled.connect(self.SetLock)
      self.movementTypeCb.currentIndexChanged.connect(self.MovementTypeChanged)
      self.nameLe.textEdited.connect(self.NameChanged)
      self.resourceCb.currentIndexChanged.connect(self.TemplateChanged)
      
      #=========================================================================
      # FINAL INITIALIZATION
      #=========================================================================
      self.TemplateChanged()
      self.nameLe.selectAll()
      self.nameLe.setFocus()
      
   def MovementTypeChanged(self):
      mvtText = self.movementTypeCb.currentText()
      mvt = TerrainTemplate.MovementTypeByText(mvtText)
      self.previewItem.movementType = mvt
      self.previewItem.UpdateToolTip()
      
   def NameChanged(self):
      print "Namechanged!"
      self.previewItem.name = self.nameLe.text()
      self.nameHasBeenChanged = True
      
   def WidthChanged(self):
      w = float(self.widthLe.text())
      if not w>1.e-8: return # don't drop to zero
      scaleW = w / self.lastW
      self.lastW = w
      
      if self.lockRatioCb.isChecked():
         self.heightLe.setText("%.2f" % (w/self.lastRatio))
         scaleH = scaleW
         self.lastH = w / self.lastRatio
      else: scaleH = 1.
         
      self.previewItem.scale(scaleW, scaleH)
      self.previewGv.centerOn(self.previewItem)
      
   def HeightChanged(self):
      h = float(self.heightLe.text())
      if not h>1.e-8: return # don't drop to zero
      scaleH = h / self.lastH
      self.lastH = h
      
      if self.lockRatioCb.isChecked():
         self.widthLe.setText("%.2f" % (h*self.lastRatio))
         scaleW = scaleH
         self.lastW = h * self.lastRatio
      else: scaleW = 1.
      
      self.previewItem.scale(scaleW, scaleH)
      self.previewGv.centerOn(self.previewItem)
         
   def SetLock(self):
      trn = self.previewItem
      w, h = float(self.widthLe.text()), float(self.heightLe.text())
      if not (w>1.e-8 and h>1.e-8):
         self.lockRatioCb.setChecked(False) 
      self.lastRatio = 1. * w / h
      
   def TemplateChanged(self):
      # empty scene
      self.previewScene.clear()
      
      name = self.resourceCb.currentText()
      tmp = QtGui.qApp.DataManager.TerrainByName(name)
      print "Switching to %s." % name
      
      if not self.nameHasBeenChanged: self.nameLe.setText(name)
      
      trnItem = TerrainGraphicsItem(tmp)
      self.previewItem = trnItem
      self.previewScene.addItem(trnItem)
      
      w, h = trnItem.scale() * trnItem.pixmap().width(), trnItem.scale() * trnItem.pixmap().height() 
      self.widthLe.setText("%.2f" % w)
      self.heightLe.setText("%.2f" % h)
      self.lastRatio = 1. * w / h
      self.lastW = w
      self.lastH = h
      
      self.movementTypeCb.setCurrentIndex(self.movementTypeCb.findText(tmp.movementType.text))
      self.previewGv.centerOn(self.previewItem)

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
      self.unitLabelLe = QtGui.QLineEdit("?")
      self.unitTypeCb = QtGui.QComboBox()
      self.unitSizeCb = QtGui.QComboBox()
      self.baseSizeCb = QtGui.QComboBox()
      
      self.playerCb = QtGui.QComboBox()
      for i in range(QtGui.qApp.GameManager.NumPlayers()):
         self.playerCb.addItem(QtGui.qApp.GameManager.GetPlayer(i).name)
      
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
      
      self.cancelBtn = QtGui.QPushButton("Cancel")
      self.acceptBtn = QtGui.QPushButton("Add >>")
      self.acceptBtn.setDefault(True)
      
      
      #=========================================================================
      # Init layout
      #=========================================================================
      lay = QtGui.QVBoxLayout()
      mainLay = QtGui.QGridLayout()
      btnLay = QtGui.QHBoxLayout()
      
      # general group box
      genGrpBox = QtGui.QGroupBox("General")
      genLay = QtGui.QGridLayout()
      
      row = 0
      # unit name
      genLay.addWidget(QtGui.QLabel("Unit name:"), row, 0)
      genLay.addWidget(self.unitNameLe, row, 1)
      row+=1
      
      # label
      genLay.addWidget(QtGui.QLabel("Unit label:"), row, 0)
      genLay.addWidget(self.unitLabelLe, row, 1)
      row+=1
      
      # unit type
      genLay.addWidget(QtGui.QLabel("Unit type:"), row, 0)
      genLay.addWidget(self.unitTypeCb, row, 1)
      row+=1
      
      # unit size
      genLay.addWidget(QtGui.QLabel("Size:"), row, 0)
      genLay.addWidget(self.unitSizeCb, row, 1)
      row+=1
      
      # base size
      genLay.addWidget(QtGui.QLabel("Base size [mm]:"), row, 0)
      genLay.addWidget(self.baseSizeCb, row, 1)
      row+=1
      
      # control group box
      conGrpBox = QtGui.QGroupBox("Control")
      conLay = QtGui.QGridLayout()
      
      row = 0
      # player
      conLay.addWidget(QtGui.QLabel("Controlled by:"), row, 0)
      conLay.addWidget(self.playerCb, row, 1)
      row += 1
      
      
      #=========================================================================
      # ASSEMBLE LAYOUTS
      #=========================================================================
      genGrpBox.setLayout(genLay)
      conGrpBox.setLayout(conLay)
      mainLay.addWidget(genGrpBox, 0, 0)
      mainLay.addWidget(conGrpBox, 1, 0)
      mainLay.addWidget(self.previewGv, 0, 1, 2, 1, stretch=1)
      
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
      self.playerCb.currentIndexChanged.connect(self.PlayerChanged)
      
      self.unitNameLe.textChanged.connect(self.UnitNameChanged)
      self.unitLabelLe.textChanged.connect(self.UnitLabelChanged)
      
      self.cancelBtn.clicked.connect(self.reject)
      self.acceptBtn.clicked.connect(self.accept)
      
      #=========================================================================
      # FINAL INITIALIZATION
      #=========================================================================
      self.unitNameLe.selectAll()
      self.unitNameLe.setFocus()
      
   def PlayerChanged(self):
      index = self.playerCb.currentIndex()
      self.unit.SetOwner(QtGui.qApp.GameManager.GetPlayer(index))

   def UnitLabelChanged(self):
      label = self.unitLabelLe.text()
      
      if label != self.unit.labelText:
         # only update unit if the label text actually changes
         self.unitLabelLe.setText(label)
         self.unit.labelText = label
         self.unit.UpdateLabel()
         self.unit.update()
   
   def UnitNameChanged(self):
      name = self.unitNameLe.text()
      words = name.split(" ")
      
      label = ""
      for w in words:
         if len(w)>0 and w[0].isalnum() and len(label)<=4: # max 4 chars
            label += w[0].upper()
            
      if label != self.unit.labelText:
         # only update unit if the label text actually changes
         self.unitLabelLe.setText(label)
         self.unit.labelText = label
         self.unit.UpdateLabel()
         self.unit.update()
      
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
      self.unit = RectBaseUnit(name = self.unitNameLe.text(), labelText = self.unitLabelLe.text(), baseSize = (unitWidth * MM_TO_IN, unitDepth * MM_TO_IN), formation=formation)
      
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
      
   def AddHistoryItem(self, text, mode="b"):
      self.chatHistory.append("<%s>%s</%s>" % (mode, text, mode))
      
   def AddChatItem(self, text):
      # add timestamp
      timestamp = "<span style=\"%s\">" % ChatWidget._TimestampCss + time.strftime("%H:%M:%S" + "</span> ")
      self.chatHistory.append( timestamp + unicode(text) )
      
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
         self.AddChatItem( text )
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
               self.AddChatItem("<i>%s</i>" % text)
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
      
      