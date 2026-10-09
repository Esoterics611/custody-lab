"""Red team: three attacks that succeed against a weak rule, then fail against the defence.

EDUCATIONAL, NOT PRODUCTION. ``run`` sets up a private chain, a 2-of-3 custody key, the policy
engine and two approvers' devices, each in its own process, and plays three attacks from
``manual/attack-vectors.md``, reporting each step as an ``Event`` and the custodian's books
against the chain after each.

**A reorganised deposit** (vector 7.2). mallory deposits 0.50 BTC. A custodian that credits at one
confirmation credits it; mallory then has the block holding the deposit replaced by a longer
branch in which the same coins pay mallory back, and the custodian owes 0.50 BTC it does not hold.
A custodian that credits at three confirmations is still waiting when the branch is replaced, and
credits nothing. On regtest the replacement is made with ``invalidateblock``, which stands in for a
miner with enough hash power to build the longer branch.

**Coins borrowed for the snapshot** (vector 9.6). The custodian hides the hole the reorganisation
left by borrowing 0.50 BTC from the exchange just before a scheduled snapshot, which then shows a
reserve ratio of 1 and is signed. It repays the loan, and an unannounced snapshot taken afterwards
shows the ratio the books really have. Both snapshots are signed by the same key; only their
timing differs.

**A misdirected withdrawal** (vector 5.7). A compromised instruction builder sends gamma-treasury's
0.40 BTC withdrawal to alpha-capital's registered address. The policy's whitelist is global, so it
passes; approvers whose devices sign blind approve it, and the coins go to the wrong client's
address. Approvers whose devices hold their own copy of each client's registered addresses refuse
it before any approval exists.
"""

from __future__ import annotations

import os
import shutil
import time
from collections.abc import Callable
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from custody_lab.demo.day import _confirmations, _custody_vout, _replace_with_payment_to_self, books
from custody_lab.demo.parties import ApproverDevice, DeviceRefused, PolicyService, PolicySpec
from custody_lab.demo.pipeline import FEE_CAP_SATS, Event
from custody_lab.foundations import schnorr
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy.engine import AssetPolicy, Tier
from custody_lab.policy.model import SettlementInstruction
from custody_lab.reserves.merkle_sum import MerkleSumTree
from custody_lab.reserves.snapshot import Snapshot, publish
from custody_lab.settlement import bitcoin, chain, transfer
from custody_lab.settlement.regtest import RegtestNode

STEPS = {
    "setup": "Start the chain, the custody key, the policy engine and the approvers' devices",
    "reorg_weak": "Credit at one confirmation: a reorganised deposit leaves a hole",
    "borrow": "Hide the hole: borrow coins for a scheduled snapshot",
    "unannounced": "Repay the loan: an unannounced snapshot shows the hole",
    "reorg_strong": "Credit at three confirmations: the same attack credits nothing",
    "blind": "A misdirected withdrawal, approved on devices that sign blind",
    "checked": "The same withdrawal, refused by devices that check the destination",
}
RUNS = Path("var/redteam")
SIGNERS = [1, 3]


def _now() -> datetime:
    return datetime.now(UTC)


def run(emit: Callable[[Event], None], workdir: Path) -> dict[str, Any]:
    """Play both attacks in ``workdir``; return whether the books matched the chain at the end."""
    started = time.monotonic()
    current = next(iter(STEPS))

    def report(step: str, status: str, **detail: Any) -> None:
        nonlocal current
        current = step
        at_ms = round((time.monotonic() - started) * 1000)
        emit(Event(step, status, STEPS[step], detail, at_ms))

    ledger = {c: Decimal(0) for c in ("gamma-treasury", "alpha-capital", "mallory")}
    origins: dict[str, str] = {}
    node: RegtestNode | None = None
    parties = ExitStack()
    report("setup", "running")
    try:
        node = RegtestNode(workdir / "node")
        rpc = node.start()
        rpc.call("createwallet", "miner")
        miner = rpc.wallet("miner")
        mine_to = miner.call("getnewaddress")
        rpc.call("generatetoaddress", 101, mine_to)
        wallets, registered = {}, {}
        for client in ledger:
            rpc.call("createwallet", client)
            wallets[client] = rpc.wallet(client)
            miner.call("sendtoaddress", wallets[client].call("getnewaddress"), "3")
            registered[client] = wallets[client].call("getnewaddress", "", "bech32")
        lender = miner.call("getnewaddress", "", "bech32")  # the exchange, which lends the coins
        rpc.call("generatetoaddress", 1, mine_to)

        book = {client: frozenset({address}) for client, address in registered.items()}
        blind = {n: parties.enter_context(ApproverDevice(n)) for n in ("bob", "carol")}
        checking = {
            n: parties.enter_context(ApproverDevice(f"{n}-checking", book))
            for n in ("bob", "carol")
        }
        policy = parties.enter_context(
            PolicyService(
                PolicySpec(
                    {
                        "BTC": AssetPolicy(
                            (Tier(Decimal("0.1"), 1), Tier(Decimal("10"), 2)),
                            frozenset({*registered.values(), lender}),  # one global whitelist
                            timedelta(hours=24),
                            Decimal("20"),
                        )
                    },
                    {
                        **{n: d.public_key for n, d in blind.items()},
                        **{d.name: d.public_key for d in checking.values()},
                    },
                )
            )
        )
        cluster = parties.enter_context(SigningCluster(2, 3, policy.authority_public_key))
        internal = cluster.dkg()
        output_key = cluster.taproot_output_key()
        address = chain.custody_address(rpc, internal)
        script = bitcoin.p2tr_script(output_key)

        honest = wallets["gamma-treasury"].call("sendtoaddress", address, "1.00")
        rpc.call("generatetoaddress", 3, mine_to)
        ledger["gamma-treasury"] += Decimal("1.00")
        origins[f"{honest}:{_custody_vout(rpc, honest, script)}"] = "deposit from gamma-treasury"
        report(
            "setup",
            "done",
            custody_address=address,
            gamma_treasury_deposit="1.00 BTC, credited at 3 confirmations",
            registered_addresses=registered,
            policy_engine_pid=policy.pid,
            approver_devices=[
                {"device": d.name, "checks_destination": d in checking.values(), "pid": d.pid}
                for d in (*blind.values(), *checking.values())
            ],
            coordinator_pid=os.getpid(),
            books=books(rpc, output_key, ledger, origins),
        )

        def reorganise(deposit: str) -> str:
            """Replace the newest block with a longer branch in which ``deposit`` pays mallory."""
            rpc.call("invalidateblock", rpc.call("getbestblockhash"))
            back = _replace_with_payment_to_self(rpc, wallets["mallory"], deposit)
            rpc.call("generatetoaddress", 2, mine_to)
            return back

        report("reorg_weak", "running", credit_rule="1 confirmation")
        deposit = wallets["mallory"].call("sendtoaddress", address, "0.50")
        rpc.call("generatetoaddress", 1, mine_to)
        seen = _confirmations(rpc, deposit)
        ledger["mallory"] += Decimal("0.50")  # credited at one confirmation
        back = reorganise(deposit)
        after = books(rpc, output_key, ledger, origins)
        report(
            "reorg_weak",
            "done",
            credit_rule="1 confirmation",
            deposit=f"0.50 BTC in {deposit}",
            confirmations_when_credited=seen,
            credited_to_mallory="0.50 BTC",
            reorganisation="the deposit's block replaced by a longer branch",
            deposit_confirmations_now=_confirmations(rpc, deposit) or 0,
            paid_back_to_mallory_in=back,
            shortfall=f"{after['owed']} owed, {after['held']} held",
            books=after,
        )

        def snapshot(label: str) -> tuple[Decimal, str]:
            """Take, sign and publish a proof-of-reserves snapshot; return its ratio and file."""
            tree = MerkleSumTree(ledger)
            assets = bitcoin.to_btc(sum(u.amount for u in chain.custody_utxos(rpc, output_key)))
            _, head = policy.audit()
            taken = Snapshot(
                taken_at=_now(),
                block_height=rpc.call("getblockcount"),
                block_hash=rpc.call("getbestblockhash"),
                liabilities_root=tree.root.hash.hex(),
                liabilities=tree.root.total,
                clients=len(ledger),
                assets=assets,
                custody_output_key=output_key.hex(),
                audit_head=head,
            )
            token = policy.authorise_attestation(taken.statement())
            message = taken.attestation_message()
            signature = cluster.sign(message, SIGNERS, token.to_bytes(), taproot=True)
            if not schnorr.verify(message, output_key, signature):
                raise RuntimeError("proof-of-control signature does not verify")
            path = publish(taken, signature, workdir / "reserves" / label)
            return taken.reserve_ratio, os.path.relpath(path)

        def pay(
            ins: SettlementInstruction,
            devices: dict[str, ApproverDevice],
            client: str | None = None,
        ) -> tuple[str, int]:
            """Build, check, approve, authorise, sign, broadcast and confirm one payment for
            ``client``; return its txid and fee in satoshis."""
            amount = bitcoin.to_sats(ins.amount)
            destination = chain.script_pubkey(rpc, ins.destination)
            stx = transfer.build(chain.custody_utxos(rpc, output_key), amount, destination, script)
            transfer.check_matches(stx, amount, destination, script, FEE_CAP_SATS)
            approvals = [devices[n].approve(ins, client) for n in ("bob", "carol")]
            token = policy.authorise(ins, approvals, stx.sighash())
            signature = cluster.sign(stx.sighash(), SIGNERS, token.to_bytes(), taproot=True)
            if not schnorr.verify(stx.sighash(), output_key, signature):
                raise RuntimeError("aggregated signature does not verify")
            txid: str = rpc.call("sendrawtransaction", stx.finalize(signature))
            rpc.call("generatetoaddress", 1, mine_to)
            if len(stx.tx.outputs) > 1:
                origins[f"{txid}:1"] = f"change from {ins.instruction_id}"
            return txid, stx.fee

        report("borrow", "running")
        hole = books(rpc, output_key, ledger, origins)
        loan = miner.call("sendtoaddress", address, "0.50")
        rpc.call("generatetoaddress", 1, mine_to)
        origins[f"{loan}:{_custody_vout(rpc, loan, script)}"] = "borrowed from the exchange"
        ratio, path = snapshot("scheduled")
        report(
            "borrow",
            "done",
            before_the_loan=f"{hole['owed']} owed, {hole['held']} held",
            borrowed="0.50 BTC from the exchange, just before the snapshot",
            scheduled_snapshot_ratio=ratio,
            snapshot=path,
            books=books(rpc, output_key, ledger, origins),
        )

        report("unannounced", "running")
        repay = SettlementInstruction(
            "repay-loan", "BTC", Decimal("0.4999969"), lender, "ops-desk", _now()
        )  # 0.50 BTC less the 310-satoshi fee, so the custody coins return to where they were
        repaid, _ = pay(repay, blind)
        ratio, path = snapshot("unannounced")
        report(
            "unannounced",
            "done",
            repaid=f"0.50 BTC to the exchange in {repaid}",
            unannounced_snapshot_ratio=ratio,
            snapshot=path,
            lesson="a snapshot shows one moment; unannounced and frequent snapshots, and the "
            "loan's inflow and outflow on the public chain, expose it",
            books=books(rpc, output_key, ledger, origins),
        )
        ledger["mallory"] -= Decimal("0.50")  # written off, to start the defended case clean

        report("reorg_strong", "running", credit_rule="3 confirmations")
        deposit = wallets["mallory"].call("sendtoaddress", address, "0.50")
        rpc.call("generatetoaddress", 1, mine_to)
        seen = _confirmations(rpc, deposit)
        back = reorganise(deposit)  # before the third confirmation: nothing was credited
        report(
            "reorg_strong",
            "done",
            credit_rule="3 confirmations",
            deposit=f"0.50 BTC in {deposit}",
            confirmations_when_reorganised=seen,
            credited_to_mallory="nothing: still waiting for 3 confirmations",
            deposit_confirmations_now=_confirmations(rpc, deposit) or 0,
            paid_back_to_mallory_in=back,
            books=books(rpc, output_key, ledger, origins),
        )

        def spoofed() -> SettlementInstruction:
            """gamma-treasury's withdrawal, with alpha-capital's address put in by the builder."""
            return SettlementInstruction(
                f"withdraw-gamma-{time.monotonic_ns()}",
                "BTC",
                Decimal("0.40"),
                registered["alpha-capital"],
                "ops-desk",
                _now(),
            )

        report("blind", "running")
        ins = spoofed()
        txid, fee = pay(ins, blind, "gamma-treasury")
        ledger["gamma-treasury"] -= ins.amount + bitcoin.to_btc(fee)
        report(
            "blind",
            "done",
            request="gamma-treasury withdraws 0.40 BTC",
            destination_put_in="alpha-capital's registered address",
            whitelist="passed: the address is registered, though to another client",
            approved_by=["bob", "carol"],
            signers=SIGNERS,
            txid=txid,
            result="0.40 BTC of gamma-treasury's paid to alpha-capital's address",
            books=books(rpc, output_key, ledger, origins),
        )

        report("checked", "running")
        ins = spoofed()
        refusals = []
        for name in ("bob", "carol"):
            try:
                checking[name].approve(ins, "gamma-treasury")
                raise RuntimeError(f"{name}'s checking device approved a misdirected payment")
            except DeviceRefused as refused:
                refusals.append(str(refused))
        report(
            "checked",
            "done",
            request="gamma-treasury withdraws 0.40 BTC",
            destination_put_in="alpha-capital's registered address",
            refusals=refusals,
            nothing_signed="no approval exists, so the policy engine has nothing to authorise",
            books=books(rpc, output_key, ledger, origins),
        )
        final = books(rpc, output_key, ledger, origins)
    except Exception as exc:
        report(current, "failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        parties.close()
        if node is not None:
            node.stop()
        shutil.rmtree(workdir / "node", ignore_errors=True)
    return {"reconciled": final["reconciled"], "owed": final["owed"], "held": final["held"]}
