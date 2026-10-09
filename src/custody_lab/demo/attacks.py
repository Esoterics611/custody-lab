"""Attacks on the custody design, each run against the real code and each expected to be refused.

EDUCATIONAL, NOT PRODUCTION. ``run`` sets up the demo's policy engine, approvers and a 2-of-3
signing cluster, then tries seventeen things an attacker or a careless insider would try. Each
attempt reports which component stopped it and that component's own words. An attempt that
succeeds is reported as accepted: it means a defence is broken, and the tests fail.

No chain is involved, so no ``bitcoind`` is needed. Where an attack needs a transaction, a 32-byte
hash of the instruction stands in for its sighash: the signers check only that the authorisation
names the exact message they are asked to sign, and a real sighash is 32 bytes like any other.
The reserves snapshot carries the stand-in block height 0 and an all-zero block hash for the same
reason.

The groups follow the design's layers:
- **Policy engine**: who may move coins, how much, and where (chapter 4).
- **Signers**: each signer process refuses a request without a valid, unused authorisation for
  exactly that message, and fewer than two signers cannot sign at all (chapters 2 and 4).
- **Published records**: a client, an auditor or anyone else checks the custodian's published
  snapshot and audit log (chapters 4 and 6).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PrivateKey

from custody_lab.foundations import schnorr
from custody_lab.foundations.hashing import sha256
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy.audit import AuditChainBroken, AuditLog, verify_chain
from custody_lab.policy.authorisation import AuthorityKey, issue
from custody_lab.policy.engine import AssetPolicy, Policy, PolicyDenied, PolicyEngine, Tier
from custody_lab.policy.model import Approval, SettlementInstruction
from custody_lab.reserves.merkle_sum import MerkleSumTree
from custody_lab.reserves.merkle_sum import verify as verify_inclusion
from custody_lab.reserves.snapshot import Snapshot

EXCHANGE = "exchange-settlement-address"  # whitelisted
ATTACKER = "attacker-address"  # not whitelisted
TTL = timedelta(seconds=60)  # authorisation lifetime, as the policy engine issues them
LEDGER = {
    "alpha-capital": Decimal("1.1499969"),
    "beta-fund": Decimal("1.50"),
    "gamma-treasury": Decimal("1.00"),
    "delta-trading": Decimal("0.50"),
}
GROUPS = {
    "policy": "Policy engine",
    "signers": "Signers",
    "records": "Published records",
}


@dataclass(frozen=True)
class Attempt:
    attack: str  # identifier
    group: str  # a key of GROUPS
    title: str  # what the attacker tries
    defence: str  # the component that refuses
    refused: bool
    reason: str  # the refusal, in the refusing component's words

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class NotRefused(Exception):
    """The attack worked: a defence is broken."""


def _now() -> datetime:
    return datetime.now(UTC)


class _Lab:
    """The demo's people, policy and signing cluster, with no chain."""

    def __init__(self, cluster: SigningCluster, authority: AuthorityKey) -> None:
        self.cluster, self.authority = cluster, authority
        self.keys = {n: Ed25519PrivateKey.generate() for n in ("bob", "carol", "mallory")}
        self.policy = Policy(
            {
                "BTC": AssetPolicy(
                    tiers=(Tier(Decimal("0.1"), 1), Tier(Decimal("10"), 2)),
                    whitelist=frozenset({EXCHANGE}),
                    velocity_window=timedelta(hours=24),
                    velocity_limit=Decimal("20"),
                )
            },
            # mallory has a key but is not on the approver list
            {n: k.public_key() for n, k in self.keys.items() if n != "mallory"},
        )
        self._count = 0

    def engine(self, clock: Callable[[], datetime] = _now) -> PolicyEngine:
        return PolicyEngine(self.policy, self.authority, AuditLog(clock), clock)

    def instruction(
        self, amount: str = "0.85", destination: str = EXCHANGE, initiator: str = "ops-desk"
    ) -> SettlementInstruction:
        self._count += 1
        return SettlementInstruction(
            f"attack-{self._count}", "BTC", Decimal(amount), destination, initiator, _now()
        )

    def approve(self, ins: SettlementInstruction, *names: str) -> list[Approval]:
        return [Approval.create(ins, n, self.keys[n]) for n in names]

    def sign(self, message: bytes, token: bytes, signers: list[int] | None = None) -> bytes:
        return self.cluster.sign(message, signers or [1, 3], token, taproot=True)


def _sighash(ins: SettlementInstruction) -> bytes:
    """A 32-byte stand-in for the transaction sighash that pays ``ins``."""
    return sha256(ins.digest())


def _denied(engine: PolicyEngine, ins: SettlementInstruction, approvals: list[Approval]) -> str:
    try:
        engine.authorise(ins, approvals, _sighash(ins))
    except PolicyDenied as denied:
        return str(denied)
    raise NotRefused("the policy engine issued an authorisation")


def _signers_refuse(
    lab: _Lab, message: bytes, token: bytes, signers: list[int] | None = None
) -> str:
    try:
        lab.sign(message, token, signers)
    except (RuntimeError, ValueError) as refused:
        return str(refused)
    raise NotRefused("the signers produced a signature")


# Policy engine


def pay_an_address_not_on_the_whitelist(lab: _Lab) -> str:
    ins = lab.instruction(destination=ATTACKER)
    return _denied(lab.engine(), ins, lab.approve(ins, "bob", "carol"))


def pay_with_one_approval(lab: _Lab) -> str:
    ins = lab.instruction()
    return _denied(lab.engine(), ins, lab.approve(ins, "bob"))


def approve_your_own_instruction(lab: _Lab) -> str:
    ins = lab.instruction(initiator="bob")
    return _denied(lab.engine(), ins, lab.approve(ins, "bob", "carol"))


def approve_with_a_key_not_on_the_list(lab: _Lab) -> str:
    ins = lab.instruction()
    return _denied(lab.engine(), ins, lab.approve(ins, "bob", "mallory"))


def raise_the_amount_after_approval(lab: _Lab) -> str:
    approved = lab.instruction()
    approvals = lab.approve(approved, "bob", "carol")
    return _denied(lab.engine(), replace(approved, amount=Decimal("8.5")), approvals)


def pay_the_same_instruction_twice(lab: _Lab) -> str:
    engine, ins = lab.engine(), lab.instruction()
    approvals = lab.approve(ins, "bob", "carol")
    engine.authorise(ins, approvals, _sighash(ins))
    return _denied(engine, ins, approvals)


def drain_through_many_payments(lab: _Lab) -> str:
    engine = lab.engine()
    for _ in range(2):  # 2 x 9.5 BTC fits the 20 BTC daily limit
        ins = lab.instruction("9.5")
        engine.authorise(ins, lab.approve(ins, "bob", "carol"), _sighash(ins))
    third = lab.instruction("9.5")
    return _denied(engine, third, lab.approve(third, "bob", "carol"))


# Signers


def forge_an_authorisation(lab: _Lab) -> str:
    ins = lab.instruction(destination=ATTACKER)
    forged = issue(AuthorityKey.generate(), ins.digest(), _sighash(ins), _now() + TTL)
    return _signers_refuse(lab, _sighash(ins), forged.to_bytes())


def forge_after_breaking_ed25519(lab: _Lab) -> str:
    # The attacker is given the authority's real Ed25519 key, as a quantum computer could derive
    # it from the public key. The ML-DSA-65 key stays out of reach.
    stolen = AuthorityKey(lab.authority.classical, MLDSA65PrivateKey.generate())
    ins = lab.instruction(destination=ATTACKER)
    forged = issue(stolen, ins.digest(), _sighash(ins), _now() + TTL)
    return _signers_refuse(lab, _sighash(ins), forged.to_bytes())


def replay_a_used_authorisation(lab: _Lab) -> str:
    engine, ins = lab.engine(), lab.instruction()
    token = engine.authorise(ins, lab.approve(ins, "bob", "carol"), _sighash(ins)).to_bytes()
    lab.sign(_sighash(ins), token)  # the legitimate payment
    return _signers_refuse(lab, _sighash(ins), token)


def swap_the_transaction_after_approval(lab: _Lab) -> str:
    engine, ins = lab.engine(), lab.instruction()
    token = engine.authorise(ins, lab.approve(ins, "bob", "carol"), _sighash(ins)).to_bytes()
    other = _sighash(lab.instruction(destination=ATTACKER))
    return _signers_refuse(lab, other, token)


def use_an_expired_authorisation(lab: _Lab) -> str:
    engine = lab.engine(clock=lambda: _now() - timedelta(minutes=5))  # issued 5 minutes ago
    ins = lab.instruction()
    token = engine.authorise(ins, lab.approve(ins, "bob", "carol"), _sighash(ins)).to_bytes()
    return _signers_refuse(lab, _sighash(ins), token)


def sign_with_one_signer(lab: _Lab) -> str:
    engine, ins = lab.engine(), lab.instruction()
    token = engine.authorise(ins, lab.approve(ins, "bob", "carol"), _sighash(ins)).to_bytes()
    return _signers_refuse(lab, _sighash(ins), token, signers=[2])


# Published records


def alter_a_signed_snapshot(lab: _Lab) -> str:
    output_key = lab.cluster.taproot_output_key()
    tree = MerkleSumTree(LEDGER)
    snapshot = Snapshot(
        taken_at=_now(),
        block_height=0,
        block_hash="00" * 32,
        liabilities_root=tree.root.hash.hex(),
        liabilities=tree.root.total,
        clients=len(LEDGER),
        assets=tree.root.total,
        custody_output_key=output_key.hex(),
        audit_head="00" * 32,
    )
    token = lab.engine().authorise_attestation(snapshot.statement())
    signature = lab.sign(snapshot.attestation_message(), token.to_bytes())
    altered = replace(snapshot, liabilities=snapshot.liabilities - Decimal("0.5"))
    if schnorr.verify(altered.attestation_message(), output_key, signature):
        raise NotRefused("the altered snapshot verifies")
    return "proof-of-control signature does not verify over the altered snapshot"


def understate_a_client_balance(lab: _Lab) -> str:
    client = "alpha-capital"
    owed = LEDGER[client]
    published = MerkleSumTree({**LEDGER, client: owed - Decimal("0.5")})
    proof = replace(published.proof(client), balance=owed)  # the client checks its own figure
    if verify_inclusion(proof, published.root):
        raise NotRefused("the understated balance verifies")
    return f"{client} recomputes the root from its own {owed} BTC and it does not match"


def leave_a_client_out(lab: _Lab) -> str:
    """The custodian publishes a tree without delta-trading, and shows delta-trading a second tree
    that includes it. Only delta-trading's own check can catch either."""
    published = MerkleSumTree({c: b for c, b in LEDGER.items() if c != "delta-trading"})
    try:
        published.proof("delta-trading")
        raise NotRefused("the published tree holds a proof for a client left out of it")
    except ValueError:
        pass  # no proof exists for a client the tree does not contain
    private = MerkleSumTree(LEDGER)  # shown to delta-trading alone
    if verify_inclusion(private.proof("delta-trading"), published.root):
        raise NotRefused("delta-trading's proof from the second tree reaches the published root")
    return (
        "delta-trading finds no proof for itself in the published tree, and its proof from a "
        "second tree reaches a root other than the published one"
    )


def edit_the_audit_log(lab: _Lab) -> str:
    engine, ins = lab.engine(), lab.instruction()
    engine.authorise(ins, lab.approve(ins, "bob", "carol"), _sighash(ins))
    entries = list(engine.audit.entries)
    i = next(n for n, e in enumerate(entries) if e.event == "authorised")
    entries[i] = replace(entries[i], payload={**entries[i].payload, "amount": Decimal("0.085")})
    try:
        verify_chain(entries)
    except AuditChainBroken as broken:
        return str(broken)
    raise NotRefused("the edited log verifies")


ATTACKS: list[tuple[str, str, str, Callable[[_Lab], str]]] = [
    # group, what the attacker tries, who refuses, the attempt
    ("policy", "Pay an address that is not on the whitelist", "policy engine",
     pay_an_address_not_on_the_whitelist),
    ("policy", "Pay 0.85 BTC with one approval where the tier needs two", "policy engine",
     pay_with_one_approval),
    ("policy", "Approve an instruction its own initiator raised", "policy engine",
     approve_your_own_instruction),
    ("policy", "Approve with a key that is not on the approver list", "policy engine",
     approve_with_a_key_not_on_the_list),
    ("policy", "Raise the amount from 0.85 to 8.5 BTC after both approvals", "policy engine",
     raise_the_amount_after_approval),
    ("policy", "Submit an authorised instruction a second time", "policy engine",
     pay_the_same_instruction_twice),
    ("policy", "Drain the account in 9.5 BTC payments, each fully approved", "policy engine",
     drain_through_many_payments),
    ("signers", "Sign with an authorisation from an attacker's own authority key", "signers",
     forge_an_authorisation),
    ("signers", "Forge an authorisation after breaking Ed25519, as a quantum computer could",
     "signers", forge_after_breaking_ed25519),
    ("signers", "Replay an authorisation that has already been used", "signers",
     replay_a_used_authorisation),
    ("signers", "Swap in a different transaction after approval", "signers",
     swap_the_transaction_after_approval),
    ("signers", "Use an authorisation issued five minutes ago", "signers",
     use_an_expired_authorisation),
    ("signers", "Sign with one signer, as an insider holding one share would", "signers",
     sign_with_one_signer),
    ("records", "Lower the liabilities in a signed reserves snapshot", "anyone verifying it",
     alter_a_signed_snapshot),
    ("records", "Publish a liabilities tree with a client's balance cut by 0.5 BTC",
     "the client's own check", understate_a_client_balance),
    ("records", "Leave a client out of the liabilities tree", "the client's own check",
     leave_a_client_out),
    ("records", "Edit an amount in the audit log", "the audit chain check",
     edit_the_audit_log),
]  # fmt: skip


@contextmanager
def lab() -> Iterator[_Lab]:
    authority = AuthorityKey.generate()
    with SigningCluster(2, 3, authority.public_bytes()) as cluster:
        cluster.dkg()
        yield _Lab(cluster, authority)


def run(emit: Callable[[Attempt], None]) -> list[Attempt]:
    """Try every attack in order, reporting each as it finishes; return them all."""
    attempts = []
    with lab() as setup:
        for group, title, defence, attack in ATTACKS:
            try:
                attempt = Attempt(attack.__name__, group, title, defence, True, attack(setup))
            except NotRefused as accepted:
                attempt = Attempt(attack.__name__, group, title, defence, False, str(accepted))
            attempts.append(attempt)
            emit(attempt)
    return attempts
