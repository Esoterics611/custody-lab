"""The key ceremonies: a share stolen before a refresh cannot combine with one stolen after it,
and a lost share is rebuilt by two helpers. No chain is needed."""

from typing import Any

import pytest

from custody_lab.demo import ceremonies


@pytest.fixture(scope="module")
def done() -> dict[str, dict[str, Any]]:
    events: list[Any] = []
    ceremonies.run(events.append)
    finished = {e.step: e.detail for e in events if e.status == "done"}
    assert list(finished) == list(ceremonies.STEPS)
    return finished


def test_one_share_cannot_sign_and_two_of_one_period_can(done: dict[str, dict[str, Any]]) -> None:
    assert done["one_share"]["alone"] == "IncorrectNumberOfCommitments"
    assert done["same_period"]["signature_valid"] is True


def test_a_refresh_keeps_the_key_and_splits_the_periods(done: dict[str, dict[str, Any]]) -> None:
    assert done["refresh"]["group_key_unchanged"] and done["refresh"]["output_key_unchanged"]
    assert done["mixed"]["with_new_public_key_package"].startswith(
        "the share from participant 1 does not fit"
    )
    assert done["mixed"]["with_old_public_key_package"].startswith(
        "the share from participant 3 does not fit"
    )
    assert done["fresh"]["signature_valid"] is True


def test_a_lost_share_is_repaired_and_signs_again(done: dict[str, dict[str, Any]]) -> None:
    assert "no key share" in done["lost"]["signer_2"]
    assert done["repair"]["public_key_package_unchanged"] is True
    assert done["repaired"]["signature_valid"] is True
    assert done["repaired"]["under_the_same_output_key"] == done["keys"]["output_key"]
