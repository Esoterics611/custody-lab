# Trusted execution environment (TEE)

**In one sentence.** A TEE is a region of an ordinary server's processor and memory that the
server's own operating system and hypervisor cannot read, together with remote attestation: a report
signed by the processor naming the exact code running inside.

## The problem

Signing servers in a data centre or a cloud are run by administrators and, in a cloud, by the
provider. An ordinary process's memory is readable to all of them. A custodian wants shares and
policy code to run on such servers without trusting the people who operate them.

## The idea

The processor encrypts the protected region's memory on its way out to the memory chips and refuses
access to it from any other code. Before anyone trusts the region, for instance by sending it a key
share, they check an **attestation report**: a hash of the code the processor loaded (the
**measurement**) plus up to 64 bytes of data chosen by that code, signed by a key the processor maker
built into the chip. Three checks are needed: the signature (genuine hardware), the measurement (the
reviewed build, not a patched one), and the report data (it must commit to the requester's own
public key, or a genuine report could be relayed by an attacker with the attacker's key attached).

To keep a secret across restarts, an enclave **seals** it under a key derived from a chip secret and
the enclave's identity: sealed to the measurement, only identical code can unseal; sealed to the
signer, any build signed by the same developer key can.

Forms in use: process enclaves (Intel SGX), confidential virtual machines (AMD SEV-SNP, Intel TDX),
and AWS Nitro Enclaves, an isolated virtual machine with no storage or network, attested through
AWS's certificate chain.

## Why custody cares

- Shares and policy code can run on cloud servers without trusting the host's administrators.
- Attestation lets a key-release service, or a peer signer, check the exact build before handing
  over a secret.
- Side channels in the processor itself (Foreshadow, SGAxe and others) have broken SGX before, and
  physical memory-bus interposer attacks (WireTap, Battering RAM, TEE.fail, DDRop; late 2025 to
  September 2026) are outside Intel's and AMD's threat models. A TEE does not protect against whoever
  has physical access to the server, which in a public cloud includes the provider.

## In the demo

No TEE. Chapter 3's cells model a measurement, a report, sealing, and a share released to an attested
signer over ML-KEM.

## In the manual

[Chapter 3](../../manual/chapters/03-key-storage.md):
"[Remote attestation](../../manual/chapters/03-key-storage.md#remote-attestation)",
"[Sealing](../../manual/chapters/03-key-storage.md#sealing)",
"[Side channels](../../manual/chapters/03-key-storage.md#side-channels)",
"[Trusted execution environments](../../manual/chapters/03-key-storage.md#trusted-execution-environments)",
"[Releasing a share to an attested signer](../../manual/chapters/03-key-storage.md#releasing-a-share-to-an-attested-signer)".

## Sources

V. Costan and S. Devadas, "Intel SGX Explained", IACR ePrint 2016/086; AWS Nitro Enclaves User Guide
and AWS KMS condition keys for Nitro Enclaves; J. Van Bulck et al., Foreshadow, USENIX Security 2018;
wiretap.fail, tee.fail, DDRop (ACM CCS 2026) (**verify current**). Intel SGX is deprecated on client
processors from 11th-generation Core and continues on Xeon (**verify current**).
