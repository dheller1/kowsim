# -*- coding: utf-8 -*-

# kow/specialrule.py
#===============================================================================
class GenericSpecialRule(object):
   """ A special rule in the KoW sense such as Elite or Crushing Strength (1).
    Special rules can be identified by their (unique) name, they can have a description,
    and they might have a parameter, such as Random Attacks (D6), and might be cumulative,
    such as Piercing(2). """
   def __init__(self, name, desc, param=None, cumulative=False):
      self._name = name
      self._description = desc
      self._param = param
      self._isCumulative = cumulative
     
      
   def __repr__(self):
      return self._name
      
   def Name(self):
      return self._name
   
   def Description(self):
      return self._desc
