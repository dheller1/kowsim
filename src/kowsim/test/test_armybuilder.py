# -*- coding: utf-8 -*-

# test/test_armybuilder.py
#===============================================================================
import unittest
import os
import sys
from PySide import QtGui, QtCore
from PySide.QtCore import Qt
from kowsim.armybuilder.mvc.models import ArmyListModel
from kowsim.armybuilder.views import ArmyListView
from kowsim.armybuilder.control import ArmyListCtrl
from kowsim.kow.force import Detachment
import kowsim.armybuilder.main as AB_Main
import kowsim.armybuilder.globals
from kowsim.armybuilder.command import AddDefaultUnitCmd, AddSpecificUnitCmd,\
   SaveArmyListCmd, LoadArmyListCmd


#===============================================================================

app = QtGui.QApplication(sys.argv)

class ArmybuilderTestCase(unittest.TestCase):
   def setUp(self):
      self.mainWnd = AB_Main.MainWindow()
      self.mainWnd.show()
      
   def tearDown(self):
      del self.mainWnd
      

class ArmyListTestCase(ArmybuilderTestCase):      
   def setUp(self):
      global __qApp
      ArmybuilderTestCase.setUp(self)
      self.alModel = ArmyListModel("TestArmy", 1500)
      self.alModel.data.AddDetachment(Detachment(app.DataManager.ForceChoicesByName("Elves")))
      
      self.alView = ArmyListView(ArmyListCtrl(self.alModel))
      self.alCtrl = self.alView.ctrl
      self.mainWnd.mdiArea.addSubWindow(self.alView)
      self.alView.show() # important!
      self.alView.showMaximized()
      
      # connect
      self.alView.siRecentFilesChanged.connect(app.MainMenu.UpdateRecent)
      self.alView.siCurrentDetachmentChanged.connect(app.MainWindow.CurrentDetachmentChanged)
      
      QtGui.qApp.MainWindow.CurrentDetachmentChanged()


class AddDefaultUnitTestCase(ArmyListTestCase):
   def runTest(self):
      cmd = AddDefaultUnitCmd(self.alModel, self.alModel.data.ListDetachments()[0])
      self.alCtrl.AddAndExecute(cmd)
      
      
class AddValidSpecificUnitTestCase(ArmyListTestCase):
   """ Test if adding a unit is possible. """
   def runTest(self):
      cmd = AddSpecificUnitCmd(self.alModel, self.alModel.data.ListDetachments()[0], "Stormwind Cavalry")
      self.alCtrl.AddAndExecute(cmd)
      self.assertEqual(self.alModel.data.ListDetachments()[0].NumUnits(), 1)
      self.assertEqual(self.alModel.data.PointsTotal(), self.alModel.data.ListDetachments()[0].PointsTotal())


class AddInvalidSpecificUnitTestCase(ArmyListTestCase):
   """ Test if adding a unit with an invalid name leads to a key error. """
   def runTest(self):
      with self.assertRaises(KeyError): # this unit does not exist
         cmd = AddSpecificUnitCmd(self.alModel, self.alModel.data.ListDetachments()[0], "Silverguard")
         self.alCtrl.AddAndExecute(cmd)
         
         
class SaveArmyListTestCase(AddValidSpecificUnitTestCase):
   """ Test if, after adding a unit to a detachment, the army list can be saved. """
   def runTest(self):
      settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
      preferredFolder = settings.value("preferred_folder")
      AddValidSpecificUnitTestCase.runTest(self) # first add something to the army list
      self.alView._lastFilename = os.path.join(preferredFolder, "unittest_list.lst") # specify filename to suppress "saveAs" dialog
      cmd = SaveArmyListCmd(self.alModel, self.alView)
      cmd.Execute()
      
      
class SaveAndReloadArmyListTestCase(SaveArmyListTestCase):
   """ Test if an army list can be saved, closed and reloaded. """
   def runTest(self):
      settings = QtCore.QSettings("NoCompany", "KowArmyBuilder")
      preferredFolder = settings.value("preferred_folder")
      SaveArmyListTestCase.runTest(self)
      oldPts = self.alModel.data.PointsTotal()
      oldNumUnits = self.alModel.data.ListDetachments()[0].NumUnits()
      self.mainWnd.mdiArea.closeAllSubWindows() # somehow this is necessary instead of self.alView.close()
      cmd = LoadArmyListCmd(self.mainWnd.mdiArea)
      newAlView = cmd.Execute(os.path.join(preferredFolder, "unittest_list.lst"))
      # check that the models are equal
      self.assertEqual(newAlView.ctrl.model.data.PointsTotal(), oldPts)
      self.assertEqual(newAlView.ctrl.model.data.ListDetachments()[0].NumUnits(), oldNumUnits)


if __name__=='__main__':
   AB_Main.initDefaultSettings()
   kowsim.armybuilder.globals.LoadSettings()
   unittest.main()
   