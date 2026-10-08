# Default deny

**In one sentence.** Under default deny, every request is refused unless a rule explicitly allows
it, so anything nobody anticipated is refused rather than let through.

## The problem

A rule set written as a list of things to block fails open: a new asset nobody wrote a rule for, a
mistyped address or an empty amount field passes a blocklist. A broadcast settlement cannot be
reversed, so an allow-by-default gap is an open door that no later control can close.

## The idea

The policy describes what is allowed; everything else is refused. In the demo's engine an
instruction passes seven ordered checks, and the first failure decides:

1. the asset has a policy;
2. the amount is a finite, positive number;
3. the amount fits a tier, which sets how many approvals it needs (above the top tier is refused);
4. the destination is on the whitelist;
5. the rolling-window velocity limit holds;
6. the instruction has not been authorised before;
7. enough valid approvals are present (too few gives PENDING, which more approvals can fix; every
   earlier failure is final).

The comparison with a FIX gateway's pre-trade risk checks holds up to correction: an erroneous trade
can sometimes be busted, a confirmed payment cannot, so the engine cannot rely on catching mistakes
afterwards.

## Why custody cares

It is the reason a misconfiguration fails safe. Firewall rule sets end with "deny everything else"
for the same reason.

## In the demo

`src/custody_lab/policy/engine.py` (`PolicyEngine._decide`: seven ordered checks; the first failure
decides). Tested in `tests/policy/test_policy_engine.py`, including a Hypothesis test that every
unknown asset is denied.

## In the manual

[Chapter 0](../../manual/chapters/00-orientation.md),
"[Default deny](../../manual/chapters/00-orientation.md#default-deny)";
[chapter 4](../../manual/chapters/04-policy.md),
"[Default deny](../../manual/chapters/04-policy.md#default-deny)" and
"[The decision function](../../manual/chapters/04-policy.md#the-decision-function)".

## Sources

NIST SP 800-53 Rev. 5, AC-3 (access enforcement) and SC-7(5) (deny by default).
