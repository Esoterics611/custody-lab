// A client's check of its own balance against the published liabilities root, in the browser.
//
// This is a second implementation of src/custody_lab/reserves/merkle_sum.py, written from its
// encoding and sharing no code with it: SHA-256 comes from WebCrypto, and amounts are exact
// integer satoshis (bigint). tests/demo/test_browser_verifier.py runs it under Node against
// proofs made by the Python tree, so the two must agree byte for byte.
//
//   leaf   = H_tag("custody-lab/por-leaf", salt || client (UTF-8) || 0x00 || sats (8 bytes, big-endian))
//   parent = H_tag("custody-lab/por-node", left hash || left sats || right hash || right sats)
//   H_tag(tag, data) = SHA-256(SHA-256(tag) || SHA-256(tag) || data), as in BIP340

export interface ProofStep {
  hash: string // the sibling's hash, hex
  sats: number // the sibling's sum
  left: boolean // the sibling is the left child
}

export interface InclusionProof {
  client: string
  balance: string // BTC, as published
  salt: string // hex
  path: ProofStep[]
}

export interface Level {
  hash: string // the node computed at this level, hex
  sats: bigint
  sibling?: ProofStep // the sibling combined with it to make the next level
}

const encoder = new TextEncoder()

export function hex(bytes: Uint8Array): string {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}

export function unhex(text: string): Uint8Array {
  if (!/^([0-9a-f]{2})*$/.test(text)) throw new Error(`not hex: ${text}`)
  return Uint8Array.from(text.match(/../g) ?? [], (pair) => parseInt(pair, 16))
}

function concat(...parts: Uint8Array[]): Uint8Array<ArrayBuffer> {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0))
  let at = 0
  for (const part of parts) {
    out.set(part, at)
    at += part.length
  }
  return out
}

async function sha256(data: Uint8Array<ArrayBuffer>): Promise<Uint8Array> {
  return new Uint8Array(await crypto.subtle.digest('SHA-256', data))
}

export async function taggedHash(tag: string, data: Uint8Array): Promise<Uint8Array> {
  const t = await sha256(encoder.encode(tag))
  return sha256(concat(t, t, data))
}

function u64(sats: bigint): Uint8Array {
  if (sats < 0n || sats >= 1n << 64n) throw new Error(`sum out of range: ${sats}`)
  const out = new Uint8Array(8)
  new DataView(out.buffer).setBigUint64(0, sats)
  return out
}

/** Exact BTC to satoshis; refuses a sub-satoshi amount, as the Python side does. */
export function toSats(btc: string): bigint {
  const match = /^(\d+)(?:\.(\d+))?$/.exec(btc)
  if (!match) throw new Error(`not an amount: ${btc}`)
  const fraction = (match[2] ?? '').replace(/0+$/, '')
  if (fraction.length > 8) throw new Error(`${btc} BTC is not a whole number of satoshis`)
  return BigInt(match[1]) * 100_000_000n + BigInt(fraction.padEnd(8, '0'))
}

export function toBtc(sats: bigint): string {
  const whole = sats / 100_000_000n
  const fraction = (sats % 100_000_000n).toString().padStart(8, '0').replace(/0+$/, '')
  return fraction ? `${whole}.${fraction}` : `${whole}`
}

/**
 * Recompute the path from the client's own leaf to the root. `balance` is the figure the client
 * believes it is owed; it defaults to the one in the proof. The last level is the root.
 */
export async function walk(proof: InclusionProof, balance = proof.balance): Promise<Level[]> {
  const sats = toSats(balance)
  let hash = await taggedHash(
    'custody-lab/por-leaf',
    concat(unhex(proof.salt), encoder.encode(proof.client), Uint8Array.of(0), u64(sats)),
  )
  let total = sats
  const levels: Level[] = []
  for (const step of proof.path) {
    levels.push({ hash: hex(hash), sats: total, sibling: step })
    const sibling = [unhex(step.hash), u64(BigInt(step.sats))]
    const mine = [hash, u64(total)]
    const [left, right] = step.left ? [sibling, mine] : [mine, sibling]
    hash = await taggedHash('custody-lab/por-node', concat(...left, ...right))
    total += BigInt(step.sats)
  }
  levels.push({ hash: hex(hash), sats: total })
  return levels
}
