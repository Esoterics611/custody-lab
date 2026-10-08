# Threshold post-quantum signatures

**Definition.** Producing an ML-DSA or SLH-DSA signature from key shares, as FROST does for
Schnorr. The obstacles:
- ML-DSA's rejection test applies to the combined response and must be computed without
  revealing it;
- SLH-DSA signing is thousands of hash evaluations on secret seeds, with no algebra to split;
- stateful schemes need agreement on which one-time leaf is next.

**Why custody cares.** No audited, standard threshold post-quantum signature exists
(**verify current**). Until one does, a post-quantum key is held in one HSM under an M-of-N
administrative quorum, or split with on-chain multisignature where the chain supports it.

**In the demo.** Not implemented. The demo's post-quantum signature (ML-DSA-65 in the
authorisation token) is held by the policy engine alone.

**In the manual.** [Chapter 7](../../manual/chapters/07-post-quantum.md), "[Threshold post-quantum signatures](../../manual/chapters/07-post-quantum.md#threshold-post-quantum-signatures)", Exercise 6.

**Sources.** del Pino et al., "Threshold Raccoon", EUROCRYPT 2024 (ePrint 2024/184); Trilithium
(ePrint 2025/675); Quorus (ePrint 2025/1163) (**verify current**).
