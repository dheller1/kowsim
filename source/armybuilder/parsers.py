# -*- coding: utf-8 -*-

# armybuilder/parsers.py
#===============================================================================
from ..util.csv_util import CsvParser
from ..kow.unit import KowUnitProfile
from ..kow.alignment import KowAlignment, Find
from ..kow.force import KowForce


class ForceListCsvParser(CsvParser):
   def __init__(self):
      super(ForceListCsvParser, self).__init__()
   
   def Parse(self):
      if self._csvLines == []: return None
      
      unitChoices = []
      
      nameParsed = False
      for row in self._csvLines:
         if len(row)==0 or row[0].startswith("#"): continue # skip comments and blank lines
         
         # parse name and alignment once
         if not nameParsed:
            name = row[0]
            alignment = Find(row[1])
            if alignment is None: raise ValueError("Unknown alignment: %s" % row[1])
            nameParsed = True
            
         # then parse unit profiles
         else:
            profile = KowUnitProfile.FromCsv(row)
            unitChoices.append(profile)

      force = KowForce(name, alignment, unitChoices)
      return force