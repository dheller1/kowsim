import os, codecs
from sets import Set
from util import unicode_csv_reader, utf_8_encoder
from kow_logic import KowUnitType, KowUnitSize

def ReadLinesFromCsv(filename, codepage='utf-8'):
      csvLines = []
      with codecs.open(filename, 'r', codepage) as f:
         csvReader = unicode_csv_reader(f, delimiter=',')
         csvLines = [line for line in csvReader]
         
      return csvLines
   
class DataManager:
   def __init__(self):
      self._unitTypes = None
      self._unitTypesByName = None
      
   def GetUnitTypes(self):
      if not self._unitTypes:
         self.LoadUnitTypes()
      
      return self._unitTypes
   
   def UnitTypeByName(self, name):
      if not self._unitTypesByName:
         self.LoadUnitTypes()
      
      return self._unitTypesByName[name]
   
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