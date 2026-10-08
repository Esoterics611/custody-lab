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

Two changes still pass the check: cutting entries off the end, and rewriting everything from the
edited entry onward with fresh hashes. Both are caught only by comparing the latest hash, the
**head**, with a copy published somewhere the operator cannot change. In the demo, every
proof-of-reserves snapshot carries the head and is signed by the custody key.

## Why custody cares

- A log the operator can silently edit is not evidence.
- The demo's engine reads velocity and "authorised before" from this log, so it is also the engine's
  only state: the record and the decision cannot disagree.

## In the demo

`src/custody_lab/policy/audit.py` (`AuditLog`, `verify_chain`), in memory. Each proof-of-reserves
snapshot anchors the head (`src/custody_lab/reserves/snapshot.py`).

## In the manual

[Chapter 4](../../manual/chapters/04-policy.md),
"[A log that shows its own edits](../../manual/chapters/04-policy.md#a-log-that-shows-its-own-edits)"
(a chain built and edited by hand),
"[Hash-chained audit log](../../manual/chapters/04-policy.md#hash-chained-audit-log)", the tamper
walkthrough, and Exercise 4.

## Sources

B. Schneier, J. Kelsey, *ACM TISSEC* 1999; S. Crosby, D. Wallach, USENIX Security 2009; RFC 9162.
