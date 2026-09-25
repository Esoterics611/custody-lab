# Glossary

Every term the manual defines, in one sentence, with the chapter and section that teach it.
Chapter 0 is the orientation; "FP" is a chapter's First principles section.

| Term | Meaning | Taught in |
|------|---------|-----------|
| Abort | A protocol run that stops without a signature because cheating was detected. | 2 FP, What the attacker is assumed to do |
| Additive share | One of several numbers that sum to the key modulo $n$; all holders are needed. | 2 FP, Three ways to split a key |
| Address | A locking script encoded for people (bech32m for Taproot: `bc1p…`, `bcrt1p…` on regtest). | 5 FP, Locking and unlocking |
| Adversary model | The statement of which parties an attacker controls, when, and what they may do. | 2 FP, What the attacker is assumed to do |
| Anchoring | Publishing an audit log's head hash elsewhere, so a rewritten or truncated log is detected. | 4, Hash-chained audit log |
| Approval quorum | The people who must approve an instruction before the policy engine authorises it. | 0, Two quorums; 4 |
| Attestation | A signed statement of a snapshot's contents, made under the custody key. | 6 FP, Proof of control |
| Authorisation | A short-lived token, signed by the policy engine, naming the exact message the signers may sign. | 4, Authorisation |
| Binding (commitment) | The committer cannot open a commitment to a different value. | 2 FP, Commitments |
| Binding factor | In FROST, a hash of the message and all commitments that fixes each signer's effective nonce. | 2 FP, Many sessions at once; 2, FROST |
| BIP340 | Bitcoin's Schnorr signature standard: x-only keys, tagged hashes, hashed nonces. | 1, Schnorr and BIP340 |
| BIP86 | A Taproot output whose key is tweaked to commit to no scripts, so it has a key path only. | 5, Taproot outputs and the BIP86 tweak |
| Block | A batch of transactions with a proof of work, naming the block before it. | 5 FP, Blocks, confirmation and regtest |
| Broadcast | A protocol message sent to every party. | 2 FP, Parties, rounds and a coordinator |
| Canonical encoding | An encoding that gives every value exactly one byte representation. | 4, Canonical encoding |
| Change | The output that returns the remainder of a spent UTXO, less the fee, to the payer. | 5 FP, Coins are outputs, not balances |
| Commitment | A value published now that fixes a choice before information that could bias it arrives. | 1 FP, What a signature proves; 2 FP, Commitments |
| Confirmation | One block containing or following a transaction; more confirmations make reversal costlier. | 5 FP, Blocks, confirmation and regtest |
| Coordinator | The process that relays protocol messages and combines results; it holds no share. | 2 FP, Parties, rounds and a coordinator |
| Corrupted party | A party the attacker controls. | 2 FP, What the attacker is assumed to do |
| Default-deny | Refusing anything the policy does not explicitly allow. | 4, Intuition |
| Discrete logarithm problem | Recovering $d$ from $Q = dG$; about $2^{128}$ steps on secp256k1 by the best known classical methods. | 1 FP, Easy forwards, infeasible backwards |
| DKG | Distributed key generation: parties create a shared key that no party ever holds. | 2, Distributed key generation |
| Domain separation | Hashing each class of message under its own tag, so two classes can never produce the same message. | 6 FP, Proof of control |
| Double-and-add | Computing $dG$ by repeated doubling, about 256 doublings for a 256-bit key. | 1 FP, Easy forwards, infeasible backwards |
| Dust | An output too small for Bitcoin Core to relay (330 sats for Taproot); the builder adds it to the fee. | 5 FP, Coins are outputs, not balances |
| ECDSA | The signature scheme $s = k^{-1}(z + rd)$; hard to split because it multiplies secrets. | 1, ECDSA |
| Ed25519 | Schnorr-type signatures (EdDSA) on Curve25519 with deterministic nonces; used for approvals. | 1, EdDSA |
| Fee | Inputs minus outputs of a transaction, collected by the miner. | 5 FP, Coins are outputs, not balances |
| Feldman commitment | Publishing each polynomial coefficient times $G$, so a share can be checked. | 2 FP, Commitments |
| Fiat-Shamir transform | Replacing a verifier's random challenge with a hash of the commitment, key and message. | 1 FP, What a signature proves |
| Finite field | The integers modulo a prime, where every non-zero number has an inverse. | 1 FP, Arithmetic on a clock |
| Four-eyes | Requiring approval by someone other than the initiator (maker-checker). | 4, Intuition |
| FROST | Two-round threshold Schnorr signing (RFC 9591); the demo's signing protocol. | 2, FROST |
| Generator | The published point $G$ from which every key is measured. | 1 FP, The cycle: generator, order and scalar |
| Group | A set with an operation that commutes, associates, has a zero and has negatives. | 1 FP, Points that can be added |
| Group order | The length $n$ of the cycle $G, 2G, \dots, nG = \mathcal{O}$. | 1 FP, The cycle: generator, order and scalar |
| Hash function | A function mapping any input to a fixed-size digest, resistant to preimages and collisions. | 1, Hash functions |
| Hiding (commitment) | A commitment reveals nothing about the committed value. | 2 FP, Commitments |
| Homomorphic encryption | Encryption in which operations on ciphertexts act on the plaintexts inside. | 2 FP, Encryption that can be computed on |
| Identifiable abort | An abort that also names the cheating party. | 2 FP, What the attacker is assumed to do |
| Inclusion proof | The sibling at each level of a hash tree, from which a holder recomputes the root. | 6 FP, Hash trees |
| Inverse | The number $a^{-1}$ with $a \cdot a^{-1} \equiv 1$; dividing means multiplying by it. | 1 FP, Arithmetic on a clock |
| Key path | Spending a Taproot output with one signature under its key. | 5 FP, Locking and unlocking |
| Lagrange coefficient | The weight on each share when rebuilding $f(0)$; depends only on which shares are present. | 1 FP, Sharing a secret as a line through points |
| Locking script | The condition an output sets for spending it (`scriptPubKey`). | 5 FP, Locking and unlocking |
| Locktime, sequence | Transaction fields carrying time locks and replacement signals. | 5 FP, What the signature covers: the sighash |
| Low-S | Bitcoin's rule that an ECDSA $s$ is at most $n/2$, removing one form of malleability. | 1, ECDSA |
| Malicious party | A corrupted party that may send anything, or nothing. | 2 FP, What the attacker is assumed to do |
| Mempool | A node's pool of valid transactions waiting for a block. | 5 FP, Blocks, confirmation and regtest |
| Merkle root | The single hash at the top of a Merkle tree, committing to every item below it. | 6 FP, Hash trees |
| Merkle sum tree | A Merkle tree whose nodes also carry sums, each parent hashing both children's sums. | 6 FP, Adding sums |
| Merkle tree | A tree of hashes built by hashing items in pairs up to one root. | 6 FP, Hash trees |
| Mobile adversary | An attacker who corrupts different machines at different times. | 2 FP, What the attacker is assumed to do |
| Modulo | Keeping only the remainder after division, as a clock does. | 1 FP, Arithmetic on a clock |
| MPC | Secure multi-party computation: parties compute a function of private inputs, each learning only the output. | 2 FP, Parties, rounds and a coordinator |
| Multiplicative share | One of two numbers whose product is the key (Lindell 2017). | 2 FP, Three ways to split a key |
| Netting | Summing a cycle's fills into one obligation per asset. | 5, Netting |
| Nonce | A secret random number used once in a signature; reusing it reveals the key. | 1 FP, What a signature proves |
| Outpoint | The txid and output index that identify the output an input spends. | 5 FP, Coins are outputs, not balances |
| Paillier encryption | Additively homomorphic public-key encryption, used by two-party ECDSA. | 2 FP, Encryption that can be computed on; 2, Paillier encryption |
| Pedersen commitment | $C = vG + rH$: a hiding, binding point commitment; commitments add. | 6, Zero-knowledge proofs of liabilities |
| Point at infinity | The zero of the curve group, $\mathcal{O}$; the sum of a point and its reflection. | 1 FP, Points that can be added |
| Private key, public key | A secret scalar $d$, and the point $Q = dG$. | 1 FP, Easy forwards, infeasible backwards |
| Proactive refresh | Replacing every share with a new one for the same key, so old shares become useless. | 2, Proactive refresh |
| Proof of control | A signature under the custody key over a message that could not be prepared in advance. | 6 FP, Proof of control |
| Proof of knowledge | A zero-knowledge proof that the prover knows a secret, such as a discrete logarithm. | 2 FP, Zero-knowledge proofs |
| Proof of reserves | Evidence that assets held cover liabilities owed: a liabilities commitment plus proof of control. | 6, Intuition |
| Proof of work | A block-header hash below a target, found by trial; it makes rewriting blocks costly. | 5 FP, Blocks, confirmation and regtest |
| Range proof | A zero-knowledge proof that a committed value lies in a stated range, such as $[0, 2^{64})$. | 6, Zero-knowledge proofs of liabilities |
| Regtest | Bitcoin Core's local test mode: blocks on command, worthless coins. | 5 FP, Blocks, confirmation and regtest |
| Reserve ratio | Assets divided by liabilities in a snapshot. | 6, Snapshot and attestation |
| ROS attack | Forging a threshold Schnorr signature by combining commitments across many concurrent sessions. | 2 FP, Many sessions at once |
| Round | One exchange in which every party sends and then waits for all the others. | 2 FP, Parties, rounds and a coordinator |
| Salt | Random bytes hashed with a value so that the value cannot be found by guessing. | 6 FP, Salts and what a proof reveals |
| Satoshi | The integer unit of bitcoin: $10^{-8}$ BTC. | 5 FP, Coins are outputs, not balances |
| Scalar | A whole number that multiplies a point; keys, nonces and shares are scalars modulo $n$. | 1 FP, The cycle: generator, order and scalar |
| Schnorr signature | The pair $(R, s)$ with $s = k + ed$ and $e$ a hash of $R$, the key and the message. | 1 FP, What a signature proves |
| Script path | Spending a Taproot output by revealing and satisfying a committed script. | 5 FP, Locking and unlocking |
| Semi-honest party | A corrupted party that follows the protocol but records everything it sees. | 2 FP, What the attacker is assumed to do |
| Share | One party's piece of a secret; for Shamir sharing, a point $(i, f(i))$. | 1 FP, Sharing a secret as a line through points |
| Sibling | The other child of a node's parent in a hash tree. | 6 FP, Hash trees |
| Sighash | The 32-byte hash of a transaction's fields that a signature actually signs. | 5 FP, What the signature covers: the sighash |
| Signing quorum | The machines holding key shares, $t$ of which must take part in a signature. | 0, Two quorums; 2, Intuition |
| Snapshot | The published record of liabilities root and total, assets, block, custody key and audit head. | 6, Snapshot and attestation |
| Taproot | Bitcoin's output type (BIP 341) locked to one 32-byte key, with optional committed scripts. | 5 FP, Locking and unlocking |
| Threshold ($t$-of-$n$) | Any $t$ of $n$ share holders can sign; $t - 1$ learn nothing and cannot sign. | 2 FP, What the attacker is assumed to do |
| Tweak | Adding $tG$ to a key, with $t$ a hash, so the key commits to extra data. | 5, Taproot outputs and the BIP86 tweak |
| Txid | A transaction's id: the double SHA-256 of its serialisation without witnesses. | 5 FP, Coins are outputs, not balances; Locking and unlocking |
| UC security | Security that still holds when many sessions run concurrently alongside other protocols. | 2 FP, What the attacker is assumed to do |
| UTXO | An unspent transaction output: an amount and a spending condition. | 5 FP, Coins are outputs, not balances |
| Velocity limit | A cap on the total authorised in a rolling time window. | 4, The decision function |
| Whitelist | The set of destinations the policy allows for an asset. | 4, The decision function |
| Witness | The data that satisfies a locking script, such as a signature. | 5 FP, Locking and unlocking |
| x-only key | A 32-byte public key (the $x$-coordinate); the point with even $y$ is meant. | 1, Schnorr and BIP340 |
| Zero-knowledge proof | A proof that a statement about a secret is true, revealing nothing else. | 2 FP, Zero-knowledge proofs |
