// Reads {"vectors": [{public_key, message, signature}], "snapshots": [document]} on stdin and
// prints what web/src/snapshot.ts concludes for each. Driven by tests/demo/test_browser_snapshot.py.
import { readFileSync } from 'node:fs'
import { checkSnapshot, verifyBip340, type SnapshotDocument } from '../src/snapshot.ts'
import { unhex } from '../src/reserves.ts'

const input = JSON.parse(readFileSync(0, 'utf8')) as {
  vectors: { public_key: string; message: string; signature: string }[]
  snapshots: SnapshotDocument[]
}
const vectors = input.vectors.map((v) =>
  verifyBip340(v.signature, unhex(v.message.toLowerCase()), v.public_key),
)
const snapshots = await Promise.all(input.snapshots.map(checkSnapshot))
console.log(JSON.stringify({ vectors, snapshots }))
