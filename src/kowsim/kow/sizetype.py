# -*- coding: utf-8 -*-

# kow/sizetype.py
#===============================================================================
class SizeType(object):
   def __init__(self, name):
      self._customName = name
      
   def Name(self): return self._customName

ST_TRP = SizeType("Troop")
ST_REG = SizeType("Regiment")
ST_HRD = SizeType("Horde")
ST_LEG = SizeType("Legion")
ST_IND = SizeType("Individual")

ALL_SIZETYPES = (ST_TRP, ST_REG, ST_HRD, ST_LEG, ST_IND)

def Find(name):
   for st in ALL_SIZETYPES:
      if name.startswith(st.Name()):
         return st
   return None