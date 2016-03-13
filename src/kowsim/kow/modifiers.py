# -*- coding: utf-8 -*-

# kow/modifiers.py
#===============================================================================


#===============================================================================
# KowModifiers
#   Represents modifier which may either set or add to/subtract from a
#   stat.
#===============================================================================
class KowModifier(object):
   def __init__(self, name):
      self._customName = name
      
MOD_SET = KowModifier("Set to")
MOD_ADD = KowModifier("Add to")