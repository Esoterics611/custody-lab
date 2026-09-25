# Hash functions

**Definition.** A cryptographic hash maps any input to a fixed-size digest and resists preimage,
second-preimage and collision attacks. SHA-256 gives 32 bytes. A BIP340 tagged hash prefixes the
input with $\text{SHA256}(\text{tag})$ twice, separating the hash domains of different uses.

**Why custody cares.** Inside a signature scheme the hash is the message digest the signer signs,
the Schnorr challenge (Fiat-Shamir), and the source of deterministic nonces. It also builds
Merkle trees for proof of reserves (Module 6) and the hash-chained audit log (Module 4).

**In the demo.** `src/custody_lab/foundations/hashing.py` (`sha256`, `tagged_hash`).

**In the manual.** Chapter 1, "Hash functions".

**Sources.** BIP 340, "Tagged Hashes"; NIST FIPS 180-4 (SHA-2).
