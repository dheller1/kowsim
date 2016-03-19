# -*- coding: utf-8 -*-

# kow/effect.py
#===============================================================================
from modifiers import MOD_ADD, MOD_SET
import stats


#===============================================================================
# UnitEffect
#   Effect that a specific unit has, e.g. from an option or a magic item.
#   This may for instance change the profile value of the unit. For example, 
#   picking two-handed weapons might lower the Defense to 4+ for a unit (Set(De,4)),
#   but grant CS(2) in turn.
#   Subclasses for the specific effects shall be implemented, such as
#   GrantSpecialRuleEffect or ModifyStatEffect
#===============================================================================
class UnitEffect(object):
   def __init__(self):
      pass
   
   @staticmethod
   def ParseFromString(s):
      s = s.strip()
      if s.startswith("Set"):
         # syntax: Set( stat, value )
         if not ("(" in s and ")" in s and "," in s):
            print "Invalid effect %s! Skipping." % (s)
            return None
         
         argsStart = s.index("(")+1
         argsEnd = s.rindex(")")
         argsStr = s[argsStart:argsEnd]
         
         args = argsStr.split(',') 
         if not len(args)==2:
            print "Invalid effect %s! Skipping." % (s)
            return None
         
         setWhat, setTo = args[0], int(args[1])
         if not setWhat in ("Speed","Melee","Ranged","Defense","Attacks","Nerve","NerveWaver","NerveBreak"):
            print "Invalid argument %s for Set modifier effect! Skipping." % setWhat
            return None
         
         effect = ModifyStatEffect(stat=setWhat, modifier=setTo, modifierType=MOD_SET)
         return effect
      
      elif s.startswith("Add"):
         # syntax: Add( stat, value )
         if not ("(" in s and ")" in s and "," in s):
            print "Invalid effect %s! Skipping." % (s)
            return None
         
         argsStart = s.index("(")+1
         argsEnd = s.rindex(")")
         argsStr = s[argsStart:argsEnd]
         
         args = argsStr.split(',') 
         if not len(args)==2:
            print "Invalid effect %s! Skipping." % (s)
            return None
         
         addToWhat, summand = args[0], int(args[1])
         if not addToWhat in ("Speed","Melee","Ranged","Defense","Attacks","NerveWaver","NerveBreak"):
            print "Invalid argument %s for Add modifier effect! Skipping." % addToWhat
            return None
         
         effect = ModifyStatEffect(stat=addToWhat, modifier=summand, modifierType=MOD_ADD)
         return effect
      
      elif s.startswith("Grant"):
         # syntax: Grant(name_of_special_rule)
         if not ("(" in s and ")" in s):
            print "Invalid effect %s! Skipping." % (s)
            return None
         
         argsStart = s.index("(")+1
         argsEnd = s.rindex(")")
         argsStr = s[argsStart:argsEnd].strip()
         
         effect = GrantSpecialRuleEffect(argsStr) # TODO: Implement proper special rule objects instead of just strings
         return effect
      
      else:
         print "Invalid effect %s! Skipping." % s
         return None


#===============================================================================
# UnitEffect which grants a special rule when active.
#===============================================================================
class GrantSpecialRuleEffect(UnitEffect):
   def __init__(self, specialRule=None):
      super(GrantSpecialRuleEffect, self).__init__()
      
      self._specialRule = specialRule
      
   def SpecialRule(self): return self._specialRule


#===============================================================================
# UnitOptionEffect which modifies a stat (such as Melee, Defense) either by
# setting it or by adding to it.
#===============================================================================
class ModifyStatEffect(UnitEffect):
   def __init__(self, stat, modifier=0, modifierType=MOD_SET):
      super(ModifyStatEffect, self).__init__()
      
      if type(stat) in (str, unicode):
         self._stat = stats.FindStat(stat)
      else: self._stat = stat
      
      self._modifier = modifier
      self._modifierType = modifierType
   
   def Modifier(self): return self._modifier
   def ModType(self): return self._modifierType
   def Stat(self): return self._stat
