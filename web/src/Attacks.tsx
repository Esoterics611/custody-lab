import { useState, type CSSProperties } from 'react'
import { post } from './stream'

// One line from POST /api/attacks; see src/custody_lab/demo/attacks.py.
interface Attempt {
  attack: string
  group: 'policy' | 'signers' | 'records'
  title: string
  defence: string
  refused: boolean
  reason: string
}

const GROUPS: Record<Attempt['group'], [string, string]> = {
  policy: ['Policy engine', 'Who may move coins, how much, and where. Chapter 4.'],
  signers: [
    'Signers',
    'Each signer process checks the authorisation itself, and one share cannot sign. Chapters 2 and 4.',
  ],
  records: ['Published records', 'Anyone can check what the custodian publishes. Chapters 4 and 6.'],
}

/** "signer 1: AuthorisationRejected('expired at …'); signer 3: …" as one line per signer. */
function reasons(reason: string): string[] {
  return reason
    .split(/; (?=signer \d+:)/)
    .map((line) => line.replace(/^(signer \d+): \w+\('(.*)'\)$/, '$1: $2'))
}

export function Attacks() {
  const [attempts, setAttempts] = useState<Attempt[]>([])
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)
  const [finished, setFinished] = useState(false)

  async function start() {
    setBusy(true)
    setAttempts([])
    setProblem(null)
    setFinished(false)
    try {
      await post<Attempt>('/api/attacks', {}, (a) => setAttempts((previous) => [...previous, a]))
      setFinished(true)
    } catch (error) {
      setProblem(`The attack stream broke: ${String(error)}`)
    } finally {
      setBusy(false)
    }
  }

  const refused = attempts.filter((a) => a.refused).length
  const accepted = attempts.length - refused
  return (
    <section className="attacks">
      <div className="toolbar card">
        <p>
          Seventeen attacks a thief or a careless insider would try, each run against the demo's real
          policy engine, signer processes and verifiers. No chain is needed. Each row names the
          component that refused the attack and quotes its refusal.
        </p>
        <button type="button" onClick={start} disabled={busy}>
          {busy ? 'Attacking' : attempts.length ? 'Run the attacks again' : 'Run the attacks'}
        </button>
      </div>
      {problem && <p className="problem">{problem}</p>}
      {finished && (
        <p className={`verdict ${accepted ? 'bad' : 'ok'}`}>
          {refused} of {attempts.length} attacks refused
          {accepted > 0 && `; ${accepted} got through, so a defence is broken`}.
        </p>
      )}
      {(Object.keys(GROUPS) as Attempt['group'][]).map((group) => {
        const rows = attempts.filter((a) => a.group === group)
        if (rows.length === 0) return null
        const [name, note] = GROUPS[group]
        return (
          <div key={group} className="attack-group">
            <h2>{name}</h2>
            <p className="muted">{note}</p>
            <ol>
              {rows.map((a) => (
                <li
                  key={a.attack}
                  className={`attempt ${a.refused ? 'refused' : 'accepted'}`}
                  style={{ '--i': attempts.indexOf(a) } as CSSProperties}
                >
                  <span className="pill">{a.refused ? 'refused' : 'accepted'}</span>
                  <div>
                    <strong>{a.title}</strong>
                    <span className="by">
                      {a.refused ? 'stopped by' : 'not stopped by'} {a.defence}
                    </span>
                    {reasons(a.reason).map((line) => (
                      <code key={line}>{line}</code>
                    ))}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )
      })}
    </section>
  )
}
