# ECDSA

**Definition.** Sign digest $z$ with key $d$: random nonce $k$, $R = kG$, $r = x_R \bmod n$,
$s = k^{-1}(z + rd) \bmod n$. Verify: $x(u_1 G + u_2 Q) \bmod n = r$ with $u_1 = z/s$, $u_2 = r/s$.

**Why custody cares.**
- ECDSA is the signature most chains accept (Bitcoin legacy and SegWit v0, Ethereum), so most
  custody signing is ECDSA.
- Reusing or biasing $k$ reveals $d$.
- $s$ multiplies secrets ($k^{-1}$ times $d$), which is why threshold ECDSA needs Paillier or OT
  machinery (Lindell 2017, CGGMP) while threshold Schnorr does not.
- Bitcoin Core relays only low-S signatures.

**In the demo.** Teaching code: `src/custody_lab/foundations/ecdsa.py` (`sign`, `verify`), checked
against `cryptography` in `tests/foundations/test_ecdsa.py`.

**In the manual.** Chapter 1, "ECDSA", the toy-curve worked example, and Exercise 3 (nonce-reuse key
recovery).

**Sources.** Certicom, *SEC 1* v2.0 (2009); NIST FIPS 186-5; RFC 6979 (deterministic nonces);
BIP 146 (low-S).
