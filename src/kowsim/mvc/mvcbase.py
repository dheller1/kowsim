# -*- coding: utf-8 -*-

# mvc/mvcbase.py
#===============================================================================

from PySide.QtGui import QWidget, QTextEdit

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
      self.model = model
      self.model.SetCtrl(self)
      self._views = set()
      self._updatesPaused = False
      self._cmdHist = []
      self._undoHist = []
      self._isUpdating = False # can't add new views when the controller is currently updating old views,
      self._addViewBuffer = [] # thus they are buffered and registered when updating is finished.
      
   def AddAndExecute(self, cmd):
      """ Execute a command and, if it's reversible, add it to the undo history. """
      cmd.Execute()
      self._cmdHist.append(cmd)
      if cmd.IsReversible():
         self._undoHist.append(cmd)
      if cmd.hints:
         self.ProcessHints(cmd.hints)
      else:
         print "No hints for command %s. Skipping update." % cmd
   
   def NotifyModelChanged(self, hints):
      """ Inform any attached views about changes in the model. """
      if self._updatesPaused: return
      self._isUpdating = True
      for view in self._views:
         view.UpdateContent(hints)
      self._isUpdating = False
      while self._addViewBuffer:
         self.AttachView(self._addViewBuffer.pop())
         
   def PauseUpdates(self, pause=True):
      if pause: self._updatesPaused = True
      else: self.UnpauseUpdates()
      
   def ProcessHints(self, hints):
      pass
      
   def UnpauseUpdates(self):
      self._updatesPaused = False
      self.NotifyModelChanged()
   
   def AttachView(self, view):
      """ Attach a view to the model controlled by this controller.
      
      Should this routine be called while the controller is currently busy
      updating its attached views, attaching the new view is postponed until
      after the previous views' updates are finished.
      """
      if not self._isUpdating:
         self._views.add(view)
      else:
         self._addViewBuffer.append(view)
      
   def DetachView(self, view): self._views.remove(view)
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
      self.modified = False # True if model was modified since last save
   
   # notify Controller about changes in the model
   def _NotifyChanges(self, hints=None):
      if self._ctrl is not None:
         self._ctrl.NotifyModelChanged(hints)
   
   # accessors
   def Ctrl(self): return self._ctrl
   def SetCtrl(self, ctrl): self._ctrl = ctrl
   def Data(self): return self._data
   def SetData(self, data):
      self._data = data
      self._NotifyChanges()
   def Touch(self): self.modified = True
      
   # properties
   data = property(Data, SetData)
   
   
#============================================================================
# View
#============================================================================
class View(QWidget):
   """Abstract base class for a View in a MVC (Model-View-Controller) architecture
   
   A view visualizes the data stored in a model and communicates changes (actively
   and passively) via the controller.
   Any number of different views can be attached to a model.
   Views must react to changes in the model by implementing the UpdateContent
   function, possibly reacting to HINTS defined in the controller and only doing
   a partial update.
   """
   def __init__(self, ctrl, parent=None):
      """View constructor
         parameters:
            -ctrl         the controller of the model to which to attach to
      """
      super(View, self).__init__(parent)
      self.ctrl = ctrl
      self.ctrl.AttachView(self)
         
   def UpdateContent(self, hints=None):
      raise NotImplementedError


#============================================================================
# View
#============================================================================
class TextEditView(QTextEdit):
   """ Special abstract base class for a QTextEdit-based View in a MVC (Model-View-Controller) architecture """
   def __init__(self, ctrl, parent=None):
      """View constructor
         parameters:
            -ctrl         the controller of the model to which to attach to
      """
      super(TextEditView, self).__init__(parent)
      self.ctrl = ctrl
      self.ctrl.AttachView(self)
         
   def UpdateContent(self, hints=None):
      raise NotImplementedError
