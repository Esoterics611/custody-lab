# custody-lab

A working model of how an institution holds bitcoin for its clients so that no single person and
no single computer can move the coins, together with a manual that teaches every idea it uses
from school arithmetic upwards.

> [!WARNING]
> **EDUCATIONAL, NOT PRODUCTION.** This is a demo and a teaching project. It runs on a private
> Bitcoin test network with worthless coins. Several parts are written from scratch to be read,
> not deployed, and are labelled as such. Do not use any of it to hold real assets.

## The problem it demonstrates

On Bitcoin, whoever can produce a signature with a key controls the coins held under that key,
and a confirmed payment cannot be reversed by anyone: there is no operator, no chargeback and no
court-ordered correction of the ledger. A custodian holding coins for clients therefore has to
answer two questions that a bank holding securities never faces in this form. Who is able to
produce the signature, and for which payments?

This project shows one complete answer, the one used by institutional custodians that rely on
multi-party computation (MPC):

- **The key never exists in one place.** It is created in three pieces by three separate
  processes, and any two of them can produce a signature together without ever rebuilding the key.
- **People decide, machines sign.** A policy engine refuses every payment it has not been
  configured to allow, requires approvals that people sign with their own keys, and gives the
  signing processes a signed permission naming the one transaction they may sign. Each signing
  process checks that permission itself.
- **The custodian proves what it holds.** After each batch of payments it publishes the total it
  owes its clients, in a form that lets each client check its own balance was counted, together
  with the coins held and a signature showing it controls them.

## What happens in one run

One run follows a client's trades through to a settled payment, in nine steps:

```
 alpha-capital sends four orders over FIX 5.0 SP2; the toy exchange fills each
            │
            ▼
 netting: four fills become one instruction, "deliver 0.85 BTC to the exchange"
            │
            ▼
 policy engine (default-deny)  ◀──  bob and carol each sign an approval
            │  signed authorisation naming one exact transaction
            ▼
 coordinator  ──▶  signer 1 ┐  two of the three signer processes, one key share each;
              ──▶  signer 3 ┘  signer 2 is not needed and the key is never rebuilt
            │  one ordinary 64-byte Bitcoin signature
            ▼
 Bitcoin Core on a private regtest chain: transaction accepted, block mined
            │
            ▼
 proof-of-reserves snapshot: liabilities, assets, signed by the same 2-of-3 key
```

| Step | What happens | Explained in |
|------|--------------|--------------|
| 1. Chain | A private Bitcoin network starts, owned by this run alone | [Chapter 5](manual/chapters/05-settlement.md) |
| 2. Keys | Three processes run distributed key generation; each ends up holding one share of a 2-of-3 key, and the custody address is derived three independent ways and compared | [Chapters 1](manual/chapters/01-foundations.md) and [2](manual/chapters/02-mpc-custody.md) |
| 3. Fund | 5.00 BTC, the four clients' balances, is sent to the custody address | [Chapter 5](manual/chapters/05-settlement.md) |
| 4. Trade | A FIX 5.0 SP2 session sends four orders and receives four fills | [Chapter 5](manual/chapters/05-settlement.md) |
| 5. Net | The fills net to one obligation: deliver 0.85 BTC | [Chapter 5](manual/chapters/05-settlement.md) |
| 6. Policy | The transaction is built and checked against the instruction; with one approval the policy says PENDING, with two it issues an authorisation | [Chapter 4](manual/chapters/04-policy.md) |
| 7. Sign | Signers 1 and 3 check the authorisation and produce one signature with FROST | [Chapter 2](manual/chapters/02-mpc-custody.md) |
| 8. Broadcast | Bitcoin Core accepts the transaction and mines a block over it | [Chapter 5](manual/chapters/05-settlement.md) |
| 9. Reserves | A snapshot is published: liabilities 4.1499969 BTC, assets 4.1499969 BTC, reserve ratio 1 | [Chapter 6](manual/chapters/06-reserves.md) |

[Chapter 0](manual/chapters/00-orientation.md) walks through all nine steps in plain words, with
the arithmetic of each step worked by hand.

## Reading the manual

The manual is written for an engineer who knows trading or payments infrastructure and has no
background in cryptography. It reads on GitHub: each chapter links to the next, and every mention
of another chapter is a link.

1. **Start with [Chapter 0, Orientation](manual/chapters/00-orientation.md).** It explains keys,
   signatures, splitting a key, threshold signing, approvals and proof of reserves with numbers
   small enough to check by hand, then follows the demo step by step.
2. **Continue in order** through the [contents page](manual/README.md): foundations, MPC custody,
   key storage, policy, trading to settlement, proof of reserves, post-quantum cryptography,
   industry and regulation, a capstone design review, and custody in practice today: custodians,
   assets, recent losses and what is being standardised.
3. **Look things up** in the [glossary](atlas/glossary.md), which links each term to the section
   that teaches it, and in the [atlas](atlas/index.md), one entry per concept.

Every code listing in the manual ran when the chapter was built, and the numbers in the text are
the numbers that code printed. Every chapter follows the manual's writing standard.

## Running it

### Prerequisites

| Tool | Version used | Needed for | Install |
|------|--------------|------------|---------|
| Python and [uv](https://docs.astral.sh/uv/) | Python 3.12, uv 0.12 | everything | `curl -LsSf https://astral.sh/uv/install.sh \| sh`; uv fetches Python itself |
| Rust, via [rustup](https://rustup.rs) | stable (1.98) | building the two Rust extensions on `uv sync` | `curl --proto '=https' -sSf https://sh.rustup.rs \| sh` |
| [Bitcoin Core](https://bitcoincore.org/en/download/) | 31.1 | the demo, the tests that settle on chain, chapters 5 and 6 | download the release for your platform, check it against `SHA256SUMS`, and put `bitcoind` and `bitcoin-cli` on `PATH` |
| [Node.js](https://nodejs.org) | 24 | the dashboard only | any Node 24 install |
| TinyTeX | TeX Live 2026 | the PDF manual only | `uv run quarto install tinytex` |

The project was built and tested on Linux (Ubuntu under WSL2). Each demo run starts its own
Bitcoin node on free ports in its own directory, so no node has to be started first.

### Commands

```bash
uv sync                      # create the environment and compile the two Rust extensions
uv run pytest                # all tests, including real settlements on regtest
uv run custody-lab run       # one demo run, printed step by step
uv run custody-lab day       # a day: deposits, a double spend, trading, withdrawals, refusals
uv run custody-lab ceremonies  # share refresh against a thief, and a lost share repaired; no chain
uv run custody-lab protocol    # every message between coordinator and signers, split into fields; no chain
uv run custody-lab clocks      # signers' clocks set back, and signed time from a time authority; no chain
uv run custody-lab audit       # the policy audit log through two settlements, then a forger's copy; no chain
uv run custody-lab redteam     # a reorganised deposit and a misdirected withdrawal, weak rule then defence
uv run custody-lab attacks   # twenty attacks on the design, each refused; needs no Bitcoin node
```

**Expect:** `custody-lab run` prints `[1/9] Start a private Bitcoin Core regtest chain` and the
results of each step after it, and ends with the settlement's transaction id, `reserve_ratio:
1.00000`, and the directory under `var/demo/` that holds the run's event log, policy audit log
and reserves snapshot. `custody-lab run --offline 1` stops signer 1's process before signing, and
signers 2 and 3 settle instead. `custody-lab day` runs eleven steps, comparing the ledger with the
coins on chain after each, and ends with `reserve_ratio: 1.00000`. `custody-lab audit` prints eight
audit entries and two anchored heads, then where a forger's edit of each entry is caught; its
summary gives `anchored_entries: [3,6]` and, for each entry, the first snapshot that exposes a
re-hashed copy (none for entry 7). `custody-lab attacks` lists each attack with the component that
refused it and ends with `20 of 20 attacks refused`.

To watch a run in the browser instead:

```bash
npm --prefix web ci          # once: install the dashboard's dependencies
npm --prefix web run build   # build the dashboard into web/dist
uv run custody-lab serve     # then open http://127.0.0.1:8000 and press "Run the demo"
```

**Expect:** nine tabs. On **Settlement run**, nine numbered steps turn from pending to running
to done as the events arrive, and a key-shares panel lists signers 1, 2 and 3 with their process
ids and a switch that takes each offline for the next run. **A day at the custodian**, **Key
ceremonies**, **Clocks** and **Red team** each play one scenario. **Watch the protocol** animates
every message between the coordinator and the signers through key generation, signing, refresh and
repair, splits each into its fields, and counts what the coordinator could not open. **The audit
log** shows each entry the policy engine writes through two settlements, and a switch that edits
one entry of a copy to show where the hash chain breaks and which signed snapshot exposes it.
**Attack the design** runs the twenty attacks. **Check a client's balance** recomputes a client's
inclusion proof in the browser after a run. [The demo walkthrough](manual/demo-walkthrough.md) takes one run through the
dashboard step by step: what each value on the screen means, and how to check the run's files
afterwards.

Linting, type checking and the manual:

```bash
uv run ruff check && uv run mypy   # lint, and strict type checking
scripts/render-manual.sh           # every chapter to PDF and to the Markdown shown on GitHub
```

## What is real and what is a toy

[The attack-vector analysis](manual/attack-vectors.md) lists every way found to attack the design,
what stops each in the demo, and what remains open, including two gaps between the demo as
packaged and the design it shows.

Five components are third-party software. Everything else is written for this project.

| Component | Used for | Status |
|-----------|----------|--------|
| Zcash Foundation [`frost-secp256k1-tr`](https://github.com/ZcashFoundation/frost) 3.0.0 (Rust) | Key generation and signing in the demo, one process per share | Real library. This variant is outside the scope of the NCC Group audit of the other ZF FROST crates |
| [Bitcoin Core](https://bitcoincore.org) 31.1 | The private regtest chain | Real node on a private network |
| [`cryptography`](https://cryptography.io) | Ed25519 approvals, ML-DSA-65 and ML-KEM | Real library (OpenSSL) |
| RustCrypto [`slh-dsa`](https://github.com/RustCrypto/signatures) 0.1.0 (Rust) | SLH-DSA post-quantum signatures | Its README states it has never been independently audited |
| [`simplefix`](https://github.com/da4089/simplefix) | Encoding and parsing FIX messages | Real library; the session on top is minimal (no heartbeats, resends or gap fill) |

- **Teaching implementations** of elliptic curves, ECDSA, Schnorr (BIP340), Shamir sharing,
  Paillier encryption, two-party ECDSA, FROST, DKG and WOTS+/XMSS are written from scratch in
  Python, labelled EDUCATIONAL, NOT PRODUCTION, and each is checked against an outside reference.
- **Bitcoin transactions** are built in Python from BIP 341. They pass every BIP 341 wallet test
  vector, and Bitcoin Core accepts and mines them.
- **The exchange is a toy** that fills every order in full at its limit price.
- **Key storage is not protected.** The three signer processes run on one computer, and an
  administrator of that computer can read all three. The demo shows the protocol, not the
  protection. [Chapter 3](manual/chapters/03-key-storage.md) explains where each key would live in
  production: separate machines under separate administration, inside hardware security modules
  or secure enclaves.

## How it is tested

- **Against outside references.** Every from-scratch implementation is checked against published
  test vectors or an independent implementation: the BIP340 and BIP341 vectors, the RFC 9591
  FROST vectors, the NIST ACVP vectors for ML-DSA, ML-KEM and SLH-DSA, the RFC 3394 key-wrapping
  vector, and the `cryptography` library as an ECDSA verifier. The Merkle sum tree has no
  published vectors; it is checked by an independent derivation of its root, by a published
  attack that must fail against it, and by property tests.
- **On a real chain.** Settlement tests sign with the three-process cluster, broadcast to Bitcoin
  Core on regtest, and check that the transaction is mined.
- **Property tests** with Hypothesis for secret sharing and the reserves tree.
- **The manual is a test.** Chapters are built with execution errors turned into build failures,
  so a listing that no longer runs, or prints a different number, is caught when the manual is
  rebuilt.
- **Static checks.** `ruff`, and `mypy` in strict mode.

## Repository layout

| Path | Contents |
|------|----------|
| [`src/custody_lab/`](src/custody_lab) | The Python package: `foundations`, `mpc`, `policy`, `trading`, `settlement`, `reserves`, `pq`, and `demo` (the pipeline, the `custody-lab` command and the dashboard server) |
| [`rust/custody-frost/`](rust/custody-frost) | Python binding to the ZF FROST crate |
| [`rust/custody-pq/`](rust/custody-pq) | Python binding to RustCrypto `slh-dsa` |
| [`web/`](web) | The dashboard: Vite, React and TypeScript |
| [`tests/`](tests) | pytest and Hypothesis |
| [`manual/`](manual) | Chapter sources (`.qmd`), the Markdown shown on GitHub (`.md`), and the build settings |
| [`atlas/`](atlas) | The glossary, one entry per concept, and the project records |
| [`scripts/`](scripts) | `regtest.sh` (a standalone regtest node) and `render-manual.sh` |

## Project records

- [`CLAUDE.md`](CLAUDE.md): conventions, toolchain, module status and the decisions log.
- [`atlas/project/build-plan.md`](atlas/project/build-plan.md): the modules, their order and the
  library choices, with the evidence for each.
- [`atlas/project/session-log.md`](atlas/project/session-log.md): what changed in each working
  session, and what was verified.

## Licence

MIT OR Apache-2.0. The texts are in [`LICENSE-MIT`](LICENSE-MIT) and
[`LICENSE-APACHE`](LICENSE-APACHE).
