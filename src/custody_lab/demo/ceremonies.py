"""Key ceremonies: what a stolen share can do, what a refresh takes from it, and repairing a share.

EDUCATIONAL, NOT PRODUCTION. ``run`` generates a 2-of-3 key in three signer processes, then plays
two ceremonies against the real Zcash Foundation FROST code, reporting each step as an ``Event``.
No chain is needed.

**Refresh** (chapter 2, proactive refresh):

1. A thief copies signer 1's share. One share cannot sign.
2. Had the thief also copied signer 3's share in the same period, the two would sign: two shares
   of one period are the key.
3. The signers refresh. Every share changes; the key, and so the custody address, do not.
4. The thief now copies signer 3's new share. Signer 1's old share and signer 3's new share do not
   combine: FROST names share 1 as the culprit.
5. The new shares sign under the unchanged key.

A refresh therefore limits how long a thief has to collect a threshold of shares. It does not undo
a theft of a threshold within one period: after that, the coins must move to a new key.

**Repair** (chapter 2, backup and repair):

6. Signer 2 loses its share, as a failed disk without a backup would, and can no longer sign.
7. Signers 1 and 3 rebuild it with the repairable threshold scheme, without revealing their own.
8. Signer 2 signs again, with signer 3, under the same key.

The thief's signing runs in the coordinator's process from copied key packages, as a thief's own
machine would; it checks no authorisation, because a thief does not. The honest signers sign
proof-of-control statements, each authorised by the policy engine.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import custody_frost as cf

from custody_lab.demo.pipeline import Event
from custody_lab.foundations import schnorr
from custody_lab.foundations.hashing import sha256, tagged_hash
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy.audit import AuditLog
from custody_lab.policy.authorisation import AuthorityKey
from custody_lab.policy.engine import Policy, PolicyEngine
from custody_lab.reserves.snapshot import ATTESTATION_TAG

STEPS = {
    "keys": "Generate the custody key: 2-of-3, one process per share",
    "one_share": "A thief copies signer 1's share; one share cannot sign",
    "same_period": "A second share from the same period would complete the key",
    "refresh": "Refresh: every share changes, the key does not",
    "mixed": "Signer 1's old share and signer 3's new share cannot sign together",
    "fresh": "The new shares sign under the same key",
    "lost": "Signer 2 loses its share",
    "repair": "Signers 1 and 3 rebuild signer 2's share",
    "repaired": "Signer 2 signs again",
}


def _now() -> datetime:
    return datetime.now(UTC)


def _fingerprint(data: bytes) -> str:
    """The first 16 hex digits of SHA-256: enough to see that a value changed."""
    return sha256(data).hex()[:16]


def thief_sign(message: bytes, shares: dict[int, bytes], public_key_package: bytes) -> bytes:
    """Sign ``message`` from copied key packages in one process, as a thief would.

    Raises when the shares do not combine: too few of them, or shares of different periods.
    """
    nonces, commitments = {}, {}
    for i, share in shares.items():
        nonces[i], commitments[i] = cf.commit(share)
    package = cf.signing_package(commitments, message)
    parts = {i: cf.sign(package, nonces[i], share, True) for i, share in shares.items()}
    return cf.aggregate(package, parts, public_key_package, True)


def _refused(attempt: Callable[[], object]) -> str:
    """The refusal of ``attempt``, with FROST's culprit identifiers given as participant numbers."""
    try:
        attempt()
    except (RuntimeError, ValueError) as refused:
        reason = str(refused)
        culprits = [int(h, 16) for h in re.findall(r'Identifier\("([0-9a-f]+)"\)', reason)]
        if culprits:
            who = " and ".join(str(c) for c in culprits)
            return f"the share from participant {who} does not fit (InvalidSignatureShare)"
        return re.sub(r"(signer \d+): \w+\('(.*?)'\)", r"\1: \2", reason)
    raise RuntimeError("the attempt produced a signature")


def run(emit: Callable[[Event], None]) -> dict[str, Any]:
    """Play both ceremonies; return the group key and whether it stayed the same."""
    started = time.monotonic()
    current = next(iter(STEPS))

    def report(step: str, status: str, **detail: Any) -> None:
        nonlocal current
        current = step
        at_ms = round((time.monotonic() - started) * 1000)
        emit(Event(step, status, STEPS[step], detail, at_ms))

    engine = PolicyEngine(Policy({}, {}), AuthorityKey.generate(), AuditLog(_now), _now)

    def honest_sign(cluster: SigningCluster, statement: bytes, signers: list[int]) -> bool:
        token = engine.authorise_attestation(statement)
        message = tagged_hash(ATTESTATION_TAG, statement)
        signature = cluster.sign(message, signers, token.to_bytes(), taproot=True)
        return schnorr.verify(message, cluster.taproot_output_key(), signature)

    report("keys", "running")
    try:
        with SigningCluster(2, 3, authority=engine.authority_public_key) as cluster:
            group = cluster.dkg()
            output_key = cluster.taproot_output_key()
            report(
                "keys",
                "done",
                signers=[{"share": i, "pid": pid} for i, pid in cluster.holders().items()],
                threshold="2 of 3",
                group_key=group.hex(),
                output_key=output_key.hex(),
                public_key_package=_fingerprint(cluster.public_key_package),
            )

            report("one_share", "running")
            old_public = cluster.public_key_package
            stolen_1 = cluster.export_share(1)
            message = tagged_hash(ATTESTATION_TAG, b"the thief's payment")
            report(
                "one_share",
                "done",
                stolen=f"signer 1's share, fingerprint {_fingerprint(stolen_1)}",
                alone=_refused(lambda: thief_sign(message, {1: stolen_1}, old_public)),
            )

            report("same_period", "running")
            same_period_3 = cluster.export_share(3)
            signature = thief_sign(message, {1: stolen_1, 3: same_period_3}, old_public)
            report(
                "same_period",
                "done",
                if_also_stolen="signer 3's share, from the same period",
                signature_valid=schnorr.verify(message, output_key, signature),
                lesson="two shares of one period are the key; after such a theft the coins "
                "must move to a new key",
            )
            del same_period_3  # the rest of the story: the thief got only signer 1's share

            report("refresh", "running")
            cluster.refresh()
            report(
                "refresh",
                "done",
                group_key=group.hex(),
                group_key_unchanged=cf.group_public_key(cluster.public_key_package) == group,
                output_key_unchanged=cluster.taproot_output_key() == output_key,
                public_key_package=f"{_fingerprint(old_public)} before, "
                f"{_fingerprint(cluster.public_key_package)} after",
            )

            report("mixed", "running")
            stolen_3 = cluster.export_share(3)
            new_public = cluster.public_key_package
            report(
                "mixed",
                "done",
                stolen_later=f"signer 3's new share, fingerprint {_fingerprint(stolen_3)}",
                with_new_public_key_package=_refused(
                    lambda: thief_sign(message, {1: stolen_1, 3: stolen_3}, new_public)
                ),
                with_old_public_key_package=_refused(
                    lambda: thief_sign(message, {1: stolen_1, 3: stolen_3}, old_public)
                ),
            )

            report("fresh", "running", signers=[1, 3])
            report(
                "fresh",
                "done",
                signers=[1, 3],
                signature_valid=honest_sign(cluster, b"after the refresh", [1, 3]),
                under_the_same_output_key=output_key.hex(),
            )

            report("lost", "running")
            cluster.wipe(2)
            report(
                "lost",
                "done",
                signer_2=_refused(lambda: honest_sign(cluster, b"signer 2 lost", [2, 3])),
            )

            report("repair", "running", helpers=[1, 3])
            cluster.repair(2, [1, 3])
            report(
                "repair",
                "done",
                helpers=[1, 3],
                each_helper_sent="one sigma: the sum of the deltas it received, which reveals "
                "nothing about its own share",
                public_key_package_unchanged=cluster.public_key_package == new_public,
            )

            report("repaired", "running", signers=[2, 3])
            report(
                "repaired",
                "done",
                signers=[2, 3],
                signature_valid=honest_sign(cluster, b"after the repair", [2, 3]),
                under_the_same_output_key=output_key.hex(),
            )
    except Exception as exc:
        report(current, "failed", error=f"{type(exc).__name__}: {exc}")
        raise
    return {"group_key": group.hex(), "output_key": output_key.hex()}
