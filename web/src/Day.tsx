import { useEffect, useState } from 'react'
import { BooksPanel } from './Books'
import { Step } from './steps'
import { PENDING, lastTwoBooks, merge, post, type DemoEvent, type StepState } from './stream'

// One row of the day's transaction log, gathered from the steps' details.
interface Entry {
  kind: string
  who: string
  amount: string
  outcome: string
  tone: 'ok' | 'bad' | 'off'
}

type Row = Record<string, string>

function entries(state: Record<string, StepState>): Entry[] {
  const log: Entry[] = []
  for (const d of (state.deposits?.detail.deposits ?? []) as Row[]) {
    const credited = d.status.startsWith('credited')
    log.push({
      kind: 'deposit',
      who: d.client,
      amount: d.amount,
      outcome: credited ? 'credited' : 'replaced before it confirmed',
      tone: credited ? 'ok' : 'bad',
    })
  }
  const settle = state.settle?.detail
  if (settle?.txid) {
    log.push({
      kind: 'settlement',
      who: 'net of alpha-capital and beta-fund',
      amount: String(settle.pays),
      outcome: 'confirmed',
      tone: 'ok',
    })
  }
  for (const step of ['withdraw_gamma', 'withdraw_beta']) {
    const w = state[step]?.detail
    if (w?.txid) {
      log.push({
        kind: 'withdrawal',
        who: String(w.client),
        amount: String(w.pays),
        outcome: 'confirmed',
        tone: 'ok',
      })
    }
  }
  const refused = (state.refused?.detail.requests ?? {}) as Record<string, Row>
  for (const r of Object.values(refused)) {
    log.push({
      kind: 'withdrawal',
      who: r.client,
      amount: r.amount,
      outcome: `refused by ${r.refused_by}`,
      tone: 'off',
    })
  }
  return log
}

function Log({ log }: { log: Entry[] }) {
  if (log.length === 0) return null
  return (
    <section className="card txlog">
      <h2>The day's transactions</h2>
      <ol>
        {log.map((e, i) => (
          <li key={i} className={e.tone}>
            <span className="kind">{e.kind}</span>
            <span>{e.who}</span>
            <strong>{e.amount}</strong>
            <span className="outcome">{e.outcome}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}

export function Day() {
  const [steps, setSteps] = useState<[string, string][]>([])
  const [state, setState] = useState<Record<string, StepState>>({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/day/steps')
      .then((response) => response.json())
      .then((listed: Record<string, string>) => setSteps(Object.entries(listed)))
      .catch(() => setProblem('The demo server is not reachable. Start it: uv run custody-lab serve'))
  }, [])

  const [books, before] = lastTwoBooks(steps, state)

  async function start() {
    setBusy(true)
    setState({})
    setProblem(null)
    let last: DemoEvent | undefined
    try {
      await post<DemoEvent>('/api/day', {}, (event) => {
        last = event
        setState((previous) => merge(previous, event))
      })
      if (last?.status === 'running') setProblem(`The stream ended during: ${last.title}`)
    } catch (error) {
      setProblem(`The day's stream broke: ${String(error)}`)
    } finally {
      setBusy(false)
    }
  }

  const done = steps.filter(([id]) => state[id]?.status === 'done').length
  return (
    <section className="day">
      <div className="toolbar card">
        <p>
          A busier day than the settlement run: four clients deposit, one tries to take its
          deposit back before it confirms, two trade, the custodian nets across them, a signer
          goes down, clients withdraw, and three requests are refused. After every step the
          ledger is compared with the coins on the chain.
        </p>
        <button type="button" onClick={start} disabled={busy || steps.length === 0}>
          {busy ? 'Running the day' : done ? 'Run the day again' : 'Run the day'}
        </button>
        <div className="progress" aria-label={`${done} of ${steps.length} steps done`}>
          <div style={{ width: `${(100 * done) / Math.max(steps.length, 1)}%` }} />
        </div>
        <span className="muted">
          {done} of {steps.length} steps
        </span>
      </div>
      {problem && <p className="problem">{problem}</p>}
      <main>
        <ol className="steps">
          {steps.map(([id, title], i) => (
            <Step
              key={id}
              n={i + 1}
              title={title}
              state={state[id] ?? PENDING}
              hidden={['books', 'inclusion_proofs', 'snapshot_document']}
            />
          ))}
        </ol>
        <aside>
          <BooksPanel books={books} before={before} />
          <Log log={entries(state)} />
        </aside>
      </main>
    </section>
  )
}
