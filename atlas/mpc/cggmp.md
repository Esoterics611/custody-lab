# CGGMP threshold ECDSA

**Definition.** Canetti, Gennaro, Goldfeder, Makriyannis and Peled (CCS 2020): $t$-of-$n$ ECDSA with
UC security, identifiable abort, proactive refresh, and presigning that leaves one online round.
It relies on Paillier and a set of zero-knowledge proofs; an auxiliary-information phase
generates safe primes.

**Why custody cares.**
- It is the reference protocol for multi-party ECDSA custody (Ethereum, Bitcoin SegWit v0).
- Identifiable abort lets an operator remove a misbehaving node rather than just retry.
- Presignatures are single-use secrets that must never be restored from backup.

**In the demo.** Not implemented. Chapter 2 shows an abridged `cggmp21` (Rust, LFDT-Lockness)
listing. The crate's README reports a Kudelski audit; it lacks key refresh and identifiable abort
(**verify current**).

**In the manual.** [Chapter 2](../../manual/chapters/02-mpc-custody.md), "[CGGMP](../../manual/chapters/02-mpc-custody.md#cggmp)" and "[Production ECDSA libraries (listings, not executed)](../../manual/chapters/02-mpc-custody.md#production-ecdsa-libraries-listings-not-executed)".

**Sources.** IACR ePrint 2021/060; `github.com/LFDT-Lockness/cggmp21`.
