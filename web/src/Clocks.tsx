import { useEffect, useState } from 'react'
import { Step } from './steps'
import { PENDING, merge, post, type DemoEvent, type StepState } from './stream'

// The steps of POST /api/clocks; see src/custody_lab/demo/clocks.py.
type State = Record<string, StepState>
type Tone = 'idle' | 'ok' | 'bad'

// Where the true time and each signer's reading fall in an authorisation's life, in seconds from
// its issue: _lifetime() in clocks.py.
interface Lifetime {
  life_s: number
  true_s: number
  readings_s: Record<string, number>
  read_from: string
}

const SCALE_S = 360 // every bar spans six minutes, so bars compare at a glance
const done = (state: State, step: string) => state[step]?.status === 'done'

function seconds(s: number): string {
  return s < 10 ? `${s.toFixed(2)} s` : `${Math.round(s)} s`
}

/** The authorisation's 60-second life as a band, the true time as a line, each signer's reading
 * as a numbered mark. */
function LifetimeBar({ lifetime }: { lifetime: Lifetime }) {
  const scale = Math.max(SCALE_S, lifetime.true_s, ...Object.values(lifetime.readings_s)) * 1.02
  const at = (s: number) => `${(100 * Math.max(0, s)) / scale}%`
  const mark = (s: number) => `clamp(9px, ${at(s)}, calc(100% - 9px))` // keep a mark's label inside
  const readings = Object.entries(lifetime.readings_s)
  const said = readings
    .map(([signer, s]) => `signer ${signer} ${s < lifetime.life_s ? 'inside' : 'after'} it`)
    .join(', ')
  const summary =
    `The authorisation lives ${lifetime.life_s} s. The true time is ${seconds(lifetime.true_s)} ` +
    `after its issue. Read from ${lifetime.read_from}: ${said}.`
  return (
    <figure className="lifetime">
      <div className="lifetime-axis" role="img" aria-label={summary}>
        <div className="lifetime-life" style={{ width: at(lifetime.life_s) }} />
        <div className="lifetime-true" style={{ left: at(lifetime.true_s) }} />
        {readings.map(([signer, s], i) => (
          <span
            key={signer}
            className={`lifetime-mark ${s < lifetime.life_s ? 'inside' : 'after'}`}
            style={{ left: mark(s), top: `${3 + 18 * i}px` }}
          >
            {signer}
          </span>
        ))}
      </div>
      <figcaption className="muted">
        Green: its {lifetime.life_s} s of life from issue. Line: the true time,{' '}
        {seconds(lifetime.true_s)} after issue. Numbered: where each signer's time put it, read
        from {lifetime.read_from}.
      </figcaption>
    </figure>
  )
}

function clock(state: State, signer: number): [string, Tone] {
  if (!done(state, 'setup')) return ['not started', 'idle']
  if (signer === 1 && done(state, 'one_clock')) return ['set back five minutes', 'bad']
  if (signer === 3 && done(state, 'both_clocks')) return ['set back five minutes', 'bad']
  return ['reads its own clock: correct', 'ok']
}

function WhoseClock({ state }: { state: State }) {
  const started = done(state, 'setup')
  return (
    <section className="signers card">
      <h2>Where each signer reads the time</h2>
      <p className="muted">Own clocks: the first set of signers</p>
      <ul>
        {[1, 3].map((signer) => {
          const [text, tone] = clock(state, signer)
          return (
            <li key={signer} className={`signer ${tone}`}>
              <strong>Signer {signer}</strong>
              <span className="role">{text}</span>
            </li>
          )
        })}
      </ul>
      <p className="muted">Signed time: the second set of signers</p>
      <ul>
        {[1, 3].map((signer) => (
          <li key={signer} className={`signer ${started ? 'ok' : 'idle'}`}>
            <strong>Signer {signer}</strong>
            <span className="role">
              {started ? "the time authority's signed time" : 'not started'}
            </span>
            {done(state, 'attested') && (
              <span className="muted">its machine's clock is set back too, and not read</span>
            )}
          </li>
        ))}
        <li className={`signer ${started ? 'ok' : 'idle'}`}>
          <strong>Time authority</strong>
          <span className="role">{started ? 'signs the time with each nonce' : 'not started'}</span>
        </li>
      </ul>
    </section>
  )
}

export function Clocks() {
  const [steps, setSteps] = useState<[string, string][]>([])
  const [state, setState] = useState<State>({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/clocks/steps')
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
      await post<DemoEvent>('/api/clocks', {}, (event) => {
        last = event
        setState((previous) => merge(previous, event))
      })
      if (last?.status === 'running') setProblem(`The stream ended during: ${last.title}`)
    } catch (error) {
      setProblem(`The clocks' stream broke: ${String(error)}`)
    } finally {
      setBusy(false)
    }
  }

  const finished = steps.filter(([id]) => done(state, id)).length
  return (
    <section className="clocks">
      <div className="toolbar card">
        <p>
          Every authorisation lives 60 seconds, and each signer checks that against the time. An
          authorisation held back five minutes is refused, until an attacker sets both signers'
          clocks back. Signers that read a time authority's signed time instead refuse it whatever
          their clocks say, and refuse a signed time that answers another request.
        </p>
        <button type="button" onClick={start} disabled={busy || steps.length === 0}>
          {busy ? 'Running' : finished ? 'Run the clocks again' : 'Run the clocks'}
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
          {steps.map(([id, title], i) => {
            const step = state[id] ?? PENDING
            const lifetime = step.detail.lifetime as Lifetime | undefined
            return (
              <Step key={id} n={i + 1} title={title} state={step} hidden={['lifetime']}>
                {lifetime && <LifetimeBar lifetime={lifetime} />}
              </Step>
            )
          })}
        </ol>
        <aside>
          <WhoseClock state={state} />
        </aside>
      </main>
    </section>
  )
}
