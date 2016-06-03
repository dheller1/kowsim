# -*- coding: utf-8 -*-

# kow/widgets.py
#===============================================================================
import os

from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from command import AddSpecificUnitCmd, ChangeUnitCmd, ChangeUnitSizeCmd, ChangeUnitItemCmd, SetUnitOptionsCmd
from kowsim.kow.unittype import ALL_UNITTYPES
from kowsim.kow.validation import ArmyListValidator, ValidationMessage, ALL_VALIDATIONRULES 
from kowsim.mvc.mvcbase import View
import kowsim.kow.stats as st
import globals 


#===============================================================================
# UnitTable
#===============================================================================
class UnitTable(QtGui.QTableWidget):
   siPointsChanged = QtCore.Signal()
   siAddUnitRequested = QtCore.Signal(str)
   siModified = QtCore.Signal(bool)
   DefaultRowHeight = 22
   
   def __init__(self, model, armyCtrl):
      QtGui.QTableWidget.__init__(self)
      self._armyCtrl = armyCtrl
      self._model = model # Detachment object
      self._columns = ("Unit", "Type", "Size", "Sp", "Me", "Ra", "De", "At", "Ne", "Points", "Special", "Magic item", "Options")
      self._colWidths = {"Unit": 170, "Type": 90, "Size": 80, "Sp": 30, "Me": 30, "Ra": 30, "De": 30, "At": 30, "Ne": 45, "Points": 45, "Special": 350, "Magic item": 200, "Options": 50}
      self.setColumnCount(len(self._columns))
      self.verticalHeader().hide()
      self.setHorizontalHeaderLabels(self._columns)
      for idx, col in enumerate(self._columns):
         self.setColumnWidth(idx, self._colWidths[col])
      self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
      
      self.setAcceptDrops(True) # for unit browser drag&drop
      
   def dragEnterEvent(self, e):
      if e.mimeData().hasFormat("text/plain"):
         e.acceptProposedAction()
      else:
         super(UnitTable, self).dragEnterEvent(e)
      
   def dragMoveEvent(self, e):
      if e.mimeData().hasFormat("text/plain"):
         e.acceptProposedAction()
      else:
         super(UnitTable, self).dragMoveEvent(e)
         
   def dropEvent(self, e):
      if e.mimeData().hasFormat("text/plain"):
         e.acceptProposedAction()
         self.siAddUnitRequested.emit(e.mimeData().text())
   
   def ChangeItem(self):
      sender = self.sender()
      row = sender.rowForWidget
      unit = self._model.Unit(row)
      
      itemName = self.cellWidget(row, self._columns.index("Magic item")).currentText()

      if itemName == "-":
         item = None
      else:
         # extract item name by stripping the points cost (e.g. 'Brew of Strength (30p)')
         leftBracket = itemName.index('(')
         itemName = itemName[:leftBracket].strip()
         item = QtGui.qApp.DataManager.ItemByName(itemName)
         
      cmd = ChangeUnitItemCmd(unit, item)
      self._armyCtrl.AddAndExecute(cmd)
   
   def ChangeOptions(self):
      optMenu = self.sender()
      row = optMenu.rowForWidget
      unit = self._model.Unit(row)
      
      chosenOpts = []
      for act in optMenu.actions():
         opt = act.option # option reference was previously saved in the QAction object
         if act.isChecked():
            chosenOpts.append(opt)
      
      cmd = SetUnitOptionsCmd(self._armyCtrl.model, unit, chosenOpts)
      self._armyCtrl.AddAndExecute(cmd)
      
   def ChangeUnit(self, newindex):
      sender = self.sender() # determine which exact combobox was changed
      row = sender.rowForWidget
      
      newUnitName = self.cellWidget(row, self._columns.index("Unit")).currentText()
      cmd = ChangeUnitCmd(self._armyCtrl.model, self._model, row, newUnitName)
      self._armyCtrl.AddAndExecute(cmd)
      
   def ChangeSize(self, newindex):
      sender = self.sender() 
      row = sender.rowForWidget
      
      newSizeStr = self.cellWidget(row, self._columns.index("Size")).currentText()
      unit = self._model.ListUnits()[row]
      
      cmd = ChangeUnitSizeCmd(self._armyCtrl.model, unit, newSizeStr)
      self._armyCtrl.AddAndExecute(cmd)
      
   def SelectedUnits(self):
      return [self._model.ListUnits()[row] for row in self.SelectedRows()]
      
   def SelectedRows(self):
      rows = []
      for itm in self.selectedItems():
         if itm.row() not in rows:
            rows.append(itm.row())
      return rows
      
   def SetRow(self, row, unit):
      if row>=self.rowCount():
         self.insertRow(row)
      
      for col in range(self.columnCount()):
         olditm = self.item(row, col)
         if olditm is not None:
            del olditm
         oldwdg = self.cellWidget(row, col)
         if oldwdg is not None:
            del oldwdg
            
      self.setRowHeight(row, UnitTable.DefaultRowHeight)
            
      for col in [self._columns.index(s) for s in ("Type", "Sp", "Me", "Ra", "De", "At", "Ne", "Points", "Special")]:
         self.setItem(row, col, QtGui.QTableWidgetItem())
         self.item(row, col).setFlags(self.item(row, col).flags() ^ Qt.ItemIsEditable) # remove editable flag)
         
      for col in [self._columns.index(s) for s in ("Type", "Sp", "Me", "Ra", "De", "At", "Ne", "Points")]:   
         self.item(row, col).setTextAlignment(Qt.AlignCenter)
      
      self.UpdateTextInRow(row)
      
      # unit options
      unitCb = QtGui.QComboBox()
      for unitgroup in unit.Detachment().Choices().ListGroups():
         unitCb.addItem(unitgroup.Name())
      self.setCellWidget(row, self._columns.index("Unit"), unitCb)
      unitCb.rowForWidget = row
      unitCb.setCurrentIndex(unitCb.findText(unit.Profile().Name()))
   
      # size type options
      sizeCb = QtGui.QComboBox()
      for profile in unit.Detachment().Choices().GroupByName(unit.Profile().Name()).ListOptions():
         sizeCb.addItem(profile.SizeType().Name())
      self.setCellWidget(row, self._columns.index("Size"), sizeCb)
      sizeCb.rowForWidget = row
      sizeCb.setCurrentIndex(sizeCb.findText(unit.SizeType().Name()))
      if sizeCb.count()==1:
         sizeCb.setEnabled(False)
      
      # magic item
      itemCb = QtGui.QComboBox()
      itemCb.rowForWidget = row
      itemCb.addItem("-")
      if unit.CanHaveItem():
         itemCb.addItems(["%s (%dp)" % (itm.Name(), itm.PointsCost()) for itm in QtGui.qApp.DataManager.ListItems()])
         itemCb.setEnabled(True)
      else:
         itemCb.setEnabled(False)
      self.setCellWidget(row, self._columns.index("Magic item"), itemCb)
      if unit.Item(): itemCb.setCurrentIndex(itemCb.findText(unit.Item().StringWithPoints()))
      
      # options
      self.UpdateUnitOptions(row)
      
      # after everything has been set, register connections
      unitCb.currentIndexChanged.connect(self.ChangeUnit)
      sizeCb.currentIndexChanged.connect(self.ChangeSize)
      itemCb.currentIndexChanged.connect(self.ChangeItem)
   
   def SetModified(self, modified=True):
      self.siModified.emit(modified)
      
   def UpdateUnitOptions(self, row):
      unit = self._model.Unit(row)
      
      # overwrite old options pb
      optPb = QtGui.QPushButton("...")
      self.setCellWidget(row, self._columns.index("Options"), optPb)
      optPb.setStyleSheet("border-style: none;")
      
      if len(unit.Profile().ListOptions())==0:
         optPb.setEnabled(False)
         optPb.setText("-")
      else:
         optMenu = QtGui.QMenu(optPb)
         optMenu.rowForWidget = row
         optPb.setMenu(optMenu)
         for opt in unit.Profile().ListOptions():
            act = optMenu.addAction(opt.DisplayStr())
            act.setCheckable(True)
            act.option = opt # just save corresponding UnitOption object inside the QAction
            if opt in unit.ListChosenOptions():
               act.setChecked(True)
         optMenu.triggered.connect(self.ChangeOptions)
      
   def UpdateTextInRow(self, row):
      """ Updates each TableWidgetItem where only text is displayed but
      leaves more complex CellWidgets (e.g. combo boxes) untouched. """
      unit = self._model.Unit(row)
      
      self.item(row, self._columns.index("Type")).setText(unit.UnitType().Name())
      self.item(row, self._columns.index("Sp")).setText("%d" % unit.Sp())
      self.item(row, self._columns.index("Me")).setText(unit.MeStr())
      self.item(row, self._columns.index("Ra")).setText(unit.RaStr())
      self.item(row, self._columns.index("De")).setText(unit.DeStr())
      self.item(row, self._columns.index("At")).setText(unit.AtStr())
      self.item(row, self._columns.index("Ne")).setText(unit.NeStr())
      self.item(row, self._columns.index("Points")).setText("%d" % unit.PointsCost())
      
      # determine font weight
      normalFont = self.item(row, self._columns.index("Special")).font()
      boldFont = QtGui.QFont(normalFont)
      boldFont.setWeight(QtGui.QFont.Bold)
      
      self.item(row, self._columns.index("Sp")).setFont( boldFont if unit.HasStatModifier(st.ST_SPEED) else normalFont )
      self.item(row, self._columns.index("Me")).setFont( boldFont if unit.HasStatModifier(st.ST_MELEE) else normalFont )
      self.item(row, self._columns.index("Ra")).setFont( boldFont if unit.HasStatModifier(st.ST_RANGED) else normalFont )
      self.item(row, self._columns.index("De")).setFont( boldFont if unit.HasStatModifier(st.ST_DEFENSE) else normalFont )
      self.item(row, self._columns.index("At")).setFont( boldFont if unit.HasStatModifier(st.ST_ATTACKS) else normalFont )
      self.item(row, self._columns.index("Points")).setFont( boldFont if unit.HasPointsCostModifier() else normalFont )
      
      specialText = ", ".join(unit.ListSpecialRules())
      if len(unit.ListChosenOptions())>0:
         optsText = ", ".join(["%s" % o.Name() for o in unit.ListChosenOptions()])
         specialText += ", " + optsText
      self.item(row, self._columns.index("Special")).setText(specialText)
      self.item(row, self._columns.index("Special")).setToolTip(specialText)
            

#===============================================================================
# ValidationWidget
#===============================================================================
class ValidationWidget(View):
   def __init__(self, armyCtrl, parent=None):
      super(ValidationWidget, self).__init__(armyCtrl, parent)
      
      self._validator = ArmyListValidator(armyCtrl.model.data, ALL_VALIDATIONRULES) # FIXME: Direct data access really necessary?
      self.setMinimumWidth(300)
      self.setFixedHeight(150)
      
      # child widgets
      self._messageLw = QtGui.QListWidget()
      #self._messageLw.setFixedHeight(130)
      #self.pointsTotalLbl = QtGui.QLabel("Total points: <b>0</b>/2000")
      
      # layout
      lay = QtGui.QGridLayout()
      lay.addWidget(self._messageLw)
      self.setLayout(lay)
      
      self.UpdateContent()
      
   @staticmethod
   def ListWidgetItemForMessage(message):
      ICN_ERROR16 = QtGui.QIcon(os.path.join(globals.BASEDIR, "data", "icons", "no16.png"))
      ICN_INFO16 = QtGui.QIcon(os.path.join(globals.BASEDIR, "data", "icons", "info16.png"))
      icnForMsgType = {ValidationMessage.VM_INFO : ICN_INFO16, ValidationMessage.VM_CRITICAL : ICN_ERROR16, ValidationMessage.VM_WARNING : QtGui.QIcon() }
      lwi = QtGui.QListWidgetItem(icnForMsgType[message._msgType], message._shortDesc)
      lwi.setToolTip(message._longDesc)
      return lwi
      
   def UpdateContent(self, hints=None):
      messages = self._validator.Check()
      self._messageLw.clear()
      valid = True
      warnings = False
      for msg in messages:
         self._messageLw.addItem(ValidationWidget.ListWidgetItemForMessage(msg))
         if msg._msgType == ValidationMessage.VM_CRITICAL: valid = False
         if msg._msgType == ValidationMessage.VM_WARNING: warnings = True
      
      if not valid:
         self._messageLw.addItem("Errors occured - army list is invalid.")
      elif warnings:
         self._messageLw.addItem("Army list is valid, but warnings occured.")
      else:
         self._messageLw.addItem("Army list is valid.")
   
         
#===============================================================================
# UnitBrowserWidget
#===============================================================================
class UnitBrowserWidget(QtGui.QDockWidget):
   siWasClosed = QtCore.Signal() # emitted to sync with 'View unit browser' menu option/setting
   
   def __init__(self, parent=None):
      super(UnitBrowserWidget, self).__init__("Unit browser", parent)
      self.setObjectName("UnitBrowser")
      self._ctrlContext = None # points to the army list control to which the unit browser was linked, such that if a unit shall be added it will be added to the right army list
      self._detContext = None  # points to the detachment which is linked with the unit browser so that a unit can be added to the right detachment
      
      self.listWdg = UnitBrowserTreeWidget(self)
      self.setWidget(self.listWdg)
      self.listWdg.itemDoubleClicked[QtGui.QTreeWidgetItem, int].connect(self.AddUnitTriggered)
      
   def closeEvent(self, e):
      self.siWasClosed.emit() # notify to allow settings/menus to be updated
      return super(UnitBrowserWidget, self).closeEvent(e)
   
   def AddUnitTriggered(self, item, col):
      if not item or not item.parent(): # top level items are just unit type groups, they can't be added themselves
         return
      unitname = item.text(col)
      cmd = AddSpecificUnitCmd(alModel=self._ctrlContext.model, detachment=self._detContext, unitname=unitname)
      self._ctrlContext.AddAndExecute(cmd)
   
   def Update(self, detContext=None, ctrlContext=None):
      if detContext is self._detContext:
         return # do nothing to not waste performance
      self.listWdg.clear()
      if detContext is None:
         self.listWdg.setHeaderLabel("No detachment active")
         self._ctrlContext = None
         self._detContext = None
      else:
         self._ctrlContext = ctrlContext
         self._detContext = detContext
         choices = detContext.Choices()
         self.listWdg.setHeaderLabel(choices.Name())
         for ut in ALL_UNITTYPES:
            units = choices.ListUnitsForType(ut)
            if len(units)>0:
               tli = QtGui.QTreeWidgetItem(self.listWdg, [ut.PluralName()])
               self.listWdg.addTopLevelItem(tli)
               for u in units:
                  tli.addChild(QtGui.QTreeWidgetItem(tli, [u.Name()]))
         self.listWdg.expandAll()
         
         
class UnitBrowserTreeWidget(QtGui.QTreeWidget):
   """ Overridden QTreeWidget for the unit browser with custom drag&drop capabilities. """
   def __init__(self, parent=None):
      super(UnitBrowserTreeWidget, self).__init__(parent)
      self.setColumnCount(1)
      self.setHeaderLabel("No detachment active")
      self.dragStartPosition = None
      self.dragItem = None
      
   def mousePressEvent(self, e):
      startDrag = False
      if e.button() == Qt.LeftButton:
         itm = self.itemAt(e.pos())
         if itm and itm.parent(): # don't drag top-level items (i.e. unit categories)
            self.dragItem = itm
            self.dragStartPosition = e.pos()
            startDrag = True
            
      if not startDrag:
         self.dragItem = None
         self.dragStartPosition = None
      
      super(UnitBrowserTreeWidget, self).mousePressEvent(e)
      
   def mouseMoveEvent(self, e):
      if e.buttons() & Qt.LeftButton and self.dragStartPosition and self.dragItem:
         dist = (e.pos() - self.dragStartPosition).manhattanLength()
         if dist > QtGui.QApplication.startDragDistance():
            # start drag
            lbl = QtGui.QLabel(self.dragItem.text(0))
            pm = QtGui.QPixmap(lbl.size())
            lbl.render(pm)
            md = QtCore.QMimeData()
            md.setText(self.dragItem.text(0))
            drag = QtGui.QDrag(self)
            drag.setMimeData(md)
            drag.setPixmap(pm)
            drag.exec_(Qt.CopyAction)
            
            self.dragItem = None
            self.dragStartPosition = None