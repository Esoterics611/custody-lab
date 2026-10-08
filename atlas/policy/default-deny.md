# Default deny

**Definition.** Every request is refused unless a rule explicitly allows it. An unknown asset, an
amount outside every tier, a non-positive or non-numeric amount, or an unlisted destination is a
denial, not a pass-through.

**Why custody cares.** A broadcast settlement cannot be reversed. An allow-by-default gap, such as
a new asset nobody wrote a rule for, is an open door that no later control can close.

**In the demo.** `src/custody_lab/policy/engine.py` (`PolicyEngine._decide`: seven ordered checks;
the first failure decides). Tested in `tests/policy/test_policy_engine.py`, including a
Hypothesis test that every unknown asset is denied.

**In the manual.** [Chapter 4](../../manual/chapters/04-policy.md), "[The decision function](../../manual/chapters/04-policy.md#the-decision-function)".

**Sources.** NIST SP 800-53 Rev. 5, AC-3 (access enforcement) and SC-7(5) (deny by default).
