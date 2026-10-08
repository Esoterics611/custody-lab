# ECDSA

**In one sentence.** ECDSA signs a digest $z$ with a private key $d$ by picking a secret nonce $k$
and computing $r$ from the point $kG$ and $s = k^{-1}(z + rd) \bmod n$; anyone with the public key
can check the pair $(r, s)$.

## The problem

A signature must prove that the holder of $d$ approved one exact message without revealing $d$.
ECDSA is the scheme most blockchains settled on first, so most custody signing is ECDSA.

## The idea

To sign:

1. pick a fresh secret nonce $k$ and compute the point $R = kG$;
2. keep its $x$-coordinate, reduced modulo the group order $n$, as $r$;
3. compute $s = k^{-1}(z + rd) \bmod n$.

To verify $(r, s)$ against $Q = dG$: compute $u_1 = z s^{-1}$ and $u_2 = r s^{-1}$, then
$X = u_1 G + u_2 Q$. This lands on $R$, because
$X = s^{-1}(z + rd)G = kG$, so the check is $x_X \bmod n = r$.

On the manual's toy curve, with $d = 7$, $z = 17$ and $k = 10$: $R = 10G = (42, 7)$, $r = 42 \bmod 31 =
11$, $s = 28$, which the low-S rule turns into $31 - 28 = 3$. The signature is $(11, 3)$, and the
verifier reaches $X = (42, 36)$, the mirror of $R$, with the same $x$.

**Two forms.** $(r, s)$ and $(r, n - s)$ both verify, because negating $s$ is the same as negating
$k$, which reflects $R$, and a reflection keeps $x$. Anyone can therefore turn one valid signature
into another without the key. Bitcoin Core relays only the low-S form (BIP 146).

**Nonce reuse.** Two signatures with one $k$ share $r$ and give two equations in the unknowns $k$
and $d$, which school algebra solves. Partly predictable nonces also leak the key, through lattice
methods across many signatures.

## Why custody cares

- ECDSA is what Bitcoin's legacy and SegWit v0 outputs and Ethereum accept.
- Reused or biased nonces have lost real coins, so nonce generation (RFC 6979 deterministic nonces,
  or hashed nonces) is a custody control, not a detail.
- $s$ multiplies one secret by the inverse of another ($k^{-1}$ times $d$). Splitting that across
  parties needs Paillier encryption or oblivious transfer (Lindell 2017, CGGMP), which is why
  threshold ECDSA is much heavier than threshold Schnorr.

## In the demo

Teaching code: `src/custody_lab/foundations/ecdsa.py` (`sign`, `verify`), checked against the
`cryptography` library in `tests/foundations/test_ecdsa.py`. Two-party ECDSA is
`src/custody_lab/mpc/lindell17.py` (chapter 2). The demo itself signs with Schnorr.

## In the manual

[Chapter 1](../../manual/chapters/01-foundations.md):
"[ECDSA](../../manual/chapters/01-foundations.md#ecdsa)" (with the verification derived and the
low-S rule explained), the toy-curve worked example, and Exercise 3 (key recovery from a reused
nonce).

## Sources

Certicom, *SEC 1* v2.0 (2009); NIST FIPS 186-5; RFC 6979 (deterministic nonces); BIP 146 (low-S).
