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
      self.TickToDegrees = 1.0
      self.I2caddr       = 0x10
      self.Stop()

   
   
   def RGB(self, ColourL, ColourR):
       buf = bytearray(3)
       buf[0] = 0x0b
       buf[1] = ColourL
       buf[2] = ColourR
       i2c.write(self.I2caddr, buf)

   
   
   def Servo(self, Nr, Degrees):

      buf = bytearray(2)
      buf[0] = 0
      buf[1] = Degrees

      if Nr == 1 :
         buf[0] = 0x14

      if Nr == 2 :
         buf[0] = 0x15

      if Nr == 3 :
         buf[0] = 0x16

      if buf[0] > 0 :
         i2c.write(self.I2caddr, buf)

   
   
   def GetEncoders(self):
       buf = bytearray(1)
       buf[0] = 0x04
       i2c.write(self.I2caddr, buf)
       return struct.unpack('>HH', i2c.read(self.I2caddr, 4))

   
   
   
   
   
   def GetFloorSensors(self):
       buf = bytearray(1)
       buf[0] = 0x1E
       i2c.write(self.I2caddr, buf)
       return struct.unpack('>HHHHHH', i2c.read(self.I2caddr, 12))

   
   
   
   def _Motors(self, SpeedL, SpeedR):

      if SpeedL > 0 :
         DirL     = 1
      else :
         DirL     = 2
         SpeedL   = -SpeedL

      if SpeedR > 0 :
         DirR     = 1
      else:
         DirR     = 2
         SpeedR   = -SpeedR

      buf = bytearray(5)
      buf[0] = 0x00
      buf[1] = DirL
      buf[2] = int(SpeedL)
      buf[3] = DirR
      buf[4] = int(SpeedR)
      i2c.write(self.I2caddr, buf)

   
   
   
   def Motors(self, SpeedL, SpeedR):

      self.TaktMode = "Motors"
      self._Motors(SpeedL, SpeedR)

   
   
   def Stop(self):
      self.TaktMode = "Stop"
      self._Motors(0,0)

   
   
   def _UpdateHeading(self):
      self.SpL, self.SpR = self.GetEncoders()

   
   
   def SpeedDistance(self, Speed, Distance):

      self._UpdateHeading()
      self.SpeedSp   = Speed
      self.HeadingSp = self.SpL - self.SpR
      self.EndPoint  = self.SpL + self.SpR + Distance * 1.17 
      self.TaktMode  = "SpeedDistance"

      print("Distance :", self.EndPoint, self.SpL, self.SpR, Distance)
      self._Motors(self.SpeedSp, self.SpeedSp)

   
   
   def Rotate(self, Degrees, Speed):

      self._UpdateHeading()

      if Degrees > 0 :
         self.SpeedSp = abs(Speed)
      else:
         self.SpeedSp = -abs(Speed)

      self.HeadingSp = Degrees
      self.TaktMode  = "Rotate"

      print("Rotate :", Degrees, Speed, self.SpL, self.SpR, self.HeadingSp)
      self._Motors(self.SpeedSp * -1, self.SpeedSp)


   
   def _SpeedDistanceTakt(self):
      CurrentL, CurrentR = self.GetEncoders()

      
      CurHeading = CurrentL - CurrentR
      Correction = (self.HeadingSp - CurHeading) * 5.0
      self._Motors(self.SpeedSp + Correction, self.SpeedSp - Correction)
      

      
      if (CurrentL + CurrentR) >= self.EndPoint :
         print("Done ", self.GetEncoders())
         self.Stop()
         return True    

      return False      

   
   def _RotateTakt(self) :
      CurrentL, CurrentR = self.GetEncoders()

      

      
      CurrentHeading = (CurrentL - self.SpL) + (CurrentR - self.SpR)
      

      
      if CurrentHeading >= abs(self.HeadingSp) * self.TickToDegrees :
         print("Done ", self.GetEncoders())
         self._UpdateHeading()
         self.Stop()
         return True    

      return False      

   
   
   
   def IsDone(self):

      if self.TaktMode == "SpeedDistance" :
         return self._SpeedDistanceTakt()

      if self.TaktMode == "Rotate" :
         return self._RotateTakt()

      if self.TaktMode == "Stop" :
         self.Stop()
         return True

      if self.TaktMode == "Motors" :
         
         return True

      
      print("IsDone/Takt ERROR: invalid TaktMode (%s)" % self.TaktMode)
      return True 


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

