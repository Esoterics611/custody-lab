# Threshold post-quantum signatures

**In one sentence.** No audited, standard way yet exists to produce an ML-DSA or SLH-DSA signature
from key shares the way FROST does for Schnorr, because the post-quantum schemes lack the linearity
threshold signing relies on.

## The problem

Chapter 2's threshold signing works because Schnorr's $s = k + e\,d$ is accepted unconditionally:
shares of the nonce and key give shares of $s$ that simply add. A custodian that moves to
post-quantum signatures loses that.

## The idea

- **ML-DSA.** Its response $z = y + c\,s_1$ is linear too, but the signer must reject any $z$ that
  is too large, and the test applies to the combined $z$. A share that passes locally can still
  produce a combined value that fails, so the parties must evaluate the test jointly without revealing
  $z$, and keep every rejected attempt secret. Research since 2025 produces FIPS 204-compatible
  threshold ML-DSA under restrictions: Trilithium (two parties with a helper), Quorus, and schemes for
  up to six parties (**verify current**). Threshold Raccoon is designed for thresholds but does not
  produce FIPS 204 signatures.
- **SLH-DSA.** Signing is thousands of hash evaluations on secret seeds, with no algebra to split; a
  threshold version means running SHA-256 inside a generic secure computation, at a cost many orders
  of magnitude above ordinary signing.
- **Stateful schemes** (XMSS, LMS) add a distributed-state problem: several signers must agree on
  which one-time leaf is next, and no leaf may ever be used twice.

## Why custody cares

Until a standard threshold scheme exists, the options are a post-quantum key held in one HSM under an
M-of-N administrative quorum (the Shamir model, with its single point of rebuild), on-chain
multisignature where the chain supports post-quantum scripts, or waiting for threshold ML-DSA to
mature.

## In the demo

Not implemented. The demo's post-quantum signature (ML-DSA-65 in the authorisation token) is held by
the policy engine alone.

## In the manual

[Chapter 7](../../manual/chapters/07-post-quantum.md),
"[Threshold post-quantum signatures](../../manual/chapters/07-post-quantum.md#threshold-post-quantum-signatures)",
and Exercise 6.

## Sources

R. del Pino et al., "Threshold Raccoon", EUROCRYPT 2024 (ePrint 2024/184); Trilithium (ePrint
2025/675); Quorus (ePrint 2025/1163) (**verify current**).
