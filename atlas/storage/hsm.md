# Hardware security module (HSM)

**In one sentence.** An HSM is a separate, tamper-resistant device that generates, stores and uses
keys inside itself, signs on request, and lets a key leave only wrapped under another key that never
leaves.

## The problem

A key held in an ordinary server's memory can be copied by anyone with administrator rights on that
server, or by malware running with those rights. A copied key works from anywhere, and the copy
leaves no trace.

## The idea

Software outside the HSM asks it to sign and never receives the key. A key that must travel, for a
backup or to a second HSM in a cluster, leaves **wrapped**: encrypted under a key-encryption key
that stays inside the device. AES key wrap (RFC 3394) is the standard construction; it carries an
integrity check, so a modified wrapped key fails to unwrap. Attributes fixed at creation control
whether a key may leave at all (PKCS#11's *sensitive* and *extractable*).

Physically, the device shows evidence of opening, resists it, and responds to it by **zeroisation**:
sensors trigger the erasure of keys before an attacker reaches them. FIPS 140-3 certifies a module
version at one of four security levels; custody HSMs are typically Level 3 (tamper response,
identity-based operator authentication). Most HSMs expose the OASIS PKCS#11 programming interface.

## Why custody cares

- The key cannot be copied, by administrators included.
- The key can still be used by whoever holds the login. Policy must run inside the boundary (a
  programmable HSM) or before it (chapter 4), or the HSM signs anything it is asked to.
- New algorithms (BIP340, the Taproot tweak, ML-DSA) arrive by firmware update, and are outside the
  certificate until that version is validated.
- The custody key cannot be rotated without moving every coin, so the comparison with a payment HSM
  stops holding at that point: a card key is replaced by reissuing cards.

## In the demo

No HSM. Chapter 3's worked example places the policy authority key and the share backups' recovery
key in HSMs, and the key-wrapping cell reproduces RFC 3394's test vector.

## In the manual

[Chapter 3](../../manual/chapters/03-key-storage.md):
"[Key wrapping](../../manual/chapters/03-key-storage.md#key-wrapping)",
"[Tamper response and certification levels](../../manual/chapters/03-key-storage.md#tamper-response-and-certification-levels)",
"[Hardware security modules](../../manual/chapters/03-key-storage.md#hardware-security-modules)".

## Sources

NIST FIPS 140-3 (2019), ISO/IEC 19790:2012; RFC 3394 and NIST SP 800-38F; OASIS PKCS #11
Specification Version 3.2 (2026, **verify current**); NIST SP 800-186 (secp256k1 allowed for
blockchain-related applications). FIPS 140-2 certificates moved to the historical list on
21 September 2026 (reported; **verify current**).
