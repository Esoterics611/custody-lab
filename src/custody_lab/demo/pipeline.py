"""The end-to-end demo: a FIX fill becomes a policy-approved, FROST-signed, mined settlement.

A proof-of-reserves snapshot follows. ``run`` drives every module in order and reports each step
as an ``Event`` to a callback: the CLI prints events, and the dashboard receives them over
server-sent events. Each run gets a private regtest chain and signer processes. The artefacts are
written under ``var/demo/<run>/``: the reserves snapshot, the policy audit log and the event log.

Cast:
- **Clients** hold BTC with the custodian: the ledger below.
- **alpha-capital** trades on the toy exchange.
- **ops-desk** raises the settlement instruction.
- **bob** and **carol** approve it.
- Signers 1 and 3 of 3 sign it.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custody_lab.foundations import schnorr
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy.audit import AuditLog, verify_chain
from custody_lab.policy.authorisation import AuthorityKey
from custody_lab.policy.engine import AssetPolicy, Policy, PolicyDenied, PolicyEngine, Tier
from custody_lab.policy.model import Approval, SettlementInstruction
from custody_lab.reserves.merkle_sum import MerkleSumTree
from custody_lab.reserves.merkle_sum import verify as verify_inclusion
from custody_lab.reserves.snapshot import Snapshot, publish
from custody_lab.settlement import bitcoin, chain, transfer
from custody_lab.settlement.netting import net
from custody_lab.settlement.regtest import RegtestNode
from custody_lab.trading.fix import Order, trade

STEPS = {
    "chain": "Start a private Bitcoin Core regtest chain",
    "keys": "Distributed key generation: 2-of-3, one process per share",
    "fund": "Fund the custody address",
    "trade": "FIX 5.0 SP2 trading session with the exchange",
    "net": "Net the settlement cycle into one instruction",
    "policy": "Policy engine: default deny, quorum, whitelist, velocity",
    "sign": "Threshold signature from 2 of 3 signer processes",
    "broadcast": "Broadcast and confirm on chain",
    "reserves": "Proof-of-reserves snapshot with proof of control",
}
LEDGER = {  # client BTC balances held by the custodian before the cycle
    "alpha-capital": Decimal("2.00"),
    "beta-fund": Decimal("1.50"),
    "gamma-treasury": Decimal("1.00"),
    "delta-trading": Decimal("0.50"),
}
HOUSE_BUFFER = Decimal("0.01")  # the custodian's own BTC; pays network fees
TRADER = "alpha-capital"
ORDERS = [
    Order("C1", "BTC-USD", "sell", Decimal("0.40"), Decimal("64000")),
    Order("C2", "BTC-USD", "buy", Decimal("0.15"), Decimal("63950.50")),
    Order("C3", "BTC-USD", "sell", Decimal("0.35"), Decimal("64010")),
    Order("C4", "BTC-USD", "sell", Decimal("0.25"), Decimal("64020")),
]
SIGNERS = [1, 3]


@dataclass(frozen=True)
class Event:
    step: str
    status: str  # "running" | "done"
    title: str
    detail: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


Emit = Callable[[Event], None]


def _now() -> datetime:
    return datetime.now(UTC)


def run(emit: Emit, workdir: Path) -> dict[str, Any]:
    """Run the demo end to end in ``workdir``; return the final summary."""
    events: list[Event] = []

    def report(step: str, status: str, **detail: Any) -> None:
        event = Event(step, status, STEPS[step], detail)
        events.append(event)
        emit(event)

    approvers = {n: Ed25519PrivateKey.generate() for n in ("bob", "carol")}
    custodian_key = Ed25519PrivateKey.generate()
    node = RegtestNode(workdir / "node")
    report("chain", "running")
    rpc = node.start()
    try:
        rpc.call("createwallet", "exchange")
        exchange = rpc.wallet("exchange")
        mine_to = exchange.call("getnewaddress")
        rpc.call("generatetoaddress", 101, mine_to)
        settle_to = exchange.call("getnewaddress", "", "bech32")
        report("chain", "done", height=rpc.call("getblockcount"), exchange_address=settle_to)

        btc_policy = AssetPolicy(
            tiers=(Tier(Decimal("0.1"), 1), Tier(Decimal("10"), 2)),
            whitelist=frozenset({settle_to}),
            velocity_window=timedelta(hours=24),
            velocity_limit=Decimal("20"),
        )
        policy = Policy({"BTC": btc_policy}, {n: k.public_key() for n, k in approvers.items()})
        engine = PolicyEngine(policy, AuthorityKey.generate(), AuditLog(_now), _now)

        report("keys", "running")
        with SigningCluster(2, 3, authority=engine.authority_public_key) as cluster:
            internal = cluster.dkg()
            output_key = cluster.taproot_output_key()
            address = chain.custody_address(rpc, internal)
            agree = output_key == bitcoin.taproot_tweak(internal) and chain.script_pubkey(
                rpc, address
            ) == bitcoin.p2tr_script(output_key)
            if not agree:
                raise RuntimeError("Rust, Python and Bitcoin Core disagree on the custody key")
            report(
                "keys",
                "done",
                signers=[{"share": i, "pid": pid} for i, pid in cluster.holders().items()],
                threshold="2 of 3",
                group_key=internal.hex(),
                output_key=output_key.hex(),
                address=address,
                implementations_agree=True,
            )

            report("fund", "running")
            funding = sum(LEDGER.values(), HOUSE_BUFFER)
            fund_txid = exchange.call("sendtoaddress", address, str(funding))
            rpc.call("generatetoaddress", 1, mine_to)
            report("fund", "done", txid=fund_txid, amount=funding, ledger=LEDGER)

            report("trade", "running")
            fills, transcript = trade(ORDERS)
            report(
                "trade",
                "done",
                client=TRADER,
                fills=[asdict(f) for f in fills],
                fix_messages=len(transcript),
                transcript=transcript,
            )

            report("net", "running")
            position = net(fills)
            if not position.client_delivers_base:
                raise RuntimeError("demo expects the client to deliver BTC")
            ins = SettlementInstruction(
                "settle-cycle-1", "BTC", -position.base, settle_to, "ops-desk", _now()
            )
            report(
                "net",
                "done",
                fills=position.fills,
                base=position.base,
                quote=position.quote,
                instruction={"asset": ins.asset, "amount": ins.amount, "to": ins.destination},
            )

            report("policy", "running")
            amount = bitcoin.to_sats(ins.amount)
            destination = chain.script_pubkey(rpc, settle_to)
            change = bitcoin.p2tr_script(output_key)
            utxos = chain.custody_utxos(rpc, output_key)
            stx = transfer.build(utxos, amount, destination, change)
            transfer.check_matches(stx, amount, destination, change, max_fee=10_000)
            first = [Approval.create(ins, "bob", approvers["bob"])]
            try:
                engine.authorise(ins, first, stx.sighash())
                raise RuntimeError("one approval must not be enough for this tier")
            except PolicyDenied as denied:
                pending = denied.decision
            both = first + [Approval.create(ins, "carol", approvers["carol"])]
            token = engine.authorise(ins, both, stx.sighash())
            report(
                "policy",
                "done",
                initiator=ins.initiator,
                with_one_approval=f"{pending.status.value}: {pending.reason}",
                approved_by=["bob", "carol"],
                authorisation_id=token.authorisation_id,
                sighash=stx.sighash().hex(),
                checks=["asset", "amount", "tier quorum", "whitelist", "velocity", "fee cap"],
            )

            report("sign", "running", signers=SIGNERS)
            signature = cluster.sign(stx.sighash(), SIGNERS, token.to_bytes(), taproot=True)
            if not schnorr.verify(stx.sighash(), output_key, signature):
                raise RuntimeError("aggregated signature does not verify")
            report("sign", "done", signers=SIGNERS, signature=signature.hex(), verified=True)

            report("broadcast", "running")
            txid = rpc.call("sendrawtransaction", stx.finalize(signature))
            block_hash = rpc.call("generatetoaddress", 1, mine_to)[0]
            confirmations = rpc.call("getrawtransaction", txid, True)["confirmations"]
            report(
                "broadcast",
                "done",
                txid=txid,
                block=block_hash,
                confirmations=confirmations,
                fee_sats=stx.fee,
            )

            report("reserves", "running")
            ledger = dict(LEDGER)
            ledger[TRADER] -= ins.amount
            tree = MerkleSumTree(ledger)
            proofs_ok = all(verify_inclusion(tree.proof(c), tree.root) for c in ledger)
            assets = bitcoin.to_btc(sum(u.amount for u in chain.custody_utxos(rpc, output_key)))
            verify_chain(engine.audit.entries)
            snapshot = Snapshot(
                taken_at=_now(),
                block_height=rpc.call("getblockcount"),
                block_hash=rpc.call("getbestblockhash"),
                liabilities_root=tree.root.hash.hex(),
                liabilities=tree.root.total,
                clients=len(ledger),
                assets=assets,
                custody_output_key=output_key.hex(),
                audit_head=engine.audit.head,
            )
            attest = engine.authorise_attestation(snapshot.statement())
            message = snapshot.attestation_message()
            proof_of_control = cluster.sign(message, SIGNERS, attest.to_bytes(), taproot=True)
            if not schnorr.verify(message, output_key, proof_of_control):
                raise RuntimeError("proof-of-control signature does not verify")
            path = publish(snapshot, proof_of_control, workdir / "reserves")
            report(
                "reserves",
                "done",
                liabilities=snapshot.liabilities,
                assets=snapshot.assets,
                reserve_ratio=snapshot.reserve_ratio,
                root=snapshot.liabilities_root,
                inclusion_proofs_verify=proofs_ok,
                proof_of_control=True,
                audit_head=snapshot.audit_head,
                snapshot=str(path),
            )
            del custodian_key  # reserved for signing published snapshots in a later module
    finally:
        node.stop()
        shutil.rmtree(workdir / "node", ignore_errors=True)
        (workdir / "audit.jsonl").write_text(
            "".join(json.dumps(asdict(e), default=str) + "\n" for e in engine.audit.entries)
            if "engine" in locals()
            else ""
        )
        (workdir / "events.jsonl").write_text("".join(e.to_json() + "\n" for e in events))
    return {
        "txid": txid,
        "reserve_ratio": snapshot.reserve_ratio,
        "snapshot": str(path),
        "workdir": str(workdir),
    }
