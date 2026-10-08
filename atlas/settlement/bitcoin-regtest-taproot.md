# Taproot key-path spends on regtest

**In one sentence.** The demo's custody coins sit in a Taproot output locked to the tweaked FROST
group key, and spending them takes one 64-byte BIP340 signature over the transaction's BIP341
sighash, checked by a real Bitcoin Core node on a private network.

## The problem

The signing cluster produces a signature; Bitcoin must accept it. That requires building a
transaction Bitcoin Core will validate, locking coins to a key the cluster can sign for, and signing
exactly the fields Bitcoin's rules say a signature covers.

## The idea

- **The output.** A Taproot output has the locking script `OP_1 <Q>`, 34 bytes. $Q$ is the FROST
  group key $P$ tweaked, $Q = P + H_{\text{TapTweak}}(P_x)\,G$. With no script tree this is BIP86:
  anyone who knows $P$ can confirm that no hidden spending script was folded in. The signers sign for
  $Q$, so each share is shifted by the tweak.
- **The transaction.** Spending a 5.00 BTC coin to pay 0.85 BTC creates two outputs, the payment and
  4.1499969 BTC of change back to custody; the 310-satoshi fee is what is left over (155 virtual
  bytes at 2 satoshis each).
- **The sighash.** The signature covers a tagged hash of the transaction's version, locktime, every
  input's outpoint, amount, script and sequence, and every output. One satoshi more to the payee
  gives a different sighash. Committing to every input's amount lets a signer trust the fee it signs.
- **Regtest.** Bitcoin Core in a mode where blocks are mined on command and coins have no value,
  with the same transaction and signature rules as the public network.

## Why custody cares

- A key-path spend of an MPC key is indistinguishable on chain from a single-signer spend.
- The fee is not a field: a transaction without its change output pays everything to the miner, so
  the builder's fee cap is a control.
- A Taproot output shows its key on chain from the moment it is created, which matters for quantum
  exposure (chapter 7).

## In the demo

- `src/custody_lab/settlement/bitcoin.py` (`taproot_tweak`, `sig_msg`, `taproot_sighash`,
  `Transaction`) passes every BIP 341 wallet test vector.
- `transfer.py` builds a one-input spend and checks it: exact payment, change only to custody, fee
  cap.
- `regtest.py` runs a private Bitcoin Core node; each demo run starts its own.
- `tests/settlement/test_regtest_settlement.py` mines a FROST-signed spend.

## In the manual

[Chapter 5](../../manual/chapters/05-settlement.md),
"[Locking and unlocking](../../manual/chapters/05-settlement.md#locking-and-unlocking)",
"[What the signature covers: the sighash](../../manual/chapters/05-settlement.md#what-the-signature-covers-the-sighash)",
"[Taproot outputs and the BIP86 tweak](../../manual/chapters/05-settlement.md#taproot-outputs-and-the-bip86-tweak)",
"[What a key-path signature signs: the BIP341 sighash](../../manual/chapters/05-settlement.md#what-a-key-path-signature-signs-the-bip341-sighash)",
"[Settling on regtest](../../manual/chapters/05-settlement.md#settling-on-regtest)".

## Sources

BIP 341, BIP 86, BIP 350; A. Antonopoulos, D. Harding, *Mastering Bitcoin*, 3rd ed.
