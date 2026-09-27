# Custody system design

**Definition.** The demo's architecture as a production design: FIX fills are netted into one
instruction per cycle. A default-deny policy engine, whose authority key is in an HSM, authorises
the exact sighash after an approval quorum on personal devices. A coordinator with no secret runs
FROST with any two of three signers at independent sites, one of them offline. The transaction is
broadcast, and a proof-of-reserves snapshot, signed by the same key and carrying the audit log's
head, follows each batch.

**Why custody cares.** Each component either holds nothing secret or holds one piece whose loss
alone is contained:

- one approver key gives one approval;
- one share gives nothing below the threshold;
- the coordinator can only deny service;
- the authority key is the exception, as valuable as a threshold of shares, hence the HSM.

Safety wins over liveness: a component in doubt refuses.

**Failure modes worth knowing by heart.**
- Signers keep their used-token sets in memory (observed in `mpc/cluster.py`). Once shares
  survive a restart (sealed, or behind an HSM), a restart empties the set while the share
  remains; in the demo the share is lost with it. With $n \ge 2t$ two disjoint signer sets can
  each honour one token. Both are bounded by the token's expiry and by its naming one exact
  message.
- Nonces must never be restored from backup.
- Clock skew between engine and signers breaks expiry in both directions.
- One recovery key for every share backup is the whole key.

**In the demo.** `demo/pipeline.py` runs the eight-step settlement; chapter 9's walkthrough shows
any two of three signers producing valid signatures under one key and a replayed token refused.

**In the manual.** Chapter 9: "Architecture", "Deep dives", "Failure modes", "Trade-offs".

**Sources.** RFC 9591; BIP 340, 341, 86; BIP 125; Alpern and Schneider, "Defining Liveness"
(1985); Canetti et al., CGGMP (ACM CCS 2020).
