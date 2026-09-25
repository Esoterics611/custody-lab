# Hash-chained audit trail

**Definition.** Each log entry stores the hash of its content plus the previous entry's hash.
Editing, deleting or reordering an entry breaks every later link. Truncation and a full rewrite
are detected only by comparing the head hash with a copy published elsewhere (anchoring).

**Why custody cares.**
- Approvals, denials and authorisations are evidence for auditors (SOC 2) and in disputes.
- A log the operator can silently edit is not evidence.
- The engine reads velocity and "authorised before" from this log, so it is also the engine's
  only state.

**In the demo.** `src/custody_lab/policy/audit.py` (`AuditLog`, `verify_chain`), in memory. Each
proof-of-reserves snapshot anchors the head (`src/custody_lab/reserves/snapshot.py`).

**In the manual.** Chapter 4, "Hash-chained audit log", the tamper walkthrough, Exercise 4.

**Sources.** Schneier and Kelsey, *ACM TISSEC* 1999; Crosby and Wallach, USENIX Security 2009;
RFC 9162.
