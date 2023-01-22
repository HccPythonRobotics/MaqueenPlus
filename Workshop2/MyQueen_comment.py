import time
from microbit import *
from machine import time_pulse_us

import struct

#******************************************************************************
class StateMachine:

   # --------------------------------------------------------------------------
   def __init__(self):
      self.TaktInterval = 0      # in ms
      self.Reset()

   # --------------------------------------------------------------------------
   def Reset(self):
      self._States      = []
      self._PreNewState = True
      self._NewState    = True
      self._LastTaktMs  = 0

   # --------------------------------------------------------------------------
   # Goto - Execute NextState (leave current state)
   def Goto(self, NextState):
      print("Goto ", end='')
      self.Return(True) # remove current active state (if any) without message

      # NextState can be a function or list of functions
      if isinstance(NextState, list) :
         for S in reversed(NextState) :
            self._States.append(S)        # add new items in reverse order
      else :
         self._States.append(NextState)   # add new item

   # --------------------------------------------------------------------------
   # Return - Return to previous state in list (leave current state)
   #          note: when list is empty, IsDone() is true
   def Return(self, Silent=False):
      if Silent == False : print("Return.")
      if len(self._States) > 0 :
         self._States.pop() # drop current item (if there is one)
      self._PreNewState = True

   # --------------------------------------------------------------------------
   def Takt(self):

      if time.ticks_ms() - (self.TaktInterval + self._LastTaktMs) < 0 :
         return # not yet time for next takt execution

      self._LastTaktMs = time.ticks_ms()

      if len(self._States) == 0:
         print('Takt error - no more states')
         return

      # execute state
      self._PreNewState = False
      if self._NewState:
         self._StateStartMs = time.ticks_ms()
      self._States[-1](self)
      self._NewState = self._PreNewState

   # --------------------------------------------------------------------------
   # IsNewState - check if this is first call to state, print Statename if so.
   def IsNewState(self, StateName):
      if self._NewState:
         print("NewState", StateName)
      return self._NewState

   # --------------------------------------------------------------------------
   # IsDone - returns true when all states are executed
   def IsDone(self):
      return len(self._States) == 0

   # --------------------------------------------------------------------------
   # StateTime - returns true when we're longer than Delay in the current state
   def StateTime(self, Delay):
      return (time.ticks_ms() - (self._StateStartMs + Delay)) > 0

#******************************************************************************
class MaqueenPlus:

   # --------------------------------------------------------------------------
   def __init__(self):
      self.TickToDegrees = 1.0
      self.I2caddr       = 0x10
      self.Stop()

   # --------------------------------------------------------------------------
   # RGB - Maqueen Plus - set RGB leds (color range 1~7, 1=red, 2=green, 4=blue)
   def RGB(self, ColourL, ColourR):
       buf = bytearray(3)
       buf[0] = 0x0b
       buf[1] = ColourL
       buf[2] = ColourR
       i2c.write(self.I2caddr, buf)

   # --------------------------------------------------------------------------
   # Servo - Maqueen Plus - set Degrees of servo 'Nr' = 1, 2 or 3
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

   # --------------------------------------------------------------------------
   # GetEncoders - Maqueen Plus - returns list with L & R encoder value
   def GetEncoders(self):
       buf = bytearray(1)
       buf[0] = 0x04
       i2c.write(self.I2caddr, buf)
       return struct.unpack('>HH', i2c.read(self.I2caddr, 4))

   # --------------------------------------------------------------------------
   # GetFloorSensors - Maqueen Plus - analog read of 6 floor sensors
   # Modified version of DFRobot's grayscaleValue()
   # Returns list of 6 values, from left-most to rightmost sensor.
   # 12 bits, high values are white
   def GetFloorSensors(self):
       buf = bytearray(1)
       buf[0] = 0x1E
       i2c.write(self.I2caddr, buf)
       return struct.unpack('>HHHHHH', i2c.read(self.I2caddr, 12))

   # --------------------------------------------------------------------------
   # _Motors - Maqueen Plus - set motors to speeds specified
   # Speed* = 255...-255, negative = reverse
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

   # --------------------------------------------------------------------------
   # Motors - set motors to speeds specified
   # Speed* = 255...-255, negative = reverse
   def Motors(self, SpeedL, SpeedR):

      self.TaktMode = "Motors"
      self._Motors(SpeedL, SpeedR)

   # --------------------------------------------------------------------------
   # Stop - Stop motors & reset Taktmode
   def Stop(self):
      self.TaktMode = "Stop"
      self._Motors(0,0)

   # --------------------------------------------------------------------------
   # _UpdateHeading - Use current encoder values as heading setuppoint.
   def _UpdateHeading(self):
      self.SpL, self.SpR = self.GetEncoders()

   # --------------------------------------------------------------------------
   # SpeedDistance - drive straight for <Distance> mm, correct for heading deviation
   def SpeedDistance(self, Speed, Distance):

      self._UpdateHeading()
      self.SpeedSp   = Speed
      self.HeadingSp = self.SpL - self.SpR
      self.EndPoint  = self.SpL + self.SpR + Distance * 1.17 # ticks to mm
      self.TaktMode  = "SpeedDistance"

      print("Distance :", self.EndPoint, self.SpL, self.SpR, Distance)
      self._Motors(self.SpeedSp, self.SpeedSp)

   # --------------------------------------------------------------------------
   # Rotate - rotate # of degrees at given speed
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


   # --------------------------------------------------------------------------
   def _SpeedDistanceTakt(self):
      CurrentL, CurrentR = self.GetEncoders()

      # Motor-control
      CurHeading = CurrentL - CurrentR
      Correction = (self.HeadingSp - CurHeading) * 5.0
      self._Motors(self.SpeedSp + Correction, self.SpeedSp - Correction)
      #print("Correction", Correction)

      # Check end-condition
      if (CurrentL + CurrentR) >= self.EndPoint :
         print("Done ", self.GetEncoders())
         self.Stop()
         return True    # Done

      return False      # still moving

   # --------------------------------------------------------------------------
   def _RotateTakt(self) :
      CurrentL, CurrentR = self.GetEncoders()

      # No motor control - rotation speed set at start and remains constant.

      # Check end-condition
      CurrentHeading = (CurrentL - self.SpL) + (CurrentR - self.SpR)
      #print("Rotate", CurrentL, CurrentR, self.SpL, self.SpR, CurrentHeading, self.HeadingSp, self.SpeedSp)

      # Check end-condition
      if CurrentHeading >= abs(self.HeadingSp) * self.TickToDegrees :
         print("Done ", self.GetEncoders())
         self._UpdateHeading()
         self.Stop()
         return True    # Done

      return False      # still moving

   # --------------------------------------------------------------------------
   # IsDone - return true if requested command had been completed
   # Note: also act as takt, so call at regular interval.
   def IsDone(self):

      if self.TaktMode == "SpeedDistance" :
         return self._SpeedDistanceTakt()

      if self.TaktMode == "Rotate" :
         return self._RotateTakt()

      if self.TaktMode == "Stop" :
         self.Stop()
         return True

      if self.TaktMode == "Motors" :
         # no action
         return True

      # Known modes are handled above, so error.
      print("IsDone/Takt ERROR: invalid TaktMode (%s)" % self.TaktMode)
      return True # done (sort of)

#******************************************************************************
class TSensors():

   # --------------------------------------------------------------------------
   def __init__(self):
      self.UsDistance   = 9999
      self.GyDistance   = 9999
      self.UsTriggerPin = pin1
      self.UsEchoPin    = pin2
      self.GyPin        = pin15
      self._UsCounter   = 99

   # --------------------------------------------------------------------------
   def Takt(self) :
      self._Ultrasonic()
      self._GY53()
      #print("Distances: ", self.UsDistance, self.GyDistance)

   # --------------------------------------------------------------------------
   def _GY53(self) :
      while self.GyPin.read_digital() == True:
         pass # Avoid measurement errors: wait until input is low.

      # High-time is proportional to distance, 10us = 1mm
      # max 55 ms, pwm cycle time is 50ms
      self.GyDistance = int(0.1 * time_pulse_us(self.GyPin, 1, 55000))

   # --------------------------------------------------------------------------
   def _Ultrasonic(self):

      self._UsCounter += 1
      if self._UsCounter < 2 :
         return # not yet time for the next measurement

      self._UsCounter = 0 # restart time-measurement

      # init io
      self.UsTriggerPin.write_digital(0)
      self.UsEchoPin.read_digital()

      # Send ultrasonic pulse
      self.UsTriggerPin.write_digital(1)
      self.UsTriggerPin.write_digital(0)

      # Measure time until echo is received (blokking)
      us = time_pulse_us(self.UsEchoPin, 1, 10000)
      if us > 0 :
         self.UsDistance = int(us * 0.17)   # convert us to mm
      else :
         self.UsDistance = 9999             # no echo

# create instance
Mq = MaqueenPlus()

