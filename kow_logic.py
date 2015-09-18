class KowUnitType:
   """ Container class for a unit type in KoW with information on available sizes and formations. """
   def __init__(self, typeName="Infantry"):
      self.typeName = typeName
      self.availableSizes = []
      self.availableBaseSizes = []
      
   def __str__(self):
      return self.typeName + " (Options: " + ", ".join([str(avS) for avS in self.availableSizes]) + ")"
      
class KowUnitSize:
   def __init__(self, unitSize="Troop", formation=(5,2)):
      self.unitSize = unitSize
      self.formation = formation
      
   def __str__(self):
      return self.unitSize + " (%i)" % self.Count()
      
   def Count(self):
      return self.formation[0]*self.formation[1]