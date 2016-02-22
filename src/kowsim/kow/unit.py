# -*- coding: utf-8 -*-

# kow/unit.py
#===============================================================================
import unittype as ut
import sizetype as st

from ..util.core import Size

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
      
   def __repr__(self):
      return "KowUnitProfile(%s)" % self._name

   # Getters
   def At(self): return self._attacks
   def AtStr(self): return "%d" % self._attacks if self._attacks>0 else "-"
   def De(self): return self._defense
   def DeStr(self): return "%d+" % self._defense
   def Item(self): return self._item
   def ItemCost(self):
      if self._item: return self._item.PointsCost()
      else: return 0
   def Me(self): return self._melee
   def MeStr(self): return "%d+" % self._melee if self._melee>0 else "-"
   def Ne(self): return (self._nerveWaver, self._nerveBreak)
   def NeStr(self): return "%s/%d" % (str(self._nerveWaver) if self._nerveWaver != 0 else "-", self._nerveBreak)
   def Name(self): return self._name
   def PointsCost(self): return self._pointsCost + self._item.PointsCost() if self._item else self._pointsCost
   def Ra(self): return self._ranged
   def RaStr(self): return "%d+" % self._ranged if self._ranged>0 else "-"
   def SizeType(self): return self._sizeType
   def Sp(self): return self._speed
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
                            self._unitType, self._sizeType, self._baseSize, self._specialRules, self._item)
   
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
      name = unicode(cols[1])
      
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
      
      options = cols[10] # Options
      points = int(cols[11]) # Points
      baseW, baseH = cols[12].split('x') # Base Size
      base = Size(int(baseW), int(baseH))
      
      p = KowUnitProfile(name, sp, me, ra, de, at, nv[0], nv[1], points, utype, stype, base, specRules)
      return p