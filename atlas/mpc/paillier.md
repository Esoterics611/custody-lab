# Paillier encryption

**Definition.** Public-key encryption modulo $N^2$ ($N = pq$) with an additive homomorphism:
$\text{Enc}(a)\cdot\text{Enc}(b) = \text{Enc}(a+b)$ and $\text{Enc}(a)^k = \text{Enc}(ka)$, computable
with the public key alone.

**Why custody cares.**
- Threshold ECDSA must multiply secrets held by different parties. Paillier lets one party compute
  on another's encrypted secret. Lindell 2017 and CGGMP both depend on it.
- A malformed modulus (for example one with small factors) leaks shares. Proofs that $N$ is well
  formed are mandatory; their absence was among the weaknesses behind the 2023 BitForge
  disclosures.

**In the demo.** Teaching code: `src/custody_lab/mpc/paillier.py` (`generate_keypair`,
`PublicKey.add`, `PublicKey.mul`), tested in `tests/mpc/test_paillier.py`.

**In the manual.** [Chapter 2](../../manual/chapters/02-mpc-custody.md), "[Paillier encryption](../../manual/chapters/02-mpc-custody.md#paillier-encryption)".

**Sources.** P. Paillier, "Public-Key Cryptosystems Based on Composite Degree Residuosity
Classes", EUROCRYPT 1999.
