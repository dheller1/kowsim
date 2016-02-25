from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from player import Player

class GameManager:
   def __init__(self):
      self._players = [Player("Player 1"), Player("Player 2", QtGui.QColor(11,121,5))]
      self._curPlayer = self._players[0]
   
   def GetCurrentPlayer(self):
      return self._curPlayer
   
   def GetPlayer(self, id):
      return self._players[id]
   
   def NumPlayers(self):
      return len(self._players)