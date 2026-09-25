"""A proof-of-reserves snapshot, published after each settlement batch.

A snapshot binds:
- **Liabilities**: the Merkle-sum root and total over every client balance.
- **Assets**: the custody output key's on-chain balance at a stated block.
- **Proof of control**: a BIP340 signature by the FROST cluster, under the custody output key,
  over a tagged hash of the snapshot.
- **The policy audit head**: anchoring the Module 4 log, so truncating it is detectable.

The attestation message is ``H_tag(statement)`` with a tag of its own. A tagged hash under this
tag can never equal a BIP341 transaction sighash (``TapSighash`` tag), so a coordinator cannot pass
off a spend as an attestation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from custody_lab.foundations.hashing import tagged_hash
from custody_lab.policy.model import canonical_json

ATTESTATION_TAG = "custody-lab/reserves-attestation"


@dataclass(frozen=True)
class Snapshot:
    taken_at: datetime
    block_height: int
    block_hash: str
    liabilities_root: str
    liabilities: Decimal
    clients: int
    assets: Decimal
    custody_output_key: str
    audit_head: str

    @property
    def reserve_ratio(self) -> Decimal:
        return (self.assets / self.liabilities).quantize(Decimal("0.00001"))

    def statement(self) -> bytes:
        """Canonical bytes of the snapshot: what the attestation covers."""
        return canonical_json({k: v for k, v in self.__dict__.items()})

    def attestation_message(self) -> bytes:
        return tagged_hash(ATTESTATION_TAG, self.statement())


def publish(snapshot: Snapshot, signature: bytes, directory: Path) -> Path:
    """Write the snapshot and its proof-of-control signature as JSON; return the path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"snapshot-{snapshot.block_height}.json"
    document = json.loads(snapshot.statement())
    document["reserve_ratio"] = str(snapshot.reserve_ratio)
    document["attestation"] = {
        "tag": ATTESTATION_TAG,
        "message": snapshot.attestation_message().hex(),
        "bip340_signature": signature.hex(),
        "verify_with": "x-only key custody_output_key",
    }
    path.write_text(json.dumps(document, indent=2) + "\n")
    return path
