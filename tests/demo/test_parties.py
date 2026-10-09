"""The policy engine and the approvers run in processes of their own, so the coordinator holds none
of their keys (manual/attack-vectors.md, Finding 2)."""

import gc
import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from custody_lab.demo.parties import ApproverDevice, PolicyService, PolicySpec, TimeService
from custody_lab.policy import signed_time
from custody_lab.policy.authorisation import AuthorityKey
from custody_lab.policy.engine import AssetPolicy, PolicyDenied, Tier
from custody_lab.policy.model import SettlementInstruction

EXCHANGE = "exchange-settlement-address"


@pytest.fixture(scope="module")
def parties() -> Iterator[tuple[PolicyService, dict[str, ApproverDevice]]]:
    with ApproverDevice("bob") as bob, ApproverDevice("carol") as carol:
        btc = AssetPolicy(
            (Tier(Decimal("0.1"), 1), Tier(Decimal("10"), 2)),
            frozenset({EXCHANGE}),
            timedelta(hours=24),
            Decimal("20"),
        )
        spec = PolicySpec({"BTC": btc}, {"bob": bob.public_key, "carol": carol.public_key})
        with PolicyService(spec) as policy:
            yield policy, {"bob": bob, "carol": carol}


def _instruction(amount: str = "0.85") -> SettlementInstruction:
    return SettlementInstruction(
        f"i-{amount}", "BTC", Decimal(amount), EXCHANGE, "ops-desk", datetime.now(UTC)
    )


def test_each_party_is_a_process_other_than_the_coordinator(
    parties: tuple[PolicyService, dict[str, ApproverDevice]],
) -> None:
    policy, devices = parties
    pids = {policy.pid, *(d.pid for d in devices.values())}
    assert len(pids) == 3 and os.getpid() not in pids


def test_the_coordinator_holds_no_authority_key(
    parties: tuple[PolicyService, dict[str, ApproverDevice]],
) -> None:
    policy, devices = parties
    ins = _instruction()
    token = policy.authorise(
        ins, [devices["bob"].approve(ins), devices["carol"].approve(ins)], b"\x01" * 32
    )

    assert token.message == b"\x01" * 32
    here = [o for o in gc.get_objects() if isinstance(o, AuthorityKey)]  # other tests make some
    assert all(k.public_bytes() != policy.authority_public_key for k in here)


def test_a_refusal_crosses_the_process_boundary_with_its_decision(
    parties: tuple[PolicyService, dict[str, ApproverDevice]],
) -> None:
    policy, devices = parties
    ins = _instruction("0.90")

    with pytest.raises(PolicyDenied) as denied:
        policy.authorise(ins, [devices["bob"].approve(ins)], b"\x02" * 32)

    assert denied.value.decision.reason == "1 of 2 required approvals"
    entries, head = policy.audit()
    assert entries[-1].payload["status"] == "pending" and head == entries[-1].hash


def test_the_time_authority_signs_the_time_for_a_nonce_in_its_own_process() -> None:
    with TimeService() as service:
        nonce = signed_time.new_nonce()
        signed = signed_time.SignedTime.from_bytes(service.stamp(nonce))
        moment = signed_time.read(signed, service.public_key, nonce)
        assert service.pid not in (None, os.getpid())
        assert abs(moment - datetime.now(UTC)) < timedelta(seconds=5)
