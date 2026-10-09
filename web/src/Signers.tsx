import type { StepState } from './stream'

// The demo's three share holders and its threshold, as in src/custody_lab/demo/pipeline.py.
const SHARES = [1, 2, 3]
const THRESHOLD = 2

interface Holder {
  share: number
  pid: number
}

interface Props {
  keys?: StepState
  sign?: StepState
  reserves?: StepState
  offline: number[] // chosen for the next run, or the current run's while it is going
  onToggle: (share: number) => void
  locked: boolean
}

type Role = { text: string; tone: 'idle' | 'busy' | 'ok' | 'off' | 'bad' }

function role(share: number, { keys, sign, reserves, offline }: Props): Role {
  if (sign) {
    if ((sign.detail.offline as number[] | undefined)?.includes(share))
      return { text: 'offline: process stopped', tone: 'off' }
    if (!(sign.detail.signers as number[] | undefined)?.includes(share))
      return { text: 'online, not asked', tone: 'idle' }
    if (sign.status === 'failed') return { text: 'could not sign alone', tone: 'bad' }
    if (sign.status === 'running') return { text: 'signing the payment', tone: 'busy' }
    if (reserves?.status === 'running') return { text: 'signing the snapshot', tone: 'busy' }
    if (reserves?.status === 'done') return { text: 'signed payment and snapshot', tone: 'ok' }
    return { text: 'signed the payment', tone: 'ok' }
  }
  if (offline.includes(share)) return { text: 'stops before step 7', tone: 'off' }
  if (keys?.status === 'running') return { text: 'generating its share', tone: 'busy' }
  if (keys?.status === 'done') return { text: 'holds its share', tone: 'idle' }
  return { text: 'not started', tone: 'idle' }
}

export function Signers(props: Props) {
  const { keys, offline, onToggle, locked } = props
  const holders = (keys?.status === 'done' ? keys.detail.signers : []) as Holder[]
  const pid = (share: number) => holders.find((h) => h.share === share)?.pid
  const online = SHARES.length - offline.length
  return (
    <section className="signers card">
      <h2>Key shares</h2>
      <ul>
        {SHARES.map((share) => {
          const { text, tone } = role(share, props)
          const up = !offline.includes(share)
          return (
            <li key={share} className={`signer ${tone}`}>
              <div className="signer-head">
                <strong>Signer {share}</strong>
                <label className="switch" title="Online at step 7">
                  <input
                    type="checkbox"
                    checked={up}
                    disabled={locked}
                    onChange={() => onToggle(share)}
                  />
                  <span>{up ? 'online' : 'offline'}</span>
                </label>
              </div>
              <span className="role">{text}</span>
              <span className="muted">
                {pid(share) ? `process ${pid(share)}, share ${share} of 3` : `share ${share} of 3`}
              </span>
            </li>
          )
        })}
      </ul>
      <p className={online < THRESHOLD ? 'warning' : 'muted'}>
        Any {THRESHOLD} of {SHARES.length} sign. The switches set who is online at step 7 of the
        next run:{' '}
        {online < THRESHOLD
          ? `with ${online} online, step 7 fails and no coins move.`
          : `${online} online.`}
      </p>
      <p className="muted">
        The coordinator, which is the server's own process, relays protocol messages and holds no
        share, so it cannot sign alone. Key-generation sub-shares pass through it sealed to their
        recipient, so it cannot read them.
      </p>
    </section>
  )
}
