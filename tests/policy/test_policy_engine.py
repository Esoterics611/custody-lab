from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from conftest import EXCHANGE, UNKNOWN, FakeClock, Make
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from custody_lab.policy.audit import verify_chain
from custody_lab.policy.engine import PolicyDenied, PolicyEngine, Status
from custody_lab.policy.model import Approval, SettlementInstruction

Keys = dict[str, Ed25519PrivateKey]
MSG = b"\x01" * 32


def approve(ins: SettlementInstruction, keys: Keys, *names: str) -> list[Approval]:
    return [Approval.create(ins, n, keys[n]) for n in names]


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.text(min_size=1).filter(lambda a: a != "BTC"))
def test_unknown_asset_is_denied(engine: PolicyEngine, make: Make, keys: Keys, asset: str) -> None:
    ins = make(asset=asset)
    assert engine.evaluate(ins, approve(ins, keys, "bob", "carol")).status is Status.DENIED


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity"])
def test_non_positive_or_non_finite_amount_is_denied(
    engine: PolicyEngine, make: Make, amount: str
) -> None:
    assert engine.evaluate(make(amount=amount), []).status is Status.DENIED


def test_above_top_tier_is_denied_even_with_every_approval(
    engine: PolicyEngine, make: Make, keys: Keys
) -> None:
    ins = make(amount="10.00000001")
    decision = engine.evaluate(ins, approve(ins, keys, "bob", "carol"))
    assert decision.status is Status.DENIED and "highest tier" in decision.reason


def test_destination_must_be_whitelisted(engine: PolicyEngine, make: Make, keys: Keys) -> None:
    ins = make(destination=UNKNOWN)
    decision = engine.evaluate(ins, approve(ins, keys, "bob", "carol"))
    assert decision.status is Status.DENIED and "not whitelisted" in decision.reason


def test_quorum_scales_with_amount(engine: PolicyEngine, make: Make, keys: Keys) -> None:
    small, large = make(amount="0.5"), make(amount="5", destination=EXCHANGE)
    assert engine.evaluate(small, approve(small, keys, "bob")).status is Status.APPROVED
    assert engine.evaluate(large, approve(large, keys, "bob")).status is Status.PENDING
    assert engine.evaluate(large, approve(large, keys, "bob", "carol")).status is Status.APPROVED


def test_initiator_cannot_approve_own_instruction(
    engine: PolicyEngine, make: Make, keys: Keys
) -> None:
    ins = make(amount="0.5", initiator="bob")
    assert engine.evaluate(ins, approve(ins, keys, "bob")).status is Status.PENDING


def test_invalid_approvals_are_not_counted(engine: PolicyEngine, make: Make, keys: Keys) -> None:
    ins, other = make(amount="5"), make(amount="6")
    bogus = [
        Approval.create(ins, "dave", keys["dave"]),  # not an approver
        Approval.create(other, "bob", keys["bob"]),  # signed a different instruction
        Approval(ins.digest(), "carol", keys["bob"].sign(b"x")),  # forged signature
        *approve(ins, keys, "bob", "bob"),  # duplicates count once
    ]
    decision = engine.evaluate(ins, bogus)
    assert decision.status is Status.PENDING and decision.approvers == ("bob",)


def test_velocity_limit_rolls_over(
    engine: PolicyEngine, make: Make, keys: Keys, clock: FakeClock
) -> None:
    for amount in ("10", "5"):
        ins = make(amount=amount)
        engine.authorise(ins, approve(ins, keys, "bob", "carol"), MSG)
    blocked = make(amount="0.1")
    with pytest.raises(PolicyDenied, match="velocity"):
        engine.authorise(blocked, approve(blocked, keys, "bob"), MSG)
    clock.advance(timedelta(hours=24, seconds=1))
    later = make(amount="0.1")
    engine.authorise(later, approve(later, keys, "bob"), MSG)


def test_an_instruction_is_authorised_once(engine: PolicyEngine, make: Make, keys: Keys) -> None:
    ins = make()
    engine.authorise(ins, approve(ins, keys, "bob"), MSG)
    with pytest.raises(PolicyDenied, match="already authorised"):
        engine.authorise(ins, approve(ins, keys, "bob"), MSG)


@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=12 * 60),
            st.decimals(min_value=Decimal("0.01"), max_value=Decimal("10"), places=2),
        ),
        max_size=25,
    )
)
def test_authorised_volume_never_exceeds_the_limit_in_any_window(
    engine: PolicyEngine,
    make: Make,
    keys: Keys,
    clock: FakeClock,
    steps: list[tuple[int, Decimal]],
) -> None:
    issued: list[tuple[datetime, Decimal]] = []
    for minutes, amount in steps:
        clock.advance(timedelta(minutes=minutes))
        ins = make(amount=amount)
        try:
            engine.authorise(ins, approve(ins, keys, "bob", "carol"), MSG)
            issued.append((clock(), amount))
        except PolicyDenied:
            pass
    for t, _ in issued:
        window = [a for s, a in issued if t - timedelta(hours=24) < s <= t]
        assert sum(window, Decimal(0)) <= Decimal("15")


def test_every_decision_is_in_a_valid_audit_chain(
    engine: PolicyEngine, make: Make, keys: Keys
) -> None:
    ins = make()
    engine.evaluate(ins, [])
    engine.authorise(ins, approve(ins, keys, "bob"), MSG)
    events = [e.event for e in engine.audit.entries]
    assert events == ["evaluated", "evaluated", "authorised"]
    verify_chain(engine.audit.entries)
