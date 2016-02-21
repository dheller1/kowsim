# -*- coding: utf-8 -*-

from PySide import QtGui, QtCore
from PySide.QtCore import Qt

#===============================================================================
# MouseMode
#   Abstract base class for a mouse mode, associated with a name, a cursor,
#   possible operands and abstract event handlers.
#   Subclasses should reimplement the event handlers to invoke their functionality.
#===============================================================================
class MouseMode(object):
   def __init__(self, name, cursor=None):
      self.name = name
      self.operands = []
      
      self.cursor = cursor
      self.cursorLoaded = False
      
   def mouseMoveEvent(self, e, scene):
      raise TypeError("Abstract base class MouseMode instantiated.")

   def mousePressEvent(self, e, scene):
      raise TypeError("Abstract base class MouseMode instantiated.")
      
   def LoadCursor(self):
      if not self.cursorLoaded:
         self.cursor = QtGui.QCursor(QtGui.qApp.DataManager.IconByName(self.cursor).pixmap(24, 24), 0, 0)
         self.cursorLoaded = True
         
   def SetArgs(self, *args):
      self.operands = args
      print "Operands:", self.operands
      
#===============================================================================
# Default MouseMode
#   No action, default cursor.
#===============================================================================
class DefaultMouseMode(MouseMode):
   def __init__(self):
      super(DefaultMouseMode, self).__init__("Default", "NO_CURSOR")
      
#===============================================================================
# Check Distance
#   Calculate distance from selected unit to target point or target unit given
#   by cursor position.
#   If the cursor hovers another unit, the shortest distance to that unit
#   (e.g. for charging or shooting) is calculated and drawn as a marker.
#   For any other point, the distance from point to point is written out. 
#===============================================================================
class CheckDistanceMouseMode(MouseMode):
   def __init__(self):
      super(CheckDistanceMouseMode, self).__init__("Check distance", "CUR_MEASURE")
   
   def mouseMoveEvent(self, e, scene):
      target = scene.UnitAt(e.scenePos())
      
      # hovering unit? check distance, but only if no old distance marker is present
      if (target is not None) and target!=scene.SelectedItem():
         p, d = scene.SelectedItem().DistanceToUnit(target)
         scene.SetDistMarker(scene.SelectedItem().GetUnitLeaderPoint(), p)
      
      elif target is None:
         scene.SetDistMarker(scene.SelectedItem().GetUnitLeaderPoint(), e.scenePos())
      
      # no hover? remove dist marker, if present
      #elif (target is None) and scene.distMarker:
      #   scene.RemoveDistMarker()
         
   def mousePressEvent(self, e, scene):
      target = scene.UnitAt(e.scenePos())
      if (target is not None) and target!=scene.SelectedItem():
         p, d = scene.SelectedItem().DistanceToUnit(target)
         scene.siLogEvent.emit("Distance from %s's unit leader point to the closest point of %s is %.2f\"." % (scene.SelectedItem().name, target.name, d))