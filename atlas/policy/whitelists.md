# Destination whitelists

**Definition.** Each asset has a set of approved destination addresses; an instruction to any
other address is denied regardless of approvals.

**Why custody cares.**
- It limits what a compromised approval quorum can do: at worst, move funds between known
  addresses.
- The whitelist becomes the high-value target. Adding an address needs its own quorum, a
  cooling-off period, notification and verification of the address.

**In the demo.** `src/custody_lab/policy/engine.py` (`AssetPolicy.whitelist`, check 4). Whitelist
governance is not implemented.

**In the manual.** Chapter 4, worked example row 9; Exercise 5.

**Sources.** Vendor policy documentation for address allow-lists (**verify current** per vendor).
