# -*- coding: utf-8 -*-

# armybuilder/control.py
#===============================================================================
from kowsim.kow.unit import UnitInstance
import kowsim.mvc.mvcbase as MVC
import kowsim.armybuilder.views
import mvc.hints as ALH

#===============================================================================
# ArmyListCtrl
#===============================================================================
class ArmyListCtrl(MVC.Controller):
   def __init__(self, model):
      MVC.Controller.__init__(self, model)
      self.model = model
      self.attachedPreview = None
      
   def AttachView(self, view):
      MVC.Controller.AttachView(self, view) # call base class routine to use _addViewBuffer
      if isinstance(view, kowsim.armybuilder.views.ArmyListOutputView) and self.attachedPreview is None:
            self.attachedPreview = view
   
   def DetachView(self, view):
      self._views.remove(view)
      if self.attachedPreview is view:
         self.attachedPreview = None
         
   def ProcessHints(self, hints):
      # Currently, all hints are forwarded. As soon as commands which do not modify a model
      # are introduced (e.g. printing), these should be filtered and ignored here.
      self.NotifyModelChanged(hints)
      
   def Revalidate(self):
      self.NotifyModelChanged((ALH.RevalidateHint(), ))
         
   def SetPrimaryDetachment(self, detachment, makePrimary):
      try: self._model.ListDetachments().index(detachment)
      except ValueError:
         raise ValueError("Can't modify a detachment not belonging to my armylist!")
      
      detachment._isPrimary = makePrimary
      self.Revalidate()