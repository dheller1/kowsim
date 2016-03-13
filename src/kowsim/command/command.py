# -*- coding: utf-8 -*-

# command/command.py
#===============================================================================

#===============================================================================
# Command
#===============================================================================
class Command(object):
   def __init__(self, name, params={}, repeatable=False):
      self._customName = name
      self._params = params
      self._isRepeatable = repeatable
      
      self._timesExecuted = 0
      self._expectedParams = []
   
   def Execute(self):
      self.Validate()
      
      if not self._isRepeatable and self._timesExecuted>0:
         print "Warning: Non-repeatable command %s executed more than once." % self._customName
         return
      self._timesExecuted += 1
      
   def Reset(self):
      self._timesExecuted = 0
      
   def Validate(self):
      if len(self._expectedParams) < len(self._params):
         print "Warning: More parameters given to command %s than were expected." % self._customName
      
      paramsProcessed = 0
      for ep in self._expectedParams:
         epFound = False
         for p in self._params:
            try:
               ep.CheckParam(p)
               paramsProcessed += 1
               epFound = True
            except (TypeError, ValueError):
               continue
         
         if not epFound and ep.IsObligatory():
            raise ValueError("Obligatory parameter %s not present!" % ep.Name()) # implement CommandError?
         
      if paramsProcessed != len(self._params):
         print "Warning: There were %d unprocessed parameters for command %s." % (len(self._params)-paramsProcessed, self._customName)
   
   
#===============================================================================
# ReversibleCommand
#===============================================================================
class ReversibleCommand(Command):
   def __init__(self, name, params={}, reverseCmd=None):
      Command.__init__(self, name, params)
      self._reverseCmd = reverseCmd
      self._wasUndone = False
   
   def Redo(self):
      if not self._wasUndone:
         raise ValueError("Command %s cannot be redone: was not undone before." % self._customName)
      
      else:
         self.Execute()
         self._reverseCmd.Reset()
         self._wasUndone = False
   
   def Reset(self):
      Command.Reset(self)
      self._wasUndone = False
   
   def Undo(self):
      if self._timesExecuted <= 0:
         print "Warning: Tried to undo command %s which was not executed before." % self._customName
         return
       
      if self._reverseCmd:
         self._reverseCmd.Execute()
         self._timesExecuted -= 1
         self._wasUndone = True
      else:
         raise ValueError("Command %s cannot be undone: no reverse command set." % self._customName)
   
   def Validate(self):
      Command.Validate(self)
      if not self._reverseCmd:
         raise ValueError("Reversible command has no reverse command set.")


#===============================================================================
# CommandParameter
#===============================================================================
class CommandParameter(object):
   def __init__(self, name, value):
      self._customName = name
      self._value = value
      
   def Name(self): return self._customName
   def Value(self): return self._value
   
   
#===============================================================================
# ExpectedParameter
#===============================================================================
class ExpectedParameter(object):
   def __init__(self, name, isObligatory=True, description="", typeCheck=None):
      self._customName = name
      self._isObligatory = isObligatory
      self._description = description
      self._typeCheck = typeCheck
      
      self._value = None # this will be set if CheckParam is successful.
      
   def CheckParam(self, param):
      """ Check a given parameter (CommandParameter instance) if it matches
        the expected parameter syntax. Returns True if everything is okay,
        otherwise errors will be raised. """
      if self._typeCheck and type(param) not in self._typeCheck:
         raise TypeError("Parameter doesn't match expected type(s): " + ", ".join(self._typeCheck))
      
      if self._customName != param.Name():
         raise ValueError("Parameter name is %s (expected %s)." % (param.Name(), self._customName))
      
      if param is None and self._isObligatory:
         raise ValueError("No parameter given for %s but it is obligatory." % self._customName)
      
      # success? set value
      self._value = param.Value()
      return True
   
   def IsObligatory(self): return self._isObligatory
   def Name(self): return self._customName