# Hash-based signatures

**Definition.** Signatures whose security rests only on a hash function.
- **Lamport:** reveal one of two secrets per digest bit.
- **WOTS+:** reveal a position along a hash chain per 4-bit digit, with a checksum so that no
  digit can be advanced.
- **XMSS / LMS:** a Merkle tree of one-time keys; stateful.
- **SLH-DSA (FIPS 205):** a hypertree of XMSS trees with FORS at the bottom; stateless.

**Why custody cares.**
- They survive a quantum computer as long as the hash does.
- A one-time key used twice leaks enough to forge. A stateful signer restored from backup can
  reuse a leaf.
- SLH-DSA has no state to lose, at 7,856 to 49,856 bytes per signature.

**In the demo.** Teaching code: `src/custody_lab/pq/wots.py` (WOTS+, XMSS, the SLH-DSA-SHA2-128f
public root), checked against NIST ACVP keyGen vectors in `tests/pq/test_wots.py`. Library:
RustCrypto `slh-dsa` through `rust/custody-pq`, checked in `tests/pq/test_pq_vectors.py`.

**In the manual.** Chapter 7, "Signatures from a hash alone: Lamport", "Winternitz chains and
the checksum", "A Merkle tree of one-time keys", "SLH-DSA (FIPS 205)", the worked example.

**Sources.** NIST FIPS 205 (2024), SP 800-208 (2020); Lamport 1979; Merkle, CRYPTO 1989; Hülsing,
AFRICACRYPT 2013; Bernstein et al., ACM CCS 2019.
