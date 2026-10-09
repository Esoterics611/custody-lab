"""A t-of-n FROST signing cluster with one operating-system process per key share.

This is the demo's signing path, not teaching code. It uses the Zcash Foundation crate
``frost-secp256k1-tr`` through ``custody_frost``, and produces BIP340 signatures.

Each signer process holds its own key package and round-1 nonces and never sends them anywhere.
This process is the coordinator. It relays the DKG broadcast packages in clear and each signer's
sub-shares sealed to their recipient (``custody_lab.mpc.channel``), and does the same for refresh
and repair; it collects commitments and signature shares, and aggregates. It never holds a share
and cannot open the sealed messages, so it cannot sign alone. In the paper's terms it is
semi-trusted: it can deny service, and a passive coordinator learns nothing secret. One trust
remains: the signers' channel public keys pass through it at start-up, and a coordinator that
substituted its own could read the sub-shares. In production they are provisioned out of band.

Transport is a ``multiprocessing`` pipe per signer. The ``spawn`` start method gives every signer
a fresh interpreter with no memory inherited from the coordinator.

A signer produces a share only against an authorisation from the policy engine (Module 4). The
signer checks four things:
- the token carries valid Ed25519 and ML-DSA-65 signatures by the configured policy authority;
- it has not expired;
- it authorises exactly the message inside the FROST signing package;
- it has not been used before.

Nonces are burnt before those checks, so a refused request cannot be retried with the same nonces
on a different message.

Expiry is checked against the signer's own clock, unless the cluster was started with a time
authority. Then each signer sends a fresh nonce with every signing, the coordinator fetches the
time authority's signed time for it, and the signer checks the expiry against that time and never
reads its own clock (``custody_lab.policy.signed_time``). The coordinator relays the signed time;
it cannot change it or substitute an earlier one, because the signature covers the signer's own
nonce.
"""

from __future__ import annotations

import multiprocessing as mp
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from multiprocessing.connection import Connection
from types import TracebackType
from typing import Any, Protocol

import custody_frost as cf

from custody_lab.mpc import channel
from custody_lab.policy import authorisation, signed_time


class _Signer:
    """State held inside one signer process."""

    def __init__(self, identifier: int, authority: bytes, time_authority: bytes | None) -> None:
        self.identifier = identifier
        self._authority = authority
        self._time_authority = time_authority  # None: this machine's clock decides expiry
        self._time_nonce: bytes | None = None
        self._clock_offset = timedelta(0)
        self._used_authorisations: set[str] = set()
        self._secret = b""
        self._round1: dict[int, bytes] = {}
        self._key_package = b""
        self._nonces: bytes | None = None
        self._channel = channel.new_key()  # never leaves this process
        self._peers: dict[int, bytes] = {}  # the other signers' channel public keys

    def channel_key(self) -> bytes:
        return channel.public_bytes(self._channel)

    def set_peers(self, peers: dict[int, bytes]) -> None:
        self._peers = {i: key for i, key in peers.items() if i != self.identifier}

    def _seal(self, recipient: int, step: str, data: bytes) -> bytes:
        peer = self._peers.get(recipient) or channel.public_bytes(self._channel)
        return channel.seal(self._channel, peer, self.identifier, recipient, step, data)

    def _open(self, sender: int, step: str, sealed: bytes) -> bytes:
        peer = self._peers.get(sender) or channel.public_bytes(self._channel)
        return channel.open_(self._channel, peer, sender, self.identifier, step, sealed)

    def dkg1(self, max_signers: int, min_signers: int) -> bytes:
        self._secret, package = cf.dkg_part1(self.identifier, max_signers, min_signers)
        return package

    def dkg2(self, round1_from_others: dict[int, bytes]) -> dict[int, bytes]:
        self._round1 = round1_from_others
        self._secret, outgoing = cf.dkg_part2(self._secret, round1_from_others)
        return {j: self._seal(j, "dkg", sub_share) for j, sub_share in outgoing.items()}

    def dkg3(self, round2_to_me: dict[int, bytes]) -> bytes:
        opened = {j: self._open(j, "dkg", sealed) for j, sealed in round2_to_me.items()}
        self._key_package, public = cf.dkg_part3(self._secret, self._round1, opened)
        self._secret = b""
        return public

    def commit(self) -> bytes:
        if not self._key_package:
            raise RuntimeError("no key share: it was lost and has not been repaired")
        self._nonces, commitments = cf.commit(self._key_package)
        return commitments

    def refresh1(self, max_signers: int, min_signers: int) -> bytes:
        self._secret, package = cf.refresh_part1(self.identifier, max_signers, min_signers)
        return package

    def refresh2(self, round1_from_others: dict[int, bytes]) -> dict[int, bytes]:
        self._round1 = round1_from_others
        self._secret, outgoing = cf.refresh_part2(self._secret, round1_from_others)
        return {j: self._seal(j, "refresh", package) for j, package in outgoing.items()}

    def refresh3(self, round2_to_me: dict[int, bytes], public_key_package: bytes) -> bytes:
        opened = {j: self._open(j, "refresh", sealed) for j, sealed in round2_to_me.items()}
        self._key_package, public = cf.refresh_part3(
            self._secret, self._round1, opened, public_key_package, self._key_package
        )
        self._secret = b""
        return public

    def used(self) -> list[str]:
        return sorted(self._used_authorisations)

    def copy_share(self) -> bytes:
        """EDUCATIONAL, NOT PRODUCTION: what a thief who copies this signer's storage holds."""
        return self._key_package

    def wipe(self) -> None:
        self._key_package = b""

    def repair1(self, helpers: list[int], participant: int) -> dict[int, bytes]:
        deltas = cf.repair_part1(helpers, self._key_package, participant)
        return {k: self._seal(k, "repair-delta", delta) for k, delta in deltas.items()}

    def repair2(self, deltas: dict[int, bytes], participant: int) -> bytes:
        opened = [self._open(h, "repair-delta", sealed) for h, sealed in deltas.items()]
        return self._seal(participant, "repair-sigma", cf.repair_part2(opened))

    def repair3(self, sigmas: dict[int, bytes], public_key_package: bytes) -> None:
        opened = [self._open(k, "repair-sigma", sealed) for k, sealed in sigmas.items()]
        self._key_package = cf.repair_part3(opened, self.identifier, public_key_package)

    def set_clock(self, offset: timedelta) -> None:
        """EDUCATIONAL, NOT PRODUCTION: this machine's clock reads the true time plus ``offset``,
        as an attacker who can set the clock would leave it."""
        self._clock_offset = offset

    def time_nonce(self) -> bytes:
        self._time_nonce = signed_time.new_nonce()
        return self._time_nonce

    def _now(self, stamped: bytes | None) -> datetime:
        if self._time_authority is None:
            return datetime.now(UTC) + self._clock_offset
        nonce, self._time_nonce = self._time_nonce, None  # one signed time per nonce
        if stamped is None or nonce is None:
            raise authorisation.AuthorisationRejected("no signed time from the time authority")
        try:
            return signed_time.read(
                signed_time.SignedTime.from_bytes(stamped), self._time_authority, nonce
            )
        except signed_time.TimeRejected as rejected:
            raise authorisation.AuthorisationRejected(str(rejected)) from None

    def sign(
        self, signing_package: bytes, token: bytes, taproot: bool, stamped: bytes | None
    ) -> bytes:
        if self._nonces is None:
            raise RuntimeError("no nonces: commit first; nonces are single-use")
        nonces, self._nonces = self._nonces, None
        auth = authorisation.Authorisation.from_bytes(token)
        message = cf.signing_package_message(signing_package)
        authorisation.check(auth, self._authority, message, self._now(stamped))
        if auth.authorisation_id in self._used_authorisations:
            raise authorisation.AuthorisationRejected("authorisation already used")
        self._used_authorisations.add(auth.authorisation_id)
        return cf.sign(signing_package, nonces, self._key_package, taproot)


def _signer_main(
    identifier: int, authority: bytes, time_authority: bytes | None, conn: Connection
) -> None:
    signer = _Signer(identifier, authority, time_authority)
    while (request := conn.recv()) is not None:
        method, args = request
        try:
            conn.send((True, getattr(signer, method)(*args)))
        except Exception as exc:  # report to the coordinator instead of dying silently
            conn.send((False, repr(exc)))


class TimeSource(Protocol):
    """The coordinator's route to a time authority (``custody_lab.demo.parties.TimeService``)."""

    @property
    def public_key(self) -> bytes: ...  # raw Ed25519, given to every signer at start

    def stamp(self, nonce: bytes) -> bytes: ...  # a serialized ``signed_time.SignedTime``


class SigningCluster:
    def __init__(
        self, threshold: int, count: int, authority: bytes, time_source: TimeSource | None = None
    ) -> None:
        """``authority`` is the policy engine's hybrid public key, ``AuthorityKey.public_bytes``.

        With ``time_source``, every signer is given its public key and checks expiry against the
        time authority's signed time only; ``time_source`` is how this process fetches it, and
        replacing it later changes nothing the signers accept.
        """
        self.threshold, self.count = threshold, count
        self.public_key_package = b""
        self.time_source = time_source
        time_authority = time_source.public_key if time_source else None
        ctx = mp.get_context("spawn")
        self._conns: dict[int, Connection] = {}
        self._procs: dict[int, mp.process.BaseProcess] = {}
        for i in range(1, count + 1):
            parent, child = ctx.Pipe()
            proc = ctx.Process(
                target=_signer_main, args=(i, authority, time_authority, child), name=f"signer-{i}"
            )
            proc.start()
            self._conns[i], self._procs[i] = parent, proc
        # Private channels: each signer's channel public key, handed to the others. The keys pass
        # through this process; in production they are provisioned out of band (channel.py).
        self.channel_keys = self._request({i: ("channel_key", ()) for i in self._conns})
        self._request({i: ("set_peers", (self.channel_keys,)) for i in self._conns})

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
        round2 = self._request({i: ("dkg2", ({j: round1[j] for j in ids if j != i},)) for i in ids})
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
        stamped: dict[int, bytes | None] = dict.fromkeys(signers)
        if self.time_source is not None:
            nonces = self._request({i: ("time_nonce", ()) for i in signers})
            stamped = {i: self.time_source.stamp(nonce) for i, nonce in nonces.items()}
        shares = self._request(
            {i: ("sign", (package, token, taproot, stamped[i])) for i in signers}
        )
        return cf.aggregate(package, shares, self.public_key_package, taproot)

    def refresh(self) -> bytes:
        """Proactive refresh: every signer gets a new share of the same key; return the group key.

        The signers run a DKG whose shared secret is zero and add their part of it to their
        current share. Every share and every verifying share changes; the group key, and so the
        custody address, do not. A share copied before the refresh no longer combines with
        shares made after it. Every signer must be running.
        """
        ids = list(self._conns)
        if len(ids) != self.count:
            raise RuntimeError(f"refresh needs all {self.count} signers; {len(ids)} are running")
        before = cf.group_public_key(self.public_key_package)
        round1 = self._request({i: ("refresh1", (self.count, self.threshold)) for i in ids})
        round2 = self._request(
            {i: ("refresh2", ({j: round1[j] for j in ids if j != i},)) for i in ids}
        )
        publics = self._request(
            {
                i: ("refresh3", ({j: round2[j][i] for j in ids if j != i}, self.public_key_package))
                for i in ids
            }
        )
        if len(set(publics.values())) != 1:
            raise RuntimeError("signers disagree on the refreshed public key package")
        if cf.group_public_key(publics[ids[0]]) != before:
            raise RuntimeError("refresh changed the group key")
        self.public_key_package = publics[ids[0]]
        return before

    def export_share(self, identifier: int) -> bytes:
        """EDUCATIONAL, NOT PRODUCTION: a copy of one signer's key package, as a thief who copied
        its storage would hold. It exists to show what a stolen share can and cannot do."""
        share: bytes = self._request({identifier: ("copy_share", ())})[identifier]
        return share

    def wipe(self, identifier: int) -> None:
        """Signer ``identifier`` loses its share, as a failed disk without a backup would."""
        self._request({identifier: ("wipe", ())})

    def repair(self, identifier: int, helpers: Sequence[int]) -> None:
        """Rebuild signer ``identifier``'s share with the help of ``helpers`` (at least the
        threshold), by the repairable threshold scheme of Laing and Stinson (ePrint 2017/1155).

        Each helper splits its contribution into one random-looking delta per helper, itself
        included; each helper adds the deltas it receives into one sigma; the participant adds
        the sigmas into its share. No helper's share, and no single delta or sigma, reveals a
        share.
        """
        helpers = list(helpers)
        deltas = self._request({h: ("repair1", (helpers, identifier)) for h in helpers})
        sigmas = self._request(
            {k: ("repair2", ({h: deltas[h][k] for h in helpers}, identifier)) for k in helpers}
        )
        self._request({identifier: ("repair3", (sigmas, self.public_key_package))})

    def set_clock(self, identifier: int, offset: timedelta) -> None:
        """EDUCATIONAL, NOT PRODUCTION: signer ``identifier``'s machine clock reads the true time
        plus ``offset`` from now on, as an attacker who sets it would leave it. A signer started
        with a time authority never reads it."""
        self._request({identifier: ("set_clock", (offset,))})

    def used_authorisations(self) -> set[str]:
        """Every authorisation identifier any running signer has signed under: the signers' own
        record, to reconcile against the policy engine's audit log."""
        used: dict[int, list[str]] = self._request({i: ("used", ()) for i in self._conns})
        return {a for ids in used.values() for a in ids}

    def holders(self) -> dict[int, int | None]:
        """Participant identifier -> operating-system process id holding that share."""
        return {i: proc.pid for i, proc in self._procs.items()}

    def stop(self, identifier: int) -> None:
        """End one signer's process, as an outage would; its share goes with it.

        The remaining signers can still sign while at least ``threshold`` of them are running.
        A request to a stopped signer raises ``KeyError``.
        """
        self._conns.pop(identifier).send(None)
        self._procs[identifier].join()

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
