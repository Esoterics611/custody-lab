// Reads {"proofs": [...], "claims": {client: btc}} on stdin and prints, for each proof, the root
// that web/src/reserves.ts recomputes from the claimed balance (the proof's own when unclaimed).
// Driven by tests/demo/test_browser_verifier.py.
import { readFileSync } from 'node:fs'
import { walk, type InclusionProof } from '../src/reserves.ts'

const input = JSON.parse(readFileSync(0, 'utf8')) as {
  proofs: InclusionProof[]
  claims: Record<string, string>
}
const out: Record<string, { root: string; sats: string }> = {}
for (const proof of input.proofs) {
  const levels = await walk(proof, input.claims[proof.client] ?? proof.balance)
  const root = levels[levels.length - 1]
  out[proof.client] = { root: root.hash, sats: root.sats.toString() }
}
console.log(JSON.stringify(out))
