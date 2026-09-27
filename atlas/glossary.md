# Glossary

Every term the manual defines, in one sentence, with the chapter and section that teach it.
Chapter 0 is the orientation; "FP" is a chapter's First principles section.

| Term | Meaning | Taught in |
|------|---------|-----------|
| Abort | A protocol run that stops without a signature because cheating was detected. | 2 FP, What the attacker is assumed to do |
| Additive share | One of several numbers that sum to the key modulo $n$; all holders are needed. | 2 FP, Three ways to split a key |
| Address | A locking script encoded for people (bech32m for Taproot: `bc1p…`, `bcrt1p…` on regtest). | 5 FP, Locking and unlocking |
| Adversary model | The statement of which parties an attacker controls, when, and what they may do. | 2 FP, What the attacker is assumed to do |
| Allowlist | Addresses a token's issuer permits to hold it; transfers to any other address fail. | 8 FP, Public and permissioned ledgers |
| Anchoring | Publishing an audit log's head hash elsewhere, so a rewritten or truncated log is detected. | 4, Hash-chained audit log |
| Approval quorum | The people who must approve an instruction before the policy engine authorises it. | 0, Two quorums; 4 |
| Atomic settlement | Both legs of a trade in one ledger transaction, valid or invalid together. | 8 FP, Delivery versus payment |
| Attestation | A signed statement of a snapshot's contents, made under the custody key; compare remote attestation. | 6 FP, Proof of control |
| Attestation report | A measurement and report data, signed through the processor maker's or cloud provider's root of trust. | 3 FP, Remote attestation |
| Authorisation | A short-lived token, signed by the policy engine, naming the exact message the signers may sign. | 4, Authorisation |
| Binding (commitment) | The committer cannot open a commitment to a different value. | 2 FP, Commitments |
| Binding factor | In FROST, a hash of the message and all commitments that fixes each signer's effective nonce. | 2 FP, Many sessions at once; 2, FROST |
| BIP340 | Bitcoin's Schnorr signature standard: x-only keys, tagged hashes, hashed nonces. | 1, Schnorr and BIP340 |
| BIP86 | A Taproot output whose key is tweaked to commit to no scripts, so it has a key path only. | 5, Taproot outputs and the BIP86 tweak |
| Block | A batch of transactions with a proof of work, naming the block before it. | 5 FP, Blocks, confirmation and regtest |
| Broadcast | A protocol message sent to every party. | 2 FP, Parties, rounds and a coordinator |
| Canonical encoding | An encoding that gives every value exactly one byte representation. | 4, Canonical encoding |
| CASP | Crypto-asset service provider: a firm licensed under MiCA, for example to hold crypto-assets for clients. | 8, Regulation in the EU: MiCA |
| CBDC | Central bank digital currency: central bank money as a token, wholesale (banks only) or retail (the public). | 8 FP, Four forms of money on a ledger |
| Change | The output that returns the remainder of a spent UTXO, less the fee, to the payer. | 5 FP, Coins are outputs, not balances |
| Commitment | A value published now that fixes a choice before information that could bias it arrives. | 1 FP, What a signature proves; 2 FP, Commitments |
| Confidential virtual machine | A whole virtual machine whose memory the hypervisor cannot read (AMD SEV-SNP, Intel TDX). | 3, Trusted execution environments |
| Confirmation | One block containing or following a transaction; more confirmations make reversal costlier. | 5 FP, Blocks, confirmation and regtest |
| Constant-time code | Code whose running time and memory accesses do not depend on secret values. | 3 FP, Side channels |
| Context string | Up to 255 bytes bound into an ML-DSA or SLH-DSA signature to separate uses of one key. | 7, The demo's hybrid authorisation |
| Coordinator | The process that relays protocol messages and combines results; it holds no share. | 2 FP, Parties, rounds and a coordinator |
| Corrupted party | A party the attacker controls. | 2 FP, What the attacker is assumed to do |
| Default-deny | Refusing anything the policy does not explicitly allow. | 4, Intuition |
| Discrete logarithm problem | Recovering $d$ from $Q = dG$; about $2^{128}$ steps on secp256k1 by the best known classical methods. | 1 FP, Easy forwards, infeasible backwards |
| DKG | Distributed key generation: parties create a shared key that no party ever holds. | 2, Distributed key generation |
| Domain separation | Hashing each class of message under its own tag, so two classes can never produce the same message. | 6 FP, Proof of control |
| Double-and-add | Computing $dG$ by repeated doubling, about 256 doublings for a 256-bit key. | 1 FP, Easy forwards, infeasible backwards |
| Dust | An output too small for Bitcoin Core to relay (330 sats for Taproot); the builder adds it to the fee. | 5 FP, Coins are outputs, not balances |
| DvP | Delivery versus payment: the asset moves if and only if the cash moves. | 8 FP, Delivery versus payment |
| ECDSA | The signature scheme $s = k^{-1}(z + rd)$; hard to split because it multiplies secrets. | 1, ECDSA |
| Ed25519 | Schnorr-type signatures (EdDSA) on Curve25519 with deterministic nonces; used for approvals. | 1, EdDSA |
| Enclave | The protected region of a TEE: code and memory the host cannot read. | 3, Intuition |
| Extractable key | A key an HSM may export, and then only wrapped under a key-encryption key. | 3 FP, Key wrapping |
| Fee | Inputs minus outputs of a transaction, collected by the miner. | 5 FP, Coins are outputs, not balances |
| Feldman commitment | Publishing each polynomial coefficient times $G$, so a share can be checked. | 2 FP, Commitments |
| Fiat-Shamir transform | Replacing a verifier's random challenge with a hash of the commitment, key and message. | 1 FP, What a signature proves |
| Fiat-Shamir with aborts | A lattice signature that discards and retries any response that would leak the secret. | 7, ML-DSA (FIPS 204) |
| Finite field | The integers modulo a prime, where every non-zero number has an inverse. | 1 FP, Arithmetic on a clock |
| FIPS 140-3 | The US and Canadian standard that certifies a cryptographic module version at one of four security levels. | 3 FP, Tamper response and certification levels |
| FORS | The few-time signature at the bottom of SLH-DSA that signs the message digest. | 7 FP, A Merkle tree of one-time keys |
| Four-eyes | Requiring approval by someone other than the initiator (maker-checker). | 4, Intuition |
| FROST | Two-round threshold Schnorr signing (RFC 9591); the demo's signing protocol. | 2, FROST |
| Generator | The published point $G$ from which every key is measured. | 1 FP, The cycle: generator, order and scalar |
| Group | A set with an operation that commutes, associates, has a zero and has negatives. | 1 FP, Points that can be added |
| Group order | The length $n$ of the cycle $G, 2G, \dots, nG = \mathcal{O}$. | 1 FP, The cycle: generator, order and scalar |
| Grover's algorithm | Quantum search of $2^k$ values in about $2^{k/2}$ steps; it weakens hashes and symmetric keys. | 7 FP, What a quantum computer breaks |
| Harvest now, decrypt later | Recording ciphertext today to decrypt it once a quantum computer exists. | 7, Intuition |
| Hash chain | A value hashed repeatedly; a position along it can be advanced but not reversed. | 7 FP, Winternitz chains and the checksum |
| Hash function | A function mapping any input to a fixed-size digest, resistant to preimages and collisions. | 1, Hash functions |
| Herstatt risk | Paying one currency and not receiving the other, named after a bank closed between the two legs in 1974. | 8 FP, Delivery versus payment |
| Hiding (commitment) | A commitment reveals nothing about the committed value. | 2 FP, Commitments |
| Homomorphic encryption | Encryption in which operations on ciphertexts act on the plaintexts inside. | 2 FP, Encryption that can be computed on |
| HSM | Hardware security module: a device that keeps keys and uses them inside itself, exporting them only wrapped. | 3, Intuition; 3, Hardware security modules |
| Hybrid signature | Two signatures of different schemes over one payload, both required to verify. | 7, The demo's hybrid authorisation |
| Hypertree | SLH-DSA's stack of XMSS trees in which each tree signs the root of the tree below. | 7 FP, A Merkle tree of one-time keys |
| Identifiable abort | An abort that also names the cheating party. | 2 FP, What the attacker is assumed to do |
| Inclusion proof | The sibling at each level of a hash tree, from which a holder recomputes the root. | 6 FP, Hash trees |
| Interposer | A circuit board between processor and memory that reads or alters memory traffic; used against TEEs since 2025. | 3, Trusted execution environments |
| Inverse | The number $a^{-1}$ with $a \cdot a^{-1} \equiv 1$; dividing means multiplying by it. | 1 FP, Arithmetic on a clock |
| KEK | Key-encryption key: the key under which other keys are wrapped; it never leaves its device. | 3 FP, Key wrapping |
| KEM | Key encapsulation mechanism: produces a shared secret and a ciphertext that only the key holder can open. | 7, ML-KEM (FIPS 203) |
| Key ceremony | A scripted, witnessed session that creates or recovers keys, with authority split across M-of-N smart cards. | 3, Hardware security modules |
| Key path | Spending a Taproot output with one signature under its key. | 5 FP, Locking and unlocking |
| Key release | Handing a secret to an enclave only after checking its attestation report, encrypted to a key the report binds. | 3, Releasing a share to an attested signer |
| Key wrapping | Encrypting a key under a key-encryption key with an integrity check (AES key wrap, RFC 3394). | 3 FP, Key wrapping |
| Lagrange coefficient | The weight on each share when rebuilding $f(0)$; depends only on which shares are present. | 1 FP, Sharing a secret as a line through points |
| Lamport signature | A one-time signature that reveals one of two hashed secrets per digest bit. | 7 FP, Signatures from a hash alone: Lamport |
| Locking script | The condition an output sets for spending it (`scriptPubKey`). | 5 FP, Locking and unlocking |
| Locktime, sequence | Transaction fields carrying time locks and replacement signals. | 5 FP, What the signature covers: the sighash |
| Low-S | Bitcoin's rule that an ECDSA $s$ is at most $n/2$, removing one form of malleability. | 1, ECDSA |
| LWE | Learning with errors: recovering a secret from linear equations with small added errors. | 7 FP, Lattices in one bit |
| Malicious party | A corrupted party that may send anything, or nothing. | 2 FP, What the attacker is assumed to do |
| Measurement | A hash of the code and data loaded into an enclave, computed by the processor. | 3 FP, Remote attestation |
| Mempool | A node's pool of valid transactions waiting for a block. | 5 FP, Blocks, confirmation and regtest |
| Merkle root | The single hash at the top of a Merkle tree, committing to every item below it. | 6 FP, Hash trees |
| Merkle sum tree | A Merkle tree whose nodes also carry sums, each parent hashing both children's sums. | 6 FP, Adding sums |
| Merkle tree | A tree of hashes built by hashing items in pairs up to one root. | 6 FP, Hash trees |
| MiCA | Regulation (EU) 2023/1114 on crypto-assets; Article 75 sets the duties of a custodian. | 8, Regulation in the EU: MiCA |
| ML-DSA | FIPS 204 lattice signature; ML-DSA-65 has a 1,952-byte key and a 3,309-byte signature. | 7, ML-DSA (FIPS 204) |
| ML-KEM | FIPS 203 lattice key encapsulation; ML-KEM-768 has a 1,184-byte key and a 1,088-byte ciphertext. | 7, ML-KEM (FIPS 203) |
| Mobile adversary | An attacker who corrupts different machines at different times. | 2 FP, What the attacker is assumed to do |
| Modulo | Keeping only the remainder after division, as a clock does. | 1 FP, Arithmetic on a clock |
| MPC | Secure multi-party computation: parties compute a function of private inputs, each learning only the output. | 2 FP, Parties, rounds and a coordinator |
| Multiplicative share | One of two numbers whose product is the key (Lindell 2017). | 2 FP, Three ways to split a key |
| Netting | Summing a cycle's fills into one obligation per asset. | 5, Netting |
| Nitro Enclave | An isolated virtual machine carved from an AWS EC2 instance, with no storage or network, attested through AWS's PKI. | 3, Trusted execution environments |
| Nonce | A secret random number used once in a signature; reusing it reveals the key. | 1 FP, What a signature proves |
| One-time signature | A key that may sign only one message; a second signature leaks enough to forge. | 7 FP, Signatures from a hash alone: Lamport |
| Outpoint | The txid and output index that identify the output an input spends. | 5 FP, Coins are outputs, not balances |
| Paillier encryption | Additively homomorphic public-key encryption, used by two-party ECDSA. | 2 FP, Encryption that can be computed on; 2, Paillier encryption |
| Pedersen commitment | $C = vG + rH$: a hiding, binding point commitment; commitments add. | 6, Zero-knowledge proofs of liabilities |
| Permissioned ledger | A ledger whose operators and participants are admitted, not open to anyone. | 8 FP, Public and permissioned ledgers |
| PKCS#11 | The OASIS C interface to HSMs: sessions, logins, key handles, attributes and mechanisms. | 3, Hardware security modules |
| Point at infinity | The zero of the curve group, $\mathcal{O}$; the sum of a point and its reflection. | 1 FP, Points that can be added |
| Private key, public key | A secret scalar $d$, and the point $Q = dG$. | 1 FP, Easy forwards, infeasible backwards |
| Proactive refresh | Replacing every share with a new one for the same key, so old shares become useless. | 2, Proactive refresh |
| Proof of control | A signature under the custody key over a message that could not be prepared in advance. | 6 FP, Proof of control |
| Proof of knowledge | A zero-knowledge proof that the prover knows a secret, such as a discrete logarithm. | 2 FP, Zero-knowledge proofs |
| Proof of reserves | Evidence that assets held cover liabilities owed: a liabilities commitment plus proof of control. | 6, Intuition |
| Proof of work | A block-header hash below a target, found by trial; it makes rewriting blocks costly. | 5 FP, Blocks, confirmation and regtest |
| Public ledger | A ledger on which anyone can run a node and submit transactions, and every transaction is visible. | 8 FP, Public and permissioned ledgers |
| PvP | Payment versus payment: one currency moves if and only if the other does. | 8 FP, Delivery versus payment |
| Qualified custodian | Under the US adviser custody rule, a bank, broker-dealer, futures commission merchant or eligible foreign institution. | 8, Regulation in the US |
| Range proof | A zero-knowledge proof that a committed value lies in a stated range, such as $[0, 2^{64})$. | 6, Zero-knowledge proofs of liabilities |
| Regtest | Bitcoin Core's local test mode: blocks on command, worthless coins. | 5 FP, Blocks, confirmation and regtest |
| Remote attestation | Hardware's signed statement of which code runs in an enclave, checked by a verifier against expected values. | 3 FP, Remote attestation |
| Report data | Up to 64 bytes chosen by enclave code and signed into its attestation report, typically a hash of a public key. | 3 FP, Remote attestation |
| Reserve ratio | Assets divided by liabilities in a snapshot. | 6, Snapshot and attestation |
| Root of trust | The key a verifier trusts at the base of a chain of signatures, such as the processor maker's. | 3 FP, Remote attestation |
| ROS attack | Forging a threshold Schnorr signature by combining commitments across many concurrent sessions. | 2 FP, Many sessions at once |
| Round | One exchange in which every party sends and then waits for all the others. | 2 FP, Parties, rounds and a coordinator |
| Salt | Random bytes hashed with a value so that the value cannot be found by guessing. | 6 FP, Salts and what a proof reveals |
| Satoshi | The integer unit of bitcoin: $10^{-8}$ BTC. | 5 FP, Coins are outputs, not balances |
| Scalar | A whole number that multiplies a point; keys, nonces and shares are scalars modulo $n$. | 1 FP, The cycle: generator, order and scalar |
| Schnorr signature | The pair $(R, s)$ with $s = k + ed$ and $e$ a hash of $R$, the key and the message. | 1 FP, What a signature proves |
| Script path | Spending a Taproot output by revealing and satisfying a committed script. | 5 FP, Locking and unlocking |
| Sealing | Encrypting data under a key derived from the processor's secret and the enclave's measurement or signer. | 3 FP, Sealing |
| Security level | One of FIPS 140-3's four grades of physical protection and operator authentication. | 3 FP, Tamper response and certification levels |
| Semi-honest party | A corrupted party that follows the protocol but records everything it sees. | 2 FP, What the attacker is assumed to do |
| Sensitive key | A key an HSM never reveals in plaintext. | 3 FP, Key wrapping |
| Settlement finality | The legally defined point after which a settlement cannot be unwound. | 8 FP, Settlement finality |
| Settlement risk | The risk that one side of a trade delivers and the other does not. | 8 FP, Delivery versus payment |
| Share | One party's piece of a secret; for Shamir sharing, a point $(i, f(i))$. | 1 FP, Sharing a secret as a line through points |
| Shor's algorithm | Quantum algorithm that factors and computes discrete logarithms, breaking ECDSA, Schnorr, Ed25519 and Paillier. | 7, Intuition |
| Sibling | The other child of a node's parent in a hash tree. | 6 FP, Hash trees |
| Side channel | A measurable effect of a computation, such as its timing or power, that depends on a secret. | 3 FP, Side channels |
| Sighash | The 32-byte hash of a transaction's fields that a signature actually signs. | 5 FP, What the signature covers: the sighash |
| Signing quorum | The machines holding key shares, $t$ of which must take part in a signature. | 0, Two quorums; 2, Intuition |
| SLH-DSA | FIPS 205 stateless hash-based signature; SHA2-128f signatures are 17,088 bytes. | 7, SLH-DSA (FIPS 205) |
| Snapshot | The published record of liabilities root and total, assets, block, custody key and audit head. | 6, Snapshot and attestation |
| SOC report | An auditor's report on a service organisation's controls: SOC 1 for financial reporting, SOC 2 for the Trust Services Criteria. | 8, Assurance: SOC reports |
| Stablecoin | A token issued by a non-bank against reserves, redeemable at a fixed value. | 8 FP, Four forms of money on a ledger |
| Stateful signature | A scheme (XMSS, LMS) whose signer must record which one-time leaves it has used. | 7 FP, A Merkle tree of one-time keys |
| Tamper evidence, resistance, response | Seals that show opening; an enclosure hard to open; sensors that zeroise keys when opened. | 3 FP, Tamper response and certification levels |
| Taproot | Bitcoin's output type (BIP 341) locked to one 32-byte key, with optional committed scripts. | 5 FP, Locking and unlocking |
| TCB | Trusted computing base: everything that must behave correctly for a key to stay secret. | 3 FP, Three questions for any key store |
| TEE | Trusted execution environment: processor-protected memory and code on an ordinary server, with remote attestation. | 3, Intuition; 3, Trusted execution environments |
| Threshold ($t$-of-$n$) | Any $t$ of $n$ share holders can sign; $t - 1$ learn nothing and cannot sign. | 2 FP, What the attacker is assumed to do |
| Token | A balance on a ledger that moves when its holder's key signs. | 8, Intuition |
| Tokenisation | Moving an asset's register of ownership onto a ledger as tokens. | 8, Intuition |
| Tokenised deposit | A commercial bank deposit represented as a token; a claim on the bank. | 8 FP, Four forms of money on a ledger |
| Tokenised money market fund | Money market fund shares issued as tokens; used as yield-bearing collateral. | 8 FP, Four forms of money on a ledger |
| Trust Services Criteria | The AICPA criteria a SOC 2 report tests: security, and optionally availability, processing integrity, confidentiality, privacy. | 8, Assurance: SOC reports |
| Tweak | Adding $tG$ to a key, with $t$ a hash, so the key commits to extra data. | 5, Taproot outputs and the BIP86 tweak |
| Txid | A transaction's id: the double SHA-256 of its serialisation without witnesses. | 5 FP, Coins are outputs, not balances; 5 FP, Locking and unlocking |
| Type I, Type II | A SOC report on control design at one date, or on design and operation over a period. | 8, Assurance: SOC reports |
| UC security | Security that still holds when many sessions run concurrently alongside other protocols. | 2 FP, What the attacker is assumed to do |
| UTXO | An unspent transaction output: an amount and a spending condition. | 5 FP, Coins are outputs, not balances |
| Velocity limit | A cap on the total authorised in a rolling time window. | 4, The decision function |
| Whitelist | The set of destinations the policy allows for an asset. | 4, The decision function |
| Witness | The data that satisfies a locking script, such as a signature. | 5 FP, Locking and unlocking |
| WOTS+ | The Winternitz one-time signature of FIPS 205: 35 hash chains, with a checksum, per 16-byte digest. | 7 FP, Winternitz chains and the checksum |
| x-only key | A 32-byte public key (the $x$-coordinate); the point with even $y$ is meant. | 1, Schnorr and BIP340 |
| XMSS | A Merkle tree whose leaves are WOTS+ public keys; its root is the long-term public key. | 7 FP, A Merkle tree of one-time keys |
| Zero-knowledge proof | A proof that a statement about a secret is true, revealing nothing else. | 2 FP, Zero-knowledge proofs |
| Zeroisation | Overwriting keys when tampering is detected, before an attacker can read them. | 3 FP, Tamper response and certification levels |
