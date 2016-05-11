# -*- coding: utf-8 -*-

# kow/stats.py
#===============================================================================
class KowStat(object):
   """ Class representing a stat in a KoW unit profile, such as Speed, Melee or Nerve.
   
   Should not be called directly. Instead, use the module instances ST_SPEED, ST_MELEE,
   ST_RANGED, ST_DEFENSE, ST_ATTACKS, ST_NERVE (assembled in ALL_STATS) to allow
   equality-checking.
   Currently, objects of this class only comprises a name and an abbreviation of a stat.
   Later on, stats could include further information, such as if they represent a d6 roll
   like Me 4+, or a composite stat such as Nerve with a waiver and a break value.
   
   :param name: Name of the stat (e.g. 'Speed', 'Attacks')
   :type name: str
   :param short: Abbreviation of the stat's name (e.g. 'Sp', 'At')
   :type short: str 
   """
   def __init__(self, name, short):
      self._name = name
      self._short = short
      
   def __repr__(self):
      return self._name
      
   def Name(self):
      """ :return: str -- Name"""
      return self._name
   
   def Abbreviation(self):
      """ :return: Abbreviation (2-character string)"""
      return self._short

ST_SPEED = KowStat("Speed", "Sp")
ST_MELEE = KowStat("Melee", "Me")
ST_RANGED = KowStat("Ranged", "Ra")
ST_DEFENSE = KowStat("Defense", "De")
ST_ATTACKS = KowStat("Attacks", "At")
ST_NERVE = KowStat("Nerve", "Ne")

ALL_STATS = (ST_SPEED, ST_MELEE, ST_RANGED, ST_DEFENSE, ST_ATTACKS, ST_NERVE)

def FindStat(name):
   """ Find one of the pre-created stat objects by its name.
   
   :param name: Name of the stat (e.g. 'Speed', 'Attacks')
   :type name: str
   :return: KowStat -- Corresponding object, if it is found, **None** otherwise
   """
   for a in ALL_STATS:
      if a.Name()==name or a.Abbreviation() == name:
         return a
   return None
