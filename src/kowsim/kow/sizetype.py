# -*- coding: utf-8 -*-

# kow/sizetype.py
#===============================================================================
class KowSizeType(object):
   def __init__(self, name):
      self._name = name
      
   def Name(self): return self._name

ST_TRP = KowSizeType("Troop")
ST_REG = KowSizeType("Regiment")
ST_HRD = KowSizeType("Horde")
ST_LEG = KowSizeType("Legion")
ST_IND = KowSizeType("Individual")

ALL_SIZETYPES = (ST_TRP, ST_REG, ST_HRD, ST_LEG, ST_IND)

def Find(name):
   for st in ALL_SIZETYPES:
      if name.startswith(st.Name()):
         return st
   return None