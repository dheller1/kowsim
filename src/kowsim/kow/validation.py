# -*- coding: utf-8 -*-

# kow/validation.py
#===============================================================================
from kowsim.kow.alignment import AL_GOOD, AL_EVIL
import kowsim.kow.unittype as ut
import kowsim.kow.sizetype as st
from _collections import defaultdict


""" When you add a new validation rule, don't forget to add an instance of it to ALL_VALIDATIONRULES way down in this file! """

#===============================================================================
# ValidationMessage
#===============================================================================
class ValidationMessage(object):
   VM_CRITICAL= 0x1
   VM_WARNING = 0x2
   VM_INFO    = 0x4
    
   def __init__(self, msgtype, shortdesc, longdesc):
      self._shortDesc = shortdesc
      self._longDesc = longdesc
      self._msgType = msgtype


#===============================================================================
# ArmyListValidator
#===============================================================================
class ArmyListValidator(object):
   def __init__(self, armylist, rules):
      self._armyList = armylist
      self._rules = rules
      
   def Check(self):
      msgs = []
      for rule in self._rules:
         msgs.extend( rule.Check(self._armyList) )
      return msgs


#===============================================================================
# ValidationRule (abstract)
#===============================================================================
class ValidationRule(object):
   def __init__(self, name):
      self._name = name
      
   def Check(self, obj):
      raise NotImplementedError()
      

#===============================================================================
# PointsLimitFulfilledRule
#===============================================================================
class PointsLimitFulfilledRule(ValidationRule):
   def __init__(self):
      ValidationRule.__init__(self, "PointsLimitFulfilled")
   
   def Check(self, obj):
      msgs = []
      limit = obj.PointsLimit()
      total = obj.PointsTotal()
      if total > limit: msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "Points limit exceeded (%d/%d pts)" % (total, limit),
            "The army list has a limit of %d points, but you fielded troops for a total of %d points (%d too many)." % (limit, total, total-limit)))
      elif total < limit: msgs.append(ValidationMessage(ValidationMessage.VM_INFO, "%d leftover points." % (limit-total),
            "You have fielded troops for %d points, but the army list allows %d points. You can field another %d points worth of troops." % (total, limit, limit-total)))
      return msgs
      

#===============================================================================
# NumberOfPrimaryDetachmentsOkRule
#===============================================================================
class NumberOfPrimaryDetachmentsOkRule(ValidationRule):
   def __init__(self):
      ValidationRule.__init__(self, "NumberOfPrimaryDetachmentsOk")
   
   def Check(self, obj):
      msgs = []
      numPrimary = 0
      for det in obj.ListDetachments():
         if det.IsPrimary(): numPrimary+=1
      if numPrimary == 0: msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "No primary detachment",
            "Each army list must have exactly one primary detachment. Click the checkbox in one of your detachments to make it primary."))
      elif numPrimary > 1: msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "Multiple (%d) primary detachments" % numPrimary,
            "Each army list must have exactly one primary detachment. Click the checkbox in %d of your detachments to unmark it as primary." % (numPrimary-1)))
      return msgs
   
   
class NumberOfNonRegimentsOkRule(ValidationRule):
   """ Checks if the allowed number of Monsters, War engines and Heroes is not exceeded. """ 
   def __init__(self):
      ValidationRule.__init__(self, "NumberOfNonRegimentsOk")
   
   def Check(self, obj):
      msgs = []
      for det in obj.ListDetachments():
         nHeroes = 0
         nWarengs = 0
         nMonsters = 0
         
         nTroops = 0
         nRegiments = 0
         nHordes = 0

         for unit in det.ListUnits(): # count unit type occasions
            if unit.UnitType() == ut.UT_HERO:
               nHeroes += 1
            elif unit.UnitType() == ut.UT_WENG:
               nWarengs += 1
            elif unit.UnitType() == ut.UT_MON:
               nMonsters += 1
            elif unit.UnitType() in (ut.UT_INF, ut.UT_LINF, ut.UT_CAV, ut.UT_LCAV):
               if unit.SizeType() == st.ST_REG and not unit.irregular:
                  nRegiments += 1
               elif unit.SizeType() in (st.ST_HRD, st.ST_LEG) and not unit.irregular:
                  nHordes += 1
               elif unit.SizeType() == st.ST_TRP:
                  nTroops += 1
                  
         # hordes allow one of each
         excessiveHeroSlotsUsed = max(nHeroes - nHordes, 0)
         excessiveWengSlotsUsed = max(nWarengs - nHordes, 0)
         excessiveMonsterSlotsUsed = max(nMonsters - nHordes, 0)
         
         # regiments allow any one (1) slot each
         if excessiveHeroSlotsUsed+excessiveMonsterSlotsUsed+excessiveWengSlotsUsed > nRegiments:
            msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "%s: More Heroes/War engines/Monsters than allowed." % det.CustomName(),
                  "For each non-irregular horde/legion in a detachment there may be 1 Hero, 1 War engine, AND 1 Monster; plus 1 Hero, War engine, OR Monster for each regiment.\n" +
                  "You may include %d Heroes, War engines, and Monsters plus another %d of any kind." % (nHordes, nRegiments)))
         
         # regiments allow 2 troops each, while hordes/legions allow 4
         if nTroops > 2*nRegiments + 4*nHordes:
            msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "%s: Too many troops fielded, need more regiments or hordes." % det.CustomName(),
                  "The number of troops (%d) in the detachment must not exceed %d.\n(Two per regiment plus four per horde or legion)." % (nTroops, 2*nRegiments + 4*nHordes)))          
      
      return msgs
               

#===============================================================================
# AlliedAlignmentsOkRule
#===============================================================================
class AlliedAlignmentsOkRule(ValidationRule):
   def __init__(self):
      ValidationRule.__init__(self, "AlliedAlignmentsOk")
   
   def Check(self, obj):
      msgs = []
      failed = False
      for det in obj.ListDetachments():
         if failed: break
         if not det.IsPrimary(): continue # only check for primary detachments
         for alliedDet in obj.ListDetachments():
            if det is alliedDet: continue
            if (det.Choices().Alignment()==AL_GOOD and alliedDet.Choices().Alignment()==AL_EVIL) or \
                        (det.Choices().Alignment()==AL_EVIL and alliedDet.Choices().Alignment()==AL_GOOD):
               msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "Good and Evil forces can't be allies.",
                  "Your army list contains both good and evil forces, allied with each other - this is not allowed."))
               failed = True
               break
      return msgs
   

class MagicArtefactsAreUniqueRule(ValidationRule):
   """ Check if each magic artefact is used only once in the army. """
   def __init__(self):
      ValidationRule.__init__(self, "MagicArtefactsAreUnique")
   
   def Check(self, obj):
      msgs = []
      itemmap = defaultdict(int) # {str:int} map with ItemName=>number of occurrences entries
      for det in obj.ListDetachments():
         for unit in det.ListUnits():
            if unit.Item() is not None:
               itemmap[unit.Item().Name()] += 1
      
      for itemName, occs in itemmap.iteritems():
         if occs > 1:
            msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "Item '%s' used more than once. (%d times)" % (itemName, occs),
                                          "Each magic artefact may only be used once in an army list, but %s is present %d times." % (itemName, occs)))
      return msgs
   
   
class UniqueUnitsAreUniqueRule(ValidationRule):
   """ Check if units flagged as unique actually are unique in the army, regardless of their detachment.
   (E.g. The Green Lady might occur in both Elves and Forces of Nature detachments.) """
   def __init__(self):
      ValidationRule.__init__(self, "UniqueUnitsAreUnique")
      
   def Check(self, obj):
      msgs = []
      uniqmap = defaultdict(int) # {str:int} map with UnitName=>number of occurrences entries
      for det in obj.ListDetachments():
         for unit in det.ListUnits():
            if unit.unique:
               uniqmap[unit.Name()] += 1
               
      for unitName, occs in uniqmap.iteritems():
         if occs > 1:
            msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "Unique unit '%s' included more than once." % (unitName),
                                          "A unique unit may only occur once in the whole army list, but %s is present %d times." % (unitName, occs)))
      return msgs
   
   
class CokSpecialUnitsMaxThreeTimesRule(ValidationRule):
   """ Check if units flagged as unique actually are unique in the army, regardless of their detachment.
   (E.g. The Green Lady might occur in both Elves and Forces of Nature detachments.) """
   def __init__(self):
      ValidationRule.__init__(self, "COK_SpecialUnitsMaxThreeTimes")
      
   def Check(self, obj):
      msgs = []
      for det in obj.ListDetachments():
         maxn = 3 if det.IsPrimary() else 1
         unitMap = defaultdict(int)
         for unit in det.ListUnits():
            if unit.UnitType() in (ut.UT_HERO, ut.UT_WENG, ut.UT_MON):
               unitMap[unit.Name()] += 1
         for unitName, occs in unitMap.iteritems():
            if occs > maxn:
               msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "Unit %s chosen too often: Only %d allowed, but you fielded %d." % (unitName, maxn, occs),
                                            "In a primary detachment, each Hero, War Engine, or Monster may only appear up to three times. In an allied detachment, only one occurrence is allowed."))
      
      return msgs


class CokNoMagicItemsForAlliesRule(ValidationRule):
   """ Check if units flagged as unique actually are unique in the army, regardless of their detachment.
   (E.g. The Green Lady might occur in both Elves and Forces of Nature detachments.) """
   def __init__(self):
      ValidationRule.__init__(self, "COK_NoMagicItemsForAllies")
      
   def Check(self, obj):
      msgs = []
      for det in obj.ListDetachments():
         if not det.IsPrimary():
            for unit in det.ListUnits():
               if unit.Item() is not None:
                  msgs.append(ValidationMessage(ValidationMessage.VM_CRITICAL, "Allies may not be given magic artifacts (detachment %s)" % (det.CustomName()),
                                            "The detachment '%s' has at least one magic artifact, but as an allied detachment it may not have any."))
                  break
      
      return msgs

ALL_VALIDATIONRULES = (PointsLimitFulfilledRule(), NumberOfPrimaryDetachmentsOkRule(), AlliedAlignmentsOkRule(),
                       NumberOfNonRegimentsOkRule(), MagicArtefactsAreUniqueRule(), UniqueUnitsAreUniqueRule())

COK_ADDITIONALRULES = (CokSpecialUnitsMaxThreeTimesRule(), CokNoMagicItemsForAlliesRule())