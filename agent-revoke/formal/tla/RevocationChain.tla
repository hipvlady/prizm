------------------------------ MODULE RevocationChain ------------------------------
EXTENDS Naturals, TLC

CONSTANTS
  NumDepth,
  TimeoutTicks,
  RevokeTick,
  MaxTicks

DepthSet == 0..NumDepth
Capabilities == DepthSet
Root == 0
Parent == [c \in Capabilities |-> IF c = Root THEN Root ELSE c - 1]
CapAtDepth == [d \in DepthSet |-> d]
BoundByDepth == [d \in DepthSet |-> TimeoutTicks * (d + 1)]

States == {"Valid", "Revoked", "Transient", "Invalid"}

VARIABLES
  tick,
  capState,
  transientAge,
  unauthorizedCount

vars == <<tick, capState, transientAge, unauthorizedCount>>

TypeOK ==
  /\ tick \in Nat
  /\ capState \in [Capabilities -> States]
  /\ transientAge \in [Capabilities -> Nat]
  /\ unauthorizedCount \in [Capabilities -> Nat]

ConstantsOK ==
  /\ NumDepth \in Nat
  /\ NumDepth >= 1
  /\ TimeoutTicks \in Nat \ {0}
  /\ RevokeTick \in Nat
  /\ MaxTicks \in Nat
  /\ RevokeTick <= MaxTicks

Init ==
  /\ ConstantsOK
  /\ tick = 0
  /\ capState = [c \in Capabilities |-> "Valid"]
  /\ transientAge = [c \in Capabilities |-> 0]
  /\ unauthorizedCount = [c \in Capabilities |-> 0]

RECURSIVE Ancestors(_)
Ancestors(c) ==
  IF c = Root THEN {}
  ELSE {Parent[c]} \cup Ancestors(Parent[c])

HasRevokedAncestor(c, state) ==
  \E a \in Ancestors(c): state[a] \in {"Revoked", "Invalid"}

NextState(c, state, age) ==
  IF c = Root THEN
    IF tick >= RevokeTick THEN "Revoked" ELSE state[c]
  ELSE IF HasRevokedAncestor(c, state) THEN
    CASE state[c] = "Invalid" -> "Invalid"
      [] state[c] = "Transient" /\ age[c] + 1 >= TimeoutTicks -> "Invalid"
      [] state[c] = "Transient" -> "Transient"
      [] OTHER -> "Transient"
  ELSE state[c]

NextAge(c, state, age) ==
  IF c = Root THEN
    0
  ELSE
    CASE NextState(c, state, age) = "Transient" /\ state[c] = "Transient" -> age[c] + 1
      [] NextState(c, state, age) = "Transient" -> 0
      [] OTHER -> 0

NextUnauthorized(c, state, age, unauthorized) ==
  IF c # Root /\ state[c] = "Transient" /\ NextState(c, state, age) = "Transient" THEN
    unauthorized[c] + 1
  ELSE
    unauthorized[c]

Tick ==
  IF tick < MaxTicks THEN
    /\ tick' = tick + 1
    /\ capState' = [c \in Capabilities |-> NextState(c, capState, transientAge)]
    /\ transientAge' = [c \in Capabilities |-> NextAge(c, capState, transientAge)]
    /\ unauthorizedCount' =
      [c \in Capabilities |-> NextUnauthorized(c, capState, transientAge, unauthorizedCount)]
  ELSE
    /\ UNCHANGED vars

Spec == Init /\ [][Tick]_vars /\ WF_vars(Tick)

TransientAgeBound ==
  \A c \in Capabilities: capState[c] = "Transient" => transientAge[c] < TimeoutTicks

UnauthorizedWithinBound ==
  \A d \in DepthSet: unauthorizedCount[CapAtDepth[d]] <= BoundByDepth[d]

CascadeSafety ==
  \A c \in Capabilities \ {Root}:
    []((HasRevokedAncestor(c, capState)) => <>(capState[c] = "Invalid"))

TransientEventuallyInvalid ==
  \A c \in Capabilities:
    [](capState[c] = "Transient" => <>(capState[c] = "Invalid"))

=============================================================================
