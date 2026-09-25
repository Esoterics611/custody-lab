# Proof of control

**Definition.** A signature under the custody key over a message that could not have been
prepared in advance, such as a statement naming a recent block hash. It shows that the key
holders could sign at that time.

**Why custody cares.**
- On-chain coins are public, but whoever names an address may not control it.
- The signing key is also the spending key, so the attestation message must never be usable as
  a transaction sighash. A tag of its own for the attestation hash separates the two.
- It does not show that the coins are unencumbered or were not borrowed for the snapshot.

**In the demo.** `src/custody_lab/reserves/snapshot.py` (`Snapshot.attestation_message`,
`publish`); `PolicyEngine.authorise_attestation` in `src/custody_lab/policy/engine.py`. The FROST
cluster signs under the Taproot output key. Tests: `tests/reserves/test_snapshot.py`.

**In the manual.** Chapter 6, "Proof of control", "Snapshot and attestation", "The whole demo".

**Sources.** BIP 340 (signature), BIP 341 (`TapSighash` tag); G. G. Dagher et al., ACM CCS 2015.
