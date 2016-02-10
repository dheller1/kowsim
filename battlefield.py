# -*- coding: utf-8 -*-


#===============================================================================
# TODO:
#
#  * Remove units when they die
#  * 1-click nerve check?
#  * automated movement to exact position after charge? 
#  * exact moves by console (e.g. '/m b 1' could move the current unit back 1 inch)
#  * set damage quantity when adding a damage marker 
#
#===============================================================================

from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from constants import *
from util import dot2d, len2d, dist2d

import math, os

#===============================================================================
# MarkerContextMenu
#   Context menu class relating to a MarkerItem object.
#===============================================================================
class MarkerContextMenu(QtGui.QMenu):
   def __init__(self, parentMarker):
      super(MarkerContextMenu, self).__init__()
      
      self.parentMarker = parentMarker
      
      if parentMarker.cumulative:
         inc = self.addAction("Increase by 1")
         dec = self.addAction("Decrease by 1")
         mod = self.addAction("Modify...")
         #setTo = self.addAction("Set to...")
         
         inc.triggered.connect(self.parentMarker.Increase)
         dec.triggered.connect(self.parentMarker.Decrease)
         mod.triggered.connect(self.parentMarker.ModifyQuantity)
         #setTo.triggered.connect(self.parentMarker.SetQuantity)
         
      rem = self.addAction("Remove")
      rem.triggered.connect(self.parentMarker.Remove)
      
      
#===============================================================================
# MarkerItem
#   Container class derived from QGraphicsPixmapItem, representing a marker
#   which must be attached to a unit on the battlefield.
#===============================================================================
class MarkerItem(QtGui.QGraphicsPixmapItem):
   MarkerSize = (2., 2.)
   
   def __init__(self, markerType, parent):
      super(MarkerItem, self).__init__(markerType.pixmap, parent)
      
      self.name = markerType.name
      
      scaleX = MarkerItem.MarkerSize[0] / self.boundingRect().width()
      scaleY = MarkerItem.MarkerSize[1] / self.boundingRect().height()
      self.scale(scaleX, scaleY) # scale to apprx. 1 inch
      
      self._count = 1
      self.cumulative = markerType.cumulative
      self.rank = 0 # markers are drawn in order of their rank
      
      self.contextMenu = MarkerContextMenu(self)
      
      if self.cumulative:
         self.countText = QtGui.QGraphicsTextItem("%i" % self._count, self)
         self.countText.setDefaultTextColor(QtGui.QColor(255,255,255))
         self.countText.moveBy(35,0)
         self.countText.scale(10,10)
         
      self.scene().siLogEvent.emit("Added %s marker to %s." % (self.name, self.parentItem().name))
         
   # property: count
   def getCount(self):
      return self._count
   def setCount(self, val):
      self._count = val
      self.countText.setPlainText("%i" % self.count)
      if self.count <= 0:
         self.Remove()
   #
   count = property(getCount, setCount)
      
   def contextMenuEvent(self, e):
      self.contextMenu.exec_(e.screenPos())
      
   def Increase(self):
      self.count += 1
      self.scene().siLogEvent.emit("%s's %s marker increased by 1 to %i total." % (self.parentItem().name, self.name, self.count))
      print "%s's %s marker increased by 1 to %i total." % (self.parentItem().name, self.name, self.count)
      
   def Decrease(self):
      self.count -= 1
      self.scene().siLogEvent.emit("%s's %s marker decreased by 1 to %i total." % (self.parentItem().name, self.name, self.count))
      
   def ModifyQuantity(self):
      increment, accepted = QtGui.QInputDialog.getInt(self.window(), self.name, "Modify by (can be negative):", 0, -999, 999, 1)
      if accepted:
         self.count += increment
         self.scene().siLogEvent.emit("%s's %s marker modified by %i to %i total." % (self.parentItem().name, self.name, increment, self.count))
      
   def SetQuantity(self):
      newCount, accepted = QtGui.QInputDialog.getInt(self.window(), self.name, "New value:", self.count, 0, 999, 1)
      if accepted:
         self.scene().siLogEvent.emit("%s's %s marker set to %i total (previously %i)." % (self.parentItem().name, self.name, newCount, self.count))
         self.count = newCount
   
   def Remove(self):
      self.parentItem().RemoveMarker(self.name)
      self.scene().siLogEvent.emit("Removed %s marker from %s." % (self.name, self.parentItem().name))

#===============================================================================
# DialDialog
# - obsolete -
#   Dialog enabling to rotate a unit (no longer in use).
#===============================================================================
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

#===============================================================================
# BattlefieldScene
#   Scene class inheriting from QGraphicsScene which holds the battlefield
#   geometry plus all other objects drawn on the battlefield, such as units,
#   markers, templates, etc.
#   Provides some logic for moving objects within the scene, measuring
#   distances, and more.
#===============================================================================
class BattlefieldScene(QtGui.QGraphicsScene):
   siStatusMessage = QtCore.Signal(str)
   siLogEvent = QtCore.Signal(str)
   siUnitSelected = QtCore.Signal(bool)
   
   def __init__(self):
      super(BattlefieldScene, self).__init__()
      
      self.mouseMode = MOUSE_DEFAULT
      
      margin = 4
      tableSize = (72,48)
      
      self.setSceneRect(-margin, -margin, tableSize[0]+2*margin, tableSize[1]+2*margin)
      
      # background texture
      bgImg = QtGui.QPixmap(os.path.join("data", "mats", "mat01.jpg"))
      aspectRatio = 1. * tableSize[0] / tableSize[1]
      
      if (1.*bgImg.width()/bgImg.height() > aspectRatio): # image file is too wide
         cropRect = QtCore.QRect(0, 0, bgImg.height() * aspectRatio, bgImg.height())
      else: # image file too high
         cropRect = QtCore.QRect(0, 0, bgImg.width(), bgImg.width()/aspectRatio)
      
      croppedBg = bgImg.copy(cropRect)
      self.backgroundItem = QtGui.QGraphicsPixmapItem(croppedBg)
      scale = 1. * tableSize[0] / croppedBg.width()
      self.backgroundItem.scale(scale, scale)
      
      self.addItem(self.backgroundItem)
      
      # draw table border
      pen = QtGui.QPen()
      pen.setWidthF(0.5)
      pen.setColor(QtGui.QColor(52,24,7))
      
      self.addLine(QtCore.QLineF(0, 0, tableSize[0], 0), pen) # TL to TR
      self.addLine(QtCore.QLineF(tableSize[0], 0, tableSize[0], tableSize[1]), pen) # TR to BR
      self.addLine(QtCore.QLineF(tableSize[0], tableSize[1], 0, tableSize[1]), pen) # BR to BL
      self.addLine(QtCore.QLineF(0, tableSize[1], 0, 0), pen) # BL to TL
      
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
      
      # current distance marker
      self.distMarker = None
      
      # add a placeable unit container
      self.unitToPlace = None
      
      # add test unit
      #testUnit = RectBaseItem(20. / 2.54, 8. / 2.54)
      testUnit = RectBaseUnit("Sea Guard Horde (40)", "SG", (200 * MM_TO_IN, 80 * MM_TO_IN), (10,4))
      testUnit.setPos(36, 38)
      testUnit.SetOwner(QtGui.qApp.GameManager.GetPlayer(0))
      self.addItem(testUnit)
      
      testUnit2 = RectBaseUnit("Ax Horde (40)", "AX", (250 * MM_TO_IN, 100 * MM_TO_IN), (10,4))
      testUnit2.setPos(32, 7.5)
      testUnit2.setRotation(173)
      print testUnit2.rotation()
      testUnit2.SetOwner(QtGui.qApp.GameManager.GetPlayer(1))
      self.addItem(testUnit2)
      
      self.InitConnections()
    
   def InitConnections(self):
      self.selectionChanged.connect(self.HandleSelectionChanged)
      
   def InitRotation(self):
      """ Initialize rotation on a selected unit (invoked from outside such as a pressed toolbutton). """
      if len(self.selectedItems())==1:
         self.selectedItems()[0].InitRotation()
   
   def AbortMouseAction(self):
      if(len(self.selectedItems())>0):
         sel = self.selectedItems()[0]
      
      if self.mouseMode == MOUSE_ROTATE_UNIT:
         sel.CancelMovement()
         
      self.mouseMode = MOUSE_DEFAULT
      self.ClearDistCounter()
      self.ResetStatusMessage()
      self.RemoveDistanceMarker()
          
   def ClearDistCounter(self):
      self.distCounter.setPlainText("")
      self.distCounter.setVisible(False)
   
   def HandleSelectionChanged(self):
      self.ResetStatusMessage()
      
#       # clear arc templates
#       for itm in self.arcTemplates:
#          self.removeItem(itm)
#       self.arcTemplates = []
      
      if len(self.selectedItems())>1:
         raise BaseException("Why is there more than one item selected?!")
      
      elif len(self.selectedItems())==1:
         self.siUnitSelected.emit(True)
      
      elif len(self.selectedItems())==0:
         self.siUnitSelected.emit(False)
#          sel = self.selectedItems()[0]
#          
#          template = sel.GetFrontArcTemplate()
#          self.arcTemplates.append(template)
#          self.addItem(template)
   
   def SetDistCounter(self, text, pos):
      self.distCounter.setPlainText(text)
      self.distCounter.setPos(pos)
      self.distCounter.setVisible(True)
      
   def SelectedItem(self):
      if(len(self.selectedItems())>0):
         return self.selectedItems()[0]
      else:
         return None
   
   def RemoveDistanceMarker(self):
      if self.distMarker:
         self.removeItem(self.distMarker)
         del self.distMarker
         self.distMarker = None
         
   def ResetStatusMessage(self):
      if len(self.selectedItems())==1:
         self.siStatusMessage.emit("%s selected." % self.selectedItems()[0].name)
      else:
         self.siStatusMessage.emit("Ready.")
         
   def UnitAt(self, scenePos):
      target = self.itemAt(scenePos)
      if target and type(target)!=RectBaseUnit:
         target = target.topLevelItem()
         
      return target
            
   def mouseMoveEvent(self, e):
      if self.mouseMode == MOUSE_ROTATE_UNIT:
         e.accept()
         if len(self.selectedItems()) != 1: raise BaseException("Invalid number of selected units!")
         else:
            sel = self.selectedItems()[0]
            sel.RotateToPoint(e.scenePos())
            if sel.movementTemplate is not None: # RectBaseUnit instance with its own movement template
               angle = sel.movementTemplate.rotation() - sel.rotation()
            else: # MovementTemplate itself is selected
               angle = sel.rotation() - sel.parentUnit.rotation()
            
            angle = math.fabs(angle)
            if angle > 180.: # instead of "345° to the right", output "15° to the left"
               angle = 360.-angle
            self.SetDistCounter(u"%.0f°" % (angle), self.selectedItems()[0].scenePos())

      elif self.mouseMode == MOUSE_CHECK_DIST:
         target = self.UnitAt(e.scenePos())
         
         # hovering unit? check distance, but only if no old distance marker is present
         if not self.distMarker and (target is not None) and (type(target) is RectBaseUnit) and self.SelectedItem() and target!=self.SelectedItem():
            p, d = self.SelectedItem().DistanceToUnit(target)
            self.distMarker = DistanceMarker(self.SelectedItem().GetUnitLeaderPoint(), p)
            self.addItem(self.distMarker)
         
         # no hover? remove dist marker, if present
         elif (target is None or type(target)!=RectBaseUnit) and self.distMarker:
            self.RemoveDistanceMarker()
            
         super(BattlefieldScene, self).mouseMoveEvent(e)
         
      elif self.mouseMode == MOUSE_PLACE_UNIT:
         # item should already be in the scene, just make it visible
         self.unitToPlace.show()
         self.unitToPlace.setPos(e.scenePos())
            
      else:
         super(BattlefieldScene, self).mouseMoveEvent(e)
      
   def mousePressEvent(self, e):    
      if self.mouseMode == MOUSE_ROTATE_UNIT and e.button() == Qt.LeftButton:
         e.accept()
         self.mouseMode = MOUSE_DEFAULT
         if(len(self.selectedItems())>0):
            self.siStatusMessage.emit("%s selected." % self.selectedItems()[0].name)
         else:
            self.siStatusMessage.emit("Ready.")
         
      elif self.mouseMode == MOUSE_ROTATE_UNIT and e.button() == Qt.RightButton:
         e.accept()
         self.AbortMouseAction()
         
      elif self.mouseMode == MOUSE_ALIGN_TO and e.button() == Qt.LeftButton and self.itemAt(e.scenePos()) is not None:
         target = self.UnitAt(e.scenePos())
         
         if type(target) == RectBaseUnit and target != self.selectedItems()[0]: # don't align to non-unit objects or to self
            self.selectedItems()[0].AlignToUnit(target) # unit decides to which exact facing it aligns based on its position
         
         self.AbortMouseAction()
         
      elif self.mouseMode == MOUSE_ALIGN_TO and (self.itemAt(e.scenePos()) is None or e.button() == Qt.RightButton):
         self.AbortMouseAction()
         super(BattlefieldScene, self).mousePressEvent(e)
         
      elif self.mouseMode == MOUSE_CHECK_ARC and e.button() == Qt.LeftButton:
         self.AbortMouseAction()
         target = self.UnitAt(e.scenePos())
         if (target is not None) and (type(target) is RectBaseUnit) and self.SelectedItem() and target!=self.SelectedItem():
            arc = self.SelectedItem().DetermineArc(target)
            if arc == ARC_FRONT: text = "front arc"
            elif arc == ARC_REAR: text = "rear arc"
            elif arc == ARC_LEFT: text = "left flank"
            elif arc == ARC_RIGHT: text = "right flank"
            
            self.siLogEvent.emit("%s is currently in %s's %s." % (self.SelectedItem().name, target.name, text))
         
      elif self.mouseMode == MOUSE_CHECK_ARC and (self.itemAt(e.scenePos()) is None or e.button() == Qt.RightButton):
         self.AbortMouseAction()
         super(BattlefieldScene, self).mousePressEvent(e)
         
      #=========================================================================
      # MOUSE_CHECK_DIST
      #  Check closest distance from unit to unit. Left-click over target unit 
      #  write the distance to the log, visible for all players. Right-click
      #  to cancel. Hovering over a unit in this mode will show the distance
      #  within the scene, see mouseMoveEvent.
      #=========================================================================
      elif self.mouseMode == MOUSE_CHECK_DIST and e.button() == Qt.LeftButton:
         self.AbortMouseAction()
         target = self.UnitAt(e.scenePos())
         if (target is not None) and (type(target) is RectBaseUnit) and self.SelectedItem() and target!=self.SelectedItem():
            
            p, d = self.SelectedItem().DistanceToUnit(target)
            self.siLogEvent.emit("Distance from %s's unit leader point to the closest point of %s is %.2f\"." % (self.SelectedItem().name, target.name, d))
            
            #self.AddTimedMarker("MRK_DIST01", TimedDistanceMarker(self.SelectedItem().GetUnitLeaderPoint(), p))

      elif self.mouseMode == MOUSE_CHECK_DIST and (self.itemAt(e.scenePos()) is None or e.button() == Qt.RightButton):
         self.AbortMouseAction()
         super(BattlefieldScene, self).mousePressEvent(e)
         
      #=========================================================================
      # MOUSE_PLACE_UNIT
      #  Place a new unit in the scene. Click left to place at the mouse cursor
      #  or click right to cancel.
      #  TODO: Pressing ESCAPE should cancel as well.
      #=========================================================================
      elif self.mouseMode == MOUSE_PLACE_UNIT and e.button() == Qt.LeftButton:
         # item should already be in the scene, just make it visible
         self.unitToPlace.show()
         self.unitToPlace.setPos(e.scenePos())
         self.unitToPlace.setOpacity(1.0)
         self.unitToPlace = None
         self.AbortMouseAction()

      elif self.mouseMode == MOUSE_PLACE_UNIT and e.button() == Qt.RightButton:
         # item should already be in the scene, just make it visible
         self.removeItem(self.unitToPlace)
         del self.unitToPlace
         self.unitToPlace = None
         self.AbortMouseAction()
      
      #=========================================================================
      # Anything else / mode not handled: Propagate to base class.
      #=========================================================================
      else:
         super(BattlefieldScene, self).mousePressEvent(e)
      
      
class BattlefieldView(QtGui.QGraphicsView):
   ZoomPerTick = 1.2
   
   def __init__(self):
      super(BattlefieldView, self).__init__()
      
      scene = BattlefieldScene()
      
      self.setScene(scene)
      self.fitInView(scene.sceneRect())
      
      self.scale(1.44, 1.44)
      
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
      else: self.ZoomOut(-ticks) # argument must always be positive, else the scene would be flipped
      
   def ZoomIn(self, ticks):
      assert(ticks>=0)
      self.scale(BattlefieldView.ZoomPerTick * ticks, BattlefieldView.ZoomPerTick * ticks)
      
   def ZoomOut(self, ticks):
      assert(ticks>=0)
      self.scale(1./BattlefieldView.ZoomPerTick * ticks, 1./BattlefieldView.ZoomPerTick * ticks)
      
      
class RectBaseUnit(QtGui.QGraphicsRectItem):
   DefaultColor = QtGui.QColor(34,134,219)
   
   def __init__(self, name="Unnamed unit", labelText="?", baseSize=(100*MM_TO_IN, 80*MM_TO_IN), formation=None, parent=None):
      super(RectBaseUnit, self).__init__(parent)
      
      self.name = name
      self.formation = formation
      self.labelText = labelText
      
      self.owner = None # player who controls this unit
      
      # label
      self.label = QtGui.QGraphicsTextItem(labelText, self) # short label with 1-4 characters to easily identify the unit (e.g. "SG1" for the first Sea Guard unit)
      self.label.setDefaultTextColor(QtGui.QColor(255,255,255,200))
      
      self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | QtGui.QGraphicsItem.ItemSendsGeometryChanges) # | QtGui.QGraphicsItem.ItemIsMovable 
      self.setToolTip(name)
      
      # child templates
      self.movementTemplate = None
      self.arcTemplates = []
      
      self.movementInitiated = False
      self.rotationInitiated = False
      
      # draw
      self.setBrush(RectBaseUnit.DefaultColor)
      
      w, h = baseSize
      if w != 0 and h != 0:
         if w < 0 or h < 0: raise ValueError("Cannot initialize RectBaseItem with negative width or height!")
         else:
            self.setRect(-w/2, -h/2, w, h)
         
      elif w != 0 or h != 0:
         raise ValueError("Must initialize RectBaseItem either without width and height or with both!")
      
      # set context menu
      self.contextMenu = UnitContextMenu(self)
      
      # container for markers
      self.markers = {} # (markerName : quantity) tuples
      
      self.UpdateLabel()
      
   @QtCore.Slot(str)
   def AddMarker(self, markerName):
      marker = QtGui.qApp.DataManager.MarkerByName(markerName)
      
      if markerName in self.markers.keys() and not marker.cumulative:
         return # marker is unique and already present
      
      elif markerName in self.markers.keys():
         self.markers[markerName].Increase()
      
      else:
         rank = len(self.markers.keys())
         item = MarkerItem(marker, self) # this implicitly adds the marker graphics item to the scene as child of the RectBaseUnit item
         
         # BUG: If you add two markers (ranks 0 and 1), remove the first one, and add it again, both markers are at rank 1. 
         item.rank = rank
         item.moveBy(1+2*rank, 1)
         
         self.markers[markerName] = item
         
   def AlignToUnit(self, unit):
      # check facing and align
      arc = self.DetermineArc(unit)
      if arc == ARC_FRONT: self.AlignToUnitFront(unit)
      elif arc == ARC_REAR: self.AlignToUnitRear(unit)
      elif arc == ARC_LEFT: self.AlignToUnitLeftFlank(unit)
      elif arc == ARC_RIGHT: self.AlignToUnitRightFlank(unit)
      
   def AlignToUnitFront(self, unit):
      self.setRotation(unit.rotation()+180)
   def AlignToUnitRear(self, unit):
      self.setRotation(unit.rotation())
   def AlignToUnitLeftFlank(self, unit):
      self.setRotation(unit.rotation()+90)
   def AlignToUnitRightFlank(self, unit):
      self.setRotation(unit.rotation()-90)
      
   def CancelMovement(self):
      self.movementInitiated = False
      self.scene().distCounter.setVisible(False)
      if self.movementTemplate:
         if(self.scene().SelectedItem() is self.movementTemplate):
            self.scene().clearSelection()
         
         self.scene().removeItem(self.movementTemplate)
         del self.movementTemplate
         self.movementTemplate = None
                
   def DetermineArc(self, unit):
      """ Determine in which arc (front/rear/left/right) of a target unit this unit (i.e. this unit's leader point) is. """
      if unit.mapToScene(unit.GetFrontArc()).containsPoint(self.GetUnitLeaderPoint(), Qt.OddEvenFill):
         return ARC_FRONT
      elif unit.mapToScene(unit.GetRearArc()).containsPoint(self.GetUnitLeaderPoint(), Qt.OddEvenFill):
         return ARC_REAR
      elif unit.mapToScene(unit.GetLeftArc()).containsPoint(self.GetUnitLeaderPoint(), Qt.OddEvenFill):
         return ARC_LEFT
      elif unit.mapToScene(unit.GetRightArc()).containsPoint(self.GetUnitLeaderPoint(), Qt.OddEvenFill):
         return ARC_RIGHT
      
   def DistanceToUnit(self, unit):
      """ Return (QPointF, float) tuple containing the closest point of the target unit and its distance to this unit's leader point. """
      poly = unit.mapToScene(unit.rect()) # target (rotated) rect, now a QPolygonF with points (TL, TR, BR, BL, TL)
      p = self.GetUnitLeaderPoint()
      
      TL = poly[0]
      TR = poly[1]
      BR = poly[2]
      BL = poly[3]
      
      # distance from point to rectangle...
      # two cases: A) point-to-corner is the closest distance
      #            B) point-to-edge is the closest distance
      # For A), just check the four corners.
      # For B), project the point onto each of the four edges.
      #         If the projection is inside the rect, calculate
      #         distance from the projection to the point. ("Lot")
      
      # front projection: p to lf (line front)
      lf = TR - TL
      scale = dot2d(p, lf) / dot2d(lf, lf)
      scaleP2 = dot2d(TL,lf) / dot2d(lf, lf)
      
      # projection of p is only in between tr.topRight and tr.topLeft if the scaling factor is between 0 and 1
      # in this case, the same is true for a rear arc projection, we just have to determine which one is closer
      if (0. <= scale - scaleP2 <= 1.):
         pprojF = (scale - scaleP2) * lf + TL
         distF = dist2d(p, pprojF)
         
         lr = BR - BL
         scale = dot2d(p, lr) / dot2d(lr, lr)
         scaleP2 = dot2d(BL, lr) / dot2d(lr, lr)
         pprojR = (scale - scaleP2) * lr + BL
         distR = dist2d(p, pprojR)
         
         if(distF < distR):
            return (pprojF, distF)
         else: return (pprojR, distR)
         
      else:
         # check left/right flanks
         ll = TL - BL
         scale = dot2d(p, ll) / dot2d(ll, ll)
         scaleP2 = dot2d(BL, ll) / dot2d(ll, ll)
         print "Scale L/R: %.2f" % scale   
         if (0. <= scale - scaleP2 <= 1.):
            pprojL = (scale - scaleP2) * ll + BL
            distL = dist2d(p, pprojL)
            
            lri = TR - BR
            scale = dot2d(p, lri) / dot2d(lri, lri)
            scaleP2 = dot2d(BR, lri) / dot2d(lri, lri)
            pprojRi = (scale - scaleP2) * lri + BR
            distRi = dist2d(p, pprojRi)
            
            if(distL < distRi):
               return (pprojL, distL)
            else: return (pprojRi, distRi)
            
         else:
            # projection is neither on front/rear nor on left/right segments.
            # Thus one of the corners must be the closest point.
            dMin = 1.e50
            pMin = None
            
            for c in (TL, BL, BR, TR):
               d = dist2d(p, c)
               if(d < dMin):
                  dMin = d
                  pMin = c
                  
            return (pMin, dMin)
      
         
   def FinalizeMovement(self):
      if self.movementTemplate:
         # determine distance (center to center)
         d = self.movementTemplate.scenePos() - self.scenePos()
         dist = math.sqrt(d.x()**2 + d.y()**2)
         
         moveType = "freely"
         
         # determine which type of movement was executed (if any)
         if self.movementTemplate.restrictedMovementAxis:
            ax = self.movementTemplate.restrictedMovementAxis
            moveType = ax.name
            
            # determine movement distance along axis
            uVec = QtCore.QPointF( self.movementTemplate.restrictedMovementAxis.axis.x2() - self.movementTemplate.restrictedMovementAxis.axis.x1(),
                                self.movementTemplate.restrictedMovementAxis.axis.y2() - self.movementTemplate.restrictedMovementAxis.axis.y1() )
            xVec = self.movementTemplate.scenePos() - self.movementTemplate.restrictedMovementAxis.axis.p1()
            dist = dot2d(xVec, uVec) / dot2d(uVec, uVec)
            
            if moveType == "FORWARD" and dist<0:
               moveType = "BACKWARD"
               dist = -dist
            elif moveType == "SIDEWAYS":
               if dist > 0: moveType = "to the left"
               elif dist < 0:
                  moveType = "to the right"
                  dist = -dist
                  
            # BUG: moveType not working correctly, in some cases left and right are mistaken for each other.
                  
         moveType = moveType.lower()
         
         # determine rotation
         angle = self.movementTemplate.rotation() - self.rotation()
         rotType = "right"
         if angle<0:
            angle = -angle
            rotType = "left"
         if angle>180.:
            angle = 360. - angle
         
         eps = 0.05
         
         # print output, depending on whether the unit moved, rotated, or both
         if(dist > eps and angle<=eps):
            self.scene().siLogEvent.emit("%s moved %.1f\" %s." % (self.name, dist, moveType))
         elif(angle > eps and dist<=eps):
            self.scene().siLogEvent.emit("%s rotated %.0f&deg; to the %s." % (self.name, angle, rotType))
         elif(angle > eps and dist > eps):
            self.scene().siLogEvent.emit("%s moved %.1f\" %s and rotated %.0f&deg; to the %s." % (self.name, dist, moveType, angle, rotType))
         
         # finalize movement
         self.setPos(self.movementTemplate.scenePos())
         self.setRotation(self.movementTemplate.rotation())
         self.CancelMovement()

   def GetFrontArc(self):
      """ All arc polygons given in local (not scene) coordinates. """
      topLeft = self.rect().topLeft()
      topRight = self.rect().topRight()
         
      leftDir = self.rect().topLeft() + QtCore.QPointF(-100,-100)
      rightDir = self.rect().topRight() + QtCore.QPointF(100, -100)
         
      arc = QtGui.QPolygonF( [topLeft, topRight, rightDir, leftDir] )
      return arc
   
   def GetLeftArc(self):
      """ All arc polygons given in local (not scene) coordinates. """
      topLeft = self.rect().topLeft()
      bottomLeft = self.rect().bottomLeft()
         
      topDir = self.rect().topLeft() + QtCore.QPointF(-100,-100)
      bottomDir = self.rect().bottomLeft() + QtCore.QPointF(-100, 100)
         
      arc = QtGui.QPolygonF( [topLeft, topDir, bottomDir, bottomLeft] )
      return arc
   
   def GetRearArc(self):
      """ All arc polygons given in local (not scene) coordinates. """
      bottomLeft = self.rect().bottomLeft()
      bottomRight = self.rect().bottomRight()
         
      leftDir = self.rect().topLeft() + QtCore.QPointF(-100,100)
      rightDir = self.rect().topRight() + QtCore.QPointF(100,100)
         
      arc = QtGui.QPolygonF( [bottomLeft, leftDir, rightDir, bottomRight] )
      return arc
   
   def GetRightArc(self):
      """ All arc polygons given in local (not scene) coordinates. """
      topRight = self.rect().topRight()
      bottomRight = self.rect().bottomRight()
         
      topDir = self.rect().topRight() + QtCore.QPointF(100,-100)
      bottomDir = self.rect().bottomRight() + QtCore.QPointF(100,100)
         
      arc = QtGui.QPolygonF( [topRight, topDir, bottomDir, bottomRight] )
      return arc
      
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
   
   def GetNormalVectorSide(self):
      # normal vector is always (-1, 0) at center location (0, 0) in local coordinates
      normalDir = QtCore.QPointF(-1, 0)
      normalLoc = QtCore.QPointF(0, 0)
      
      # map to scene
      scNormalDir = self.mapToScene(normalDir)
      scNormalLoc = self.mapToScene(normalLoc)
      
      # return in scene coordinates
      normal = QtCore.QLineF( scNormalLoc, scNormalDir )
      
      return normal
   
   def GetUnitLeaderPoint(self):
      """ Unit leader point always returned in scene coordinates. """
      pt = QtCore.QPointF(0, -self.rect().height()/2)
      return self.mapToScene(pt)
   
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
      else: self.scene().siStatusMessage.emit("Moving %s %s." % (self.name, self.movementTemplate.restrictedMovementAxis.name))
      
      # handle movement event itself
      
      # just set to mouse position if not restricted
      if not self.movementTemplate.restrictedMovementAxis:
         self.movementTemplate.setPos(e.scenePos())
      
      # or, handle movement restricted to axis
      else: # orthogonal projection point x to axis u: P(x) = x dot u / u dot u * vec(u) 
         # vector from starting point to end point of movement axis
         uVec = QtCore.QPointF( self.movementTemplate.restrictedMovementAxis.axis.x2() - self.movementTemplate.restrictedMovementAxis.axis.x1(),
                                self.movementTemplate.restrictedMovementAxis.axis.y2() - self.movementTemplate.restrictedMovementAxis.axis.y1() )
         xVec = e.scenePos() - self.movementTemplate.restrictedMovementAxis.axis.p1()
         
         scalingFactor = dot2d(xVec, uVec) / dot2d(uVec, uVec)
         uVec *= scalingFactor
         
         self.movementTemplate.setPos( uVec + self.movementTemplate.restrictedMovementAxis.axis.p1() )
      
      # update distance counter
      d = self.movementTemplate.scenePos() - self.scenePos()
      dist = math.sqrt(d.x()**2 + d.y()**2)
      self.scene().SetDistCounter("%.1f\"" % dist, self.movementTemplate.scenePos())
      
   def InitAlignTo(self):
      if self.scene().mouseMode == MOUSE_ALIGN_TO:
         self.scene().mouseMode == MOUSE_DEFAULT
         self.scene().ResetStatusMessage()

      else:
         self.scene().mouseMode = MOUSE_ALIGN_TO
         self.scene().siStatusMessage.emit("Aligning %s." % self.name)
         
   def InitCheckDistance(self):
      if self.scene().mouseMode == MOUSE_CHECK_DIST:
         self.scene().mouseMode == MOUSE_DEFAULT
         self.scene().ResetStatusMessage()

      else:
         self.scene().mouseMode = MOUSE_CHECK_DIST
         self.scene().siStatusMessage.emit("Checking distance to %s's unit leader point." % self.name)
         
   def InitDetermineArc(self):
      if self.scene().mouseMode == MOUSE_CHECK_ARC:
         self.scene().mouseMode == MOUSE_DEFAULT
         self.scene().ResetStatusMessage()

      else:
         self.scene().mouseMode = MOUSE_CHECK_ARC
         self.scene().siStatusMessage.emit("Checking arcs for %s." % self.name)
      
   def InitRotation(self):
      if self.scene().mouseMode == MOUSE_ROTATE_UNIT:
         self.scene().mouseMode == MOUSE_DEFAULT
         self.scene().siStatusMessage.emit("%s selected." % self.name)
         self.rotationInitiated = False
      
      else:
         self.scene().mouseMode = MOUSE_ROTATE_UNIT
         self.SpawnMovementTemplate()
         self.rotationInitiated = True
         #self.SpawnRotator()
         self.scene().siStatusMessage.emit("Rotating %s. Left click to set rotation." % self.name)
      
   def RemoveMarker(self, name):
      if name in self.markers:
         self.scene().removeItem(self.markers[name])
         del self.markers[name]
      
   def RotateToPoint(self, point):
      self.SpawnMovementTemplate()
      vecToPoint = point - self.movementTemplate.scenePos()
      angle = (180. / math.pi) * math.atan2(vecToPoint.x(), -vecToPoint.y())
      
      self.movementTemplate.setRotation(angle)
      
   def SetOwner(self, owner):
      self.owner = owner
      self.setBrush(owner.color)
         
   def SpawnArcTemplates(self):
      if len(self.arcTemplates)==0:
         f = QtGui.QGraphicsPolygonItem(self.GetFrontArc())
         l = QtGui.QGraphicsPolygonItem(self.GetLeftArc())
         b = QtGui.QGraphicsPolygonItem(self.GetRearArc())
         r = QtGui.QGraphicsPolygonItem(self.GetRightArc())
         
         for fb in (f, b):
            fb.setBrush(QtGui.QColor(255,255,255,80))
         for lr in (l, r):
            lr.setBrush(QtGui.QColor(255,255,255,15))
            
         for flbr in (f,l,b,r):
            flbr.setPen(Qt.NoPen)
            flbr.setParentItem(self)
            flbr.setVisible(False)
         
         self.arcTemplates = [f,l,b,r]

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
      
   def UpdateLabel(self):
      self.label.setPlainText(self.labelText)
      if len(self.labelText)==0: return
      
      # adjust label font size
      fm = QtGui.QFontMetricsF(self.label.font())
      scale = min( self.rect().width() / fm.width(self.labelText), 0.8 * self.rect().height() / fm.height() )
      self.label.setScale(scale)
      self.label.setPos(-0.5*self.label.boundingRect().width()*self.label.scale(), -0.5*self.label.boundingRect().height()*self.label.scale())
      
   def contextMenuEvent(self, e):
      self.setSelected(True)
      self.contextMenu.exec_(e.screenPos())
   
   def itemChange(self, change, value):
      if change == QtGui.QGraphicsItem.ItemPositionChange:
         if not Qt.LeftButton & int(QtGui.QApplication.mouseButtons()):
            pass #print "Moved"
         
      return QtGui.QGraphicsItem.itemChange(self, change, value)
      
   def paint(self, painter, option, widget):
      # draw normal rect
      super(RectBaseUnit, self).paint(painter, option, widget)
      
      # determine front facing triangle coordinates
      triW, triH = 4, 0.7
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
      
      # if a formation is set, lightly draw individual bases
      if self.formation:
         painter.setPen(QtGui.QColor(0,0,0,120))
         
         dx = 1.* self.rect().width() / self.formation[0]
         for j in range(self.formation[0]-1):
             painter.drawLine(QtCore.QLineF(self.rect().left()+(j+1)*dx, self.rect().top(), self.rect().left()+(j+1)*dx, self.rect().bottom()))
         
         dy = 1.* self.rect().height() / self.formation[1]
         for i in range(self.formation[1]-1):
             painter.drawLine(QtCore.QLineF(self.rect().left(), self.rect().top()+(i+1)*dy, self.rect().right(), self.rect().top()+(i+1)*dy))
             
      # add label text
#       if self.drawLabel:
#          font = QtGui.QFont()
#          font.setPointSizeF(self.labelSize)
#          painter.setFont(font)
#          painter.setPen(QtGui.QColor(255,255,255,180))
#          painter.drawText(self.rect(), Qt.AlignCenter, self.label)
   
   def keyPressEvent(self, e):
      if e.key() == Qt.Key_R: # rotate
         e.accept()
         self.InitRotation()
            
      elif e.key() == Qt.Key_N: # align to
         e.accept()
         self.InitAlignTo()
      
      elif e.key() == Qt.Key_A: # toggle arc template
         e.accept()
         self.SpawnArcTemplates()
         for t in self.arcTemplates:
            t.setVisible(not t.isVisible())
            
      elif e.key() == Qt.Key_D: # check distance
         e.accept()
         self.InitCheckDistance()
         
      elif e.key() == Qt.Key_Return and (self.movementInitiated or self.rotationInitiated): # finalize movement
         e.accept()
         self.FinalizeMovement()
         
      elif e.key() == Qt.Key_Escape and (self.movementInitiated or self.rotationInitiated): # cancel movement
         e.accept()
         self.CancelMovement()
         self.scene().AbortMouseAction()
      
      # BUG: Restricted movement axis always related to parent unit, even if the movement template has already been rotated.
      #  However, using the movement template's frontal normal vector, self.movementTemplate.GetNormalVectorFront(), is also
      #  not working as intended, as the movement template might be already rotated AND translated.
      #  Need to work this out.
      elif e.key() == Qt.Key_F and self.movementInitiated: # restrict to forward axis
         e.accept()
         self.SpawnMovementTemplate()
         
         if not self.movementTemplate.restrictedMovementAxis or self.movementTemplate.restrictedMovementAxis.name != "FORWARD":
            self.scene().siStatusMessage.emit("Moving %s FORWARD." % self.name)
            self.movementTemplate.restrictedMovementAxis = RestrictedMovementAxis("FORWARD", self.GetNormalVectorFront())
         else:
            self.scene().siStatusMessage.emit("Moving %s." % self.name)
            self.movementTemplate.restrictedMovementAxis = None
      
      elif e.key() == Qt.Key_S and self.movementInitiated: # restrict to sideways axis
         e.accept()
         self.SpawnMovementTemplate()
         
         if not self.movementTemplate.restrictedMovementAxis or self.movementTemplate.restrictedMovementAxis.name != "SIDEWAYS":
            self.scene().siStatusMessage.emit("Moving %s SIDEWAYS." % self.name)
            self.movementTemplate.restrictedMovementAxis = RestrictedMovementAxis("SIDEWAYS", self.GetNormalVectorSide())
         else:
            self.scene().siStatusMessage.emit("Moving %s." % self.name)
            self.movementTemplate.restrictedMovementAxis = None
            
      else:
         super(RectBaseUnit, self).keyPressEvent(e)
   
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
         # Don't remove restricted axis just when releasing the mouse for a while
         #if self.movementTemplate: self.movementTemplate.restrictedMovementAxis = None
         
      super(RectBaseUnit, self).mouseReleaseEvent(e)
       
   def mouseMoveEvent(self, e):
      if Qt.LeftButton & int(e.buttons()): # left mouse dragging
         self.HandleMovementEvent(e, self)
         
class UnitContextMenu(QtGui.QMenu):
   def __init__(self, parentUnit):
      super(UnitContextMenu, self).__init__()
      self.parentUnit = parentUnit
      
      # Rotate
      rot = self.addAction(QtGui.qApp.DataManager.IconByName("ICN_ROTATE_UNIT"), "Rotate")
      rot.triggered.connect(self.parentUnit.InitRotation)
      
      # Align to
      algn = self.addAction("Align to")
      algn.triggered.connect(self.parentUnit.InitAlignTo)
         
      # Check menu
      self.checkMenu = self.addMenu("Check...")
      cdist = self.checkMenu.addAction("Distance to")
      cdist.triggered.connect(self.parentUnit.InitCheckDistance)
      carc = self.checkMenu.addAction("Arc/Facing")
      carc.triggered.connect(self.parentUnit.InitDetermineArc)
      
      # Add marker menu
      self.signalMapper = QtCore.QSignalMapper(self)
      self.addMarkerMenu = self.addMenu("Add marker...")
      for mrk in QtGui.qApp.DataManager.GetMarkers():
         act = self.addMarkerMenu.addAction(mrk.name)
         # use signal mapper to identify each action by its marker name
         self.signalMapper.setMapping(act, mrk.name)
         act.triggered.connect(self.signalMapper.map)
      # signal mapper propagates the signal to parent unit, along with the respective marker name
      self.signalMapper.mapped[str].connect(self.parentUnit.AddMarker)

class MovementTemplateContextMenu(QtGui.QMenu):
   def __init__(self):
      super(MovementTemplateContextMenu, self).__init__()
      
      self.finalizeAction = self.addAction("Finalize")
      self.cancelAction = self.addAction("Cancel")


class RestrictedMovementAxis:
   def __init__(self, name="", axis = QtCore.QLineF(0.,0.,0.,1.)):
      self.name = name
      self.axis = axis
         
class RectBaseMovementTemplate(RectBaseUnit):
   Alpha = 145
   
   def __init__(self, parentUnit):
      super(RectBaseMovementTemplate, self).__init__(name=parentUnit.name)
      self.label.hide()
      
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
      
   def RotateToPoint(self, point):
      vecToPoint = point - self.scenePos()
      angle = (180. / math.pi) * math.atan2(vecToPoint.x(), -vecToPoint.y())
      self.setRotation(angle)
      
   def SpawnMovementTemplate(self):
      # don't spawn a child template
      pass
      
   def contextMenuEvent(self, e):
      self.setSelected(True)
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
      
      #if e.button() == Qt.LeftButton:
      #   self.restrictedMovementAxis = None


class DistanceMarker(QtGui.QGraphicsLineItem):
   def __init__(self, ptFrom, ptTo):
      line = QtCore.QLineF(ptFrom, ptTo)
      super(DistanceMarker, self).__init__(line)
      #pen = self.pen()
      #pen.setWidth(1.)
      #self.setPen(pen)
      
      dist = line.length()
      self.text = QtGui.QGraphicsTextItem("%.2f\"" % dist, self)
      self.text.scale(0.15, 0.15)
      self.text.setPos((ptFrom+ptTo)*0.5) # move to middle of line
      
      
class TextLabel(QtGui.QGraphicsTextItem):
   """ Custom implementation of QGraphicsTextItem which
   propagates all mouse events to its parent, if present. """
   def __init__(self, text, parent=None):
      super(TextLabel, self).__init__(text, parent)
#       
#    def mouseMoveEvent(self, e):
#       if self.parent() is not None:
#          self.parent().mouseMoveEvent(e)
#       else: super(TextLabel, self).mouseMoveEvent(e)
#       
#    def mousePressEvent(self, e):
#       if self.parent() is not None:
#          self.parent().mousePressEvent(e)
#       else: super(TextLabel, self).mousePressEvent(e)