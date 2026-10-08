# Elliptic curves

**In one sentence.** The points satisfying $y^2 = x^3 + ax + b$ modulo a prime, plus a point at
infinity, can be added by a fixed rule; adding a generator point $G$ to itself $d$ times is fast,
while finding $d$ from the result is infeasible, and that asymmetry is a key pair.

## The problem

A key pair needs a calculation that is easy one way and infeasible the other. Multiplication on a
clock does not qualify: if $Q = d \times g \bmod p$, then $d = Q \times g^{-1}$, one multiplication
away. Something with no division shortcut is needed.

## The idea

An elliptic curve is a set of points $(x, y)$ satisfying an equation such as $y^2 = x^3 + 7$, with
the arithmetic done modulo a prime. Two points add by a geometric rule: draw the line through them,
find where it meets the curve a third time, and reflect that point across the horizontal axis. The
rule obeys the laws of ordinary addition, with an extra point at infinity $\mathcal{O}$ as zero, so
the points form a **group**.

Starting from a generator $G$ and adding it repeatedly walks a cycle through the points. On the
manual's toy curve ($p = 43$) the cycle has length $n = 31$: $G = (2, 12)$, $2G = (7, 7)$, ...,
$31G = \mathcal{O}$. A private key is a step count $d$; the public key is the point $Q = dG$ where
the walk lands. With $d = 7$, $Q = (25, 18)$.

Going forwards is fast because doubling skips ahead ($13G = 8G + 4G + G$), so a 256-bit key needs a
few hundred operations. Going backwards, recovering $d$ from $Q$, is the **discrete logarithm
problem**: no known method beats about $2^{128}$ steps on a 256-bit curve. A large quantum computer
running Shor's algorithm would solve it, which is why chapter 7 exists.

## Why custody cares

Every key a custodian protects is a step count on one of these curves. secp256k1
($y^2 = x^3 + 7$ over a 256-bit prime) is Bitcoin's and Ethereum's curve; Ed25519's curve is used by
Solana and others and by the demo's approvals; P-256 is the curve most HSMs and TLS stacks support
natively. A curve's second half mirrors its first ($(n - k)G = -(kG)$, same $x$), which is why
BIP340 can store keys as an $x$-coordinate alone and why every ECDSA signature has a mirrored twin.

## In the demo

Teaching code: `src/custody_lab/foundations/ec.py` (`SECP256K1`, `TOY`, `Curve.mul`). The demo's
signing path uses the `frost-secp256k1-tr` crate (chapter 2).

## In the manual

[Chapter 1](../../manual/chapters/01-foundations.md):
"[Points that can be added](../../manual/chapters/01-foundations.md#points-that-can-be-added)" (figure),
"[The cycle: generator, order and scalar](../../manual/chapters/01-foundations.md#the-cycle-generator-order-and-scalar)",
"[Easy forwards, infeasible backwards](../../manual/chapters/01-foundations.md#easy-forwards-infeasible-backwards)",
"[Fields and curves](../../manual/chapters/01-foundations.md#fields-and-curves)",
"[Doubling on the toy curve](../../manual/chapters/01-foundations.md#doubling-on-the-toy-curve)".

## Sources

Certicom, *SEC 2* v2.0 (2010), section 2.4.1 for the secp256k1 parameters.
