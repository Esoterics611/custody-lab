# ML-DSA (FIPS 204)

**Definition.** A module-lattice Fiat-Shamir signature. The response $z = y + c\,s_1$ has
Schnorr's shape, but the signer rejects any $z$ that is too large and tries again, because
otherwise $z$ would reveal $s_1$ (Fiat-Shamir with aborts). ML-DSA-65: 1,952-byte public key,
3,309-byte signature. Signing is randomised by default and takes an optional context string.

**Why custody cares.**
- It is the general-purpose post-quantum signature for keys the custodian controls: approvals,
  authorisations and attestations.
- The rejection step is why threshold ML-DSA is still research.

**In the demo.** `cryptography` ML-DSA-44/65/87, checked against NIST ACVP keyGen and sigVer
vectors. The policy engine's authorisation tokens carry an ML-DSA-65 signature alongside Ed25519,
and every signer requires both (`src/custody_lab/policy/authorisation.py`, `AuthorityKey`).

**In the manual.** [Chapter 7](../../manual/chapters/07-post-quantum.md), "[ML-DSA (FIPS 204)](../../manual/chapters/07-post-quantum.md#ml-dsa-fips-204)", "[The demo's hybrid authorisation](../../manual/chapters/07-post-quantum.md#the-demos-hybrid-authorisation)"; [chapter 4](../../manual/chapters/04-policy.md),
"[Authorisation](../../manual/chapters/04-policy.md#authorisation)".

**Sources.** NIST FIPS 204 (2024); V. Lyubashevsky, ASIACRYPT 2009.
