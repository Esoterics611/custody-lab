# Shamir secret sharing

**In one sentence.** Shamir's scheme hides a secret as the starting value $f(0)$ of a random
polynomial of degree $t - 1$ and gives party $i$ the point $(i, f(i))$; any $t$ points rebuild the
secret, and fewer reveal nothing about it.

## The problem

A single copy of a key can be lost; many copies can be stolen. Splitting the key into pieces, any
$t$ of which suffice, protects against both, provided fewer than $t$ pieces say nothing.

## The idea

For 2-of-3, draw a random line through the secret: $f(x) = s + c_1 x$. Two points fix a line and one
does not. With $s = 9$ and slope 5 modulo 31, the shares are $(1, 14)$, $(2, 19)$ and $(3, 24)$. One
share is consistent with every one of the 31 possible secrets, one line each, so it reveals
nothing; any two determine the line and so the secret.

The secret is a weighted sum of any $t$ shares, $s = \sum \lambda_i f(i)$, with **Lagrange
coefficients** $\lambda_i$ that depend only on which parties take part. For parties 1 and 3 the
weights are $3/2$ and $-1/2$, which modulo 31 are 17 and 15, and
$17 \times 14 + 15 \times 24 = 598 \equiv 9$. Over ordinary numbers one share leaks a little,
because the random slope must come from a limited range; on a clock it leaks nothing.

## Why custody cares

- M-of-N quorums of smart cards in HSM key ceremonies, and SLIP-39 wallet backups, rest on this
  idea.
- Its limit is the rebuild: to sign, the shares must meet and the key exists whole in one place,
  and whoever dealt the shares saw the key at creation.
- Threshold signing (chapter 2) keeps the Lagrange weights but never rebuilds the key: each party
  multiplies its own share by its own weight. Distributed key generation removes the dealer.

## In the demo

Teaching code: `src/custody_lab/foundations/shamir.py` (`split`, `lagrange_coefficient`,
`reconstruct`). `lagrange_coefficient` is reused by the educational FROST in chapter 2.

## In the manual

[Chapter 0](../../manual/chapters/00-orientation.md),
"[Pieces of a secret: a line through two points](../../manual/chapters/00-orientation.md#pieces-of-a-secret-a-line-through-two-points)"
(with a figure); [chapter 1](../../manual/chapters/01-foundations.md),
"[Sharing a secret as a line through points](../../manual/chapters/01-foundations.md#sharing-a-secret-as-a-line-through-points)",
"[Shamir secret sharing](../../manual/chapters/01-foundations.md#shamir-secret-sharing)", the 2-of-3
worked example, and Exercise 5.

## Sources

A. Shamir, "How to Share a Secret", *CACM* 22(11), 1979; SatoshiLabs SLIP-0039.
