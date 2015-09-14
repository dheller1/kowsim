from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from constants import *
from util import dot2d

import math 

class DialDialog(QtGui.QDialog):
   def __init__(self, startValue=0, min=0, max=359, parent=None):
      super(DialDialog, self).__init__(parent)
      self.setWindowFlags(Qt.Popup)
      
      self.setLayout(QtGui.QVBoxLayout())
      
      self.dial = QtGui.QDial()
      self.dial.setRange(min, max)
      
      self.label = QtGui.QLabel("%i" % self.dial.value())
      
      self.layout().addWidget(self.dial)
      self.layout().addWidget(self.label)
      
      self.dial.valueChanged.connect(self.UpdateLabel)
      self.dial.setValue(startValue)
      
   def UpdateLabel(self):
      self.label.setText("%i" % self.dial.value())

class BattlefieldScene(QtGui.QGraphicsScene):
   siStatusMessage = QtCore.Signal(str)
   
   def __init__(self):
      super(BattlefieldScene, self).__init__()
      
      margin = 4
      tableSize = (72,48)
      
      self.setSceneRect(-margin, -margin, tableSize[0]+2*margin, tableSize[1]+2*margin)
      
      # add background rect
      self.addRect(0, 0, tableSize[0], tableSize[1], brush=QtGui.QColor(121,217,82))
      
      # draw "coordinate system"
      self.addLine(0,0,tableSize[0],0)
      self.addLine(0,0,0,tableSize[1])
      
      markInterval = 6 # inches
      for i in xrange(0, int(tableSize[1])+1, markInterval):
         self.addLine(-0.5, i, 0.5, i)
         text = self.addText(str(i))
         text.setScale(0.15)
         text.setPos(-4, i - 1.4*text.font().pointSize() * text.scale())
         
      for j in xrange(0, int(tableSize[0])+1, markInterval):
         self.addLine(j, -0.5, j, 0.5)
         text = self.addText(str(j))
         text.setScale(0.15)
         text.setPos(j - 1.4*text.font().pointSize() * text.scale(), -4)
         
         
      # draw lines for deployment zones
      self.addLine(0,tableSize[1]/4.,tableSize[0],tableSize[1]/4.)
      self.addLine(0,tableSize[1]*3./4.,tableSize[0],tableSize[1]*3./4.)
      
      # add floatable distance counter
      self.distCounter = self.addText("")
      self.distCounter.setZValue(+10)
      self.distCounter.setScale(0.15)
      self.distCounter.setVisible(False)
      
      # add test unit
      #testUnit = RectBaseItem(20. / 2.54, 8. / 2.54)
      testUnit = RectBaseUnit("Sea Guard Horde (40)", (200 * MM_TO_IN, 80 * MM_TO_IN))
      testUnit.setPos(36, 38)
      self.addItem(testUnit)
      
      
      testUnit2 = RectBaseUnit("Ax Horde (40)", (250 * MM_TO_IN, 100 * MM_TO_IN))
      testUnit2.setPos(32, 7.5)
      testUnit2.setRotation(173)
      print testUnit2.rotation()
      testUnit2.setBrush(QtGui.QColor(11,121,5))
      self.addItem(testUnit2)
      
      self.InitConnections()
    
   def InitConnections(self):
      self.selectionChanged.connect(self.HandleSelectionChanged)
          
   def HandleSelectionChanged(self):
      if len(self.selectedItems())>1:
         raise BaseException("Why is there more than one item selected?!")
      
      elif len(self.selectedItems())==1:
         sel = self.selectedItems()[0]
         self.siStatusMessage.emit("%s selected." % sel.name)
         
      else:
         self.siStatusMessage.emit("")
   
   def ClearDistCounter(self):
      self.distCounter.setPlainText("")
      self.distCounter.setVisible(False)
   
   def SetDistCounter(self, text, pos):
      self.distCounter.setPlainText(text)
      self.distCounter.setPos(pos)
      self.distCounter.setVisible(True)
      
      
class BattlefieldView(QtGui.QGraphicsView):
   ZoomPerTick = 1.2
   
   def __init__(self):
      super(BattlefieldView, self).__init__()
      
      scene = BattlefieldScene()
      
      self.setScene(scene)
      self.fitInView(scene.sceneRect())
      
      #self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
      
   def keyPressEvent(self, e):
      # propagate to children
      super(BattlefieldView, self).keyPressEvent(e)
       
      if not e.isAccepted():
         for i in self.scene().selectedItems():
            i.keyPressEvent(e)
            
   def mousePressEvent(self, e):
      if e.button() == Qt.MidButton:
         self.lastDragPos = e.pos()
         self.setCursor(Qt.ClosedHandCursor)
         e.accept()
         
      else: # propagate to base class
         super(BattlefieldView, self).mousePressEvent(e)
           
   def mouseReleaseEvent(self, e):
      if e.button() == Qt.MidButton:
         self.lastDragPos = None
         self.setCursor(Qt.ArrowCursor)
         e.accept()
         
      else: # propagate to base class
         super(BattlefieldView, self).mouseReleaseEvent(e)
           
   def mouseMoveEvent(self, e):
      if Qt.MidButton & int(e.buttons()):
         delta = e.pos() - self.lastDragPos
         self.lastDragPos = e.pos()
            
         self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
         self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
         e.accept()
         
      else: # propagate to base class
         super(BattlefieldView, self).mouseMoveEvent(e)

   def resizeEvent(self, e):
      e.accept()
      #self.fitInView(self.scene().sceneRect())
      
   def wheelEvent(self, e):
      e.accept()
      
      # delta is probably 120 for a single tick (15 degrees times 8 steps per degree)
      ticks = e.delta() / 120
      
      if ticks > 0: self.ZoomIn(ticks)
      else: self.ZoomOut(-ticks) # ticks must always be positive, else the scene would be flipped
      
   def ZoomIn(self, ticks):
      assert(ticks>=0)
      self.scale(BattlefieldView.ZoomPerTick * ticks, BattlefieldView.ZoomPerTick * ticks)
      
   def ZoomOut(self, ticks):
      assert(ticks>=0)
      self.scale(1./BattlefieldView.ZoomPerTick * ticks, 1./BattlefieldView.ZoomPerTick * ticks)
      
      
class RectBaseUnit(QtGui.QGraphicsRectItem):
   DefaultColor = QtGui.QColor(34,134,219)
   
   def __init__(self, name="Unnamed unit", baseSize=(100*MM_TO_IN, 80*MM_TO_IN), parent=None):
      super(RectBaseUnit, self).__init__(parent)
      
      self.name = name
      
      self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | QtGui.QGraphicsItem.ItemSendsGeometryChanges) # | QtGui.QGraphicsItem.ItemIsMovable 
      self.setToolTip(name)
      
      self.movementTemplate = None
      self.movementInitiated = False
      
      # draw
      self.setBrush(RectBaseUnit.DefaultColor)
      
      w, h = baseSize
      if w != 0 and h != 0:
         if w < 0 or h < 0: raise ValueError("Cannot initialize RectBaseItem with negative width or height!")
         else:
            self.setRect(-w/2, -h/2, w, h)
         
      elif w != 0 or h != 0:
         raise ValueError("Must initialize RectBaseItem either without width and height or with both!")
      
   def CancelMovement(self):
      self.movementInitiated = False
      self.scene().distCounter.setVisible(False)
      if self.movementTemplate:
         self.scene().removeItem(self.movementTemplate)
         del self.movementTemplate
         self.movementTemplate = None
         
   def FinalizeMovement(self):
      if self.movementTemplate:
         self.setPos(self.movementTemplate.scenePos())
         self.CancelMovement()
      
   def GetNormalVectorFront(self):
      # normal vector is always (0, -1) at center location (0, 0) in local coordinates
      normalDir = QtCore.QPointF(0, -1)
      normalLoc = QtCore.QPointF(0, 0)
      
      # map to scene
      scNormalDir = self.mapToScene(normalDir)
      scNormalLoc = self.mapToScene(normalLoc)
      
      # return in scene coordinates
      normal = QtCore.QLineF( scNormalLoc, scNormalDir )
      
      return normal
   
   def HandleMovementEvent(self, event, evtSource):
      e = event
      if (QtCore.QLineF(e.screenPos(), e.buttonDownScreenPos(Qt.LeftButton)).length() < QtGui.QApplication.startDragDistance()):
            return
      
      
      # initiate movement
      self.SpawnMovementTemplate()
      self.movementInitiated = True
      self.movementTemplate.movementInitiated=True

      # select movement template      
      self.setSelected(False)
      self.movementTemplate.setSelected(True)
      
      # emit status message
      if not self.movementTemplate.restrictedMovementAxis: self.scene().siStatusMessage.emit("Moving %s." % self.name)
      else: self.scene().siStatusMessage.emit("Moving %s FORWARD." % self.name)
      
      # handle movement event itself
      
      # just set to mouse position if not restricted
      if not self.movementTemplate.restrictedMovementAxis:
         self.movementTemplate.setPos(e.scenePos())
      
      # or, handle movement restricted to axis
      else: # orthogonal projection point x to axis u: P(x) = x dot u / u dot u * vec(u) 
         # vector from starting point to end point of movement axis
         uVec = QtCore.QPointF( self.movementTemplate.restrictedMovementAxis.x2() - self.movementTemplate.restrictedMovementAxis.x1(),
                                self.movementTemplate.restrictedMovementAxis.y2() - self.movementTemplate.restrictedMovementAxis.y1() )
         xVec = e.scenePos() - self.movementTemplate.restrictedMovementAxis.p1()
         
         scalingFactor = dot2d(xVec, uVec) / dot2d(uVec, uVec)
         uVec *= scalingFactor
         
         self.movementTemplate.setPos( uVec + self.movementTemplate.restrictedMovementAxis.p1() )
      
      # update distance counter
      d = self.movementTemplate.scenePos() - self.scenePos()
      dist = math.sqrt(d.x()**2 + d.y()**2)
      self.scene().SetDistCounter("%.1f\"" % dist, self.movementTemplate.scenePos())

   def SpawnMovementTemplate(self):
      # make sure that a movement template for this unit has already been created
      if self.movementTemplate is None:
         self.movementTemplate = RectBaseMovementTemplate(self)
         self.scene().addItem(self.movementTemplate)
         self.movementTemplate.setPos(self.scenePos())
         
   def SpawnRotator(self):
      diag = DialDialog(self.rotation(), -180, 180)
      diag.move(QtGui.QCursor.pos())
      diag.dial.valueChanged.connect(self.movementTemplate.setRotation)
      diag.exec_()
   
   def itemChange(self, change, value):
      if change == QtGui.QGraphicsItem.ItemPositionChange:
         if not Qt.LeftButton & int(QtGui.QApplication.mouseButtons()):
            print "Moved"
         
      return QtGui.QGraphicsItem.itemChange(self, change, value)
      
   def paint(self, painter, option, widget):
      super(RectBaseUnit, self).paint(painter, option, widget)
      
      # determine triangle coordinates
      triW, triH = 4, 0.8
      if triW > self.rect().width():
         triW = self.rect().width()
         
      vOffset = self.rect().height()/2
      
      triPoints = [QtCore.QPointF(x,y) for x,y in [(0, -vOffset), (triW/2, -vOffset+triH), (-triW/2, -vOffset+triH)]]
      
      # set color
      dr, dg, db = 255 - self.brush().color().red(), 255 - self.brush().color().green(), 255 - self.brush().color().blue()
      brighteningFactor = 1.7
      
      painter.setBrush(QtGui.QColor(255-dr/brighteningFactor, 255-dg/brighteningFactor, 255-db/brighteningFactor))
      painter.setPen(Qt.NoPen)
      
      painter.drawConvexPolygon(triPoints)
   
   def keyPressEvent(self, e):
      if e.key() == Qt.Key_R: # rotate
         self.SpawnMovementTemplate()
         self.SpawnRotator()
      
      if e.key() == Qt.Key_F and self.movementInitiated: # restrict to forward axis
         self.SpawnMovementTemplate()
         
         if not self.movementTemplate.restrictedMovementAxis:
            self.scene().siStatusMessage.emit("Moving %s FORWARD." % self.name)
            self.movementTemplate.restrictedMovementAxis = self.GetNormalVectorFront()
         else:
            self.scene().siStatusMessage.emit("Moving %s." % self.name)
            self.movementTemplate.restrictedMovementAxis = None
   
   def mousePressEvent(self, e):
      if e.button() == Qt.LeftButton:
         self.setCursor(Qt.ClosedHandCursor)
         self.movementInitiated = True
                  
      super(RectBaseUnit, self).mousePressEvent(e)
       
   def mouseReleaseEvent(self, e):
      if e.button() == Qt.LeftButton:
         self.setCursor(Qt.ArrowCursor)
         self.scene().siStatusMessage.emit("%s selected." % self.name)
         self.movementInitiated = False
         if self.movementTemplate: self.movementTemplate.restrictedMovementAxis = None
         
      super(RectBaseUnit, self).mouseReleaseEvent(e)
       
   def mouseMoveEvent(self, e):
      if Qt.LeftButton & int(e.buttons()): # left mouse dragging
         self.HandleMovementEvent(e, self)

class MovementTemplateContextMenu(QtGui.QMenu):
   def __init__(self):
      super(MovementTemplateContextMenu, self).__init__()
      
      self.finalizeAction = self.addAction("Finalize")
      self.cancelAction = self.addAction("Cancel")
      
        
         
class RectBaseMovementTemplate(RectBaseUnit):
   Alpha = 145
   
   def __init__(self, parentUnit):
      super(RectBaseMovementTemplate, self).__init__(name=parentUnit.name)
      
      self.parentUnit = parentUnit 
      self.setRect(parentUnit.rect())
      
      self.restrictedMovementAxis = None
      
      brColor = parentUnit.brush().color()
      brColor.setAlpha(RectBaseMovementTemplate.Alpha)
      self.setBrush(brColor)
      
      penColor = parentUnit.pen().color()
      penColor.setAlpha(RectBaseMovementTemplate.Alpha)
      pen = QtGui.QPen(penColor, width=4, style=Qt.DotLine)
      
      self.setPen(pen)
      
      self.setPos(parentUnit.scenePos())
      self.setRotation(parentUnit.rotation())
      
      # init and connect context menu
      self.contextMenu = MovementTemplateContextMenu()
      self.contextMenu.finalizeAction.triggered.connect(self.parentUnit.FinalizeMovement)
      self.contextMenu.cancelAction.triggered.connect(self.parentUnit.CancelMovement)
      
   def contextMenuEvent(self, e):
      self.contextMenu.exec_(e.screenPos())
      
   def keyPressEvent(self, e):
      # propagate backwards to parent unit.
      self.parentUnit.keyPressEvent(e)
   
   def paint(self, painter, option, widget):
      super(RectBaseMovementTemplate, self).paint(painter, option, widget)
      
      dist = QtCore.QLineF(self.scenePos(), self.parentUnit.scenePos()).length()
      
      #if self.restrictedMovementAxis:
      #   self.scene().addLine(self.restrictedMovementAxis)

   def mouseMoveEvent(self, e):
      # reimplement this! don't spawn more movement templates from a movement template!
      if Qt.LeftButton & int(e.buttons()): # left mouse dragging
         self.parentUnit.HandleMovementEvent(e, self)
            
   def mouseReleaseEvent(self, e):
      super(RectBaseMovementTemplate, self).mouseReleaseEvent(e)
      
      if e.button() == Qt.LeftButton:
         self.restrictedMovementAxis = None