import { useEffect, useState } from 'react'
import { BooksPanel } from './Books'
import { Step } from './steps'
import { PENDING, lastTwoBooks, merge, post, type DemoEvent, type StepState } from './stream'

// The steps of POST /api/redteam; see src/custody_lab/demo/redteam.py.
export function RedTeam() {
  const [steps, setSteps] = useState<[string, string][]>([])
  const [state, setState] = useState<Record<string, StepState>>({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/redteam/steps')
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
      await post<DemoEvent>('/api/redteam', {}, (event) => {
        last = event
        setState((previous) => merge(previous, event))
      })
      if (last?.status === 'running') setProblem(`The stream ended during: ${last.title}`)
    } catch (error) {
      setProblem(`The red team's stream broke: ${String(error)}`)
    } finally {
      setBusy(false)
    }
  }

  const [books, before] = lastTwoBooks(steps, state)
  const finished = steps.filter(([id]) => state[id]?.status === 'done').length
  return (
    <section className="day redteam">
      <div className="toolbar card">
        <p>
          Two attacks on a private chain, each first against a weak rule and then against the
          defence. A deposit credited at one confirmation is taken back by a reorganised chain;
          credited at three, it never is. A withdrawal sent to another client's registered address
          passes devices that sign blind; devices that check the destination refuse it.
        </p>
        <button type="button" onClick={start} disabled={busy || steps.length === 0}>
          {busy ? 'Attacking' : finished ? 'Run the red team again' : 'Run the red team'}
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
            <Step key={id} n={i + 1} title={title} state={state[id] ?? PENDING} hidden={['books']} />
          ))}
        </ol>
        <aside>
          <BooksPanel books={books} before={before} />
        </aside>
      </main>
    </section>
  )
}
