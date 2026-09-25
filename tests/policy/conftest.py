from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custody_lab.policy.audit import AuditLog
from custody_lab.policy.authorisation import AuthorityKey
from custody_lab.policy.engine import AssetPolicy, Policy, PolicyEngine, Tier
from custody_lab.policy.model import SettlementInstruction

TREASURY, EXCHANGE, UNKNOWN = "bcrt1q-treasury", "bcrt1p-exchange", "bcrt1q-stranger"


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 24, 9, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, delta: timedelta) -> None:
        self.now += delta


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def keys() -> dict[str, Ed25519PrivateKey]:
    return {name: Ed25519PrivateKey.generate() for name in ("alice", "bob", "carol", "dave")}


@pytest.fixture
def engine(clock: FakeClock, keys: dict[str, Ed25519PrivateKey]) -> PolicyEngine:
    btc = AssetPolicy(
        tiers=(Tier(Decimal("1"), quorum=1), Tier(Decimal("10"), quorum=2)),
        whitelist=frozenset({TREASURY, EXCHANGE}),
        velocity_window=timedelta(hours=24),
        velocity_limit=Decimal("15"),
    )
    approvers = {n: k.public_key() for n, k in keys.items() if n != "dave"}  # dave: not an approver
    return PolicyEngine(
        Policy({"BTC": btc}, approvers), AuthorityKey.generate(), AuditLog(clock), clock
    )


Make = Callable[..., SettlementInstruction]


@pytest.fixture
def make(clock: FakeClock) -> Make:
    counter = iter(range(1, 10_000))

    def _make(
        amount: str | Decimal = "0.5",
        asset: str = "BTC",
        destination: str = TREASURY,
        initiator: str = "alice",
    ) -> SettlementInstruction:
        return SettlementInstruction(
            f"ins-{next(counter)}", asset, Decimal(amount), destination, initiator, clock()
        )

    return _make
