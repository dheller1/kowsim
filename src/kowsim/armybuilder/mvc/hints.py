# -*- coding: utf-8 -*-

# mvc/hints.py
#===============================================================================

REVALIDATE              = 10001
CHANGE_NAME             = 10002
MODIFY_DETACHMENT       = 10003
MODIFY_UNIT             = 10004 # additional arg: reference to unit
ADD_DETACHMENT          = 10005 # additional arg: reference to new detachment

#===============================================================================
# ArmyListHint
#===============================================================================
class ArmyListHint:
   def __init__(self, name, hintType):
      self._name = "Hint(%s)" % name
      self.id = hintType
      
   def __repr__(self):
      return self._name
   
   def IsType(self, classname):
      return self.id == classname.id
   
   def TypeIn(self, classnames):
      for classname in classnames:
         if self.id == classname.id: return True
      return False


class RevalidateHint(ArmyListHint):
   id = REVALIDATE
   def __init__(self):
      ArmyListHint.__init__(self, "Revalidate army list", RevalidateHint.id)
      
class ChangeNameHint(ArmyListHint):
   id = CHANGE_NAME
   def __init__(self, which):
      ArmyListHint.__init__(self, "Change name", ChangeNameHint.id)
      self.which = which
      
class ModifyDetachmentHint(ArmyListHint):
   id = MODIFY_DETACHMENT
   def __init__(self, which):
      ArmyListHint.__init__(self, "Modify detachment", ModifyDetachmentHint.id)
      self.which = which
      
class ModifyUnitHint(ArmyListHint):
   id = MODIFY_UNIT
   def __init__(self, which):
      ArmyListHint.__init__(self, "Modify unit", ModifyUnitHint.id)
      self.which = which
      
class AddDetachmentHint(ArmyListHint):
   id = ADD_DETACHMENT
   def __init__(self, which):
      ArmyListHint.__init__(self, "Add detachment", AddDetachmentHint.id)
      self.which = which