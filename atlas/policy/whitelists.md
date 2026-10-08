# Destination whitelists

**In one sentence.** Each asset has a list of approved destination addresses, and an instruction to
any other address is refused whatever approvals it carries.

## The problem

An attacker who controls the approval quorum, or an insider who raises a payment, wants the coins
sent to an address they control. Approvals alone do not stop that.

## The idea

The policy holds, per asset, the set of addresses coins may go to: in the demo, the exchange's one
settlement address. The engine checks the destination before it looks at approvals. At worst, a
compromised quorum can move funds between known addresses.

The whitelist then becomes the high-value target, so changing it needs its own controls: a quorum
distinct from payment approvers, a cooling-off period before a new address becomes usable,
notification to all administrators, and verification of the address (a test transfer or a signed
statement from its owner). A tokenised fund enforces the same idea from the other side, with an
allowlist kept by its transfer agent: the custodian refuses to send to unknown addresses, and the
token refuses to arrive at them (chapter 8).

## Why custody cares

It limits what a compromised approval quorum can do, and it moves the attack to the whitelist's own
governance, which can be made slower and more visible than a payment.

## In the demo

`src/custody_lab/policy/engine.py` (`AssetPolicy.whitelist`, check 4). Whitelist governance is not
implemented.

## In the manual

[Chapter 4](../../manual/chapters/04-policy.md),
"[Rules: tiers, whitelist and a rolling window](../../manual/chapters/04-policy.md#rules-tiers-whitelist-and-a-rolling-window)",
worked example row 9, and Exercise 5.

## Sources

Vendor policy documentation for address allow-lists (**verify current** per vendor).
