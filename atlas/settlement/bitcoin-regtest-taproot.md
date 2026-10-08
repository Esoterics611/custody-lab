# Taproot key-path spends on regtest

**Definition.** A Taproot output pays `OP_1 <Q>`, where $Q = P + H_{TapTweak}(P_x)G$ is the FROST
group key $P$ with the BIP86 tweak. Spending it by key path needs one 64-byte BIP340 signature
over the BIP341 sighash. That sighash commits to every input's amount and script, and to all
outputs.

**Why custody cares.**
- A key-path spend of an MPC key is indistinguishable on chain from a single-signer spend.
- Committing to all input amounts lets a signer trust the fee.
- The tweak means signers sign for $Q$, not $P$, so each share is shifted by the tweak.

**In the demo.**
- `src/custody_lab/settlement/bitcoin.py` (`taproot_tweak`, `sig_msg`, `taproot_sighash`,
  `Transaction`) passes every BIP 341 wallet test vector.
- `transfer.py` builds a one-input spend and checks it: exact payment, change only to custody,
  fee cap.
- `regtest.py` runs a private Bitcoin Core node.
- `tests/settlement/test_regtest_settlement.py` mines a FROST-signed spend.

**In the manual.** [Chapter 5](../../manual/chapters/05-settlement.md), "[Taproot outputs and the BIP86 tweak](../../manual/chapters/05-settlement.md#taproot-outputs-and-the-bip86-tweak)", "[What a key-path signature
signs: the BIP341 sighash](../../manual/chapters/05-settlement.md#what-a-key-path-signature-signs-the-bip341-sighash)", "[Settling on regtest](../../manual/chapters/05-settlement.md#settling-on-regtest)".

**Sources.** BIP 341, BIP 86, BIP 350; A. Antonopoulos, D. Harding, *Mastering Bitcoin*, 3rd ed.
