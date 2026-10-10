# Protocol messages: what the signing cluster sends

**In one sentence.** Every message between the demo's signers passes through the coordinator and
is an instruction, a public message, a message sealed to one signer, or the policy engine's
authorisation, each with a fixed serialization whose fields and sizes are listed here.

## The problem

"The coordinator learns nothing secret" is a claim about bytes, and only the bytes can confirm it.
The demo's documents made that claim while its coordinator relayed every key-generation sub-share
in clear, and a recording coordinator could have rebuilt the key from them ([attack vectors,
Finding 1](../../manual/attack-vectors.md#two-findings-about-the-demo-as-packaged)). Sizing a
network link, a log or a hardware module's message buffer has the same need: the actual messages,
not a description of the protocol.

## The idea

A message on a network is a row of bytes, and its **serialization** is the rule that turns the
protocol's values into those bytes. The Zcash Foundation crate serializes with postcard, a compact
binary format in which a small count or length takes one byte. Every FROST message begins with a
5-byte header: the format version, 0, and the CRC-32 of the ciphersuite's name,
`FROST-secp256k1-SHA256-TR-v1`, which is `230f8ab3`. A message from another ciphersuite is refused
when it is read. A number modulo the group order, such as a share, a sub-share or a signature
share, takes 32 bytes, big-endian; a participant's identifier is such a number too. A point takes
33 bytes in compressed form: the x coordinate and a byte for which of the two points with that x it
is. A proof of knowledge is a Schnorr signature written as BIP340 writes one, an x-only R of 32
bytes and z of 32, after one length byte.

The demo seals a message for one signer as a 12-byte nonce, the ChaCha20-Poly1305 ciphertext (as
long as the message), and a 16-byte authentication tag (`custody_lab.mpc.channel`).

The sizes below were observed on this repository's 2-of-3 cluster. Each message's fields were read
from the crate source and are checked against its length every time it passes
(`custody_lab.demo.protocol`).

| Round | Message | Bytes | Fields | Kind |
|-------|---------|-------|--------|------|
| Private channels | channel public key | 32 | X25519 public key | clear |
| Key generation 1 | round-1 package | 137 | header 5, count 1, two Feldman commitments 66, proof length 1, R 32, z 32 | clear |
| Key generation 2 | sub-share | 65 | nonce 12, ciphertext 37 (header 5 and the 32-byte sub-share), tag 16 | sealed |
| Key generation 3 | public key package | 236 | header 5, count 1, three identifiers and verifying shares 195, group public key 33, threshold 2 | clear |
| Signing 1 | nonce commitments | 71 | header 5, D 33, E 33 | clear |
| Signing 2 | signing package | 245 | header 5, count 1, two identifiers with their commitments 206, message length 1, message 32 | clear |
| Signing 2 | authorisation | 7,047 | ML-DSA-65 signature in hex 6,618, Ed25519 signature in hex 128, identifier, digest, message, expiry and JSON 301 | authorisation |
| Signing 2 | signature share | 32 | z for this signer | clear |
| Refresh 1 | round-1 package | 104 | as key generation, with one commitment: a line through zero has no starting-value commitment | clear |
| Refresh 2 | point on a zero line | 65 | as the sub-share | sealed |
| Repair 1 and 2 | delta, sigma | 60 | nonce 12, ciphertext 32, tag 16 | sealed |

The key package each signer keeps, and never sends, is 136 bytes: header 5, identifier 32, signing
share 32, verifying share 33, group public key 33, threshold 1.

One run of the protocol tab, six ceremonies in sixteen rounds, relays 113 messages: 6,305 bytes in
clear, 2,280 sealed and 28,188 of authorisations. The authorisation's size varies by a few bytes
with its expiry's written form.

## Why custody cares

- What the coordinator can read is a property of these bytes. Everything it relays in clear is
  public by design; the sealed messages are the ones that would give away the key.
- The channel keys are static, so the channel has no forward secrecy: a signer's channel key stolen
  later opens the sealed messages to and from that signer that were recorded earlier. A recording
  of this traffic is therefore sensitive for as long as the channel keys are in use.
- The threshold protocol's own messages are small, tens to a few hundred bytes. In this demo the
  authorisation is most of the traffic, because ML-DSA-65 signatures are 3,309 bytes and the token
  sends them as hex, which doubles them; a binary token would halve that part.
- The header's ciphersuite tag makes a message from a differently configured signer fail on
  arrival rather than produce a wrong result.

## In the demo

`SigningCluster(watch=...)` (`src/custody_lab/mpc/cluster.py`) reports every round's requests and
replies as they pass through the coordinator. `custody_lab.demo.protocol` turns them into messages,
with `messages()` and one function per message kind that reads its fields and checks their sizes.
The **Watch the protocol** tab and `custody-lab protocol` show them. Tests:
`tests/demo/test_protocol.py` (fields add up, sealed messages delivered unchanged, round-1 packages
forwarded unchanged) and `test_no_share_of_any_period_passes_through_the_coordinator` in
`tests/mpc/test_signing_cluster.py`, which searches every relayed byte for every signer's share of
each period, read from its key package and checked against OpenSSL's share times G.

## In the manual

The walkthrough's "[Watching the
protocol](../../manual/demo-walkthrough.md#watching-the-protocol)";
[chapter 2](../../manual/chapters/02-mpc-custody.md), "[The demo's signing path: ZF FROST in three
processes](../../manual/chapters/02-mpc-custody.md#the-demos-signing-path-zf-frost-in-three-processes)".

## Sources

- `frost-core` 3.0.0, `src/serialization.rs` (the header and the CRC-32 short identifier) and
  `src/keys/refresh.rs` (the refresh commitment without its constant term); `frost-secp256k1-tr`
  3.0.0, `src/lib.rs` (33-byte points; signatures as x-only R and z). Read in the cargo registry
  on 2026-10-10. Evidence class: observed. Crate version: **verify current**.
- RFC 9591, the FROST protocol.
- Sizes: observed on this repository's run of `custody-lab protocol`, 2026-10-10.
