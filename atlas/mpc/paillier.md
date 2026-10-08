# Paillier encryption

**In one sentence.** Paillier encryption is public-key encryption with an additive homomorphism:
anyone holding only the public key can multiply two ciphertexts to get an encryption of the sum of
their plaintexts, or raise a ciphertext to a known power $k$ to get an encryption of $k$ times its
plaintext.

## The problem

ECDSA's signing formula multiplies the nonce's inverse by the key. When two parties each hold a
piece, one of them must compute with the other's piece without seeing it.

## The idea

The public key is $N = pq$ for two large secret primes; plaintexts are numbers modulo $N$ and
ciphertexts numbers modulo $N^2$. Only the holder of $p$ and $q$ can decrypt. Encryption is
randomised, so the same value encrypts differently each time. The two homomorphic rules:

$$
\text{Enc}(a) \cdot \text{Enc}(b) = \text{Enc}(a + b), \qquad \text{Enc}(a)^k = \text{Enc}(k \cdot a) .
$$

With the manual's toy key $N = 5 \times 7 = 35$: 4 encrypts (with randomness 2) to 88 and 9 (with
randomness 3) to 712; $88 \times 712 \bmod 1225 = 181$ decrypts to 13; $88^3 \bmod 1225 = 372$
decrypts to 12; and 4 encrypted again with randomness 3 gives 1062, unrelated to 88. Paillier cannot
multiply two encrypted values together, but adding and scaling by known numbers is enough for
two-party ECDSA.

## Why custody cares

- Threshold ECDSA must combine secrets held by different parties. Paillier lets one party compute on
  another's encrypted secret; Lindell 2017 and CGGMP both depend on it.
- A malformed modulus (for example one with small factors) leaks the honest party's share over a
  number of signing sessions. Zero-knowledge proofs that $N$ is well formed are mandatory; a missing
  proof of this kind was among the weaknesses behind the 2023 BitForge disclosures.

## In the demo

Teaching code: `src/custody_lab/mpc/paillier.py` (`generate_keypair`, `PublicKey.add`,
`PublicKey.mul`), tested in `tests/mpc/test_paillier.py`. Not on the demo's signing path, which uses
Schnorr.

## In the manual

[Chapter 2](../../manual/chapters/02-mpc-custody.md):
"[Encryption that can be computed on](../../manual/chapters/02-mpc-custody.md#encryption-that-can-be-computed-on)"
(the toy key worked) and
"[Paillier encryption](../../manual/chapters/02-mpc-custody.md#paillier-encryption)".

## Sources

P. Paillier, "Public-Key Cryptosystems Based on Composite Degree Residuosity Classes", EUROCRYPT
1999.
