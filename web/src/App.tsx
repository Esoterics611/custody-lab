import { useEffect, useState } from 'react'
import './App.css'
import { Attacks } from './Attacks'
import { BalanceCheck } from './BalanceCheck'
import { Day } from './Day'
import { Text } from './fields'
import { Flow } from './Flow'
import { Signers } from './Signers'
import { Step } from './steps'
import { PENDING, merge, post, type DemoEvent, type StepState } from './stream'

const LONGEST_PAUSE_MS = 700 // a replay shortens longer gaps, such as bitcoind starting

// One entry of GET /api/runs.
interface Recorded {
  run: string
  ended: string
  offline: number[]
}

const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))
const TABS = {
  run: 'Settlement run',
  day: 'A day at the custodian',
  attacks: 'Attack the design',
  check: "Check a client's balance",
}
type Tab = keyof typeof TABS

function RunStep(props: { n: number; title: string; state: StepState; onCheck: () => void }) {
  const { inclusion_proofs: proofs } = props.state.detail
  return (
    <Step {...props} hidden={['inclusion_proofs', 'snapshot_document']}>
      {Array.isArray(proofs) && (
        <button type="button" className="link" onClick={props.onCheck}>
          {proofs.length} inclusion proofs published: check one in this browser
        </button>
      )}
    </Step>
  )
}

function Summary({ state, onCheck }: { state: Record<string, StepState>; onCheck: () => void }) {
  if (state.reserves?.status !== 'done') return null
  const { net, broadcast, reserves, sign } = state
  return (
    <div className="summary">
      <p>
        <strong>Settled.</strong> {String(net?.detail.client_delivers)} paid to the exchange,
        signed by signers {(sign?.detail.signers as number[] | undefined)?.join(' and ')} in
        transaction{' '}
        <Text text={String(broadcast?.detail.txid)} />, confirmed on the regtest chain. Reserve
        ratio {String(reserves.detail.reserve_ratio)}: assets {String(reserves.detail.assets)},
        liabilities {String(reserves.detail.liabilities)}.
      </p>
      <button type="button" className="secondary" onClick={onCheck}>
        Check a client's balance
      </button>
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState<Tab>('run')
  const [steps, setSteps] = useState<[string, string][]>([])
  const [state, setState] = useState<Record<string, StepState>>({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)
  const [offline, setOffline] = useState<number[]>([])
  const [recorded, setRecorded] = useState<Recorded[]>([])
  const [chosen, setChosen] = useState('')
  const [replayed, setReplayed] = useState<string | null>(null) // the run on screen, if replayed

  function listRecorded() {
    fetch('/api/runs')
      .then((response) => response.json())
      .then((listed: Recorded[]) => setRecorded(listed))
      .catch(() => setRecorded([]))
  }

  useEffect(() => {
    fetch('/api/steps')
      .then((response) => response.json())
      .then((listed: Record<string, string>) => setSteps(Object.entries(listed)))
      .catch(() => setProblem('The demo server is not reachable. Start it: uv run custody-lab serve'))
    listRecorded()
  }, [])

  function toggle(share: number) {
    setOffline((now) =>
      now.includes(share) ? now.filter((s) => s !== share) : [...now, share].sort(),
    )
  }

  function apply(event: DemoEvent) {
    setState((previous) => merge(previous, event))
  }

  async function start() {
    setBusy(true)
    setState({})
    setProblem(null)
    setReplayed(null)
    let last: DemoEvent | undefined
    try {
      await post<DemoEvent>('/api/runs', { offline }, (event) => {
        last = event
        apply(event)
      })
      if (last?.status === 'running') setProblem(`The stream ended during: ${last.title}`)
    } catch (error) {
      setProblem(`The run stream broke: ${String(error)}`)
    } finally {
      setBusy(false)
      listRecorded()
    }
  }

  async function replay(run: string) {
    setBusy(true)
    setState({})
    setProblem(null)
    setReplayed(run)
    try {
      const response = await fetch(`/api/runs/${encodeURIComponent(run)}`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      let previous = 0
      for (const event of (await response.json()) as DemoEvent[]) {
        const gap = event.at_ms === undefined ? 150 : event.at_ms - previous
        await pause(Math.min(gap, LONGEST_PAUSE_MS))
        previous = event.at_ms ?? previous
        apply(event)
      }
    } catch (error) {
      setProblem(`The recorded run could not be read: ${String(error)}`)
    } finally {
      setBusy(false)
    }
  }

  const done = steps.filter(([id]) => state[id]?.status === 'done').length
  const check = () => setTab('check')
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
        <span className="banner">EDUCATIONAL, NOT PRODUCTION</span>
      </header>

      {tab === 'run' && <Flow state={state} />}

      <nav className="tabs" role="tablist">
        {(Object.keys(TABS) as Tab[]).map((id) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={tab === id ? 'chosen' : ''}
            onClick={() => setTab(id)}
          >
            {TABS[id]}
          </button>
        ))}
      </nav>

      {problem && <p className="problem">{problem}</p>}

      <div hidden={tab !== 'run'}>
        <main>
          <div>
            <div className="toolbar card">
              <button type="button" onClick={start} disabled={busy || steps.length === 0}>
                {busy ? (replayed ? 'Replaying' : 'Running') : 'Run the demo'}
              </button>
              <div className="progress" aria-label={`${done} of ${steps.length} steps done`}>
                <div style={{ width: `${(100 * done) / Math.max(steps.length, 1)}%` }} />
              </div>
              <span className="muted">
                {done} of {steps.length} steps
              </span>
              {recorded.length > 0 && (
                <div className="replay">
                  <select
                    value={chosen}
                    onChange={(event) => setChosen(event.target.value)}
                    disabled={busy}
                    aria-label="Recorded run"
                  >
                    <option value="">Replay a recorded run</option>
                    {recorded.map(({ run, ended, offline: off }) => (
                      <option key={run} value={run}>
                        {run.slice(0, 16)}: {ended}
                        {off.length > 0 && `, signer${off.length > 1 ? 's' : ''} ${off.join(' and ')} offline`}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => replay(chosen)}
                    disabled={busy || !chosen}
                  >
                    Replay
                  </button>
                </div>
              )}
            </div>
            {replayed && (
              <p className="replayed">
                Replaying recorded run {replayed}, from <code>var/demo/{replayed}/events.jsonl</code>.
                Durations are as recorded; pauses longer than {LONGEST_PAUSE_MS} ms are shortened.
              </p>
            )}
            <Summary state={state} onCheck={check} />
            <ol className="steps">
              {steps.map(([id, title], i) => (
                <RunStep
                  key={id}
                  n={i + 1}
                  title={title}
                  state={state[id] ?? PENDING}
                  onCheck={check}
                />
              ))}
            </ol>
          </div>
          <aside>
            <Signers
              keys={state.keys}
              sign={state.sign}
              reserves={state.reserves}
              offline={offline}
              onToggle={toggle}
              locked={busy}
            />
          </aside>
        </main>
      </div>
      {/* every tab stays mounted, so a tab's results survive switching away from it */}
      <div hidden={tab !== 'day'}>
        <Day />
      </div>
      <div hidden={tab !== 'attacks'}>
        <Attacks />
      </div>
      <div hidden={tab !== 'check'}>
        <BalanceCheck reserves={state.reserves} />
      </div>
    </div>
  )
}
