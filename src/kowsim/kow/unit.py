# -*- coding: utf-8 -*-

# kow/unit.py
#===============================================================================
import unittype as ut
import sizetype as st

from ..util.core import Size
from modifiers import MOD_ADD, MOD_SET
import stats


#===============================================================================
# KowUnitOptionEffect
#   Effect that a specific unit option has. This may for instance change the profile
#   value of the unit. For example, picking two-handed weapons might lower the Defense
#   to 4+ for a unit (Set(De,4)), but grant CS(2) in turn.
#   Subclasses for the specific effects shall be implemented, such as
#   KowUnitOptionGrantSpecialRuleEffect, or
#   KowUnitOptionModifyStatEffect
#===============================================================================
class KowUnitOptionEffect(object):
   def __init__(self):
      self._isApplied = False
   
   @staticmethod
   def ParseFromString(s):
      s = s.strip()
      if s.startswith("Set"):
         # syntax: Set( stat, value )
         if not ("(" in s and ")" in s and "," in s):
            print "Invalid effect %s! Skipping." % (s)
            return None
         
         argsStart = s.index("(")+1
         argsEnd = s.index(")")
         argsStr = s[argsStart:argsEnd]
         
         args = argsStr.split(',') 
         if not len(args)==2:
            print "Invalid effect %s! Skipping." % (s)
            return None
         
         setWhat, setTo = args[0], int(args[1])
         if not setWhat in ("Speed","Melee","Ranged","Defense","Attacks","Nerve","NerveWaver","NerveBreak"):
            print "Invalid argument %s for Set modifier effect! Skipping." % setWhat
            return None
         
         effect = KowModifyStatEffect(stat=setWhat, modifier=setTo, modifierType=MOD_SET)
         return effect
      
      elif s.startswith("Add"):
         # syntax: Add( stat, value )
         if not ("(" in s and ")" in s and "," in s):
            print "Invalid effect %s! Skipping." % (s)
            return None
         
         argsStart = s.index("(")+1
         argsEnd = s.index(")")
         argsStr = s[argsStart:argsEnd]
         
         args = argsStr.split(',') 
         if not len(args)==2:
            print "Invalid effect %s! Skipping." % (s)
            return None
         
         addToWhat, summand = args[0], int(args[1])
         if not addToWhat in ("Speed","Melee","Ranged","Defense","Attacks","NerveWaver","NerveBreak"):
            print "Invalid argument %s for Add modifier effect! Skipping." % addToWhat
            return None
         
         effect = KowModifyStatEffect(stat=addToWhat, modifier=summand, modifierType=MOD_ADD)
         return effect
      
      else:
         print "Invalid effect %s! Skipping." % s
         return None
         
#===============================================================================
# UnitOptionEffect which grants a special rule when active.
#===============================================================================
class KowGrantSpecialRuleEffect(KowUnitOptionEffect):
   def __init__(self, specialRule=None):
      super(KowGrantSpecialRuleEffect, self).__init__()
      
      self._specialRule = specialRule
      
#===============================================================================
# UnitOptionEffect which modifies a stat (such as Melee, Defense) either by
# setting it or by adding to it.
#===============================================================================
class KowModifyStatEffect(KowUnitOptionEffect):
   def __init__(self, stat, modifier=0, modifierType=MOD_SET):
      super(KowModifyStatEffect, self).__init__()
      
      if type(stat) in (str, unicode):
         self._stat = stats.FindStat(stat)
      else: self._stat = stat
      
      self._modifier = modifier
      self._modifierType = modifierType
   
   def Modifier(self): return self._modifier
   def ModType(self): return self._modifierType
   def Stat(self): return self._stat
      

#===============================================================================
# KowUnitOption
#   Option for a specific unit, e.g. to take two-handed weapons instead of
#   weapon and shield. May be associated with a points cost as well as a list
#   of effects (e.g. increasing one profile value but lowering another one in turn).
#===============================================================================
class KowUnitOption(object):
   def __init__(self, name, pointsCost=0, effects=[], isActive=False):
      self._name = name
      self._pointsCost = pointsCost
      self._effects = effects
      
   def Name(self): return self._name
   def PointsCost(self): return self._pointsCost
      
   def __repr__(self):
      if len(self._effects) == 0:
         return "%s (%dp)" % (self._name, self._pointsCost)
      elif len(self._effects) == 1:
         return "%s (%dp), 1 effect" % (self._name, self._pointsCost)
      elif len(self._effects) > 1:
         return "%s (%dp), %d effects" % (self._name, self._pointsCost, len(self._effects))

#===============================================================================
# KowUnitProfile
#   Unit profile as given in an army list entry, e.g. Sea Guarde Horde, along
#   with its statistics.
#===============================================================================
class KowUnitProfile(object):
   def __init__(self, *args):
      self._name = args[0] if len(args)>0 else "Unknown unit"
      self._speed = args[1] if len(args)>1 else 5
      self._melee = args[2] if len(args)>2 else 4
      self._ranged = args[3] if len(args)>3 else 0
      self._defense = args[4] if len(args)>4 else 4
      self._attacks = args[5] if len(args)>5 else 10
      self._nerveWaver = args[6] if len(args)>6 else 12
      self._nerveBreak = args[7] if len(args)>7 else 14
      self._pointsCost = args[8] if len(args)>8 else 100
      self._unitType = args[9] if len(args)>9 else ut.UT_INF
      self._sizeType = args[10] if len(args)>10 else st.ST_REG
      self._baseSize = args[11] if len(args)>11 else Size(20, 20) # base size in mm
      self._specialRules = args[12] if len(args)>12 else []
      self._item = args[13] if len(args)>13 else None
      self._options = args[14] if len(args)>14 else []
      
      self._activeOptions = []
      
   def __repr__(self):
      return "KowUnitProfile(%s)" % self._name

   # Getters
   def At(self): return self._StatWithModifiers(stats.ST_ATTACKS)
   def AtStr(self): return "%d" % self.At() if self.At()>0 else "-"
   def De(self): return self._StatWithModifiers(stats.ST_DEFENSE)
   def DeStr(self): return "%d+" % self.De()
   def Item(self): return self._item
   def ItemCost(self):
      if self._item: return self._item.PointsCost()
      else: return 0
   def ItemName(self):
      if self._item: return self._item.Name()
      else: return ""
   def Me(self): return self._StatWithModifiers(stats.ST_MELEE)
   def MeStr(self): return "%d+" % self.Me() if self.Me()>0 else "-"
   def Ne(self): return (self._nerveWaver, self._nerveBreak)
   def NeStr(self): return "%s/%d" % (str(self._nerveWaver) if self._nerveWaver != 0 else "-", self._nerveBreak)
   def Name(self): return self._name
   def ListActiveOptions(self): return self._activeOptions
   def ListOptions(self): return self._options
   def PointsCost(self):
      pc = self._pointsCost
      if self._item:
         pc += self.Item().PointsCost()
      for o in self._activeOptions:
         pc += o.PointsCost()
      return pc
   
   def Ra(self): self._StatWithModifiers(stats.ST_RANGED)
   def RaStr(self): return "%d+" % self.Ra() if self.Ra()>0 else "-"
   def SizeType(self): return self._sizeType
   def Sp(self): return self._StatWithModifiers(stats.ST_SPEED)
   def SpecialRules(self): return self._specialRules
   def UnitType(self): return self._unitType
   
   # Setters
   def SetItem(self, item): self._item = item
   def SetName(self, name): self._name = name
   
   # property decorators
   name = property(Name, SetName)
   
   # generate a fresh copy of this unit
   def Clone(self):
      return KowUnitProfile(self._name, self._speed, self._melee, self._ranged, self._defense, self._attacks, self._nerveWaver, self._nerveBreak, self._pointsCost,
                            self._unitType, self._sizeType, self._baseSize, self._specialRules, self._item, self._options)
      
   def _StatWithModifiers(self, stat):
      """ Return the unit's current effective stat (KowStat instance) with all its modifiers from options or magic items. """
      setModifiers = []
      addModifiers = []
      
      if stat == stats.ST_SPEED:
         val = self._speed
         for o in self._activeOptions:
            for e in o._effects:
               if type(e) == KowModifyStatEffect and e.Stat()==stats.ST_SPEED:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)
      
      elif stat == stats.ST_MELEE:
         val = self._melee
         for o in self._activeOptions:
            for e in o._effects:
               if type(e) == KowModifyStatEffect and e.Stat()==stats.ST_MELEE:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)
               
      elif stat == stats.ST_RANGED:
         val = self._ranged
         for o in self._activeOptions:
            for e in o._effects:
               if type(e) == KowModifyStatEffect and e.Stat()==stats.ST_RANGED:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)
               
      elif stat == stats.ST_DEFENSE:
         val = self._defense
         for o in self._activeOptions:
            for e in o._effects:
               if type(e) == KowModifyStatEffect and e.Stat()==stats.ST_DEFENSE:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)
               
      elif stat == stats.ST_ATTACKS:
         val = self._attacks
         for o in self._activeOptions:
            for e in o._effects:
               if type(e) == KowModifyStatEffect and e.Stat()==stats.ST_ATTACKS:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)
               
      elif stat == stats.ST_NERVE:
         raise ValueError("Nerve modifiers not yet supported!")
         return 0
      
      if len(setModifiers)>1:
         print "Warning: Multiple 'Set' modifiers for %s!" % stat.Name()
         
      if len(setModifiers)>0:
         val = setModifiers[-1].Modifier()
      
      for a in addModifiers: val += a.Modifier()
      return val
   
   # derived properties
   def Footprint(self):
      """ Return the footprint (Size) of a unit, given by its individual base size, model count
        and size type. """
      
      # determine formation
      u = self._unitType
      s = self._sizeType
      if u == ut.UT_INF:
         if s == st.ST_TRP: formation = (5, 2)
         elif s == st.ST_REG: formation = (5, 4)
         elif s == st.ST_HRD: formation = (10, 4)
         elif s == st.ST_LEG: formation = (10, 6)
         else: formation = (1, 1)        
      elif u == ut.UT_CAV:
         if s == st.ST_TRP: formation = (5, 1)
         elif s == st.ST_REG: formation = (5, 2)
         elif s == st.ST_HRD: formation = (10, 2)
         else: formation = (1, 1)        
      elif u == ut.UT_LINF:
         if s == st.ST_REG: formation = (3, 1)
         elif s == st.ST_HRD: formation = (3, 2)
         elif s == st.ST_HRD: formation = (6, 2)
         else: formation = (1, 1)        
      elif u == ut.UT_CAV:
         if s == st.ST_TRP: formation = (5, 1)
         elif s == st.ST_REG: formation = (5, 2)
         elif s == st.ST_HRD: formation = (10, 2)
         else: formation = (1, 1)        
      elif u == ut.UT_LCAV:
         if s == st.ST_TRP: formation = (5, 1)
         elif s == st.ST_REG: formation = (5, 2)
         elif s == st.ST_HRD: formation = (10, 2)
         else: formation = (1, 1)
      elif u in (ut.UT_WENG, ut.UT_MON, ut.UT_HERO):
         formation = (1, 1)
         
      # footprint is the single base size times the formation models
      return Size(self._baseSize.W() * formation[0], self._baseSize.H() * formation[1])
   
   # static generators
   @staticmethod
   def FromCsv(cols):
      """ Generate from a CSV row (individual columns given as list). """
      if len(cols)<13: 
         raise ValueError("Insufficient number of values (%d)." % len(cols))
         return None
      
      #type
      utype = ut.Find(cols[0])
      if not utype: raise ValueError("Unknown unit type: %s" % cols[0])
      
      #unit name
      name = unicode(cols[1]).strip()
      if name != name.strip():
         print "Warning: Unit name %s has leading or trailing blanks!" % name
      
      #size
      stype = st.Find(cols[2])
      if not stype: raise ValueError("Unknown size type: %s" % cols[2])
      
      sp = float(cols[3]) if cols[3] != "-" else 0 # Speed
      me = int(cols[4]) if cols[4] != "-" else 0 # Melee
      ra = int(cols[5]) if cols[5] != "-" else 0 # Ranged
      de = int(cols[6]) if cols[6] != "-" else 0 # Defense
      at = int(cols[7]) if cols[7] != "-" else 0 # Attacks
      
      nv = cols[8].split('/') # Nerve
      if nv[0]=="-": nv = (0, int(nv[1]))
      else: nv = int(nv[0]), int(nv[1])
      
      # special rules
      special = cols[9]
      specRules = [word.strip() for word in special.split(',')]
      
      # parse options
      options = cols[10] # Options
      opts = KowUnitProfile.ParseOptionsString(options)
      print "%d options for unit %s." % (len(opts), name)
      for o in opts: print (" %s" % o)
      
      points = int(cols[11]) # Points
      baseW, baseH = cols[12].split('x') # Base Size
      base = Size(int(baseW), int(baseH))
      
      p = KowUnitProfile(name, sp, me, ra, de, at, nv[0], nv[1], points, utype, stype, base, specRules, None, opts)
      return p
   
   @staticmethod
   def ParseOptionsString(s):
      """ Parse options string as read from CSV and generate unit options from it. """
      if len(s)==0: return []
      
      # option syntax: Name
      #         or:     Name|+35
      #         or:     Name|+35|Effect1|Effect2|...
      #
      # multiple options must be separated with semicolons
      # e.g. " Lightning Bolt(5)|+45;Fireball (10)|+10;Wind Blast (5)|+30;Bane Chant(2)|+15;Sabre-toothed Pussycat|+10;Mount|+15|Set(Speed,9) "
      options = s.split(';')
      optList = []
      for o in options:
         params = o.split('|')
         optName = params[0]
         if len(params)>1:
            try: optPointsCost = int(params[1])
            except ValueError:
               print "Warning: Invalid points cost '%s' for option %s! Skipping option!" % (params[1], optName)
               continue
         else: optPointsCost = 0
         if len(params)>2: effectStrs = params[2:]
         else: effectStrs = []
         
         effects = []
         for e in effectStrs:
            effect = KowUnitOptionEffect.ParseFromString(e)
            if effect is not None: effects.append(effect)
         
         optObject = KowUnitOption(optName, optPointsCost, effects)
         optList.append(optObject)
      return optList