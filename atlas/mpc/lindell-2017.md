# Two-party ECDSA (Lindell 2017)

**In one sentence.** In Lindell's two-party ECDSA, two parties hold multiplicative key shares
($Q = x_1 x_2 G$), and one computes on the other's Paillier-encrypted share so that together they
produce a standard ECDSA signature without either seeing the other's secret.

## The problem

ECDSA is what Ethereum and Bitcoin's older outputs accept, and its formula
$s = k^{-1}(z + rd)$ multiplies secrets, so the additive trick that splits Schnorr does not apply.

## The idea

At key generation $P_1$ creates a Paillier key pair and sends $P_2$ an encryption of its key share,
$c_{\text{key}} = \text{Enc}(x_1)$. To sign a digest $z$:

1. $P_1$ picks a nonce piece $k_1$ and sends $R_1 = k_1 G$; $P_2$ picks $k_2$ and computes
   $R = k_2 R_1$ and $r$ from it. Neither knows the full nonce $k = k_1 k_2$.
2. $P_2$ computes on encrypted data. Raising $c_{\text{key}}$ to the power $k_2^{-1} r x_2$ gives an
   encryption of $k_2^{-1} r x_1 x_2$; multiplying by an encryption of $k_2^{-1} z$ (plus a random
   multiple of the group order $q$, which hides the size of the number) adds the digest term.
3. $P_1$ decrypts, reduces modulo $q$ to get $k_2^{-1}(z + r x_1 x_2)$, and divides by $k_1$. The
   result is $k^{-1}(z + rd)$ with $d = x_1 x_2$: an ordinary ECDSA signature.

$P_2$ never sees $x_1$; $P_1$ never sees $x_2$ or $k_2$. Against a cheating party the protocol needs
zero-knowledge proofs: of knowledge of the key and nonce pieces, that $N$ is a valid Paillier
modulus, and that $c_{\text{key}}$ encrypts the discrete logarithm of $P_1$'s public share.

## Why custody cares

- It is the classic two-party custody design: a client device and a server, or two data centres.
- Coinbase's cb-mpc implements it, with additive shares and the full proofs.
- Every execution with a key must halt once cheating is detected (cb-mpc theory document), because
  an attacker allowed to retry learns a little from each failure. An operator runbook needs a
  "freeze key" action, not a retry loop.

## In the demo

Teaching code, secure only against parties that follow the protocol, with the proofs omitted:
`src/custody_lab/mpc/lindell17.py` (`Party1`, `Party2`). Its signatures verify with `cryptography`
in `tests/mpc/test_lindell17.py`. Not on the demo's signing path.

## In the manual

[Chapter 2](../../manual/chapters/02-mpc-custody.md):
"[Two-party ECDSA (Lindell 2017)](../../manual/chapters/02-mpc-custody.md#two-party-ecdsa-lindell-2017)"
(walked step by step), "[Two-party ECDSA](../../manual/chapters/02-mpc-custody.md#two-party-ecdsa)"
(the code), and Exercise 3.

## Sources

Y. Lindell, CRYPTO 2017 and *Journal of Cryptology* 34 (2021); cb-mpc
`docs/theory/ecdsa-2pc-theory.pdf`.
