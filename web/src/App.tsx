import { Fragment, useEffect, useState } from 'react'
import './App.css'

// One event per line from POST /api/runs; see src/custody_lab/demo/server.py.
type Status = 'pending' | 'running' | 'done' | 'failed'
type Detail = Record<string, unknown>

interface DemoEvent {
  step: string
  status: Exclude<Status, 'pending'>
  title: string
  detail: Detail
}

interface StepState {
  status: Status
  detail: Detail // the step's running and done details, merged
}

interface Holder {
  share: number
  pid: number
}

const PENDING: StepState = { status: 'pending', detail: {} }

async function* lines(body: ReadableStream<Uint8Array>): AsyncGenerator<string> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const complete = buffer.split('\n')
    buffer = complete.pop() ?? ''
    yield* complete.filter(Boolean)
  }
  if (buffer) yield buffer
}

function isRecord(value: unknown): value is Detail {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function label(key: string): string {
  return key.replaceAll('_', ' ')
}

function Value({ value }: { value: unknown }) {
  if (typeof value === 'boolean') return <>{value ? 'yes' : 'no'}</>
  if (Array.isArray(value)) {
    if (value.length > 0 && value.every(isRecord)) return <Table rows={value} />
    return <>{value.map(String).join(', ')}</>
  }
  if (isRecord(value)) return <Fields detail={value} />
  return <>{String(value)}</>
}

function Table({ rows }: { rows: Detail[] }) {
  const columns = Object.keys(rows[0])
  return (
    <table>
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c}>{label(c)}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            {columns.map((c) => (
              <td key={c}>
                <Value value={row[c]} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function Fields({ detail }: { detail: Detail }) {
  return (
    <dl className="fields">
      {Object.entries(detail).map(([key, value]) => (
        <Fragment key={key}>
          <dt>{label(key)}</dt>
          <dd>
            {key === 'transcript' && Array.isArray(value) ? (
              <details>
                <summary>{value.length} FIX messages</summary>
                <pre>{value.join('\n')}</pre>
              </details>
            ) : (
              <Value value={value} />
            )}
          </dd>
        </Fragment>
      ))}
    </dl>
  )
}

function Step({ n, title, state }: { n: number; title: string; state: StepState }) {
  return (
    <li className={`step ${state.status}`}>
      <div className="step-head">
        <span className="n">{n}</span>
        <h2>{title}</h2>
        <span className="status">{state.status}</span>
      </div>
      {Object.keys(state.detail).length > 0 && <Fields detail={state.detail} />}
    </li>
  )
}

function signerRole(share: number, sign: StepState | undefined): string {
  if (!sign) return 'idle'
  const chosen = sign.detail.signers as number[] | undefined
  if (!chosen?.includes(share)) return 'not asked'
  if (sign.status === 'done') return 'signed'
  return sign.status === 'failed' ? 'failed' : 'signing'
}

function Signers({ keys, sign }: { keys?: StepState; sign?: StepState }) {
  const holders = (keys?.status === 'done' ? keys.detail.signers : []) as Holder[]
  return (
    <section className="signers">
      <h2>Key shares</h2>
      {holders.length === 0 ? (
        <p className="muted">Key generation has not run.</p>
      ) : (
        <ul>
          {holders.map(({ share, pid }) => {
            const role = signerRole(share, sign)
            return (
              <li key={share} className={`signer ${role.replace(' ', '-')}`}>
                <strong>Signer {share}</strong>
                <span className="role">{role}</span>
                <span>process {pid}</span>
                <span>
                  holds share {share} of {holders.length}
                </span>
              </li>
            )
          })}
        </ul>
      )}
      <p className="muted">
        {keys?.status === 'done' && <>Threshold {String(keys.detail.threshold)}. </>}
        The coordinator, which is the server's own process, relays protocol messages and holds no
        share, so it cannot sign alone.
      </p>
    </section>
  )
}

export default function App() {
  const [steps, setSteps] = useState<[string, string][]>([])
  const [state, setState] = useState<Record<string, StepState>>({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/steps')
      .then((response) => response.json())
      .then((listed: Record<string, string>) => setSteps(Object.entries(listed)))
      .catch(() => setProblem('The demo server is not reachable. Start it: uv run custody-lab serve'))
  }, [])

  async function start() {
    setBusy(true)
    setState({})
    setProblem(null)
    let last: DemoEvent | undefined
    try {
      const response = await fetch('/api/runs', { method: 'POST' })
      if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)
      for await (const line of lines(response.body)) {
        const event = JSON.parse(line) as DemoEvent
        last = event
        setState((previous) => ({
          ...previous,
          [event.step]: {
            status: event.status,
            detail: { ...previous[event.step]?.detail, ...event.detail },
          },
        }))
      }
      if (last?.status === 'running') setProblem(`The stream ended during: ${last.title}`)
    } catch (error) {
      setProblem(`The run stream broke: ${String(error)}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page">
      <header>
        <div>
          <h1>custody-lab</h1>
          <p className="lede">
            A FIX fill settled on a private Bitcoin chain: policy approval, a 2-of-3 threshold
            signature from separate processes, and a proof-of-reserves snapshot.
          </p>
        </div>
        <div className="controls">
          <span className="banner">EDUCATIONAL, NOT PRODUCTION</span>
          <button type="button" onClick={start} disabled={busy || steps.length === 0}>
            {busy ? 'Running' : 'Run the demo'}
          </button>
        </div>
      </header>
      {problem && <p className="problem">{problem}</p>}
      <main>
        <ol className="steps">
          {steps.map(([id, title], i) => (
            <Step key={id} n={i + 1} title={title} state={state[id] ?? PENDING} />
          ))}
        </ol>
        <aside>
          <Signers keys={state.keys} sign={state.sign} />
        </aside>
      </main>
    </div>
  )
}
