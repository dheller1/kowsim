# -*- coding: utf-8 -*-

# command/command.py
#===============================================================================

#===============================================================================
# Command
#===============================================================================
class Command(object):
   def __init__(self, name):
      self._name = name
      self._reversible = False
      
   def __repr__(self):
      return self._name
      
   def Execute(self):
      raise NotImplementedError
   
   def IsReversible(self): return self._reversible
   
#===============================================================================
# ModelViewCommand
#===============================================================================
class ModelViewCommand(Command):
   def __init__(self, model, view, name):
      Command.__init__(self, name)
      self._model = model
      self._view = view
   
#===============================================================================
# ReversibleCommandMixin
#===============================================================================
class ReversibleCommandMixin(object):
   def __init__(self):
      self._reversible = True
      self._timesExecuted = 0
      self._timesUndone = 0
   
   def Redo(self):
      raise NotImplementedError
   
   def Undo(self):
      raise NotImplementedError