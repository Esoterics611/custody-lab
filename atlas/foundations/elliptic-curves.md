# Elliptic curves

**Definition.** The solutions of $y^2 = x^3 + ax + b$ over $\mathbb{F}_p$, plus a point at infinity,
form a group under the chord-and-tangent rule. A public key is $Q = dG$ for a private scalar $d$
and a fixed generator $G$. Recovering $d$ from $Q$ is the discrete logarithm problem, about $2^{128}$
work on a 256-bit curve.

**Why custody cares.** Every key the custodian protects is a scalar on one of these curves.
secp256k1 ($y^2 = x^3 + 7$) is Bitcoin's and Ethereum's curve; Ed25519 is used by Solana and
others; P-256 is the curve most HSMs and TLS stacks support natively.

**In the demo.** Teaching code: `src/custody_lab/foundations/ec.py` (`SECP256K1`, `TOY`,
`Curve.mul`). The demo's signing path uses `frost-secp256k1-tr` (Module 2).

**In the manual.** [Chapter 1](../../manual/chapters/01-foundations.md), "[Points that can be added](../../manual/chapters/01-foundations.md#points-that-can-be-added)" (figure), "[Fields and curves](../../manual/chapters/01-foundations.md#fields-and-curves)", "[Doubling on the toy curve](../../manual/chapters/01-foundations.md#doubling-on-the-toy-curve)".

**Sources.** Certicom, *SEC 2* v2.0 (2010), section 2.4.1 for secp256k1 parameters.
