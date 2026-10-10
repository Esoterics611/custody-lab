"""The audit log through two settlements, and a forger's copy of it checked against the heads the
signed snapshots anchored. No chain."""

from typing import Any

import pytest

from custody_lab.demo import audit_trail
from custody_lab.foundations.hashing import sha256
from custody_lab.policy.audit import GENESIS
from custody_lab.policy.model import canonical_json

Done = dict[str, dict[str, Any]]
EVENTS = [
    "evaluated",
    "evaluated",
    "authorised",
    "evaluated",
    "attestation_authorised",
    "evaluated",
    "authorised",
    "attestation_authorised",
]


@pytest.fixture(scope="module")
def run() -> tuple[Done, dict[str, Any]]:
    events: list[Any] = []
    summary = audit_trail.run(events.append)
    done = {e.step: e.detail for e in events if e.status == "done"}
    assert list(done) == list(audit_trail.STEPS)
    return done, summary


def _entries(done: Done) -> list[dict[str, Any]]:
    return [e for step in done.values() for e in step.get("entries", [])]


def test_each_entry_links_to_the_one_before_and_hashes_as_shown(
    run: tuple[Done, dict[str, Any]],
) -> None:
    done, summary = run
    entries = _entries(done)
    assert [e["event"] for e in entries] == EVENTS
    assert [e["seq"] for e in entries] == list(range(summary["entries"]))
    prev = GENESIS
    for e in entries:
        assert e["prev_hash"] == prev
        body = {k: v for k, v in e.items() if k not in ("hash", "about")}
        assert sha256(canonical_json(body)).hex() == e["hash"]  # the dashboard shows what is hashed
        prev = e["hash"]
    assert done["snapshot_2"]["head"] == entries[-1]["hash"]
    statuses = [e["payload"].get("status") for e in entries if e["event"] == "evaluated"]
    assert statuses == ["pending", "approved", "denied", "approved"]


def test_each_snapshot_anchors_the_head_before_its_own_attestation(
    run: tuple[Done, dict[str, Any]],
) -> None:
    done, summary = run
    entries = _entries(done)
    assert summary["anchored_entries"] == [3, 6]
    for step, anchored in (("snapshot_1", 3), ("snapshot_2", 6)):
        assert done[step]["anchored_entry"] == anchored
        assert done[step]["audit_head"] == entries[anchored]["hash"]
        assert done[step]["signature_valid"] is True
        assert [e["seq"] for e in done[step]["entries"]] == [anchored + 1]


def test_an_edit_breaks_the_chain_at_the_entry_and_a_new_hash_at_the_next_link(
    run: tuple[Done, dict[str, Any]],
) -> None:
    done, _ = run
    last = len(EVENTS) - 1
    assert done["edited"]["untouched"] == "verifies"  # the copy as exported, before any edit
    for row in done["edited"]["forgeries"]:
        assert row["breaks_at"] == row["entry"]
        assert row["reason"].endswith("content does not match its hash")
        assert row["recomputed_hash"] != row["stored_hash"]
    for row in done["relinked"]["forgeries"]:
        if row["entry"] == last:
            assert row["breaks_at"] is None  # nothing after it links to the old hash
        else:
            assert row["breaks_at"] == row["entry"] + 1
            assert row["reason"].endswith("sequence or link broken")
    authorised = done["edited"]["forgeries"][2]
    assert (authorised["field"], authorised["before"], authorised["after"]) == (
        "amount",
        "0.85 BTC",
        "0.085 BTC",
    )


def test_a_rehashed_copy_verifies_and_only_an_anchor_at_or_after_the_edit_exposes_it(
    run: tuple[Done, dict[str, Any]],
) -> None:
    done, summary = run
    genuine = {e["seq"]: e["hash"] for e in _entries(done)}
    for row in done["rehashed"]["forgeries"]:
        assert row["reason"] == "verifies"
        rewritten = row["entries"]
        assert [e["seq"] for e in rewritten] == list(range(row["entry"], len(EVENTS)))
        assert all(e["hash"] != genuine[e["seq"]] for e in rewritten)
        assert rewritten[0]["prev_hash"] == (genuine[row["entry"] - 1] if row["entry"] else GENESIS)
    assert summary["exposed_by"] == {
        "0": 1, "1": 1, "2": 1, "3": 1, "4": 2, "5": 2, "6": 2, "7": None,
    }  # fmt: skip
    for row in done["anchored"]["forgeries"]:
        for snapshot in row["snapshots"]:
            kept = row["entry"] > snapshot["anchored_entry"]
            assert (snapshot["found_at"] == snapshot["anchored_entry"]) is kept
            assert (snapshot["copy_hash"] == snapshot["anchored_head"]) is kept


def test_moving_a_snapshots_head_breaks_its_signature(run: tuple[Done, dict[str, Any]]) -> None:
    done, summary = run
    assert summary["moved_heads_verify"] == [False, False]
    shown = done["anchored"]["shown"]
    forged = done["anchored"]["forgeries"][shown]["snapshots"]
    assert [m["head"] for m in done["anchored"]["moved_heads"]] == [f["copy_hash"] for f in forged]
