# Lattices and learning with errors

**In one sentence.** Learning with errors (LWE) hides a secret list of numbers $s$ behind many
equations $b_i = a_i \cdot s + e_i \bmod q$ with small random errors $e_i$; without the errors $s$
falls out of school elimination, with them recovering $s$ is believed hard even for quantum computers.

## The problem

Post-quantum schemes need a problem that quantum algorithms do not solve efficiently and that also
supports encryption and compact signatures, which hash functions alone do not.

## The idea

Each published equation is a random combination of the secret's entries plus a small error such as
$-1$, $0$ or $1$. Elimination, which solves exact simultaneous equations, amplifies the errors until
the answer is noise.

Encryption follows. To encrypt a bit, add up a random subset of the published equations and add half
the modulus if the bit is 1. The holder of $s$ subtracts $s$'s contribution and is left with the
bit's offset plus a sum of small errors: near 0 means 0, near $q/2$ means 1. The manual's toy uses
$q = 97$, a secret of length 4 and eight equations; every one of the 512 (bit, subset) pairs
decrypts correctly, because the error sum (at most 8) stays inside the $q/4 = 24$ margin.

ML-KEM and ML-DSA use **module-LWE**: the numbers become polynomials and the lists short vectors of
polynomials, which makes keys smaller for the same security.

## Why custody cares

- It is the assumption under the two NIST lattice standards: key encapsulation (ML-KEM) for share
  backups and transport, and ML-DSA signatures.
- The errors are also what make lattice signatures need rejection sampling, which in turn makes them
  hard to produce with a threshold of signers.

## In the demo

No code of its own; ML-KEM and ML-DSA come from `cryptography`. Chapter 7's toy cell encrypts one
bit with $q = 97$.

## In the manual

[Chapter 7](../../manual/chapters/07-post-quantum.md),
"[Lattices in one bit](../../manual/chapters/07-post-quantum.md#lattices-in-one-bit)",
"[ML-KEM (FIPS 203)](../../manual/chapters/07-post-quantum.md#ml-kem-fips-203)".

## Sources

O. Regev, STOC 2005; NIST FIPS 203 and 204 (2024).
