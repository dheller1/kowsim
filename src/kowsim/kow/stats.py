# -*- coding: utf-8 -*-

# kow/stats.py
#===============================================================================
class KowStat(object):
   def __init__(self, name, short):
      self._name = name
      self._short = short
      
   def __repr__(self):
      return self._name
      
   def Name(self):
      return self._name
   
   def Abbreviation(self):
      return self._short

ST_SPEED = KowStat("Speed", "Sp")
ST_MELEE = KowStat("Melee", "Me")
ST_RANGED = KowStat("Ranged", "Ra")
ST_DEFENSE = KowStat("Defense", "De")
ST_ATTACKS = KowStat("Attacks", "At")
ST_NERVE = KowStat("Nerve", "Ne")

ALL_STATS = (ST_SPEED, ST_MELEE, ST_RANGED, ST_DEFENSE, ST_ATTACKS, ST_NERVE)

def FindStat(name):
   for a in ALL_STATS:
      if a.Name()==name or a.Abbreviation() == name:
         return a
   return None
