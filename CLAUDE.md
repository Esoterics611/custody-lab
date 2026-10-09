# custody-lab

This is the authoritative project spine. Update it in the same change as the work it describes.

## Purpose

An institutional digital-asset custody demo and learning lab. It has two outputs of equal weight:

1. A demo that runs end to end.
2. A manual (one PDF per module) plus the `atlas/` knowledge base, together teaching every concept
   the demo uses.

**Depth target: training, initial exposure, and a showcase.** Choose breadth and a working demo
over protocol depth. State results and cite proofs; do not reproduce them. When a topic starts
pulling toward research depth, stop and cut it to a chapter paragraph.

**Assume no cryptography background.** Every term is defined in bold at first use and listed in
`atlas/glossary.md`. A chapter that introduces cryptography or chain mechanics builds it in a
First principles section before the formal treatment, with one toy example per idea asserted
in a cell.

## Writing standard for the manual and atlas

The manual, the atlas and the glossary are teaching material, and they explain at length. The
owner read the earlier, compressed versions and could not follow them (2026-10-08). The general
rule that every line must be short governs chat replies, not these documents. Length comes from
explanation, never from filler: no adjective in place of a fact, no hype word, no sentence that
only introduces the next one. Mathematical depth does not grow: the depth target above still
holds.

Each concept is taught in this order:

1. **The problem**: what goes wrong for a custodian without it, as a concrete case.
2. **The idea in plain words**, without symbols. Where the reader's own work has a counterpart
   (signed exchange API requests, FIX sessions, maker-checker, clearing and netting, a central
   bank ledger), state it and state where it stops holding.
3. **A worked example** with small numbers and every step written out. No "it follows",
   "clearly" or "it can be shown".
4. **The code**: a cell that computes the example, then a sentence on what each printed line shows.
5. **What breaks when it is done wrong**, demonstrated in a cell where possible.
6. **A recap**: what is now known, and which later section uses it.

Rules for every chapter and entry:

- No term is used before it is explained. A forward reference names the chapter and says in one
  clause what the term is.
- No fact without its reason. A fact the text cannot explain is cut or moved to the chapter that
  can.
- Tables summarise what the prose has already explained; a table never carries an explanation
  alone.
- A chapter opens with "What this chapter is for", in plain words, and closes with a Recap.

`manual/chapters/00-orientation.qmd` is the reference example.

## Conventions (non-negotiable)

- **Languages: Python, TypeScript, Rust only.** No C++, Go or other toolchains. A library in another
  language is covered as reading material, not built.
- Python is managed with uv. Monetary values are `Decimal`; convert to integer base units (satoshis)
  only at the chain boundary.
- No `time.sleep` in business logic (enforced by ruff `TID251`). Time is an injected clock.
- The policy engine is default-deny.
- Every module ships with tests. QA is a first-class deliverable. Every educational implementation
  is checked against an external oracle: a published test vector set or an independent verifier.
- Verify that a library exists and does what is claimed before designing around it. Record the
  evidence class (observed / reported / unverified) in `atlas/project/`.
- Label toy implementations **EDUCATIONAL, NOT PRODUCTION**. Where an audited library exists in an
  allowed language, show both the from-scratch version and the library on the same inputs.
- Persistent documentation lives in `atlas/`. `atlas/project/session-log.md` is kept current as part
  of the work.
- Mark time-sensitive facts (company status, regulation, audits, versions) **verify current**.

## Architecture

The demo story: a FIX order is filled, then a settlement instruction is created, then policy
evaluates it, then an MPC threshold signature is produced, then the transaction is broadcast to
regtest, then a proof-of-reserves snapshot is published after each settlement batch.

```
toy exchange ──FIX──▶ trading ──fills──▶ settlement batch (netted)
                                             │ instruction
                                             ▼
                        approvers ──signed approvals──▶ policy engine (default-deny)
                                             │ signed authorisation
                                             ▼
             signer A ◀─┐                coordinator ──FROST rounds──▶ 2 of {A, B, C}
             signer B ◀─┼─ one share each  │ BIP340 signature
             signer C ◀─┘                  ▼
                                      bitcoind regtest ──▶ proof-of-reserves snapshot
                                             │
                          dashboard (TypeScript) ◀── event stream (FastAPI)
```

- **Two quorums, deliberately separate.**
  - Approval quorum: people approve an instruction in the policy engine.
  - Signing quorum: machines hold key shares.
  - A signer refuses any request that lacks the policy engine's signed authorisation.
- **Each signer is its own process holding one share.** No process ever holds the whole key; the
  dashboard shows which process holds which share.

## Repository layout

| Path | Contents |
|------|----------|
| `src/custody_lab/` | Python package, one subpackage per demo module (`foundations`, `mpc`, `policy`, `trading`, `settlement`, `reserves`, `pq`); `demo/pipeline.py` runs all of them end to end, with any signers taken offline before step 7; `demo/redteam.py` plays a reorganised deposit and a misdirected withdrawal on regtest, each against a weak rule then the defence; `demo/parties.py` runs the policy engine and each approver's device in its own process; `demo/ceremonies.py` plays share refresh against a thief and a lost share repaired, with no chain; `demo/day.py` runs a day of deposits, a double spend, two clients trading, netting across them, withdrawals and three refusals, reconciling books with chain after every step; `demo/attacks.py` tries seventeen attacks on the design against the real code, with no chain; `demo/cli.py` is the `custody-lab` command (`run`, `day`, `ceremonies`, `redteam`, `attacks`, `serve`); `demo/server.py` streams runs and attacks to the dashboard and serves recorded runs for replay |
| `tests/` | pytest + Hypothesis |
| `atlas/` | knowledge base; `atlas/index.md` is the index; `atlas/glossary.md` defines every term the manual uses; `atlas/project/` holds the plan, feasibility notes and session log |
| `manual/` | chapter sources; `manual/_quarto.yml` holds the shared settings for both outputs; `manual/chapter-template.qmd` is the template; chapters go in `manual/chapters/NN-slug.qmd`; `00-orientation.qmd` is the plain-language entry point; `manual/demo-walkthrough.md` (plain Markdown, not rendered) walks the operator through one dashboard run; `manual/attack-vectors.md` (plain Markdown) analyses every attack vector found, with its status in the demo. Each chapter builds to a PDF (not committed) and to GitHub Markdown beside its source (`NN-slug.md` and `NN-slug_files/`, committed, so the manual reads and links on GitHub). `manual/links.py` is a Pandoc filter: chapter links per format, "chapter N" auto-links, previous/next lines, heading anchors. `manual/README.md` is the contents page. Code lines wrap; printed output does not, so keep it under 80 characters |
| `rust/custody-frost/` | PyO3 extension over ZF `frost-secp256k1-tr` (DKG, signing, share refresh and repair); a uv workspace member built by maturin on `uv sync` |
| `rust/custody-pq/` | PyO3 extension over RustCrypto `slh-dsa` (FIPS 205); a uv workspace member, like `custody-frost` |
| `web/` | Dashboard: Vite + React + TypeScript. Three tabs: the settlement run (each step as its events arrive, which process holds which share, a switch per signer to take it offline, replay of recorded runs), the attack panel, and a client's balance check. `web/src/reserves.ts` is a second implementation of the Merkle-sum check, run in the browser; `tests/demo/test_browser_verifier.py` drives it under Node through `web/tests/verify-proofs.ts`. `custody-lab serve` serves the build in `web/dist` |
| `scripts/` | `regtest.sh` (start / stop / cli) and `bitcoin-regtest.conf`; `render-manual.sh` (every chapter, or the ones named, to PDF and Markdown) |
| `var/` | local runtime data, gitignored (`var/regtest`; demo runs in `var/demo/<run>/`) |

## Toolchain

| Concern | Choice |
|---------|--------|
| Python | 3.12, uv; default groups `dev` (pytest, hypothesis, ruff, mypy strict) and `docs` (quarto-cli, ipykernel, nbclient, pyyaml) |
| Manual | Quarto 1.10.18 (from the `docs` group) with lualatex from TinyTeX (TeX Live 2026, in `~/.TinyTeX`) |
| Rust | stable via rustup (1.98.1 at setup), `~/.cargo`; maturin 1.15, PyO3 0.29 (abi3-py312) |
| Threshold signing | from-scratch Python (teaching) + ZF `frost-secp256k1-tr` 3.0.0 via PyO3 (demo) |
| Post-quantum | ML-DSA, ML-KEM from `cryptography` (OpenSSL 4.0.2); SLH-DSA from RustCrypto `slh-dsa` 0.1.0 via PyO3 (`signature` pinned to 2.3.0-pre.4); WOTS+/XMSS from scratch; oracle: NIST ACVP vectors |
| FIX | FIX 5.0 SP2 on FIXT.1.1 (`8=FIXT.1.1`, Logon `1137=9`), `simplefix` over asyncio TCP; message shape follows `~/code/fix-client/ROE.md` (no AvgPx) |
| Chain | Bitcoin Core 31.1 in `~/.local/opt/bitcoin-31.1`, symlinked into `~/.local/bin`; regtest, Taproot key-path spends |
| CLI / dashboard | Typer; FastAPI streaming each run's events as NDJSON; Vite 8 + React 19 + TypeScript 6, Node 24 |

**Why Quarto for the manual.**
- Chapters are Markdown (`.qmd`).
- Math goes through LaTeX, which is the reference renderer for the notation in this subject.
- Python cells execute against this project's environment at render time, with `error: false`.
  Every listing in the PDF is code that ran, and a broken listing fails the build. That makes the
  manual part of QA rather than a copy of the code that drifts.
- Callouts (used for the EDUCATIONAL banner), cross-references and per-chapter PDFs are built in.

Runner-up: plain Pandoc + LaTeX. It gives the same math quality, but code does not execute, so
listings can drift from the repo. Quarto's Typst engine is the fallback if TinyTeX is a burden; how
it handles this manual's math has not been checked.

## Commands

```bash
uv sync                                  # environment; also builds rust/custody-frost (needs cargo on PATH)
uv run pytest                            # tests
uv run ruff check && uv run mypy         # lint, types
scripts/render-manual.sh                 # every chapter to PDF and GitHub Markdown; commit the .md and _files
scripts/render-manual.sh manual/chapters/NN-slug.qmd   # one chapter
scripts/regtest.sh start                 # regtest node; data in var/regtest
scripts/regtest.sh cli getblockchaininfo
scripts/regtest.sh stop
uv run custody-lab run                   # the demo once, printed step by step; artefacts in var/demo/<run>/
uv run custody-lab run --offline 1       # the same with signer 1's process stopped before step 7
uv run custody-lab day                   # a day at the custodian, books reconciled with chain; artefacts in var/day/<run>/
uv run custody-lab ceremonies            # share refresh and repair on the signing processes; no bitcoind needed
uv run custody-lab redteam               # two attacks on regtest, each against a weak rule then the defence
uv run custody-lab attacks               # seventeen attacks on the design, each refused; no bitcoind needed
npm --prefix web run build               # type-check and bundle the dashboard into web/dist
uv run custody-lab serve                 # API and built dashboard at http://127.0.0.1:8000
npm --prefix web run dev                 # dashboard dev server; proxies /api to custody-lab serve
```

Figures are matplotlib cells (`#| label: fig-...`), as in the chapter template. Mermaid is not used: in
PDF it needs headless Chrome, and `quarto install chrome-headless-shell` needs `unzip`, which this
host lacks.

## Module status

| # | Module | Code | Chapter | Atlas |
|---|--------|------|---------|-------|
| 0 | Toolchain | done | n/a | n/a |
| 1 | Foundations | done: `ec`, `hashing`, `ecdsa`, `schnorr`, `shamir`; tests pass | rewritten to the writing standard; renders (27 pages) | 6 entries, draft |
| 2 | MPC custody | done: `paillier`, `lindell17`, `frost`, `dkg` (teaching); `cluster` + `rust/custody-frost` (demo signing path); tests pass | rewritten to the writing standard; renders (29 pages) | 8 entries, draft |
| 3 | Key storage (chapter only) | n/a; model cells for key wrapping (RFC 3394 vector), attestation, sealing, side channels, key release | rewritten to the writing standard; renders (20 pages) | 3 entries, draft |
| 4 | Policy and authorisation | done: `model`, `audit`, `authorisation`, `engine`; signers enforce authorisations; tests pass | rewritten to the writing standard; renders (20 pages) | 5 entries, draft |
| 5 | Trading to settlement | done: FIX 5.0 SP2 `trading/fix`; `settlement/` netting, BIP341/BIP86 transactions, regtest node; FROST-signed spends confirm on regtest; tests pass | rewritten to the writing standard; renders (18 pages) | 4 entries, draft |
| – | Demo front ends | done: `custody-lab run`, `day`, `ceremonies`, `redteam`, `attacks` and `serve`; events streamed per run with server timings; dashboard with offline switches, a day at the custodian (books beside chain), key ceremonies, a red team, attack panel, in-browser balance check and replay; tests pass | n/a | n/a |
| 6 | Proof of reserves | done: `merkle_sum`, `snapshot`; `demo/pipeline` runs all nine steps; tests pass | rewritten to the writing standard; renders (16 pages) | 4 entries, draft |
| 7 | Post-quantum | done: `wots` (teaching); `rust/custody-pq` (SLH-DSA); hybrid authorisation tokens; tests pass | rewritten to the writing standard; renders (21 pages) | 6 entries, draft |
| 8 | Industry and regulation (chapter only) | n/a; DvP model cell; the demo's unsettled USD leg measured; fees charged to the client so the custody address holds client coins only | rewritten to the writing standard; renders (17 pages) | 6 entries, draft |
| 9 | Capstone (chapter only) | n/a; runs the signing cluster (any 2 of 3, replay refused) and computes the design's numbers | rewritten to the writing standard; renders (17 pages) | 1 entry, draft |
| 10 | Custody in practice (chapter only) | n/a; cells: one key under two signature rules, the signers refusing a swapped and an expired authorisation, an unbacked credit lowering the reserve ratio | written to the writing standard from sources read 2026-10-09; renders (14 pages) | glossary only (8 terms); notes in `atlas/project/research/` |

Plan, dependencies and estimates: `atlas/project/build-plan.md`.

## Decisions log

Newest first. **Proposed** entries await review; they become **Accepted** or are replaced.

| Date | Decision | Status |
|------|----------|--------|
| 2026-10-09 | The dashboard's balance check is a TypeScript reimplementation of the Merkle-sum verifier on WebCrypto, sharing no code with the Python tree; a test runs it under Node against Python-built proofs, so it is also the tree's cross-language oracle | Proposed |
| 2026-10-09 | The attack panel runs against the real policy engine, signer processes and verifiers, without a chain; an attack that succeeds is reported as accepted, not raised, so a broken defence shows on the panel | Proposed |
| 2026-10-09 | A run can take signers offline: their processes stop before step 7, and the coordinator asks signers 1 and 3 while both run, otherwise any still running. The default run is unchanged, so chapter 0's numbers hold | Proposed |
| 2026-10-08 | The project is open source under MIT OR Apache-2.0 (`LICENSE-MIT`, `LICENSE-APACHE`, standard texts), copyright Esoterics611 | Accepted (owner) |
| 2026-10-08 | Chapters are also built to GitHub Markdown and committed beside their sources, so the manual reads on GitHub; PDFs stay local builds. `manual/links.py` (standard library, a Pandoc JSON filter) rewrites chapter links per format and links every "chapter N" | Accepted (owner) |
| 2026-10-08 | The manual, atlas and glossary follow the writing standard above: each concept explained at length, problem first, with a worked example; chapter 0 is the pilot | Accepted (owner) |
| 2026-10-08 | Chapter figures are matplotlib cells, including the template's; Mermaid is not used, so headless Chrome is not a dependency | Proposed |
| 2026-09-27 | The demo charges each settlement's network fee to the client being settled, so the custody address holds client coins only (MiCA Article 75(7)); a house address spent as a second input is the alternative, left as chapter 8's Exercise 4 | Proposed |
| 2026-09-27 | The server streams a run's events as NDJSON in the `POST /api/runs` response, not server-sent events: `EventSource` sends only GET and reconnects on its own, so a reconnect would start another run | Accepted (owner) |
| 2026-09-25 | SLH-DSA comes from RustCrypto `slh-dsa` via PyO3 in `rust/custody-pq`, not PyPI `slhdsa` | Accepted (owner) |
| 2026-09-25 | Lamport is a chapter illustration, not a module: no published vectors exist | Accepted (owner) |
| 2026-09-25 | Policy authorisation tokens are hybrid: Ed25519 and ML-DSA-65, both required by every signer | Accepted (owner) |
| 2026-09-25 | The Merkle-sum tree has no published test vectors. Its oracles are an independent hashlib derivation of the root, the Hu, Zhang and Guo (2019) attack (which must fail), and Hypothesis properties | Proposed |
| 2026-09-25 | Chapters assume no cryptography background: a First principles section before the formal treatment, every term defined at first use, and `atlas/glossary.md` | Accepted (owner) |
| 2026-09-24 | Dashboard front end is React (Vite `react-ts` template) | Accepted (owner) |
| 2026-09-24 | The Rust extension is a uv workspace member and a runtime dependency of `custody-lab`, so `uv sync` needs a Rust toolchain | Accepted (owner) |
| 2026-09-24 | `docs` dependency group is installed by default so `uv run quarto` works without flags | Accepted (owner) |
| 2026-09-24 | Languages limited to Python, TypeScript, Rust | Accepted (owner) |
| 2026-09-24 | cb-mpc is reading material, not built: C++, no Python binding, patched OpenSSL. See `atlas/project/threshold-signing-feasibility.md` | Accepted (owner) |
| 2026-09-24 | Demo signs with ZF `frost-secp256k1-tr` 2-of-3 via PyO3. That crate is outside the NCC audit scope and is labelled so | Accepted (owner) |
| 2026-09-24 | Local chain is Bitcoin regtest (Taproot key-path spend) | Accepted (owner) |
| 2026-09-24 | Manual toolchain is Quarto with LaTeX | Accepted (owner) |
| 2026-09-24 | FIX via `simplefix`, not QuickFIX (sdist-only on PyPI, C++ build at install) | Accepted (owner) |
| 2026-09-24 | Build a thin end-to-end slice (M0, M1, M2, M4, M5, demo) before deepening | Accepted (owner) |
| 2026-09-24 | Policy approval quorum and signing quorum are separate; signers require a signed authorisation | Accepted (owner) |
