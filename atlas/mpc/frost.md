# FROST

**Definition.** Flexible Round-Optimized Schnorr Threshold signatures (Komlo and Goldberg 2020;
RFC 9591).
- Round 1: each signer commits to a hiding and a binding nonce.
- Round 2: each signer returns $z_i = d_i + e_i\rho_i + \lambda_i s_i c$.
- Per-signer binding factors $\rho_i$ tie the nonces to the message and the signer set.
- The sum of the $z_i$ is an ordinary Schnorr signature.

**Why custody cares.**
- It is the simplest secure threshold signature: two rounds, no Paillier, and round 1 can be
  precomputed.
- It produces Ed25519 or, with the Taproot variant, BIP340 signatures.
- The binding factor defeats concurrent-session (ROS / Wagner) attacks on naive threshold
  Schnorr.

**In the demo.**
- Signing path: `src/custody_lab/mpc/cluster.py` over `rust/custody-frost` (ZF
  `frost-secp256k1-tr` 3.0.0, outside the NCC audit scope).
- Teaching code: `src/custody_lab/mpc/frost.py`, matching the RFC 9591 vectors for
  FROST(secp256k1, SHA-256) in `tests/mpc/test_frost.py`.

**In the manual.** [Chapter 2](../../manual/chapters/02-mpc-custody.md), "[FROST](../../manual/chapters/02-mpc-custody.md#frost)", the worked example, and the code walkthrough.

**Sources.** RFC 9591; C. Komlo, I. Goldberg, SAC 2020; `github.com/ZcashFoundation/frost`.
