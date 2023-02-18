from microbit import *
from MyQueen import *

# ------------------------------------------------------------------------------
def SequenceWachtA(S):
    if S.IsNewState('SequenceWachtA') :
        Mq.RGB(7, 7)
        Mq.Stop()

    if pin5.read_digital() == False:
        S.Goto(Sequence1s)

# ------------------------------------------------------------------------------
def Sequence1s(S):
    if S.IsNewState('Sequence1s') :
        Mq.RGB(5, 5)

    if S.StateTime(1000) :
        S.Return() # einde van sequence

# ------------------------------------------------------------------------------
def SeqenceVolgWand(S):
    if S.IsNewState('SeqenceVolgWand') :
        Mq.RGB(4, 4)

    Correctie = (Sensoren.GyDistance - 570) * 0.4 # 500 mm afstand + 70 offset voor rechtuit rijden.
    Correctie = max(-50, min(50, Correctie))

    Mq.Motors(100 + Correctie, 100 - Correctie)
    print("Afstand: %d, Correctie: %d" % (Sensoren.GyDistance, Correctie))

    Mq.IsDone() # niet nodig voor Motors() maar kan geen kwaad (aanroep van IsDone() moet altijd werken)

# ------------------------------------------------------------------------------
# start van main
# ------------------------------------------------------------------------------

Sm = StateMachine()

Sensoren = TSensors()
print("Begin")

Sm.Goto([SequenceWachtA, SeqenceVolgWand])

while Sm.IsDone() == False:
    Sensoren.Takt()   # volgt tevens timing van GY-53 pwm signaal
    Sm.Takt()

Mq.RGB(0, 0)

print("Einde")
