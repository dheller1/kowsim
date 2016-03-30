# -*- coding: utf-8 -*-

# kow/unittype.py
#===============================================================================
class KowUnitType(object):
   def __init__(self, name, plural=None):
      self._name = name
      self._plural = plural if plural is not None else name
   
   def __repr__(self): return "KowUnitType(%s)" % self._name
   
   def Name(self): return self._name
   def PluralName(self): return self._plural

UT_INF = KowUnitType("Infantry")
UT_CAV = KowUnitType("Cavalry")
UT_LINF = KowUnitType("Large Infantry")
UT_LCAV = KowUnitType("Large Cavalry")
UT_WENG = KowUnitType("War Engine", "War Engines")
UT_MON = KowUnitType("Monster", "Monsters")
UT_HERO = KowUnitType("Hero", "Heroes")

ALL_UNITTYPES = (UT_INF, UT_CAV, UT_LINF, UT_LCAV, UT_WENG, UT_MON, UT_HERO)

def Find(name):
   for ut in ALL_UNITTYPES:
      if ut.Name().startswith(name):
         return ut
   return None