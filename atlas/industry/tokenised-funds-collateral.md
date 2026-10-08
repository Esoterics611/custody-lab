# Tokenised funds and collateral

**In one sentence.** Fund shares, typically of US Treasury or money market funds, recorded as tokens
that move only between allowlisted addresses, used above all as collateral that can be posted at any
hour while it keeps earning the fund's yield.

## The problem

Collateral posted as cash earns nothing, and collateral posted as securities moves only during
settlement-system hours. A token for a fund share moves at any time and keeps paying interest, but it
brings a key-custody problem to whoever receives it.

## The idea

A **money market fund** invests in short-dated, high-quality debt such as Treasury bills, so its
shares hold their value closely and pay interest. Recorded as a token, a fund share can be posted as
**margin**, collateral against a derivatives or lending position, and moved at any hour. Because only
eligible investors may hold fund shares, the token usually refuses transfers to addresses that are not
on an allowlist kept by the fund's **transfer agent**, the firm that maintains its register of
holders.

## Why custody cares

- A collateral taker (clearing house, swap dealer) must hold the token, so it needs key custody or a
  custodian, and its receiving address must be allowlisted before the margin call.
- The issuer's powers to freeze or force-transfer tokens belong in the custody policy.
- Fund tokens usually live on Ethereum-family chains: ECDSA under secp256k1, so threshold ECDSA
  rather than FROST.

## In the demo

None. Chapter 8, Exercise 5 lists what the demo would need to accept fund tokens.

## In the manual

[Chapter 8](../../manual/chapters/08-industry.md),
"[Four forms of money on a ledger](../../manual/chapters/08-industry.md#four-forms-of-money-on-a-ledger)",
"[Public and permissioned ledgers](../../manual/chapters/08-industry.md#public-and-permissioned-ledgers)",
"[Tokenised funds and collateral](../../manual/chapters/08-industry.md#tokenised-funds-and-collateral)".

## Sources

About USD 15 billion in tokenised US Treasury products, September 2026, BUIDL and USYC the largest
(reported, rwa.xyz via the press; **verify current**). CFTC staff guidance (2025 and 2026) accepting
tokenised eligible collateral with equivalent legal and economic rights (reported; **verify
current**).
