# Custody system design

**In one sentence.** The demo's architecture as a production design: fills netted per cycle, a
default-deny policy engine with its authority key in an HSM, a coordinator with no secret running
FROST with any two of three signers at independent sites, and a signed proof of reserves after each
batch.

## The problem

Each chapter built one part. A design review asks whether the parts make a sound system: what each
part holds, what its compromise alone gives an attacker, what happens when it fails, and what each
choice costs.

## The idea

FIX fills are netted into one instruction per cycle. A default-deny policy engine, whose authority
key is in an HSM, authorises the exact sighash after an approval quorum on personal devices. A
coordinator with no secret runs FROST with any two of three signers at independent sites, one of them
offline. The transaction is broadcast, and a proof-of-reserves snapshot, signed by the same key and
carrying the audit log's head, follows each batch.

Each component either holds nothing secret or holds one piece whose loss alone is contained:

- one approver key gives one approval;
- one share gives nothing below the threshold;
- the coordinator can only deny service;
- the authority key is the exception, as valuable as a threshold of shares, hence the HSM.

**Safety and liveness.** Safety failures (an unauthorised signature, lost funds) cannot be undone;
liveness failures (a delayed settlement) can be retried, so a component in doubt refuses. A threshold
of independent sites improves both: with each site 99 percent available and 1 percent likely to be
compromised, 2-of-3 signs 99.97 percent of the time and is compromised with probability about 0.0003.
Shared administration of the sites erases the gain.

## Why custody cares

The failure modes worth knowing by heart:

- Signers keep their used-token sets in memory (observed in `mpc/cluster.py`). Once shares survive a
  restart (sealed, or behind an HSM), a restart empties the set while the share remains; in the demo
  the share is lost with it. With $n \ge 2t$ two disjoint signer sets can each honour one token. Both
  are bounded by the token's expiry and by its naming one exact message.
- Nonces must never be restored from backup.
- Clock skew between engine and signers breaks expiry in both directions.
- One recovery key for every share backup is the whole key.

## In the demo

`demo/pipeline.py` runs the settlement; chapter 9's walkthrough shows any two of three signers
producing valid signatures under one key and a replayed token refused.

## In the manual

[Chapter 9](../../manual/chapters/09-capstone.md):
"[Safety and liveness](../../manual/chapters/09-capstone.md#safety-and-liveness)",
"[Architecture](../../manual/chapters/09-capstone.md#architecture)",
"[Deep dives](../../manual/chapters/09-capstone.md#deep-dives)",
"[Failure modes](../../manual/chapters/09-capstone.md#failure-modes)",
"[Trade-offs](../../manual/chapters/09-capstone.md#trade-offs)".

## Sources

RFC 9591; BIP 340, 341, 86; BIP 125; B. Alpern and F. B. Schneider, "Defining Liveness" (1985);
R. Canetti et al., CGGMP (ACM CCS 2020).
