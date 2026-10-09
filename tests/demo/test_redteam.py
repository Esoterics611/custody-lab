"""Red team on regtest: a reorganised deposit leaves a hole only under a one-confirmation rule, and
a misdirected withdrawal passes blind devices and is refused by checking ones."""

import shutil
from typing import Any

import pytest

from custody_lab.demo import redteam

pytestmark = [
    pytest.mark.regtest,
    pytest.mark.skipif(shutil.which("bitcoind") is None, reason="bitcoind not on PATH"),
]


@pytest.fixture(scope="module")
def done(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    events: list[Any] = []
    redteam.run(events.append, tmp_path_factory.mktemp("redteam"))
    finished = {e.step: e.detail for e in events if e.status == "done"}
    assert list(finished) == list(redteam.STEPS)
    return finished


def test_one_confirmation_credits_a_deposit_that_is_then_reorganised_away(
    done: dict[str, dict[str, Any]],
) -> None:
    weak = done["reorg_weak"]
    assert weak["confirmations_when_credited"] == 1 and weak["deposit_confirmations_now"] == 0
    assert weak["books"]["reconciled"] is False
    assert weak["shortfall"] == "1.50 BTC owed, 1.00 BTC held"


def test_three_confirmations_credit_nothing_before_the_reorganisation(
    done: dict[str, dict[str, Any]],
) -> None:
    strong = done["reorg_strong"]
    assert strong["credited_to_mallory"].startswith("nothing")
    assert strong["deposit_confirmations_now"] == 0 and strong["books"]["reconciled"] is True


def test_blind_devices_approve_a_misdirected_payment_and_the_books_still_agree(
    done: dict[str, dict[str, Any]],
) -> None:
    blind = done["blind"]
    assert blind["approved_by"] == ["bob", "carol"]
    # the coins went to the wrong client, and reconciliation cannot see it
    assert blind["books"]["reconciled"] is True


def test_checking_devices_refuse_the_same_payment(done: dict[str, dict[str, Any]]) -> None:
    refusals = done["checked"]["refusals"]
    assert len(refusals) == 2
    assert all("alpha-capital's registered address, not gamma-treasury's" in r for r in refusals)
