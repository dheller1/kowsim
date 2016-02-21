# -*- coding: utf-8 -*-

# kow/items.py
#===============================================================================


#===============================================================================
# KowItem
#   Represents a magic item in Kow with a name (e.g. Brew of Strenght) and
#   an associated points cost (e.g. 30).
#===============================================================================
class KowItem(object):

   def __init__(self, name, points, description=""):
      self._name = name
      self._pointsCost = points
      self._description = description

   def Description(self): return self._description   
   def Name(self): return self._name
   def PointsCost(self): return self._pointsCost

   @staticmethod
   def FromCsv(cols):
      """ Generate from a CSV row (individual columns given as list). """
      if len(cols)<3: 
         raise ValueError("Insufficient number of values (%d)." % len(cols))
         return None
      
      name = cols[0]
      description = cols[1]
      points = int(cols[2])
      return KowItem(name, points, description)