# Two-party ECDSA (Lindell 2017)

**Definition.** Two parties hold multiplicative shares ($Q = x_1 x_2 G$). $P_1$ gives $P_2$ an
encryption of $x_1$ under $P_1$'s Paillier key at key generation. To sign, $P_2$ homomorphically
computes an encryption of $k_2^{-1}(z + r x_1 x_2)$; $P_1$ decrypts it and removes $k_1$. The
output is standard ECDSA.

**Why custody cares.**
- It is the classic two-party custody design: client device and server, or two data centres.
- Coinbase's cb-mpc implements it, with additive shares and full proofs.
- Security needs zero-knowledge proofs of key and nonce knowledge, modulus validity and the
  encrypted key share.
- All executions with a key must halt once cheating is detected (cb-mpc theory document).

**In the demo.** Teaching code, semi-honest and with proofs omitted:
`src/custody_lab/mpc/lindell17.py` (`Party1`, `Party2`). Signatures verify with `cryptography`
in `tests/mpc/test_lindell17.py`. Not on the demo's signing path.

**In the manual.** Chapter 2, "Two-party ECDSA (Lindell 2017)", Exercise 3.

**Sources.** Y. Lindell, CRYPTO 2017 and *Journal of Cryptology* 34 (2021); cb-mpc
`docs/theory/ecdsa-2pc-theory.pdf`.
