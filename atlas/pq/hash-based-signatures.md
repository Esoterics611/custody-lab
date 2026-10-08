# Hash-based signatures

**In one sentence.** Hash-based signatures rest only on a hash function: a one-time key reveals
secrets whose hashes form the public key, and a Merkle tree turns many one-time keys into one
long-term key.

## The problem

A large quantum computer would break every elliptic-curve and factoring-based signature, but only
weaken hash functions. A signature built from hashes alone survives it.

## The idea

- **Lamport.** For each of the 256 digest bits, keep two secrets, one for 0 and one for 1; the public
  key is all their hashes. To sign, reveal the secret matching each bit. Each signature reveals half
  the secrets, so a key may sign once: after eight signatures with one key, the manual's cell forges
  an arbitrary message in two tries.
- **Winternitz (WOTS+).** One secret, hashed repeatedly, forms a chain whose end is public. Signing a
  digit reveals the position that many steps along. Anyone can step a chain forwards, so a
  **checksum** on extra chains signs the sum of $(15 - a_i)$: raising any message digit lowers the
  checksum, which would mean stepping a checksum chain backwards, that is, inverting the hash. With
  chains of length 4, signing the digit 2 reveals position 2 of the message chain and position 1 of
  the checksum chain; raising the digit to 3 would need position 0.
- **XMSS / LMS.** A Merkle tree of one-time keys; the root is the long-term key, and a signature
  includes the path from its leaf. The signer is **stateful**: it must never reuse a leaf, so it
  must record which it has used.
- **SLH-DSA (FIPS 205).** A hypertree of XMSS trees with a few-time scheme (FORS) at the bottom,
  choosing the leaf by a hash of the message from so many leaves that no state is needed.

## Why custody cares

- They survive a quantum computer as long as the hash does.
- A one-time key used twice leaks enough to forge, and a stateful signer restored from backup can
  reuse a leaf: the same operational hazard as a restored nonce.
- SLH-DSA has no state to lose, at a price of 7,856 to 49,856 bytes per signature.

## In the demo

Teaching code: `src/custody_lab/pq/wots.py` (WOTS+, XMSS, the SLH-DSA-SHA2-128f public root), checked
against NIST ACVP keyGen vectors in `tests/pq/test_wots.py`. Library: RustCrypto `slh-dsa` through
`rust/custody-pq`, checked in `tests/pq/test_pq_vectors.py`.

## In the manual

[Chapter 7](../../manual/chapters/07-post-quantum.md),
"[Signatures from a hash alone: Lamport](../../manual/chapters/07-post-quantum.md#signatures-from-a-hash-alone-lamport)",
"[Winternitz chains and the checksum](../../manual/chapters/07-post-quantum.md#winternitz-chains-and-the-checksum)",
"[A Merkle tree of one-time keys](../../manual/chapters/07-post-quantum.md#a-merkle-tree-of-one-time-keys)",
"[SLH-DSA (FIPS 205)](../../manual/chapters/07-post-quantum.md#slh-dsa-fips-205)", and the worked
example.

## Sources

NIST FIPS 205 (2024), SP 800-208 (2020); L. Lamport 1979; R. C. Merkle, CRYPTO 1989; A. Hülsing,
AFRICACRYPT 2013; D. J. Bernstein et al., ACM CCS 2019.
