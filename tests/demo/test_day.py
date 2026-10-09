"""A day at the custodian, run on regtest: every deposit, payment and refusal, and the books equal
to the chain after every step."""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from custody_lab.demo import day
from custody_lab.foundations import schnorr

pytestmark = [
    pytest.mark.regtest,
    pytest.mark.skipif(shutil.which("bitcoind") is None, reason="bitcoind not on PATH"),
]


@pytest.fixture(scope="module")
def the_day(tmp_path_factory: pytest.TempPathFactory) -> tuple[dict[str, Any], dict[str, Any]]:
    """One day, run once for every test: (the summary, each step's done detail)."""
    events: list[Any] = []
    summary = day.run(events.append, tmp_path_factory.mktemp("day"))
    done = {e.step: e.detail for e in events if e.status == "done"}
    assert list(done) == list(day.STEPS)
    return summary, done


def test_only_confirmed_deposits_are_credited(
    the_day: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    _, done = the_day
    status = {d["client"]: d["status"] for d in done["deposits"]["deposits"]}
    assert status["delta-trading"] == "replaced before it confirmed: not credited"
    assert all(
        status[c].startswith("credited") for c in ("alpha-capital", "beta-fund", "gamma-treasury")
    )
    assert done["deposits"]["books"]["ledger"]["delta-trading"] == "0.00 BTC"


def test_the_books_equal_the_chain_after_every_step(
    the_day: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    _, done = the_day
    books = {step: d["books"] for step, d in done.items() if "books" in d}
    moved = {"deposits", "settle", "withdraw_gamma", "withdraw_beta", "refused", "reserves"}
    assert set(books) == {"keys"} | moved  # every step that moves or could move coins
    for step, b in books.items():
        assert b["reconciled"] and b["owed"] == b["held"], step


def test_netting_across_clients_keeps_one_purchase_off_the_chain(
    the_day: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    _, done = the_day
    assert done["net"]["custodian_delivers"] == "0.75 BTC to the exchange"
    assert done["settle"]["pays"] == "0.75 BTC"
    # coins at one address are interchangeable: alpha-capital's delivery spends gamma's deposit
    assert done["settle"]["coin_spent"] == "1.00 BTC, deposit from gamma-treasury"
    assert done["settle"]["books"]["ledger"]["beta-fund"] == "1.95 BTC"


def test_signers_one_and_two_sign_after_signer_three_goes_down(
    the_day: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    _, done = the_day
    assert done["settle"]["signers"] == [1, 3]
    assert done["withdraw_gamma"]["signers"] == [1, 2]
    assert done["withdraw_beta"]["approved_by"] == ["bob"]  # the lower tier needs one approval
    assert done["reserves"]["proof_of_control"] == "signed by signers 1 and 2"


def test_each_refusal_comes_from_the_layer_that_owns_the_rule(
    the_day: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    _, done = the_day
    refused = done["refused"]["requests"]
    assert refused["withdraw-delta-1"]["refused_by"] == "the ledger"
    assert refused["withdraw-delta-1"]["reason"] == "delta-trading holds 0.00 BTC"
    assert refused["withdraw-alpha-1"]["reason"].endswith("is not whitelisted")
    assert refused["withdraw-alpha-2"]["reason"] == (
        "denied: velocity limit 1.50 BTC per 24 hours; 1.40 BTC already authorised"
    )


def test_the_day_ends_with_a_signed_snapshot_equal_to_the_books(
    the_day: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    summary, done = the_day
    assert done["reserves"]["liabilities"] == done["reserves"]["assets"] == "3.0999907 BTC"
    document = json.loads(Path(summary["snapshot"]).read_text())
    attestation = document["attestation"]
    assert schnorr.verify(
        bytes.fromhex(attestation["message"]),
        bytes.fromhex(document["custody_output_key"]),
        bytes.fromhex(attestation["bip340_signature"]),
    )
