# ML-DSA (FIPS 204)

**In one sentence.** ML-DSA is the NIST standard lattice-based signature: a Fiat-Shamir signature
whose response $z = y + c\,s_1$ has Schnorr's shape, except that the signer throws away any response
that is too large and tries again.

## The problem

The custodian's own signatures (approvals, policy authorisations, reserves attestations) all use
schemes a quantum computer breaks, and unlike Bitcoin's signatures they are the custodian's to change.

## The idea

With a secret $s_1$ of small coefficients, the signer picks a small random $y$ (the nonce), computes
a commitment $w = Ay$, a challenge $c$ from the message and the high bits of $w$, and the response
$z = y + c\,s_1$. If $z$ is too large, or a condition on the low bits fails, the signer discards the
attempt and starts again with a new $y$. Without that rejection, the distribution of $z$ would show
traces of $s_1$, because small numbers do not hide each other the way uniformly random numbers do.
This is **Fiat-Shamir with aborts**. ML-DSA-65 has a 1,952-byte public key and a 3,309-byte
signature, about 50 times a BIP340 signature. Signing is randomised by default and takes an optional
context string that binds a signature to one use.

## Why custody cares

- It is the general-purpose post-quantum signature for keys the custodian controls.
- The rejection step is why threshold ML-DSA is still research: the test applies to the combined
  response, which no signer may see.

## In the demo

`cryptography` ML-DSA-44/65/87, checked against NIST ACVP keyGen and sigVer vectors. The policy
engine's authorisation tokens carry an ML-DSA-65 signature, with the context string
`custody-lab/authorisation`, alongside Ed25519, and every signer requires both
(`src/custody_lab/policy/authorisation.py`, `AuthorityKey`).

## In the manual

[Chapter 7](../../manual/chapters/07-post-quantum.md),
"[ML-DSA (FIPS 204)](../../manual/chapters/07-post-quantum.md#ml-dsa-fips-204)",
"[The demo's hybrid authorisation](../../manual/chapters/07-post-quantum.md#the-demos-hybrid-authorisation)";
[chapter 4](../../manual/chapters/04-policy.md),
"[Authorisation](../../manual/chapters/04-policy.md#authorisation)".

## Sources

NIST FIPS 204 (2024); V. Lyubashevsky, ASIACRYPT 2009.
