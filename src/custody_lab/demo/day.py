"""A day at the custodian: deposits, trading, netting across clients, withdrawals and refusals.

EDUCATIONAL, NOT PRODUCTION. ``run`` drives the same modules as ``pipeline.run`` through a busier
day and reports each step as an ``Event``. After every step it reconciles the custodian's books
with the chain: the ledger's total must equal the coins at the custody address, to the satoshi.

The day:

1. A private chain starts, and each of the four clients gets a wallet of its own with coins in it.
2. Three processes generate the 2-of-3 custody key.
3. Each client deposits. delta-trading replaces its deposit before it confirms, paying itself
   instead. The custodian credits a deposit only once it has a confirmation, so delta-trading is
   credited nothing and the books stay equal to the chain.
4. alpha-capital sells 1.20 BTC and beta-fund buys 0.45 BTC, each in its own FIX session.
5. The custodian nets each client's fills, then nets across its clients: 0.75 BTC goes to the
   exchange on chain, and beta-fund's 0.45 BTC is settled inside the custodian's books.
6. The settlement is approved, signed by signers 1 and 3, and confirmed. The coin it spends was
   deposited by gamma-treasury: coins at one address are interchangeable, and the ledger, not the
   coin, says whose they are.
7. Signer 3 is taken down for maintenance; signers 1 and 2 sign for the rest of the day.
8. gamma-treasury withdraws 0.60 BTC (two approvals) and beta-fund 0.05 BTC (one approval, the
   lower tier).
9. Three withdrawal requests are refused: delta-trading holds nothing (the ledger), alpha-capital
   names an address it never registered (the whitelist), and alpha-capital's retry to its
   registered address would take the day past the 1.50 BTC limit (velocity).
10. The end-of-day proof of reserves, signed by signers 1 and 2.

The demo has one custody address, so it attributes each deposit by the transaction id the client
reports. A real custodian gives each client a deposit address of its own, so that the chain itself
says whose a deposit is.

Each network fee is charged to the client the payment is for: the delivering client for the
settlement, the withdrawing client for a withdrawal. The custody address therefore holds client
coins only, and the books equal the chain after every step.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custody_lab.demo.pipeline import (
    FEE_CAP_SATS,
    Emit,
    Event,
    published_proof,
    show_btc,
)
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
from custody_lab.settlement.regtest import BitcoinRPC, RegtestNode, RPCError
from custody_lab.trading.fix import Fill, Order, trade

STEPS = {
    "chain": "Start the chain and give each client a wallet of its own",
    "keys": "Generate the custody key: 2-of-3, one process per share",
    "deposits": "Clients deposit; only confirmed deposits are credited",
    "trade": "Two clients trade over FIX, each in its own session",
    "net": "Net each client, then net across clients",
    "settle": "Settle the net with the exchange",
    "outage": "Signer 3 goes down for maintenance",
    "withdraw_gamma": "gamma-treasury withdraws 0.60 BTC: two approvals",
    "withdraw_beta": "beta-fund withdraws 0.05 BTC: one approval",
    "refused": "Three withdrawal requests the custodian refuses",
    "reserves": "End-of-day proof of reserves",
}
CLIENTS = ("alpha-capital", "beta-fund", "gamma-treasury", "delta-trading")
DEPOSITS = {  # BTC each client deposits
    "alpha-capital": Decimal("2.00"),
    "beta-fund": Decimal("1.50"),
    "gamma-treasury": Decimal("1.00"),
    "delta-trading": Decimal("0.50"),
}
DOUBLE_SPENDER = "delta-trading"
WALLET_FUNDING = Decimal("3")  # BTC each client's own wallet starts with
TRADES = {
    "alpha-capital": [
        Order("A1", "BTC-USD", "sell", Decimal("0.80"), Decimal("64000")),
        Order("A2", "BTC-USD", "sell", Decimal("0.40"), Decimal("64050")),
    ],
    "beta-fund": [Order("B1", "BTC-USD", "buy", Decimal("0.45"), Decimal("63980"))],
}
COMP_IDS = {"alpha-capital": "ALPHA-CAPITAL", "beta-fund": "BETA-FUND"}  # FIX SenderCompIDs
DAILY_LIMIT = Decimal("1.50")  # BTC authorised per rolling 24 hours
TIERS = {1: "up to 0.1 BTC: one approval", 2: "up to 10 BTC: two approvals"}
MORNING_SIGNERS = [1, 3]
MAINTENANCE = 3  # the signer taken down at noon
AFTERNOON_SIGNERS = [1, 2]
RUNS = Path("var/day")


@dataclass(frozen=True)
class Request:
    """A withdrawal a client asks for."""

    instruction_id: str
    client: str
    amount: Decimal
    to: str  # "registered" or "unregistered"
    approvers: tuple[str, ...]


WITHDRAWALS = {  # step -> request
    "withdraw_gamma": Request(
        "withdraw-gamma-1", "gamma-treasury", Decimal("0.60"), "registered", ("bob", "carol")
    ),
    "withdraw_beta": Request(
        "withdraw-beta-1", "beta-fund", Decimal("0.05"), "registered", ("bob",)
    ),
}
REFUSED = [
    Request("withdraw-delta-1", "delta-trading", Decimal("0.20"), "registered", ("bob", "carol")),
    Request("withdraw-alpha-1", "alpha-capital", Decimal("0.30"), "unregistered", ("bob", "carol")),
    Request("withdraw-alpha-2", "alpha-capital", Decimal("0.30"), "registered", ("bob", "carol")),
]


def _now() -> datetime:
    return datetime.now(UTC)


def _custody_vout(rpc: BitcoinRPC, txid: str, script: bytes) -> int:
    """The output of ``txid`` that pays the custody script."""
    outputs = rpc.call("getrawtransaction", txid, True)["vout"]
    return next(int(o["n"]) for o in outputs if o["scriptPubKey"]["hex"] == script.hex())


def _confirmations(rpc: BitcoinRPC, txid: str) -> int | None:
    """Confirmations of ``txid``; None if no node has it any more (it was replaced)."""
    try:
        return int(rpc.call("getrawtransaction", txid, True).get("confirmations", 0))
    except RPCError:
        return None


def _replace_with_payment_to_self(rpc: BitcoinRPC, wallet: BitcoinRPC, txid: str) -> str:
    """Spend the inputs of unconfirmed ``txid`` again, back to the wallet, at a higher fee.

    Bitcoin Core relays a replacement that pays a higher fee than the transaction it replaces;
    the replaced transaction leaves every mempool and never confirms.
    """
    vin = rpc.call("getrawtransaction", txid, True)["vin"]
    spent = sum(
        Decimal(str(rpc.call("getrawtransaction", i["txid"], True)["vout"][i["vout"]]["value"]))
        for i in vin
    )
    inputs = [{"txid": i["txid"], "vout": i["vout"]} for i in vin]
    outputs = [{wallet.call("getnewaddress"): str(spent - Decimal("0.001"))}]
    unsigned = rpc.call("createrawtransaction", inputs, outputs)
    signed = wallet.call("signrawtransactionwithwallet", unsigned)
    replacement: str = rpc.call("sendrawtransaction", signed["hex"])
    return replacement


def run(emit: Emit, workdir: Path) -> dict[str, Any]:
    """Run the day in ``workdir``; return the end-of-day summary."""
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
    ledger = {client: Decimal(0) for client in CLIENTS}  # BTC the custodian owes each client
    origins: dict[str, str] = {}  # "txid:vout" of a custody coin -> where it came from
    node: RegtestNode | None = None
    report("chain", "running")
    try:
        node = RegtestNode(workdir / "node")
        rpc = node.start()
        rpc.call("createwallet", "exchange")
        exchange = rpc.wallet("exchange")
        mine_to = exchange.call("getnewaddress")
        rpc.call("generatetoaddress", 101, mine_to)
        wallets: dict[str, BitcoinRPC] = {}
        registered: dict[str, str] = {}
        for client in CLIENTS:
            rpc.call("createwallet", client)
            wallets[client] = rpc.wallet(client)
            funding = wallets[client].call("getnewaddress")
            exchange.call("sendtoaddress", funding, str(WALLET_FUNDING))
            registered[client] = wallets[client].call("getnewaddress", "", "bech32")
        unregistered = wallets["alpha-capital"].call("getnewaddress", "", "bech32")
        rpc.call("generatetoaddress", 1, mine_to)
        settle_to = exchange.call("getnewaddress", "", "bech32")
        report(
            "chain",
            "done",
            height=rpc.call("getblockcount"),
            client_wallets={c: show_btc(bitcoin.to_sats(WALLET_FUNDING)) for c in CLIENTS},
            registered_withdrawal_addresses=registered,
            exchange_address=settle_to,
        )

        policy = Policy(
            {
                "BTC": AssetPolicy(
                    tiers=(Tier(Decimal("0.1"), 1), Tier(Decimal("10"), 2)),
                    whitelist=frozenset({settle_to, *registered.values()}),
                    velocity_window=timedelta(hours=24),
                    velocity_limit=DAILY_LIMIT,
                )
            },
            {n: k.public_key() for n, k in approvers.items()},
        )
        engine = PolicyEngine(policy, AuthorityKey.generate(), AuditLog(_now), _now)

        report("keys", "running")
        with SigningCluster(2, 3, authority=engine.authority_public_key) as cluster:
            internal = cluster.dkg()
            output_key = cluster.taproot_output_key()
            address = chain.custody_address(rpc, internal)
            custody_script = bitcoin.p2tr_script(output_key)
            if chain.script_pubkey(rpc, address) != custody_script:
                raise RuntimeError("Python and Bitcoin Core disagree on the custody address")

            def books() -> dict[str, Any]:
                """The ledger, the coins at the custody address, and whether they agree."""
                coins = chain.custody_utxos(rpc, output_key)
                held = sum(c.amount for c in coins)
                owed = sum(bitcoin.to_sats(b) for b in ledger.values())
                return {
                    "ledger": {c: show_btc(bitcoin.to_sats(b)) for c, b in ledger.items()},
                    "coins": [
                        {
                            "coin": f"{c.txid}:{c.vout}",
                            "amount": show_btc(c.amount),
                            "origin": origins.get(f"{c.txid}:{c.vout}", "unknown"),
                        }
                        for c in sorted(coins, key=lambda c: -c.amount)
                    ],
                    "owed": show_btc(owed),
                    "held": show_btc(held),
                    "reconciled": owed == held,
                }

            report(
                "keys",
                "done",
                signers=[{"share": i, "pid": pid} for i, pid in cluster.holders().items()],
                threshold="2 of 3",
                group_key=internal.hex(),
                address=address,
                books=books(),
            )

            report("deposits", "running")
            sent = {c: wallets[c].call("sendtoaddress", address, str(DEPOSITS[c])) for c in CLIENTS}
            in_mempool = set(rpc.call("getrawmempool"))
            seen = sorted(c for c in CLIENTS if sent[c] in in_mempool)
            replacement = _replace_with_payment_to_self(
                rpc, wallets[DOUBLE_SPENDER], sent[DOUBLE_SPENDER]
            )
            rpc.call("generatetoaddress", 1, mine_to)
            deposits = []
            for client in CLIENTS:
                confirmations = _confirmations(rpc, sent[client])
                if confirmations:
                    ledger[client] += DEPOSITS[client]
                    vout = _custody_vout(rpc, sent[client], custody_script)
                    origins[f"{sent[client]}:{vout}"] = f"deposit from {client}"
                    status = f"credited at {confirmations} confirmation"
                else:
                    status = "replaced before it confirmed: not credited"
                deposits.append(
                    {
                        "client": client,
                        "amount": show_btc(bitcoin.to_sats(DEPOSITS[client])),
                        "status": status,
                        "txid": sent[client],
                    }
                )
            report(
                "deposits",
                "done",
                seen_unconfirmed=f"{len(seen)} deposits in the mempool, none credited yet",
                deposits=deposits,
                replacement=f"{DOUBLE_SPENDER} paid the same coins back to itself in {replacement}",
                credit_rule="credit a deposit only once it has a confirmation",
                books=books(),
            )

            report("trade", "running")
            sessions: dict[str, dict[str, Any]] = {}
            fills: dict[str, list[Fill]] = {}
            for client, orders in TRADES.items():
                fills[client], transcript = trade(orders, COMP_IDS[client])
                sessions[client] = {
                    "sender_comp_id": COMP_IDS[client],
                    "fills": [asdict(f) for f in fills[client]],
                    "transcript": transcript,
                }
            report("trade", "done", **sessions)  # one entry per client, by name

            report("net", "running")
            positions = {client: net(f) for client, f in fills.items()}
            base = sum((p.base for p in positions.values()), Decimal(0))
            quote = sum((p.quote for p in positions.values()), Decimal(0))
            if base >= 0:
                raise RuntimeError("the day expects the custodian to deliver BTC to the exchange")
            delivered = -base
            internalised = min(
                sum((-p.base for p in positions.values() if p.base < 0), Decimal(0)),
                sum((p.base for p in positions.values() if p.base > 0), Decimal(0)),
            )
            settlement = SettlementInstruction(
                "settle-day-1", "BTC", delivered, settle_to, "ops-desk", _now()
            )
            report(
                "net",
                "done",
                per_client=[
                    {
                        "client": client,
                        "btc": f"{'delivers' if p.base < 0 else 'receives'} "
                        f"{show_btc(bitcoin.to_sats(abs(p.base)))}",
                        "usd": f"{'receives' if p.quote > 0 else 'pays'} {abs(p.quote):,.2f} USD",
                    }
                    for client, p in positions.items()
                ],
                custodian_delivers=f"{show_btc(bitcoin.to_sats(delivered))} to the exchange",
                custodian_receives=f"{quote:,.2f} USD from the exchange",
                internalised=f"{internalised} BTC moves from alpha-capital to beta-fund in the "
                "custodian's books only",
                instruction={"id": settlement.instruction_id, "amount": f"{delivered} BTC"},
            )

            def pay(
                ins: SettlementInstruction, names: tuple[str, ...], signers: list[int]
            ) -> tuple[dict[str, Any], Decimal]:
                """Build, check, authorise, sign, broadcast and confirm one payment."""
                amount = bitcoin.to_sats(ins.amount)
                destination = chain.script_pubkey(rpc, ins.destination)
                coins = chain.custody_utxos(rpc, output_key)
                stx = transfer.build(coins, amount, destination, custody_script)
                transfer.check_matches(stx, amount, destination, custody_script, FEE_CAP_SATS)
                spent = stx.tx.inputs[0]
                approvals = [Approval.create(ins, n, approvers[n]) for n in names]
                token = engine.authorise(ins, approvals, stx.sighash())
                signature = cluster.sign(stx.sighash(), signers, token.to_bytes(), taproot=True)
                if not schnorr.verify(stx.sighash(), output_key, signature):
                    raise RuntimeError("aggregated signature does not verify")
                txid = rpc.call("sendrawtransaction", stx.finalize(signature))
                rpc.call("generatetoaddress", 1, mine_to)
                change = [i for i, o in enumerate(stx.tx.outputs) if o.script_pubkey != destination]
                for vout in change:
                    origins[f"{txid}:{vout}"] = f"change from {ins.instruction_id}"
                return {
                    "instruction": ins.instruction_id,
                    "coin_spent": f"{show_btc(stx.spent.amount)}, "
                    f"{origins.pop(f'{spent.txid}:{spent.vout}', 'a custody coin')}",
                    "pays": show_btc(amount),
                    "change": show_btc(stx.spent.amount - amount - stx.fee) if change else "none",
                    "fee": f"{stx.fee} sats",
                    "approved_by": list(names),
                    "signers": signers,
                    "txid": txid,
                    "confirmations": _confirmations(rpc, txid),
                }, bitcoin.to_btc(stx.fee)

            report("settle", "running", signers=MORNING_SIGNERS)
            paid, fee = pay(settlement, ("bob", "carol"), MORNING_SIGNERS)
            for client, p in positions.items():
                ledger[client] += p.base
            ledger["alpha-capital"] -= fee  # the delivering client pays the network fee
            report(
                "settle",
                "done",
                **paid,
                fee_charged_to="alpha-capital, the delivering client",
                books=books(),
            )

            report("outage", "running")
            cluster.stop(MAINTENANCE)
            report(
                "outage",
                "done",
                stopped=f"signer {MAINTENANCE}'s process; its share is unusable until it returns",
                online=AFTERNOON_SIGNERS,
                still_signs="any 2 of 3: signers 1 and 2 sign for the rest of the day",
            )

            for step, request in WITHDRAWALS.items():
                report(step, "running", signers=AFTERNOON_SIGNERS)
                ins = SettlementInstruction(
                    request.instruction_id,
                    "BTC",
                    request.amount,
                    registered[request.client],
                    "ops-desk",
                    _now(),
                )
                paid, fee = pay(ins, request.approvers, AFTERNOON_SIGNERS)
                ledger[request.client] -= request.amount + fee
                report(
                    step,
                    "done",
                    client=request.client,
                    to=f"{request.client}'s registered address",
                    tier=TIERS[len(request.approvers)],
                    **paid,
                    books=books(),
                )

            report("refused", "running")
            fee_estimate = bitcoin.to_btc(bitcoin.estimated_vsize(1, 2) * 2)
            refusals = []
            for request in REFUSED:
                owed = ledger[request.client]
                destination = (
                    registered[request.client] if request.to == "registered" else unregistered
                )
                if owed < request.amount + fee_estimate:
                    by = "the ledger"
                    reason = f"{request.client} holds {show_btc(bitcoin.to_sats(owed))}"
                else:
                    ins = SettlementInstruction(
                        request.instruction_id,
                        "BTC",
                        request.amount,
                        destination,
                        "ops-desk",
                        _now(),
                    )
                    approvals = [Approval.create(ins, n, approvers[n]) for n in request.approvers]
                    try:
                        engine.authorise(ins, approvals, bytes(32))
                        raise RuntimeError(f"{request.instruction_id} was authorised")
                    except PolicyDenied as denied:
                        by, reason = "the policy engine", str(denied)
                refusals.append(
                    {
                        "client": request.client,
                        "amount": show_btc(bitcoin.to_sats(request.amount)),
                        "refused_by": by,
                        "reason": reason,
                        "to": f"{request.to} address",
                        "request": request.instruction_id,
                    }
                )
            report(
                "refused",
                "done",
                requests=refusals,
                nothing_signed="no transaction was built or signed for any of them",
                books=books(),
            )

            report("reserves", "running", signers=AFTERNOON_SIGNERS)
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
            proof_of_control = cluster.sign(
                message, AFTERNOON_SIGNERS, attest.to_bytes(), taproot=True
            )
            if not schnorr.verify(message, output_key, proof_of_control):
                raise RuntimeError("proof-of-control signature does not verify")
            path = publish(snapshot, proof_of_control, workdir / "reserves")
            report(
                "reserves",
                "done",
                liabilities=show_btc(bitcoin.to_sats(snapshot.liabilities)),
                assets=show_btc(bitcoin.to_sats(snapshot.assets)),
                reserve_ratio=snapshot.reserve_ratio,
                root=snapshot.liabilities_root,
                inclusion_proofs_verify=proofs_ok,
                proof_of_control=f"signed by signers {' and '.join(map(str, AFTERNOON_SIGNERS))}",
                audit_entries=len(engine.audit.entries),
                audit_head=snapshot.audit_head,
                snapshot=os.path.relpath(path),
                inclusion_proofs=[published_proof(tree.proof(c)) for c in ledger],
                books=books(),
            )
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
        "liabilities": snapshot.liabilities,
        "assets": snapshot.assets,
        "reserve_ratio": snapshot.reserve_ratio,
        "snapshot": str(path),
        "workdir": str(workdir),
    }
