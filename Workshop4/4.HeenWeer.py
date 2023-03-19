from microbit import *
from MyQueen import *

# ------------------------------------------------------------------------------
def SequenceWachtA(S):
    if S.IsNewState("SequenceWachtA"):
        Mq.RGB(7, 7)
        Mq.Stop()

    if pin5.read_digital() == False:
        S.Goto(Sequence1s)


# ------------------------------------------------------------------------------
def Sequence1s(S):
    if S.IsNewState("Sequence1s"):
        Mq.RGB(5, 5)

    if S.StateTime(1000):
        S.Return()  # einde van sequence


# ------------------------------------------------------------------------------
def SeqenceVolgWand(S):
    if S.IsNewState("SeqenceVolgWand"):
        Mq.RGB(4, 4)

    Correctie = (
        Sensoren.GyDistance - 570
    ) * 0.4  # 500 mm afstand + 70 offset voor rechtuit rijden.
    Correctie = max(-50, min(50, Correctie))

    Mq.Motors(100 + Correctie, 100 - Correctie)
    print("Afstand: %d, Correctie: %d" % (Sensoren.GyDistance, Correctie))

    # stop als we dichtbij een obstakel (wand B) zien
    if Sensoren.UsDistance < 300:
        Mq.Stop()
        S.Return()

    Mq.IsDone()  # niet nodig voor Motors() maar kan geen kwaad (aanroep van IsDone() moet altijd werken)


# ------------------------------------------------------------------------------
def SeqenceTerugNaarStart(S):
    if S.IsNewState("SeqenceTerugNaarStart"):
        Mq.RGB(3, 3)
        Mq.Rotate(180, 40)  # draai 180 graden

    if Mq.IsDone():
        S.Goto(SeqenceRijTerugNaarStart)


# ------------------------------------------------------------------------------
def SeqenceRijTerugNaarStart(S):
    if S.IsNewState("SeqenceRijTerugNaarStart"):
        Mq.RGB(2, 2)
        Mq.SpeedDistance(100, 9999)  # rechtuit rijden, heel ver

    # stop als we dichtbij een obstakel (wand A) zien
    if Sensoren.UsDistance < 300:
        Mq.Stop()
        S.Return()

    Mq.IsDone()  # Dit zorgt er voor dat SpeedDistance goed werkt


# ------------------------------------------------------------------------------
# start van main
# ------------------------------------------------------------------------------

Sm = StateMachine()

Sensoren = TSensors()
print("Begin")

Sm.Goto(vul_dit_in)

while Sm.IsDone() == False:
    Sensoren.Takt()  # volgt tevens timing van GY-53 pwm signaal
    Sm.Takt()

Mq.RGB(0, 0)

print("Einde")
