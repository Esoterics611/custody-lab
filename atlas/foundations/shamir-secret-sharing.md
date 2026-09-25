# Shamir secret sharing

**Definition.** Hide secret $s$ as $f(0)$ of a random polynomial of degree $t-1$; share $i$ is
$(i, f(i))$. Any $t$ shares rebuild $s = \sum \lambda_i f(i)$ by Lagrange interpolation; $t-1$
shares are consistent with every possible secret.

**Why custody cares.**
- M-of-N quorums in HSM key ceremonies and SLIP-39 wallet backups rest on this idea.
- Its limit is the rebuild: to sign, the key must exist whole in one place, and the dealer saw
  it at creation.
- Threshold signing (Module 2) keeps the Lagrange coefficients but never rebuilds the key; DKG
  removes the dealer.

**In the demo.** Teaching code: `src/custody_lab/foundations/shamir.py` (`split`,
`lagrange_coefficient`, `reconstruct`). `lagrange_coefficient` is reused by the educational FROST in
Module 2.

**In the manual.** Chapter 1, "Shamir secret sharing", the 2-of-3 worked example, Exercise 5.

**Sources.** A. Shamir, "How to Share a Secret", *CACM* 22(11), 1979; SatoshiLabs SLIP-0039.
