# Custody landscape, October 2026: research notes for custody-lab

Compiled 2026-10-09. Input for the manual and `atlas/`; not itself manual text.

## How to read these notes

Every fact carries a source tag `[S#]` that resolves in the source list at the end. All sources were read on 2026-10-09.

Evidence classes:

| Class | Meaning |
|-------|---------|
| **observed** | A command or API call was run in this session and its output read (market data, GitHub, crates.io, BIP files). |
| **reported** | The cited source states it. The source list marks which pages were read directly (`direct`) and which were read through a search-engine summary of the page (`summary`). A `summary` fact is one step further from the page and should be re-read before it goes into the manual. |
| **unverified** | General knowledge with no source found in this session. Do not put in the manual without a source. |

**verify current** marks anything that changes over time: prices, rankings, licences, charters, company status, protocol status.

Scope relative to chapter 8 (`manual/chapters/08-industry.qmd`): chapter 8 already covers DvP, tokenised funds, Canton and Kinexys, wholesale CBDC, MiCA, US qualified custody and SOC reports in general, and Israel. These notes add what chapter 8 does not have: a custodian-by-custodian survey, an asset-by-asset signing table, the 2022-2026 research frontier, and an incident list with lessons.

---

## 1. Institutional custodians and how each protects keys

### 1.1 The US charter wave (context for every US entry below)

- On 2025-12-12 the OCC conditionally approved five national trust bank charters: two new charters (First National Digital Currency Bank, which is Circle's; Ripple National Trust Bank) and three conversions from state trust companies (BitGo Bank & Trust, N.A.; Fidelity Digital Assets, N.A.; Paxos Trust Company, N.A.). The release says "Subject to meeting the OCC's conditions" they join about 60 other national trust banks. Reported [S19, direct]. **verify current**
- A national trust charter does not allow deposit-taking or FDIC insurance. Reported [S42, summary].
- Coinbase received OCC conditional approval for a national trust company charter on 2026-04-02; Coinbase stated it "will not be taking retail deposits". Reported [S6, direct]. Final approval: not found. **verify current**
- The OCC conditionally approved Anchorage's conversion to Anchorage Digital Bank N.A. on 2021-01-13 [S14, summary]; a 2026-10-05 SEC filing names "Anchorage Digital Bank N.A." as custodian [S12, direct]. The OCC's 2022 BSA/AML consent order against it was terminated on 2025-08-21. Reported [S15, summary]. **verify current**

Custody lesson for the manual: a "qualified custodian" in the US is now increasingly a federally chartered trust bank, which matters for chapter 8's US section; the charter governs who may hold the keys, not how the keys are protected.

### 1.2 Coinbase (Coinbase Custody Trust Company, Coinbase Prime)

| Item | Finding | Evidence |
|------|---------|----------|
| Entity and regulator | Coinbase Custody Trust Company, LLC (CCTC) "operates as a New York State-chartered limited purpose trust company", supervised by NYDFS. | reported [S3, direct] **verify current** |
| Federal charter | OCC conditional approval for a national trust company, 2026-04-02 (see 1.1). | reported [S6, direct] **verify current** |
| Hot/cold split | Coinbase "generally seek[s] to hold no more than 2% of assets under custody in hot wallets at any given time". | reported [S3, direct] |
| Key protection | "Wallet private keys are never stored in plaintext format in any location." "The cryptographic consensus of multiple human approvers is required to decrypt a private key for both hot and cold wallets." "No single individual can control or operate Coinbase's wallet private keys." Cold key material is held "at facilities within the United States and internationally"; release of cold-wallet funds sits with "a geographically distributed team". CCTC assets are "held separately in dedicated addresses and managed using a proprietary combination of software and hardware security modules". | reported [S3, direct] |
| MPC | Coinbase acquired Unbound Security, a Tel Aviv MPC firm, in 2021 [S7, summary]. In March 2025 it open-sourced **cb-mpc**, which it says derives from its production MPC library [S5, summary]. The part of the FY2025 10-K read for these notes does not say that CCTC cold custody uses MPC; the 10-K describes encrypted keys, multi-approver decryption and HSMs. Whether CCTC signs with MPC: not established. | reported / gap |
| cb-mpc | MIT licence; C++17; components listed: EC-DKG, ECDSA-2PC, ECDSA-MPC, MPC-friendly derivation, OT and OT extension, publicly verifiable encryption (PVE), Schnorr, threshold encryption (TDH2). README: not a hosted service, no networking stack, no peer authentication or storage; not thread-safe; no third-party audit named in the README. Last push 2026-10-05. Already covered in `atlas/project/threshold-signing-feasibility.md` as reading material. | observed [S4] |
| Developer wallets | CDP server wallets run in AWS Nitro Enclaves: "no persistent storage, no interactive access, and no external networking"; keys are decrypted and used only inside the enclave. | reported [S8, summary] |
| ETF role | Coinbase is primary custodian for BlackRock's IBIT and ETHA; an 8-K of 2025-04-07 added Anchorage Digital as a standby second custodian with no current plan to move assets [S9, summary]. Bitwise estimate: Coinbase custodies 9 of 11 US spot bitcoin ETFs and 8 of 9 ether ETFs [S10, summary, secondary]; a separate April 2026 estimate puts Coinbase at 81-84% of about $92 bn in US spot bitcoin ETF assets [S11, summary, secondary]. | reported **verify current** |
| ETF liability terms | In the Grayscale CoinDesk Crypto 5 ETF prospectus supplement of 2026-10-05, Coinbase Custody's maximum liability per cold storage address is capped at a "Cold Storage Threshold" of $100 million. | reported [S12, direct] **verify current** |
| Insurance | Coinbase Global's $320 million commercial crime insurance is cited in a Bitwise ETF supplement. | reported [S12b, summary, secondary] **verify current** |
| SOC reports | SOC 1 Type II and SOC 2 Type II are claimed by secondary sources only. | unverified |
| Incidents | May 2025: overseas support-vendor staff were bribed to copy customer data (under 1% of monthly transacting users); Coinbase said no passwords, keys or funds were accessed; SEC-filed remediation estimate $180-400 million; Coinbase refused a $20 million ransom [S13, summary]. 2023: Coinbase WaaS was among the BitForge-affected implementations and had fixed the issue before disclosure [S100, summary]. | reported |

### 1.3 Anchorage Digital

| Item | Finding | Evidence |
|------|---------|----------|
| Entities | Anchorage Digital Bank N.A. (OCC); Anchorage Digital New York (BitLicense); Anchorage Digital Singapore (MAS Major Payment Institution licence, after in-principle approval in August 2024). | reported [S14, S18, summary] **verify current** |
| Key protection | Keys are "generated and processed in air-gapped HSMs" and never leave the HSM boundary in plaintext; HSMs are "air-gapped and housed in protected data centers"; physical tampering "destroy[s] the keys rather than reveal[s] them". Custom HSM logic "verifies that each operation has a valid quorum of client approvals as well as Anchorage Digital approval". Each approver's identity key is "created and stored in the iOS Secure Enclave" and unlocked by Face ID; no passwords, email or SMS. The page does not mention MPC. | reported [S16, direct] |
| Discrepancy to note | The 2026-10-05 Grayscale prospectus supplement says, of Anchorage as additional custodian: "Multiple private key shards held by the Additional Custodian must be combined to reconstitute the private key". Anchorage's own documentation describes keys that stay inside HSMs. The two descriptions are not reconciled by either source. | reported [S12, S16, direct] |
| Assurance | SOC 2 Type 2 attestations since 2021 (Anchorage's own statement). | reported [S17, summary] |
| ETF role | Standby custodian for IBIT and ETHA (April 2025) [S9]; additional custodian for the Grayscale CoinDesk Crypto 5 ETF under an agreement dated 2026-09-29 [S12, direct]. | reported **verify current** |
| Incidents | None found. The 2022 consent order (AML programme, not key security) was terminated 2025-08-21 [S15]. | reported |

### 1.4 BitGo

| Item | Finding | Evidence |
|------|---------|----------|
| Charter | BitGo Bank & Trust, N.A.: OCC conversion approval 2025-12-12 [S19, direct]; BitGo says it met the conditions and operates as an N.A. [S20, summary]. | reported **verify current** |
| Listing | NYSE: BTGO; IPO priced at $18.00 on 2026-01-21, trading from 2026-01-22. | reported [S21, summary] |
| EU | MiCA licence from BaFin for BitGo Europe GmbH, announced 2025-05-12. | reported [S26, summary] **verify current** |
| Key technology | S-1: "self-custody solutions built upon patented multi-sig and multiple-party computation ("MPC") wallet technology" [S22, summary]. Multisig wallets: three complete keys (user, backup, BitGo), backup optionally held by a Key Recovery Service. MPC/TSS wallets: three key shares (user, backup, BitGo); the backup share cannot be held by a KRS; the curve decides the algorithm; "MPCv1" for EdDSA and "MPCv2" for ECDSA; cold MPC signing needs a multi-round ceremony through BitGo's Offline Vault Console [S23, direct and summary]. Silence Laboratories states BitGo runs its Silent Shard libraries, built on DKLs23, in hot and cold custody wallets [S24, direct, vendor claim]. | reported |
| Assurance | SOC 2 Type 2, renewed annually (BitGo's statement). | reported [S25, summary] |
| Incident | "Zero Proof", disclosed by Fireblocks in early 2023: BitGo's ECDSA TSS omitted mandatory zero-knowledge proofs, so a party could recover the full private key from one signature. Reported to BitGo 2022-12-05; BitGo suspended the service 2022-12-10 and required client updates by 2023-03-17. BitGo said the wallet type was early-access and available to 20 developers. The two firms compete, so Fireblocks' severity framing is its own. | reported [S27, summary] |

### 1.5 Fireblocks

| Item | Finding | Evidence |
|------|---------|----------|
| Protocol | MPC-CMP, "developed by the Fireblocks cryptography team in 2020", described as open-source and peer-reviewed. Fireblocks' Nikolaos Makriyannis is a co-author of CGGMP21 (section 3.1). | reported [S28, direct]; [S69] |
| Key protection | "MPC-CMP key shares are implemented across multiple Trusted Execution Environments (Intel SGX)"; "At no point does Fireblocks have enough key shares to unilaterally sign a transaction". Shares are distributed across multiple cloud environments [S29, summary]. Supports one share held offline in an air-gapped device for cold signing [S29, summary]. | reported [S28, direct] |
| Code | `fireblocks/mpc-lib`: GPL-3.0, last push 2026-07-30. Open-source key recovery tool for recovering MPC keys outside Fireblocks. | observed [S30]; reported [S28] |
| Regulated entity | Fireblocks Trust Company, LLC: NYDFS limited purpose trust charter (reported August 2024). | reported [S31, summary] **verify current** |
| Research output | BitForge (2023) and Zero Proof (2022-23) disclosures; ePrint 2023/1234 (section 3.11). | reported [S100, S101] |
| Vendor claims to treat as such | Round counts ("1 round" for MPC-CMP vs 9 for GG18) and "8x faster" come from Fireblocks marketing. | reported [S29, summary] |

### 1.6 Copper

| Item | Finding | Evidence |
|------|---------|----------|
| Key technology | MPC with key shards; secondary sources describe a 2-of-3 quorum and no assembled private key. | reported [S32, summary, partly secondary] |
| Settlement network | ClearLoop: connects derivatives venues and participants with real-time visibility of pledged margin and automated margin movements; Coinbase International Exchange and Bitmart added in Q3 2025. | reported [S32, summary] |
| Entities | Copper Markets (Switzerland) AG (VQF), Copper Markets (Liechtenstein) AG (TVTG), Copper Securities (ME) (Abu Dhabi FSRA), Copper Markets U.S. (SEC broker-dealer, FINRA). UK FCA status not confirmed. | reported [S32, summary] **verify current** |
| Ownership | A May 2026 report of a sale exploration appears only in a low-confidence aggregator. | unverified |

### 1.7 Fidelity Digital Assets

| Item | Finding | Evidence |
|------|---------|----------|
| Charter | "Fidelity Digital Assets, National Association was granted a national trust bank charter by the OCC in 2025" (Fidelity's wording; the OCC release of 2025-12-12 calls it conditional). UK: Fidelity Digital Assets, Ltd. registered with the FCA. | reported [S33, direct; S19] **verify current** |
| Key protection | "Offline, Cold-Vaulted Storage", "Multi-Site Storage", "Multi-Tiered Approval Structure"; no mention of MPC or HSM. | reported [S33, direct] |
| Assurance | "SOC 1 Type 2 and SOC 2 Type 2 audits annually". | reported [S33, direct] |
| ETF role | Fidelity's FBTC is described as not relying on Coinbase for custody. | reported [S10, summary, secondary] |

### 1.8 BNY

| Item | Finding | Evidence |
|------|---------|----------|
| Platform | Digital Asset Custody platform live 2022-10-11 for select US clients, bitcoin and ether; built with Fireblocks (custody technology) and Chainalysis (compliance). | reported [S34, summary] |
| Stablecoins | 2026-06-29: USDC is the first stablecoin on the platform (hold, transfer, mint, burn); BNY is "primary custodian of USDC reserves". | reported [S35, direct] |
| Abu Dhabi | Bitcoin and ether custody in ADGM with local partners; sources disagree on whether it has launched or awaits approvals. | reported [S36, summary] **verify current** |

### 1.9 Other top-tier custodians

- **Komainu** — joint venture of Nomura, CoinShares and Ledger, headquartered in Jersey (JFSC); VARA licence in Dubai; UK FCA registration for anti-money-laundering purposes only; Italian OAM registration. One report says its technology is based on Ledger Vault; not confirmed. Reported [S37, summary] **verify current**
- **Zodia Custody** — launched by Standard Chartered and Northern Trust (2020). May 2026 reports: Standard Chartered to absorb Zodia's regulated custody into its Financing and Securities Services division, with the software platform spun out as Zodia Solutions under SC Ventures; completion was pending regulatory approval. Standard Chartered holds a Luxembourg MiCA custody licence (January 2025). Key technology: not found. Reported [S38, summary] **verify current**
- **Ledger Enterprise** — FIPS 140-2 Level 3 HSMs, on premises or in Ledger data centres, enforce governance rules; approvers sign on Ledger hardware devices with clear signing (recipient, amount and fee shown on the device). Anti-replay state moved from per-object HSM counters to one 32-byte sparse-Merkle-tree root per customer held in the HSM. Ledger Enterprise Multisig is built on Safe contracts. An HSM On-Premise option was announced March 2026. Reported [S39, summary, vendor]
- **Cobo** — MPC-TSS co-managed custody; recommended three-node layout: node 1 run by Cobo and always online, node 2 run by a third party the client appoints for disaster recovery, node 3 run by the client. Licences not researched. Reported [S40, summary]
- **Taurus** (Switzerland) — Taurus-PROTECT combines FIPS 140-2 Level 3 HSMs with MPC/TSS and lists State Street and Deutsche Bank among clients (vendor claims). Publishes `taurushq-io/multi-party-sig` (Go; CMP and FROST; Apache-2.0; last push 2025-09-10). Reported [S41, summary]; observed [S41b]

### 1.10 Patterns across custodians (for the manual)

1. **Three key-protection families coexist at the top tier:** HSM-enforced quorum with no MPC described in the public material read (Anchorage, Ledger Enterprise; Coinbase CCTC's 10-K describes HSMs and multi-approver decryption); MPC with shares in TEEs or on separate parties (Fireblocks, BitGo TSS wallets, Copper, Cobo); and hybrids (Taurus, BitGo multisig plus MPC). Reported [S3, S16, S23, S28, S39, S41]. The manual's chapter 3 (HSM vs MPC vs TEE) can cite these as live examples.
2. **The approval quorum lives in different places:** inside the HSM firmware (Anchorage, Ledger), in a policy layer in front of MPC nodes (Fireblocks, Cobo), or in an on-chain contract (Safe-based products). This maps onto custody-lab's two-quorum design (chapter 4).
3. **ETF custody is concentrated** in one custodian, and issuers have started adding standby second custodians (BlackRock April 2025; Grayscale September 2026). Reported [S9, S10, S12] **verify current**

---

## 2. Top assets by market capitalisation and how each is signed

### 2.1 Ranking

Source: CoinGecko public API, `coins/markets`, `last_updated` 2026-10-09 09:04 UTC. Observed [S1]. Cross-checked against CoinPaprika `tickers`, 2026-10-09 09:01 UTC. Observed [S2]. **verify current** (prices move by the minute).

| CG rank | Asset | Market cap (USD bn) | Note |
|--:|---|--:|---|
| 1 | Bitcoin (BTC) | 1,658.9 | price $82,546 |
| 2 | Ethereum (ETH) | 305.6 | price $2,502 |
| 3 | Tether (USDT) | 184.1 | stablecoin |
| 4 | BNB | 98.9 | |
| 5 | XRP | 88.4 | |
| 6 | USDC | 73.0 | stablecoin |
| 7 | Solana (SOL) | 65.1 | |
| 8 | TRON (TRX) | 31.6 | |
| 9 | Figure Heloc (FIGR_HELOC) | 24.4 | tokenised home-equity credit; absent from CoinPaprika's top 25; not researched |
| 10 | Zcash (ZEC) | 20.8 | |
| 11 | Hyperliquid (HYPE) | 19.1 | |
| 12 | Dogecoin (DOGE) | 13.3 | |
| 13 | Monero (XMR) | 10.3 | |
| 14 | USDS (Sky) | 10.2 | stablecoin |
| 15 | WhiteBIT Coin (WBT) | 9.6 | exchange token; not researched |
| 16 | Chainlink (LINK) | 9.6 | |
| 17 | Cardano (ADA) | 9.0 | |
| 18 | LEO Token | 8.2 | exchange token; not researched |
| 19 | Rain | 7.3 | not researched |
| 20 | Stellar (XLM) | 6.8 | |

The two sources agree on ranks 1-8. CoinPaprika additionally ranks wrapped and staked derivatives (Lido stETH at 9, wstETH, WBTC, Coinbase cbBTC) that CoinGecko's default list omits. Observed [S1, S2]. For a custodian these derivatives are ERC-20 balances whose value depends on a second custodian or protocol (Lido, BitGo for WBTC, Coinbase for cbBTC); reported issuers for WBTC/cbBTC are general knowledge here and unverified.

### 2.2 Signing scheme, ledger model and custody quirks

"Threshold options" lists what the ledger offers natively and which MPC family a custodian needs. No source found states what share of custodians use MPC for a given asset, so "standard practice" is not asserted.

| Asset | Signature scheme and curve | Model | Threshold options | Custody quirks | Evidence |
|---|---|---|---|---|---|
| **BTC** | ECDSA secp256k1 (legacy, SegWit v0); BIP340 Schnorr secp256k1 (Taproot, SegWit v1) | UTXO | Native script multisig; MuSig2 (BIP 327, n-of-n); FROST for t-of-n with one key on-chain (no BIP yet, section 3.2); threshold ECDSA via MPC | Taproot key-path outputs put the tweaked public key on-chain, which BIP 360's authors treat as long-exposure quantum risk (section 3.7). Fees come from inputs, so a custodian chooses whose coins pay (custody-lab charges the client, chapter 8). | BIP 340/341 in the BIPs index, observed [S77]; [S88] |
| **ETH** | Accounts: ECDSA (secp256k1 per the Yellow Paper; ethereum.org names only "Elliptic Curve Digital Signature Algorithm"). Validators: BLS keys, separate from account keys | Account; per-account nonce counts sent transactions | Smart-contract multisig (Safe); threshold ECDSA via MPC; threshold BLS for validator keys (distributed validators, section 3.12) | Nonce strictly orders transactions (same discipline as INX's per-key nonce). Staking: slashable offences are double proposal, surround vote, double vote; an immediate burn of 0.0078125 ETH for a 32 ETH validator (scaled with balance), a correlation penalty that grows with the total stake slashed at the same time, and 36 days to exit. Since Pectra (2025-05-07, epoch 364032) the maximum effective balance is 2,048 ETH (EIP-7251) and EOAs can delegate code (EIP-7702, type `0x04`; an authorization with chain ID 0 is valid on every chain). Losing the BLS withdrawal key before switching to `0x01` withdrawal credentials loses access to the balance. | reported [S51, S52, S53, S54, S55, direct]; secp256k1 per Yellow Paper unverified here |
| **USDT** | Inherits the host chain (Ethereum ERC-20, Tron TRC-20, others) | Token on account chains | As host chain | Issuer controls: the Ethereum `TetherToken` contract ABI includes `addBlackList`, `removeBlackList`, `destroyBlackFunds`, `pause`, `issue`. Tether froze $182 m across five Tron addresses (2026-01-11) and over $344 m on two Tron addresses with OFAC (April 2026). A custodian can hold a balance it cannot move. | observed ABI via Etherscan [S56]; reported [S57, summary] **verify current** |
| **BNB** | BNB Smart Chain is EVM-compatible (account keys as Ethereum, assumed secp256k1 ECDSA); validators also hold BLS vote keys for fast finality | Account | As Ethereum (Safe on BSC, MPC ECDSA) | BNB Beacon Chain sunset completed (final fork 2024-11-19); some small and unbound Beacon Chain balances were declared unrecoverable. Native staking on BSC: running the same consensus and BLS vote keys on two machines is a slashable "malicious vote" (200 BNB, 30-day jail); delegators are not slashed per BSC docs. | reported [S61, summary]; BSC account curve unverified |
| **XRP** | secp256k1 ECDSA by default; Ed25519 supported, interchangeable for master, regular and signer-list keys | Account | Native multisig (signer lists); regular key can replace the master key; master key can be disabled | Base reserve 1 XRP plus 0.2 XRP per owned object (Mainnet), recoverable only by deleting the account. Destination tags identify the beneficiary inside a hosted account; `RequireDest` makes the ledger reject untagged payments. | reported [S43, S44, S45, direct] **verify current** (reserves change by fee vote) |
| **USDC** | Inherits host chain | Token | As host chain | Circle's terms (updated 2025-12-12): Circle "reserves the right to block the transfer of USDC to and from an address on chain" and may freeze. BNY is primary custodian of USDC reserves. | reported [S58, S35, direct] |
| **SOL** | Ed25519 (one 64-byte signature per signer; addresses are 32-byte Ed25519 keys or program-derived addresses) | Account (accounts hold data and lamports) | Program-based multisig (unverified; not researched); threshold EdDSA via MPC | A recent blockhash is valid for 150 slots (about 80-90 s per Solana's guide), which bounds an air-gapped signing round trip. Durable nonces remove that expiry: a signed transaction stays valid until the nonce is advanced, which made the Drift attack possible (section 4). Every account must hold a refundable minimum balance: (size + 128) x 3,480 lamports per byte-year x 2 years. Base fee 5,000 lamports per signature. Slashing: an evidence programme (SIMD-0204) exists; penalties (SIMD-0212) were under discussion and not live as of mid-2026. | reported [S46, S47, S48, S49, direct; S50, summary] **verify current** (slashing) |
| **TRX** | Assumed secp256k1 ECDSA (Ethereum-style addresses) | Account | Native account permissions (not researched); MPC ECDSA | Resource model: Bandwidth and Energy; a TRC-20 USDT transfer burns TRX if the sender has no staked Energy, and costs more Energy to a recipient that has never held USDT. Activating a new account costs 1 TRX; TRC-20 transfers do not activate accounts. Energy price cut to 100 sun by Proposal #104 (2025-08-29). Most reported 2026 USDT freezes are on Tron. | reported [S59, summary]; curve unverified **verify current** |
| **ZEC** | Transparent addresses: Bitcoin-derived ECDSA secp256k1 (unverified). Shielded spends: RedDSA re-randomizable Schnorr (RedJubjub for Sapling, RedPallas for Orchard; unverified in this session) | UTXO plus shielded note pools | Transparent: script multisig. Shielded: FROST over shares of the spend authorization key; the Zcash Foundation publishes `frost-rerandomized` 3.0.0 and `reddsa` 0.6.1 | Shielded balances are invisible on-chain, so proof of reserves needs viewing keys or a ZK proof. Bitget's September 2026 loss included Zcash assets. | reported [S67, direct]; observed crates.io [S81]; [S121] |
| **HYPE** | User actions on HyperCore are EIP-712 typed-data signatures (Ethereum keys, secp256k1) | Account; L1 order book plus HyperEVM | Ethereum-style keys, so MPC ECDSA | USDC bridge to Arbitrum: withdrawals need signatures from 2/3 of stake-weighted validators, then a dispute period during which a cold-wallet quorum can lock the bridge; L2BEAT reports four permissioned validators per set and flags that a validator majority could sign an invalid withdrawal. | reported [S60, summary] **verify current** |
| **DOGE** | ECDSA secp256k1; no SegWit or Taproot | UTXO | Script multisig; MPC ECDSA | Merge-mined with Litecoin since 2014. | merge mining reported [S68, summary]; signature facts unverified |
| **XMR** | Ed25519-family keys; CLSAG ring signatures; one-time (stealth) addresses | UTXO-like outputs | Native Monero multisig, being reworked for FCMP++; no MPC custody product for XMR found among the custodians in section 1 | FCMP++ (replaces CLSAG) was on a stress test network with a fork on 2026-10-05; no mainnet date; multisig work pending. Many regulated venues do not list it. | reported [S66, summary]; key facts beyond FCMP++ unverified **verify current** |
| **USDS** | ERC-20 on Ethereum | Token | As Ethereum | Upgradeable contract; no freeze function at launch (2024-09-18); governance could add one later. Activation since: not confirmed. | reported [S65, summary] **verify current** |
| **LINK** | ERC-677 on Ethereum (ERC-20 plus `transferAndCall`) | Token | As Ethereum | Bridged LINK on other chains may not be ERC-677. | reported [S64, summary] |
| **ADA** | Ed25519 payment key and stake key | Extended UTXO (unverified) | Native script multisig (stake addresses may be script-based) | Delegators keep spending power while staked; the docs describe no delegator penalty. Registering a stake address requires a refundable deposit. | reported [S62, direct] |
| **XLM** | Ed25519 (unverified) | Account | Native multisig through signers and thresholds | Each subentry (trustline, offer, signer) raises the minimum balance by one base reserve of 0.5 XLM. Memos (unverified). | reported [S63, direct] **verify current** |

### 2.3 What the table teaches a custodian

- **Two curves cover most of the table:** secp256k1 (BTC, ETH and EVM chains, XRP default, TRX, DOGE, transparent ZEC, HYPE) and Curve25519/Ed25519 (SOL, XLM, ADA, XRP optional, XMR keys). Shielded ZEC uses its own curves (Jubjub, Pallas; unverified in this session). This is why MPC vendors ship one ECDSA protocol and one EdDSA protocol (BitGo MPCv2/MPCv1 [S23]; cb-mpc [S4]; Fireblocks MPC-CMP for both [S29]).
- **Shielded ZEC and XMR need signature types a standard ECDSA/EdDSA MPC stack does not produce** (re-randomizable Schnorr, ring signatures). Staking keys on Ethereum and BSC are BLS, a third family.
- **Stablecoin issuers can freeze balances held in custody** (USDT, USDC; possibly USDS later). A custodian's books can show an asset it cannot deliver.
- **Signed-transaction lifetime differs by chain:** Bitcoin has none, Ethereum is bounded by the account nonce, Solana's blockhash expires in about a minute unless a durable nonce is used. The policy engine must know which, because a pre-signed transaction that never expires is a standing authorisation (Drift, section 4).
- **Rent, reserves and activation fees** (SOL, XRP, XLM, TRX) mean a client's balance cannot be withdrawn to zero; the custodian's ledger must model the locked portion.

---

## 3. Research and engineering frontier, 2022-2026

### 3.1 Threshold ECDSA

- **CGGMP21 / CGGMP24** — Canetti, Gennaro, Goldfeder, Makriyannis, Peled, "UC Non-Interactive, Proactive, Threshold ECDSA with Identifiable Aborts", ePrint 2021/060; the revised version is often called CGGMP24. A custodian cares because it supports one-round signing after preprocessing, key refresh and identifying a misbehaving signer. Reported [S69, summary]
  - Dfns (2025-11-24) disclosed two issues in its open-source `cggmp21` crate: the original paper's Paillier-Blum modulus proof omitted a check (possible full key extraction; added in CGGMP24), and combining presignatures with "raw" hash signing allows a forgery (blocked at the API in `cggmp24` v0.7.0-alpha.2). Advisories CVE-2025-66016 and CVE-2025-66017. Reported [S70, direct and summary]
- **DKLs23** — Doerner, Kondi, Lee, shelat, "Threshold ECDSA in Three Rounds", IEEE S&P 2024, ePrint 2023/765. Uses oblivious transfer instead of Paillier encryption and subsumes the earlier DKLs 2-of-n and t-of-n protocols. Custodian relevance: fewer heavy zero-knowledge proofs, which the BitForge and TSSHOCK attacks show are where implementations fail. Reported [S71, summary]. Trail of Bits' review of an early Silence Laboratories DKLs23 library found key-destruction flaws (fixed) and concluded OT-based designs are generally less error-prone than Paillier-based ones. Reported [S72, summary]
- **NIST's threshold call lists the current ECDSA field** as preview submissions: TECLA, THE-CLASH, BAM, CCGMP, KU, Trout++, Twig, Menshen and Octopus-(T)CL, DKLs, Stoats. Observed [S83]. **verify current**

### 3.2 FROST, ROAST and robust threshold Schnorr

- **RFC 9591** (June 2024) standardises two-round FROST. Reported [S73, summary]
- **RFC 9591 does not produce BIP340 signatures directly:** the BIP 445 pull request (open since 2026-01-03, last updated 2026-10-02) states RFC 9591 "is incompatible with Bitcoin's BIP340 X-only public keys" and specifies the FROST3 variant from the ROAST paper, modelled on MuSig2 (BIP 327). Key generation is out of scope and comes from ChillDKG or a trusted-dealer BIP. Observed [S74]. custody-lab's `frost-secp256k1-tr` crate is one of the implementations that handles Taproot today.
- **ChillDKG** — Ruffing and Nick's DKG for FROST (bitcoin-dev, July 2024); BIP pull request opened 2026-07-30, open. Design goal: a wallet can be restored from the device seed plus public data. Observed [S75]; reported [S75b, summary]
- **ROAST** — Ruffing, Ronge, Jin, Schneider-Bensch, Schröder, ACM CCS 2022, ePrint 2022/550. A wrapper that makes FROST signing complete even when some signers stall or misbehave, under arbitrary network delay. Custodian relevance: a signing ceremony that cannot be blocked by one unavailable or hostile node. Reported [S76, summary]
- **ZF FROST 3.0.0** (2026-04-23): `frost-core`, `frost-secp256k1-tr`, `frost-rerandomized`; `frost_core::keys` has `dkg`, `refresh` ("Refresh Shares") and `repairable` ("Repairable Threshold Scheme"). Observed [S81]

### 3.3 MuSig2

- BIP 327 (MuSig2) status **Deployed**; BIP 328 (derivation for MuSig2 aggregate keys) Complete; BIP 373 (MuSig2 PSBT fields); BIP 390 (`musig()` descriptor) Draft. Observed [S77]
- Bitcoin Core PR #31244 (`musig()` descriptors) merged 2025-07-31; PR #29675 (wallet receive and spend with MuSig2 aggregate keys) merged 2025-10-14. Neither the 30.0 nor the 31.0 release notes mention MuSig2, so the user-facing release is not established. Observed [S78]
- Custodian relevance: MuSig2 is n-of-n, so every key holder must sign; a custodian wanting t-of-n with one on-chain key needs FROST, or MuSig2 inside a Taproot script tree.

### 3.4 Threshold key derivation (BIP32 with threshold keys)

- Non-hardened BIP32 derivation adds a public tweak to the key, so each share-holder can apply it locally; hardened derivation needs the secret inside HMAC-SHA512 and so needs MPC. (Mechanism: general knowledge; unverified in this session.)
- **Groth and Shoup, Eurocrypt 2022** (ePrint 2021/1330): ECDSA with additive key derivation is secure, presignatures are secure, but the combination weakens security; their fix is re-randomised presignatures. The Dfns 2025 presignature advisory cites this class of attack. Reported [S79, S70, summary]
- **cb-mpc** lists "MPC Friendly Derivation" as a component. Observed [S4]
- **BIP 89 Chain Code Delegation** (Deployed; assigned 2025-12-03): a privileged participant withholds BIP32 chain codes from a co-signer and sends per-spend scalar tweaks, so a custodian co-signer can sign without learning the client's wallet-wide balances. Observed [S80]

### 3.5 Proactive refresh and share repair in practice

- Libraries now ship refresh and repair: ZF `frost-core` (`refresh`, `repairable`) [S81, observed]; cb-mpc ("generate and refresh keyshares") [S4, observed]; Silence Laboratories `dkls23` (refresh, quorum change, migration from GG/CMP keys) [S82, summary]; CGGMP's proactive refresh [S69].
- Gap: no custodian found in this session publishes how often it refreshes shares or how it repairs a lost share. Cobo's three-node layout and BitGo's self-held backup share [S40, S23] are the closest public descriptions of recovery.

### 3.6 Post-quantum threshold signatures

- **NIST IR 8214C, "First Call for Multi-Party Threshold Schemes"**, 2026-01-20; classes N (NIST-specified primitives) and S (special primitives); three preview rounds in 2026; package deadline "expected to be set to 2027-Mar-01 (it will not be before)". Threshold ML-DSA previews: Mithril, Quorus, TALUS. Observed [S83] **verify current**
- **Efficient Threshold ML-DSA** — Celi, del Pino, Espitau, Niot, Prest; USENIX Security 2026; ePrint 2026/013. Claims the first threshold scheme producing standard ML-DSA (FIPS 204) signatures, with average communication per party up to about 1 MB for up to 6 parties. Names multi-device cryptocurrency wallets as a use case. Reported [S84, summary]
- **Threshold Raccoon** (PQShield-led; NIST PQC conference 2024): 13 KiB signatures, 40 KiB communication per user, up to 1,024 signers. Raccoon itself is not among the 14 second-round candidates of NIST's additional-signatures process (October 2024). Reported [S85, S86, summary]
- **Ringtail** — two-round lattice threshold signature. Reported [S87, summary]
- Custodian relevance: a custodian moving to post-quantum signatures today must either sign ML-DSA in one place (an HSM) or use a research-stage threshold scheme. In custody-lab the hybrid Ed25519 + ML-DSA-65 authorisation tokens (chapter 7) are signed by the policy engine alone; only the on-chain signature is threshold, and it is classical (FROST).

### 3.7 Bitcoin post-quantum proposals

- **BIP 360, Pay-to-Merkle-Root (P2MR)** — Draft, version 0.12.1, assigned 2024-12-18 (formerly P2QRH). P2TR without the key path: spends go through the script tree, which protects against "long exposure" attacks on keys sitting on-chain but not against "short exposure" attacks on keys revealed in the mempool; post-quantum signatures are left to a separate proposal. Observed [S88]
- **BIP 361, Post Quantum Migration and Legacy Signature Sunset** — Draft, Informational, assigned 2026-02-11 (Lopp et al.). Phase A forbids sending to quantum-vulnerable addresses; Phase B, five years after activation, restricts ECDSA/Schnorr spends to a quantum-safe rescue protocol. Requires a not-yet-written post-quantum signature BIP. Observed [S89]
- No post-quantum signature BIP is merged. An "Output Public Key Exposure Classification" draft PR opened 2026-09-18. Observed [S77, S74b]
- Custodian relevance: which client coins sit in outputs whose public key is already on-chain (P2PK, reused addresses, P2TR key path) becomes a reportable risk; BIP 361 would freeze coins that are not moved in time.

### 3.8 Ethereum account abstraction and smart-contract custody

- **ERC-4337** — Final. UserOperations go to a separate mempool; bundlers submit them to a singleton EntryPoint contract; no consensus change. Reported [S90, direct]
- **EIP-7702** — Final; live since Pectra (2025-05-07). An EOA signs an authorization `[chain_id, address, nonce]` (signed over `0x05 || rlp(...)`) that delegates its code to a contract; chain ID 0 makes it valid on any chain. The EIP warns "A poorly implemented delegate can allow a malicious actor to take near complete control over a signer's EOA." Reported [S55, direct]. Wintermute's analysis (reported 2025-06-01) found over 80% of EIP-7702 delegations pointed at copies of one wallet-sweeping script. Reported [S91, summary]
- **EIP-7951** — secp256r1 (P-256) verification precompile, live with Fusaka (2025-12-03). Lets contracts verify passkey and HSM-native P-256 signatures. Reported [S92, summary]
- **Safe** — Q1 2026: $35.25 bn in assets across 61 million accounts; Q2 2026: 63.4 million accounts. Reported [S93, summary] **verify current**
- Custodian relevance: a policy engine signing for an Ethereum EOA must now decode type-4 transactions and authorization tuples, and for Safe must decode `operation` (CALL vs DELEGATECALL), because both change who controls the account (Bybit, section 4).

### 3.9 Zero-knowledge proof of liabilities and solvency

- **Summa** (Ethereum Foundation PSE): started March 2023 after FTX; retrospective published 2025-02-10 describing adoption hurdles. Reported [S94, direct for date; summary for content]
- **Exchange deployments:** Binance added zk-SNARKs to its Merkle-tree proof of reserves in February 2023 (with Polyhedra) to prove every leaf is counted and no user balance is negative; OKX added zk-STARKs in April 2023 and publishes monthly. Whether either proves complete liabilities is disputed by independent trackers. Reported [S95, summary, secondary]
- Custodian relevance: custody-lab's Merkle-sum tree (chapter 6) proves inclusion and sums but not that every leaf is non-negative; the ZK layer is what stops a negative-balance leaf from shrinking the total. Check: whether the repo's Hu, Zhang and Guo (2019) oracle already covers the negative-leaf case or a different summation flaw.

### 3.10 TEEs and attestation in custody

- **In production:** Fireblocks (Intel SGX) [S28]; Coinbase CDP server wallets (AWS Nitro Enclaves) [S8]; Turnkey (Nitro Enclaves running its QuorumOS, with reproducible builds so a verifier can match the attested measurement to source; whitepaper January 2025) [S96]. Reported.
- **WireTap** (Georgia Tech, Purdue) and **Battering RAM** (KU Leuven, Birmingham), October 2025: physical DDR4 memory-bus interposers (about $1,000 and under $50) that defeat SGX's deterministic memory encryption and extract the attestation (Quoting Enclave) key, so a forged quote passes verification. Reported [S97, summary]
- **TEE.fail**, October 2025: the DDR5 follow-up; extracts keys from Intel TDX and AMD SEV-SNP (including Ciphertext Hiding) and forges SGX/TDX attestations; demonstrated against BuilderNet and Phala's dstack. Intel and AMD state physical attacks are outside their threat model. Reported [S98, summary]
- Custodian relevance: attestation proves which code runs, under the vendor's threat model. A custodian's threat model includes someone with physical access to the data centre, which is the case these attacks cover.

### 3.11 Published attacks on MPC wallets

| Year | Name | What failed | Who was affected | Evidence |
|---|---|---|---|---|
| 2022-12 | Zero Proof | BitGo ECDSA TSS omitted mandatory ZK proofs; key from one signature | BitGo early-access TSS wallets | reported [S27] |
| 2023-03 | Kudelski CVEs (e.g. CVE-2022-47931) | Ambiguous hashing of concatenated values in tss-lib ZK proofs | io.finnet tss-lib | reported [S102] |
| 2023-08 | TSSHOCK (Verichains, Black Hat USA 2023) | Three key-extraction attacks on GG18, GG20 and CGGMP21 implementations, including forged dlnproofs; one malicious party suffices | Most implementations tested; Multichain fastMPC | reported [S99] |
| 2023-08-09 | BitForge (Fireblocks) | GG18/GG20: Paillier modulus not validated, key in 16 signatures (CVE-2023-33241); Lindell17 implementations leaking key bits on abort, about 200 signatures | 15+ providers incl. Coinbase WaaS, ZenGo, Binance tss-lib | reported [S100] |
| 2023-08 | ePrint 2023/1234 (Makriyannis, Yomtov, Galansky) | Four attacks needing about 10^6, 256, 16 or 1 signatures depending on target | As BitForge | reported [S101] |
| 2023-10 | Early DKLs23 library review (Trail of Bits) | Key-destruction flaws | Silence Laboratories (fixed) | reported [S72] |
| 2025-11 | CGGMP21 crate issues (Dfns) | Missing Paillier-Blum check; presignature plus raw-hash forgery | `cggmp21` <= 0.6.3 users | reported [S70] |

Pattern: every published break is in the zero-knowledge proofs or parameter checks around Paillier encryption, or in deviations from the paper, never in the underlying signature scheme. Chapter 2's Lindell 2017 section can cite the BitForge Lindell17 abort leak as its "what breaks when done wrong" case.

### 3.12 Distributed validators (threshold BLS for staking keys)

- Obol and SSV split one Ethereum validator key across several operators with DKG and threshold BLS; reported adoption includes Lido and EtherFi operator sets and (per a promotional release) Bitcoin Suisse moving its staking to Obol in July 2026. Reported [S103, summary, partly promotional]. Custodian relevance: the same two-quorum question as custody, applied to the slashable validator key.

---

## 4. Custody-relevant incidents, 2022-2026

Amounts are as reported at the time. Root causes carry the evidence class of the source; where victims dispute a cause, both positions are given.

| Date | Victim | Loss | Root cause | Custody lesson | Evidence |
|---|---|---|---|---|---|
| 2022-03-23 | Ronin bridge | 173,600 ETH and 25.5 m USDC (about $600-625 m) | 5-of-9 validator threshold; attacker obtained four Sky Mavis keys (employee phished) plus an Axie DAO key whose signing delegation to Sky Mavis was never revoked; undetected for six days | A threshold is only as strong as the number of independent organisations behind it; revoke delegated signing authority; monitor outflows | reported [S104, summary] |
| 2022-09-20 | Wintermute | about $160 m | Hot-wallet admin key generated by Profanity, whose 32-bit seed made keys brute-forceable; disclosed days earlier and the admin role was not rotated | Key generation randomness is part of custody; rotate keys on disclosure | reported [S105, summary] |
| 2022-11 | FTX | estate-wide shortfall | Debtors' first interim report (April 2023): keys stored unencrypted or in AWS secrets/password vaults accessible to many staff; almost all assets in hot wallets; no multisig; no backups for many keys | Every control in custody-lab (shares, quorum, cold storage, segregation) is the counter-example | reported [S106, summary] |
| 2023-01-04 | Celsius (ruling) | about $4.2 bn in Earn accounts | Court held the Earn terms transferred title to Celsius, so Earn assets were estate property | Legal title is set by the account terms, not the wallet; chapter 8's segregation discussion | reported [S107, summary] |
| 2023-06 | Prime Trust | receivership | Lost access to legacy wallets from December 2021; used other customers' funds to meet withdrawals from them | Key loss plus commingling turns an operational failure into insolvency | reported [S108, summary] |
| 2023-07 | Multichain | $130-200 m+ (sources differ) | All MPC node servers ran under the CEO's personal cloud account; after his detention, his sister moved assets | MPC with every share under one person's control is single-key custody | reported [S109, summary] |
| 2023-12-14 | Ledger Connect Kit | about $600 k | Former employee phished; malicious versions of an npm package (also served via CDN) were live for about five hours and drained dApp users | Signing front ends are part of the attack surface; pin versions, revoke leavers | reported [S110, summary] |
| 2024-05 | DMM Bitcoin | 4,502.9 BTC (about $305 m) | TraderTraitor (DPRK) social-engineered an employee of wallet vendor Ginco with a fake job test, then altered a legitimate transaction request | Vendor staff with access to the signing workflow are inside the perimeter | reported [S111, summary] |
| 2024-07-18 | WazirX | about $230 m | Safe multisig with six signers (five WazirX, one Liminal); signers approved a payload that differed from what was displayed and upgraded the wallet; WazirX and Liminal dispute where the mismatch originated | What the signer sees must be derived independently of the system proposing the transaction | reported [S112, summary] |
| 2025-02-21 | Bybit | about $1.5 bn | FBI: DPRK "TraderTraitor" [S113, direct]. A Safe{Wallet} developer's Mac was compromised on 2025-02-04; AWS session tokens let the attacker modify JavaScript served from Safe's S3 bucket on 2025-02-19; Bybit's cold-wallet signers approved a transaction that, via `delegatecall`, replaced the Safe's implementation [S114, S115, summary; analyses differ on sequence]. Safe's contracts were not at fault. | The signing devices signed what they were given; no signer verified the decoded transaction against an independent source. Question for chapter 4: if the reported mechanism is right, would a policy rule rejecting `operation = 1` (DELEGATECALL) on a treasury Safe have refused it? | reported |
| 2025-05 onward | EIP-7702 sweepers | per-victim; not aggregated here | Users phished into signing 7702 authorizations to sweeper contracts | New transaction types need policy rules before they are allowed | reported [S91, summary] |
| 2025-05 | Coinbase | $180-400 m remediation estimate | Bribed support-vendor staff leaked customer data; no keys accessed | Insider data leaks feed impersonation attacks on clients, so custody needs out-of-band verification of client instructions | reported [S13, summary] |
| 2025-09-08 | SwissBorg / Kiln | about 192,600 SOL ($41 m) | Staking API provider compromised; eight days earlier a transaction disguised as a small unstake reassigned stake-account authority to the attacker | Staking delegation changes who can withdraw; decode every authority change | reported [S116, summary] |
| 2025-09-08 | npm (chalk, debug) | small; exposure huge | Maintainer phished; payload rewrote wallet destination addresses in browsers for about two hours | Address substitution before signing; verify destinations on the signing device | reported [S117, summary] |
| 2025-11-27 | Upbit (Dunamu) | Dunamu: about 44.5 bn KRW in total; Decrypt: about $36 m | Dunamu: a weakness let the Solana hot-wallet private key be inferred by analysing published transactions; a professor's hypothesis of weak nonce generation is not confirmed by Dunamu | If the nonce hypothesis holds, it is chapter 1's nonce-reuse lesson in production; open question: which signing implementation produced the weak nonces | reported [S118, summary] |
| 2026-04-01 | Drift Protocol | about $280-285 m | Attacker obtained 2 of 5 Security Council approvals through months of social engineering, pre-signed admin-transfer transactions on durable nonces, and executed them later; no code bug | A pre-signed transaction without expiry is a standing authorisation; policy must bound transaction lifetime | reported [S119, direct] |
| 2026-09-06 | Liquid Network (Blockstream federation) | about 4,000 BTC; 3,400 BTC returned | A cache bug in Elements' range-proof verification let the attacker mint about 4,000 unbacked L-BTC, then peg out through SideSwap, a member holding a peg-out authorization key; no private keys compromised | Intact keys do not mean intact reserves: the signer approved a valid-looking peg-out for an invalid claim; reconcile on-chain reserves against issued liabilities (chapter 6) | reported [S120, summary] **verify current** (post-mortem pending) |
| 2026-09-24 | Bitget | $351.6 m, revised to $387.5 m | CEO: attacker compromised a backend system in the wallet infrastructure, spoofed transaction data and triggered the authorisation process; "Private key compromise has been ruled out"; root-cause report promised | Authorisation that trusts data from the system it authorises can be driven by that system; the approval quorum must check what it approves against an independent source | reported [S121, summary] **verify current** |

Aggregate context: Chainalysis reported $2.17 bn stolen from services in H1 2025, with Bybit about 69% of it [S122, summary]; a secondary source citing Chainalysis' 2026 report gives $3.4 bn stolen in 2025 [S122b, summary, secondary].

### 4.1 Lessons grouped by manual chapter

- **Chapter 1 (signatures):** Profanity's weak seed and the Upbit inference both show that key and nonce generation are where signature schemes fail in practice.
- **Chapter 2 (MPC):** Multichain shows MPC without independent share holders; BitForge, TSSHOCK and Zero Proof show implementation failures in the proofs around threshold ECDSA.
- **Chapter 3 (key storage):** TEE.fail and WireTap show that attestation keys can be extracted with physical access.
- **Chapter 4 (policy):** Bybit, WazirX, Drift, SwissBorg and Bitget are all approved transactions; the control that failed was the check of what was approved: decoded calldata, DELEGATECALL, authority changes, transaction lifetime, and data provenance.
- **Chapter 6 (proof of reserves):** Liquid and Prime Trust show reserves diverging from liabilities while keys are intact.
- **Chapter 8 (industry):** FTX and Celsius show segregation and legal title; the OCC charter wave changes who is a qualified custodian.

---

## Gaps and items not verified

- Coinbase CCTC: whether cold custody signs with MPC (the 10-K portion read describes HSMs and multi-approver decryption only); SOC report types.
- Anchorage: the Grayscale filing's "key shards ... combined to reconstitute the private key" against Anchorage's "keys never leave the HSM in plaintext".
- Copper's UK status and ownership; Zodia's deal completion; Komainu's technology base.
- Signature curves for BNB Chain accounts, TRON, Dogecoin, Stellar, transparent and shielded Zcash, Cardano's EUTXO label: general knowledge only.
- Bitcoin Core: whether MuSig2 wallet support is exposed in a release (PRs merged; release notes silent).
- Custodian share-refresh cadence: no public source found.
- Liquid and Bitget root-cause reports were pending as of the sources read.

## Process note

One crates.io API request in this session sent the user's email address in its User-Agent header. It should not have; no other request did.

---

## Sources

All read 2026-10-09. `direct` = page fetched and read; `summary` = read through a search-engine summary of the page; `observed` = API or repository data retrieved by command.

**Market data**
- [S1] CoinGecko API, coins/markets, top 25 by market cap — https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=25&page=1 (observed)
- [S2] CoinPaprika API, tickers — https://api.coinpaprika.com/v1/tickers?limit=25 (observed)

**Custodians**
- [S3] Coinbase Global, Form 10-K FY2025 — https://www.sec.gov/Archives/edgar/data/1679788/000167978826000015/coin-20251231.htm (direct, first 100,000 characters)
- [S4] coinbase/cb-mpc README and repository metadata — https://github.com/coinbase/cb-mpc (direct; licence and push date observed via GitHub API)
- [S5] Coinbase blog, "Introducing Coinbase's Open Source MPC Cryptography Library" — https://www.coinbase.com/blog/introducing-coinbases-open-source-mpc-cryptography-library (summary; direct fetch returned 403)
- [S6] The Block, Coinbase conditional OCC charter, 2026-04-02 — https://www.theblock.co/post/396244/coinbase-receives-conditional-approval-national-trust-charter-occ (direct)
- [S7] The Block, Coinbase to acquire Unbound Security — https://www.theblock.co/post/125770/coinbase-to-acquire-crypto-custody-technology-firm-unbound-security (summary); Decrypt — https://decrypt.co/87226/coinbase-acquires-outbound (summary)
- [S8] Coinbase CDP server wallet security — https://docs.cdp.coinbase.com/server-wallets/v2/introduction/security (summary); AWS Web3 blog — https://aws.amazon.com/blogs/web3/powering-programmable-crypto-wallets-at-coinbase-with-aws-nitro-enclaves (summary)
- [S9] iShares IBIT 8-K, 2025-04-07 — https://www.ishares.com/us/literature/fund-announcement/ibit-8k-04-08-25.pdf (summary); Decrypt — https://decrypt.co/313880/blackrock-anchorage-bitcoin-ethereum-etf-custodian (summary)
- [S10] KuCoin news citing Bitwise — https://www.kucoin.com/news/flash/coinbase-custodies-80-84-of-bitcoin-etf-assets-says-bitwise (summary, secondary)
- [S11] bit.com, IBIT analysis (April 2026) — https://www.bit.com/knowledge-hub/ibit-ishares-bitcoin-trust-the-etf-that-made-bitcoin-a-blue-chip (summary, secondary)
- [S12] Grayscale CoinDesk Crypto 5 ETF, 424B3, 2026-10-05 — https://www.sec.gov/Archives/edgar/data/1729997/000119312526414351/gdlc_424b3_secondary_cus.htm (direct)
- [S12b] Bitwise 10 Crypto Index ETF 424B3 summary — https://www.stocktitan.net/sec-filings/BITW/424b3-bitwise-10-crypto-index-etf-prospectus-filed-pursuant-to-rule-4-58422869121a.html (summary, secondary)
- [S13] eSecurity Planet, Coinbase insider data leak — https://www.esecurityplanet.com/news/coinbase-rejects-ransom-data-leak/ (summary); Computing — https://www.computing.co.uk/news/2025/security/coinbase-to-lose-400-million-after-staff-bribed (summary)
- [S14] OCC News Release 2021-6 (Anchorage) — https://occ.gov/news-issuances/news-releases/2021/nr-occ-2021-6.html (summary)
- [S15] The Block, OCC drops Anchorage consent order, 2025-08-21 — https://www.theblock.co/news/regulation/2025-08-21-us-occ-drops-consent-order-against-anchorage-digital-amid-regulatory-shift-367827 (summary)
- [S16] Anchorage documentation, security — https://docs.anchorage.com/knowledge-base/platform/users/security (direct)
- [S17] Anchorage, SOC 2 Type 2 examination — https://www.anchorage.com/insights/built-by-security-engineers-verified-by-independent-auditors-anchorage-digitals-soc-2-type-2-examination (summary)
- [S18] Fintech News Singapore, Anchorage Digital Singapore licence — https://fintechnews.sg/102943/crypto/anchorage-digital-singapore-license/ (summary)
- [S19] OCC News Release 2025-125, 2025-12-12 — https://occ.treas.gov/news-issuances/news-releases/2025/nr-occ-2025-125.html (direct)
- [S20] BitGo, OCC approval — https://investors.bitgo.com/news/news-details/2025/BitGo-Secures-OCC-Approval-to-Convert-to-Federally-Chartered-National-Trust-Bank/default.aspx (summary)
- [S21] Business Wire, BitGo IPO pricing — https://www.businesswire.com/news/home/20260121850585/en (summary); The Block, first day — https://www.theblock.co/post/386794/bitgo-shares-surge-retrace-volatile-first-day-nyse-trading (summary)
- [S22] BitGo Holdings Form S-1 (2025) — https://www.sec.gov/Archives/edgar/data/1740604/000162828025042203/bitgoholdingsincforms-1.htm (summary)
- [S23] BitGo developer docs, Create MPC keys — https://developers.bitgo.com/docs/wallets-create-mpc-keys (direct); BitGo support, MPC/TSS wallet operations — https://support.bitgo.com/support/solutions/articles/158000454652-mpc-tss-wallet-operations-overview (summary); BitGo changelog — https://developers.bitgo.com/changelog/20240624 (summary)
- [S24] Silence Laboratories, BitGo customer story — https://silencelaboratories.com/customer-stories/bitgo (direct)
- [S25] BitGo blog, SOC 2 — https://bitgo.com/resources/blog/bitgos-commitment-to-security-and-trust-the-soc-2-advantage/ (summary)
- [S26] Cointelegraph, BitGo MiCA licence — https://cointelegraph.com/news/bitgo-crypto-custody-mica-license-germany (summary)
- [S27] Fireblocks, BitGo "Zero Proof" — https://www.fireblocks.com/blog/bitgo-wallet-zero-proof-vulnerability (summary); Decrypt — https://decrypt.co/123869/fireblocks-discloses-critical-vulnerability-with-bitgo-ethereum-wallets (summary)
- [S28] Fireblocks, security principles — https://fireblocks.com/principles/ (direct)
- [S29] Fireblocks developer docs — https://developers.fireblocks.com/docs/what-is-fireblocks (summary); Fireblocks, What is MPC — https://www.fireblocks.com/what-is-mpc (summary)
- [S30] fireblocks/mpc-lib repository metadata — https://github.com/fireblocks/mpc-lib (observed)
- [S31] Fireblocks regulated entities — https://www.fireblocks.com/Regulated-Entities (summary); Cointelegraph — https://cointelegraph.com/news/exclusive-fireblocks-granted-new-york-charter-crypto-custody (summary)
- [S32] Copper Q3 2025 recap — https://copper.co/en-ch/insights/emea/copper-recap-q3-2025 (summary); Copper about — https://copper.co/en/company/about (summary); rfp.wiki Copper profile (low confidence) — https://www.rfp.wiki/crypto/custody-security/institutional-custody-services/copper (summary)
- [S33] Fidelity Digital Assets, trading and custody — https://fidelitydigitalassets.com/trading-custody (direct)
- [S34] BNY press release, 2022-10-11 — https://www.bny.com/corporate/global/en/about-us/newsroom/press-release/bny-mellon-launches-new-digital-asset-custody-platform-130305.html (summary)
- [S35] BNY press release, 2026-06-29 — https://www.bny.com/corporate/global/en/about-us/newsroom/press-release/bny-expands-relationship-circle-adds-institutional-grade-stablecoin-enablement-services.html (direct)
- [S36] crypto.news, BNY ADGM — https://crypto.news/bny-launches-bitcoin-and-ether-custody-in-abu-dhabis-adgm/ (summary)
- [S37] Ledger Insights, Komainu VARA — https://www.ledgerinsights.com/komainu-nomura-digital-asset-custody-vara-license/ (summary); Benzinga, Komainu FCA — https://benzinga.com/markets/cryptocurrency/23/10/35144141/komainu-gets-approval-for-uk-crypto-register-crypto-custody-goes-mainstream (summary)
- [S38] The Block, Standard Chartered to absorb Zodia — https://www.theblock.co/post/401663/standard-chartered-absorb-zodia-custody-crypto-business-bloomberg (summary); Treasury Management — https://treasury-management.com/news/standard-chartered-to-acquire-zodia-custodys-custody-business (summary)
- [S39] Ledger, Merkle-tree HSM scaling — https://www.ledger.com/blog-merkle-tree-hsm-scaling-ledger-enterprise-security (summary); Ledger Enterprise terminology — https://www.ledger.com/blog-ledger-enterprise-new-capabilities-new-language (summary); Crowdfund Insider, Feb 2026 — https://www.crowdfundinsider.com/2026/02/262440-crypto-hardware-wallet-provider-ledger-strengthens-ecosystem-with-enterprise-tools-and-multichain-trading/ (summary)
- [S40] Cobo MPC-TSS technology — https://docs.cobo.com/cobo-mpc-waas/cobo-mpc-co-managed-custody/mpc-tss-technology (summary)
- [S41] Taurus platform capabilities — https://docs.taurushq.com/protect-capital/docs/taurus-platform-capabilities (summary); Taurus-PROTECT product sheet — https://www.taurushq.com/pdfs/taurus-protect-product-sheet.pdf (summary)
- [S41b] taurushq-io/multi-party-sig repository metadata — https://github.com/taurushq-io/multi-party-sig (observed)
- [S42] Axios, OCC conditionally approves five crypto charters — https://www.axios.com/2025/12/12/banks-crypto-occ-charters (summary)

**Assets**
- [S43] XRPL reserves — https://xrpl.org/docs/concepts/accounts/reserves (direct)
- [S44] XRPL cryptographic keys — https://xrpl.org/docs/concepts/accounts/cryptographic-keys (direct)
- [S45] XRPL source and destination tags — https://xrpl.org/docs/concepts/transactions/source-and-destination-tags (direct)
- [S46] Solana transactions — https://solana.com/docs/core/transactions (direct)
- [S47] Solana accounts — https://solana.com/docs/core/accounts (direct)
- [S48] Solana fees — https://solana.com/docs/core/fees (direct)
- [S49] Solana durable nonces guide — https://solana.com/developers/guides/advanced/introduction-to-durable-nonces (direct)
- [S50] Anza, SIMD-0204 — https://anza.xyz/blog/simd-0204-the-first-step-to-slashing-on-solana (summary); Everstake — https://everstake.one/resources/blog/solana-slashing-validators-delegators (summary)
- [S51] ethereum.org, accounts — https://ethereum.org/en/developers/docs/accounts/ (direct)
- [S52] ethereum.org, proof-of-stake keys — https://ethereum.org/en/developers/docs/consensus-mechanisms/pos/keys/ (direct)
- [S53] ethereum.org, rewards and penalties — https://ethereum.org/en/developers/docs/consensus-mechanisms/pos/rewards-and-penalties/ (direct)
- [S54] Ethereum Foundation, Pectra mainnet announcement — https://blog.ethereum.org/2025/04/23/pectra-mainnet (summary); ethereum.org Pectra — https://ethereum.org/roadmap/pectra/ (summary)
- [S55] EIP-7702 — https://eips.ethereum.org/EIPS/eip-7702 (direct)
- [S56] Etherscan, TetherToken contract — https://etherscan.io/address/0xdac17f958d2ee523a2206206994597c13d831ec7#code (direct, ABI)
- [S57] The Block, Tether freezes $344 m — https://www.theblock.co/post/398599/tether-freezes-344-million-in-usdt-on-tron-after-wallets-flagged-by-u-s-authorities (summary); The Block, $182 m — https://www.theblock.co/post/385051/tether-freezes-182-million-usdt (summary)
- [S58] Circle, USDC terms (updated 2025-12-12) — https://www.circle.com/legal/usdc-terms (direct)
- [S59] TRON developers, paying for resources — https://developers.tron.network/docs/paying-for-resources (summary); OneKey, TRC-20 fees — https://onekey.so/blog/ecosystem/usdt-trc20-transfer-fees-energy-bandwidth/ (summary)
- [S60] Hyperliquid bridge docs — https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/bridge (summary); Hyperliquid Bridge2 API — https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/bridge2 (summary); L2BEAT — https://www.l2beat.com/bridges/projects/hyperliquid (summary)
- [S61] BNB Chain, Beacon Chain migration guidance — https://www.bnbchain.org/en/blog/the-bnb-chain-beacon-chain-migration-guidance (summary); BSC validator overview — https://docs.bnbchain.org/bnb-smart-chain/validator/overview/ (summary)
- [S62] Cardano docs, delegation — https://docs.cardano.org/about-cardano/learn/delegation (direct); PyCardano keys and addresses — https://pycardano.readthedocs.io/en/latest/guides/address.html (summary)
- [S63] Stellar docs, accounts — https://developers.stellar.org/docs/learn/fundamentals/stellar-data-structures/accounts (direct)
- [S64] Chainlink, LINK token contracts — https://docs.chain.link/resources/link-token-contracts (summary)
- [S65] Cointelegraph, USDS freeze — https://cointelegraph.com/news/makerdao-sky-usds-stablecoin-freeze-decentralized-court (summary); Decrypt — https://decrypt.co/248173/christensen-sky-governance-freeze-function-debate (summary)
- [S66] CryptoTicker, Monero FCMP++ stressnet fork — https://cryptoticker.io/en/monero-fcmp-stressnet-fork-october-2026/ (summary); Monero CCS, FCMP++ integration audit — https://ccs.getmonero.org/proposals/fcmp++-integration-audit.html (summary)
- [S67] Zcash Foundation FROST book, Zcash — https://frost.zfnd.org/zcash.html (direct)
- [S68] Cointelegraph, Dogecoin merged mining — https://cointelegraph.com/news/dogecoin-adopts-merged-mining-with-litecoin (summary)

**Research frontier**
- [S69] ePrint 2021/060, CGGMP — https://eprint.iacr.org/2021/060 (summary)
- [S70] Dfns, "CGGMP21 Vulnerabilities Patched and Explained", 2025-11-24 — https://dfns.co/article/cggmp21-vulnerabilities-patched-and-explained (direct); GitLab advisory CVE-2025-66016 — https://advisories.gitlab.com/cargo/cggmp21/CVE-2025-66016/ (summary)
- [S71] ePrint 2023/765, DKLs23 — https://eprint.iacr.org/2023/765 (summary)
- [S72] Trail of Bits, DKLs23 review lessons, 2025-06-10 — https://blog.trailofbits.com/2025/06/10/what-we-learned-reviewing-one-of-the-first-dkls23-libraries-from-silence-laboratories/ (summary)
- [S73] RFC 9591 — https://www.rfc-editor.org/rfc/rfc9591.html (summary)
- [S74] bitcoin/bips PR #2070, BIP 445 FROST signing — https://github.com/bitcoin/bips/pull/2070 (observed)
- [S74b] bitcoin/bips PR search results (PRs #2294, #2176, #2133, #2205, #2210) — https://github.com/bitcoin/bips/pulls (observed)
- [S75] bitcoin/bips PR #2227, ChillDKG — https://github.com/bitcoin/bips/pull/2227 (observed)
- [S75b] bitcoin-dev, BIP draft ChillDKG — https://groups.google.com/g/bitcoindev/c/HE3HSnGTpoQ (summary)
- [S76] ePrint 2022/550, ROAST — https://eprint.iacr.org/2022/550 (summary); Blockstream blog — https://blog.blockstream.com/roast-robust-asynchronous-schnorr-threshold-signatures/ (summary)
- [S77] bitcoin/bips README (BIP index with status) — https://github.com/bitcoin/bips/blob/master/README.mediawiki (observed)
- [S78] bitcoin/bitcoin PRs #29675 and #31244, release notes 30.0 and 31.0 — https://github.com/bitcoin/bitcoin/pull/29675 , https://github.com/bitcoin/bitcoin/pull/31244 , https://github.com/bitcoin/bitcoin/blob/master/doc/release-notes/release-notes-31.0.md (observed)
- [S79] ePrint 2021/1330, Groth and Shoup — https://eprint.iacr.org/2021/1330 (summary)
- [S80] BIP 89, Chain Code Delegation — https://github.com/bitcoin/bips/blob/master/bip-0089.mediawiki (observed)
- [S81] docs.rs frost-core 3.0.0 keys module — https://docs.rs/frost-core/3.0.0/frost_core/keys/index.html (direct); crates.io API for frost-core, frost-secp256k1-tr, frost-rerandomized, reddsa — https://crates.io/crates/frost-core (observed)
- [S82] silence-laboratories/dkls23 — https://github.com/silence-laboratories/dkls23 (summary; metadata observed)
- [S83] NIST threshold call page — https://csrc.nist.gov/projects/threshold-cryptography/tcall-1 (direct); NIST IR 8214C — https://nvlpubs.nist.gov/nistpubs/ir/2026/NIST.IR.8214C.pdf (summary)
- [S84] ePrint 2026/013, Efficient Threshold ML-DSA — https://eprint.iacr.org/2026/013 (summary); USENIX Security 2026 — https://www.usenix.org/conference/usenixsecurity26/presentation/celi (summary)
- [S85] NIST, Threshold Raccoon presentation (2024) — https://csrc.nist.gov/Presentations/2024/threshold-raccoon (summary)
- [S86] NIST, second round of additional signatures (2024-10-25) — https://csrc.nist.gov/news/2024/pqc-digital-signature-second-round-announcement (summary)
- [S87] Ringtail paper — https://people.eecs.berkeley.edu/~daryakaviani/ringtail.pdf (summary)
- [S88] BIP 360, P2MR — https://github.com/bitcoin/bips/blob/master/bip-0360.mediawiki (observed)
- [S89] BIP 361 — https://github.com/bitcoin/bips/blob/master/bip-0361.mediawiki (observed)
- [S90] ERC-4337 — https://eips.ethereum.org/EIPS/eip-4337 (direct)
- [S91] The Block, Wintermute on EIP-7702 sweepers — https://www.theblock.co/post/356481/wintermute-warns-pectra-upgrade-leaves-ethereum-users-at-risk-of-automated-attacks (summary)
- [S92] Ethereum Foundation, Fusaka mainnet announcement — https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement (summary)
- [S93] Safe Q1 2026 report — https://safefoundation.org/blog/safe-q1-2026-quarterly-report (summary); Q2 2026 — https://safefoundation.org/blog/safe-q2-2026-quarterly-report (summary)
- [S94] PSE, Summa — https://pse.dev/projects/summa (summary); Retrospective: Summa — https://pse.dev/blog/retrospective-summa (direct, date only)
- [S95] OKX zk-STARK PoR press release — https://aap.com.au/aapreleases/cision20230428ae83378/ (summary); Spark, PoR comparison — https://www.spark.money/tools/bitcoin-proof-of-reserves-comparison (summary, secondary)
- [S96] Turnkey whitepaper — https://whitepaper.turnkey.com/ (summary)
- [S97] The Hacker News, WireTap — https://thehackernews.com/2025/10/new-wiretap-attack-extracts-intel-sgx.html (summary); Intel, encrypted memory frameworks — https://www.intel.com/content/www/us/en/developer/articles/news/more-information-encrypted-memory-frameworks.html (summary)
- [S98] SecurityWeek, TEE.fail — https://www.securityweek.com/new-attack-targets-ddr5-memory-to-steal-keys-from-intel-and-amd-tees/ (summary); The Hacker News — https://thehackernews.com/2025/10/new-teefail-side-channel-attack.html (summary)
- [S99] Verichains, TSSHOCK — https://www.verichains.io/tsshock/ (summary); Black Hat paper — https://i.blackhat.com/BH-US-23/Presentations/US-23-Nguyen-TSSHOCK-Breaking-MPC-Wallets-wp.pdf (summary)
- [S100] Fireblocks, BitForge — https://fireblocks.com/blog/bitforge-fireblocks-researchers-uncover-vulnerabilities-in-over-15-major-wallet-providers/ (summary)
- [S101] ePrint 2023/1234 — https://eprint.iacr.org/2023/1234 (summary)
- [S102] Kudelski Security, threshold CVEs — https://research.kudelskisecurity.com/2023/03/23/multiple-cves-in-threshold-cryptography-implementations/ (summary)
- [S103] Blockworks, Obol — https://blockworks.co/news/obol-launches-obol-token-validator (summary)

**Incidents**
- [S104] Ronin postmortem — https://roninchain.com/blog/posts/back-to-building-ronin-security-breach-6513cc78a5edc1001b03c364 (summary)
- [S105] Halborn, Wintermute — https://halborn.com/explained-the-wintermute-hack-september-2022/ (summary)
- [S106] The Block, FTX interim report — https://www.theblock.co/amp/post/225601/ftx-bankruptcy-report-latest (summary); Decrypt — https://decrypt.co/125866/ftx-private-keys-amazon-web-services-aws (summary)
- [S107] Morrison Foerster, Celsius Earn ruling — https://www.mofo.com/resources/insights/230109-celsius-bankruptcy-court-customer-deposits-earn-accounts (summary)
- [S108] The Block, Prime Trust receivership petition — https://www.theblock.co/news/business/2023-06-27-nevada-regulator-files-petition-to-place-prime-trust-in-receivership-236762 (summary)
- [S109] Blockworks, Multichain — https://blockworks.co/news/multichain-founder-family-arrested (summary)
- [S110] Revoke.cash, Ledger Connect Kit retrospective — https://revoke.cash/blog/2023/ledger-connect-kit-hack-retrospective (summary)
- [S111] BleepingComputer, FBI on DMM Bitcoin — https://www.bleepingcomputer.com/news/security/fbi-links-north-korean-hackers-to-308-million-crypto-heist (summary)
- [S112] QuillAudits, WazirX — https://quillaudits.com/blog/hack-analysis/wazirx-235m-hack (summary); Unlock, Liminal account — https://www.unlock-bc.com/126004/liminal-details-wazirx-security-breach/ (summary)
- [S113] FBI PSA I-022625-PSA, 2025-02-26 — https://ic3.gov/psa/2025/psa250226 (direct)
- [S114] BleepingComputer, Safe developer machine — https://www.bleepingcomputer.com/news/security/lazarus-hacked-bybit-via-a-breached-safe-wallet-developer-machine/ (summary); Decrypt, Mandiant findings — https://decrypt.co/309018/what-caused-bybit-ethereum-hack-new-details (summary); CryptoSlate — https://cryptoslate.com/safes-internal-investigation-reveals-developers-laptop-breach-led-to-bybit-hack/ (summary)
- [S115] BlockSec, Bybit incident — https://blocksec.com/blog/bybit-incident-a-web2-breach-enables-the-largest-crypto-hack-in-history (summary)
- [S116] Halborn, SwissBorg — https://www.halborn.com/blog/post/explained-the-swissborg-hack-september-2025 (summary); The Record — https://therecord.media/swissborg-platform-solana-cryptocurrency-stolen (summary)
- [S117] Endor Labs, npm chalk/debug compromise — https://endorlabs.com/learn/major-supply-chain-attack-compromises-popular-npm-packages-including-chalk-and-debug (summary)
- [S118] Decrypt, Upbit — https://decrypt.co/350196/south-koreas-upbit-36-million-loss-solana-hot-wallet-breach (summary); SC World — https://www.scworld.com/brief/crypto-heist-against-upbit-linked-to-private-key-vulnerability (summary)
- [S119] BleepingComputer, Drift, 2026-04-02 — https://www.bleepingcomputer.com/news/security/drift-loses-280-million-north-korean-hackers-seize-security-council-powers (direct)
- [S120] Halborn, Liquid Network — https://www.halborn.com/blog/post/explained-the-liquid-network-hack-september-2026 (summary); Gizmodo — https://gizmodo.com/hackers-drain-320-million-from-bitcoins-liquid-network-keep-47-million-for-themselves-in-white-hat-operation-2000808262 (summary)
- [S121] The Block, Bitget — https://theblock.co/news/markets/2026-09-24-more-than-170-million-in-crypto-moves-from-bitget-wallets-unidentified-address-416345 (summary); Blockhead — https://www.blockhead.co/2026/09/25/bitget-loses-351-6-million-in-hot-wallet-breach-rules-out-private-key-compromise/ (summary)
- [S122] Outlook Business, Chainalysis H1 2025 — https://www.outlookbusiness.com/news/mid-year-update-crypto-thefts-top-usd-217-billion-in-2025-shows-data (summary)
- [S122b] Stingrai, citing Chainalysis 2026 report — https://www.stingrai.io/blog/crypto-hacking-statistics-2026 (summary, secondary)
