# -*- coding: utf-8 -*-

# kow/alignment.py
#===============================================================================
class KowAlignment(object):
   def __init__(self, name):
      self._name = name
      
   def Name(self):
      return self._name

AL_GOOD = KowAlignment("Good")
AL_NEUT = KowAlignment("Neutral")
AL_EVIL = KowAlignment("Evil")

ALL_ALIGNMENTS = (AL_GOOD, AL_NEUT, AL_EVIL)

def Find(name):
   for a in ALL_ALIGNMENTS:
      if a.Name().startswith(name):
         return a
   return None
