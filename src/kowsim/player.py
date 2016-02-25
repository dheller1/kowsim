from PySide import QtGui, QtCore
from PySide.QtCore import Qt

class Player:
   def __init__(self, name="Player 1", color=QtGui.QColor(34,134,219)):
      self.name = name
      self.color = color