# Trusted execution environment (TEE)

**Definition.** A region of an ordinary server's processor and memory that the host's operating
system and hypervisor cannot read, with remote attestation: a report, signed through the
processor maker's or cloud provider's root of trust, of the code's measurement and 64 bytes of
report data. Process enclaves (Intel SGX), confidential virtual machines (AMD SEV-SNP, Intel
TDX) and AWS Nitro Enclaves (an isolated VM with no storage or network, attested through AWS's
Nitro PKI).

**Why custody cares.**
- Shares and policy code can run on cloud servers without trusting the host's administrators.
- Attestation lets a key-release service, or a peer signer, check the exact build before it
  hands over a secret. The release must also check that the report data binds the requester's
  public key, or a relayed report is accepted.
- Physical memory-bus interposer attacks (WireTap, Battering RAM, TEE.fail, DDRop; late 2025 to
  September 2026) are outside Intel's and AMD's threat models, so a TEE does not protect against
  whoever has physical access to the server.

**In the demo.** No TEE. Chapter 3's cells model a measurement, a report, sealing, and a share
released to an attested signer over ML-KEM.

**In the manual.** [Chapter 3](../../manual/chapters/03-key-storage.md), "[Remote attestation](../../manual/chapters/03-key-storage.md#remote-attestation)", "[Sealing](../../manual/chapters/03-key-storage.md#sealing)", "[Side channels](../../manual/chapters/03-key-storage.md#side-channels)", "[Trusted
execution environments](../../manual/chapters/03-key-storage.md#trusted-execution-environments)", "[Releasing a share to an attested signer](../../manual/chapters/03-key-storage.md#releasing-a-share-to-an-attested-signer)".

**Sources.** V. Costan and S. Devadas, "Intel SGX Explained", IACR ePrint 2016/086; AWS Nitro
Enclaves User Guide and AWS KMS condition keys for Nitro Enclaves; Van Bulck et al., Foreshadow,
USENIX Security 2018; wiretap.fail, tee.fail, DDRop (ACM CCS 2026) (**verify current**). Intel
SGX is deprecated on client processors from 11th-generation Core and continues on Xeon
(**verify current**).
