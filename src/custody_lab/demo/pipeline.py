"""The end-to-end demo: a FIX fill becomes a policy-approved, FROST-signed, mined settlement.

A proof-of-reserves snapshot follows. ``run`` drives every module in order and reports each step
as an ``Event`` to a callback: the CLI prints events, and the server streams them to the
dashboard. A step that raises is reported as a ``failed`` event before the exception propagates.
Each run gets a private regtest chain and signer processes, so runs can proceed side by side. The
artefacts are written under ``var/demo/<run>/``: the reserves snapshot, the policy audit log and
the event log.

Cast:
- **Clients** hold BTC with the custodian: the ledger below.
- **alpha-capital** trades on the toy exchange.
- **ops-desk** raises the settlement instruction.
- **bob** and **carol** approve it.
- Signers 1 and 3 of 3 sign it. A run can take signers offline: their processes are stopped
  before step 7, as an outage would stop them, and the coordinator asks the signers still running.
  With fewer than two left, step 7 fails and no coins move.

The network fee is charged to the client whose settlement it is, so the custody address holds
client coins only and assets equal liabilities after every batch (MiCA Article 75(7), chapter 8).
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from collections.abc import Callable, Sequence
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
from custody_lab.reserves.merkle_sum import InclusionProof, MerkleSumTree
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
    "policy": "Build the transaction and apply the policy",
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
TRADER = "alpha-capital"
ORDERS = [
    Order("C1", "BTC-USD", "sell", Decimal("0.40"), Decimal("64000")),
    Order("C2", "BTC-USD", "buy", Decimal("0.15"), Decimal("63950.50")),
    Order("C3", "BTC-USD", "sell", Decimal("0.35"), Decimal("64010")),
    Order("C4", "BTC-USD", "sell", Decimal("0.25"), Decimal("64020")),
]
SIGNERS = [1, 3]  # the signers the coordinator asks while both are online
SHARES = (1, 2, 3)
FEE_CAP_SATS = 10_000  # the most network fee a settlement may pay
RUNS = Path("var/demo")


@dataclass(frozen=True)
class Event:
    step: str
    status: str  # "running" | "done" | "failed"
    title: str
    detail: dict[str, Any] = field(default_factory=dict)
    at_ms: int = 0  # milliseconds since the run started, on the monotonic clock

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


Emit = Callable[[Event], None]


def _now() -> datetime:
    return datetime.now(UTC)


def show_btc(sats: int) -> str:
    """Satoshis as BTC for the screen, with at least two decimals: 5.00, 0.85, 4.1499969."""
    btc = bitcoin.to_btc(sats)
    shown = btc.quantize(Decimal("0.01")) if btc == btc.quantize(Decimal("0.01")) else btc
    return f"{shown:f} BTC"


def published_proof(proof: InclusionProof) -> dict[str, Any]:
    """The inclusion proof a client receives: its balance, its salt and the path to the root.

    The dashboard checks it in the browser (``web/src/reserves.ts``) without the Python code.
    """
    return {
        "client": proof.client_id,
        "balance": format(proof.balance, "f"),  # never exponent notation (1E-8)
        "salt": proof.salt.hex(),
        "path": [
            {"hash": s.sibling.hash.hex(), "sats": s.sibling.sats, "left": s.sibling_is_left}
            for s in proof.path
        ],
    }


def new_workdir(root: Path = RUNS) -> Path:
    """Create a fresh run directory under ``root``, named by its UTC start time."""
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(tempfile.mkdtemp(prefix=f"{stamp}-", dir=root))


def _asked(offline: Sequence[int], threshold: int) -> list[int]:
    """The signers the coordinator asks: ``SIGNERS`` where online, topped up from the others."""
    online = [i for i in SHARES if i not in offline]
    asked = [i for i in SIGNERS if i in online]
    asked += [i for i in online if i not in asked][: max(0, threshold - len(asked))]
    return sorted(asked)


def run(emit: Emit, workdir: Path, offline: Sequence[int] = ()) -> dict[str, Any]:
    """Run the demo end to end in ``workdir``; return the final summary.

    The signers in ``offline`` have their processes stopped before step 7.
    """
    offline = sorted(set(offline))
    if not set(offline) <= set(SHARES):
        raise ValueError(f"offline signers must be among {SHARES}, not {offline}")
    events: list[Event] = []
    current = next(iter(STEPS))
    started = time.monotonic()

    def report(step: str, status: str, **detail: Any) -> None:
        nonlocal current
        current = step
        at_ms = round((time.monotonic() - started) * 1000)
        event = Event(step, status, STEPS[step], detail, at_ms)
        events.append(event)
        emit(event)

    approvers = {n: Ed25519PrivateKey.generate() for n in ("bob", "carol")}
    custodian_key = Ed25519PrivateKey.generate()
    node: RegtestNode | None = None
    report("chain", "running")
    try:  # a missing or failing bitcoind is reported as step 1 failing
        node = RegtestNode(workdir / "node")
        rpc = node.start()
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
        with SigningCluster(2, len(SHARES), authority=engine.authority_public_key) as cluster:
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
            funding = sum(LEDGER.values(), Decimal(0))
            fund_txid = exchange.call("sendtoaddress", address, str(funding))
            rpc.call("generatetoaddress", 1, mine_to)
            report(
                "fund",
                "done",
                txid=fund_txid,
                amount=f"{funding} BTC",
                ledger={client: f"{balance} BTC" for client, balance in LEDGER.items()},
            )

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
                client_delivers=f"{-position.base} {position.base_asset}",
                client_receives=f"{position.quote:,} {position.quote_asset}",
                instruction={"asset": ins.asset, "amount": ins.amount, "to": ins.destination},
            )

            report("policy", "running")
            amount = bitcoin.to_sats(ins.amount)
            destination = chain.script_pubkey(rpc, settle_to)
            change = bitcoin.p2tr_script(output_key)
            utxos = chain.custody_utxos(rpc, output_key)
            stx = transfer.build(utxos, amount, destination, change)
            transfer.check_matches(stx, amount, destination, change, max_fee=FEE_CAP_SATS)
            first = [Approval.create(ins, "bob", approvers["bob"])]
            try:
                engine.authorise(ins, first, stx.sighash())
                raise RuntimeError("one approval must not be enough for this tier")
            except PolicyDenied as denied:
                pending = denied.decision
            both = first + [Approval.create(ins, "carol", approvers["carol"])]
            token = engine.authorise(ins, both, stx.sighash())
            spent = stx.tx.inputs[0]
            report(
                "policy",
                "done",
                spends=f"{show_btc(stx.spent.amount)}, output {spent.vout} of {spent.txid}",
                pays=[
                    {
                        "to": "exchange" if o.script_pubkey == destination else "custody (change)",
                        "amount": show_btc(o.amount),
                    }
                    for o in stx.tx.outputs
                ],
                matches_instruction=True,  # check_matches raises otherwise
                fee=f"{stx.fee} sats",
                fee_cap=f"{FEE_CAP_SATS:,} sats",
                sighash=stx.sighash().hex(),
                initiator=ins.initiator,
                policy_checks=[
                    "asset",
                    "amount",
                    "tier",
                    "whitelist",
                    "velocity",
                    "not authorised before",
                    "approvals",
                ],
                with_one_approval=f"{pending.status.value}: {pending.reason}",
                approved_by=["bob", "carol"],
                authorisation_id=token.authorisation_id,
            )

            signers = _asked(offline, cluster.threshold)
            report("sign", "running", signers=signers, offline=offline)
            for i in offline:
                cluster.stop(i)
            try:
                signature = cluster.sign(stx.sighash(), signers, token.to_bytes(), taproot=True)
            except (RuntimeError, ValueError) as refused:
                if len(signers) >= cluster.threshold:
                    raise
                online = cluster.count - len(offline)
                raise RuntimeError(
                    f"{online} of {cluster.count} signers online and {cluster.threshold} "
                    f"are required; FROST refused: {refused}"
                ) from refused
            if not schnorr.verify(stx.sighash(), output_key, signature):
                raise RuntimeError("aggregated signature does not verify")
            report(
                "sign",
                "done",
                signers=signers,
                offline=offline,
                signature=signature.hex(),
                verified=True,
            )

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
                fee=f"{stx.fee} sats",
            )

            report("reserves", "running")
            ledger = dict(LEDGER)
            ledger[TRADER] -= ins.amount + bitcoin.to_btc(stx.fee)
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
            proof_of_control = cluster.sign(message, signers, attest.to_bytes(), taproot=True)
            if not schnorr.verify(message, output_key, proof_of_control):
                raise RuntimeError("proof-of-control signature does not verify")
            path = publish(snapshot, proof_of_control, workdir / "reserves")
            report(
                "reserves",
                "done",
                liabilities=f"{snapshot.liabilities} BTC",
                assets=f"{snapshot.assets} BTC",
                reserve_ratio=snapshot.reserve_ratio,
                root=snapshot.liabilities_root,
                inclusion_proofs_verify=proofs_ok,
                proof_of_control=True,
                audit_head=snapshot.audit_head,
                snapshot=os.path.relpath(path),  # no home directory on screen
                snapshot_document=json.loads(path.read_text()),  # as a client downloads it
                # each client receives only its own; the dashboard plays every client
                inclusion_proofs=[published_proof(tree.proof(c)) for c in ledger],
            )
            del custodian_key  # reserved for signing published snapshots in a later module
    except Exception as exc:
        report(current, "failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if node is not None:
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
