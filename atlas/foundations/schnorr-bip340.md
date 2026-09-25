# Schnorr, BIP340 and EdDSA

**Definition.** Schnorr: $R = kG$, $e = H(R \| P \| m)$, $s = k + ed$; verify $sG = R + eP$.
BIP340 adds three rules:
- x-only 32-byte keys, with even $y$ implied;
- tagged hashes;
- nonces derived from the key, the message and auxiliary randomness.

EdDSA (Ed25519) is Schnorr on an Edwards curve with a fully deterministic nonce.

**Why custody cares.**
- The equation is linear in the secrets: shares of $d$ and $k$ give shares of $s$. That makes
  threshold Schnorr (FROST) much simpler than threshold ECDSA.
- Bitcoin Taproot outputs (BIP 341) require BIP340 signatures; the demo's regtest settlements
  spend them.
- Threshold EdDSA must use random nonces, because a group cannot cheaply compute the
  deterministic one. Verifiers cannot tell.

**In the demo.** Teaching code: `src/custody_lab/foundations/schnorr.py` (`pubkey_gen`, `sign`,
`verify`), checked against all 19 BIP 340 test vectors. The demo signs with `frost-secp256k1-tr`
(Module 2).

**In the manual.** Chapter 1, "Schnorr and BIP340", "EdDSA", "Linearity: a naive two-party Schnorr
signature".

**Sources.** BIP 340; BIP 341; RFC 8032.
