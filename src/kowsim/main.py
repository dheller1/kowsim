# -*- coding: utf-8 -*-
import sys

from ui import MainWindow
from PySide import QtGui

def main():
   app = QtGui.QApplication(sys.argv)

   #scene = BattlefieldScene()
   w = MainWindow()
   w.show()

   sys.exit(app.exec_())
   
#   rh = RollHandler("20d6 5+ 4+")
#   print rh.commandString
#   rh.Roll()
   return

if __name__=='__main__':
   main()
