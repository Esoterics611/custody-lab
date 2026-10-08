# Finite fields

**In one sentence.** A finite field $\mathbb{F}_p$ is the numbers $0$ to $p - 1$ with addition,
subtraction, multiplication and division all done modulo a prime $p$, so every result has the same
fixed size and every division is exact.

## The problem

Keys are 256-bit numbers. Ordinary arithmetic on them would grow without limit (a product of two
78-digit numbers has 155 digits) and division would leave fractions. Cryptography needs a number
system in which results never grow and division always works.

## The idea

Arithmetic modulo $m$ keeps only the remainder after dividing by $m$, the way a 12-hour clock turns
15:00 into 3. Modulo 7: $5 + 4 = 9 \equiv 2$, $3 \times 5 = 15 \equiv 1$, and $2 - 5 = -3 \equiv 4$.

Division by $a$ means multiplying by the **inverse** $a^{-1}$, the number with
$a \times a^{-1} \equiv 1$. Modulo 7 the inverse of 3 is 5, so $6 / 3$ is computed as
$6 \times 5 = 30 \equiv 2$. In Python, `pow(a, -1, m)` computes an inverse.

The modulus must be prime. Modulo 8 the number 2 has no inverse, because $2k$ is always even and an
even number never leaves remainder 1 when divided by 8. A prime shares no factor with any smaller
number, so with a prime modulus every non-zero number can be divided by.

## Why custody cares

Every key, nonce, signature value and secret share is an element of a finite field. Two fields
appear side by side on an elliptic curve: point coordinates are numbers modulo the field prime $p$,
while scalars (keys, nonces, shares) are numbers modulo the group order $n$. Both are large numbers
of similar size, and nothing in a program's types distinguishes them, so mixing them up is a classic
implementation bug. On the manual's toy curve a point with $x = 42$ gives an ECDSA value of 11,
because $42 \bmod 31 = 11$.

## In the demo

Teaching code: `src/custody_lab/foundations/ec.py` (`Curve.add` uses inverses modulo `p`);
`ecdsa.py` and `shamir.py` work modulo `n`.

## In the manual

[Chapter 1](../../manual/chapters/01-foundations.md):
"[Arithmetic on a clock](../../manual/chapters/01-foundations.md#arithmetic-on-a-clock)" (built from
the beginning, with the inverse table modulo 7) and
"[Fields and curves](../../manual/chapters/01-foundations.md#fields-and-curves)".

## Sources

J. Song, *Programming Bitcoin* (O'Reilly, 2019), chapter 1.
