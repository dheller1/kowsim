# -*- coding: utf-8 -*-

# kow/unit.py
#===============================================================================
import unittype as ut
import sizetype as st

from ..util.core import Size
from modifiers import MOD_ADD, MOD_SET
from effect import UnitEffect, ModifyStatEffect
import stats
from kowsim.kow.effect import GrantSpecialRuleEffect, RemoveSpecialRuleEffect

#===============================================================================
# KowUnitOption
#   Option for a specific unit, e.g. to take two-handed weapons instead of
#   weapon and shield. May be associated with a points cost as well as a list
#   of effects (e.g. increasing one profile value but lowering another one in turn).
#===============================================================================
class KowUnitOption(object):
   def __init__(self, name, pointsCost=0, effects=None, isActive=False):
      self._name = name
      self._pointsCost = pointsCost
      self._effects = effects if effects is not None else []
      
   def Name(self): return self._name
   def PointsCost(self): return self._pointsCost
      
   def __repr__(self):
      if len(self._effects) == 0:
         return "%s (%dp)" % (self._name, self._pointsCost)
      elif len(self._effects) == 1:
         return "%s (%dp), 1 effect" % (self._name, self._pointsCost)
      elif len(self._effects) > 1:
         return "%s (%dp), %d effects" % (self._name, self._pointsCost, len(self._effects))
      
   def DisplayStr(self):
      s = self._name
      if self._pointsCost > 0:
         s += " (%dp)" % self._pointsCost
      return s

#===============================================================================
# UnitProfile
#   Unit profile as given in an army list entry, e.g. Sea Guarde Horde, along
#   with its statistics.
#===============================================================================
class UnitProfile(object):
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
      self.irregular = args[15] if len(args)>15 else False
      self.unique = args[16] if len(args)>16 else False
            
   def __repr__(self):
      return "UnitProfile(%s)" % self._name

   # Getters
   def At(self): return self._attacks
   def AtStr(self): return "%d" % self.At() if self.At()>0 else "-"
   def CanHaveItem(self): return self._unitType not in (ut.UT_MON, ut.UT_WENG)
   def De(self): return self._defense
   def DeStr(self): return "%d+" % self.De()
   def DisplayName(self):
      s = self._name
      if (self.irregular): s+="*"
      if (self.unique): s+=" [1]"
      return s
   def Me(self): return self._melee
   def MeStr(self): return "%d+" % self.Me() if self.Me()>0 else "-"
   def Ne(self): return (self._nerveWaver, self._nerveBreak)
   def NeStr(self): return "%s/%d" % (str(self._nerveWaver) if self._nerveWaver != 0 else "-", self._nerveBreak)
   def Name(self): return self._name
   def ListOptions(self): return self._options
   def ListSpecialRules(self): return self._specialRules
   def PointsCost(self): return self._pointsCost
   def Ra(self): return self._ranged
   def RaStr(self): return "%d+" % self.Ra() if self.Ra()>0 else "-"
   def SizeType(self): return self._sizeType
   def Sp(self): return self._speed
   def UnitType(self): return self._unitType
   
   # Setters
   def SetName(self, name): self._name = name
   
   # property decorators
   name = property(Name, SetName)
   
   # generate a fresh instance of a unit using this profile
   def CreateInstance(self, detachment):
      return UnitInstance(self, detachment)
      
   # derived properties
   def Footprint(self):
      """ Return the footprint (Size) of a unit, given by its individual base size, model count
        and size type. """
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
   def NameFromDisplayName(dispname):
      n = dispname
      if(n.endswith(" [1]")):
         n = n[:-4]
      if(n.endswith("*")):
         n = n[:-1]
      return n
   
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
      opts = UnitProfile.ParseOptionsString(options)
      
      points = int(cols[11]) # Points
      baseW, baseH = cols[12].split('x') # Base Size
      base = Size(int(baseW), int(baseH))
      
      irregular = bool(cols[13])
      unique = bool(cols[14])
      
      p = UnitProfile(name, sp, me, ra, de, at, nv[0], nv[1], points, utype, stype, base, specRules, None, opts, irregular, unique)
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
            effect = UnitEffect.ParseFromString(e)
            if effect is not None: effects.append(effect)
         
         optObject = KowUnitOption(optName, optPointsCost, effects)
         optList.append(optObject)
      return optList
   

#===============================================================================
# UnitInstance
#   Instance of a specific unit someone has included into their army list.
#   In contrast to a UnitProfile, a UnitInstance may choose options, magic items,
#   etc. individually, while the corresponding UnitProfile object only catalogues
#   the available generic options.
#   Each UnitInstance object must have a reference to a UnitProfile object it
#   originates from (e.g. Shield Guard Horde).
#===============================================================================
class UnitInstance(object):
   def __init__(self, profile, detachment, customName=None, chosenOptions=None, chosenItem=None):
      self._profile = profile
      self._detachment = detachment
      self._customName = customName
      self._chosenOptions = chosenOptions if chosenOptions is not None else []
      self._chosenItem = chosenItem
      
   def __repr__(self):
      return "UnitInstance(%s)" % self.Name()
      
   # Getters
   def At(self): return self._StatWithModifiers(stats.ST_ATTACKS)
   def AtStr(self): return "%d" % self.At() if self.At()>0 else "-"
   def CanHaveItem(self): return self._profile.CanHaveItem()
   def ChooseOption(self, opt):
      if opt not in self._profile.ListOptions():
         raise ValueError("Unit %s cannot choose option %s." % (self.Name(), opt.Name()))
      elif opt in self._chosenOptions:
         raise ValueError("Unit %s already has option %s." % (self.Name(), opt.Name()))
      else: self._chosenOptions.append(opt)
         
   def ClearChosenOptions(self): self._chosenOptions = []
   def CustomName(self): return self._customName if self._customName is not None else ""
   def De(self): return self._StatWithModifiers(stats.ST_DEFENSE)
   def DeStr(self): return "%d+" % self.De()
   def Detachment(self): return self._detachment
   def DisplayName(self): return self._profile.DisplayName()
   def Item(self): return self._chosenItem
   @property
   def irregular(self):
      return self._profile.irregular
   def ListChosenOptions(self): return self._chosenOptions
   def ListSpecialRules(self):
      specRules = []
      specRules.extend(self._profile._specialRules)
      for o in self._chosenOptions:
         for e in o._effects:
            if type(e) == GrantSpecialRuleEffect:
               specRules.append(e.SpecialRule())
            elif type(e) == RemoveSpecialRuleEffect:
               if e.SpecialRule() in specRules:
                  specRules.remove(e.SpecialRule())
               else:
                  print "Warning: Unit %s has RemoveSpecialRuleEffect(%s), but it does not have that special rule!" % (self.Name(), e.SpecialRule())
      return specRules
   
   def Me(self): return self._StatWithModifiers(stats.ST_MELEE)
   def MeStr(self): return "%d+" % self.Me() if self.Me()>0 else "-"
   def Name(self): return self._profile.Name()
   def Ne(self): return (self._profile._nerveWaver, self._profile._nerveBreak)
   def NeStr(self): return "%s/%d" % (str(self._profile._nerveWaver) if self._profile._nerveWaver != 0 else "-", self._profile._nerveBreak)
   def Profile(self): return self._profile
   def Ra(self): self._StatWithModifiers(stats.ST_RANGED)
   def RaStr(self): return "%d+" % self.Ra() if self.Ra()>0 else "-"
   def SetProfile(self, profile):
      self._profile = profile
      self.Validate()
      
   def SizeType(self): return self._profile.SizeType()
   def Sp(self): return self._StatWithModifiers(stats.ST_SPEED)
   @property
   def unique(self):
      return self._profile.unique
   def UnitType(self): return self._profile.UnitType()
   
   # Setters
   def SetItem(self, item): self._chosenItem = item
   
   def HasPointsCostModifier(self):
      if self.Item() is not None and self.Item().PointsCost() > 0:
         return True
      for opt in self._chosenOptions:
         if opt.PointsCost() > 0:
            return True
      return False
   
   def HasStatModifier(self, stat):
      if stat == stats.ST_SPEED: return (self._profile._speed != self._StatWithModifiers(stats.ST_SPEED))
      elif stat == stats.ST_MELEE: return (self._profile._melee != self._StatWithModifiers(stats.ST_MELEE))
      elif stat == stats.ST_RANGED: return (self._profile._ranged != self._StatWithModifiers(stats.ST_RANGED))
      elif stat == stats.ST_DEFENSE: return (self._profile._defense != self._StatWithModifiers(stats.ST_DEFENSE))
      elif stat == stats.ST_ATTACKS: return (self._profile._attacks != self._StatWithModifiers(stats.ST_ATTACKS))
      else: raise ValueError("Unknown stat: %s" % stat)
   
   def ItemCost(self):
      if self._chosenItem: return self._chosenItem.PointsCost()
      else: return 0
      
   def ItemName(self):
      if self._chosenItem: return self._chosenItem.Name()
      else: return ""
      
   def PointsCost(self):
      pc = self._profile.PointsCost()
      if self.Item():
         pc += self.Item().PointsCost()
      for o in self._chosenOptions:
         pc += o.PointsCost()
      return pc
   
   def Validate(self):
      if self.Item() is not None and (not self._profile.CanHaveItem()):
         raise ValueError("Unit %s has an item but isn't allowed to have one." % self.Name())
      for opt in self._chosenOptions:
         if opt not in self._profile.ListOptions():
            raise ValueError("Unit %s has chosen option %s which should not be available." % (self.Name(), opt.Name()))
   
   def _StatWithModifiers(self, stat):
      """ Return the unit's current effective stat (KowStat instance) with all its modifiers from options or magic items. """
      setModifiers = []
      addModifiers = []
      
      if stat == stats.ST_SPEED:
         val = self._profile._speed
         for o in self._chosenOptions:
            for e in o._effects:
               if type(e) == ModifyStatEffect and e.Stat()==stats.ST_SPEED:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)   
      elif stat == stats.ST_MELEE:
         val = self._profile._melee
         for o in self._chosenOptions:
            for e in o._effects:
               if type(e) == ModifyStatEffect and e.Stat()==stats.ST_MELEE:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)
      elif stat == stats.ST_RANGED:
         val = self._profile._ranged
         for o in self._chosenOptions:
            for e in o._effects:
               if type(e) == ModifyStatEffect and e.Stat()==stats.ST_RANGED:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)
      elif stat == stats.ST_DEFENSE:
         val = self._profile._defense
         for o in self._chosenOptions:
            for e in o._effects:
               if type(e) == ModifyStatEffect and e.Stat()==stats.ST_DEFENSE:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)
      elif stat == stats.ST_ATTACKS:
         val = self._profile._attacks
         for o in self._chosenOptions:
            for e in o._effects:
               if type(e) == ModifyStatEffect and e.Stat()==stats.ST_ATTACKS:
                  if e.ModType()==MOD_ADD: addModifiers.append(e)
                  elif e.ModType()==MOD_SET: setModifiers.append(e)
      elif stat == stats.ST_NERVE:
         raise ValueError("Nerve modifiers not yet supported!")
         return 0
      else:
         raise ValueError("Unknown stat: %s" % stat)
      
      if len(setModifiers)>1:
         print "Warning: Multiple 'Set' modifiers for %s!" % stat.Name()
         
      if len(setModifiers)>0:
         val = setModifiers[-1].Modifier()
      
      for a in addModifiers: val += a.Modifier()
      return val
   