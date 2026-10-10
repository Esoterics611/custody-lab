import { useEffect, useRef, useState } from 'react'
import { Hex } from './fields'
import { merge, post, type DemoEvent, type StepState } from './stream'

// The steps of POST /api/audit; see src/custody_lab/demo/audit_trail.py.
type State = Record<string, StepState>

/** One audit entry as the run reports it: its hashed body, canonically encoded, and its hash. */
interface Entry {
  seq: number
  time: string
  event: string
  payload: Record<string, unknown>
  prev_hash: string
  hash: string
  about: string
}

// One row per entry for each of the forger's moves: forgeries() in audit_trail.py.
interface Edited {
  entry: number
  field: string
  before: string
  after: string
  stored_hash: string
  recomputed_hash: string
  breaks_at: number | null
  reason: string
}
interface Relinked {
  entry: number
  breaks_at: number | null
  reason: string
}
interface Rehashed extends Relinked {
  entries: { seq: number; prev_hash: string; hash: string }[] // from the edited entry on
  head: string
}
interface Found {
  snapshot: number
  anchored_entry: number
  anchored_head: string
  copy_hash: string
  found_at: number | null
}
interface Anchored {
  entry: number
  snapshots: Found[]
  exposed_by: number | null
}

// What the forger has done to its copy: nothing, edited one entry, also replaced that entry's
// hash, or re-hashed every entry after it.
type Move = 'none' | 'edited' | 'relinked' | 'rehashed'
const MOVES: [Move, string][] = [
  ['none', 'Untouched'],
  ['edited', 'Edit it'],
  ['relinked', 'Also replace its hash'],
  ['rehashed', 'Re-hash every later entry'],
]
const FORGER = ['edited', 'relinked', 'rehashed', 'anchored']
const MOVE_AT: Record<string, Move> = {
  edited: 'edited',
  relinked: 'relinked',
  rehashed: 'rehashed',
  anchored: 'rehashed',
}
const SNAPSHOTS = ['snapshot_1', 'snapshot_2']
const GENESIS = '0'.repeat(64)
const STEP_MS = 3200
const SPEEDS = [0.5, 1, 2, 4]

const short = (hash: string) => hash.slice(0, 10)
const clock = (iso: string) => `${iso.slice(11, 19)} UTC`
const rows = <T,>(step?: StepState) => (step?.detail.forgeries as T[] | undefined) ?? []

/** A row of the chain as the chosen copy has it. */
interface Shown extends Entry {
  edit?: { field: string; before: string; after: string }
  recomputed?: string // the edited content's hash, where it differs from the stored one
  replaced?: boolean // the stored hash replaced by the forger
  rehashed?: boolean
}

function copyOf(entries: Entry[], state: State, move: Move, k: number): Shown[] {
  const shown: Shown[] = entries.map((e) => ({ ...e }))
  const edit = rows<Edited>(state.edited)[k]
  if (move === 'none' || !edit || !shown[k]) return shown
  shown[k].edit = { field: edit.field, before: edit.before, after: edit.after }
  if (move === 'edited') shown[k].recomputed = edit.recomputed_hash
  if (move === 'relinked') {
    shown[k].hash = edit.recomputed_hash
    shown[k].replaced = true
  }
  if (move === 'rehashed')
    for (const r of rows<Rehashed>(state.rehashed)[k]?.entries ?? []) {
      shown[r.seq] = { ...shown[r.seq], prev_hash: r.prev_hash, hash: r.hash, rehashed: true }
    }
  return shown
}

interface Verdict {
  tone: 'ok' | 'bad' | 'warn'
  text: string
}

/** What verify_chain said of the chosen copy, and what the snapshots' heads say of it. */
function verdicts(state: State, move: Move, k: number, anchorsIn: boolean): Verdict[] {
  if (move === 'none') {
    const said = state.edited?.detail.untouched
    return said ? [{ tone: 'ok', text: `As exported from the policy engine: ${said}.` }] : []
  }
  const row = rows<Relinked>(state[move])[k]
  if (!row) return []
  const said: Verdict[] = [
    row.breaks_at === null
      ? { tone: 'ok', text: 'verify_chain: the copy verifies.' }
      : { tone: 'bad', text: `verify_chain: ${row.reason}.` },
  ]
  if (move === 'relinked' && row.breaks_at === null)
    said.push({ tone: 'warn', text: 'No entry follows the last one, so no link gives it away.' })
  const anchored = rows<Anchored>(state.anchored)[k]
  if (move === 'rehashed' && anchorsIn && anchored)
    said.push(
      anchored.exposed_by
        ? {
            tone: 'bad',
            text:
              `Exposed by snapshot ${anchored.exposed_by}: ` +
              'the head it signed is not in this copy.',
          }
        : {
            tone: 'warn',
            text:
              'Not exposed yet: every anchored head is still in this copy. ' +
              "The next snapshot will anchor the engine's own head.",
          },
    )
  return said
}

function Chain(props: {
  entries: Shown[]
  fresh: Set<number>
  anchors: Record<number, { snapshot: number; head: string }>
  found: Found[]
  brokenAt: number | null
  forged: boolean
  k: number
}) {
  const { entries, fresh, anchors, found, brokenAt, forged, k } = props
  return (
    <section className="card chain-card">
      <h2>{forged ? "The forger's copy" : "The policy engine's audit log"}</h2>
      <ol className="chain">
        <li className="genesis">
          <span className="mono">genesis</span> <code>{short(GENESIS)}</code>
          <span className="muted"> 64 zeros: what entry 0 links to</span>
        </li>
        {entries.map((e, i) => {
          const above = i === 0 ? GENESIS : entries[i - 1].hash
          const linked = e.prev_hash === above
          const anchor = anchors[e.seq]
          const check = found.find((f) => f.anchored_entry === e.seq)
          const contentBroken = e.recomputed !== undefined
          const classes = [
            'entry',
            fresh.has(e.seq) ? 'fresh' : '',
            forged && e.seq === k ? 'edited' : '',
            contentBroken ? 'broken' : '',
            e.rehashed ? 'rehashed' : '',
          ]
          return (
            <li key={e.seq} className="link-and-entry">
              <div className={`link ${linked ? 'ok' : 'bad'}`}>
                {!linked && (
                  <span>
                    entry {e.seq} still links to <code>{short(e.prev_hash)}</code>;{' '}
                    entry {i - 1} now hashes to <code>{short(above)}</code>
                  </span>
                )}
              </div>
              <article
                className={classes.join(' ')}
                aria-current={brokenAt === e.seq || undefined}
              >
                <div className="entry-head">
                  <span className="seq">#{e.seq}</span>
                  <strong>{e.event}</strong>
                  {e.rehashed && <span className="tag re">re-hashed</span>}
                  {e.replaced && <span className="tag re">hash replaced</span>}
                  <span className="muted when">{clock(e.time)}</span>
                </div>
                <p className="about">{e.about}</p>
                {e.edit && (
                  <p className="edit">
                    {e.edit.field}: <s>{e.edit.before}</s> → <strong>{e.edit.after}</strong>
                  </p>
                )}
                <dl className="hashes">
                  <dt>prev</dt>
                  <dd>
                    <code>{short(e.prev_hash)}</code>
                  </dd>
                  <dt>hash</dt>
                  <dd>
                    <code>{short(e.hash)}</code>
                    {contentBroken && (
                      <span className="mismatch">
                        {' '}
                        stored; its content now hashes to <code>{short(e.recomputed!)}</code>
                      </span>
                    )}
                  </dd>
                </dl>
                {anchor && (
                  <p className={`anchor ${check && check.found_at === null ? 'bad' : 'ok'}`}>
                    Snapshot {anchor.snapshot} anchored <code>{short(anchor.head)}</code>
                    {check?.found_at === null && <>: this copy has a different hash here</>}
                    {check && check.found_at !== null && <>: found in this copy</>}
                  </p>
                )}
              </article>
            </li>
          )
        })}
      </ol>
    </section>
  )
}

function Forger(props: {
  entries: Entry[]
  edits: Edited[]
  ready: boolean
  k: number
  move: Move
  onEntry: (k: number) => void
  onMove: (move: Move) => void
  said: Verdict[]
}) {
  const { entries, edits, ready, k, move, onEntry, onMove, said } = props
  return (
    <section className="card forger">
      <h2>The forger's switch</h2>
      {!ready ? (
        <p className="muted">
          From step 8 on: choose an entry of the exported copy and what the forger does to it.
        </p>
      ) : (
        <>
          <label className="pick">
            <span>Entry</span>
            <select value={k} onChange={(event) => onEntry(Number(event.target.value))}>
              {edits.map((edit) => (
                <option key={edit.entry} value={edit.entry}>
                  #{edit.entry} {entries[edit.entry]?.event}: {edit.field} {edit.before} →{' '}
                  {edit.after}
                </option>
              ))}
            </select>
          </label>
          <div className="moves" role="group" aria-label="What the forger does">
            {MOVES.map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={`secondary ${id === move ? 'chosen' : ''}`}
                aria-pressed={id === move}
                onClick={() => onMove(id)}
              >
                {label}
              </button>
            ))}
          </div>
        </>
      )}
      {said.map((v, i) => (
        <p key={i} className={`verdict ${v.tone}`}>
          {v.text}
        </p>
      ))}
    </section>
  )
}

interface AnchorsProps {
  state: State
  visible: Set<string>
  found: Found[]
}

function Anchors({ state, visible, found }: AnchorsProps) {
  const shown = SNAPSHOTS.filter((id) => visible.has(id) && state[id]?.status === 'done')
  return (
    <section className="card anchors">
      <h2>Heads anchored in signed snapshots</h2>
      {shown.length === 0 && <p className="muted">None yet: the first comes at step 5.</p>}
      {shown.map((id, i) => {
        const d = state[id].detail
        const check = found.find((f) => f.snapshot === i + 1)
        return (
          <div key={id} className="anchor-card">
            <strong>Snapshot {i + 1}</strong>
            <span>
              anchors entry {String(d.anchored_entry)}: <Hex text={String(d.audit_head)} />
            </span>
            <span className="muted">
              liabilities {String(d.liabilities)}; the custody key's BIP340 signature{' '}
              {d.signature_valid ? 'verifies' : 'does NOT verify'}
            </span>
            {check && (
              <span className={check.found_at === null ? 'bad' : 'ok'}>
                {check.found_at === null
                  ? `Not in the forger's copy, whose entry ${check.anchored_entry} is ` +
                    `${short(check.copy_hash)}: exposed`
                  : `Found in the forger's copy at entry ${check.found_at}`}
              </span>
            )}
          </div>
        )
      })}
    </section>
  )
}

interface StepProps {
  n: number
  of: number
  title: string
  step: StepState
}

function StepCard({ n, of, title, step }: StepProps) {
  const d = step.detail
  const ms = step.started !== undefined && step.ended !== undefined ? step.ended - step.started : null
  const moved = d.moved_heads as { snapshot: number; signature_valid: boolean }[] | undefined
  const processes = d.processes as Record<string, number> | undefined
  return (
    <section className="round card">
      <div className="round-head">
        <span className="chip">
          {n > of - FORGER.length ? "A forger's copy" : 'Two settlements'}
        </span>
        <span className="muted">
          Step {n} of {of}
          {ms !== null && `, ${ms < 1 ? 'under 1' : ms} ms`}
        </span>
      </div>
      <h2>{title}</h2>
      {typeof d.explanation === 'string' && <p>{d.explanation}</p>}
      {typeof d.decision === 'string' && (
        <p className={`verdict ${d.decision.startsWith('denied') ? 'bad' : 'warn'}`}>
          Policy engine: {d.decision}
        </p>
      )}
      {d.signature_valid === true && Array.isArray(d.signers) && (
        <p className="verdict ok">
          Signers {(d.signers as number[]).join(' and ')} signed under authorisation{' '}
          <code>{String(d.authorisation_id).slice(0, 8)}</code>; the signature verifies under the
          custody key.
        </p>
      )}
      {typeof d.anchored_entry === 'number' && (
        <p className="verdict ok">
          The snapshot carries entry {d.anchored_entry}'s hash,{' '}
          <code>{short(String(d.audit_head))}</code>, and the custody key's signature over it
          verifies.
        </p>
      )}
      {moved?.map((m) => (
        <p key={m.snapshot} className={`verdict ${m.signature_valid ? 'ok' : 'bad'}`}>
          Snapshot {m.snapshot} with its head replaced by the copy's, entry {String(d.shown)}{' '}
          edited and re-hashed: the custody key's signature{' '}
          {m.signature_valid ? 'still verifies' : 'no longer verifies'}.
        </p>
      ))}
      {processes && (
        <p className="muted">
          Processes:{' '}
          {Object.entries(processes)
            .map(([who, pid]) => `${who} ${pid}`)
            .join(', ')}
          .
        </p>
      )}
    </section>
  )
}

function Steps(props: {
  order: string[]
  titles: Record<string, string>
  available: number
  current: number
  onPick: (i: number) => void
}) {
  const { order, titles, available, current, onPick } = props
  const parts: [string, string[]][] = [
    ['Two settlements', order.filter((id) => !FORGER.includes(id))],
    ["A forger's copy", order.filter((id) => FORGER.includes(id))],
  ]
  return (
    <section className="timeline card">
      <h2>Steps</h2>
      {parts.map(([name, ids]) => (
        <div key={name}>
          <h3>{name}</h3>
          <ol>
            {ids.map((id) => {
              const i = order.indexOf(id)
              const when = i < current ? 'played' : i === current ? 'current' : ''
              return (
                <li key={id}>
                  <button
                    type="button"
                    className={when}
                    disabled={i >= available}
                    onClick={() => onPick(i)}
                  >
                    <span className="n">{i + 1}</span>
                    <span>{titles[id]}</span>
                  </button>
                </li>
              )
            })}
          </ol>
        </div>
      ))}
    </section>
  )
}

export function AuditTrail() {
  const [titles, setTitles] = useState<Record<string, string>>({})
  const [state, setState] = useState<State>({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)
  const [position, setPosition] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [k, setK] = useState(2)
  const [move, setMove] = useState<Move>('none')

  useEffect(() => {
    fetch('/api/audit/steps')
      .then((response) => response.json())
      .then((listed: Record<string, string>) => setTitles(listed))
      .catch(() => setProblem('The demo server is not reachable. Start it: uv run custody-lab serve'))
  }, [])

  const order = Object.keys(titles)
  let available = 0
  while (available < order.length && state[order[available]]?.status === 'done') available += 1
  const finished = available === order.length && order.length > 0 && !busy

  // The player reads its position and how far the run has got through refs, so that a step
  // arriving does not restart it.
  const shownEntry = Number(state.edited?.detail.shown ?? 2)
  const reach = useRef({ available, finished, order, shownEntry })
  useEffect(() => {
    reach.current = { available, finished, order, shownEntry }
  })
  const at = useRef(position)
  /** Move the player to step `p`. Reaching one of the forger's steps sets the switch to that
   * step's move on the entry the run names; the reader may change it after. */
  function place(p: number) {
    at.current = p
    setPosition(p)
    const reached = reach.current.order[p]
    setMove(MOVE_AT[reached] ?? 'none')
    if (reached in MOVE_AT) setK(reach.current.shownEntry)
  }

  useEffect(() => {
    if (!playing) return
    const timer = setInterval(() => {
      if (at.current + 1 < reach.current.available) place(at.current + 1)
      else if (reach.current.finished) setPlaying(false)
    }, STEP_MS / speed)
    return () => clearInterval(timer)
  }, [playing, speed])


  async function start() {
    setBusy(true)
    setState({})
    setProblem(null)
    place(0)
    setPlaying(true)
    let last: DemoEvent | undefined
    try {
      await post<DemoEvent>('/api/audit', {}, (event) => {
        last = event
        setState((previous) => merge(previous, event))
      })
      if (last?.status === 'running') setProblem(`The stream ended during: ${last.title}`)
      if (last?.status === 'failed') setProblem(`The run failed: ${String(last.detail.error)}`)
    } catch (error) {
      setProblem(`The audit log's stream broke: ${String(error)}`)
    } finally {
      setBusy(false)
    }
  }

  function toggle() {
    if (!playing && finished && position === order.length - 1) place(0)
    setPlaying(!playing)
  }

  const id = order[position]
  const visible = new Set(available > 0 ? order.slice(0, position + 1) : [])
  const entries = order
    .filter((s) => visible.has(s))
    .flatMap((s) => (state[s]?.detail.entries as Entry[] | undefined) ?? [])
  const added = (state[id]?.detail.entries as Entry[] | undefined) ?? []
  const fresh = new Set(added.map((e) => e.seq))
  const ready = visible.has('edited') && state.edited?.status === 'done'
  const forged = ready && move !== 'none'
  const shown = forged ? copyOf(entries, state, move, k) : entries
  const anchorsIn = visible.has('anchored') && state.anchored?.status === 'done'
  const checked = forged && move === 'rehashed' && anchorsIn
  const found = checked ? (rows<Anchored>(state.anchored)[k]?.snapshots ?? []) : []
  const anchors: Record<number, { snapshot: number; head: string }> = {}
  SNAPSHOTS.forEach((s, i) => {
    const d = state[s]?.detail
    if (visible.has(s) && typeof d?.anchored_entry === 'number')
      anchors[d.anchored_entry] = { snapshot: i + 1, head: String(d.audit_head) }
  })
  const said = ready ? verdicts(state, forged ? move : 'none', k, anchorsIn) : []
  const brokenAt = forged ? (rows<Relinked>(state[move])[k]?.breaks_at ?? null) : null
  const step = available > 0 ? state[id] : undefined
  return (
    <section className="audit">
      <div className="toolbar card">
        <p>
          Every entry the policy engine writes to its audit log through two settlements, each
          linked to the one before by its hash, and two reserves snapshots that carry the log's
          head under the custody key's signature. Then a forger edits a copy of the log: see where
          the chain breaks, and which snapshot exposes a copy re-hashed to hide the edit.
        </p>
        <button type="button" onClick={start} disabled={busy || order.length === 0}>
          {busy ? 'Running' : available ? 'Run it again' : 'Run the settlements'}
        </button>
        <div className="player">
          <button
            type="button"
            className="secondary"
            onClick={() => place(Math.max(0, position - 1))}
            disabled={available === 0 || position === 0}
          >
            Previous
          </button>
          <button type="button" className="secondary" onClick={toggle} disabled={available === 0}>
            {playing ? 'Pause' : 'Play'}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => place(Math.min(available - 1, position + 1))}
            disabled={position >= available - 1}
          >
            Next
          </button>
          <span className="speeds" role="group" aria-label="Speed">
            {SPEEDS.map((s) => (
              <button
                key={s}
                type="button"
                className={`secondary ${s === speed ? 'chosen' : ''}`}
                aria-pressed={s === speed}
                onClick={() => setSpeed(s)}
              >
                {s}×
              </button>
            ))}
          </span>
        </div>
      </div>
      {problem && <p className="problem">{problem}</p>}
      <main>
        <div className="audit-main">
          {step && <StepCard n={position + 1} of={order.length} title={titles[id]} step={step} />}
          <Forger
            entries={entries}
            edits={rows<Edited>(state.edited)}
            ready={ready}
            k={k}
            move={move}
            onEntry={setK}
            onMove={setMove}
            said={said}
          />
          <Chain
            entries={shown}
            fresh={fresh}
            anchors={anchors}
            found={found}
            brokenAt={brokenAt}
            forged={forged}
            k={k}
          />
        </div>
        <aside>
          <Anchors state={state} visible={visible} found={found} />
          <Steps
            order={order}
            titles={titles}
            available={available}
            current={available ? position : -1}
            onPick={place}
          />
        </aside>
      </main>
    </section>
  )
}
