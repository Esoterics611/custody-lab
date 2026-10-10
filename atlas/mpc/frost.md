# FROST

**In one sentence.** FROST (Flexible Round-Optimized Schnorr Threshold signatures) produces an
ordinary Schnorr signature from $t$ of $n$ key shares in two rounds, with a binding factor that ties
every signer's nonce to one message and one set of commitments.

## The problem

Naive threshold Schnorr, in which each signer publishes a nonce point and then a partial signature,
is breakable when many signing sessions run at once. An attacker who controls some signers or the
coordinator sees the honest signers' nonce commitments in many sessions before fixing its own, and
that freedom of choice lets it compute a signature on a message nobody approved (the ROS attack,
made practical by Wagner's algorithm and shown to run in polynomial time).

## The idea

- **Round 1 (commit).** Each signer $i$ draws two nonces, a hiding nonce $d_i$ and a binding nonce
  $e_i$, and publishes $D_i = d_i G$ and $E_i = e_i G$. This can happen before the message exists.
- **Round 2 (sign).** For message $m$ and the list $B$ of all commitments, each signer computes a
  **binding factor** $\rho_j = H_1(P, H_4(m), H_5(B), j)$ for every signer, the group commitment
  $R = \sum_j (D_j + \rho_j E_j)$ and the challenge $c = H_2(R, P, m)$, and returns
  $z_i = d_i + e_i\rho_i + \lambda_i s_i c$.
- **Aggregate.** The coordinator outputs $(R, \sum z_i)$, an ordinary Schnorr signature.

Each signer's effective nonce is $d_i + \rho_i e_i$. Changing the message or any commitment changes
every $\rho_j$ unpredictably, so nothing can be chosen after the honest signers' commitments are
seen. $z_i$ is that nonce plus the challenge times the signer's additive key share
$\lambda_i s_i$.

## Why custody cares

- It is the simplest secure threshold signature in use: two rounds, no Paillier encryption, and
  round 1 can be precomputed, leaving one round between an authorised transaction and its signature.
- It produces Ed25519 signatures or, with the Taproot variant, BIP340 signatures that Bitcoin
  accepts.
- Nonces are single-use state: a nonce restored from backup and used again leaks the share.

## In the demo

- Signing path: `src/custody_lab/mpc/cluster.py` over `rust/custody-frost` (Zcash Foundation
  `frost-secp256k1-tr` 3.0.0, outside the NCC Group audit scope).
- Teaching code: `src/custody_lab/mpc/frost.py`, matching the RFC 9591 vectors for
  FROST(secp256k1, SHA-256) in `tests/mpc/test_frost.py`.
- The protocol tab (`custody_lab.demo.protocol`) shows both signing rounds' messages as the
  coordinator relays them: 71-byte nonce commitments, a 245-byte signing package with a 7,047-byte
  authorisation, and 32-byte signature shares ([message formats](protocol-messages.md)).

## In the manual

[Chapter 2](../../manual/chapters/02-mpc-custody.md):
"[Many sessions at once](../../manual/chapters/02-mpc-custody.md#many-sessions-at-once)" (the attack
and the binding factor), "[FROST](../../manual/chapters/02-mpc-custody.md#frost)" (each symbol named),
the worked example, and
"[FROST against RFC 9591](../../manual/chapters/02-mpc-custody.md#frost-against-rfc-9591)".

## Sources

RFC 9591; C. Komlo, I. Goldberg, SAC 2020; `github.com/ZcashFoundation/frost`.
