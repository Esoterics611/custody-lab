# Session log

Newest first.

## 2026-10-08: Open-source licence, links between chapters, the manual on GitHub, README

**Changed.**
- Licence (owner's choice): MIT OR Apache-2.0, copyright Esoterics611. `LICENSE-MIT` and
  `LICENSE-APACHE` are GitHub's standard texts (`gh api /licenses/mit`, `/licenses/apache-2.0`)
  with only the MIT year and holder filled in. The licence is declared in `pyproject.toml`
  (`license`, `license-files`), both Rust `Cargo.toml` files and `web/package.json`.
- `manual/links.py`, a Pandoc JSON filter in standard-library Python, registered in
  `manual/_quarto.yml`. It rewrites links to sibling `.qmd` sources to `.pdf` or `.md`, links
  every "chapter N" and "Module N" in running text, adds previous and next lines at the top and
  bottom of each chapter, and in Markdown output puts an `<a id>` before every heading. It is
  in mypy's file list.
- `manual/_quarto.yml` builds a second format, GitHub Markdown, beside each source
  (`manual/chapters/NN-slug.md`, figures in `NN-slug_files/`). All ten chapters are rendered and
  the Markdown is committed; PDFs stay uncommitted.
- `scripts/render-manual.sh` renders every chapter, or the ones named, in both formats.
- `manual/README.md`, the contents page; `README.md` rewritten: the problem, one run in nine steps
  with links to chapters, reading order, prerequisites and commands with expected output, what is
  real and what is a toy, how it is tested, layout, records, licence.
- `atlas/glossary.md`: every "Taught in" pointer is a link to its section. Each atlas entry's "In
  the manual" line links its chapter and each quoted section, and each module heading in
  `atlas/index.md` links its chapter (one-off script, not kept).
- Chapter 0 links the glossary and atlas.
- `CLAUDE.md`: layout, commands, two Accepted decisions.

**Verified.**
- Quarto passes a JSON filter the format (`latex` for PDF, `commonmark` for GitHub Markdown) and
  the input file in `QUARTO_DOCUMENT_FILE` (observed in a scratch project before the filter was
  written).
- `scripts/render-manual.sh`: all ten chapters render in both formats (exit 0).
- Chapter 0's PDF holds 35 links to sibling chapter PDFs (`pymupdf`); its Markdown has 45 heading
  anchors and 34 chapter links.
- A link check over every Markdown file in the repository: 682 relative links, none pointing at a
  missing file or anchor.
- No generated Markdown contains a local path or a personal name (`grep` for `/home/`, `/tmp/`,
  and the account and owner names).
- The built wheel carries `License-Expression: MIT OR Apache-2.0` and both licence files;
  `cargo metadata` reads the licence for both crates.
- `mypy` (strict) and `ruff` are clean on the filter.
- After the push, GitHub's rendered HTML (`gh api .../contents/<file>`, `Accept:
  application/vnd.github.html`): chapter 0 has 71 formulas marked up for maths display, its
  figure, 34 relative chapter links and its heading anchors; the README and chapter 1 show their
  warning boxes. GitHub's licence detection reports Apache-2.0 only, reading one of the two files.

**Found (observed).** Two atlas entries cited headings by shortened names that no longer
matched: `mpc/cggmp.md` ("Production ECDSA libraries") and `settlement/bitcoin-regtest-taproot.md`
("What a key-path signature signs"). Both now name and link the full headings.

**Open.**
- Whether every formula displays correctly on GitHub needs a look in a browser; the HTML only
  shows that GitHub marks each one up for its maths display.
- `pyproject.toml` still names the owner as author, while the licence and history use
  Esoterics611.
- Each chapter rewrite changes headings, so the glossary and atlas links need re-pointing with it.
- Unchanged: the owner's read of chapter 0, the dashboard in a browser, ML-KEM decapsulation
  vectors, three Proposed decisions.

### Deliverables

- The project is open source under MIT OR Apache-2.0, the same licences as the Rust libraries it
  builds on.
- The whole manual reads on GitHub: every chapter is published as a page with its code output
  and figures, and readers can click from chapter to chapter.
- Every mention of another chapter, in the PDFs and on GitHub, is a link, and each chapter ends
  with previous and next links.
- The glossary and the atlas link each term and concept to the section of the manual that
  teaches it.
- The README explains what the project demonstrates and where to start reading, and gives
  commands to install and run it with the expected output.

## 2026-10-08: Writing standard; chapter 0 rewritten as the pilot

**Changed.**
- The owner read the manual and could not follow it. Reading chapter 0, chapter 1 and the atlas
  found five causes: terms used before they were explained (chapter 0's first table used DKG,
  threshold signing, Merkle sum trees and sighash), one sentence where a paragraph was needed,
  facts given without their reason, tables carrying the explanation, and glossary definitions
  built from other undefined terms.
- `CLAUDE.md`: a writing standard for the manual, atlas and glossary. Each concept is taught as
  problem, plain idea with a trading-infrastructure counterpart, worked example, code, failure
  and recap. One Accepted decision.
- `manual/chapters/00-orientation.qmd` rewritten to the standard, from 1,861 to about 10,100 words
  (prose, tables and code). New: Bitcoin in five ideas (ledger, keys, signatures, hash functions,
  transactions and blocks); secret sharing as a line through points with a figure; threshold
  signing worked by hand ($s = k + e d$ on shares 10, 13 and 16, combined to 39 by Lagrange
  weights); nonce reuse solved as two equations; DKG as three lines summed; policy, approvals and
  the authorisation; a compromise table for the two quorums; proof of reserves with the demo's
  tree worked by hand; the nine steps in the pipeline's own order and names. Eleven code cells
  compute the chapter's numbers from `custody_lab` and the `cryptography` library.
- `manual/chapter-template.qmd`: opens with "What this chapter is for", gives the per-concept
  order in First principles, and closes with a Recap.
- `atlas/glossary.md`: ten terms chapter 0 now defines (Custodian, Digital signature, Ledger,
  Node, Partial signature, Policy engine, Quorum, Secret sharing, Threshold signing, Transaction);
  182 in total.

**Verified.**
- Chapter 0 renders to 31 pages (exit 0); no page ends on a heading (`pypdf`). Every cell's
  printed output was read in the PDF: the threshold pairs all combine to 39, the nonce-reuse cell
  recovers 7, netting gives 0.85 BTC and 54,415.925 USD, the fee is 155 vB x 2 = 310 satoshis, and
  liabilities and assets after settlement are both 4.1499969 BTC. The figure and three table
  pages were rasterised (`pymupdf`) and inspected.
- Every bold term in chapter 0 is in the glossary, apart from paragraph labels.
- The template renders (exit 0).
- Facts re-derived from the code, not carried over: policy tiers and checks
  (`policy/engine.py`), the 60-second authorisation lifetime, the four signer checks and nonce
  burning (`mpc/cluster.py`), the leaf layout and alphabetical leaf order (`reserves/merkle_sum.py`),
  the three-way address check (`demo/pipeline.py`, `settlement/chain.py`), and that each run
  starts its own regtest node.

**Found (observed).** Quarto (`project: type: default`) leaves links to other `.qmd` files
unchanged in both PDF and GitHub Markdown output. A standard-library Python JSON filter, tested in
a scratch project, rewrites them to `.pdf` and `.md`; Quarto passes it `latex` and `commonmark`
as the format. Section links still fail in Markdown output, which drops heading ids.

**Open.**
- The owner reads chapter 0 before chapters 1 to 9, the atlas and the glossary are rewritten.
- Links between chapters and a full README, both requested; plan pending.
- The dashboard in a browser; ML-KEM decapsulation vectors; three Proposed decisions.

### Deliverables

- The manual has a written standard for explanation: every concept starts from the problem it
  solves, is explained in plain words, and is worked through by hand before any code.
- The orientation chapter is rewritten to that standard and now teaches Bitcoin, keys,
  signatures, key splitting, threshold signing, approvals and proof of reserves from nothing,
  with every number computed by code at build time.
- The chapter shows by hand, with numbers under 100, how two of three machines produce the
  signature of a key that none of them holds.
- The glossary gains ten basic terms the manual previously used without defining.

## 2026-10-08: Build plan brought current; figures are matplotlib, Mermaid dropped

**Changed.**
- `atlas/project/build-plan.md`: M6 and M7 are marked done on 2026-09-25 with what each delivers.
  The M7 row names RustCrypto `slh-dsa` instead of calling the SLH-DSA choice open. The M0 and
  `quarto-cli` rows no longer list Mermaid as a blocker.
- `manual/chapter-template.qmd`: the Mermaid block is replaced by a matplotlib figure cell, which
  is what every chapter already uses.
- `CLAUDE.md`: Toolchain status is done; the note under Commands says figures are matplotlib and
  why Mermaid is not used; the Quarto rationale no longer counts Mermaid; one Proposed decision.

**Verified.**
- No `{mermaid}` block exists in `manual/chapters/*.qmd` (`grep`).
- The template renders to a 4-page PDF (exit 0), the figure caption on page 2. The figure cell was
  rendered to PNG and inspected; the first version clipped the boxes at the bottom edge, fixed
  with `set_ylim`.

**Open.**
- The dashboard has not been viewed in a browser. Playwright's cached Chromium
  (`~/.cache/ms-playwright/chromium_headless_shell-1243`) does not start on this host:
  `libnspr4.so` is missing.
- ML-KEM decapsulation vectors; the three Proposed decisions.

### Deliverables

- The build plan records all ten modules as done, including proof of reserves and post-quantum,
  with the libraries actually chosen.
- The chapter template draws its example diagram with matplotlib, so a new chapter renders to PDF
  on this host without a browser installed.
- The Mermaid-in-PDF blocker is closed: no chapter uses Mermaid, and the template no longer does.

## 2026-09-27: Fees charged to the client; no house coins at the custody address

**Changed.**
- `demo/pipeline.py`: `HOUSE_BUFFER` is removed. The custody address is funded with the clients'
  5.00 BTC only, and the settlement's network fee is debited from the settled client's balance
  with the delivered amount. The docstring states why (MiCA Article 75(7)).
- `tests/demo/test_pipeline.py`: the reserve ratio must now equal 1, and the snapshot's assets
  must equal its liabilities.
- Chapter 5: funding and the worked arithmetic move from 5.01 to 5.00 BTC (change 414,999,690
  sats); one sentence names who pays the fee.
- Chapter 6: alpha-capital's balance after settlement is 1.1499969 BTC in the figure, the table,
  the text, the cells and Solution 2; the reserve ratio is exactly 1.
- Chapter 8: the ¶7 row and the walkthrough ("Fees without house coins") describe the new
  behaviour. Exercise 4 now asks for the alternative, a house address spent as a second input.
- Chapter 9: the restart row applies once shares persist. In the demo a restart loses the share
  with the used-token set, so no persistence was added. The production list no longer names
  segregated house funds.
- `atlas/industry/mica.md`, `atlas/capstone/system-design.md`, `CLAUDE.md` (status, one
  Proposed decision).

**Verified.**
- `pytest`: 202 passed; `ruff` and `mypy` clean.
- `custody-lab run` on regtest: funding 5.00 BTC, fee 310 sats, liabilities and assets both
  4.1499969 BTC, reserve ratio 1.00000.
- Chapters 5, 6, 8 and 9 re-render (15, 13, 14 and 14 pages); none ends a page on a heading. The
  printed outputs match the text: chapter 5's custody output of 4.1499969 BTC after settlement,
  chapter 6's ratio of 1.00000, chapter 8's equal assets and liabilities. Chapter 6's tree figure
  was rendered to PNG and inspected with the longer labels.

**Decided.** The two-input design from the previous session's prompt was not built. It needs a
multi-input transaction builder, a second key and a second authorisation, all to keep round
client balances. Charging the fee to the client closes the ¶7 gap with a four-line change, and it
matches common custody practice. Recorded as Proposed in `CLAUDE.md` for the owner.

**Open.** Unchanged from the capstone entry: ML-KEM decapsulation vectors, Mermaid in PDF, the
dashboard in a browser, and the Proposed Merkle-sum oracle decision.

### Deliverables

- The demo no longer keeps the custodian's own coins at the client custody address: each
  settlement's network fee is charged to the client being settled.
- After every settlement batch the custody address now holds exactly what clients are owed, and
  the proof of reserves shows a ratio of exactly 1.
- The manual's figures, worked examples and exercises in chapters 5, 6, 8 and 9 match the new
  behaviour, and every one of them was regenerated by running the code.
- The capstone's failure table now states that the signer-restart replay risk applies only once
  shares survive a restart, which they do not in the demo.

## 2026-09-27: Module 9, capstone

**Changed.**
- Wrote `manual/chapters/09-capstone.qmd` as a design review in question-and-answer form:
  - the brief, the assumptions, and the safety and liveness requirements;
  - a production architecture figure, drawn with matplotlib because Mermaid in PDF is still
    blocked;
  - the eight-step settlement walk, and a table of what each component holds and what its
    compromise gives an attacker;
  - deep dives: threshold signing vs multisig, FROST vs threshold ECDSA, the signer's checks,
    two quorums, hot, warm and cold, the key lifecycle, what clients get, quantum risk;
  - fourteen failure modes with class, detection and response, and seven trade-offs with their
    cost;
  - a numbers cell computed from the libraries, and a walkthrough on the real signing cluster.
- `atlas/capstone/system-design.md`, linked from the index; 9 glossary terms (171 in total).
- Updated chapter 0's reading order, `CLAUDE.md` module status and the build plan. Every module
  in the build plan is now done.

**Verified.**
- Chapter 9 renders to 13 pages; page endings read with `pypdf`, none on a heading. The figure was
  rendered to PNG and inspected before it went into the chapter.
- The numbers cell printed: 155 vB and 310 sats for a one-input settlement (the fee chapter 6's
  demo paid), 58 vB per further key-path input, a 1,984-byte authority key, a 7,047-byte
  serialised token, and 20 siblings for a million clients.
- The walkthrough ran the real cluster: signers {1, 3} and {2, 3} each produced a valid 64-byte
  signature under one group key; the first token replayed to {1, 2} was refused by signer 1.
- Every glossary pointer names a heading in its chapter. Chapter 0 re-renders.

**Found (observed in `mpc/cluster.py`).** Each signer keeps its used-authorisation set in process
memory. A restart empties it, and in a cluster with $n \ge 2t$ two disjoint signer sets can each
honour one token. Both are bounded by the token's expiry and by its naming one exact message; the
chapter lists them as failure modes, and Exercise 3 works the second. The code is unchanged.

**Open.**
- ML-KEM decapsulation vectors remain unchecked. Checking them needs a second implementation that
  loads expanded decapsulation keys, such as RustCrypto `ml-kem` bound through `custody-pq`.
- Mermaid in PDF still needs `unzip` on this host.
- The dashboard has not been viewed in a browser.

### Deliverables

- Chapter 9 presents the whole custody system as a design review: the brief, the architecture,
  the reasoning behind each major choice, and what each choice costs.
- A diagram shows where every key lives in a production deployment, with shares at three
  independent sites and one of them offline.
- A table of fourteen failure modes gives, for each, whether money or only availability is at
  risk, how it is detected, and the response.
- The chapter's figures (transaction sizes, fees, token and proof sizes) are computed from the
  project's own code when the manual is built, not quoted.
- Running the real signing processes, the chapter shows that any two of the three signers can
  sign for the same key, and that a reused approval token is refused.

## 2026-09-27: Module 8, industry and regulation

**Changed.**
- Wrote `manual/chapters/08-industry.qmd`:
  - First principles: four forms of money on a ledger, DvP with an atomic-settlement model cell,
    settlement finality, public and permissioned ledgers;
  - Formal treatment: tokenised funds and collateral, Canton and Kinexys, Agorá and mBridge, MiCA
    Article 75 paragraph by paragraph, US qualified-custodian rules and recent changes, SOC
    reports, and Israel (public sector, companies, researchers);
  - worked example: the demo against MiCA Article 75;
  - walkthrough: the demo's two settlement legs (0.85 BTC on chain, USD 54,415.925 never settled)
    and the custodian's fee buffer commingled with client coins at the custody address.
- Six atlas entries under `atlas/industry/`, linked from the index; 21 glossary terms (162 in
  total).
- Updated chapter 0's reading order, `CLAUDE.md` module status and the build plan.

**Verified.**
- Chapter 8 renders to 13 pages; every cell ran and printed the values the text states. Page
  endings read with `pypdf`: none ends on a heading. Chapter 0 re-renders.
- Every glossary pointer names a heading in its chapter.
- Primary sources read: the BIS Agorá press release of 27 May 2026 (eight central banks, the
  Bank of Canada having joined the original seven; atomic multi-currency settlement in a
  prototype; real-value testing next; no production timeline); MiCA Article 75 text.
- Reported by secondary sources and marked **verify current** in the chapter: tokenised Treasury
  products about USD 15 billion; CFTC tokenised-collateral guidance; Canton and Broadridge DLR
  volumes; the DTCC Canton plan; Kinexys volumes and JPMD on Base; mBridge membership; the MiCA
  transition ending 1 July 2026; the SEC safeguarding withdrawal, SAB 122 and the state trust
  company no-action letter; GENIUS Act timing; the CLARITY Act cloture vote failing on
  15 September 2026; the digital shekel timeline; Sela and Icebreaker; Project Eden; the Israeli
  acquisitions; researcher affiliations.

**Decided.** Single-fund figures (BUIDL) are left out: two sources a month apart gave USD 2.8
billion and USD 5 billion. The chapter cites the market aggregate only.

**Open.**
- The demo breaches MiCA Article 75(7) by design: its fee buffer shares the custody address with
  client coins. The chapter describes the fix (Exercise 4); the pipeline is unchanged.

### Deliverables

- Chapter 8 explains the four kinds of money now issued as tokens: bank deposits, stablecoins,
  money market fund shares and central bank money. It sets out what the holder of each actually
  owns.
- It describes the institutional networks (Canton, Kinexys) and the central bank projects
  (Agorá, mBridge) as of September 2026, with every fact that can change marked for re-checking.
- It sets out the EU's custody duties under MiCA and the US qualified-custodian rules, and maps
  each duty onto the demo's controls.
- It shows, with the demo's own code, that the demo settles only the bitcoin side of a trade and
  keeps the custodian's own coins at the client address. Both are gaps a regulated custodian
  would have to close.
- It maps Israel's part in the field: the Bank of Israel's digital shekel and experiments, Project
  Eden, the MPC custody companies founded in Israel, and the Israeli researchers whose protocols
  the demo teaches.

## 2026-09-27: Module 3, key storage

**Changed.**
- Wrote `manual/chapters/03-key-storage.qmd`, a chapter with no module:
  - First principles: three questions for any key store, key wrapping, tamper response and the
    FIPS 140-3 levels, remote attestation, sealing, side channels;
  - Formal treatment: HSMs (PKCS#11, key ceremonies), TEEs (SGX, SEV-SNP and TDX, Nitro
    Enclaves, interposer attacks), MPC as a storage choice, combinations, a comparison table;
  - worked example: where each part of the demo would live in production;
  - walkthrough: a key share released over ML-KEM only to an enclave whose report carries the
    reviewed measurement and binds the requester's public key.
- Three atlas entries under `atlas/storage/`, linked from the index. 26 glossary terms (141 in
  total); the chapter 6 "Attestation" row now points to "Remote attestation", and the Txid row's
  second pointer gained its missing "5 FP" prefix.
- Updated chapter 0 (reading order, what is real), `CLAUDE.md` module status and the build plan.

**Verified.**
- Chapter 3 renders to 16 pages. Every cell ran; the key-wrapping cell reproduces the RFC 3394
  section 4.1 vector, and the release cell refuses a patched build and a substituted public key.
  Page endings read with a throwaway `pypdf`: none ends on a heading.
- Chapter 0 re-renders.
- Every glossary pointer names a heading in its chapter (a scratchpad script over all chapters).
- Facts checked by web search, each marked in the chapter:
  - FIPS 140-2 certificates moved to the historical list on 21 September 2026 (reported);
  - AWS CloudHSM `hsm2m.medium` and Azure Managed HSM at FIPS 140-3 Level 3 (reported);
  - Nitro Enclaves isolation, PCR0 and PCR8, KMS condition keys (**observed** in AWS
    documentation);
  - SGX deprecated on client processors from 11th-generation Core, continued on Xeon (reported);
  - WireTap, Battering RAM, TEE.fail and DDRop (September 2026, ACM CCS 2026), with Intel's and
    AMD's statements that interposer attacks are out of scope (reported);
  - PKCS#11 3.2 approved as an OASIS Standard in 2026, with ML-KEM, ML-DSA and SLH-DSA
    (reported);
  - SP 800-186 allows secp256k1 for blockchain-related applications (reported);
  - NIST IR 8214C threshold call taking submissions, no standard yet (reported);
  - Fireblocks: MPC-CMP shares and policy engine in SGX across clouds (reported by Fireblocks).

**Open.**
- Vendor-specific claims about programmable HSMs and BIP340 support are left general and marked
  **verify current**; no vendor documentation was read.

### Deliverables

- Chapter 3 compares the three places a custody key can live: a hardware security module, a
  processor enclave, and shares spread across machines.
- For each option, the chapter states where the key exists, who can make it sign, what an
  outsider can verify, and which attacks it does not stop.
- It covers the memory-bus attacks on processor enclaves published between late 2025 and
  September 2026, which the chip makers place outside their protection.
- A worked example places every key in the demo where a production deployment would keep it.
- A model walkthrough hands a key share only to a machine that proves, by attestation, that it
  runs the reviewed signer code.

## 2026-09-27: Demo front ends

**Changed.**
- `demo/cli.py` is the `custody-lab` command (`[project.scripts]`):
  - `run` runs the demo once and prints each step, its details (cut to the terminal width) and
    the summary;
  - `serve` starts uvicorn on the server app.
- `demo/server.py`:
  - `POST /api/runs` runs `pipeline.run` on a worker thread in a fresh `var/demo/<run>/` and
    streams its events in the response as NDJSON;
  - `GET /api/steps` lists the steps;
  - `web/dist` is served at `/` when it has been built;
  - there is no limit on concurrent runs.
- `demo/pipeline.py`:
  - `new_workdir` names each run directory by its UTC start time;
  - a step that raises is reported as a `failed` event, which also lands in `events.jsonl`,
    before the exception propagates.
- `web/`: the Vite starter is replaced by the dashboard:
  - a Run button and nine step rows with status and details;
  - fills and signers as tables, and the FIX transcript collapsed;
  - a key-shares panel mapping each share to its process ID and marking the two signers;
  - light and dark themes, and a dev proxy from `/api` to port 8000.

  The starter assets are removed and `web/README.md` is rewritten.
- Tests:
  - `tests/demo/test_front_ends.py` (5 tests) drives the CLI and the server against stand-ins
    for `pipeline.run`. They share one file because mypy rejects a second `conftest.py` in a test
    tree without `__init__.py`;
  - `test_pipeline.py` adds a regtest test in which the FIX step raises.
- Updated `CLAUDE.md` (layout, commands, module status, one Accepted decision), the build plan's
  demo slice row, and chapter 0 (how to run the demo, where the code is).

**Verified.**
- `pytest`: 202 passed, up from 196. `ruff` and `mypy` are clean (60 files).
- `npm --prefix web run build` (tsc and vite) and `oxlint` pass.
- One real run through `custody-lab serve`:
  - `POST /api/runs` streamed running and done for all nine steps;
  - shares 1 to 3 were held by three processes, and signers 1 and 3 signed;
  - the settlement had one confirmation, and the reserve ratio was 1.00241;
  - the run directory holds `events.jsonl`, `audit.jsonl` and `reserves/`;
  - `/` served the built dashboard.
- Two real runs posted at the same time both completed all nine steps, each with its own signer
  processes, settlement transaction and run directory.
- Chapter 0 renders to 7 pages. Page endings were read with a throwaway `pypdf` (this host has no
  rasteriser); none ends on a heading.

**Decided (owner).** Runs stream as NDJSON in the `POST /api/runs` response, not as server-sent
events.

**Open.**
- The dashboard has not been viewed in a browser: this host has no headless browser. Only the
  type check, the bundle and the served HTML were checked.
- Starlette 1.7.0 warns that its test client's use of `httpx` is deprecated in favour of `httpx2`
  (**observed** in the pytest warnings). Not acted on.
- Chapters 3, 8 and 9. ML-KEM decapsulation vectors. Mermaid in PDF still needs `unzip`.

### Deliverables

- The demo runs from one command, `custody-lab run`, which prints each step of the custody flow as
  it happens.
- A browser dashboard starts a run and shows all nine steps live, from the FIX trading session to
  the proof-of-reserves snapshot. It shows which operating-system process holds each key share
  and which two signed.
- `custody-lab serve` serves the dashboard and its API from one process. Each run gets its own
  private Bitcoin chain and signer processes; two runs at once both settled.
- A step that fails is reported by name on the dashboard, in the command-line output and in the
  run's event log.
- 202 tests pass. A manual run through the server settled a transaction on the private chain with
  one confirmation.

## 2026-09-25: Module 7, post-quantum

**Changed.**
- `rust/custody-pq`: a PyO3 binding to RustCrypto `slh-dsa` 0.1.0 covering all 12 FIPS 205
  parameter sets. It exposes key generation (random and from seeds), and sign and verify in both
  the internal form and the context form. It is a uv workspace member and a runtime dependency.
  `signature` is pinned to `=2.3.0-pre.4`, because cargo otherwise picks pre.7, which does not
  compile with this `slh-dsa`.
- `src/custody_lab/pq/wots.py` (EDUCATIONAL) implements the FIPS 205 pieces for
  SLH-DSA-SHA2-128f:
  - address (ADRS) and its compressed form;
  - SHA-256 tweakable hashes and hash chains;
  - WOTS+ key generation, signing and public-key recovery, with the checksum;
  - XMSS nodes, signing and root recovery;
  - the SLH-DSA public root.
- Hybrid authorisation tokens (`policy/authorisation.py`):
  - `AuthorityKey` holds an Ed25519 key and an ML-DSA-65 key;
  - every token carries both signatures, the ML-DSA one with context
    `custody-lab/authorisation`;
  - `check` requires both;
  - `PolicyEngine`, the pipeline, every test and the chapter 2, 4 and 5 cells use it.

  Chapter 4's authorisation section is updated to match.
- `tests/pq/vectors/acvp-subset.json` holds 46 NIST ACVP vectors from `usnistgov/ACVP-Server`
  commit `a7f283c`, with the SHA-256 of each source file and the selection rule. New tests:
  - `tests/pq/test_pq_vectors.py`: ML-DSA key generation and verification, ML-KEM key generation,
    SLH-DSA key generation for all 12 parameter sets, verification, deterministic signing, and
    hedged signing;
  - `tests/pq/test_wots.py`: the public root against 10 NIST cases and against RustCrypto on
    fresh seeds, XMSS round trips, and the checksum defeating a chain advance;
  - `tests/policy/test_authorisation.py`: a token with only one valid signature is rejected.
- Wrote `manual/chapters/07-post-quantum.qmd`:
  - First principles: what a quantum computer breaks, Lamport with a forgery after reuse,
    Winternitz chains and the checksum, XMSS and SLH-DSA, one-bit LWE;
  - Formal treatment: ML-KEM, ML-DSA (Fiat-Shamir with aborts), SLH-DSA, a size table, the hybrid
    token;
  - threshold post-quantum signatures, migration design, and walkthroughs for the libraries, an
    ML-KEM share backup and the hybrid token.
- Six atlas entries under `atlas/pq/` and 19 glossary terms (115 in total). Also updated:
  - the orientation chapter (reading order, what is real);
  - `CLAUDE.md` (layout, toolchain, module status, three Accepted decisions);
  - the build plan's SLH-DSA row.

**Verified.**
- `pytest`: 196 passed, up from 134. `ruff` and `mypy` are clean (57 files).
- Teaching WOTS+/XMSS reproduces PK.root for all 10 NIST SLH-DSA-SHA2-128f keyGen cases on the
  first run, and matches RustCrypto on fresh seeds.
- RustCrypto `slh-dsa` matches NIST on the following (**observed**):
  - key generation, 21 cases over all 12 parameter sets;
  - verification, 2 pass and 1 fail as expected;
  - a deterministic signature, byte for byte.
- `cryptography` ML-DSA matches NIST key generation for 44, 65 and 87, and verification including
  2 rejected cases. ML-KEM-768 and -1024 match NIST key generation.
- All chapters render. Chapters 2, 4, 5 and 6 were re-rendered with hybrid tokens, and chapter 6
  runs the full demo with them. Chapter 7 renders to 18 pages. No page in any chapter ends on a
  heading.
- Every glossary section pointer resolves.
- Citations checked by web search:
  - Threshold Raccoon (EUROCRYPT 2024, ePrint 2024/184);
  - Trilithium (ePrint 2025/675) and Quorus (ePrint 2025/1163);
  - BIP 360 Pay-to-Merkle-Root, merged 2026, and BIP 361 (reported by news sites; **verify
    current**);
  - NIST IR 8547 draft dates, 2030 and 2035 (**verify current**).

**Decided (owner).** RustCrypto `slh-dsa` via PyO3; Lamport as an illustration only; hybrid
authorisation tokens.

**Open.**
- ML-KEM decapsulation vectors are not checked: `cryptography` loads ML-KEM private keys only from
  seeds, and those vectors give expanded keys.
- Approvals, proof of control and settlements remain classical.
- Chapters 3, 8 and 9.

### Deliverables

- The custody signers now require every policy authorisation to carry both an Ed25519 and an
  ML-DSA-65 signature. A forger would have to break both a classical and a post-quantum scheme.
- SLH-DSA, ML-DSA and ML-KEM are in the project and checked against NIST's official ACVP test
  vectors. SLH-DSA comes from a Rust library bound the same way as the FROST signer.
- A from-scratch WOTS+ and XMSS implementation reproduces NIST's SLH-DSA public keys exactly, as
  the teaching version of hash-based signatures.
- Chapter 7 covers the following, with every example executed at build time:
  - what a quantum computer breaks;
  - how hash-based and lattice signatures work from first principles;
  - why they resist threshold signing;
  - the order in which a custodian should migrate.

## 2026-09-25: Module 7 library survey

**Changed.** Updated the library status table in `atlas/project/build-plan.md` with the
post-quantum survey. No code changed.

**Verified.**
- `cryptography` 50.0.1 (OpenSSL 4.0.2) exposes ML-DSA-44/65/87 and ML-KEM-768/1024 with
  seed-based key generation. ML-DSA-65 and ML-KEM-768 round trips ran here with FIPS 203/204
  sizes.
- It has no SLH-DSA module.
- PyPI `slh-dsa` 0.2.5 imports as `slhdsa` with all 12 parameter sets.
- `pqcrypto` 1.0.0 still ships empty algorithm packages here.
- NIST ACVP vectors exist for all three standards. The SLH-DSA keyGen file gives seeds and the
  expected public key.

**Open.** SLH-DSA library choice, and whether Lamport is a module or a chapter illustration.
Whether the demo moves its authorisation tokens to hybrid Ed25519 + ML-DSA. All three wait on
the owner.

## 2026-09-25: Module 6, proof of reserves; first commit

**Changed.**
- First commit, `489194e`: everything up to the previous entry. Rendered PDFs are now ignored
  (`manual/.gitignore`).
- Reviewed the uncommitted Module 6 code from 2026-09-24 before changing it:
  - `reserves/merkle_sum.py` hashes both children's sums into each parent and rejects negative
    sibling sums;
  - `reserves/snapshot.py` signs a tagged hash of the canonical statement;
  - `PolicyEngine.authorise_attestation` issues a token for that message without approvals.

  No defects found. No source file changed.
- Tests added, 9 in total:
  - `tests/reserves/test_merkle_sum.py`: the root against an independent hashlib derivation;
    Hypothesis over arbitrary ledgers; altered balance, salt, id and negative sibling; the Hu,
    Zhang and Guo total-only attack, passing a total-only tree and failing this one;
  - `tests/reserves/test_snapshot.py`: the published file verifies with the standard library and a
    BIP340 verifier; an attestation token signs its attestation and is refused for a sighash;
  - `tests/demo/test_pipeline.py` (regtest): all nine steps complete, the snapshot signature
    verifies, and the snapshot's audit head is in the exported log.
- Wrote `manual/chapters/06-reserves.qmd`:
  - First principles: hash trees, sum trees, the total-only attack, salts and leaks, proof of
    control with domain separation, and what a proof of reserves does not show;
  - Formal treatment: the leaf and node layout, verification, the snapshot, and a zero-knowledge
    section without code (Pedersen commitments, range proofs, Provisions, DAPOL+);
  - the worked example on the demo's ledger, and a code walkthrough that runs the whole demo and
    verifies the published snapshot from the file.
- Added four atlas entries under `atlas/reserves/` and 14 glossary terms (96 in total). Also
  updated:
  - the orientation chapter (chapter 6 in the reading order);
  - the audit-trail atlas entry (the head is now anchored);
  - `CLAUDE.md` module status and layout, and one **Proposed** decision on the Merkle-sum test
    oracle.

**Verified.**
- `pytest`: 134 passed, up from 125. `ruff` and `mypy` are clean (54 files).
- The pipeline, run from a file, completed all nine steps:
  - 0.85 BTC settled with one confirmation and a 310-sat fee;
  - liabilities 4.15 BTC, assets 4.1599969 BTC, reserve ratio 1.00241;
  - all inclusion proofs and the proof-of-control signature verify.

  Run from stdin, it failed when the signer processes started. Inferred, not confirmed: `spawn`
  re-imports `__main__`, which stdin cannot provide.
- Chapter 6 renders to 13 pages and runs the full demo on regtest during the build. Its pages were
  rasterised and inspected; no page in chapters 0 or 6 ends on a heading.
- Every chapter section cited in the glossary exists.
- Citations checked by web search:
  - Hu, Zhang and Guo, *Computers & Security* 2019, ePrint 2018/1139 (reported);
  - Dagher et al., CCS 2015;
  - Ji and Chalkias, CCS 2021;
  - Chalkias, Chatzigiannis and Ji, ePrint 2022/043.

  The `dapol` Rust crate is reported by the same search (GitHub, docs.rs) and was not built.

**Decided.**
- Chapter 6 covers zero-knowledge proofs of liabilities as a section with no code, as the build
  plan says.
- The Merkle-sum test oracle is recorded as Proposed in `CLAUDE.md`.

**Open.**
- The pipeline has no CLI or dashboard entry point; the docstring describes both.
- The Mazars pause and exchange zk-SNARK proofs in chapter 6 are marked **verify current**.
- The remaining modules: key storage (chapter 3), post-quantum (Module 7), industry (Module 8)
  and the capstone.

### Deliverables

- The repository has its first commit, with rendered PDFs excluded.
- Proof of reserves works end to end. After each settlement the demo publishes the following,
  and a third party can verify the file with the standard library and a BIP340 verifier:
  - a Merkle-sum commitment to client liabilities;
  - the custody key's on-chain balance;
  - a 2-of-3 FROST proof-of-control signature;
  - the anchored policy audit head.
- New tests show that the liabilities tree resists the published attack on total-only sum trees,
  and that an attestation authorisation cannot be used to sign a transaction.
- Chapter 6 teaches the topic from first principles and runs the whole demo during its build.
  Four atlas entries and 14 glossary terms cover the topic.

## 2026-09-25: First principles in chapters 2 and 5, glossary, depth rule

**Changed.**
- Chapter 2 has a new "First principles" section with seven subsections:
  - MPC, parties, rounds, the coordinator, broadcast and private channels;
  - three ways to split a key: Shamir, additive, multiplicative;
  - adversary models: corrupted, semi-honest and malicious parties, static and mobile
    adversaries, abort and identifiable abort, UC security;
  - commitments: hiding, binding, hash and point commitments, Feldman commitments on the toy
    curve;
  - zero-knowledge proofs, with chapter 1's forgery as the reason a transcript reveals nothing;
  - Paillier's homomorphism on a toy key with $N = 35$;
  - concurrent sessions: the ROS attack and FROST's binding factor.
- Five new cells in chapter 2. `dkg.check_round1` rejects a rogue-key commitment, and every toy
  number is asserted. Other chapter 2 changes:
  - "MPC" is expanded at first use and safe primes are defined;
  - Exercises 6 (classify semi-honest and malicious actions) and 7 (Feldman binding) are added,
    with an asserted solution for 7;
  - Paillier 1999, Feldman 1987, Drijvers et al. 2019 and Benhamouda et al. 2021 are added to
    further reading.
- Chapter 5 has a new "First principles" section with four subsections:
  - UTXOs against an account ledger: inputs, outputs, outpoint, txid, change, fee, satoshis,
    dust;
  - locking scripts and witnesses: Taproot key and script paths, addresses, SegWit;
  - what the sighash covers, plus locktime and sequence;
  - mempool, blocks, proof of work, confirmation, regtest and coinbase maturity.

  One offline cell builds the worked example's transaction, shows `check_matches` refusing the
  transaction with its change output removed (fee 416,000,000 sats), and shows that one satoshi
  more to the payee changes the sighash.
- Chapter 4: "canonical" is defined at the start of "Canonical encoding". Its other terms map onto
  pre-trade risk checks and are defined where used, so it has no First principles section.
- `atlas/glossary.md` has 82 terms, each with one sentence and the chapter section that teaches
  it. It is linked from `atlas/index.md` and the orientation chapter.
- `manual/chapter-template.qmd` has a "First principles" section.
- `CLAUDE.md` changes:
  - new rule "Assume no cryptography background";
  - a decision-log row (accepted by the owner this session);
  - the glossary added to the layout table;
  - chapter page counts updated.

**Verified.**
- All five chapters render: orientation 7 pages, chapter 1 20, chapter 2 22, chapter 4 12,
  chapter 5 15. Chapter 5 still confirms a regtest transaction during the build.
- New cell output appears in the PDFs:
  - "rejected: participant 3: bad proof of knowledge";
  - "no change output: fee 416000000 sats outside [0, 10000]".
- A text scan of all five PDFs finds no page whose last line is a heading.
- Chapter 2's and chapter 5's new pages were rasterised and inspected.
- A script confirmed that every chapter section title cited in the glossary exists.
- `pytest`, `ruff` and `mypy` were not run; no source file changed.

**Found and fixed.**
- Chapter 2's split table hyphenated "Multiplicative". Widened the column.
- The first wording of the depth rule required a First principles section in every chapter, which
  chapter 4 does not need. The rule now requires the section where a chapter introduces
  cryptography or chain mechanics.

**Open.**
- The uncommitted, untested `demo/pipeline.py` and `reserves/` work noted in the previous entry is
  unchanged. `CLAUDE.md` still lists Module 6 as a skeleton.
- The atlas entries' Definition lines still use compressed wording; the glossary covers the terms.
- Nothing is committed.

### Deliverables

- Chapter 2 now teaches, before its formal treatment:
  - what a multi-party protocol is;
  - the attacker models its security claims rest on;
  - commitments, zero-knowledge proofs and homomorphic encryption;
  - why many concurrent signing sessions are an attack surface.
- Chapter 5 now explains Bitcoin's transaction model from the ground up: coins as outputs, change
  and fee, locking scripts and witnesses, the sighash, and confirmation.
- A new glossary defines 82 terms in one sentence each and points to the section that teaches
  each one.
- The manual's standing rule now assumes no cryptography background. The chapter template carries
  a First principles section for future chapters.
- All five chapters render with every new example asserted by executed code.

## 2026-09-25: Orientation chapter, first principles in chapter 1

**Changed.**
- Added `manual/chapters/00-orientation.qmd`, with no code cells. It covers:
  - the demo's nine steps in plain words, each with the idea it rests on and the chapter that
    teaches it;
  - the two quorums;
  - trading-infrastructure counterparts and where each analogy breaks;
  - terms with a different meaning here (nonce, share, commitment, settlement);
  - which components are real and which are toys;
  - reading order.
- Chapter 1 has a new "First principles" section before the formal treatment. It starts from
  school algebra:
  - modular arithmetic and inverses;
  - the four group rules;
  - the cycle of multiples of $G$: generator, order, scalar, and the two moduli;
  - double-and-add and the discrete logarithm;
  - Schnorr identification: what the nonce hides, why the commitment comes first, key recovery
    from a reused nonce, a forgery when the challenge is known in advance, then Fiat-Shamir;
  - Shamir sharing as a line through points.
- Six new cells assert every number in that prose. The learning objectives are reworked.
  Exercise 6 (forge with a known challenge) has an asserted solution. Schnorr 1991 and
  Fiat-Shamir 1986 are added to further reading.
- `manual/_quarto.yml`:
  - the `Highlighting` redefinition is guarded, so a chapter without code blocks renders;
  - section and subsection headings reserve 16 and 9 lines, so no heading is left at a page foot
    above a table.

**Verified.**
- All five chapters render:
  - orientation, 7 pages;
  - chapter 1, 20 pages (was 12);
  - chapter 2, 15 pages;
  - chapter 4, 12 pages;
  - chapter 5, 11 pages, and it still settles a regtest transaction during the build.
- Chapter 1's new cells check:
  - the group rules on all 31 elements of the toy curve;
  - the 31-step cycle, by repeated addition;
  - key recovery from a reused nonce;
  - the forged commitment $(21, 18)$.
- Orientation and chapter 1 pages were rasterised and inspected. A text scan of all five PDFs
  finds no page whose last line is a heading.
- `pytest`, `ruff` and `mypy` were not run; no source file changed.

**Found and fixed.**
- The orientation chapter failed to render. The shared header redefines `Highlighting`, which
  pandoc defines only in a document with a code block.
- Orientation table columns were sized by header length. Widths are now set in the separator
  rows.
- Headings were stranded at the page foot above a long table. The first subsection threshold
  exceeded what a section check leaves after its own heading, which recreated the fault below
  a section heading. Thresholds of 16 and 9 lines avoid it.

**Observed, not changed.**
- The following were modified at 20:40-20:41 on 2026-09-24, after the previous log entry:
  - `src/custody_lab/demo/pipeline.py`;
  - `src/custody_lab/reserves/`;
  - `policy/engine.py`, which gained `authorise_attestation` and now imports
    `reserves.snapshot`.

  They have no tests and no log entry. The pipeline imports.
- Mermaid is still blocked. `unzip` is absent, and Quarto's `chrome-headless-shell` directory is
  empty.
- Nothing in the repository is committed; `master` has no commits.

**Open.**
- Plan items 3 to 6 wait for review of chapter 1's depth and tone:
  - chapter 2 background (adversary models, commitments, zero-knowledge proofs, homomorphic
    encryption, concurrent sessions);
  - chapter 5's Bitcoin transaction model;
  - `atlas/glossary.md`;
  - the template section and the `CLAUDE.md` depth rule.

### Deliverables

- A new orientation chapter traces one settlement through the demo in plain words. For each step
  it names the idea the step rests on and the chapter that teaches it.
- Chapter 1 now teaches its vocabulary from school algebra before any notation: modular
  arithmetic, groups, generator and order, the discrete logarithm, what a signature's nonce and
  commitment do, and Shamir sharing as a line through points.
- Every number in the new material is computed on the toy curve and asserted by code that runs
  when the chapter renders.
- All five chapters render under the shared configuration, which now handles chapters without
  code and keeps headings with the tables that follow them.

## 2026-09-24: Module 5, trading to settlement

**Changed.**
- `src/custody_lab/trading/fix.py`: FIX 5.0 SP2 on FIXT.1.1. `8=FIXT.1.1`; Logon
  `98=0 108=30 1137=9`; NewOrderSingle; fills with 150=F 39=2 32/31 14 151 75 60 and no AvgPx;
  MsgSeqNum checked. The toy exchange fills at the limit price. `trade()` also works from inside a
  running event loop.
- `src/custody_lab/settlement/`:
  - `netting.py`: `Decimal` netting.
  - `bitcoin.py`: BIP86 tweak, BIP341 `sig_msg`/`taproot_sighash` for all hash types, BIP144
    serialization, parser, exact BTC-to-sats conversion.
  - `transfer.py`: one-input spend, smallest sufficient UTXO, dust to fee. `check_matches`
    checks exact payment, change only to custody, and a fee cap computed from input minus
    outputs.
  - `regtest.py`: a private `bitcoind` on free ports, readiness via `bitcoin-cli -rpcwait`, and
    JSON-RPC with `Decimal` amounts.
  - `chain.py`: descriptor-derived address, `validateaddress`, `scantxoutset rawtr(...)`.
- `rust/custody-frost`: `taproot_output_key`; `sign`/`aggregate` take `taproot=True`
  (`sign_with_tweak`/`aggregate_with_tweak`). `SigningCluster.sign(..., taproot=True)` and
  `taproot_output_key()` pass them through.
- Added a `regtest` pytest marker and a mypy override for `simplefix`.
- Wrote chapter 5, which settles a real transaction on a throwaway node when rendered, and four
  atlas entries under `atlas/settlement/`.

**Verified.**
- `pytest` 125 passed, including `test_frost_signed_taproot_spend_is_mined`. `ruff` and `mypy`
  are clean.
- All BIP 341 wallet vectors pass: 7 tweaks including script-tree roots, and `sigMsg`/`sigHash`
  for 7 hash types. The expected signatures are reproduced byte for byte by chapter 1's BIP340
  signer with zero aux randomness.
- The custody output key is computed identically by the Rust crate, `bitcoin.taproot_tweak`, and
  Bitcoin Core's `tr()` descriptor.
- Chapter 5's render confirmed a spend with 1 confirmation and 4.1599969 BTC of custody change.
  The FIX transcript and settlement pages were rasterised and inspected.

**Found and fixed.**
- `check_matches` initially had no fee cap, so a transaction paying the approved amount to the
  approved address could burn the rest as fee. The cap is added and tested.
- `trade()` failed inside a running event loop (caught by the chapter render).
- 14 Markdown lists across chapters 2, 4 and 5 lacked the blank line pandoc requires and
  rendered as run-on paragraphs. All are fixed and checked in the PDF text.

**Decided.**
- **FIX 5.0 SP2, never 4.4** (owner, mid-session). Conventions come from
  `~/code/fix-client/ROE.md`, read only; the fix-gateway and fix-client repos agree.
- Taproot transactions are written from BIP 341, not taken from a library. The oracles are the
  BIP vectors and Bitcoin Core acceptance.

**Open.**
- Signer-side transaction decoding (PSBT).
- Multi-UTXO settlements.
- Fee estimation from the mempool.

### Deliverables

- Fills from a FIX 5.0 SP2 session (FIXT.1.1, DefaultApplVerID 9) are netted per settlement cycle
  into one instruction per asset.
- Each instruction becomes a Taproot key-path spend that is checked against it (exact payment,
  change, fee cap), authorised by the policy engine, signed 2-of-3 by separate FROST processes,
  and mined by Bitcoin Core.
- The transaction and sighash code passes every BIP 341 wallet test vector, and three independent
  implementations agree on the custody address.
- Chapter 5 renders to an 11-page PDF that settles a real regtest transaction during the build.

## 2026-09-24: Module 4, policy and authorisation

**Changed.**
- Wrote `src/custody_lab/policy/`:
  - `model.py`: canonical JSON, `SettlementInstruction`, and Ed25519 `Approval`.
  - `audit.py`: hash-chained `AuditLog` and `verify_chain`.
  - `authorisation.py`: a signed token binding id, instruction digest, exact message and expiry.
  - `engine.py`: a default-deny `PolicyEngine` with seven ordered checks. Velocity and "authorised
    before" are read from the audit log.
- Signers now enforce authorisations:
  - `SigningCluster(threshold, count, authority)` and `sign(message, signers, token)`.
  - Each signer burns its nonces, then verifies the token's signature and expiry, that it matches
    the FROST signing package's message (new binding `signing_package_message`), and that it has
    not been used before.
- `cryptography` moved from the `dev` group to runtime dependencies.
- Added `manual/_quarto.yml` with the shared PDF settings. Code lines now wrap (`fvextra`), and
  chapter front matter keeps only title, subtitle and date.
- Updated chapter 2's cluster cell for the gate, and wrote chapter 4 and five atlas entries under
  `atlas/policy/`.

**Verified.**
- `pytest` 92 passed, `ruff` clean, `mypy` clean (37 files).
- Hypothesis checks two properties: authorised volume never exceeds the velocity cap in any
  24-hour window, and unknown assets are always denied.
- Cluster tests confirm signers refuse forged, expired, message-substituted and replayed tokens.
- Chapters 1, 2 and 4 re-render under the shared config (12, 14 and 12 pages). Chapter 2's and 4's
  signing pages were rasterised with `pypdfium2` and inspected.

**Found and fixed.**
- `SigningCluster._request` raised on the first signer error without reading the other replies.
  The unread reply was then taken as the answer to the next request. It was caught by
  `test_signers_refuse_forged_expired_and_replayed_tokens`, which received the previous test's
  error. All replies are now drained before raising.
- Page inspection showed code lines of 81-88 characters and long outputs clipped at the margin.
  The 88-character check was wrong: the code area is about 80 characters. Code now wraps; cell
  output does not, so printed lines stay under 80 characters.

**Decided.**
- The engine's only state is the audit log.
- Until Module 5 the caller supplies the sighash with the instruction and the engine takes the
  binding on trust. The chapter says so.

**Open.**
- Policy governance (who changes rules and whitelists) is not implemented.
- The audit log is in memory.
- The anchoring of the audit head is planned for Module 6.
- Taproot tweak binding and transaction library for Module 5.
- Rendered PDFs are neither committed nor ignored.

### Deliverables

- A default-deny policy engine decides every settlement instruction through seven ordered checks:
  asset, amount, tier quorum, whitelist, rolling velocity limit, duplicate authorisation, and
  four-eyes approvals signed with Ed25519.
- Every decision is written to a hash-chained audit log that detects edited, deleted and
  reordered entries, and the engine reads its velocity state back from that log.
- The MPC signers now refuse to produce a share without the policy engine's signed
  authorisation. They check it against the exact message in the FROST signing package and reject
  forged, expired, substituted and replayed tokens.
- A coordinator bug that could pair one signer's error with the next request was found by the new
  tests and fixed.
- Chapter 4 renders to a 12-page PDF with a nine-step worked example asserted in code, and all
  chapters now share one PDF configuration that wraps long code lines.

## 2026-09-24: Module 2, MPC custody

**Changed.**
- Teaching code in `src/custody_lab/mpc/`, all EDUCATIONAL, NOT PRODUCTION:
  - `paillier.py`: Miller-Rabin primes, encryption, homomorphic add and scalar multiply.
  - `lindell17.py`: two-party ECDSA, semi-honest core, zero-knowledge proofs omitted and listed.
  - `frost.py`: RFC 9591 FROST(secp256k1, SHA-256).
  - `dkg.py`: Pedersen DKG with Feldman checks and proof of knowledge; zero-sharing refresh.
- Added `encode_point`/`decode_point` (SEC1) to `foundations/ec.py`, and `expand_message_xmd` and
  `hash_to_field` (RFC 9380) to `foundations/hashing.py`.
- Demo signing path:
  - `rust/custody-frost/src/lib.rs` binds ZF `frost-secp256k1-tr` 3.0.0: `dkg_part1..3`,
    `commit`, `signing_package`, `sign`, `aggregate`, `group_public_key`. It is stateless, bytes
    in and out.
  - `src/custody_lab/mpc/cluster.py` (`SigningCluster`) runs one spawned process per share.
    Nonces are single-use and erased on use.
- Tests in `tests/mpc/`. The RFC 9591 vectors are stored at
  `tests/mpc/vectors/frost-secp256k1-sha256.json` (sha256 `5bda3e29…`, from `cfrg/draft-irtf-cfrg-frost`
  `poc/`).
- Wrote chapter 2 (`manual/chapters/02-mpc-custody.qmd`) and eight atlas entries under
  `atlas/mpc/`.

**Verified.**
- Module 1: `pytest` 42 passed, `ruff` and `mypy` clean, before any Module 2 change.
- After Module 2: `pytest` 68 passed, `ruff` clean, `mypy` clean (29 files). Two issues found by
  the first lint run were fixed.
- The educational FROST matches every RFC 9591 intermediate value: shares, nonces, commitments,
  binding-factor inputs, binding factors, signature shares and the final signature.
- The ZF crate's 2-of-3 signatures from three separate processes verify with
  `custody_lab.foundations.schnorr.verify` for all three signer pairs; a single signer is refused.
- Lindell 2017 signatures (2048-bit Paillier) verify with `cryptography`.
- Chapter 2 renders to 13 pages with all six cells executed.

**Decided.**
- The Rust binding passes serialized bytes rather than holding Python objects. Each signer
  process owns its secrets, and the coordinator relays only public packages.
- The cggmp21 listing is abridged from docs.rs 0.6.3 and not compiled.
- Backup and repair are covered as prose, pointing at cb-mpc PVE and ZF `repairable`.

**Open.**
- Taproot tweak (`sign_with_tweak`, `aggregate_with_tweak`) is not yet bound; Module 5 needs it
  for BIP86 key-path spends.
- The Taproot transaction library.
- Rendered PDFs are neither committed nor ignored.
- Mermaid is still blocked on `unzip`.

### Deliverables

- The demo's signing path works end to end. Three separate processes run distributed key
  generation and 2-of-3 FROST signing through the Zcash Foundation crate. The resulting BIP340
  signatures verify with an independent implementation.
- Teaching implementations of Paillier, two-party ECDSA (Lindell 2017), FROST and distributed key
  generation with proactive refresh are in place, each checked against an external oracle.
- The educational FROST reproduces every intermediate value of the RFC 9591 secp256k1 test
  vector.
- Chapter 2 renders to a 13-page PDF covering threshold signing, CGGMP, FROST, DKG, refresh and
  backup, with a hand-checkable threshold signature worked on the toy curve.
- Eight MPC atlas entries are drafted, and the full suite (68 tests), ruff and mypy pass.

## 2026-09-24: Module 1, Foundations

**Changed.**
- Wrote `src/custody_lab/foundations/`, all EDUCATIONAL, NOT PRODUCTION:
  - `ec.py`: the `Curve` group law, `SECP256K1`, and a toy curve y^2 = x^3 + 7 over F_43 with n = 31.
  - `hashing.py`: SHA-256 and BIP340 tagged hashes.
  - `ecdsa.py`: sign and verify, with low-S.
  - `schnorr.py`: BIP340.
  - `shamir.py`: split, Lagrange coefficients, reconstruct.
- Wrote tests in `tests/foundations/`. Oracles are `cryptography` 50.0.1 for ECDSA and public
  keys, and all 19 official BIP340 test vectors
  (`tests/foundations/vectors/bip340-test-vectors.csv`, sha256 `34c9d1d9…`). Shamir uses Hypothesis
  property tests plus an exhaustive secrecy check on Z_31.
- Wrote `manual/chapters/01-foundations.qmd`, with hand-computed toy examples asserted in code, and
  six atlas entries under `atlas/foundations/`.
- Added `cryptography` to the `dev` group and `matplotlib` to the `docs` group.
- Removed the second-person line from the chapter template's objectives.

**Verified.**
- Chapter 1 rendered to a 12-page PDF with all 12 code cells executed. The PDF text contains each
  cell's output.
- secp256k1 constants were checked against independent sources: p equals 2^256 - 2^32 - 977; G
  equals `cryptography`'s generator; n*G is infinity; n passes a Fermat check.
- Twenty random ECDSA sign/verify round trips passed, and BIP340 vector 0 reproduced (ad-hoc run).
- The figure was exported to PNG and inspected.
- `pytest`, `ruff` and `mypy` were not run.

**Found and fixed.** The first chapter render failed: the secp256k1 group order had a dropped hex
digit (63 digits, not prime). The render's executed cells caught it before any test run.
`test_n_times_generator_is_infinity` covers it.

**Decided.**
- Chapter 1 uses a matplotlib figure instead of Mermaid, because headless Chrome is still blocked
  on `unzip`.
- EdDSA is covered by `cryptography`'s Ed25519, with no from-scratch version.

**Open.**
- Run the test suite.
- Whether rendered chapter PDFs are committed. `manual/chapters/01-foundations.pdf` is currently
  untracked and not ignored.

### Deliverables

- Module 1 teaching code implements secp256k1 arithmetic, ECDSA, BIP340 Schnorr and Shamir secret
  sharing in readable Python, labelled EDUCATIONAL, NOT PRODUCTION.
- Its test suite checks the code against independent oracles: the `cryptography` library and the
  19 official BIP340 test vectors.
- Chapter 1 renders to a 12-page PDF whose worked examples are computed by hand and asserted by
  executed code. Every listing in it ran at build time.
- The chapter build caught a wrong secp256k1 constant before the tests were run, the failure the
  executed-manual design was chosen to catch.
- Six atlas entries cover finite fields, elliptic curves, hash functions, ECDSA, Schnorr/BIP340
  and EdDSA, and Shamir sharing.

## 2026-09-24: Module 0, toolchain

**Changed.**
- Added a `docs` dependency group (quarto-cli, ipykernel, nbclient, pyyaml). It and `dev` are
  installed by default.
- Added the Rust extension `rust/custody-frost` (PyO3 0.29, maturin, `frost-secp256k1-tr` 3.0.0).
  It is a uv workspace member and a dependency of `custody-lab`. Added `tests/test_custody_frost.py`.
- Added `scripts/regtest.sh` and `scripts/bitcoin-regtest.conf`; node data goes in `var/regtest`.
- Scaffolded `web/` from Vite 9.2.1's `react-ts` template.
- Installed, per user, with no sudo:
  - TinyTeX in `~/.TinyTeX`.
  - Rust 1.98.1 via rustup. rustup added `. "$HOME/.cargo/env"` to `~/.profile` and `~/.bashrc`.
  - Bitcoin Core 31.1 in `~/.local/opt`, symlinked into `~/.local/bin`.

**Verified.**
- `quarto check jupyter` passed.
- A copy of the chapter template, with the Mermaid block removed, rendered to a 3-page PDF with
  lualatex. Its code cell ran in `.venv/bin/python` and imported `custody_lab`.
- `uv sync` built the extension, and `custody_frost.ciphersuite_id()` returned
  `FROST-secp256k1-SHA256-TR-v1`.
- `bitcoind` 31.1 SHA256 matched `SHA256SUMS`. The regtest node started, mined 101 blocks to a
  bech32m address (wallet balance 50.00000000) and stopped.
- `npm run build` in `web/` succeeded.
- `pytest`, `ruff` and `mypy` were not run.

**Decided.** React for the dashboard, the Rust extension as a runtime dependency, and the `docs`
group on by default. All three are logged as Proposed in `CLAUDE.md`.

**Open.**
- Mermaid in PDF: `quarto install chrome-headless-shell` fails with
  `Failed to spawn 'unzip': entity not found`. Fix: `sudo apt install -y unzip`, then rerun it.
- The GPG signature on Bitcoin Core's `SHA256SUMS` was not checked.

### Deliverables

- The manual toolchain works: Quarto 1.10.18 with TinyTeX renders the chapter template to PDF,
  executing its Python cells in the project environment.
- The demo's threshold-signing library, ZF `frost-secp256k1-tr` 3.0.0, compiles into a PyO3
  extension that `uv sync` builds and Python imports.
- A local Bitcoin Core 31.1 regtest node starts, mines to a Taproot address and stops through
  `scripts/regtest.sh`.
- The TypeScript dashboard scaffold (Vite, React) builds.
- Mermaid diagrams in PDF remain blocked on the missing `unzip` system package.

## 2026-09-24: project setup, threshold-signing feasibility

**Changed.**
- Created the uv project (`custody-lab`, Python 3.12) with a package skeleton of seven empty
  subpackages and one import smoke test. The dev group holds pytest, hypothesis, ruff and mypy.
- Wrote `CLAUDE.md`, `atlas/index.md`, `atlas/project/build-plan.md`,
  `atlas/project/threshold-signing-feasibility.md` and `manual/chapter-template.qmd`.

**Verified.**
- `uv sync` resolved 16 packages.
- cb-mpc was cloned and its README, `Makefile`, `CMakeLists.txt`, C API headers, theory PDFs and
  Cure53 report were read.
- `cryptography` 50.0.1 signed and verified with ML-DSA-65 on this host.
- PyPI and crates.io metadata were read for each candidate library.
- `pytest`, `ruff` and `mypy` were not run.

**Decided.** The owner limited the project to Python, TypeScript and Rust, at showcase depth. The
cb-mpc build was stopped for that reason before it started. On review, the owner accepted every
proposed decision in the `CLAUDE.md` log. The demo signs with FROST (`frost-secp256k1-tr`, 2-of-3)
on Bitcoin regtest.

**Open.**
- The Taproot transaction library.
- The SLH-DSA library.
- Quarto, Rust and `bitcoind` are not installed.

### Deliverables

- `CLAUDE.md` defines the project's purpose, conventions, architecture, toolchain, module status
  and a dated decisions log.
- The repository is a uv-managed Python 3.12 package, with one subpackage per demo module and a
  strict lint, type and test configuration.
- `atlas/index.md` indexes 42 planned knowledge-base entries across the nine curriculum areas and
  defines the entry format.
- `atlas/project/build-plan.md` sequences the modules into a thin end-to-end slice followed by
  deepening, estimated at about 24.5 working days.
- `manual/chapter-template.qmd` fixes the eight-section chapter structure and executes code cells
  at render time.
- `atlas/project/threshold-signing-feasibility.md` records that cb-mpc implements Lindell 2017,
  HLNR 2018 and Lindell 2024 Schnorr in C++ with no Python binding. It recommends from-scratch
  Python for teaching and the Zcash Foundation FROST crate (Rust) for the demo.
