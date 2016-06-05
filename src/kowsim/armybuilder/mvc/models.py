# -*- coding: utf-8 -*-

# mvc/models.py
#===============================================================================
from kowsim.kow.force import ArmyList
from kowsim.mvc.mvcbase import Model

#===============================================================================
# ArmyListModel
#===============================================================================
class ArmyListModel(Model):   
   def __init__(self, *args):
      if len(args)==1 and isinstance(args[0], ArmyList):
         armylist = args[0]
         Model.__init__(self, armylist)
      else:
         name, points = args
         Model.__init__(self, ArmyList(name, points))
         
      self.settings = {}
      self.settings["UseCokValidation"] = False
   
   def _GetHtmlUnitTable(self, unit):
      """ Create and return HTML code for unit table. """
      specialText = ", ".join(unit.ListSpecialRules())
      if len(unit.ListChosenOptions())>0:
         optsText = ", ".join(["<b>%s</b>" % o.Name() for o in unit.ListChosenOptions()])
         specialText += ", " + optsText
      
      tableStyle = "{ border: 1px solid black; border-collapse: collapse; }"
      
      pre = '<table style="border-style: solid;">\n'# % tableStyle
      post = "</table>\n\n"
      name = "%s (%s)" % (unit.CustomName(), unit.Profile().DisplayName()) if len(unit.CustomName())>0 else unit.Profile().DisplayName()
      headRow = "<tr><td colspan='7'><b>%s</b></td><td colspan='2' align='right'><b>%s</b></td></tr>\n" % (name, unit.UnitType().Name())
      labelsRow="""<tr><td width='120'>Unit Size</td>
                       <td width='40'>Sp</td>
                       <td width='40'>Me</td>
                       <td width='40'>Ra</td>
                       <td width='40'>De</td>
                       <td width='40'>At</td>
                       <td width='55'>Ne</td>
                       <td width='55'>Pts</td>
                       <td width='350'>Special</td></tr>\n"""
      profileRow="""<tr><td width='120'>%s</td>
                       <td width='40'>%d</td>
                       <td width='40'>%s</td>
                       <td width='40'>%s</td>
                       <td width='40'>%s</td>
                       <td width='40'>%s</td>
                       <td width='55'>%s</td>
                       <td width='55'>%d</td>
                       <td width='350'>%s</td></tr>\n""" % (unit.SizeType().Name(), unit.Sp(), unit.MeStr(), unit.RaStr(), unit.DeStr(), unit.AtStr(),
                                                            unit.NeStr(), unit.PointsCost(), specialText)
      return pre+headRow+labelsRow+profileRow+post
      
   
   def GenerateHtml(self):
      """ Generate HTML string for army list and return it for export or display. """
      al = self.Data()
      
      header = """<html>\n
      <head>\n
         <title>%s (%dp)</title>\n
         <meta charset="UTF-8">\n
      </head>\n
      <body>\n""" % (al.CustomName(), al.PointsLimit())
      
      footer = """</body>\n</html>\n"""
      
      pointsStr = "%d/%d points" % (al.PointsTotal(), al.PointsLimit())
      if al.PointsTotal() > al.PointsLimit():
         pointsStr = "<font color='#ff0000'><u>" + pointsStr + "</u></font>"
      content  = "   <h1>%s (%s)</h1>\n" % (al.CustomName(), pointsStr)
      content += "   <h4>%d detachment%s</h4>\n" % (al.NumDetachments(), "s" if al.NumDetachments()>1 else "")
      
      for det in al.ListDetachments():
         content += "   <h2>%s (%s)</h2>\n" % (det.CustomName(), det.Choices().Name())
         content += "   <h4>%d units, %d points</h4>\n" % (det.NumUnits(), det.PointsTotal())
         content += "</p>\n".join([self._GetHtmlUnitTable(unit) for unit in det.ListUnits()])
      
      return (header + content + footer)