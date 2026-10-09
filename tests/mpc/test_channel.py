"""Private channels: a sealed message opens only for its recipient, for its protocol step and
unaltered; and the coordinator relays key-generation sub-shares it cannot open."""

from typing import Any

import pytest
from cryptography.exceptions import InvalidTag

from custody_lab.mpc import channel
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy import authorisation


def test_a_sealed_message_opens_only_for_its_recipient_its_step_and_unaltered() -> None:
    one, two, outsider = channel.new_key(), channel.new_key(), channel.new_key()
    sealed = channel.seal(one, channel.public_bytes(two), 1, 2, "dkg", b"sub-share for 2")

    assert channel.open_(two, channel.public_bytes(one), 1, 2, "dkg", sealed) == b"sub-share for 2"
    attempts = [
        (outsider, channel.public_bytes(one), 1, 2, "dkg", sealed),  # someone else's key
        (two, channel.public_bytes(one), 1, 2, "refresh", sealed),  # another step
        (two, channel.public_bytes(one), 3, 2, "dkg", sealed),  # claimed from another sender
        (two, channel.public_bytes(one), 1, 2, "dkg", sealed[:-1] + bytes([sealed[-1] ^ 1])),
    ]
    for own, peer, sender, recipient, step, data in attempts:
        with pytest.raises(InvalidTag):
            channel.open_(own, peer, sender, recipient, step, data)


class _Recording(SigningCluster):
    """A curious coordinator: it keeps every reply it relays."""

    def __init__(self, threshold: int, count: int, authority: bytes) -> None:
        self.relayed: list[tuple[str, dict[int, Any]]] = []
        super().__init__(threshold, count, authority)

    def _request(self, calls: dict[int, tuple[str, tuple[Any, ...]]]) -> dict[int, Any]:
        replies = super()._request(calls)
        self.relayed.append((next(iter(calls.values()))[0], replies))
        return replies


def test_the_coordinator_relays_sub_shares_it_cannot_open() -> None:
    authority = authorisation.AuthorityKey.generate()
    cluster = _Recording(2, 3, authority.public_bytes())
    with cluster:
        cluster.dkg()
        cluster.refresh()
        sealed = [r for step, r in cluster.relayed if step in ("dkg2", "refresh2")]
        own = channel.new_key()  # the coordinator's own key: all it can bring

    assert len(sealed) == 2
    for replies in sealed:
        for sender, outgoing in replies.items():
            for recipient, message in outgoing.items():
                for peer in (cluster.channel_keys[sender], cluster.channel_keys[recipient]):
                    with pytest.raises(InvalidTag):
                        channel.open_(own, peer, sender, recipient, "dkg", message)
                    with pytest.raises(InvalidTag):
                        channel.open_(own, peer, sender, recipient, "refresh", message)
