"""Clocks: signers whose clocks are set back accept an expired authorisation; signers on the time
authority's signed time refuse it, and refuse a signed time for another nonce. No chain."""

from typing import Any

import pytest

from custody_lab.demo import clocks


@pytest.fixture(scope="module")
def run() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    events: list[Any] = []
    summary = clocks.run(events.append)
    finished = {e.step: e.detail for e in events if e.status == "done"}
    assert list(finished) == list(clocks.STEPS)
    return finished, summary


def test_only_the_timely_and_the_clock_set_back_cases_sign(
    run: tuple[dict[str, dict[str, Any]], dict[str, Any]],
) -> None:
    done, summary = run
    assert summary == {"signed": ["in_time", "both_clocks"]}
    assert done["in_time"]["signature_valid"] and done["both_clocks"]["signature_valid"]
    assert done["in_time"]["lifetime"]["true_s"] < 5


def test_a_late_authorisation_is_refused_until_both_clocks_are_set_back(
    run: tuple[dict[str, dict[str, Any]], dict[str, Any]],
) -> None:
    done, _ = run
    assert done["too_late"]["refusal"].count("expired at") == 2
    refusal = done["one_clock"]["refusal"]
    assert refusal.startswith("signer 3: expired at") and "signer 1" not in refusal
    late = done["both_clocks"]["lifetime"]
    assert late["true_s"] >= 300 and all(r < 60 for r in late["readings_s"].values())


def test_signed_time_ignores_the_clocks_and_binds_the_nonce(
    run: tuple[dict[str, dict[str, Any]], dict[str, Any]],
) -> None:
    done, _ = run
    assert done["attested"]["refusal"].count("expired at") == 2
    assert all(r >= 300 for r in done["attested"]["lifetime"]["readings_s"].values())
    assert done["replayed"]["refusal"].count("answers another request") == 2
    assert done["replayed"]["without_the_nonce_check"].endswith("it would be accepted")
