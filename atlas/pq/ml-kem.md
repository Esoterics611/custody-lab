# ML-KEM (FIPS 203)

**Definition.** A module-lattice key encapsulation mechanism. `encapsulate` on a public key
returns a 32-byte shared secret and a ciphertext; `decapsulate` on the ciphertext returns the same
secret. Parameter sets 512, 768 and 1024 target NIST categories 1, 3 and 5. ML-KEM-768: 1,184-byte
public key, 1,088-byte ciphertext.

**Why custody cares.**
- Encrypted data recorded today can be decrypted once a quantum computer exists. Share backups
  and recorded transport are the exposure that exists now.
- Production designs combine it with X25519, so the result holds while either scheme holds.

**In the demo.** `cryptography` 50.0.1 (OpenSSL 4.0.2) ML-KEM-768 and -1024; no ML-KEM-512 on this
host. Key generation from seeds is checked against NIST ACVP vectors in
`tests/pq/test_pq_vectors.py`. Chapter 7 encrypts a DKG share backup with it and AES-256-GCM.

**In the manual.** Chapter 7, "ML-KEM (FIPS 203)", "A share backup under ML-KEM".

**Sources.** NIST FIPS 203 (2024); NIST ACVP-Server `ML-KEM-keyGen-FIPS203`.
