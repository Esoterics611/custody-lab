# Glossary

Every term the manual defines, explained in two to four sentences, with links to the sections that
teach it. Chapter 0 is the orientation, and "FP" means a chapter's First principles section.
Abbreviations such as HSM, KEM and TEE are listed under the abbreviation.

[A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [F](#f) · [G](#g) · [H](#h) · [I](#i) · [K](#k) · [L](#l) · [M](#m) · [N](#n) · [O](#o) · [P](#p) · [Q](#q) · [R](#r) · [S](#s) · [T](#t) · [U](#u) · [V](#v) · [W](#w) · [X](#x) · [Z](#z)

## A

**Abort.** A protocol run that stops without producing a signature because a party's misbehaviour was detected. Aborting is the safe outcome: no signature is better than a wrong one. It does not by itself say who cheated; see identifiable abort. *Taught in:* [2 FP, What the attacker is assumed to do](../manual/chapters/02-mpc-custody.md#what-the-attacker-is-assumed-to-do).

**Additive share.** One of several numbers that add up to the key modulo the group order $n$. Every holder is needed, because leaving one out changes the sum. On the toy curve, 21 and 19 are additive shares of the key 9, since $21 + 19 = 40 \equiv 9 \pmod{31}$; threshold Schnorr signing turns Shamir shares into additive shares for each session. *Taught in:* [2 FP, Three ways to split a key](../manual/chapters/02-mpc-custody.md#three-ways-to-split-a-key).

**Address.** A locking script written in a checksummed text form for people to copy. Paying an address means creating an output with that locking script. Taproot addresses use bech32m and start `bc1p` on the main network and `bcrt1p` on regtest. *Taught in:* [5 FP, Locking and unlocking](../manual/chapters/05-settlement.md#locking-and-unlocking).

**Adversary model.** The statement of which parties an attacker controls, when, and what those parties may do. A security claim means nothing without one: a protocol safe against a machine whose logs leak can be broken by a machine that lies. It plays the role of a test plan's fault model. *Taught in:* [2 FP, What the attacker is assumed to do](../manual/chapters/02-mpc-custody.md#what-the-attacker-is-assumed-to-do).

**Allowlist.** The list of addresses a token's issuer, usually through its transfer agent, permits to hold the token; a transfer to any other address fails. It is the custodian's whitelist enforced by the asset itself: the custodian refuses to send to unknown addresses, and the token refuses to arrive at them. *Taught in:* [8 FP, Public and permissioned ledgers](../manual/chapters/08-industry.md#public-and-permissioned-ledgers).

**Amount tier.** A band of payment sizes with its own approval quorum. The policy engine uses the smallest tier the amount fits and refuses amounts above every tier. In the demo, up to 0.1 BTC needs one approval and up to 10 BTC needs two, so 0.85 BTC needs two. *Taught in:* [4 FP, Rules: tiers, whitelist and a rolling window](../manual/chapters/04-policy.md#rules-tiers-whitelist-and-a-rolling-window); [4, The decision function](../manual/chapters/04-policy.md#the-decision-function).

**Anchoring.** Publishing the head hash of an audit log somewhere the operator cannot change it. A hash chain detects edits inside the log, but not truncation or a wholesale rewrite; comparing the current head with the anchored one detects both. The demo anchors the head in every proof-of-reserves snapshot. *Taught in:* [4, Hash-chained audit log](../manual/chapters/04-policy.md#hash-chained-audit-log).

**Approval quorum.** The people who must approve an instruction before the policy engine authorises it, each with a signature from their own device. In the demo, bob and carol; the initiator's own approval does not count. It is separate from the signing quorum of machines, and the authorisation is the only link between them. *Taught in:* [0, Two quorums](../manual/chapters/00-orientation.md#two-quorums); [4](../manual/chapters/04-policy.md).

**Assets, liabilities.** In a proof of reserves, assets are the coins the custodian controls on chain, which anyone can see, and liabilities are the balances it owes its clients, which are private. A proof of reserves shows assets at least equal to liabilities. *Taught in:* [6, What this chapter is for](../manual/chapters/06-reserves.md#what-this-chapter-is-for).

**Atomic settlement.** Both legs of a trade carried out in one ledger transaction, valid or invalid together, so there is no moment at which one has moved and the other has not. It removes settlement risk when the asset and the cash are on the same ledger. *Taught in:* [8 FP, Delivery versus payment](../manual/chapters/08-industry.md#delivery-versus-payment).

**Attestation.** In this manual's chapter 6 sense: the custodian's signed statement of a reserves snapshot's contents, made under the custody key. Compare remote attestation, which is hardware's signed statement about software. *Taught in:* [6 FP, Proof of control](../manual/chapters/06-reserves.md#proof-of-control).

**Attestation report.** The measurement of an enclave's code plus up to 64 bytes of report data, signed through the processor maker's or the cloud provider's root of trust. A verifier checks the signature, the measurement and the report data before trusting the enclave. *Taught in:* [3 FP, Remote attestation](../manual/chapters/03-key-storage.md#remote-attestation).

**Authenticated encryption.** Encryption that also computes a short tag over the ciphertext, so that any modification makes decryption fail instead of returning altered data. AES-GCM is the common form; it needs a fresh 12-byte nonce for every encryption under one key. *Taught in:* [3 FP, Symmetric encryption in brief](../manual/chapters/03-key-storage.md#symmetric-encryption-in-brief).

**Authorisation.** A short-lived token, signed by the policy engine's authority key, naming the exact 32 bytes the signers may sign, the instruction it came from, a unique identifier and an expiry. Each signer checks the signatures, the expiry, that the bytes match its signing request, and that the token is unused, before contributing a share. *Taught in:* [4, Authorisation](../manual/chapters/04-policy.md#authorisation).

**Authority key.** The policy engine's signing key, an Ed25519 key and an ML-DSA-65 key used together, that signs authorisations. The signers hold only its public half. Whoever holds it can authorise any transaction the signers' checks allow, so it is the most valuable secret after the shares and belongs in an HSM. *Taught in:* [4 FP, One permission per transaction: the authorisation](../manual/chapters/04-policy.md#one-permission-per-transaction-the-authorisation); [4, Authorisation](../manual/chapters/04-policy.md#authorisation).

## B

**Binding (commitment).** The property that the committer cannot later open a commitment to a different value. A hash commitment is binding because finding a second input with the same hash is infeasible; a point commitment $vG$ is binding because a point has exactly one position on the cycle. *Taught in:* [2 FP, Commitments](../manual/chapters/02-mpc-custody.md#commitments).

**Binding factor.** In FROST, a hash $\rho_i$ of the message, the group key and the full list of round-one commitments, computed for each signer. It weights the binding nonce, so any change to the message or the commitment list changes every signer's effective nonce, which defeats attacks that choose values after seeing others'. *Taught in:* [2 FP, Many sessions at once](../manual/chapters/02-mpc-custody.md#many-sessions-at-once); [2, FROST](../manual/chapters/02-mpc-custody.md#frost).

**Binding nonce.** The second of a FROST signer's two nonces, $e_i$, committed in round one as $E_i = e_i G$. Weighted by the binding factor, it ties the signer's effective nonce $d_i + \rho_i e_i$ to one message and one commitment list. *Taught in:* [2 FP, Many sessions at once](../manual/chapters/02-mpc-custody.md#many-sessions-at-once); [2, FROST](../manual/chapters/02-mpc-custody.md#frost).

**BIP340.** Bitcoin's Schnorr signature standard, used by Taproot. It adds three rules to textbook Schnorr: x-only 32-byte keys, tagged hashes, and nonces derived from the key, the message and extra randomness. Signatures are 64 bytes. *Taught in:* [1, Schnorr and BIP340](../manual/chapters/01-foundations.md#schnorr-and-bip340).

**BIP86.** A Taproot output whose key is tweaked to commit to an empty script tree, so it can be spent only by the key path. Anyone who knows the untweaked key can confirm that no hidden spending script exists. The demo's custody address is a BIP86 output. *Taught in:* [5, Taproot outputs and the BIP86 tweak](../manual/chapters/05-settlement.md#taproot-outputs-and-the-bip86-tweak).

**Block.** A batch of transactions with a proof of work, containing the hash of the block before it, so the blocks form a chain. Changing an old transaction would change its block's hash and break every later link. *Taught in:* [5 FP, Blocks, confirmation and regtest](../manual/chapters/05-settlement.md#blocks-confirmation-and-regtest).

**Broadcast.** A protocol message sent to every party, such as a commitment. Compare a private channel, which reaches one party only. *Taught in:* [2 FP, Parties, rounds and a coordinator](../manual/chapters/02-mpc-custody.md#parties-rounds-and-a-coordinator).

## C

**Canonical encoding.** An encoding that gives every value exactly one byte representation. Hashes and signatures cover bytes, not meaning, so `1.50` and `1.5`, or two field orders of the same JSON object, must encode identically or two systems disagree about the digest of one instruction. The policy engine sorts keys, removes whitespace and normalises decimals. *Taught in:* [4, Canonical encoding](../manual/chapters/04-policy.md#canonical-encoding).

**CASP.** Crypto-asset service provider: a firm licensed under MiCA to provide services such as holding crypto-assets for clients. Custody and administration for clients is a licensed service under MiCA Article 75. *Taught in:* [8, Regulation in the EU: MiCA](../manual/chapters/08-industry.md#regulation-in-the-eu-mica).

**CBDC.** Central bank digital currency: central bank money issued as a token. Wholesale CBDC is held by banks only and settles interbank and cross-border payments; retail CBDC is for the public, like a digital form of banknotes. *Taught in:* [8 FP, Four forms of money on a ledger](../manual/chapters/08-industry.md#four-forms-of-money-on-a-ledger).

**Chain reorganisation.** The replacement of recent blocks by a longer competing branch, which can turn a confirmed transaction back into an unconfirmed one. It is why a custodian waits for several confirmations before treating a settlement as final. *Taught in:* [9, Failure modes](../manual/chapters/09-capstone.md#failure-modes).

**Change.** The output that returns the remainder of a spent UTXO, less the fee, to the payer. Paying 0.85 BTC from a 5.00 BTC coin creates 0.85 BTC to the payee and 4.1499969 BTC of change. A transaction that leaves out its change output pays the whole remainder to the miner. *Taught in:* [5 FP, Coins are outputs, not balances](../manual/chapters/05-settlement.md#coins-are-outputs-not-balances).

**Checksum (Winternitz).** An extra signed value equal to the sum of $(w - 1 - a_i)$ over the message digits $a_i$. Anyone can step a hash chain forwards to raise a digit, but raising a digit lowers the checksum, which would need some chain stepped backwards: inverting the hash. That stops the forgery. *Taught in:* [7 FP, Winternitz chains and the checksum](../manual/chapters/07-post-quantum.md#winternitz-chains-and-the-checksum).

**Coin selection.** Choosing which coins at the custody address a payment spends. Coins at one address are interchangeable, so the choice is made on cost, not on whose coins they are: every coin spent needs its own signature. The demo spends the smallest single coin that covers the payment and its fee. *Taught in:* [the demo walkthrough, Which coin to spend](../manual/demo-walkthrough.md#which-coin-to-spend).

**Cold storage.** Holdings whose signing needs at least one share kept on a device that is never connected to a network, reached through an air gap in a scheduled ceremony. It holds most of a custodian's assets and trades signing speed for safety. *Taught in:* [9, Deep dives](../manual/chapters/09-capstone.md#deep-dives).

**Commitment.** A value published now that fixes a choice before information that could bias it arrives, and that is opened later. A sealed bid is the physical version. Schnorr's $R = kG$ commits to the nonce before the challenge, and FROST's first round commits to each signer's nonces. *Taught in:* [1 FP, What a signature proves](../manual/chapters/01-foundations.md#what-a-signature-proves); [2 FP, Commitments](../manual/chapters/02-mpc-custody.md#commitments).

**Confidential virtual machine.** A whole virtual machine whose memory is encrypted and protected against the hypervisor, such as AMD SEV-SNP or Intel TDX. Ordinary software runs inside it unmodified, at the cost of a larger trusted computing base than a process enclave. *Taught in:* [3, Trusted execution environments](../manual/chapters/03-key-storage.md#trusted-execution-environments).

**Confirmation.** A block containing a transaction, or any block after it. A transaction in a block has one confirmation and each later block adds one; each makes reversal more expensive, and none makes it impossible. Six is the customary figure for large Bitcoin transfers. *Taught in:* [5 FP, Blocks, confirmation and regtest](../manual/chapters/05-settlement.md#blocks-confirmation-and-regtest).

**Constant-time code.** Code whose running time and memory accesses do not depend on secret values, so timing them reveals nothing. Comparing bytes with `hmac.compare_digest` instead of stopping at the first difference is the simplest example. *Taught in:* [3 FP, Side channels](../manual/chapters/03-key-storage.md#side-channels).

**Context string.** Up to 255 bytes bound into an ML-DSA or SLH-DSA signature to separate the uses of one key: a signature made with one context string does not verify with another. The demo's authorisations use `custody-lab/authorisation`. *Taught in:* [7, The demo's hybrid authorisation](../manual/chapters/07-post-quantum.md#the-demos-hybrid-authorisation).

**Coordinator.** The process that relays protocol messages between signers and combines their results. It holds no share and cannot sign; compromising it allows denial of service but not an unapproved signature, because every signer checks the authorisation itself. *Taught in:* [2 FP, Parties, rounds and a coordinator](../manual/chapters/02-mpc-custody.md#parties-rounds-and-a-coordinator).

**Corrupted party.** A party the attacker controls. A $t$-of-$n$ scheme promises that up to $t - 1$ corrupted parties learn nothing about the key and cannot sign. *Taught in:* [2 FP, What the attacker is assumed to do](../manual/chapters/02-mpc-custody.md#what-the-attacker-is-assumed-to-do).

**CPFP.** Child-pays-for-parent: unsticking a low-fee transaction by spending one of its outputs, usually its change, in a new transaction whose fee is high enough to pay for both. Miners include the pair together. *Taught in:* [9, Failure modes](../manual/chapters/09-capstone.md#failure-modes).

**Custodian.** A firm that holds assets on behalf of clients. For bitcoin there is no register to correct, so the custodian's job is to control who can sign with the keys that hold client coins, and for which payments. *Taught in:* [0, What a custodian does](../manual/chapters/00-orientation.md#what-a-custodian-does).

## D

**Default-deny.** Refusing anything the policy does not explicitly allow: an unknown asset, an unlisted address or an amount above every tier is refused, not passed through. A misconfiguration therefore fails safe, which matters because a broadcast settlement cannot be reversed. *Taught in:* [4 FP, Default deny](../manual/chapters/04-policy.md#default-deny); [4, The decision function](../manual/chapters/04-policy.md#the-decision-function).

**Digest.** The hash of a message's canonical bytes. Approvals and signatures are made over digests, so a change to any field of the message produces a different digest and the old signature no longer applies. *Taught in:* [4 FP, Approvals: four eyes, signed](../manual/chapters/04-policy.md#approvals-four-eyes-signed); [1, Hash functions](../manual/chapters/01-foundations.md#hash-functions).

**Digital signature.** A number computed from a private key and the exact bytes of a message, which anyone with the public key can check. Changing one byte of the message, or checking against a different public key, makes the check fail, and nobody without the private key can produce one that passes. *Taught in:* [0, Signatures](../manual/chapters/00-orientation.md#signatures).

**Discrete logarithm problem.** Recovering the private key $d$ from the public key $Q = dG$: finding how many steps along the cycle $Q$ sits. On the toy curve trying every count finds $d = 7$ on the seventh try; on secp256k1 the best known ordinary methods need about $2^{128}$ steps. A large quantum computer running Shor's algorithm would solve it. *Taught in:* [1 FP, Easy forwards, infeasible backwards](../manual/chapters/01-foundations.md#easy-forwards-infeasible-backwards).

**DKG.** Distributed key generation: each party deals a Shamir sharing of its own random secret, each party's share is the sum of what it receives, and the key is the sum of everyone's secrets, which no party ever holds. A proof of knowledge from each party stops a rogue-key attack. *Taught in:* [2, Distributed key generation](../manual/chapters/02-mpc-custody.md#distributed-key-generation).

**Domain separation.** Hashing each class of message under its own tag, so that a value computed for one purpose can never equal one computed for another. A reserves attestation hashed with its own tag can never be a valid transaction sighash, which uses the tag `TapSighash`. *Taught in:* [1, Hash functions](../manual/chapters/01-foundations.md#hash-functions); [6 FP, Proof of control](../manual/chapters/06-reserves.md#proof-of-control).

**Double spend.** Promising the same coins to two payees, of whom only one can receive them. A payment still in the mempool can be replaced by another spending the same coins (RBF), so a custodian credits a deposit only once it is in a block. The demo's day shows a client replacing its deposit before it confirms. *Taught in:* [the demo walkthrough, Deposits: credit only what has confirmed](../manual/demo-walkthrough.md#deposits-credit-only-what-has-confirmed).

**Double-and-add.** Computing $dG$ by repeated doubling ($2G$, $4G$, $8G$, ...) and adding the doublings that make up $d$: $13G = 8G + 4G + G$. A 256-bit key needs about 256 doublings and at most 256 additions. The teaching version branches on secret bits, which leaks them through timing. *Taught in:* [1 FP, Easy forwards, infeasible backwards](../manual/chapters/01-foundations.md#easy-forwards-infeasible-backwards).

**Dust.** An output too small for Bitcoin Core to relay under its default policy: below 330 satoshis for a Taproot output. The demo's transaction builder adds change below that limit to the fee instead of creating it. *Taught in:* [5 FP, Coins are outputs, not balances](../manual/chapters/05-settlement.md#coins-are-outputs-not-balances).

**DvP.** Delivery versus payment: the asset moves if and only if the cash moves. It removes settlement risk, and on a single ledger it can be atomic: both legs in one transaction. *Taught in:* [8 FP, Delivery versus payment](../manual/chapters/08-industry.md#delivery-versus-payment).

## E

**ECDSA.** The signature scheme $s = k^{-1}(z + rd) \bmod n$, with $r$ taken from the point $kG$. Bitcoin's older outputs and Ethereum use it. Because it multiplies one secret by the inverse of another, splitting it between parties needs Paillier encryption or oblivious transfer, unlike Schnorr. *Taught in:* [1, ECDSA](../manual/chapters/01-foundations.md#ecdsa).

**Ed25519.** Schnorr-type signatures (EdDSA) on Curve25519, with a nonce derived entirely from the private key and the message, so a single signer can never repeat it. The demo's approvals are Ed25519 signatures, and the authority key includes an Ed25519 key. *Taught in:* [1, EdDSA](../manual/chapters/01-foundations.md#eddsa).

**Elliptic curve.** The set of points $(x, y)$ satisfying an equation such as $y^2 = x^3 + 7$ modulo a prime, plus the point at infinity. Its points can be added by a geometric rule, and repeatedly adding a generator is easy to do and infeasible to undo, which is what a key pair needs. *Taught in:* [1 FP, Points that can be added](../manual/chapters/01-foundations.md#points-that-can-be-added); [1, Fields and curves](../manual/chapters/01-foundations.md#fields-and-curves).

**Enclave.** The protected region of a trusted execution environment: code and memory the host's operating system and hypervisor cannot read. Its code is identified by a measurement that the processor signs into an attestation report. *Taught in:* [3, What this chapter is for](../manual/chapters/03-key-storage.md#what-this-chapter-is-for); [3, Trusted execution environments](../manual/chapters/03-key-storage.md#trusted-execution-environments).

**Extractable key.** A key an HSM may export, and then only wrapped under a key-encryption key. A non-extractable key cannot leave through the standard interface at all, so its backups depend on the vendor's own mechanism. *Taught in:* [3 FP, Key wrapping](../manual/chapters/03-key-storage.md#key-wrapping).

## F

**Fee.** The total of a transaction's inputs minus the total of its outputs, collected by the miner who includes it. It is not a field in the transaction, which is why a missing change output silently becomes fee and why the demo caps the fee before authorising. *Taught in:* [5 FP, Coins are outputs, not balances](../manual/chapters/05-settlement.md#coins-are-outputs-not-balances).

**Feldman commitment.** Publishing each coefficient of a sharing polynomial multiplied by $G$, so that a receiver can check its share: $f(j)G$ must equal $C_0 + jC_1 + \dots$. For $f(x) = 9 + 5x$, party 3's share 24 passes because $24G = 9G + 3 \times 5G$. The first commitment is the shared secret's public key. *Taught in:* [2 FP, Commitments](../manual/chapters/02-mpc-custody.md#commitments).

**Fiat-Shamir transform.** Replacing a verifier's random challenge with a hash of the commitment, the public key and the message, which turns a live identification protocol into a signature anyone can check later. The prover cannot steer the hash, so it still cannot choose its commitment after the challenge. *Taught in:* [1 FP, From a conversation to a signature](../manual/chapters/01-foundations.md#from-a-conversation-to-a-signature).

**Fiat-Shamir with aborts.** The lattice-signature technique in which the signer discards and retries any response that is too large, because such a response would show traces of the secret. ML-DSA signs this way; the retry is what makes it hard to sign with a threshold. *Taught in:* [7, ML-DSA (FIPS 204)](../manual/chapters/07-post-quantum.md#ml-dsa-fips-204).

**Finite field.** The numbers $0$ to $p - 1$ for a prime $p$, with addition, subtraction, multiplication and division modulo $p$. Every non-zero number has an inverse, so every division is exact, and every result has the same size. *Taught in:* [1 FP, Arithmetic on a clock](../manual/chapters/01-foundations.md#arithmetic-on-a-clock).

**FIPS 140-3.** The US and Canadian standard (aligned with ISO/IEC 19790) under which an accredited laboratory certifies one version of a cryptographic module at one of four security levels. A firmware update that adds an algorithm is outside the certificate until the new version is validated. *Taught in:* [3 FP, Tamper response and certification levels](../manual/chapters/03-key-storage.md#tamper-response-and-certification-levels).

**FORS.** The few-time signature scheme at the bottom of SLH-DSA, which signs the message digest at a leaf chosen by a hash of the message. A few-time scheme tolerates a small number of signatures per key, which is why SLH-DSA needs no record of used leaves. *Taught in:* [7 FP, A Merkle tree of one-time keys](../manual/chapters/07-post-quantum.md#a-merkle-tree-of-one-time-keys).

**Four-eyes.** Requiring approval by someone other than the person who raised a request (maker-checker). The policy engine enforces it by not counting the initiator's approval. *Taught in:* [4 FP, Approvals: four eyes, signed](../manual/chapters/04-policy.md#approvals-four-eyes-signed).

**FROST.** Flexible Round-Optimized Schnorr Threshold signatures (RFC 9591): threshold Schnorr in two rounds, commit then sign, with a binding factor that ties every nonce to one message and commitment list. The output is an ordinary Schnorr signature. It is the demo's signing protocol, through the Zcash Foundation crate. *Taught in:* [2, FROST](../manual/chapters/02-mpc-custody.md#frost).

## G

**Generator.** The published point $G$ from which every key is measured: a public key is $G$ added to itself $d$ times. On the toy curve, $G = (2, 12)$. *Taught in:* [1 FP, The cycle: generator, order and scalar](../manual/chapters/01-foundations.md#the-cycle-generator-order-and-scalar).

**Group.** A set with an operation that is commutative and associative, has a zero and gives every element a negative. Elliptic-curve points under point addition form a group, which is what makes expressions such as $3P + Q$ unambiguous. *Taught in:* [1 FP, Points that can be added](../manual/chapters/01-foundations.md#points-that-can-be-added).

**Group order.** The length $n$ of the cycle $G, 2G, \dots, nG = \mathcal{O}$. Keys, nonces and shares are numbers modulo $n$, while point coordinates are numbers modulo the field prime. On the toy curve $n = 31$. *Taught in:* [1 FP, The cycle: generator, order and scalar](../manual/chapters/01-foundations.md#the-cycle-generator-order-and-scalar).

**Grover's algorithm.** A quantum algorithm that searches $2^k$ possibilities in about $2^{k/2}$ steps. It weakens hash functions and symmetric keys, halving their effective size, but does not break them: a 256-bit key behaves like a 128-bit one. *Taught in:* [7 FP, What a quantum computer breaks](../manual/chapters/07-post-quantum.md#what-a-quantum-computer-breaks).

## H

**Harvest now, decrypt later.** Recording ciphertext today in order to decrypt it once a quantum computer exists. It makes long-lived encrypted data, such as share backups, exposed now, which is why backups move to post-quantum encryption first. *Taught in:* [7, What this chapter is for](../manual/chapters/07-post-quantum.md#what-this-chapter-is-for).

**Hash chain.** A value hashed repeatedly: position 0 is a secret, position 1 its hash, and so on. Anyone can step forwards along it; stepping backwards means inverting the hash. Winternitz signatures reveal a position along a chain to sign a digit. *Taught in:* [7 FP, Winternitz chains and the checksum](../manual/chapters/07-post-quantum.md#winternitz-chains-and-the-checksum).

**Hash function.** A function that maps an input of any length to a fixed-size digest (32 bytes for SHA-256) and resists preimage, second-preimage and collision attacks. It works as a fingerprint: inputs that differ in one character have unrelated digests. *Taught in:* [0, Fingerprints: hash functions](../manual/chapters/00-orientation.md#fingerprints-hash-functions); [1 FP, Fingerprints: hash functions](../manual/chapters/01-foundations.md#fingerprints-hash-functions); [1, Hash functions](../manual/chapters/01-foundations.md#hash-functions).

**Head.** The hash of the newest entry in a hash-chained log. Publishing it somewhere the operator cannot change is anchoring; the demo puts it in every proof-of-reserves snapshot. *Taught in:* [4 FP, A log that shows its own edits](../manual/chapters/04-policy.md#a-log-that-shows-its-own-edits).

**Herstatt risk.** The risk of paying one currency and not receiving the other in a cross-currency trade. It is named after a German bank closed in 1974 after it had received Deutsche marks and before it paid the dollars it owed. Payment versus payment removes it. *Taught in:* [8 FP, Delivery versus payment](../manual/chapters/08-industry.md#delivery-versus-payment).

**Hiding (commitment).** The property that a commitment reveals nothing about the committed value. A hash commitment needs a random value mixed in to be hiding: without it, a value from a small set, such as "buy" or "sell", is found by hashing each candidate. *Taught in:* [2 FP, Commitments](../manual/chapters/02-mpc-custody.md#commitments).

**Hiding nonce.** The first of a FROST signer's two nonces, $d_i$, committed in round one as $D_i = d_i G$. Together with the binding nonce weighted by the binding factor, it forms the signer's effective nonce. *Taught in:* [2 FP, Many sessions at once](../manual/chapters/02-mpc-custody.md#many-sessions-at-once); [2, FROST](../manual/chapters/02-mpc-custody.md#frost).

**Homomorphic encryption.** Encryption in which operations on ciphertexts act on the plaintexts inside them. Paillier is additively homomorphic: multiplying two ciphertexts gives an encryption of the sum of their plaintexts. *Taught in:* [2 FP, Encryption that can be computed on](../manual/chapters/02-mpc-custody.md#encryption-that-can-be-computed-on).

**Hot wallet.** Online signers that sign automatically under policy, without a human approval for each payment, within small velocity limits. It holds a small share of the assets, for speed. *Taught in:* [9, Deep dives](../manual/chapters/09-capstone.md#deep-dives).

**HSM.** Hardware security module: a separate, tamper-resistant device that keeps keys and uses them inside itself, exporting them only wrapped under a key that never leaves. It protects a key against copying, not against misuse by whoever holds the login. *Taught in:* [3, What this chapter is for](../manual/chapters/03-key-storage.md#what-this-chapter-is-for); [3, Hardware security modules](../manual/chapters/03-key-storage.md#hardware-security-modules).

**Hybrid signature.** Two signatures of different schemes over one payload, both required to verify, so a forger must break both. The demo's authorisations carry Ed25519, which a quantum computer would break, and ML-DSA-65, which is new enough that a flaw cannot be ruled out. *Taught in:* [7, The demo's hybrid authorisation](../manual/chapters/07-post-quantum.md#the-demos-hybrid-authorisation).

**Hypertree.** SLH-DSA's stack of XMSS trees in which each tree signs the root of the tree below it, giving a very large number of leaves under one public key. *Taught in:* [7 FP, A Merkle tree of one-time keys](../manual/chapters/07-post-quantum.md#a-merkle-tree-of-one-time-keys).

**Hypervisor.** The software that runs virtual machines on a physical server; in a public cloud, the provider runs it. Confidential virtual machines protect their memory against it. *Taught in:* [3, Trusted execution environments](../manual/chapters/03-key-storage.md#trusted-execution-environments).

## I

**Identifiable abort.** An abort that also names the party that cheated, so operators can exclude that signer and continue with the others instead of only retrying. CGGMP provides it. *Taught in:* [2 FP, What the attacker is assumed to do](../manual/chapters/02-mpc-custody.md#what-the-attacker-is-assumed-to-do).

**Inclusion proof.** The sibling at each level of a hash tree on the path from one leaf to the root. Its holder recomputes each parent in turn and compares the result with the published root. A tree over a million clients needs 20 siblings per proof. *Taught in:* [6 FP, Hash trees](../manual/chapters/06-reserves.md#hash-trees).

**Input, output.** A transaction's inputs name the UTXOs it spends, each by its outpoint; its outputs are the new UTXOs it creates, each an amount and a locking script. An input spends its UTXO whole. *Taught in:* [5 FP, Coins are outputs, not balances](../manual/chapters/05-settlement.md#coins-are-outputs-not-balances).

**Internalised settlement.** Settling part of clients' trades by moving balances between them in the custodian's ledger, so that only the net difference moves on chain. In the demo's day, alpha-capital sells 1.20 BTC and beta-fund buys 0.45 BTC: 0.75 BTC goes to the exchange, and 0.45 BTC moves between the two clients in the books only. *Taught in:* [the demo walkthrough, Netting across clients](../manual/demo-walkthrough.md#netting-across-clients).

**Interposer.** A small circuit board placed between a processor and a memory module that reads or alters the memory traffic. Attacks using one against TEE memory encryption were published from late 2025, and processor vendors place them outside their threat models. *Taught in:* [3, Trusted execution environments](../manual/chapters/03-key-storage.md#trusted-execution-environments).

**Inverse.** The number $a^{-1}$ with $a \times a^{-1} \equiv 1$; dividing by $a$ means multiplying by it. Modulo 7 the inverse of 3 is 5, because $3 \times 5 = 15 \equiv 1$. A number has an inverse modulo $m$ only if it shares no factor with $m$. *Taught in:* [1 FP, Arithmetic on a clock](../manual/chapters/01-foundations.md#arithmetic-on-a-clock).

## K

**KEK.** Key-encryption key: the key under which other keys are wrapped for backup or transport. It never leaves its device. *Taught in:* [3 FP, Key wrapping](../manual/chapters/03-key-storage.md#key-wrapping).

**KEM.** Key encapsulation mechanism: anyone holding a public key can create a fresh shared secret together with an encapsulation of it, and only the private-key holder can recover the secret from the encapsulation. Both sides then use the secret as a symmetric key. ML-KEM is the post-quantum standard. *Taught in:* [7, ML-KEM (FIPS 203)](../manual/chapters/07-post-quantum.md#ml-kem-fips-203).

**Key ceremony.** A scripted, witnessed session that creates or recovers keys, with administrative authority split across M-of-N smart cards held by different people. The cards rebuild a key inside the HSM, which is Shamir sharing with the device as the trusted meeting place. *Taught in:* [3, Hardware security modules](../manual/chapters/03-key-storage.md#hardware-security-modules).

**Key derivation function.** A function, such as HKDF, that derives independent keys from one secret, each labelled for its purpose. No derived key reveals the secret or any other derived key. *Taught in:* [3 FP, Symmetric encryption in brief](../manual/chapters/03-key-storage.md#symmetric-encryption-in-brief); [3 FP, Sealing](../manual/chapters/03-key-storage.md#sealing).

**Key path.** Spending a Taproot output with one BIP340 signature under its (tweaked) key, as the demo does. On chain it looks like any single-key spend. *Taught in:* [5 FP, Locking and unlocking](../manual/chapters/05-settlement.md#locking-and-unlocking).

**Key release.** Handing a secret to an enclave only after checking its attestation report (signature, measurement and report data), encrypted to a public key the report binds. AWS Nitro Enclaves with AWS KMS implement this pattern. *Taught in:* [3, Releasing a share to an attested signer](../manual/chapters/03-key-storage.md#releasing-a-share-to-an-attested-signer).

**Key wrapping.** Encrypting a key under a key-encryption key with an integrity check, so a modified wrapped key fails to unwrap instead of unwrapping to a wrong key. AES key wrap (RFC 3394) is the standard; a 16-byte key wraps into 24 bytes. *Taught in:* [3 FP, Key wrapping](../manual/chapters/03-key-storage.md#key-wrapping).

## L

**Lagrange coefficient.** The weight on each share when recovering the secret $f(0)$ as a weighted sum of shares. It depends only on which shares are present, not on their values. For shares 1 and 3 the weights are $3/2$ and $-1/2$, which modulo 31 are 17 and 15. *Taught in:* [1 FP, Sharing a secret as a line through points](../manual/chapters/01-foundations.md#sharing-a-secret-as-a-line-through-points).

**Lamport signature.** A one-time signature built from a hash alone: keep two secrets per digest bit, publish their hashes, and sign by revealing the secret matching each bit. A second signature with the same key reveals more secrets, and after a handful a forger can sign anything. *Taught in:* [7 FP, Signatures from a hash alone: Lamport](../manual/chapters/07-post-quantum.md#signatures-from-a-hash-alone-lamport).

**Layer 2.** A chain that processes transactions itself and periodically records its state on another chain, such as Base on Ethereum. *Taught in:* [8, Institutional ledgers: Canton and Kinexys](../manual/chapters/08-industry.md#institutional-ledgers-canton-and-kinexys).

**Ledger.** A record of who owns what. A bank's ledger is its own database; Bitcoin's is public, and many independent nodes keep identical copies and check every change against the same rules. *Taught in:* [0, A ledger that nobody operates](../manual/chapters/00-orientation.md#a-ledger-that-nobody-operates).

**Liveness.** The property that something good eventually happens: every approved settlement completes. A liveness failure, such as a signer being down, delays work but can be retried. *Taught in:* [9 FP, Safety and liveness](../manual/chapters/09-capstone.md#safety-and-liveness); [9, Failure modes](../manual/chapters/09-capstone.md#failure-modes).

**Locking script.** The condition an output sets for spending it (`scriptPubKey`). A Taproot output's locking script is `OP_1 <32-byte key>`, 34 bytes: a version 1 witness program whose condition is a signature under that key. *Taught in:* [5 FP, Locking and unlocking](../manual/chapters/05-settlement.md#locking-and-unlocking).

**Locktime, sequence.** Transaction fields that carry time locks and replacement signals. The demo sets locktime 0 and sequence `0xFFFFFFFD`, which allows the transaction to be replaced by one with a higher fee. *Taught in:* [5 FP, What the signature covers: the sighash](../manual/chapters/05-settlement.md#what-the-signature-covers-the-sighash).

**Low-S.** Bitcoin's rule that an ECDSA signature's $s$ is at most $n/2$. Both $(r, s)$ and $(r, n - s)$ verify, so anyone could otherwise rewrite one valid signature into another; accepting only the low form removes that. *Taught in:* [1, ECDSA](../manual/chapters/01-foundations.md#ecdsa).

**LWE.** Learning with errors: recovering a secret from many linear equations, each with a small random error added. Without the errors school elimination solves it; with them it is believed hard for quantum computers too. ML-KEM and ML-DSA rest on its module variant. *Taught in:* [7 FP, Lattices in one bit](../manual/chapters/07-post-quantum.md#lattices-in-one-bit).

## M

**Malicious party.** A corrupted party that may send anything: wrong values, values chosen after seeing others', or nothing at all. It models an attacker who controls the process, and a protocol secure only against semi-honest parties can be broken by one. *Taught in:* [2 FP, What the attacker is assumed to do](../manual/chapters/02-mpc-custody.md#what-the-attacker-is-assumed-to-do).

**Margin.** Collateral posted against a derivatives or lending position. Tokenised fund shares can be posted as margin at any hour while they keep earning the fund's yield. *Taught in:* [8, Tokenised funds and collateral](../manual/chapters/08-industry.md#tokenised-funds-and-collateral).

**Measurement.** A hash of the code and initial data loaded into an enclave, computed by the processor as it loads them. One changed byte gives a different measurement, so it identifies the exact build. *Taught in:* [3 FP, Remote attestation](../manual/chapters/03-key-storage.md#remote-attestation).

**Memory encryption.** The processor encrypting data on its way out to the memory chips and decrypting it on the way back, so the chips only ever hold ciphertext. It is the basis of TEE memory protection, and interposer attacks target it. *Taught in:* [3, Trusted execution environments](../manual/chapters/03-key-storage.md#trusted-execution-environments).

**Mempool.** A node's pool of valid transactions waiting to be included in a block. Miners choose from it by fee rate. *Taught in:* [5 FP, Blocks, confirmation and regtest](../manual/chapters/05-settlement.md#blocks-confirmation-and-regtest).

**Merkle root.** The single hash at the top of a Merkle tree, committing to every item below it: changing any item changes the root. *Taught in:* [6 FP, Hash trees](../manual/chapters/06-reserves.md#hash-trees).

**Merkle sum tree.** A Merkle tree whose nodes also carry sums, each parent's hash covering both children's hashes and both children's sums. Its root commits to every client balance and to the total owed. Hashing only the total would let a custodian show each client a different split and hide liabilities. *Taught in:* [6 FP, Adding sums](../manual/chapters/06-reserves.md#adding-sums).

**Merkle tree.** A tree of hashes built by hashing items in pairs, then the pair hashes in pairs, up to one root. An item is proved to be in the tree with one sibling hash per level. *Taught in:* [6 FP, Hash trees](../manual/chapters/06-reserves.md#hash-trees).

**MiCA.** Regulation (EU) 2023/1114 on markets in crypto-assets, which licenses crypto-asset service providers. Its Article 75 sets the duties of a custodian. *Taught in:* [8, Regulation in the EU: MiCA](../manual/chapters/08-industry.md#regulation-in-the-eu-mica).

**Microcode.** A processor's updatable internal program. Processor security fixes usually ship as microcode updates, and an attestation report shows whether the machine runs current microcode. *Taught in:* [3, Trusted execution environments](../manual/chapters/03-key-storage.md#trusted-execution-environments).

**ML-DSA.** The FIPS 204 lattice-based signature, a Fiat-Shamir signature with aborts. ML-DSA-65 has a 1,952-byte public key and a 3,309-byte signature, about 50 times a BIP340 signature. *Taught in:* [7, ML-DSA (FIPS 204)](../manual/chapters/07-post-quantum.md#ml-dsa-fips-204).

**ML-KEM.** The FIPS 203 lattice-based key encapsulation mechanism. ML-KEM-768 has a 1,184-byte public key and a 1,088-byte ciphertext, and delivers a 32-byte shared secret. *Taught in:* [7, ML-KEM (FIPS 203)](../manual/chapters/07-post-quantum.md#ml-kem-fips-203).

**Mobile adversary.** An attacker who corrupts different machines at different times, collecting shares from different periods. Proactive refresh defends against it by making shares from different periods incompatible. *Taught in:* [2 FP, What the attacker is assumed to do](../manual/chapters/02-mpc-custody.md#what-the-attacker-is-assumed-to-do).

**Modulo.** Keeping only the remainder after division by a modulus, as a clock does: modulo 12, 15 becomes 3. Results never exceed the modulus minus one, so numbers keep a fixed size through any amount of arithmetic. *Taught in:* [1 FP, Arithmetic on a clock](../manual/chapters/01-foundations.md#arithmetic-on-a-clock).

**MPC.** Secure multi-party computation: several parties compute an agreed function of their private inputs, each learning only the output. In custody the inputs are key shares and the output is a signature. *Taught in:* [2 FP, Parties, rounds and a coordinator](../manual/chapters/02-mpc-custody.md#parties-rounds-and-a-coordinator).

**Multiplicative share.** One of two numbers whose product is the key: 5 and 8 are multiplicative shares of 9 modulo 31, since $5 \times 8 = 40 \equiv 9$. Two-party ECDSA (Lindell 2017) uses them because the ECDSA formula multiplies. *Taught in:* [2 FP, Three ways to split a key](../manual/chapters/02-mpc-custody.md#three-ways-to-split-a-key).

**Multisig.** A Bitcoin output whose locking script requires signatures from several listed keys, such as any 2 of 3. The rule and every key are published on chain when the coins are spent, and the spend is larger than a single-key spend; MPC reaches the same rule off chain. *Taught in:* [2, What this chapter is for](../manual/chapters/02-mpc-custody.md#what-this-chapter-is-for).

## N

**Netting.** Adding up a settlement cycle's fills into one obligation per asset, so only the net moves. The demo's four fills net to 0.85 BTC owed to the exchange and 54,415.925 USD owed to the client. *Taught in:* [5, Netting](../manual/chapters/05-settlement.md#netting).

**Nitro Enclave.** An isolated virtual machine carved out of an AWS EC2 instance by AWS's Nitro hypervisor, with no persistent storage, no interactive access and no external network. Its attestation document is signed through AWS's certificate chain. *Taught in:* [3, Trusted execution environments](../manual/chapters/03-key-storage.md#trusted-execution-environments).

**Node.** A computer that keeps a full copy of the Bitcoin ledger and checks every transaction and block against the rules. A transaction that breaks a rule is rejected by every node independently. *Taught in:* [0, A ledger that nobody operates](../manual/chapters/00-orientation.md#a-ledger-that-nobody-operates).

**Nonce.** In a signature: a secret random number used once. If it is reused, or even partly predictable, the private key can be computed from the signatures: two signatures with one nonce give two equations in two unknowns. On an exchange API the word means something else, a public number that must increase with every request. *Taught in:* [1 FP, What a signature proves](../manual/chapters/01-foundations.md#what-a-signature-proves).

## O

**Off-exchange settlement.** Trading against a balance the custodian locks for an exchange, with the client's assets staying at the custodian and only the net obligation delivered each cycle. The client's exposure to the exchange is bounded by one cycle's net position. *Taught in:* [5 FP, Settling against an exchange](../manual/chapters/05-settlement.md#settling-against-an-exchange).

**Omnibus address.** One address holding many clients' coins, with each client's share recorded only in the custodian's ledger. Segregation between clients then lives in the ledger, not on chain. *Taught in:* [8, Worked example](../manual/chapters/08-industry.md#worked-example).

**One-time signature.** A key that may sign only one message, because each signature reveals part of the secret and a second signature reveals enough to forge. Lamport and WOTS+ keys are one-time. *Taught in:* [7 FP, Signatures from a hash alone: Lamport](../manual/chapters/07-post-quantum.md#signatures-from-a-hash-alone-lamport).

**Outpoint.** The pair that identifies the output an input spends: the txid of the transaction that created it, and the output's index in that transaction. *Taught in:* [5 FP, Coins are outputs, not balances](../manual/chapters/05-settlement.md#coins-are-outputs-not-balances).

## P

**Paillier encryption.** Additively homomorphic public-key encryption: multiplying two ciphertexts gives an encryption of the sum of their plaintexts, and raising one to a power $k$ multiplies its plaintext by $k$. Two-party ECDSA uses it so one party can compute on the other's encrypted share. *Taught in:* [2 FP, Encryption that can be computed on](../manual/chapters/02-mpc-custody.md#encryption-that-can-be-computed-on); [2, Paillier encryption](../manual/chapters/02-mpc-custody.md#paillier-encryption).

**Partial signature.** One signer's contribution to a threshold signature, computed from its own share without seeing any other. A weighted sum of $t$ of them is the full signature: on the toy curve, partials 56 and 90 combine as $1.5 \times 56 - 0.5 \times 90 = 39$. *Taught in:* [0, Signing with pieces: threshold signing](../manual/chapters/00-orientation.md#signing-with-pieces-threshold-signing); [2, FROST](../manual/chapters/02-mpc-custody.md#frost).

**Pedersen commitment.** A point commitment $C = vG + rH$ with a random $r$ and a second generator $H$ whose relation to $G$ nobody knows. It hides $v$ perfectly, binds it unless that relation is found, and commitments add, which lets a tree of sums work on hidden values. *Taught in:* [6, Zero-knowledge proofs of liabilities](../manual/chapters/06-reserves.md#zero-knowledge-proofs-of-liabilities).

**Permissioned ledger.** A ledger whose operators and participants are admitted rather than open to anyone. Institutions use them for confidentiality and to restrict regulated assets to eligible holders. *Taught in:* [8 FP, Public and permissioned ledgers](../manual/chapters/08-industry.md#public-and-permissioned-ledgers).

**PKCS#11.** The OASIS C programming interface most HSMs expose: sessions, logins by role, handles that refer to keys without revealing them, attributes such as sensitive and extractable, and named mechanisms such as `CKM_ECDSA`. Version 3.2 adds ML-KEM, ML-DSA and SLH-DSA. *Taught in:* [3, Hardware security modules](../manual/chapters/03-key-storage.md#hardware-security-modules).

**Point addition.** The rule that combines two curve points into a third: the line through them meets the curve at one more point, and the reflection of that point across the horizontal axis is the sum. Over a finite field the same rule applies as formulas, with division done by inverses. *Taught in:* [1 FP, Points that can be added](../manual/chapters/01-foundations.md#points-that-can-be-added); [1, Fields and curves](../manual/chapters/01-foundations.md#fields-and-curves).

**Point at infinity.** The zero of the curve group, written $\mathcal{O}$: an extra element, not a pair of coordinates. It is the sum of a point and its reflection, because the line through them is vertical and meets the curve nowhere else. *Taught in:* [1 FP, Points that can be added](../manual/chapters/01-foundations.md#points-that-can-be-added).

**Policy engine.** The program that decides, by default-deny rules (tiers, whitelist, velocity limit) and signed approvals, whether a settlement instruction may be signed, and issues the authorisation that names the exact transaction. It does not sign transactions itself. *Taught in:* [0, Deciding which payments happen: policy](../manual/chapters/00-orientation.md#deciding-which-payments-happen-policy); [4](../manual/chapters/04-policy.md).

**Pre-funding.** Moving assets into an exchange's own wallets before trading. If the exchange fails, the client is an unsecured creditor with no particular claim on the coins it deposited. *Taught in:* [5 FP, Settling against an exchange](../manual/chapters/05-settlement.md#settling-against-an-exchange).

**Private channel.** An encrypted, mutually authenticated connection between two parties, used for messages only the recipient may see, such as DKG sub-shares. The application around an MPC library must provide it. *Taught in:* [2 FP, Parties, rounds and a coordinator](../manual/chapters/02-mpc-custody.md#parties-rounds-and-a-coordinator).

**Private key, public key.** A private key is a secret scalar $d$, a step count along the curve's cycle; the public key is the point $Q = dG$ where the walk lands. Computing $Q$ from $d$ takes a few hundred operations; recovering $d$ from $Q$ takes about $2^{128}$. *Taught in:* [1 FP, Easy forwards, infeasible backwards](../manual/chapters/01-foundations.md#easy-forwards-infeasible-backwards).

**Proactive refresh.** Replacing every share with a new one for the same key, by adding a sharing of zero, so that shares from before and after cannot be combined. It defeats an attacker who collects shares over time, but not one who already holds $t$ shares. *Taught in:* [2, Proactive refresh](../manual/chapters/02-mpc-custody.md#proactive-refresh).

**Proof of control.** A signature under the custody key over a statement that could not have been prepared in advance, such as one naming a recent block. It shows the key holders could sign at that time; a tag of its own keeps it from ever being a transaction signature. *Taught in:* [6 FP, Proof of control](../manual/chapters/06-reserves.md#proof-of-control).

**Proof of knowledge.** A zero-knowledge proof that the prover knows a secret, such as the discrete logarithm of a published point, without revealing it. In DKG it stops a participant from publishing a commitment it cannot open. *Taught in:* [2 FP, Zero-knowledge proofs](../manual/chapters/02-mpc-custody.md#zero-knowledge-proofs).

**Proof of reserves.** Evidence that the assets a custodian holds cover the liabilities it owes: a commitment to client balances that each client can check its own inclusion in, plus a proof of control over the coins on chain. It does not cover liabilities outside the tree or borrowed coins. *Taught in:* [0, Showing that the coins are there: proof of reserves](../manual/chapters/00-orientation.md#showing-that-the-coins-are-there-proof-of-reserves); [6, What this chapter is for](../manual/chapters/06-reserves.md#what-this-chapter-is-for).

**Proof of work.** A block-header hash below a target value, found by trial and error. On the public network it takes the whole network about ten minutes per block, which is what makes rewriting history expensive. *Taught in:* [5 FP, Blocks, confirmation and regtest](../manual/chapters/05-settlement.md#blocks-confirmation-and-regtest).

**Prover.** The party in a proof or identification protocol that holds the secret, here the private key $d$, and convinces a verifier without revealing it. *Taught in:* [1 FP, What a signature proves](../manual/chapters/01-foundations.md#what-a-signature-proves).

**Public ledger.** A ledger on which anyone can run a node and submit transactions, and every transaction is visible to everyone. Bitcoin and Ethereum are public ledgers. *Taught in:* [8 FP, Public and permissioned ledgers](../manual/chapters/08-industry.md#public-and-permissioned-ledgers).

**Publicly verifiable encryption.** Encryption of a share that anyone can check matches a known public share without decrypting it, so a custodian can show an auditor that its share backups would work. *Taught in:* [2, Backup, recovery and repair](../manual/chapters/02-mpc-custody.md#backup-recovery-and-repair).

**PvP.** Payment versus payment: in a currency trade, one currency moves if and only if the other does. It removes Herstatt risk. *Taught in:* [8 FP, Delivery versus payment](../manual/chapters/08-industry.md#delivery-versus-payment).

## Q

**Qualified custodian.** Under the US Investment Advisers Act custody rule, the kind of firm with which an adviser must keep client funds and securities: a bank or savings association, a registered broker-dealer, a futures commission merchant, or certain foreign financial institutions. *Taught in:* [8, Regulation in the US](../manual/chapters/08-industry.md#regulation-in-the-us).

**Quantum computer.** A machine that computes with quantum-mechanical states. For most tasks it is no faster than an ordinary computer, but for discrete logarithms and factoring it is enormously faster, which would break every public-key scheme built on them. No machine large enough exists yet. *Taught in:* [7, What this chapter is for](../manual/chapters/07-post-quantum.md#what-this-chapter-is-for); [7 FP, What a quantum computer breaks](../manual/chapters/07-post-quantum.md#what-a-quantum-computer-breaks).

**Quorum.** The minimum number of a group's members who must take part for a decision to count. The demo has two: an approval quorum of people and a signing quorum of machines. *Taught in:* [0, Two quorums](../manual/chapters/00-orientation.md#two-quorums).

## R

**Range proof.** A zero-knowledge proof that a committed value lies in a stated range, such as $[0, 2^{64})$, without revealing it. In a proof of liabilities with hidden sums it replaces the check for negative balances. *Taught in:* [6, Zero-knowledge proofs of liabilities](../manual/chapters/06-reserves.md#zero-knowledge-proofs-of-liabilities).

**RBF.** Replace-by-fee: rebroadcasting a transaction that spends the same inputs with a higher fee, so miners prefer it. The demo's inputs signal that replacement is allowed. *Taught in:* [9, Failure modes](../manual/chapters/09-capstone.md#failure-modes).

**Reconciliation.** Comparing two records of the same money and explaining every difference. A custodian reconciles its ledger, what it owes each client, against the coins at its custody address on the chain. The demo's day compares the two totals after every step, to the satoshi. *Taught in:* [the demo walkthrough, Two records that must agree](../manual/demo-walkthrough.md#two-records-that-must-agree).

**Register.** The record of who owns what that an institution keeps, such as a central securities depository's or a bank's books. The institution can correct it; tokenisation moves it onto a ledger where keys control balances. *Taught in:* [8 FP, Registers and tokens](../manual/chapters/08-industry.md#registers-and-tokens).

**Regtest.** Bitcoin Core's local test mode: blocks are mined on command, the coins have no value, and transactions and signatures are checked by the same rules as on the public network. Each demo run starts its own regtest node. *Taught in:* [5 FP, Blocks, confirmation and regtest](../manual/chapters/05-settlement.md#blocks-confirmation-and-regtest).

**Remote attestation.** Hardware's signed statement of which code runs in an enclave: an attestation report checked by a verifier against expected values. It differs from a reserves attestation, which is the custodian's statement about its holdings. *Taught in:* [3 FP, Remote attestation](../manual/chapters/03-key-storage.md#remote-attestation).

**Replay.** Presenting a message or permission that was valid once a second time, to get its effect again. The demo's signers record each authorisation's identifier and refuse one they have seen, and the policy engine refuses an instruction it has already authorised. It is the custody counterpart of a resent exchange API request that a nonce or timestamp check rejects. *Taught in:* [9, Any two of three, and a replay](../manual/chapters/09-capstone.md#any-two-of-three-and-a-replay); [the demo walkthrough, Attacking the design](../manual/demo-walkthrough.md#attacking-the-design).

**Repo.** A short-term loan in which one party sells securities and agrees to buy them back, usually the next day. *Taught in:* [8, Institutional ledgers: Canton and Kinexys](../manual/chapters/08-industry.md#institutional-ledgers-canton-and-kinexys).

**Report data.** Up to 64 bytes chosen by an enclave's code and signed into its attestation report, typically the hash of a public key generated inside the enclave. Checking it stops a genuine report from being relayed with an attacker's key. *Taught in:* [3 FP, Remote attestation](../manual/chapters/03-key-storage.md#remote-attestation).

**Reserve ratio.** Assets divided by liabilities in a reserves snapshot. After the demo's settlement both are 4.1499969 BTC, so the ratio is exactly 1. *Taught in:* [6, Snapshot and attestation](../manual/chapters/06-reserves.md#snapshot-and-attestation).

**Rogue-key attack.** Publishing a key or commitment chosen to cancel the other parties' contributions, so that the joint key is one the attacker alone controls. A proof of knowledge of the published value's discrete logarithm stops it. *Taught in:* [2 FP, Zero-knowledge proofs](../manual/chapters/02-mpc-custody.md#zero-knowledge-proofs); [2, Distributed key generation](../manual/chapters/02-mpc-custody.md#distributed-key-generation).

**Root of trust.** The key a verifier trusts at the base of a chain of signatures, such as the key a processor maker built into its chips. Every attestation report traces back to it. *Taught in:* [3 FP, Remote attestation](../manual/chapters/03-key-storage.md#remote-attestation).

**ROS attack.** Forging a threshold Schnorr signature by opening many signing sessions at once, seeing the honest signers' commitments, and choosing how to combine them. It runs in polynomial time once the number of sessions exceeds the group order's bit length; FROST's binding factor removes the freedom it needs. *Taught in:* [2 FP, Many sessions at once](../manual/chapters/02-mpc-custody.md#many-sessions-at-once).

**Round.** One exchange of messages in which every party sends and then waits for all the others before its next step. Each round costs at least one network round trip, so the number of rounds sets a protocol's latency. *Taught in:* [2 FP, Parties, rounds and a coordinator](../manual/chapters/02-mpc-custody.md#parties-rounds-and-a-coordinator).

## S

**Safety.** The property that nothing bad happens: no signature without authorisation, no loss of funds. A safety failure cannot be undone, so where safety and liveness conflict the design chooses safety. *Taught in:* [9 FP, Safety and liveness](../manual/chapters/09-capstone.md#safety-and-liveness); [9, Failure modes](../manual/chapters/09-capstone.md#failure-modes).

**Salt.** Random bytes hashed together with a value so that the value cannot be found by guessing candidates against the hash. Each leaf of the demo's reserves tree has a fresh 32-byte salt per snapshot. *Taught in:* [6 FP, Salts and what a proof reveals](../manual/chapters/06-reserves.md#salts-and-what-a-proof-reveals).

**Satoshi.** The whole-number unit of bitcoin on chain: $10^{-8}$ BTC, so 1 BTC is 100,000,000 satoshis. The demo converts `Decimal` BTC amounts to satoshis only at the chain boundary. *Taught in:* [5 FP, Coins are outputs, not balances](../manual/chapters/05-settlement.md#coins-are-outputs-not-balances).

**Scalar.** A whole number that says how many times a point is added to itself. Keys, nonces and shares are scalars modulo the group order $n$. *Taught in:* [1 FP, The cycle: generator, order and scalar](../manual/chapters/01-foundations.md#the-cycle-generator-order-and-scalar).

**Schnorr signature.** The pair $(R, s)$ with $R = kG$, $s = k + e\,d$ and $e$ a hash of $R$, the public key and the message; anyone checks $sG = R + eP$. Its formula only adds secrets and multiplies them by public numbers, which is why it splits easily between signers. *Taught in:* [1 FP, From a conversation to a signature](../manual/chapters/01-foundations.md#from-a-conversation-to-a-signature); [1, Schnorr and BIP340](../manual/chapters/01-foundations.md#schnorr-and-bip340).

**Script path.** Spending a Taproot output by revealing one of the scripts committed inside its key and satisfying it. BIP86 outputs, like the demo's, have no script path. *Taught in:* [5 FP, Locking and unlocking](../manual/chapters/05-settlement.md#locking-and-unlocking).

**Sealing.** Encrypting data under a key the processor derives from a chip secret and the enclave's identity, so only the same chip and the same enclave identity can decrypt it. Sealing to the measurement survives no upgrade; sealing to the signer trusts the developer's key. *Taught in:* [3 FP, Sealing](../manual/chapters/03-key-storage.md#sealing).

**Secret sharing.** Splitting a secret into shares so that a threshold number of them recover it and fewer reveal nothing. Shamir's scheme puts the shares on a random polynomial whose starting value is the secret. *Taught in:* [0, Pieces of a secret: a line through two points](../manual/chapters/00-orientation.md#pieces-of-a-secret-a-line-through-two-points); [1, Shamir secret sharing](../manual/chapters/01-foundations.md#shamir-secret-sharing).

**Security level.** One of FIPS 140-3's four grades of physical protection and operator authentication, from Level 1 (no physical protection) to Level 4 (a complete protective envelope). Custody HSMs are typically Level 3. *Taught in:* [3 FP, Tamper response and certification levels](../manual/chapters/03-key-storage.md#tamper-response-and-certification-levels).

**SegWit.** Segregated Witness (BIP 141, 2017): signatures moved to a witness section that the txid does not cover, so changing a signature cannot change a transaction's identifier. *Taught in:* [5 FP, Locking and unlocking](../manual/chapters/05-settlement.md#locking-and-unlocking).

**Semi-honest party.** A corrupted party that follows the protocol exactly but records everything it sees and tries to learn from it. It models a machine whose memory or logs leak. *Taught in:* [2 FP, What the attacker is assumed to do](../manual/chapters/02-mpc-custody.md#what-the-attacker-is-assumed-to-do).

**Sensitive key.** A key an HSM never reveals in plaintext; if it leaves at all, it leaves wrapped. *Taught in:* [3 FP, Key wrapping](../manual/chapters/03-key-storage.md#key-wrapping).

**Settlement finality.** The legally defined point after which a settlement cannot be unwound, fixed by a system's rules and protected in insolvency. A blockchain's confirmations give a finality that only grows with each block; it becomes legal finality only where a rulebook or statute says so. *Taught in:* [8 FP, Settlement finality](../manual/chapters/08-industry.md#settlement-finality).

**Settlement risk.** The risk that one side of a trade delivers and the other does not. Delivery versus payment removes it; the demo carries it, because it settles only the bitcoin leg. *Taught in:* [8 FP, Delivery versus payment](../manual/chapters/08-industry.md#delivery-versus-payment).

**Share.** One party's piece of a secret. For Shamir sharing, a point $(i, f(i))$ on the secret polynomial: for $f(x) = 9 + 5x$ modulo 31, the shares are $(1, 14)$, $(2, 19)$ and $(3, 24)$. *Taught in:* [1 FP, Sharing a secret as a line through points](../manual/chapters/01-foundations.md#sharing-a-secret-as-a-line-through-points).

**Shor's algorithm.** The quantum algorithm that factors integers and computes discrete logarithms efficiently. A large enough quantum computer running it breaks ECDSA, Schnorr, Ed25519 and Paillier outright; larger keys do not help. *Taught in:* [7, What this chapter is for](../manual/chapters/07-post-quantum.md#what-this-chapter-is-for); [7 FP, What a quantum computer breaks](../manual/chapters/07-post-quantum.md#what-a-quantum-computer-breaks).

**Sibling.** The other child of a node's parent in a hash tree. An inclusion proof is one sibling per level. *Taught in:* [6 FP, Hash trees](../manual/chapters/06-reserves.md#hash-trees).

**Side channel.** A measurable effect of a computation, such as its timing, power draw or cache use, that depends on a secret. A comparison that stops at the first differing byte leaks how many bytes matched and lets a secret be found one byte at a time. *Taught in:* [3 FP, Side channels](../manual/chapters/03-key-storage.md#side-channels).

**Sighash.** The 32-byte hash of a transaction's fields that a signature actually signs, with the witness left out. It commits to every input's amount and script and every output, so one sighash authorises exactly one transaction. *Taught in:* [5 FP, What the signature covers: the sighash](../manual/chapters/05-settlement.md#what-the-signature-covers-the-sighash).

**Signing quorum.** The machines holding key shares, $t$ of which must take part in a signature: in the demo, any two of three signer processes. It is separate from the approval quorum of people. *Taught in:* [0, Two quorums](../manual/chapters/00-orientation.md#two-quorums); [2, What this chapter is for](../manual/chapters/02-mpc-custody.md#what-this-chapter-is-for).

**SLH-DSA.** The FIPS 205 stateless hash-based signature: a hypertree of XMSS trees with FORS at the bottom, secure as long as the hash function is. SHA2-128f signatures are 17,088 bytes. *Taught in:* [7, SLH-DSA (FIPS 205)](../manual/chapters/07-post-quantum.md#slh-dsa-fips-205).

**Snapshot.** The published record of a proof of reserves: the liabilities root and total, the assets, the block, the custody key and the audit log head, signed by the custody key. The demo publishes one after every settlement batch. *Taught in:* [6, Snapshot and attestation](../manual/chapters/06-reserves.md#snapshot-and-attestation).

**SOC report.** An auditor's report on a service organisation's controls, issued under AICPA standards: SOC 1 for controls relevant to clients' financial reporting, SOC 2 for the Trust Services Criteria. It shows controls exist and, for Type II, operated; it does not show that assets exist. *Taught in:* [8, Assurance: SOC reports](../manual/chapters/08-industry.md#assurance-soc-reports).

**Stablecoin.** A token issued by a non-bank against reserves, redeemable at a fixed value. The holder owns a claim on the issuer, backed by the reserves the law requires it to hold. *Taught in:* [8 FP, Four forms of money on a ledger](../manual/chapters/08-industry.md#four-forms-of-money-on-a-ledger).

**Stateful signature.** A scheme, such as XMSS or LMS, whose signer must record which one-time leaves it has used and never use one twice. Restoring a stateful signer from a backup can bring back a used leaf. *Taught in:* [7 FP, A Merkle tree of one-time keys](../manual/chapters/07-post-quantum.md#a-merkle-tree-of-one-time-keys).

**Statement.** The canonical JSON of a reserves snapshot's fields. Its tagged hash is the message the custody key signs as proof of control. *Taught in:* [6, Snapshot and attestation](../manual/chapters/06-reserves.md#snapshot-and-attestation).

**Sweep.** Moving every coin from an old key to a new one: the only way to rotate a custody key. It is itself a settlement through the full policy path. *Taught in:* [9, Deep dives](../manual/chapters/09-capstone.md#deep-dives).

**Symmetric encryption.** Encryption in which one secret key both encrypts and decrypts, such as AES. It is much faster than public-key encryption, so public-key methods usually only deliver a symmetric key. *Taught in:* [3 FP, Symmetric encryption in brief](../manual/chapters/03-key-storage.md#symmetric-encryption-in-brief).

## T

**Tagged hash.** BIP340's hash with a purpose label: SHA-256 of the data prefixed with the hash of the tag, twice. Hashes made for different purposes can then never coincide. *Taught in:* [1, Hash functions](../manual/chapters/01-foundations.md#hash-functions).

**Tamper evidence, resistance, response.** An HSM's three physical defences: seals and coatings that show it was opened, an enclosure that is hard to open, and sensors that trigger zeroisation of the keys when it is opened. *Taught in:* [3 FP, Tamper response and certification levels](../manual/chapters/03-key-storage.md#tamper-response-and-certification-levels).

**Taproot.** Bitcoin's output type since November 2021 (BIP 341), locked to one 32-byte x-only key, with an optional tree of alternative scripts committed inside the key. It is spent by a BIP340 signature (key path) or by revealing a script (script path). *Taught in:* [5 FP, Locking and unlocking](../manual/chapters/05-settlement.md#locking-and-unlocking).

**TCB.** Trusted computing base: everything that must behave correctly for a key to stay secret, including hardware, firmware, operating system, application code and the people with administrative access. *Taught in:* [3 FP, Three questions for any key store](../manual/chapters/03-key-storage.md#three-questions-for-any-key-store).

**TEE.** Trusted execution environment: processor-protected memory and code on an ordinary server, which the host's operating system and hypervisor cannot read, with remote attestation of the code inside. *Taught in:* [3, What this chapter is for](../manual/chapters/03-key-storage.md#what-this-chapter-is-for); [3, Trusted execution environments](../manual/chapters/03-key-storage.md#trusted-execution-environments).

**Threshold ($t$-of-$n$).** A scheme in which any $t$ of $n$ share holders can act together, and $t - 1$ learn nothing and cannot act. A 2-of-3 threshold across independent sites raises availability and lowers the chance of compromise at the same time. *Taught in:* [2 FP, What the attacker is assumed to do](../manual/chapters/02-mpc-custody.md#what-the-attacker-is-assumed-to-do).

**Threshold signing.** Producing one ordinary signature from the partial signatures of $t$ share holders, without the key ever being rebuilt anywhere. FROST does it for Schnorr; Lindell 2017 and CGGMP for ECDSA. *Taught in:* [0, Signing with pieces: threshold signing](../manual/chapters/00-orientation.md#signing-with-pieces-threshold-signing); [2, FROST](../manual/chapters/02-mpc-custody.md#frost).

**Token.** A balance on a ledger that moves when its holder's key signs. Whoever controls the key controls the balance. *Taught in:* [8 FP, Registers and tokens](../manual/chapters/08-industry.md#registers-and-tokens).

**Tokenisation.** Moving an asset's register of ownership onto a ledger as tokens, which turns custody into holding keys. *Taught in:* [8 FP, Registers and tokens](../manual/chapters/08-industry.md#registers-and-tokens).

**Tokenised deposit.** A commercial bank deposit represented as a token; the holder owns a deposit claim on that bank. JPM Coin (JPMD) is an example. *Taught in:* [8 FP, Four forms of money on a ledger](../manual/chapters/08-industry.md#four-forms-of-money-on-a-ledger).

**Tokenised money market fund.** Money market fund shares issued as tokens, used mainly as collateral that can move at any hour while it keeps earning the fund's yield. BlackRock's BUIDL is an example. *Taught in:* [8 FP, Four forms of money on a ledger](../manual/chapters/08-industry.md#four-forms-of-money-on-a-ledger).

**Transaction.** A signed message that spends whole UTXOs and creates new ones. What goes in minus what comes out is the fee. *Taught in:* [0, Transactions, blocks and confirmation](../manual/chapters/00-orientation.md#transactions-blocks-and-confirmation); [5 FP, Coins are outputs, not balances](../manual/chapters/05-settlement.md#coins-are-outputs-not-balances).

**Transfer agent.** The firm that keeps a fund's register of holders. For a tokenised fund it maintains the allowlist of addresses permitted to hold the token. *Taught in:* [8 FP, Public and permissioned ledgers](../manual/chapters/08-industry.md#public-and-permissioned-ledgers).

**Trust Services Criteria.** The AICPA criteria a SOC 2 report tests: security, which is required, and optionally availability, processing integrity, confidentiality and privacy. *Taught in:* [8, Assurance: SOC reports](../manual/chapters/08-industry.md#assurance-soc-reports).

**Tweak.** Adding $tG$ to a key, with $t$ a hash, so the key commits to extra data; the private key changes by $t$ to match. BIP86's tweak commits a Taproot key to an empty script tree. *Taught in:* [5, Taproot outputs and the BIP86 tweak](../manual/chapters/05-settlement.md#taproot-outputs-and-the-bip86-tweak).

**Txid.** A transaction's identifier: the double SHA-256 of its serialisation without witnesses. Because signatures are in the witness, changing a signature cannot change the txid. *Taught in:* [5 FP, Coins are outputs, not balances](../manual/chapters/05-settlement.md#coins-are-outputs-not-balances); [5 FP, Locking and unlocking](../manual/chapters/05-settlement.md#locking-and-unlocking).

**Type I, Type II.** The two kinds of SOC report: Type I reports on control design at one date; Type II also tests that the controls operated over a period, typically six to twelve months. *Taught in:* [8, Assurance: SOC reports](../manual/chapters/08-industry.md#assurance-soc-reports).

## U

**UC security.** Universal composability: security that still holds when many sessions run concurrently and alongside other protocols. A proof for one session in isolation does not extend automatically, and a custodian's signers run many sessions at once. *Taught in:* [2 FP, What the attacker is assumed to do](../manual/chapters/02-mpc-custody.md#what-the-attacker-is-assumed-to-do).

**UTXO.** An unspent transaction output: an amount together with a condition for spending it. Bitcoin's ledger is the set of UTXOs, and a wallet's balance is the sum of those it can spend. *Taught in:* [5 FP, Coins are outputs, not balances](../manual/chapters/05-settlement.md#coins-are-outputs-not-balances).

## V

**Velocity limit.** A cap on the total authorised in a rolling time window, such as 20 BTC in any 24 hours in the demo. It bounds what a compromise that gets past every other control can move before someone notices. *Taught in:* [4, The decision function](../manual/chapters/04-policy.md#the-decision-function).

**Verifier.** The party that checks a proof or signature using only public values, here the public key $Q$. In Schnorr's identification protocol it sends the challenge; in a signature a hash plays its part. *Taught in:* [1 FP, What a signature proves](../manual/chapters/01-foundations.md#what-a-signature-proves).

## W

**Warm wallet.** Online signers with a human approval quorum for every transaction. The demo is a warm wallet. *Taught in:* [9, Deep dives](../manual/chapters/09-capstone.md#deep-dives).

**Whitelist.** The set of destination addresses the policy allows for an asset; an instruction to any other address is refused regardless of approvals. Changing it needs its own controls, because it becomes the attacker's target. *Taught in:* [4, The decision function](../manual/chapters/04-policy.md#the-decision-function).

**Witness.** The data that satisfies a locking script, such as a signature. A Taproot key-path witness is one 64-byte signature. *Taught in:* [5 FP, Locking and unlocking](../manual/chapters/05-settlement.md#locking-and-unlocking).

**WOTS+.** The Winternitz one-time signature as FIPS 205 defines it: for a 16-byte digest, 35 hash chains (32 for the message digits and 3 for the checksum), each hash call labelled with an address so no two calls hash the same input. *Taught in:* [7 FP, Winternitz chains and the checksum](../manual/chapters/07-post-quantum.md#winternitz-chains-and-the-checksum).

## X

**x-only key.** A 32-byte public key that stores only the $x$-coordinate; the point with even $y$ is meant. Each $x$ belongs to a point and its mirror image, and a signer whose key has odd $y$ uses the negated private key. *Taught in:* [1, Schnorr and BIP340](../manual/chapters/01-foundations.md#schnorr-and-bip340).

**XMSS.** A Merkle tree whose leaves are WOTS+ public keys; the root is the long-term public key, and a signature includes the path from its leaf. The signer is stateful: it must never use a leaf twice. *Taught in:* [7 FP, A Merkle tree of one-time keys](../manual/chapters/07-post-quantum.md#a-merkle-tree-of-one-time-keys).

## Z

**Zero-knowledge proof.** A proof that a statement about a secret is true, revealing nothing else. Schnorr's identification protocol is one: forged transcripts, made without the key, look exactly like real ones, so real ones carry no information about the key. *Taught in:* [2 FP, Zero-knowledge proofs](../manual/chapters/02-mpc-custody.md#zero-knowledge-proofs).

**Zeroisation.** Overwriting keys when tampering is detected, before an attacker can read them. *Taught in:* [3 FP, Tamper response and certification levels](../manual/chapters/03-key-storage.md#tamper-response-and-certification-levels).
