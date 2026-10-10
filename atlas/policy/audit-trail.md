# Hash-chained audit trail

**In one sentence.** In a hash-chained log each entry includes the hash of the entry before it, so
editing, deleting or reordering any entry breaks every link after it, and publishing the latest hash
elsewhere (anchoring) also exposes truncation and wholesale rewriting.

## The problem

Approvals, denials and authorisations are the evidence auditors rely on and that settles disputes
after an incident. An ordinary log file can be edited by anyone with write access, and the edit
leaves no trace.

## The idea

Entry $n$ stores $h_n = H(n \,\|\, \text{time} \,\|\, \text{event} \,\|\, \text{payload} \,\|\,
h_{n-1})$, computed over a canonical encoding, starting from 32 zero bytes. Change entry 1 of three
and its hash no longer matches the link stored in entry 2; the chain check fails at entry 1.

The chain is **tamper-evident**, not tamper-proof: the hashes use no secret, so whoever can edit an
entry can also recompute them. A forger hiding an edit makes three moves, and the check follows
each one:

1. Edit entry $k$: the check stops at entry $k$, whose content no longer matches its hash.
2. Replace entry $k$'s stored hash with the hash of its new contents: the check stops at entry
   $k + 1$, whose **link** still names the old hash. If $k$ is the last entry, the chain verifies.
3. Re-hash every later entry, each link set to the new hash before it: the chain verifies.

Cutting entries off the end also passes the check. Both a re-hash and a truncation are caught only
by a copy of the **head**, the newest entry's hash, published somewhere the operator cannot change:
an **anchored head**. A re-hashed copy differs from the genuine log in every hash from entry $k$
onward and in none before it, so an anchor taken when entry $m$ was newest is missing from the copy
exactly when $m \ge k$. Entries after the latest anchor, the **unanchored tail**, are covered by no
anchor until the next one is published. In the demo, every proof-of-reserves snapshot carries the
head and is signed by the custody key, so the anchor cannot be moved to the forged head without
breaking the signature.

The model assumes the forger changes a copy of the log, such as the one handed to an auditor, and
not the log the engine writes to: the next snapshot anchors the engine's own head. A forger who can
rewrite the engine's own log before the next snapshot also changes what that snapshot anchors,
which is why a production log sits on write-once storage outside the engine's control.

## Why custody cares

- A log the operator can silently edit is not evidence.
- The demo's engine reads velocity and "authorised before" from this log, so it is also the engine's
  only state: the record and the decision cannot disagree.

## In the demo

`src/custody_lab/policy/audit.py` (`AuditLog`, `verify_chain`), in memory, in the policy engine's
process. Each proof-of-reserves snapshot anchors the head (`src/custody_lab/reserves/snapshot.py`).

The dashboard's **The audit log** tab and `uv run custody-lab audit`
(`src/custody_lab/demo/audit_trail.py`) show the log entry by entry through two settlements and two
snapshots, then a forger's copy: for every entry, where the chain check stops after each of the
three moves, and which snapshot's anchored head exposes the re-hashed copy. The attack panel's
"Delete a signed payment from the audit log and re-hash it" shows the other defence: the signers'
own record of the authorisations they signed under.

## In the manual

[Chapter 4](../../manual/chapters/04-policy.md),
"[A log that shows its own edits](../../manual/chapters/04-policy.md#a-log-that-shows-its-own-edits)"
(a chain built and edited by hand),
"[A forger's copy and the anchored head](../../manual/chapters/04-policy.md#a-forgers-copy-and-the-anchored-head)"
(the three moves and the anchor, worked by hand and run on the engine's `AuditLog`),
"[Hash-chained audit log](../../manual/chapters/04-policy.md#hash-chained-audit-log)" (which edits
an anchor exposes), the tamper walkthrough,
"[The anchored head inside a signed snapshot](../../manual/chapters/04-policy.md#the-anchored-head-inside-a-signed-snapshot)",
and Exercises 4 and 6. The walkthrough's
"[The audit log](../../manual/demo-walkthrough.md#the-audit-log)" operates the tab. The attack-vector
analysis lists the log's vectors as 10.1 and 10.2
([attack vectors](../../manual/attack-vectors.md#10-the-records)).

## Sources

B. Schneier, J. Kelsey, *ACM TISSEC* 1999; S. Crosby, D. Wallach, USENIX Security 2009; RFC 9162.
