# CGGMP threshold ECDSA

**In one sentence.** CGGMP (Canetti, Gennaro, Goldfeder, Makriyannis and Peled, CCS 2020) is
$t$-of-$n$ threshold ECDSA that stays secure with many concurrent sessions, names a party that
cheats, refreshes its shares, and does most of its work before the message is known.

## The problem

Lindell 2017 covers two parties. A custodian signing ECDSA (for Ethereum, or Bitcoin's older outputs)
with a larger quorum needs a multi-party protocol, and in operation it needs more than a security
proof for one session in isolation.

## The idea

Four properties set CGGMP apart:

- **UC security**: the proof still holds when many sessions run at once, which a custodian's signers
  always do.
- **Identifiable abort**: when a party cheats, the protocol names it, so operators can remove that
  signer and continue instead of only retrying.
- **Proactive refresh**: shares can be renewed without changing the key.
- **Presigning**: most of the computation happens before the message is known, leaving one round
  once it arrives.

The cost is heavy zero-knowledge machinery over Paillier encryption, including an
auxiliary-information phase that generates safe primes (primes $p$ for which $(p - 1)/2$ is also
prime).

## Why custody cares

- It is the reference protocol for multi-party ECDSA custody.
- Identifiable abort turns a cheating signer from an outage into an exclusion.
- Presignatures are single-use secrets, like nonces: one restored from backup and used again leaks
  the key.
- Its implementations carry the history chapter 2 records: the 2023 BitForge and TSShock disclosures
  affected implementations of the earlier GG18/GG20 protocols whose proofs were missing or weak.

## In the demo

Not implemented. Chapter 2 shows an abridged `cggmp21` (Rust, LFDT-Lockness) listing. The crate's
README reports a Kudelski audit; it lacks key refresh and identifiable abort (**verify current**).

## In the manual

[Chapter 2](../../manual/chapters/02-mpc-custody.md),
"[CGGMP](../../manual/chapters/02-mpc-custody.md#cggmp)" and
"[Production ECDSA libraries (listings, not executed)](../../manual/chapters/02-mpc-custody.md#production-ecdsa-libraries-listings-not-executed)".

## Sources

IACR ePrint 2021/060; `github.com/LFDT-Lockness/cggmp21`.
