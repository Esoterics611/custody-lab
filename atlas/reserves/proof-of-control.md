# Proof of control

**In one sentence.** A proof of control is a signature under the custody key over a fresh statement
that could not have been prepared in advance, such as one naming a recent block, showing that the key
holders could sign at that time.

## The problem

Coins on a public chain are visible to anyone, but anyone can name an address they do not control: a
custodian could quote someone else's address, or one whose key it has lost.

## The idea

The custodian signs a statement that includes the hash of a recent block, so the signature cannot
predate the snapshot. In the demo the statement is the canonical encoding of the reserves snapshot
(block height and hash, liabilities root and total, assets, custody key, audit head), and the same
FROST cluster that signs settlements signs it, under the same Taproot output key.

The signing key is also the spending key, so the statement must never be usable as a transaction.
The demo signs a tagged hash with the tag `custody-lab/reserves-attestation`; a transaction's sighash
is a tagged hash with the tag `TapSighash`. Two tagged hashes with different tags can be equal only
through a SHA-256 collision. The policy engine issues an attestation authorisation without approvals,
because signing a statement moves nothing, and each signer checks that the authorisation names
exactly the message in its signing package.

## Why custody cares

- It turns "these coins are on the chain" into "these coins are under our key".
- It does not show that the coins are unencumbered or were not borrowed for the moment of the
  snapshot.

## In the demo

`src/custody_lab/reserves/snapshot.py` (`Snapshot.attestation_message`, `publish`);
`PolicyEngine.authorise_attestation` in `src/custody_lab/policy/engine.py`. Tests:
`tests/reserves/test_snapshot.py`. The published file can be checked with the standard library and a
BIP340 verifier, as chapter 6's last cell does.

## In the manual

[Chapter 6](../../manual/chapters/06-reserves.md),
"[Proof of control](../../manual/chapters/06-reserves.md#proof-of-control)",
"[Snapshot and attestation](../../manual/chapters/06-reserves.md#snapshot-and-attestation)",
"[The whole demo](../../manual/chapters/06-reserves.md#the-whole-demo)".

## Sources

BIP 340 (signature), BIP 341 (`TapSighash` tag); G. G. Dagher et al., ACM CCS 2015.
