# Hash functions

**In one sentence.** A cryptographic hash function turns any input into a fixed-size fingerprint
(32 bytes for SHA-256) such that nobody can find an input for a given fingerprint or two inputs with
the same one.

## The problem

Signatures, commitments, Merkle trees and audit logs all need a short value that stands for a long
one and cannot be steered: changing the input must change the value unpredictably, and nobody may
be able to choose an input that produces a value they want.

## The idea

A hash function maps an input of any length to a digest of fixed length. "deliver 0.85 BTC" and
"deliver 8.50 BTC" give unrelated SHA-256 digests. A cryptographic hash must resist three attacks,
each of which would break something specific:

- **preimage:** finding an input for a given digest, which would let a digest reveal its input;
- **second preimage:** finding a different input with the same digest as a given one, which would
  let one signature cover two messages;
- **collision:** finding any two inputs with the same digest, which would let an attacker get a
  harmless message signed and use the signature on another.

A **tagged hash** (BIP340) prefixes the input with $\text{SHA256}(\text{tag})$ twice, so hashes made
for different purposes (a nonce, a challenge, a sighash, a reserves attestation) can never coincide.
That separation by purpose is **domain separation**.

## Why custody cares

Inside a signature scheme the hash does three jobs: it is the digest the signer signs, the Schnorr
challenge (the Fiat-Shamir transform), and the source of deterministic nonces. Outside signatures it
builds the Merkle sum tree for proof of reserves (chapter 6) and the hash-chained audit log
(chapter 4), and tags keep a reserves attestation from ever being a valid transaction sighash.
Hashes survive quantum computers, weakened only by Grover's algorithm, which is why hash-based
signatures are one of the post-quantum families (chapter 7).

## In the demo

`src/custody_lab/foundations/hashing.py` (`sha256`, `tagged_hash`).

## In the manual

[Chapter 0](../../manual/chapters/00-orientation.md),
"[Fingerprints: hash functions](../../manual/chapters/00-orientation.md#fingerprints-hash-functions)";
[chapter 1](../../manual/chapters/01-foundations.md),
"[Fingerprints: hash functions](../../manual/chapters/01-foundations.md#fingerprints-hash-functions)"
and "[Hash functions](../../manual/chapters/01-foundations.md#hash-functions)" (the three jobs and
tagging).

## Sources

BIP 340, "Tagged Hashes"; NIST FIPS 180-4 (SHA-2).
