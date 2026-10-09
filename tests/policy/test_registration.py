"""Registering a withdrawal address: approved like the largest payment, payable only after a delay,
and recorded in the audit log."""

from datetime import timedelta
from decimal import Decimal

import pytest
from conftest import FakeClock, Make
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custody_lab.policy.engine import PolicyDenied, PolicyEngine
from custody_lab.policy.model import AddressRegistration, Approval

NEW = "bcrt1q-new-client-address"
MESSAGE = b"\x07" * 32


def _registration(clock: FakeClock, initiator: str = "alice") -> AddressRegistration:
    return AddressRegistration("reg-1", "BTC", "gamma-treasury", NEW, initiator, clock())


def _approve(
    item: AddressRegistration, keys: dict[str, Ed25519PrivateKey], *names: str
) -> list[Approval]:
    return [Approval.create(item, n, keys[n]) for n in names]


def test_a_registration_needs_the_quorum_of_the_highest_tier(
    engine: PolicyEngine, clock: FakeClock, keys: dict[str, Ed25519PrivateKey]
) -> None:
    reg = _registration(clock)
    with pytest.raises(PolicyDenied, match="1 of 2 required approvals"):
        engine.register(reg, _approve(reg, keys, "bob"))
    with pytest.raises(PolicyDenied, match="1 of 2 required approvals"):  # four-eyes
        engine.register(reg, _approve(reg, keys, "alice", "bob"))


def test_a_registered_address_is_payable_only_after_the_delay(
    engine: PolicyEngine,
    clock: FakeClock,
    keys: dict[str, Ed25519PrivateKey],
    make: Make,
) -> None:
    reg = _registration(clock)
    effective = engine.register(reg, _approve(reg, keys, "bob", "carol"))
    assert effective == clock() + timedelta(hours=24)

    early = make(amount=Decimal("0.5"), destination=NEW)
    with pytest.raises(PolicyDenied, match="payable only from"):
        engine.authorise(early, [Approval.create(early, "bob", keys["bob"])], MESSAGE)

    clock.advance(timedelta(hours=24))
    later = make(amount=Decimal("0.5"), destination=NEW)
    token = engine.authorise(later, [Approval.create(later, "bob", keys["bob"])], MESSAGE)
    assert token.message == MESSAGE


def test_an_approval_of_a_payment_never_counts_for_a_registration(
    engine: PolicyEngine, clock: FakeClock, keys: dict[str, Ed25519PrivateKey], make: Make
) -> None:
    reg = _registration(clock)
    payment = make()
    reused = [Approval.create(payment, n, keys[n]) for n in ("bob", "carol")]
    assert payment.digest() != reg.digest()
    with pytest.raises(PolicyDenied, match="0 of 2 required approvals"):
        engine.register(reg, reused)


def test_a_registration_is_recorded_and_cannot_be_repeated(
    engine: PolicyEngine, clock: FakeClock, keys: dict[str, Ed25519PrivateKey]
) -> None:
    reg = _registration(clock)
    engine.register(reg, _approve(reg, keys, "bob", "carol"))

    registered = [e for e in engine.audit.entries if e.event == "registered"]
    assert len(registered) == 1 and registered[0].payload["address"] == NEW
    with pytest.raises(PolicyDenied, match="already registered"):
        engine.register(reg, _approve(reg, keys, "bob", "carol"))
