from dataclasses import replace

import pytest
from conftest import FakeClock

from custody_lab.policy.audit import AuditChainBroken, AuditLog, verify_chain


def _log(clock: FakeClock) -> AuditLog:
    log = AuditLog(clock)
    for i in range(4):
        log.append("evaluated", {"instruction_id": f"ins-{i}", "status": "pending"})
    return log


def test_untouched_chain_verifies(clock: FakeClock) -> None:
    verify_chain(_log(clock).entries)


def test_edited_entry_is_detected(clock: FakeClock) -> None:
    entries = list(_log(clock).entries)
    entries[1] = replace(entries[1], payload={"instruction_id": "ins-1", "status": "approved"})
    with pytest.raises(AuditChainBroken, match="entry 1: content does not match") as broken:
        verify_chain(entries)
    assert broken.value.entry == 1


def test_deleted_or_reordered_entries_are_detected(clock: FakeClock) -> None:
    entries = list(_log(clock).entries)
    with pytest.raises(AuditChainBroken):
        verify_chain(entries[:1] + entries[2:])
    with pytest.raises(AuditChainBroken):
        verify_chain([entries[0], entries[2], entries[1], entries[3]])


def test_truncating_the_tail_is_only_caught_by_the_anchored_head(clock: FakeClock) -> None:
    log = _log(clock)
    anchored_head = log.head  # published elsewhere, e.g. with each proof-of-reserves snapshot
    truncated = log.entries[:2]
    verify_chain(truncated)  # still a valid chain
    assert truncated[-1].hash != anchored_head
