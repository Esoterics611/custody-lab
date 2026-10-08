# Atlas

The atlas is the knowledge base: one concept per file, each readable on its own. The manual
chapters teach in order; the atlas is where a concept is looked up later. An entry lives at
`atlas/<area>/<slug>.md` and has seven parts:

1. **In one sentence** — the concept, stated so that it can be used without reading further.
2. **The problem** — what goes wrong for a custodian without it.
3. **The idea** — how it works, in plain words, with the manual's small worked numbers.
4. **Why custody cares** — the failure it prevents or the property it buys, and its limits.
5. **In the demo** — the file and function where it runs, or that it is not built.
6. **In the manual** — links to the chapter sections that teach it.
7. **Sources** — primary references; time-sensitive facts marked **verify current**.

Status: `planned` → `draft` → `reviewed`.

[Glossary](glossary.md): every term the manual defines, explained in two to four sentences, with
links to the sections that teach it.

## Project

| Entry | Status |
|-------|--------|
| [Build plan](project/build-plan.md) | draft |
| [Threshold signing: cb-mpc feasibility and recommended path](project/threshold-signing-feasibility.md) | draft |
| [Session log](project/session-log.md) | current |

## [1. Foundations](../manual/chapters/01-foundations.md)

| Entry | Status |
|-------|--------|
| [`foundations/finite-fields.md`](foundations/finite-fields.md) — modular arithmetic, inverses | draft |
| [`foundations/elliptic-curves.md`](foundations/elliptic-curves.md) — group law, scalar multiplication, secp256k1, Ed25519 | draft |
| [`foundations/hash-functions.md`](foundations/hash-functions.md) — SHA-256, tagged hashes, Fiat-Shamir | draft |
| [`foundations/ecdsa.md`](foundations/ecdsa.md) — signing, nonce reuse, malleability | draft |
| [`foundations/schnorr-bip340.md`](foundations/schnorr-bip340.md) — Schnorr, BIP340, EdDSA | draft |
| [`foundations/shamir-secret-sharing.md`](foundations/shamir-secret-sharing.md) — polynomials, Lagrange interpolation | draft |

## [2. MPC custody](../manual/chapters/02-mpc-custody.md)

| Entry | Status |
|-------|--------|
| [`mpc/threshold-signatures.md`](mpc/threshold-signatures.md) — t-of-n, MPC vs multisig | draft |
| [`mpc/paillier.md`](mpc/paillier.md) — additively homomorphic encryption | draft |
| [`mpc/lindell-2017.md`](mpc/lindell-2017.md) — two-party ECDSA | draft |
| [`mpc/cggmp.md`](mpc/cggmp.md) — multi-party threshold ECDSA | draft |
| [`mpc/frost.md`](mpc/frost.md) — RFC 9591 threshold Schnorr | draft |
| [`mpc/dkg.md`](mpc/dkg.md) — Pedersen DKG, no trusted dealer | draft |
| [`mpc/proactive-refresh.md`](mpc/proactive-refresh.md) — same key, new shares | draft |
| [`mpc/backup-recovery.md`](mpc/backup-recovery.md) — verifiable backup, recovery ceremonies | draft |

## [3. Key storage](../manual/chapters/03-key-storage.md)

| Entry | Status |
|-------|--------|
| [`storage/hsm.md`](storage/hsm.md) — FIPS 140-3 levels, PKCS#11, key wrapping | draft |
| [`storage/tee.md`](storage/tee.md) — SGX, confidential VMs, AWS Nitro Enclaves, attestation | draft |
| [`storage/hsm-vs-mpc-vs-tee.md`](storage/hsm-vs-mpc-vs-tee.md) — comparison table | draft |

## [4. Policy and authorisation](../manual/chapters/04-policy.md)

| Entry | Status |
|-------|--------|
| [`policy/default-deny.md`](policy/default-deny.md) | draft |
| [`policy/quorum-approvals.md`](policy/quorum-approvals.md) — approval quorum vs signing quorum | draft |
| [`policy/whitelists.md`](policy/whitelists.md) | draft |
| [`policy/velocity-limits.md`](policy/velocity-limits.md) | draft |
| [`policy/audit-trail.md`](policy/audit-trail.md) — hash-chained logs | draft |

## [5. Trading to settlement](../manual/chapters/05-settlement.md)

| Entry | Status |
|-------|--------|
| [`settlement/fix-to-settlement.md`](settlement/fix-to-settlement.md) — FIX 5.0 SP2 ExecutionReport to settlement instruction | draft |
| [`settlement/off-exchange-settlement.md`](settlement/off-exchange-settlement.md) — ClearLoop-style model | draft |
| [`settlement/netting.md`](settlement/netting.md) | draft |
| [`settlement/bitcoin-regtest-taproot.md`](settlement/bitcoin-regtest-taproot.md) — key-path spend, BIP341 sighash | draft |

## [6. Proof of reserves](../manual/chapters/06-reserves.md)

| Entry | Status |
|-------|--------|
| [`reserves/merkle-sum-tree.md`](reserves/merkle-sum-tree.md) — hash tree with committed sums | draft |
| [`reserves/inclusion-proofs.md`](reserves/inclusion-proofs.md) — one sibling per level | draft |
| [`reserves/proof-of-control.md`](reserves/proof-of-control.md) — signing under the custody key | draft |
| [`reserves/zk-proof-of-liabilities.md`](reserves/zk-proof-of-liabilities.md) — hidden sums, range proofs | draft |

## [7. Post-quantum](../manual/chapters/07-post-quantum.md)

| Entry | Status |
|-------|--------|
| [`pq/lattices-lwe.md`](pq/lattices-lwe.md) — learning with errors | draft |
| [`pq/ml-kem.md`](pq/ml-kem.md) — FIPS 203 | draft |
| [`pq/ml-dsa.md`](pq/ml-dsa.md) — FIPS 204 | draft |
| [`pq/hash-based-signatures.md`](pq/hash-based-signatures.md) — Lamport, WOTS+, XMSS, SLH-DSA (FIPS 205) | draft |
| [`pq/threshold-pq.md`](pq/threshold-pq.md) — why PQ schemes resist MPC | draft |
| [`pq/migration-design.md`](pq/migration-design.md) | draft |

## [8. Industry and regulation](../manual/chapters/08-industry.md)

| Entry | Status |
|-------|--------|
| [`industry/tokenised-funds-collateral.md`](industry/tokenised-funds-collateral.md) | draft |
| [`industry/canton-kinexys.md`](industry/canton-kinexys.md) | draft |
| [`industry/wholesale-cbdc.md`](industry/wholesale-cbdc.md) — Agorá, mBridge | draft |
| [`industry/mica.md`](industry/mica.md) — Article 75 custody duties | draft |
| [`industry/qualified-custodian-soc2.md`](industry/qualified-custodian-soc2.md) | draft |
| [`industry/israeli-landscape.md`](industry/israeli-landscape.md) — public sector, companies and researchers | draft |

## [9. Capstone](../manual/chapters/09-capstone.md)

| Entry | Status |
|-------|--------|
| [`capstone/system-design.md`](capstone/system-design.md) — architecture, failure modes, trade-offs | draft |
