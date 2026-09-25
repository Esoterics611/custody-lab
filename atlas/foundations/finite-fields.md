# Finite fields

**Definition.** $\mathbb{F}_p$ is the integers 0 to $p-1$ with addition and multiplication modulo a
prime $p$. Every non-zero element has a multiplicative inverse (`pow(a, -1, p)` in Python), so
division is defined.

**Why custody cares.** Every key, nonce, signature value and secret share is an element of a finite
field. Two fields appear side by side: point coordinates are mod $p$, scalars (keys, nonces,
shares) are mod the group order $n$. Mixing them up is a classic implementation bug.

**In the demo.** Teaching code: `src/custody_lab/foundations/ec.py` (`Curve.add` uses modular
inverses mod `p`); `ecdsa.py` and `shamir.py` work mod `n`.

**In the manual.** Chapter 1, "Fields and curves".

**Sources.** J. Song, *Programming Bitcoin*, chapter 1.
