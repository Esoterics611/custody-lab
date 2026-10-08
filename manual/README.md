# The custody-lab manual

The manual teaches every idea the custody-lab demo uses, starting from school arithmetic. It is
written for an engineer who knows trading or payments infrastructure (FIX sessions, signed API
requests, clearing and settlement) and has no background in cryptography or Bitcoin. Each chapter
starts from the problem a custodian faces, explains the idea in plain words, works an example by
hand, and then runs the same example in code.

Each chapter is published in two forms, built from the same source:

- **On GitHub:** the Markdown files linked below, with every code cell's output and figure. Each
  chapter has previous and next links, and every mention of another chapter is a link.
- **As PDF:** one file per chapter, built locally with `scripts/render-manual.sh` (the PDFs are not
  committed). The PDFs link to each other the same way when they sit in the same folder.

Every code listing in both forms ran when the chapter was built. A listing that fails stops the
build, so the manual is tested in the same way as the code.

## Chapters

**Status.** Chapters 0 to 8 follow the manual's writing standard (explanation at length, concept by
concept). Chapter 9 is a first draft, being rewritten to the same standard, in order.

| Chapter | The question it answers |
|---------|-------------------------|
| [0. Orientation](chapters/00-orientation.md) | What does a custodian protect against, and what happens in each of the demo's nine steps? Teaches keys, signatures, splitting a key, threshold signing, approvals and proof of reserves with numbers small enough to check by hand. Start here. |
| [1. Foundations](chapters/01-foundations.md) | How do keys and signatures work? Arithmetic on a clock, elliptic curves, ECDSA and Schnorr signatures (Bitcoin's BIP340), why a reused nonce gives away the key, and Shamir secret sharing. |
| [2. MPC custody](chapters/02-mpc-custody.md) | How can several machines produce one signature when none of them holds the key? The ways to split a key, what an attacker is assumed to do, two-party ECDSA, FROST, distributed key generation, refreshing and backing up shares, and the demo's signing processes. |
| [3. Key storage](chapters/03-key-storage.md) | Where can a key or a share be kept? Hardware security modules, secure enclaves and MPC compared: key wrapping, attestation, sealing, side channels, and where each of the demo's keys would live in production. |
| [4. Policy and authorisation](chapters/04-policy.md) | How is a payment approved before anything signs it? The default-deny policy engine, approvals signed by people, whitelists, velocity limits, the hash-chained audit log, and the authorisation each signer checks. |
| [5. Trading to settlement](chapters/05-settlement.md) | How does a FIX fill become a confirmed Bitcoin payment? The FIX 5.0 SP2 session, netting, Bitcoin transactions and Taproot, and a real settlement on a private Bitcoin network while the chapter is built. |
| [6. Proof of reserves](chapters/06-reserves.md) | How does a custodian show it holds what it owes? Hash trees, Merkle sum trees and the attack they prevent, proof of control, what the proof leaves out, and zero-knowledge proofs of liabilities. Builds by running the whole demo. |
| [7. Post-quantum cryptography](chapters/07-post-quantum.md) | What would a quantum computer break, and what replaces it? Hash-based signatures (Lamport, WOTS+, SLH-DSA), ML-DSA and ML-KEM, why they are hard to use for threshold signing, and the order in which a custodian should migrate. |
| [8. Industry and regulation](chapters/08-industry.md) | Where does this sit in finance today? Money issued as tokens, delivery versus payment, institutional ledgers and central bank projects, the EU and US custody rules, and the Israeli landscape. |
| [9. Capstone](chapters/09-capstone.md) | How would the whole system be designed for production? A design review: the architecture, what each component's compromise gives an attacker, fourteen failure modes, and the trade-offs. |

## Reference

- [Glossary](../atlas/glossary.md): every term the manual defines, with a link to the section
  that teaches it.
- [Atlas](../atlas/index.md): one short entry per concept, for looking things up after reading.

## Building the manual

```bash
scripts/render-manual.sh                                     # every chapter, PDF and Markdown
scripts/render-manual.sh manual/chapters/05-settlement.qmd   # one chapter
```

The build needs the project environment (`uv sync`), TinyTeX for the PDF
(`uv run quarto install tinytex`), and Bitcoin Core on `PATH`, because chapters 5 and 6 start their
own private Bitcoin network. Sources are `chapters/NN-slug.qmd`; the shared settings are in
`_quarto.yml`, and `links.py` makes the links between chapters. New chapters start from
`chapter-template.qmd`.
