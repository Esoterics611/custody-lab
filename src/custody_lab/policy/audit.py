"""Hash-chained, append-only audit log.

Each entry commits to the previous entry's hash, so changing, removing or reordering any entry
breaks every hash after it. That makes the log tamper-evident, not tamper-proof. An attacker
who can rewrite the whole file can recompute the chain, and dropping entries from the end leaves
a valid shorter chain. Both are caught only by comparing the head hash with a copy published
elsewhere (anchoring).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from custody_lab.foundations.hashing import sha256
from custody_lab.policy.model import canonical_json

GENESIS = "0" * 64
Clock = Callable[[], datetime]


class AuditChainBroken(Exception):
    pass


@dataclass(frozen=True)
class AuditEntry:
    seq: int
    time: datetime
    event: str
    payload: dict[str, Any]
    prev_hash: str
    hash: str

    def body(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "time": self.time,
            "event": self.event,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
        }


class AuditLog:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._entries: list[AuditEntry] = []

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        return tuple(self._entries)

    @property
    def head(self) -> str:
        """Hash of the newest entry: the value to publish for anchoring."""
        return self._entries[-1].hash if self._entries else GENESIS

    def append(self, event: str, payload: dict[str, Any]) -> AuditEntry:
        seq, time, prev = len(self._entries), self._clock(), self.head
        body = {"seq": seq, "time": time, "event": event, "payload": payload, "prev_hash": prev}
        entry = AuditEntry(seq, time, event, payload, prev, sha256(canonical_json(body)).hex())
        self._entries.append(entry)
        return entry


def verify_chain(entries: Sequence[AuditEntry]) -> None:
    """Recompute every hash and link; raise at the first entry that does not match."""
    prev = GENESIS
    for expected_seq, entry in enumerate(entries):
        if entry.seq != expected_seq or entry.prev_hash != prev:
            raise AuditChainBroken(f"entry {expected_seq}: sequence or link broken")
        if sha256(canonical_json(entry.body())).hex() != entry.hash:
            raise AuditChainBroken(f"entry {expected_seq}: content does not match its hash")
        prev = entry.hash
