// The client's check of the custodian's proof of control, in the browser.
//
// A proof-of-reserves snapshot is a statement (block, liabilities root and total, assets, custody
// key, audit head) and a BIP340 signature over a tagged hash of it, made by two of the three
// signers. This module recomputes the signed message from the statement's own fields, as
// src/custody_lab/reserves/snapshot.py defines it, and verifies the signature with @noble/curves,
// an audited secp256k1 library that shares no code with the Python verifier.
// tests/demo/test_browser_snapshot.py runs it under Node on the BIP340 test vectors and on
// snapshots the Python code signs.
//
//   statement = every field except the attestation and the reserve ratio, as JSON with sorted keys
//               and no spaces (the fields are ASCII, so JSON.stringify and Python's json.dumps
//               write the same bytes)
//   message   = H_tag(attestation.tag, statement), as in BIP340
//   valid     = BIP340 verify(signature, message, custody_output_key)

import { schnorr } from '@noble/curves/secp256k1.js'
import { hex, taggedHash, unhex } from './reserves.ts'

export interface Attestation {
  tag: string
  message: string // hex, as published
  bip340_signature: string // hex
}

export type SnapshotDocument = Record<string, unknown> & {
  attestation: Attestation
  custody_output_key: string // x-only key, hex
}

export interface SnapshotCheck {
  statement: string
  message: string // recomputed, hex
  messageMatches: boolean // the recomputed message equals the published one
  signatureValid: boolean // the signature verifies over the recomputed message
}

export function statementOf(document: SnapshotDocument): string {
  const fields = Object.entries(document)
    .filter(([key]) => key !== 'attestation' && key !== 'reserve_ratio')
    .sort(([a], [b]) => (a < b ? -1 : 1))
  return JSON.stringify(Object.fromEntries(fields))
}

/** BIP340 verification; a malformed key or signature fails the check rather than throwing. */
export function verifyBip340(signature: string, message: Uint8Array, key: string): boolean {
  try {
    return schnorr.verify(unhex(signature.toLowerCase()), message, unhex(key.toLowerCase()))
  } catch {
    return false
  }
}

export async function checkSnapshot(document: SnapshotDocument): Promise<SnapshotCheck> {
  const statement = statementOf(document)
  const message = await taggedHash(document.attestation.tag, new TextEncoder().encode(statement))
  return {
    statement,
    message: hex(message),
    messageMatches: hex(message) === document.attestation.message,
    signatureValid: verifyBip340(
      document.attestation.bip340_signature,
      message,
      document.custody_output_key,
    ),
  }
}
