"""The demo's policy engine and approvers, each in an operating-system process of its own.

The design (chapter 9) keeps the coordinator, the policy engine and the approvers apart, so that
whoever controls one cannot act as another. Before this module the demo ran all three inside the
server process, which could therefore approve and authorise any payment (manual/attack-vectors.md,
Finding 2). Now:

- ``PolicyService`` runs the policy engine in its own process. Its authority key is generated inside
  that process and never leaves it; the coordinator receives authorisations and the audit log,
  nothing else.
- ``ApproverDevice`` runs one approver's Ed25519 key in its own process, standing in for the
  approver's own device. It signs the instruction it is given and returns the approval.

Every process still runs on one computer, so an administrator of that computer reaches them all
(attack-vectors.md, vector 1.5). What the separation removes is the single process whose compromise
authorised anything.
"""

from __future__ import annotations

import multiprocessing as mp
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from multiprocessing.connection import Connection
from types import TracebackType
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from custody_lab.policy.audit import AuditEntry, AuditLog
from custody_lab.policy.authorisation import Authorisation, AuthorityKey
from custody_lab.policy.engine import AssetPolicy, Policy, PolicyDenied, PolicyEngine
from custody_lab.policy.model import Approval, SettlementInstruction


def _now() -> datetime:
    return datetime.now(UTC)


def _serve(factory: Callable[..., Any], args: tuple[Any, ...], conn: Connection) -> None:
    """Run ``factory(*args)`` in this process and answer method calls until told to stop."""
    party = factory(*args)
    while (request := conn.recv()) is not None:
        method, call_args = request
        try:
            conn.send(("ok", getattr(party, method)(*call_args)))
        except PolicyDenied as denied:  # its decision, not its message, must reach the caller
            conn.send(("denied", denied.decision))
        except Exception as exc:  # report to the caller instead of dying silently
            conn.send(("error", repr(exc)))


class _Process:
    """An object living in a spawned process, reached through a pipe."""

    def __init__(self, name: str, factory: Callable[..., Any], *args: Any) -> None:
        ctx = mp.get_context("spawn")
        self._conn, child = ctx.Pipe()
        self._proc = ctx.Process(target=_serve, args=(factory, args, child), name=name)
        self._proc.start()

    @property
    def pid(self) -> int | None:
        return self._proc.pid

    def call(self, method: str, *args: Any) -> Any:
        self._conn.send((method, args))
        kind, value = self._conn.recv()
        if kind == "denied":
            raise PolicyDenied(value)
        if kind == "error":
            raise RuntimeError(value)
        return value

    def close(self) -> None:
        if self._proc.is_alive():
            self._conn.send(None)
            self._proc.join()


@dataclass(frozen=True)
class PolicySpec:
    """The policy as plain data, so that it can be sent to another process."""

    assets: Mapping[str, AssetPolicy]
    approvers: Mapping[str, bytes]  # raw Ed25519 public keys


class _EngineInProcess:
    def __init__(self, spec: PolicySpec) -> None:
        approvers = {n: Ed25519PublicKey.from_public_bytes(k) for n, k in spec.approvers.items()}
        policy = Policy(dict(spec.assets), approvers)
        self.engine = PolicyEngine(policy, AuthorityKey.generate(), AuditLog(_now), _now)

    def public_key(self) -> bytes:
        return self.engine.authority_public_key

    def authorise(
        self, ins: SettlementInstruction, approvals: list[Approval], message: bytes
    ) -> Authorisation:
        return self.engine.authorise(ins, approvals, message)

    def authorise_attestation(self, statement: bytes) -> Authorisation:
        return self.engine.authorise_attestation(statement)

    def audit(self) -> tuple[list[AuditEntry], str]:
        return list(self.engine.audit.entries), self.engine.audit.head


class PolicyService:
    """The policy engine in its own process; the authority key never leaves it."""

    def __init__(self, spec: PolicySpec) -> None:
        self._process = _Process("policy-engine", _EngineInProcess, spec)
        self.authority_public_key: bytes = self._process.call("public_key")

    @property
    def pid(self) -> int | None:
        return self._process.pid

    def authorise(
        self, ins: SettlementInstruction, approvals: list[Approval], message: bytes
    ) -> Authorisation:
        """As ``PolicyEngine.authorise``; raises ``PolicyDenied`` with the engine's decision."""
        token: Authorisation = self._process.call("authorise", ins, approvals, message)
        return token

    def authorise_attestation(self, statement: bytes) -> Authorisation:
        token: Authorisation = self._process.call("authorise_attestation", statement)
        return token

    def audit(self) -> tuple[list[AuditEntry], str]:
        """The engine's audit entries and their head, as read from its process."""
        entries, head = self._process.call("audit")
        return entries, head

    def close(self) -> None:
        self._process.close()

    def __enter__(self) -> PolicyService:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class _DeviceInProcess:
    def __init__(self, name: str) -> None:
        self.name = name
        self._key = Ed25519PrivateKey.generate()  # never leaves this process

    def public_key(self) -> bytes:
        return self._key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )

    def approve(self, ins: SettlementInstruction) -> Approval:
        return Approval.create(ins, self.name, self._key)


class ApproverDevice:
    """One approver's key in its own process, standing in for the approver's own device."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._process = _Process(f"approver-{name}", _DeviceInProcess, name)
        self.public_key: bytes = self._process.call("public_key")

    @property
    def pid(self) -> int | None:
        return self._process.pid

    def approve(self, ins: SettlementInstruction) -> Approval:
        approval: Approval = self._process.call("approve", ins)
        return approval

    def close(self) -> None:
        self._process.close()

    def __enter__(self) -> ApproverDevice:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
