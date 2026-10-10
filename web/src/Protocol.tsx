import { useEffect, useRef, useState } from 'react'
import { Hex } from './fields'
import { merge, post, type DemoEvent, type StepState } from './stream'

// The rounds of POST /api/protocol; see src/custody_lab/demo/protocol.py.
type State = Record<string, StepState>
type Kind = 'instruction' | 'clear' | 'sealed' | 'authorisation'

/** One message through the coordinator: messages() in protocol.py. */
interface Message {
  leg: 'out' | 'back' // out: coordinator to signer; back: signer to coordinator
  signer: number
  carries: string
  origin: string
  destination: string
  kind: Kind
  bytes: number
  parts: [string, number][]
  fingerprint?: string
}

// A round plays in up to four phases: requests travel out, the signers work, replies travel
// back, a pause. A round with no message on a leg skips that leg's phase.
type Phase = 'out' | 'work' | 'back' | 'rest'
interface Position {
  round: number
  phase: Phase
  t: number // 0 to 1 through the phase
}

const PHASE_MS: Record<Phase, number> = { out: 1300, work: 650, back: 1300, rest: 1000 }
const SPEEDS = [0.5, 1, 2, 4]
const KINDS: Record<Kind, string> = {
  clear: 'clear',
  sealed: 'sealed',
  authorisation: 'authorisation',
  instruction: 'instruction',
}
const READS: Record<Exclude<Kind, 'instruction'>, string> = {
  clear: 'public by design; it can read them',
  sealed: 'it cannot open any of them',
  authorisation: 'it can read them; an altered copy is refused',
}
const RANK: Kind[] = ['sealed', 'authorisation', 'clear', 'instruction'] // a packet's colour

// The stage, in SVG units: the coordinator at the centre, one spoke to each signer.
const W = 520
const H = 440
const HUB = { x: 260, y: 218, w: 196, h: 78 }
const SIGNERS: Record<number, { x: number; y: number }> = {
  1: { x: 90, y: 60 },
  2: { x: 430, y: 60 },
  3: { x: 260, y: 382 },
}
const NODE = { w: 160, h: 88 }

const messagesOf = (step?: StepState) => (step?.detail.messages as Message[] | undefined) ?? []
const bytes = (n: number) => `${n.toLocaleString('en-GB')} B`
const ease = (t: number) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2)

function phases(step?: StepState): Phase[] {
  const messages = messagesOf(step)
  const list: Phase[] = []
  if (messages.some((m) => m.leg === 'out')) list.push('out')
  list.push('work')
  if (messages.some((m) => m.leg === 'back')) list.push('back')
  list.push('rest')
  return list
}

/** Move the player on by `dt` milliseconds of animation, through as many phases and rounds as
 * that covers; it stops at the end of the last round that has arrived. */
function advance(p: Position, dt: number, rounds: StepState[]): Position {
  if (rounds.length === 0) return p
  let { round, phase, t } = p
  t += dt / PHASE_MS[phase]
  while (t >= 1) {
    const list = phases(rounds[round])
    const next = list.indexOf(phase) + 1
    if (next < list.length) phase = list[next]
    else if (round + 1 < rounds.length) {
      round += 1
      phase = phases(rounds[round])[0]
    } else return { round, phase, t: 1 }
    t -= 1
  }
  return { round, phase, t }
}

/** Has this phase of the round finished, at position `p`? */
function past(p: Position, round: number, phase: Phase): boolean {
  if (round !== p.round) return round < p.round
  const order: Phase[] = ['out', 'work', 'back', 'rest']
  return order.indexOf(p.phase) > order.indexOf(phase)
}

interface Share {
  text: string
  tone: 'idle' | 'ok' | 'bad'
  verifying?: string // the signer's verifying share, its share times G, in hex
}

/** Each signer's share as the player's position has it: a round's effect shows once its
 * signers have done their work. */
function sharesAt(order: string[], state: State, p: Position): Record<number, Share> {
  const shares: Record<number, Share> = {}
  for (const s of [1, 2, 3]) shares[s] = { text: 'no share yet', tone: 'idle' }
  order.forEach((id, i) => {
    if (!past(p, i, 'work') || state[id]?.status !== 'done') return
    const verifying = state[id].detail.verifying_shares as Record<string, string> | undefined
    if (id === 'dkg3' || id === 'refresh3') {
      const period = id === 'dkg3' ? 1 : 2
      for (const s of [1, 2, 3])
        shares[s] = { text: `period ${period} share`, tone: 'ok', verifying: verifying?.[s] }
    }
    if (id === 'lost') shares[2] = { text: 'share lost', tone: 'bad' }
    if (id === 'repair3')
      shares[2] = { text: 'period 2 share, rebuilt', tone: 'ok', verifying: verifying?.['2'] }
  })
  return shares
}

/** Bytes that have reached the coordinator or left it, by kind, at the player's position. */
function relayedAt(order: string[], state: State, p: Position) {
  const totals = { clear: 0, sealed: 0, authorisation: 0, sealedMessages: 0, messages: 0 }
  order.forEach((id, i) => {
    for (const m of messagesOf(state[id])) {
      if (!past(p, i, m.leg === 'out' ? 'out' : 'back')) continue
      totals.messages += 1
      if (m.kind === 'instruction') continue
      totals[m.kind] += m.bytes
      if (m.kind === 'sealed') totals.sealedMessages += 1
    }
  })
  return totals
}

function Lock({ x, y }: { x: number; y: number }) {
  return (
    <g className="lock" transform={`translate(${x} ${y})`}>
      <path d="M-3.5 -1.5 v-2.5 a3.5 3.5 0 0 1 7 0 v2.5" />
      <rect x={-5} y={-1.5} width={10} height={8} rx={1.5} />
    </g>
  )
}

interface Packet {
  signer: number
  kind: Kind
  total: number
  count: number
}

/** One packet per signer and leg: everything that hop carries in this round. */
function packets(messages: Message[], leg: 'out' | 'back'): Packet[] {
  const by = new Map<number, Message[]>()
  for (const m of messages.filter((m) => m.leg === leg))
    by.set(m.signer, [...(by.get(m.signer) ?? []), m])
  return [...by].map(([signer, ms]) => ({
    signer,
    kind: RANK.find((k) => ms.some((m) => m.kind === k)) ?? 'instruction',
    total: ms.reduce((sum, m) => sum + m.bytes, 0),
    count: ms.length,
  }))
}

function PacketMark({ packet, at }: { packet: Packet; at: { x: number; y: number } }) {
  if (packet.kind === 'instruction')
    return <circle className="packet instruction" cx={at.x} cy={at.y} r={7} />
  const label = bytes(packet.total)
  const lock = packet.kind === 'sealed' ? 16 : 0
  const w = 22 + 8.2 * label.length + lock
  return (
    <g className={`packet ${packet.kind}`} transform={`translate(${at.x} ${at.y})`}>
      {packet.count > 1 && (
        <rect className="packet-stack" x={-w / 2 + 5} y={-19} width={w} height={26} rx={13} />
      )}
      <rect x={-w / 2} y={-13} width={w} height={26} rx={13} />
      {lock > 0 && <Lock x={-w / 2 + 16} y={0} />}
      <text x={lock / 2} y={5}>
        {label}
      </text>
    </g>
  )
}

interface StageProps {
  step?: StepState
  position: Position
  shares: Record<number, Share>
  holding: number // sealed messages the coordinator holds between rounds
  processes?: Record<string, number>
}

function Stage({ step, position, shares, holding, processes }: StageProps) {
  const messages = messagesOf(step)
  const addressed = new Set(messages.map((m) => m.signer))
  const aggregating = step !== undefined && messages.length === 0
  const { phase, t } = position
  const leg = phase === 'out' || phase === 'work' ? 'out' : 'back'
  const moving = packets(messages, leg)
  const reduced =
    typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const travel = (p: number) => (reduced ? (p < 0.5 ? 0 : 1) : ease(p))

  function where(signer: number): { x: number; y: number } {
    const s = SIGNERS[signer]
    let f = 0 // 0 at the coordinator's edge, 1 at the signer's
    if (phase === 'out') f = travel(t)
    else if (phase === 'work') f = 1
    else if (phase === 'back') f = 1 - travel(t)
    const along = 0.3 + 0.42 * f
    return { x: HUB.x + (s.x - HUB.x) * along, y: HUB.y + (s.y - HUB.y) * along }
  }

  const signature = step?.detail.signature_valid === true && past(position, position.round, 'work')
  let hubLine = 'relays; holds no share'
  if (aggregating) hubLine = signature ? 'signature verifies' : 'adding signature shares'
  else if (holding > 0) hubLine = `holds ${holding} sealed, unopened`
  const summary =
    `Round: ${String(step?.detail.ceremony ?? '')}. ` +
    moving.map((p) => `${p.count} message${p.count > 1 ? 's' : ''}, ${bytes(p.total)}, ` +
      `${leg === 'out' ? 'to' : 'from'} signer ${p.signer}`).join('; ')
  return (
    <svg className="stage" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={summary}>
      {[1, 2, 3].map((s) => (
        <line
          key={s}
          className={`spoke ${addressed.has(s) ? 'live' : ''}`}
          x1={HUB.x}
          y1={HUB.y}
          x2={SIGNERS[s].x}
          y2={SIGNERS[s].y}
        />
      ))}
      <g className={`node hub ${aggregating && phase === 'work' ? 'busy' : ''}`}>
        <rect x={HUB.x - HUB.w / 2} y={HUB.y - HUB.h / 2} width={HUB.w} height={HUB.h} rx={12} />
        <text className="node-title" x={HUB.x} y={HUB.y - 10}>
          Coordinator
        </text>
        <text className={`node-sub ${holding > 0 && !aggregating ? 'holding' : ''}`} x={HUB.x}
          y={HUB.y + 12}>
          {hubLine}
        </text>
        {processes?.coordinator && (
          <text className="node-mono" x={HUB.x} y={HUB.y + 30}>
            process {processes.coordinator}
          </text>
        )}
      </g>
      {[1, 2, 3].map((s) => {
        const { x, y } = SIGNERS[s]
        const share = shares[s]
        const busy = addressed.has(s) && phase === 'work'
        const quiet = step !== undefined && !aggregating && !addressed.has(s)
        return (
          <g key={s} className={`node signer-node ${share.tone} ${busy ? 'busy' : ''} ${quiet ? 'quiet' : ''}`}>
            <rect x={x - NODE.w / 2} y={y - NODE.h / 2} width={NODE.w} height={NODE.h} rx={12} />
            <text className="node-title" x={x} y={y - 18}>
              Signer {s}
            </text>
            <text className="node-sub" x={x} y={y + 4}>
              {share.text}
            </text>
            <text className="node-mono" x={x} y={y + 24}>
              {share.verifying
                ? `V ${share.verifying.slice(2, 12)}`
                : processes?.[`signer ${s}`]
                  ? `process ${processes[`signer ${s}`]}`
                  : ''}
            </text>
          </g>
        )
      })}
      {phase !== 'rest' && moving.map((p) => <PacketMark key={p.signer} packet={p} at={where(p.signer)} />)}
    </svg>
  )
}

function Anatomy({ message }: { message: Message }) {
  const { parts, kind } = message
  const described = parts.map(([label, n]) => `${label}, ${n} bytes`).join('; ')
  return (
    <figure className={`anatomy ${kind}`}>
      <figcaption>
        <strong>{message.carries}</strong>, {bytes(message.bytes)}, from {message.origin} to{' '}
        {message.destination}
        {message.fingerprint && (
          <>
            {' '}
            (SHA-256 <code>{message.fingerprint}</code>)
          </>
        )}
      </figcaption>
      <div className="anatomy-bar" role="img" aria-label={described}>
        {parts.map(([label, n], i) => (
          <span
            key={i}
            className={`seg seg-${i % 4} ${label.startsWith('ciphertext') ? 'locked' : ''}`}
            style={{ flexGrow: n }}
            title={`${label}: ${n} bytes`}
          />
        ))}
      </div>
      <ol className="anatomy-legend">
        {parts.map(([label, n], i) => (
          <li key={i}>
            <span className={`swatch seg-${i % 4} ${label.startsWith('ciphertext') ? 'locked' : ''}`} />
            {label} <code>{bytes(n)}</code>
          </li>
        ))}
      </ol>
      {kind === 'sealed' && (
        <p className="muted">
          The coordinator relays these {message.bytes} bytes and cannot open them: only{' '}
          {message.destination} holds the key.
        </p>
      )}
    </figure>
  )
}

function hop(m: Message): string {
  return m.leg === 'out' ? `C → ${m.signer}` : `${m.signer} → C`
}

interface RoundProps {
  n: number
  of: number
  title: string
  step: StepState
  live: 'out' | 'back' | null
}

function Round({ n, of, title, step, live }: RoundProps) {
  const messages = messagesOf(step)
  const [chosen, setChosen] = useState<number | null>(null)
  // Shown until one is chosen: the first sealed message, or else the largest.
  const sealedAt = messages.findIndex((m) => m.kind === 'sealed')
  const largest = messages.reduce((best, m, i) => (m.bytes > messages[best].bytes ? i : best), 0)
  const shown = messages[chosen ?? (sealedAt >= 0 ? sealedAt : largest)]
  const { ceremony, explanation, signers, signature, signature_valid: valid, custody_key: key } =
    step.detail as Record<string, unknown>
  const ms = step.started !== undefined && step.ended !== undefined ? step.ended - step.started : null
  return (
    <section className="round card">
      <div className="round-head">
        <span className="chip">{String(ceremony ?? '')}</span>
        <span className="muted">
          Round {n} of {of}
          {ms !== null && `, ${ms < 1 ? 'under 1' : ms} ms`}
        </span>
      </div>
      <h2>{title}</h2>
      {typeof explanation === 'string' && <p>{explanation}</p>}
      {typeof signature === 'string' && (
        <p className={`verdict ${valid ? 'ok' : 'bad'}`}>
          Signers {(signers as number[]).join(' and ')}: a 64-byte BIP340 signature{' '}
          <Hex text={signature} />, {valid ? 'valid' : 'NOT valid'} under the custody key{' '}
          <Hex text={String(key)} />
        </p>
      )}
      {messages.length > 0 && (
        <div className="table-wrap">
          <table className="messages">
            <thead>
              <tr>
                <th>hop</th>
                <th>carries</th>
                <th>from, for</th>
                <th>size</th>
                <th>kind</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((m, i) => (
                <tr
                  key={i}
                  className={`${m.leg === live ? 'live' : ''} ${shown === m ? 'chosen' : ''}`}
                  onClick={() => setChosen(i)}
                >
                  <td className="mono">{hop(m)}</td>
                  <td>
                    {m.kind === 'instruction' ? (
                      m.carries
                    ) : (
                      <button type="button" className="link" onClick={() => setChosen(i)}>
                        {m.carries}
                      </button>
                    )}
                  </td>
                  <td>
                    {m.origin}, for {m.destination}
                  </td>
                  <td className="mono">{m.bytes ? bytes(m.bytes) : ''}</td>
                  <td>
                    <span className={`kind ${m.kind}`}>{KINDS[m.kind]}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {shown && shown.kind !== 'instruction' && <Anatomy message={shown} />}
    </section>
  )
}

function Relayed({ totals }: { totals: ReturnType<typeof relayedAt> }) {
  const all = totals.clear + totals.sealed + totals.authorisation
  const kinds = ['clear', 'sealed', 'authorisation'] as const
  return (
    <section className="relayed card">
      <h2>What passed through the coordinator</h2>
      <div className="relayed-bar" aria-hidden="true">
        {kinds.map((k) => (
          <span key={k} className={`kind-fill ${k}`} style={{ flexGrow: totals[k] }} />
        ))}
      </div>
      <dl>
        {kinds.map((k) => (
          <div key={k}>
            <dt>
              <span className={`kind ${k}`}>{k}</span> {bytes(totals[k])}
              {k === 'sealed' && totals.sealedMessages > 0 && `, ${totals.sealedMessages} messages`}
            </dt>
            <dd className="muted">{READS[k]}</dd>
          </div>
        ))}
      </dl>
      <p className="muted">
        {totals.messages} messages so far. The coordinator holds no share and no signer's channel
        private key.
        {totals.authorisation > 0 &&
          ` So far the authorisations are ${Math.round((100 * totals.authorisation) / all)}% of ` +
            'the bytes: their ML-DSA-65 signatures are post-quantum, and large.'}
      </p>
    </section>
  )
}

interface TimelineProps {
  ceremonies: [string, string[]][]
  order: string[]
  titles: Record<string, string>
  state: State
  available: number
  current: number
  onPick: (round: number) => void
}

function Timeline({ ceremonies, order, titles, state, available, current, onPick }: TimelineProps) {
  return (
    <section className="timeline card">
      <h2>Rounds</h2>
      {ceremonies.map(([name, ids]) => (
        <div key={name}>
          <h3>{name}</h3>
          <ol>
            {ids.map((id) => {
              const i = order.indexOf(id)
              const total = messagesOf(state[id]).reduce((sum, m) => sum + m.bytes, 0)
              const short = titles[id]?.split(': ').slice(1).join(': ') || titles[id]
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
                    <span>{short}</span>
                    {total > 0 && <span className="mono muted">{bytes(total)}</span>}
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

export function Protocol() {
  const [titles, setTitles] = useState<Record<string, string>>({})
  const [ceremonies, setCeremonies] = useState<[string, string[]][]>([])
  const [state, setState] = useState<State>({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)
  const [position, setPosition] = useState<Position>({ round: 0, phase: 'out', t: 0 })
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)

  useEffect(() => {
    Promise.all([fetch('/api/protocol/steps'), fetch('/api/protocol/ceremonies')])
      .then(([steps, grouped]) => Promise.all([steps.json(), grouped.json()]))
      .then(([steps, grouped]: [Record<string, string>, Record<string, string[]>]) => {
        setTitles(steps)
        setCeremonies(Object.entries(grouped))
      })
      .catch(() => setProblem('The demo server is not reachable. Start it: uv run custody-lab serve'))
  }, [])

  const order = Object.keys(titles)
  let available = 0
  while (available < order.length && state[order[available]]?.status === 'done') available += 1
  const finished = available === order.length && order.length > 0 && !busy

  // The animation reads the rounds through refs, so that a round arriving does not restart it.
  const rounds = useRef<StepState[]>([])
  const complete = useRef(false)
  useEffect(() => {
    rounds.current = order.slice(0, available).map((id) => state[id])
    complete.current = finished
  })

  const at = useRef<Position>(position)
  function place(p: Position) {
    at.current = p
    setPosition(p)
  }

  useEffect(() => {
    if (!playing) return
    let frame = 0
    let last = performance.now()
    const tick = (now: number) => {
      const next = advance(at.current, (now - last) * speed, rounds.current)
      last = now
      place(next)
      const end = next.round === rounds.current.length - 1 && next.phase === 'rest' && next.t >= 1
      if (end && complete.current) setPlaying(false)
      else frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [playing, speed])

  function jump(round: number) {
    place({ round, phase: phases(state[order[round]])[0], t: 0 })
  }

  async function start() {
    setBusy(true)
    setState({})
    setProblem(null)
    place({ round: 0, phase: 'out', t: 0 })
    setPlaying(true)
    let last: DemoEvent | undefined
    try {
      await post<DemoEvent>('/api/protocol', {}, (event) => {
        last = event
        setState((previous) => merge(previous, event))
      })
      if (last?.status === 'running') setProblem(`The stream ended during: ${last.title}`)
      if (last?.status === 'failed') setProblem(`The run failed: ${String(last.detail.error)}`)
    } catch (error) {
      setProblem(`The protocol's stream broke: ${String(error)}`)
    } finally {
      setBusy(false)
    }
  }

  function toggle() {
    const atEnd = finished && position.round === order.length - 1 && position.phase === 'rest'
    if (!playing && atEnd) jump(0)
    setPlaying(!playing)
  }

  const id = order[position.round]
  const step = available > 0 ? state[id] : undefined
  const holding = (() => {
    // Sealed replies wait at the coordinator from the end of their round until the next round
    // sends them on.
    const back = messagesOf(step).filter((m) => m.leg === 'back' && m.kind === 'sealed').length
    return position.phase === 'rest' ? back : 0
  })()
  const live = position.phase === 'out' ? 'out' : position.phase === 'back' ? 'back' : null
  const processes = state.channel_peers?.detail.processes as Record<string, number> | undefined
  return (
    <section className="protocol">
      <div className="toolbar card">
        <p>
          Every message of every ceremony, as it passes through the coordinator: the real signing
          processes, the real Zcash Foundation FROST messages, split down to their fields. Watch
          what the coordinator relays and what it cannot open.
        </p>
        <button type="button" onClick={start} disabled={busy || order.length === 0}>
          {busy ? 'Running' : available ? 'Run it again' : 'Run the protocol'}
        </button>
        <div className="player">
          <button
            type="button"
            className="secondary"
            onClick={() => jump(Math.max(0, position.round - 1))}
            disabled={available === 0 || position.round === 0}
          >
            Previous
          </button>
          <button type="button" className="secondary" onClick={toggle} disabled={available === 0}>
            {playing ? 'Pause' : 'Play'}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => jump(Math.min(available - 1, position.round + 1))}
            disabled={position.round >= available - 1}
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
        <div className="protocol-main">
          <div className="card stage-card">
            <Stage
              step={step}
              position={position}
              shares={sharesAt(order, state, position)}
              holding={holding}
              processes={processes}
            />
            <ul className="legend">
              {(['clear', 'sealed', 'authorisation', 'instruction'] as const).map((k) => (
                <li key={k}>
                  <span className={`kind ${k}`}>{k}</span>
                </li>
              ))}
              <li className="muted">V: the signer's verifying share, its share times G</li>
            </ul>
          </div>
          {step && (
            <Round
              key={id}
              n={position.round + 1}
              of={order.length}
              title={titles[id]}
              step={step}
              live={live}
            />
          )}
        </div>
        <aside>
          <Relayed totals={relayedAt(order, state, position)} />
          <Timeline
            ceremonies={ceremonies}
            order={order}
            titles={titles}
            state={state}
            available={available}
            current={available ? position.round : -1}
            onPick={jump}
          />
        </aside>
      </main>
    </section>
  )
}
