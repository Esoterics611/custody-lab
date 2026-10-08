# ML-KEM (FIPS 203)

**In one sentence.** ML-KEM is the NIST standard lattice-based key encapsulation mechanism: anyone
holding a public key can create a fresh 32-byte shared secret with an encapsulation of it, and only
the private-key holder can recover the secret from the encapsulation.

## The problem

Encrypted data recorded today can be decrypted once a quantum computer exists ("harvest now, decrypt
later"). Share backups and recorded network traffic are exposed now, even though the break comes
later, so their key exchange must move to a scheme a quantum computer does not break.

## The idea

`encapsulate` on the recipient's public key returns a shared secret and a ciphertext; `decapsulate`
on the ciphertext returns the same secret, which both sides then use as an AES key. ML-KEM is built
on module-LWE. Parameter sets 512, 768 and 1024 target NIST security categories 1, 3 and 5, roughly
AES-128, -192 and -256. ML-KEM-768 has a 1,184-byte public key and a 1,088-byte ciphertext.

The manual's share backup: a key share from the teaching DKG is encrypted to an ML-KEM-768 recovery
key with AES-256-GCM, giving a backup of $1{,}088 + 12 + 48$ bytes (encapsulation, nonce, and the
32-byte share with its 16-byte tag).

## Why custody cares

- It removes the harvest-now exposure of backups and transport.
- Production designs combine it with X25519, an elliptic-curve key exchange, so the result holds
  while either scheme holds.

## In the demo

`cryptography` 50.0.1 (OpenSSL 4.0.2) ML-KEM-768 and -1024; no ML-KEM-512 on this host. Key
generation from seeds is checked against NIST ACVP vectors in `tests/pq/test_pq_vectors.py`;
decapsulation vectors are not checked, because they give expanded private keys that `cryptography`
does not load. Chapter 3 uses ML-KEM to release a share to an attested enclave, and chapter 7 to
back up a share.

## In the manual

[Chapter 3](../../manual/chapters/03-key-storage.md),
"[Symmetric encryption in brief](../../manual/chapters/03-key-storage.md#symmetric-encryption-in-brief)"
(key encapsulation explained); [chapter 7](../../manual/chapters/07-post-quantum.md),
"[ML-KEM (FIPS 203)](../../manual/chapters/07-post-quantum.md#ml-kem-fips-203)",
"[A share backup under ML-KEM](../../manual/chapters/07-post-quantum.md#a-share-backup-under-ml-kem)".

## Sources

NIST FIPS 203 (2024); NIST ACVP-Server `ML-KEM-keyGen-FIPS203`.
