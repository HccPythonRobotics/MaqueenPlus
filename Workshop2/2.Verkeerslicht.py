from MyQueen import *

# ------------------------------------------------------------------------------
def StateRood(S):
    if S.IsNewState('StateRood') :
        Mq.RGB(1, 1)

    if S.StateTime(5000) :
        S.Goto(StateGroen)

# ------------------------------------------------------------------------------
def StateGroen(S):
    if S.IsNewState('StateGroen') :
        Mq.RGB(2, 2)

    if S.StateTime(5000) :
        S.Goto(StateOranje)

# ------------------------------------------------------------------------------
def StateOranje(S):
    if S.IsNewState('StateOranje') :
        Mq.RGB(3, 3)

    if S.StateTime(2000) :
        S.Goto(StateRood)

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
# start van main
# ------------------------------------------------------------------------------
Sm = StateMachine()

Sm.Goto(StateGroen)

while Sm.IsDone() == False:
    Sm.Takt()
