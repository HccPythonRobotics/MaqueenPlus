import time
from microbit import *
from machine import time_pulse_us

import struct


class StateMachine:

   
   def __init__(self):
      self.TaktInterval = 0      
      self.Reset()

   
   def Reset(self):
      self._States      = []
      self._PreNewState = True
      self._NewState    = True
      self._LastTaktMs  = 0

   
   
   def Goto(self, NextState):
      print("Goto ", end='')
      self.Return(True) 

      
      if isinstance(NextState, list) :
         for S in reversed(NextState) :
            self._States.append(S)        
      else :
         self._States.append(NextState)   

   
   
   
   def Return(self, Silent=False):
      if Silent == False : print("Return.")
      if len(self._States) > 0 :
         self._States.pop() 
      self._PreNewState = True

   
   def Takt(self):

      if time.ticks_ms() - (self.TaktInterval + self._LastTaktMs) < 0 :
         return 

      self._LastTaktMs = time.ticks_ms()

      if len(self._States) == 0:
         print('Takt error - no more states')
         return

      
      self._PreNewState = False
      if self._NewState:
         self._StateStartMs = time.ticks_ms()
      self._States[-1](self)
      self._NewState = self._PreNewState

   
   
   def IsNewState(self, StateName):
      if self._NewState:
         print("NewState", StateName)
      return self._NewState

   
   
   def IsDone(self):
      return len(self._States) == 0

   
   
   def StateTime(self, Delay):
      return (time.ticks_ms() - (self._StateStartMs + Delay)) > 0


class MaqueenPlus:

   
   def __init__(self):
      pass

   
   
   def RGB(self, ColourL, ColourR):
      display.clear()
      if ColourL == 1 :
         
         display.set_pixel(1, 0, 9)
         display.set_pixel(2, 0, 9)
         display.set_pixel(3, 0, 9)
         return

      if ColourL == 3 :
         
         display.set_pixel(1, 2, 9)
         display.set_pixel(2, 2, 9)
         display.set_pixel(3, 2, 9)
         return

      if ColourL == 2 :
         
         display.set_pixel(1, 4, 9)
         display.set_pixel(2, 4, 9)
         display.set_pixel(3, 4, 9)
         return

      display.show(ColourL)

   
   
   
   def Motors(self, SpeedL, SpeedR):
      pass

   
   
   def Stop(self):
      pass

























class TSensors():

   
   def __init__(self):
      self.UsDistance   = 9999
      self.GyDistance   = 9999
      self.UsTriggerPin = pin1
      self.UsEchoPin    = pin2
      self.GyPin        = pin15
      self._UsCounter   = 99

   
   def Takt(self) :
      self._Ultrasonic()
      self._GY53()
      

   
   def _GY53(self) :
      while self.GyPin.read_digital() == True:
         pass 

      
      
      self.GyDistance = int(0.1 * time_pulse_us(self.GyPin, 1, 55000))

   
   def _Ultrasonic(self):

      self._UsCounter += 1
      if self._UsCounter < 2 :
         return 

      self._UsCounter = 0 

      
      self.UsTriggerPin.write_digital(0)
      self.UsEchoPin.read_digital()

      
      self.UsTriggerPin.write_digital(1)
      self.UsTriggerPin.write_digital(0)

      
      us = time_pulse_us(self.UsEchoPin, 1, 10000)
      if us > 0 :
         self.UsDistance = int(us * 0.17)   
      else :
         self.UsDistance = 9999             


Mq = MaqueenPlus()

