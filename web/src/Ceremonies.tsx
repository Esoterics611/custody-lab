import { useEffect, useState } from 'react'
import { Step } from './steps'
import { PENDING, merge, post, type DemoEvent, type StepState } from './stream'

// The steps of POST /api/ceremonies; see src/custody_lab/demo/ceremonies.py.
type State = Record<string, StepState>
type Tone = 'idle' | 'busy' | 'ok' | 'off' | 'bad'

const done = (state: State, step: string) => state[step]?.status === 'done'

function share(state: State, signer: number): [string, Tone] {
  if (!done(state, 'keys')) return ['no share yet', 'idle']
  const period = done(state, 'refresh') ? 2 : 1
  if (signer === 2 && done(state, 'lost') && !done(state, 'repair')) return ['share lost', 'bad']
  if (signer === 2 && done(state, 'repair')) return [`period ${period} share, rebuilt`, 'ok']
  if (state.refresh?.status === 'running') return ['refreshing its share', 'busy']
  return [`period ${period} share`, period === 2 ? 'ok' : 'idle']
}

function Holders({ state }: { state: State }) {
  const stolen: string[] = []
  if (done(state, 'one_share')) stolen.push("signer 1's share, period 1")
  if (done(state, 'mixed')) stolen.push("signer 3's share, period 2")
  const verdict = done(state, 'mixed')
    ? 'Cannot sign: its two shares are from different periods.'
    : done(state, 'one_share')
      ? 'Cannot sign: one share is not enough.'
      : 'Holds nothing yet.'
  return (
    <section className="signers card">
      <h2>Who holds what</h2>
      <ul>
        {[1, 2, 3].map((signer) => {
          const [text, tone] = share(state, signer)
          return (
            <li key={signer} className={`signer ${tone}`}>
              <strong>Signer {signer}</strong>
              <span className="role">{text}</span>
            </li>
          )
        })}
        <li className={`signer ${stolen.length ? 'bad' : 'idle'}`}>
          <strong>The thief</strong>
          {stolen.length === 0 ? (
            <span className="role">nothing</span>
          ) : (
            stolen.map((s) => (
              <span key={s} className="role">
                {s}
              </span>
            ))
          )}
          <span className="muted">{verdict}</span>
        </li>
      </ul>
      {done(state, 'same_period') && (
        <p className="muted">
          Had the thief taken signer 3's share before the refresh, the two period-1 shares would
          have been the key: a refresh shortens the time a thief has to collect two shares; it
          does not undo a theft of two.
        </p>
      )}
      {done(state, 'refresh') && (
        <p className="muted">
          The group key and the custody address are the same before and after the refresh.
        </p>
      )}
    </section>
  )
}

export function Ceremonies() {
  const [steps, setSteps] = useState<[string, string][]>([])
  const [state, setState] = useState<State>({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/ceremonies/steps')
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
      await post<DemoEvent>('/api/ceremonies', {}, (event) => {
        last = event
        setState((previous) => merge(previous, event))
      })
      if (last?.status === 'running') setProblem(`The stream ended during: ${last.title}`)
    } catch (error) {
      setProblem(`The ceremonies' stream broke: ${String(error)}`)
    } finally {
      setBusy(false)
    }
  }

  const finished = steps.filter(([id]) => done(state, id)).length
  return (
    <section className="ceremonies">
      <div className="toolbar card">
        <p>
          Two key ceremonies on the real signing processes, with no chain. A thief copies one
          share, the signers refresh their shares, and the thief's old share no longer combines
          with a new one. Then signer 2 loses its share, and signers 1 and 3 rebuild it without
          revealing their own.
        </p>
        <button type="button" onClick={start} disabled={busy || steps.length === 0}>
          {busy ? 'Running the ceremonies' : finished ? 'Run them again' : 'Run the ceremonies'}
        </button>
        <div className="progress" aria-label={`${finished} of ${steps.length} steps done`}>
          <div style={{ width: `${(100 * finished) / Math.max(steps.length, 1)}%` }} />
        </div>
        <span className="muted">
          {finished} of {steps.length} steps
        </span>
      </div>
      {problem && <p className="problem">{problem}</p>}
      <main>
        <ol className="steps">
          {steps.map(([id, title], i) => (
            <Step key={id} n={i + 1} title={title} state={state[id] ?? PENDING} />
          ))}
        </ol>
        <aside>
          <Holders state={state} />
        </aside>
      </main>
    </section>
  )
}
