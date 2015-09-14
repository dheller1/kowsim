import sys, time
from PySide import QtGui

from dice import RollHandler
from battlefield import BattlefieldView
from constants import *

class MainWindow(QtGui.QMainWindow):
   def __init__(self):
      super(MainWindow, self).__init__()
      
      self.resize(1024, 600)
      self.setWindowTitle("vbattle")
      
      self.setCentralWidget(MainWindowCentralWidget())
      self.setStatusBar(QtGui.QStatusBar())
      self.statusBar().showMessage("Ready.")
      
      self.InitConnections()
      
   def InitConnections(self):
      self.centralWidget().battlefieldView.scene().siStatusMessage.connect(self.HandleStatusMessage)
      
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
      
      
class ChatWidget(QtGui.QWidget):
   _TimestampCss = 'color:#999999;'
   _ErrorCss = 'color:#a0a0a0;font-weight:bold;font-style:italic;'
   
   _SupportedCommands = ("r")
   
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
            self.PrintError("Error: Unknown command '%s'!" % command)
            return
            
         elif command == "r": # Roll
            rollString = commandText[1:].strip()
            self.AddHistoryItem("<i>%s</i>" % text)
            rollHndlr = RollHandler()
            rollHndlr.InterpretString(rollString)
   
            results = rollHndlr.Roll()
            
            if rollHndlr.numDice < 10 and len(rollHndlr.individualRolls) <= 1:
               self.AddHistoryItem(rollHndlr.RollModeToString() + " " + rollHndlr.AllResultsToString())