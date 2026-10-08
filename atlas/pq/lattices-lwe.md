# Lattices and learning with errors

**Definition.** Learning with errors (LWE): given many equations $b_i = a_i \cdot s + e_i \bmod q$
with random $a_i$ and small errors $e_i$, find $s$. Without the errors it is linear algebra; with
them it is believed hard for classical and quantum computers. ML-KEM and ML-DSA use the module
variant, in which $a_i$ and $s$ are vectors of polynomials.

**Why custody cares.**
- It is the assumption under the two NIST lattice standards: key encapsulation for share backups
  and transport, and ML-DSA signatures.
- Its errors are also what makes lattice signatures need rejection sampling, which in turn makes
  them hard to threshold.

**In the demo.** No code of its own; ML-KEM and ML-DSA come from `cryptography`. Chapter 7's toy
cell encrypts one bit with $q = 97$.

**In the manual.** [Chapter 7](../../manual/chapters/07-post-quantum.md), "[Lattices in one bit](../../manual/chapters/07-post-quantum.md#lattices-in-one-bit)", "[ML-KEM (FIPS 203)](../../manual/chapters/07-post-quantum.md#ml-kem-fips-203)".

**Sources.** O. Regev, STOC 2005; NIST FIPS 203 and 204 (2024).
