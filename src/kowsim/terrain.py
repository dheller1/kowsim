from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from constants import *
from util import dot2d, len2d, dist2d

class TerrainMovementType:
   def __init__(self, text, idStr, id):
      self.text = text
      self.idStr = idStr
      self.id = id
      
MOV_OPEN = TerrainMovementType("Open", "MOV_OPEN", 0)
MOV_DIFFICULT = TerrainMovementType("Difficult", "MOV_DIFFICULT", 1)
MOV_IMPASSABLE = TerrainMovementType("Impassable", "MOV_IMPASSABLE", 2)

class TerrainTemplate:
   MOVEMENT_TYPES = [MOV_OPEN, MOV_DIFFICULT, MOV_IMPASSABLE]   
   def __init__(self, name="Forest", resourceId="TRN_FOREST01", movementType=MOV_DIFFICULT, pixmap=None, defaultSize=(1.,1.)):
      self.name = name
      self.id = resourceId
      self.SetMovementType(movementType)
      self.originalPixmap = pixmap
      
      self.defaultSize = defaultSize
      
   def AspectRatio(self):
      return 1. * self.originalPixmap.width() / self.originalPixmap.height()
   
   @staticmethod
   def MovementTypeByText(text):
      for mvt in TerrainTemplate.MOVEMENT_TYPES:
         if mvt.text == str(text):
            return mvt
      return None
      
   def SetMovementType(self, mtype):
      if type(mtype) in (str, unicode):
         found = False 
         for knownType in self.MOVEMENT_TYPES:
            if str(mtype) == knownType.idStr:
               self.movementType = knownType
               found = True
               break
         if not found: raise ValueError("Unknown terrain movement type: %s" % mtype)
      else: self.movementType = mtype


class TerrainGraphicsItem(QtGui.QGraphicsPixmapItem):
   def __init__(self, template, parent=None):
      super(TerrainGraphicsItem, self).__init__(parent)
      
      self.setZValue(Z_TERRAIN)
      self.template = template
      self.name = template.name
      self.movementType = template.movementType
      self.setPixmap(template.originalPixmap)
      self.Resize(*template.defaultSize)
      
      self.contextMenu = TerrainContextMenu(self)
      
   def DestroySelf(self):
      if QtGui.QMessageBox.Yes == QtGui.QMessageBox.warning(None, "Remove terrain piece", "Really remove %s?<br>This can not be undone." % self.name, \
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel):
         self.scene().DestroyTerrainPiece(self)
         
   def InitMovement(self):
      if self.scene().mouseMode == MOUSE_MOVE_TERRAIN:
         self.scene().mouseMode == MOUSE_DEFAULT
         self.scene().ResetStatusMessage()
      
      else:
         self.scene().mouseMode = MOUSE_MOVE_TERRAIN
         self.scene().movingItem = self
         self.scene().siStatusMessage.emit("Moving %s. Left click to set position." % self.name)
      
      
   def InitRotation(self):
      if self.scene().mouseMode == MOUSE_ROTATE_TERRAIN:
         self.scene().mouseMode == MOUSE_DEFAULT
         self.scene().ResetStatusMessage()
      
      else:
         self.scene().mouseMode = MOUSE_ROTATE_TERRAIN
         self.scene().rotatingItem = self
         self.scene().siStatusMessage.emit("Rotating %s. Left click to set rotation." % self.name)
      
   def Resize(self, width, height):
      pm = self.template.originalPixmap
      aspectRatio = self.template.AspectRatio()
           
      if (1.*width/height > aspectRatio): # desired size is too wide
         cropRect = QtCore.QRect(0, 0, pm.height() * aspectRatio, pm.height())
      else: # desired size too high
         cropRect = QtCore.QRect(0, 0, pm.width(), pm.width()/aspectRatio)
         
      newPm = pm.copy(cropRect)
      scale = 1. * width / newPm.width()
      self.setPixmap(newPm)
      self.setScale(scale)
      #translate to center
      self.setOffset(-0.5*self.boundingRect().width(),-0.5*self.boundingRect().height())
      
      self.UpdateToolTip()
      
   def UpdateToolTip(self):
      self.setToolTip("%s (%s terrain)" % (self.name, self.movementType.text))
   
   def contextMenuEvent(self, e):
      self.contextMenu.exec_(e.screenPos())
      
class TerrainContextMenu(QtGui.QMenu):
   def __init__(self, parentItem):
      super(TerrainContextMenu, self).__init__()
      self.parentItem = parentItem
      
      # Move
      self.mov = self.addAction("&Move")
      self.mov.triggered.connect(self.parentItem.InitMovement)
            
      # Rotate
      self.rot = self.addAction(QtGui.qApp.DataManager.IconByName("ICN_ROTATE_UNIT"), "&Rotate")
      self.rot.triggered.connect(self.parentItem.InitRotation)
      
      self.addSeparator()
      
      # Lock
      self.lock = self.addAction("&Lock")
      self.lock.setCheckable(True)
      self.lock.toggled.connect(self.SetLock)
      
      # destroy terrain piece
      self.dest = self.addAction("Remove")
      self.dest.triggered.connect(self.parentItem.DestroySelf)
      
   def SetLock(self, lock):
      for act in (self.mov, self.rot, self.dest):
         act.setEnabled(not lock)
      text = "locked" if lock else "unlocked"
      self.parentItem.scene().siLogEvent.emit("%s has been %s." % (self.parentItem.name, text))