import random

class StandardDie:
   def __init__(self, sides=6):
      self.sides = sides
      
   def Roll(self):
      return random.randint(1, self.sides)

D3 = StandardDie(3)
D4 = StandardDie(4)
D6 = StandardDie(6)
D8 = StandardDie(8)
D10 = StandardDie(10)
D12 = StandardDie(12)
D20 = StandardDie(20)
D100 = StandardDie(100)

class IndividualRoll:
   def __init__(self, die=D6, toPass=[4,5,6], reroll=False):
      self.die = die
      self.toPass = toPass
      self.reroll = reroll
      
      self.results = []
      self.numPassed = 0
      
   def __str__(self):
      s = "%i+" % self.toPass[0]
      if self.reroll: s+= " rerollable"
      return s
      
   def Execute(self, numDice):
      self.results.append([]) # self.results[0] holds the actual roll results (as a list), while self.results[1] holds results of a potential reroll.
      
      for i in range(numDice):
         r = self.die.Roll()
         self.results[0].append(r)
         if r in self.toPass: self.numPassed += 1
         
      print "Rolling %i dice on a %i+:" % (numDice, self.toPass[0]), ",".join([str(r) for r in self.results[0]])
      print "%i successes." % self.numPassed
         
      if self.reroll:
         numReroll = numDice - self.numPassed
         originalSuccesses = self.numPassed
         for j in range(numReroll):
            r = self.die.Roll()
            self.results[1].append(r)
            if r in self.toPass: self.numPassed += 1

         print "Rerolling %i dice:" % (numReroll), ",".join([str(r) for r in self.results[1]])
         print "%i extra successes for %i total." % (self.numPassed - originalSuccesses, self.numPassed)
      
      return self.numPassed, self.results


class RollHandler:
   def __init__(self, s=""):
      self.defaultDie = D6
      self.individualRolls = []
      self.numDice = 0
      
      self.finishedInit = False
      
      if s!="":
         self.InterpretString(s)
         
   def AllResultsToString(self, delimiter="\n"):
      s = ""
      
      partialStrings = []
      for res in self.allResults:
         extraS = ",".join([str(r) for r in res[1]])
         if len(self.individualRolls)>0:
            extraS += " (%i successes)" % res[0]
         
         partialStrings.append(extraS)
         
      s += delimiter.join(partialStrings)
            
      return s
         
   def RollModeToString(self):
      s = "Rolling: "
      s += "%i dice" % self.numDice if self.numDice is not 1 else "1 die"
      
      if len(self.individualRolls) > 0:
         s += " on a "
         rollStrs = [str(roll) for roll in self.individualRolls]
         s += ", then ".join(rollStrs)
      
      s += "."
      return s
      
   def InterpretString(self, s):
      self.commandString = s
      
      if len(s) == 0: # empty string, just roll a single die
         self.numDice = 1
         self.die = self.defaultDie
         self.finishedInit = True
         return
      
      # don't be case sensitive
      s = s.lower()
      
      # first, split string into arguments separated by blanks
      subStrings = s.split()
      
      # the first substring is the number and type of dice to be rolled.
      # if no type is given, use the default die.
      if subStrings[0].isdigit():
         self.numDice = int(subStrings[0])
         self.die = self.defaultDie
      else: # probably '5d6' or something
         i = subStrings[0].find('d') # look for the first 'd'
         
         if i == -1: # it's neither an integer nor does it include a 'd' - something is wrong here
            raise ValueError("Invalid parameters for roll '%s'." % s)
            
         else:
            # make sure that there's a number in front of the 'd'
            if not subStrings[0][:i].isdigit():
               raise ValueError("Invalid number of dice '%s' in roll '%s'." % (subStrings[0][:i], s))
            else:
               self.numDice = int(subStrings[0][:i])
               
            # then, determine the type of the dice
            diceStr = subStrings[0][i+1:]
            if diceStr.isdigit():
               self.die = StandardDie(int(diceStr))
            else: # TODO: May add custom dice. But as of now, yield an error
               raise ValueError("Unknown dice type '%s' in roll '%s'." % (diceStr, s))
               
      # now, if there are more arguments in the string, continue to parse them
      for subString in subStrings[1:]:
         # initialization
         toRoll = ""
         idx = 0
         reroll = False
         
         # should begin with a number which is the required roll
         while subString[idx].isdigit() and idx < len(subString):
            toRoll += subString[idx]
            idx += 1
            
         toRoll = int(toRoll)
         if idx < len(subString)-1:
            # interpret the rest of the string.
            # options until now: '+' (needs this score or more [default]), 'r' (reroll entire roll)
            for c in subString[idx:]:
               if c == '+':
                  pass
               elif c == 'r':
                  reroll = True
               else: raise ValueError("Unknown argument '%s' in roll '%s'." % (c, s))
               
         # finished parsing individual roll, assemble object for it
         passedResults = range(toRoll, self.die.sides+1)
         rpms = IndividualRoll(self.die, passedResults, reroll)
         self.individualRolls.append(rpms)
         
      # done
      self.finishedInit = True
         
   def Roll(self):
      if not self.finishedInit: raise ValueError("Can't roll yet - no command given!")
      
      self.allResults = []
      diceLeft = self.numDice
      
      if len(self.individualRolls) > 0:
         for idvRoll in self.individualRolls:
            passed, results = idvRoll.Execute(numDice=diceLeft)
            if passed==0: break
            diceLeft = passed
            
            self.allResults.append([passed, results])
            
      else: # just roll some dice and be done
         self.allResults.append([0, [self.die.Roll() for i in xrange(self.numDice)]])
            
      return self.allResults
         
   def SetDefaultDie(self, die):
      self.defaultDie = die