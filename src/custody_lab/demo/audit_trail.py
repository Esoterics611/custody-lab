"""The audit log: the policy engine's entries through two settlements, then a forger's copy.

EDUCATIONAL, NOT PRODUCTION. ``run`` starts the policy engine and bob's and carol's devices, each
in a process of its own as in the settlement run, and a 2-of-3 signing cluster, then plays two
settlement cycles and reports each step as an ``Event`` with the audit entries it added. No chain
is needed: as in the attack panel, a 32-byte hash of the instruction stands in for a transaction's
sighash, and each reserves snapshot carries block height 0, an all-zero block hash and assets
taken equal to its liabilities. What matters here is the snapshot's ``audit_head`` and the custody
key's signature over it, and both are real.

1. Start the processes. The log is empty; its head is the genesis value, 64 zeros.
2. A 0.85 BTC settlement with bob's approval alone: pending (entry 0).
3. carol approves too: evaluated and authorised (entries 1 and 2); signers 1 and 3 sign.
4. A payment to an address not on the whitelist: denied (entry 3).
5. The first snapshot anchors the head, entry 3's hash, under the custody key's signature. Its
   attestation authorisation is entry 4, written after the head was read.
6. A 0.40 BTC settlement: entries 5 and 6; signed.
7. The second snapshot anchors entry 6's hash; its attestation is entry 7.

Then a forger edits a copy of the log exported from the engine's process, which is what an auditor
would be handed; the engine's own log is untouched. Each of the last four steps is computed for
every entry in turn with the real ``verify_chain``, so that the dashboard's switch can show any of
them without hashing anything itself:

8. The entry is edited: the chain breaks at that entry, whose content no longer matches its hash.
9. Its stored hash is replaced as well: the break moves to the next entry, whose link still names
   the old hash. For the last entry nothing follows, and the chain verifies.
10. Every later entry is re-hashed: the chain verifies, with a new head.
11. Each snapshot's anchored head is looked for in the copy. A snapshot that anchored the edited
    entry or a later one no longer finds its head there, and so exposes the copy; an edit after
    the last anchor is exposed by no snapshot until the next one. A snapshot whose ``audit_head``
    is moved to the forged head no longer matches the custody key's signature.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Sequence
from contextlib import ExitStack
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from custody_lab.demo.attacks import EXCHANGE, _sighash
from custody_lab.demo.parties import ApproverDevice, PolicyService, PolicySpec
from custody_lab.demo.pipeline import LEDGER, Event
from custody_lab.foundations import schnorr
from custody_lab.foundations.hashing import sha256
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy.audit import GENESIS, AuditChainBroken, AuditEntry, verify_chain
from custody_lab.policy.engine import AssetPolicy, PolicyDenied, Tier
from custody_lab.policy.model import SettlementInstruction, canonical_json
from custody_lab.reserves.merkle_sum import MerkleSumTree
from custody_lab.reserves.snapshot import Snapshot

STEPS = {
    "start": "Start the policy engine, two approvers' devices and three signers",
    "pending": "A 0.85 BTC settlement with one approval: pending",
    "authorised": "The second approval: the settlement is authorised and signed",
    "denied": "A payment to an address not on the whitelist: denied",
    "snapshot_1": "The first reserves snapshot anchors the head",
    "second": "A 0.40 BTC settlement after the snapshot: authorised and signed",
    "snapshot_2": "The second snapshot anchors the new head",
    "edited": "A forger edits one entry of a copy: the chain breaks at that entry",
    "relinked": "It replaces that entry's hash too: the chain breaks at the next link",
    "rehashed": "It re-hashes every later entry: the chain verifies again",
    "anchored": "The heads in the signed snapshots expose the re-hashed copy",
}

# What each step does, in plain words, for the dashboard. Numbers that depend on the run are in
# the step's detail, not here.
EXPLAIN = {
    "start": "The policy engine runs in a process of its own and keeps the audit log there. "
    "Every decision it makes is appended as an entry, and each entry's hash covers its sequence "
    "number, its time, its event, its payload and the previous entry's hash. The first entry "
    "links to the genesis value, 64 zeros. The coordinator only ever reads a copy.",
    "pending": "ops-desk raises the cycle's 0.85 BTC settlement and only bob has approved it. "
    "The tier needs two approvals, so the engine records a pending evaluation: entry 0, linked "
    "to the genesis value.",
    "authorised": "carol approves as well. The engine records the evaluation, approved, and then "
    "the authorisation it issues, with the amount, the destination and the exact message the "
    "signers may sign. Each new entry links to the one before. Signers 1 and 3 sign under the "
    "authorisation and keep its identifier.",
    "denied": "A payment to an address that is not on the whitelist is refused before any "
    "approval is counted. A refusal is evidence too: it is entry 3, linked like the rest.",
    "snapshot_1": "The reserves snapshot carries the log's head, the hash of entry 3, and the "
    "custody key signs the snapshot through the policy engine and two signers. From now on, "
    "anyone holding the signed snapshot can check that a copy of the log agrees with it up to "
    "entry 3. The snapshot's own attestation is recorded after the head was read, as entry 4, "
    "so the next snapshot covers it.",
    "second": "The next settlement, 0.40 BTC, approved by bob and carol, authorised and signed: "
    "entries 5 and 6. Neither is covered by the first snapshot.",
    "snapshot_2": "The second snapshot anchors the new head, entry 6's hash. Entry 7, its "
    "attestation, is the start of what the next snapshot will cover.",
    "edited": "A forger changes one entry in a copy of the log, the copy an auditor would be "
    "handed. Recomputing that entry's hash no longer gives the hash stored with it, so the check "
    "stops there. The run makes the edit to every entry in turn; choose which one to see.",
    "relinked": "The forger stores the edited entry's new hash in place of the old one. That "
    "entry now checks, but the next entry still links to the old hash, so the check stops one "
    "entry later. Fixing one entry only moves the break; only the last entry has no successor "
    "to give it away.",
    "rehashed": "The forger recomputes every entry after the edit, each linking to the new hash "
    "before it. The chain checks from the genesis value to the end: a hash chain on its own "
    "cannot tell this copy from the real one. Every hash from the edited entry on has changed, "
    "the head included.",
    "anchored": "Each signed snapshot names a head. If the copy agrees with the log the snapshot "
    "was taken from, that hash appears in the copy, at the entry it anchored. An edit at or "
    "before the anchored entry changed that hash, so the snapshot no longer finds it. An edit "
    "after the last anchor is not exposed until the next snapshot. The forger cannot move a "
    "snapshot's head instead: the custody key's signature covers it.",
}

BTC_POLICY = AssetPolicy(  # the settlement run's policy, with the attack panel's exchange address
    tiers=(Tier(Decimal("0.1"), 1), Tier(Decimal("10"), 2)),
    whitelist=frozenset({EXCHANGE}),
    velocity_window=timedelta(hours=24),
    velocity_limit=Decimal("20"),
)
UNLISTED = "unlisted-address"
SIGNERS = [1, 3]
SHOWN = 2  # the entry the dashboard's player edits: the first settlement's authorisation
FLIPPED = {"pending": "approved", "approved": "denied", "denied": "approved"}


def _now() -> datetime:
    return datetime.now(UTC)


def _hms(moment: datetime) -> str:
    return f"{moment:%H:%M:%S} UTC"


def about(entry: AuditEntry) -> str:
    """What an entry records, in one line."""
    p = entry.payload
    match entry.event:
        case "evaluated":
            return f"{p['instruction_id']}: {p['status']}, {p['reason']}"
        case "authorised":
            return f"{p['instruction_id']}: {p['amount']:f} {p['asset']} to {p['destination']}"
        case "attestation_authorised":
            return f"a reserves snapshot's attestation, authorisation {p['authorisation_id'][:8]}"
    return entry.event


def shown(entry: AuditEntry) -> dict[str, Any]:
    """An entry as the dashboard shows it: its hashed body, canonically encoded, and its hash."""
    body: dict[str, Any] = json.loads(canonical_json(entry.body()))
    return body | {"hash": entry.hash, "about": about(entry)}


def _hash(entry: AuditEntry) -> str:
    return sha256(canonical_json(entry.body())).hex()


@dataclass(frozen=True)
class Edit:
    entry: AuditEntry  # the edited entry, its stored hash unchanged
    field: str
    before: str
    after: str


def forge(entry: AuditEntry) -> Edit:
    """The forger's edit to ``entry``: a decision reversed, an amount cut to a tenth, or a time
    moved an hour earlier."""
    p = entry.payload
    if entry.event == "evaluated":
        after = FLIPPED[p["status"]]
        return Edit(replace(entry, payload={**p, "status": after}), "status", p["status"], after)
    if entry.event == "authorised":
        cut = p["amount"] / 10
        edited = replace(entry, payload={**p, "amount": cut})
        return Edit(edited, "amount", f"{p['amount']:f} BTC", f"{cut:f} BTC")
    earlier = entry.time - timedelta(hours=1)
    return Edit(replace(entry, time=earlier), "time", _hms(entry.time), _hms(earlier))


def _breaks(entries: Sequence[AuditEntry]) -> tuple[int | None, str]:
    """Where ``verify_chain`` stops, and its words; ``None, "verifies"`` if it does not."""
    try:
        verify_chain(entries)
    except AuditChainBroken as broken:
        return broken.entry, str(broken)
    return None, "verifies"


def rehash(entries: Sequence[AuditEntry], start: int) -> list[AuditEntry]:
    """``entries`` with every hash from ``start`` on recomputed, each linking to the one before,
    as a forger who wants the chain to verify again would leave them."""
    out = list(entries[:start])
    prev = out[-1].hash if out else GENESIS
    for entry in entries[start:]:
        entry = replace(entry, prev_hash=prev)
        entry = replace(entry, hash=_hash(entry))
        out.append(entry)
        prev = entry.hash
    return out


@dataclass(frozen=True)
class Anchor:
    number: int
    snapshot: Snapshot
    entry: int  # the entry whose hash the snapshot carries
    signature: bytes


def forgeries(
    exported: Sequence[AuditEntry], anchors: Sequence[Anchor]
) -> dict[str, list[dict[str, Any]]]:
    """Each of the forger's four moves applied to each entry of ``exported`` in turn, checked with
    ``verify_chain`` and against each anchor: one list per step, one row per entry."""
    rows: dict[str, list[dict[str, Any]]] = {s: [] for s in ("edited", "relinked", "rehashed")}
    rows["anchored"] = []
    for k, entry in enumerate(exported):
        edit = forge(entry)
        name = f"entry {k} ({entry.event})"
        copy = list(exported)
        copy[k] = edit.entry
        at, words = _breaks(copy)
        recomputed = _hash(edit.entry)
        rows["edited"].append(
            {
                "entry": k,
                "field": edit.field,
                "before": edit.before,
                "after": edit.after,
                "stored_hash": entry.hash,
                "recomputed_hash": recomputed,
                "breaks_at": at,
                "reason": words,
                "says": f"{name}: {edit.field} {edit.before} -> {edit.after}; {words}",
            }
        )

        copy[k] = replace(edit.entry, hash=recomputed)
        at, words = _breaks(copy)
        rows["relinked"].append(
            {"entry": k, "breaks_at": at, "reason": words, "says": f"{name}: {words}"}
        )

        forged = rehash(copy, k)
        at, words = _breaks(forged)
        if at is not None:
            raise RuntimeError(f"the re-hashed copy does not verify: {words}")
        rows["rehashed"].append(
            {
                "entry": k,
                "entries": [
                    {"seq": e.seq, "prev_hash": e.prev_hash, "hash": e.hash} for e in forged[k:]
                ],
                "head": forged[-1].hash,
                "breaks_at": at,
                "reason": words,
                "says": f"{name}: {words}; the head is now {forged[-1].hash[:10]}",
            }
        )

        found = []
        for a in anchors:
            at_entry = next((e.seq for e in forged if e.hash == a.snapshot.audit_head), None)
            found.append(
                {
                    "snapshot": a.number,
                    "anchored_entry": a.entry,
                    "anchored_head": a.snapshot.audit_head,
                    "copy_hash": forged[a.entry].hash,
                    "found_at": at_entry,
                }
            )
        exposed_by = next((f["snapshot"] for f in found if f["found_at"] is None), None)
        verdict = (
            f"exposed by snapshot {exposed_by}, whose head is not in the copy"
            if exposed_by
            else "every anchored head is in the copy: not exposed until the next snapshot"
        )
        says = f"{name}: {verdict}"
        rows["anchored"].append(
            {"entry": k, "snapshots": found, "exposed_by": exposed_by, "says": says}
        )
    return rows


def run(emit: Callable[[Event], None]) -> dict[str, Any]:
    """Play two settlement cycles and the forger's copy; return where each edit was exposed."""
    started = time.monotonic()
    current = next(iter(STEPS))

    def report(step: str, status: str, **detail: Any) -> None:
        nonlocal current
        current = step
        at_ms = round((time.monotonic() - started) * 1000)
        emit(Event(step, status, STEPS[step], detail, at_ms))

    def begin(step: str) -> None:
        report(step, "running", explanation=EXPLAIN[step])

    parties = ExitStack()
    ledger = dict(LEDGER)
    anchors: list[Anchor] = []
    seen = 0
    begin("start")
    try:
        devices = {n: parties.enter_context(ApproverDevice(n)) for n in ("bob", "carol")}
        spec = PolicySpec({"BTC": BTC_POLICY}, {n: d.public_key for n, d in devices.items()})
        engine = parties.enter_context(PolicyService(spec))
        cluster = parties.enter_context(SigningCluster(2, 3, engine.authority_public_key))
        cluster.dkg()
        custody_key = cluster.taproot_output_key()
        report(
            "start",
            "done",
            processes={"policy engine": engine.pid}
            | {f"{n}'s device": d.pid for n, d in devices.items()}
            | {f"signer {i}": pid for i, pid in cluster.holders().items()}
            | {"coordinator": os.getpid()},
            head=GENESIS,
            custody_key=custody_key.hex(),
        )

        def logged() -> dict[str, Any]:
            """The entries added since the last call, read from the engine's process."""
            nonlocal seen
            entries, head = engine.audit()
            new, seen = entries[seen:], len(entries)
            return {"entries": [shown(e) for e in new], "head": head}

        def settle(ins: SettlementInstruction, client: str) -> dict[str, Any]:
            approvals = [devices[n].approve(ins) for n in ("bob", "carol")]
            token = engine.authorise(ins, approvals, _sighash(ins))
            signature = cluster.sign(_sighash(ins), SIGNERS, token.to_bytes(), taproot=True)
            if not schnorr.verify(_sighash(ins), custody_key, signature):
                raise RuntimeError("the settlement's signature does not verify")
            ledger[client] -= ins.amount
            return {
                "authorisation_id": token.authorisation_id,
                "signers": SIGNERS,
                "signature_valid": True,
            }

        def anchor(number: int) -> dict[str, Any]:
            """Take a snapshot that carries the engine's head and have the custody key sign it."""
            entries, head = engine.audit()
            tree = MerkleSumTree(ledger)
            snapshot = Snapshot(
                taken_at=_now(),
                block_height=0,
                block_hash="00" * 32,
                liabilities_root=tree.root.hash.hex(),
                liabilities=tree.root.total,
                clients=len(ledger),
                assets=tree.root.total,
                custody_output_key=custody_key.hex(),
                audit_head=head,
            )
            token = engine.authorise_attestation(snapshot.statement())
            message = snapshot.attestation_message()
            signature = cluster.sign(message, SIGNERS, token.to_bytes(), taproot=True)
            valid = schnorr.verify(message, custody_key, signature)
            if not valid:
                raise RuntimeError("the snapshot's signature does not verify")
            anchors.append(Anchor(number, snapshot, len(entries) - 1, signature))
            return {
                "anchored_entry": len(entries) - 1,
                "audit_head": head,
                "liabilities": f"{snapshot.liabilities} BTC",
                "signature": signature.hex(),
                "signature_valid": valid,
            } | logged()

        def instruction(name: str, amount: str, destination: str) -> SettlementInstruction:
            amount_btc = Decimal(amount)
            return SettlementInstruction(name, "BTC", amount_btc, destination, "ops-desk", _now())

        begin("pending")
        first = instruction("settle-cycle-1", "0.85", EXCHANGE)
        try:
            engine.authorise(first, [devices["bob"].approve(first)], _sighash(first))
            raise RuntimeError("one approval must not be enough for this tier")
        except PolicyDenied as denied:
            decision = f"{denied.decision.status.value}: {denied.decision.reason}"
        report("pending", "done", decision=decision, **logged())

        begin("authorised")
        signed = settle(first, "alpha-capital")
        report("authorised", "done", **signed, **logged())

        begin("denied")
        unlisted = instruction("withdrawal-1", "0.30", UNLISTED)
        try:
            approvals = [devices[n].approve(unlisted) for n in ("bob", "carol")]
            engine.authorise(unlisted, approvals, _sighash(unlisted))
            raise RuntimeError("a payment to an address off the whitelist was authorised")
        except PolicyDenied as denied:
            decision = f"{denied.decision.status.value}: {denied.decision.reason}"
        report("denied", "done", decision=decision, **logged())

        begin("snapshot_1")
        report("snapshot_1", "done", **anchor(1))

        begin("second")
        signed = settle(instruction("settle-cycle-2", "0.40", EXCHANGE), "beta-fund")
        report("second", "done", **signed, **logged())

        begin("snapshot_2")
        report("snapshot_2", "done", **anchor(2))

        exported, _ = engine.audit()  # the copy the forger edits; the engine's own log is untouched
        at, untouched = _breaks(exported)
        if at is not None:
            raise RuntimeError(f"the exported copy does not verify before any edit: {untouched}")
        rows = forgeries(exported, anchors)
        begin("edited")
        report("edited", "done", untouched=untouched, forgeries=rows["edited"], shown=SHOWN)
        for step in ("relinked", "rehashed"):
            begin(step)
            report(step, "done", forgeries=rows[step], shown=SHOWN)

        begin("anchored")
        moved = []  # each snapshot with its head moved to the shown forgery's
        for a, found in zip(anchors, rows["anchored"][SHOWN]["snapshots"], strict=True):
            altered = replace(a.snapshot, audit_head=found["copy_hash"])
            valid = schnorr.verify(altered.attestation_message(), custody_key, a.signature)
            moved.append(
                {"snapshot": a.number, "head": found["copy_hash"], "signature_valid": valid}
            )
        report("anchored", "done", forgeries=rows["anchored"], shown=SHOWN, moved_heads=moved)
    except Exception as exc:
        report(current, "failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        parties.close()
    return {
        "entries": len(exported),
        "anchored_entries": [a.entry for a in anchors],
        "exposed_by": {str(r["entry"]): r["exposed_by"] for r in rows["anchored"]},
        "moved_heads_verify": [m["signature_valid"] for m in moved],
    }
