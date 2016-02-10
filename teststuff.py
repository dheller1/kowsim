import sys
from PySide import QtGui, QtCore

class MainWindowUi(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.scene = Scene(0, 0, 300, 300, self)
        self.view = QtGui.QGraphicsView()
        self.setCentralWidget(self.view)
        self.view.setScene(self.scene)
        self.scene.addItem(Square(0,0,50,50))

class Scene(QtGui.QGraphicsScene):

    def mousePressEvent(self, e):
        self.currentItem = self.itemAt(e.scenePos())
        print (self.currentItem)
        QtGui.QGraphicsScene.mousePressEvent(self, e)

class Square(QtGui.QGraphicsRectItem):
    def __init__(self, *args):
        QtGui.QGraphicsRectItem.__init__(self, *args)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        
        QtGui.QGraphicsTextItem("#", self)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = MainWindowUi()
    win.show()
    sys.exit(app.exec_())