# Schnorr, BIP340 and EdDSA

**In one sentence.** A Schnorr signature is a commitment $R = kG$ and a response
$s = k + e\,d$, where the challenge $e$ is a hash of $R$, the public key and the message; anyone
checks $sG = R + eP$.

## The problem

A signature must prove knowledge of the private key for one message without revealing it, and, for
custody, it should be easy to produce jointly by several parties who each hold a piece of the key.

## The idea

Schnorr's identification protocol is a challenge-response login: the prover commits to a fresh
secret nonce by sending $R = kG$, the verifier sends a random challenge $e$, and the prover answers
$s = k + e\,d$. The answer passes because positions add: $sG = kG + e\,dG = R + eP$. The nonce hides
the key the way a one-time pad hides a message, and the commitment must come before the challenge,
or a prover without $d$ could pick $s$ first and solve for $R$.

The **Fiat-Shamir transform** replaces the live verifier with a hash, $e = H(R \,\|\, P \,\|\, m)$,
which nobody can steer, and the conversation becomes a signature anyone can check later. On the
manual's toy curve, with $d = 7$, $k = 10$ and the message "deliver 0.85 BTC", the hash gives
$e = 18$ and $s = 10 + 18 \times 7 \equiv 12$; the altered message "deliver 8.50 BTC" gives $e = 20$,
and the check fails.

**BIP340** is Bitcoin's version (used by Taproot). It adds x-only 32-byte keys (each $x$ belongs to
a point and its mirror, and the even-$y$ one is meant), tagged hashes, and nonces derived from the
key, the message and extra randomness. **EdDSA** (Ed25519) is Schnorr on an Edwards curve with a
nonce derived entirely from the key and the message, so a single signer can never repeat it.

## Why custody cares

- The equation is linear in the secrets: if $d = d_1 + d_2$ and $k = k_1 + k_2$, each party computes
  $k_i + e\,d_i$ alone and the shares add up to $s$. That makes threshold Schnorr (FROST) much
  simpler than threshold ECDSA.
- Bitcoin Taproot outputs (BIP 341) require BIP340 signatures; the demo's regtest settlements spend
  them.
- A threshold group cannot compute EdDSA's deterministic nonce without a costly joint hash, so
  threshold EdDSA uses random nonces. Verifiers cannot tell the difference.

## In the demo

Teaching code: `src/custody_lab/foundations/schnorr.py` (`pubkey_gen`, `sign`, `verify`), checked
against all 19 BIP 340 test vectors. The demo signs with `frost-secp256k1-tr` (chapter 2), and the
demo's approvals are Ed25519 signatures from `cryptography`.

## In the manual

[Chapter 1](../../manual/chapters/01-foundations.md):
"[What a signature proves](../../manual/chapters/01-foundations.md#what-a-signature-proves)",
"[From a conversation to a signature](../../manual/chapters/01-foundations.md#from-a-conversation-to-a-signature)",
"[Schnorr and BIP340](../../manual/chapters/01-foundations.md#schnorr-and-bip340)",
"[EdDSA](../../manual/chapters/01-foundations.md#eddsa)", and
"[Linearity: a naive two-party Schnorr signature](../../manual/chapters/01-foundations.md#linearity-a-naive-two-party-schnorr-signature)".

## Sources

BIP 340; BIP 341; RFC 8032.
