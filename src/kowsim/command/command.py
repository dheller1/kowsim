# -*- coding: utf-8 -*-

# command/command.py
#===============================================================================

#===============================================================================
# Command
#===============================================================================
class Command(object):
   def __init__(self, name):
      self._name = name
      
   def Execute(self):
      raise NotImplementedError
   
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
      self._timesExecuted = 0
      self._timesUndone = 0
   
   def Redo(self):
      raise NotImplementedError
   
   def Undo(self):
      raise NotImplementedError