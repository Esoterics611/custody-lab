import { useEffect, useState } from 'react'
import { Hex } from './fields'
import { toBtc, toSats, walk, type InclusionProof, type Level } from './reserves'
import { SignatureCheck } from './Signature'
import type { SnapshotDocument } from './snapshot'
import type { StepState } from './stream'

interface Props {
  reserves?: StepState
}

function plusOneSatoshi(btc: string): string {
  try {
    return toBtc(toSats(btc) + 1n)
  } catch {
    return btc
  }
}

export function BalanceCheck({ reserves }: Props) {
  const proofs = (reserves?.detail.inclusion_proofs ?? []) as InclusionProof[]
  const [client, setClient] = useState(0)
  const [claim, setClaim] = useState<string | null>(null) // null: the proof's own balance
  const [levels, setLevels] = useState<Level[] | null>(null)
  const [problem, setProblem] = useState<string | null>(null)
  const proof = proofs[client] as InclusionProof | undefined
  const balance = claim ?? proof?.balance ?? ''

  useEffect(() => {
    if (!proof) return
    let current = true
    walk(proof, balance)
      .then((computed) => current && (setLevels(computed), setProblem(null)))
      .catch((error: unknown) => {
        if (!current) return
        setLevels(null)
        setProblem(error instanceof Error ? error.message : String(error)) // "not an amount: …"
      })
    return () => {
      current = false
    }
  }, [proof, balance])

  if (reserves?.status !== 'done' || !proof) {
    return (
      <section className="card check">
        <h2>Check a client's balance</h2>
        <p className="muted">
          This check uses the proof-of-reserves snapshot a run publishes at step 9. Run the demo
          first, on the Settlement run tab.
        </p>
      </section>
    )
  }

  const root = String(reserves.detail.root)
  const snapshot = reserves.detail.snapshot_document as SnapshotDocument | undefined
  const liabilities = String(reserves.detail.liabilities)
  const reached = levels?.[levels.length - 1]
  const included = reached?.hash === root
  return (
    <section className="check">
      <div className="card">
        <h2>Check a client's balance</h2>
        <p>
          After each settlement the custodian publishes one hash, the liabilities root, that
          commits to every client's balance and to their total. Each client receives its own
          balance, a random salt and the hashes on the path from its entry to that root. Starting
          from the balance it expects, the client recomputes the path. If the result equals the
          published root, its balance is included as stated. A balance changed by one satoshi gives
          a different root.
        </p>
        <p className="muted">
          This page does the arithmetic itself, with the browser's SHA-256 (
          <code>web/src/reserves.ts</code>), sharing no code with the server. The page holds all
          four proofs because it plays each client in turn; a real client receives only its own.
        </p>
        <div className="clients" role="tablist" aria-label="Client">
          {proofs.map((p, i) => (
            <button
              key={p.client}
              type="button"
              role="tab"
              aria-selected={i === client}
              className={i === client ? 'chosen' : ''}
              onClick={() => (setClient(i), setClaim(null))}
            >
              {p.client}
            </button>
          ))}
        </div>
        <label className="claim">
          <span>Balance {proof.client} expects (BTC)</span>
          <input
            value={balance}
            inputMode="decimal"
            onChange={(event) => setClaim(event.target.value.trim())}
          />
          <button type="button" className="secondary" onClick={() => setClaim(plusOneSatoshi(balance))}>
            +1 satoshi
          </button>
          <button type="button" className="secondary" onClick={() => setClaim(null)} disabled={claim === null}>
            Reset
          </button>
        </label>
      </div>

      {problem && <p className="problem">{problem}</p>}
      {levels && reached && (
        <>
          <ol className="path card">
            {levels.map((level, i) => (
              <li key={i} className={i === levels.length - 1 ? (included ? 'root ok' : 'root bad') : ''}>
                <span className="level">
                  {i === 0 ? 'Leaf' : i === levels.length - 1 ? 'Root' : `Level ${i}`}
                </span>
                <div>
                  <div>
                    {i === 0
                      ? `${proof.client}'s salt, name and ${toBtc(level.sats)} BTC, hashed`
                      : `the two nodes below, with their sums, hashed: total ${toBtc(level.sats)} BTC`}
                  </div>
                  <Hex text={level.hash} />
                  {level.sibling && (
                    <div className="muted">
                      combined with the {level.sibling.left ? 'left' : 'right'}-hand sibling,{' '}
                      {toBtc(BigInt(level.sibling.sats))} BTC <Hex text={level.sibling.hash} />
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ol>
          <p className={`verdict ${included ? 'ok' : 'bad'}`}>
            {included
              ? `Included. The recomputed root equals the published root, so the snapshot commits to ${proof.client} holding ${balance} BTC, within total liabilities of ${toBtc(reached.sats)} BTC (published: ${liabilities}).`
              : `Not included. With ${balance} BTC the path reaches a different root, so the published snapshot does not commit to that balance. ${proof.client} would raise it with the custodian.`}
          </p>
          <p className="muted">
            Published root <Hex text={root} />
          </p>
        </>
      )}
      {snapshot && <SignatureCheck snapshot={snapshot} />}
    </section>
  )
}
