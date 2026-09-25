"""A t-of-n FROST signing cluster with one operating-system process per key share.

This is the demo's signing path, not teaching code. It uses the Zcash Foundation crate
``frost-secp256k1-tr`` through ``custody_frost``, and produces BIP340 signatures.

Each signer process holds its own key package and round-1 nonces and never sends them anywhere.
This process is the coordinator. It relays public DKG packages, collects commitments and
signature shares, and aggregates. It never holds a share, so it cannot sign alone. In the paper's
terms it is semi-trusted: it can deny service, but it learns nothing secret.

Transport is a ``multiprocessing`` pipe per signer. The ``spawn`` start method gives every signer
a fresh interpreter with no memory inherited from the coordinator.

A signer produces a share only against an authorisation from the policy engine (Module 4). The
signer checks four things:
- the token is signed by the configured policy authority;
- it has not expired;
- it authorises exactly the message inside the FROST signing package;
- it has not been used before.

Nonces are burnt before those checks, so a refused request cannot be retried with the same nonces
on a different message.
"""

from __future__ import annotations

import multiprocessing as mp
from collections.abc import Sequence
from datetime import UTC, datetime
from multiprocessing.connection import Connection
from types import TracebackType
from typing import Any

import custody_frost as cf

from custody_lab.policy import authorisation


class _Signer:
    """State held inside one signer process."""

    def __init__(self, identifier: int, authority: bytes) -> None:
        self.identifier = identifier
        self._authority = authority
        self._used_authorisations: set[str] = set()
        self._secret = b""
        self._round1: dict[int, bytes] = {}
        self._key_package = b""
        self._nonces: bytes | None = None

    def dkg1(self, max_signers: int, min_signers: int) -> bytes:
        self._secret, package = cf.dkg_part1(self.identifier, max_signers, min_signers)
        return package

    def dkg2(self, round1_from_others: dict[int, bytes]) -> dict[int, bytes]:
        self._round1 = round1_from_others
        self._secret, outgoing = cf.dkg_part2(self._secret, round1_from_others)
        return outgoing

    def dkg3(self, round2_to_me: dict[int, bytes]) -> bytes:
        self._key_package, public = cf.dkg_part3(self._secret, self._round1, round2_to_me)
        self._secret = b""
        return public

    def commit(self) -> bytes:
        self._nonces, commitments = cf.commit(self._key_package)
        return commitments

    def sign(self, signing_package: bytes, token: bytes, taproot: bool) -> bytes:
        if self._nonces is None:
            raise RuntimeError("no nonces: commit first; nonces are single-use")
        nonces, self._nonces = self._nonces, None
        auth = authorisation.Authorisation.from_bytes(token)
        message = cf.signing_package_message(signing_package)
        authorisation.check(auth, self._authority, message, datetime.now(UTC))
        if auth.authorisation_id in self._used_authorisations:
            raise authorisation.AuthorisationRejected("authorisation already used")
        self._used_authorisations.add(auth.authorisation_id)
        return cf.sign(signing_package, nonces, self._key_package, taproot)


def _signer_main(identifier: int, authority: bytes, conn: Connection) -> None:
    signer = _Signer(identifier, authority)
    while (request := conn.recv()) is not None:
        method, args = request
        try:
            conn.send((True, getattr(signer, method)(*args)))
        except Exception as exc:  # report to the coordinator instead of dying silently
            conn.send((False, repr(exc)))


class SigningCluster:
    def __init__(self, threshold: int, count: int, authority: bytes) -> None:
        """``authority`` is the policy engine's raw Ed25519 public key."""
        self.threshold, self.count = threshold, count
        self.public_key_package = b""
        ctx = mp.get_context("spawn")
        self._conns: dict[int, Connection] = {}
        self._procs: dict[int, mp.process.BaseProcess] = {}
        for i in range(1, count + 1):
            parent, child = ctx.Pipe()
            proc = ctx.Process(
                target=_signer_main, args=(i, authority, child), name=f"signer-{i}"
            )
            proc.start()
            self._conns[i], self._procs[i] = parent, proc

    def _request(self, calls: dict[int, tuple[str, tuple[Any, ...]]]) -> dict[int, Any]:
        """Send every call first, then collect replies, so signers compute in parallel.

        Every reply is read before any error is raised; an unread reply would otherwise be taken
        as the answer to the next request.
        """
        for i, call in calls.items():
            self._conns[i].send(call)
        results = {i: self._conns[i].recv() for i in calls}
        errors = [f"signer {i}: {value}" for i, (ok, value) in results.items() if not ok]
        if errors:
            raise RuntimeError("; ".join(errors))
        return {i: value for i, (_, value) in results.items()}

    def dkg(self) -> bytes:
        """Run distributed key generation; return the 32-byte x-only group public key."""
        ids = list(self._conns)
        round1 = self._request({i: ("dkg1", (self.count, self.threshold)) for i in ids})
        round2 = self._request(
            {i: ("dkg2", ({j: round1[j] for j in ids if j != i},)) for i in ids}
        )
        publics = self._request(
            {i: ("dkg3", ({j: round2[j][i] for j in ids if j != i},)) for i in ids}
        )
        if len(set(publics.values())) != 1:
            raise RuntimeError("signers disagree on the group public key package")
        self.public_key_package = publics[ids[0]]
        return cf.group_public_key(self.public_key_package)

    def taproot_output_key(self) -> bytes:
        """The BIP86 output key (x-only) that custody addresses pay to."""
        return cf.taproot_output_key(self.public_key_package)

    def sign(
        self, message: bytes, signers: Sequence[int], token: bytes, taproot: bool = False
    ) -> bytes:
        """Two-round FROST signing with the given signers; return a 64-byte BIP340 signature.

        ``token`` is the serialized policy authorisation; each signer checks it independently.
        With ``taproot`` the signature is valid under ``taproot_output_key()``, as a key-path
        spend of a BIP86 output requires.
        """
        commitments = self._request({i: ("commit", ()) for i in signers})
        package = cf.signing_package(commitments, message)
        shares = self._request({i: ("sign", (package, token, taproot)) for i in signers})
        return cf.aggregate(package, shares, self.public_key_package, taproot)

    def holders(self) -> dict[int, int | None]:
        """Participant identifier -> operating-system process id holding that share."""
        return {i: proc.pid for i, proc in self._procs.items()}

    def close(self) -> None:
        for i, conn in self._conns.items():
            conn.send(None)
            self._procs[i].join()

    def __enter__(self) -> SigningCluster:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
