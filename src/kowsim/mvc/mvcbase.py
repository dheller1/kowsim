# -*- coding: utf-8 -*-

# mvc/mvcbase.py
#===============================================================================

#===============================================================================
# MVCError
#===============================================================================
class MVCError(Exception):
   def __init__(self, e):
      Exception.__init__(self, e)


#===============================================================================
# Controller
#===============================================================================
class Controller(object):
   """Abstract base class for a Control in a MVC (Model-View-Controller) architecture
   
   A Control object mainly manages communication between models and views, updating
   others if one changes.
   For each model, you should have one (1) controller and you can have an arbitrary
   number of views.
   
   In order to change data in the model, a view can initiate a modification via the
   controller. The model should call NotifyModelChanged in the controller, initiating
   an update in all views. You can additionally add hints to possibly only do a
   partial update.
   A concrete Controller class should define possible HINTS in an enum-style for
   model and views to use.
   
   Updates can be temporarily paused and later reactivated (e.g. if many changes
   are expected in a short amount of time, normally leading to expensive updates).
   However, a full update (i.e. no hints) is carried out after unpausing.
   
   A controller also stores the command history for its model, allowing e.g. to
   undo and redo commands.
   """
   def __init__(self, model):
      """Controller constructor
         parameters:
            -model         the model managed by this controller
      """
      self._model = model
      self._model.SetCtrl(self)
      self._views = set()
      self._updatesPaused = False
      self._cmdHist = []
      self._undoHist = []
      
   # execute a command and, if it's reversible, add it to the command history
   def ExecuteCmd(self, cmd):
      cmd.Execute()
      self._cmdHist.append(cmd)
      print "CmdHistory:", self._cmdHist
      if cmd.IsReversible():
         self._undoHist.append(cmd)
   
   # inform views about changes in the model
   def NotifyModelChanged(self, *hints):
      if self._updatesPaused: return
      for view in self._views:
         view.UpdateContent(*hints)
         
   def PauseUpdates(self, pause=True):
      if pause: self._updatesPaused = True
      else: self.UnpauseUpdates()
      
   def UnpauseUpdates(self):
      self._updatesPaused = False
      self.NotifyModelChanged()
   
   # accessors
   def AttachView(self, view): self._views.add(view)
   def DetachView(self, view): self._views.remove(view)
   def Model(self): return self._model
   def Views(self): return self._views
   
   
#============================================================================
# Model
#============================================================================
class Model(object):
   """Abstract base class for a Model in a MVC (Model-View-Controller) architecture
   A model mainly comprises the data which is visualized in the views and coordinated
   via the controller.
   The model should not communicate with its views directly but instead only
   with its controller. It is possible to create model objects without controllers,
   but then no views can be attached to them.
   """   
   def __init__(self, data):
      """Model constructor"""
      self._ctrl = None
      self._data = data
   
   # notify Controller about changes in the model
   def _NotifyChanges(self, *hints):
      if self._ctrl is not None:
         self._ctrl.NotifyModelChanged(*hints)
   
   # accessors
   def Ctrl(self): return self._ctrl
   def SetCtrl(self, ctrl): self._ctrl = ctrl
   def Data(self): return self._data
   def SetData(self, data):
      self._data = data
      self._NotifyChanges() 
   
   
#============================================================================
# View
#============================================================================
class View(object):
   """Abstract base class for a View in a MVC (Model-View-Controller) architecture
   
   A view visualizes the data stored in a model and communicates changes (actively
   and passively) via the controller.
   Any number of different views can be attached to a model.
   Views must react to changes in the model by implementing the UpdateContent
   function, possibly reacting to HINTS defined in the controller and only doing
   a partial update.
   """
   def __init__(self, ctrl):
      """View constructor
         parameters:
            -ctrl         the controller of the model to which to attach to
      """
      self.ctrl = ctrl
      self.ctrl.AttachView(self)
      
   def __del__(self):
      self.ctrl.DetachView(self)
      self.ctrl = None
   
   def UpdateContent(self, *hints):
      raise NotImplementedError