# -*- coding: utf-8 -*-

# util/core.py
#===============================================================================
import math

# reverse dictionary by swapping keys and values.
# !make sure only to use in bijective mapping!
def reverseDict(d):
   return {v:k for k, v in d.iteritems()}


def dot2d(vec1, vec2):
   return vec1.x() * vec2.x() + vec1.y() * vec2.y()
 
def len2d(vec):
   return math.sqrt( vec.x()*vec.x() + vec.y()*vec.y() )
 
def dist2d(p1, p2):
   dx = p1.x() - p2.x()
   dy = p1.y() - p2.y()
   return math.sqrt( dx**2 + dy**2 )


#===============================================================================
# Size:
#   A 2D size object, i.e. width/height dimensions. Arguments can be float or
#   integer but should support the same operations.
#===============================================================================
class Size(object):
   def __init__(self, *args):
      
      if len(args) == 2:
         self._w = args[0]
         self._h = args[1]
         
      elif len(args) == 1:
         self._w = args[0][0]
         self._h = args[0][1]
      
      else:
         self._w = 0.
         self._h = 0.
         
   def __repr__(self):
      if type(self._w) is int:
         return "Size(%d, %d)" % (self._w, self._h)
      else:
         return "Size(%.2f, %.2f)" % (self._w, self._h)
   
   # Getters
   def W(self): return self._w
   def H(self): return self._h
   
   # derived properties
   def Area(self): return self._w * self._h