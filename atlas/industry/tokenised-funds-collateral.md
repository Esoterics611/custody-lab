# Tokenised funds and collateral

**Definition.** Fund shares, typically of US Treasury or money market funds, recorded as tokens
on a ledger and transferable only between addresses on the transfer agent's allowlist. Their main
institutional use is as collateral: posted as margin at any hour while still earning the fund's
yield.

**Why custody cares.**
- A collateral taker (clearing house, swap dealer) must hold the token, so it needs key custody
  or a custodian, and its receiving address must be allowlisted before the margin call.
- The issuer's powers to freeze or force-transfer tokens belong in the custody policy.
- Fund tokens usually live on Ethereum-family chains: ECDSA under secp256k1, so threshold ECDSA
  rather than FROST.

**In the demo.** None. Chapter 8, Exercise 5 lists what the demo would need to accept fund tokens.

**In the manual.** Chapter 8, "Four forms of money on a ledger", "Public and permissioned
ledgers", "Tokenised funds and collateral".

**Sources.** About USD 15 billion in tokenised US Treasury products, September 2026, BUIDL and
USYC the largest (reported, rwa.xyz via the press; **verify current**). CFTC staff guidance
(2025 and 2026) accepting tokenised eligible collateral with equivalent legal and economic rights
(reported; **verify current**).
