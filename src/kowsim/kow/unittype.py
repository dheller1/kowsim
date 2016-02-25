# -*- coding: utf-8 -*-

# kow/unittype.py
#===============================================================================
class KowUnitType(object):
   def __init__(self, name):
      self._name = name
   
   def Name(self): return self._name

UT_INF = KowUnitType("Infantry")
UT_CAV = KowUnitType("Cavalry")
UT_LINF = KowUnitType("Large Infantry")
UT_LCAV = KowUnitType("Large Cavalry")
UT_WENG = KowUnitType("War Engine")
UT_MON = KowUnitType("Monster")
UT_HERO = KowUnitType("Hero")

ALL_UNITTYPES = (UT_INF, UT_CAV, UT_LINF, UT_LCAV, UT_WENG, UT_MON, UT_HERO)

def Find(name):
   for ut in ALL_UNITTYPES:
      if ut.Name().startswith(name):
         return ut
   return None