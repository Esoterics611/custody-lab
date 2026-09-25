# Threshold signing: cb-mpc feasibility and recommended path

Checked 2026-09-24. Evidence class is given per fact: **observed** (a command was run here and its
output read), **reported** (the named source says so), **unverified** (not checked yet).

## Verdict

cb-mpc is a good library, but it is not the right signing engine for this lab. It is C++ only. It
ships no Python binding and needs a patched OpenSSL build. Calling it from Python would mean
writing and maintaining our own FFI layer, in a language outside the project's TypeScript/Python/Rust
set. Instead, use it as **reading material**. Its theory and spec PDFs are the best free source for
the Lindell 2017 and DKG chapters.

Recommended path: build **from-scratch Python** versions for teaching, and use the **Zcash
Foundation FROST crate (Rust)** as the real library that signs in the demo. One small PyO3 extension
wraps that crate.

## cb-mpc facts

| Fact | Detail | Evidence |
|------|--------|----------|
| Repository | `github.com/coinbase/cb-mpc`, last commit 2026-08-31, latest tag `v0.2.2`, CMake project version `0.3.0` | observed (clone) |
| Licence | MIT | observed (`LICENSE.md`) |
| Language | C++17; public C API with a stable ABI in `include/cbmpc/c_api/` | observed |
| Bindings | Go only, in the separate repository `coinbase/cb-mpc-go`. No Python binding in the repository; `cbmpc` and `cb-mpc` are not on PyPI | observed (README, PyPI) |
| 2-party ECDSA | Lindell 2017 (Paillier-based), additive rather than multiplicative sharing | observed (`docs/theory/ecdsa-2pc-theory.pdf`) |
| Multi-party ECDSA | Haitner, Lindell, Nof, Ranellucci 2018 with OT-based multiplication; t-of-n via access structures | observed (`ecdsa-mpc-theory.pdf`, `c_api/ecdsa_mp.h`) |
| Schnorr / EdDSA | Lindell 2024 three-round Schnorr, EdDSA and BIP340 variants; **not FROST** | observed (`schnorr-theory.pdf`, `schnorr_mp.h`) |
| Not implemented | CGGMP, FROST | observed (protocol sources and spec list) |
| Also included | DKG, share refresh, HD derivation (not BIP32-compliant), publicly verifiable encryption for backup, TDH2 | observed |
| Build requirements | CMake 3.16 or later. Clang 20 recommended (constant-time properties tested on Clang 20 only). Custom static OpenSSL 3.6.4 with a patched `curve25519.c` and a modified OAEP padding function. Git submodules. git-lfs for the PDFs | observed (README, `Makefile`, `scripts/openssl/`) |
| Artefact | Static `libcbmpc.a` only, compiled with `-fPIC` | observed (`CMakeLists.txt`, `scripts/install.sh`) |
| Platforms | 64-bit Linux and macOS; no Windows, WebAssembly or mobile | observed (README) |
| Transport | Caller supplies blocking `send` / `receive` / `receive_all` callbacks; the library is not thread-safe | observed (`c_api/job.h`, README) |
| Audit | Cure53 report CBS-02, fieldwork Nov-Dec 2024, report dated 2025-03-21. Findings: 1 High (refresh small-subgroup), 1 Medium, 1 Low, 6 Info. It predates the current code | observed (`docs/cure53-audit.pdf`) |

Host state: cmake, clang and docker are absent. apt offers cmake 3.28.3 and clang-20 20.1.2; both
need sudo (**observed**). No build was attempted: the language constraint made the build moot.

### How Python would call it (not pursued)

1. Link `libcbmpc.a` and the patched `libcrypto.a` into one shared object with `--whole-archive`.
2. Declare the `cbmpc_*` C API to `cffi`.
3. Implement the transport callbacks in Python, over one socket per party.
4. Run each party in its own process.

None of this has been built. **Unverified.**

## Candidates compared

| Option | Language | Protocol | Audit | Fits the lab |
|--------|----------|----------|-------|--------------|
| cb-mpc | C++ | Lindell17, HLNR18, Lindell24 Schnorr | Cure53, 2024 (reported in-repo) | Reading material only |
| ZF `frost-*` 3.0.0 | Rust | FROST, RFC 9591, with DKG | NCC Group audited v0.6.0. That audit **excludes `frost-secp256k1-tr`** (the Taproot variant) | **Demo signing engine** |
| `cggmp21` 0.6.3 | Rust | CGGMP t-of-n ECDSA | Kudelski (reported in README, no date given). No key refresh, no identifiable abort | Chapter snippet; optional stretch |
| From scratch | Python | Shamir, Lindell17, FROST, Pedersen DKG, refresh | None; labelled EDUCATIONAL | **Teaching versions** |

Crate versions: **observed** on crates.io. Audit statements: **reported** by each project's
README.

## Recommended path

1. **Teaching (Module 2), Python, EDUCATIONAL, NOT PRODUCTION.** Implement Shamir, 2-party ECDSA
   (Lindell 2017 with a from-scratch Paillier), FROST and Pedersen DKG with refresh. Every version
   is checked against an independent oracle:
   - ECDSA signatures verify with `cryptography`'s standard verifier, which shows the chain cannot
     tell the signature came from MPC.
   - FROST passes the RFC 9591 test vectors.
2. **Real library (demo), Rust.** Use `frost-secp256k1-tr` in a 2-of-3 set, exposed to Python by
   one PyO3/maturin extension with four calls: keygen, round 1, round 2, aggregate.
   - The output is a BIP340 signature, which spends a Taproot output on Bitcoin regtest.
   - Each signer runs in its own process holding one share. The dashboard shows which process holds
     which share.
3. **ECDSA production libraries (chapter only).** Show cb-mpc's `cbmpc_ecdsa_2p_*` API and
   `cggmp21`'s signing call as annotated listings next to the Python Lindell 2017 code. Running
   `cggmp21` is an optional stretch.

### Decisions (accepted by the owner 2026-09-24)

| Decision | Accepted | Alternative not taken |
|----------|----------------|-------------|
| Demo signature scheme | FROST / BIP340 on Bitcoin regtest | ECDSA (educational Lindell 2017) on an Ethereum dev chain (`anvil`). This keeps ECDSA on the demo path but puts no audited library behind it |
| Audited-only on the demo path | Accept `frost-secp256k1-tr`: same codebase as the audited crates, outside the audit scope, labelled as such | `frost-ed25519` (audited) on a Solana test validator: a heavier toolchain |
| Brief says "show both" for cb-mpc | Show cb-mpc as an annotated API listing, not executed | Build cb-mpc with a cffi binding: C++ toolchain, custom OpenSSL, our own FFI |

### Still unverified

- A Python library that builds Taproot key-path spends and BIP341 sighashes. Candidates are
  `bitcoin-utils` and `embit`; `rust-bitcoin` inside the PyO3 extension is the fallback.
- Resolved in Module 0: PyO3 and maturin build inside the uv project; `bitcoind` 31.1 regtest
  runs on this host.
- Resolved in Module 2: `frost-secp256k1-tr` DKG and 2-of-3 signing work across three processes,
  and the signatures verify with an independent BIP340 implementation.
