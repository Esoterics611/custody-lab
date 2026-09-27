# Hardware security module (HSM)

**Definition.** A separate device that generates, stores and uses keys, and exports them only
wrapped under a key-encryption key it never releases. FIPS 140-3 certifies a module version at
one of four security levels; custody HSMs are typically Level 3 (tamper response, identity-based
operator authentication). Most expose the OASIS PKCS#11 interface.

**Why custody cares.**
- The key cannot be copied, by administrators included.
- The key can still be used by whoever holds the login. Policy must run inside the boundary
  (a programmable HSM) or before it (chapter 4), or the HSM signs anything it is asked to.
- New algorithms (BIP340, the Taproot tweak, ML-DSA) arrive by firmware update, and are outside
  the certificate until that version is validated.

**In the demo.** No HSM. Chapter 3's worked example places the policy authority key and the share
backups' recovery key in HSMs, and the key-wrapping cell reproduces RFC 3394's test vector.

**In the manual.** Chapter 3, "Key wrapping", "Tamper response and certification levels",
"Hardware security modules".

**Sources.** NIST FIPS 140-3 (2019), ISO/IEC 19790:2012; RFC 3394 and NIST SP 800-38F; OASIS
PKCS #11 Specification Version 3.2 (2026, **verify current**); NIST SP 800-186 (secp256k1 allowed
for blockchain-related applications). FIPS 140-2 certificates moved to the historical list on
21 September 2026 (reported; **verify current**).
