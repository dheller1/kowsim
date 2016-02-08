import os, codecs

from PySide import QtGui

from sets import Set
from util import unicode_csv_reader, utf_8_encoder
from kow_logic import KowUnitType, KowUnitSize

def ReadLinesFromCsv(filename, codepage='utf-8'):
      csvLines = []
      with codecs.open(filename, 'r', codepage) as f:
         csvReader = unicode_csv_reader(f, delimiter=',')
         csvLines = [line for line in csvReader]
         
      return csvLines
   
class Marker:
   def __init__(self, name, pixmap, bgcolor, cumulative=True):
      self.name = name
      self.pixmap = pixmap
      self.bgColor = bgcolor
      self.cumulative = cumulative
   
class DataManager:
   def __init__(self):
      self._unitTypes = None
      self._unitTypesByName = None
      self._markers = None
      self._markersByName = None
      self._icons = None
      self._iconsByName = None
      
   def GetUnitTypes(self):
      if not self._unitTypes:
         self.LoadUnitTypes()
      
      return self._unitTypes
   
   def GetMarkers(self):
      return self._markers
   
   def GetIcons(self):
      return self._icons
   
   def MarkerByName(self, name):
      return self._markersByName[name]
   
   def UnitTypeByName(self, name):
      if not self._unitTypesByName:
         self.LoadUnitTypes()
      
      return self._unitTypesByName[name]
   
   def IconByName(self, name):
      return self._iconsByName[name]
   
   def LoadBaseSizes(self, filename = os.path.join("data", "base_sizes.csv")):
      if not self._unitTypes:
         self.LoadUnitTypes()
      
      lines = ReadLinesFromCsv(filename)
      
      for line in lines:
         if line[0].startswith("#"): continue
         
         unitType = line[0]
         width = int(line[1])
         depth = int(line[2])
         
         self._unitTypesByName[unitType].availableBaseSizes.append( (width, depth) )
         
   def LoadIcons(self, filename = os.path.join("data", "icons", "icons.csv")):
      lines = ReadLinesFromCsv(filename)
      
      self._icons = []
      self._iconsByName = {}
       
      for line in lines:
         if line[0].startswith("#"): continue
         
         name = line[0]
         imgFile = line[1]
         
         # check if file is existent
         f = open(os.path.join("data","icons",imgFile))
         f.close()
         
         icn = QtGui.QIcon(os.path.join("data","icons",imgFile))
         self._icons.append(icn)
         self._iconsByName[name] = icn
      
   def LoadMarkers(self, filename = os.path.join("data", "markers", "markers.csv")):
      lines = ReadLinesFromCsv(filename)
      
      self._markers = []
      self._markersByName = {}
       
      for line in lines:
         if line[0].startswith("#"): continue
         
         name = line[0]
         imgFile = line[1]
         bgColor = (int(line[2]),int(line[3]),int(line[4]),int(line[5]))
         cumulative = (line[6]=="yes")
         
         # check if file is existent
         f = open(os.path.join("data","markers",imgFile))
         f.close()
         
         bgColor = QtGui.QColor(bgColor[0],bgColor[1],bgColor[2],bgColor[3])
         pixmap = QtGui.QPixmap(os.path.join("data", "markers", imgFile))
         
         mrk = Marker(name, pixmap, bgColor, cumulative)
         self._markers.append(mrk)
         self._markersByName[name] = mrk
         
   
   def LoadUnitTypes(self, filename = os.path.join("data", "unit_types.csv")):
      lines = ReadLinesFromCsv(filename)
      
      unitTypes = []
      unitTypeByName = {}
      
      for line in lines:
         if line[0].startswith("#"): continue
         
         typeName = line[0]
         unitSize = line[1]
         width = int(line[2])
         depth = int(line[3])
         
         if typeName not in unitTypeByName:
            newUnitType = KowUnitType(typeName)
            unitTypes.append(newUnitType)
            unitTypeByName[typeName] = newUnitType
         
         unitTypeByName[typeName].availableSizes.append(KowUnitSize(unitSize, (width, depth)))

      self._unitTypes = unitTypes
      self._unitTypesByName = unitTypeByName