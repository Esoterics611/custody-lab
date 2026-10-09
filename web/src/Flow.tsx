import type { Status, StepState } from './stream'

// The path of one settlement through the design, left to right, and the steps that light each
// stage. Chapter 0 draws the same path.
const STAGES: { name: string; note: string; steps: string[] }[] = [
  { name: 'Exchange', note: 'FIX fills', steps: ['trade'] },
  { name: 'Netting', note: 'one instruction', steps: ['net'] },
  { name: 'Policy', note: 'two approvals', steps: ['policy'] },
  { name: 'Signers', note: 'any 2 of 3', steps: ['keys', 'sign'] },
  { name: 'Bitcoin', note: 'regtest', steps: ['chain', 'fund', 'broadcast'] },
  { name: 'Reserves', note: 'proof published', steps: ['reserves'] },
]

// 'partial': some of the stage's steps are done and none is running, as Bitcoin is between
// funding (step 3) and broadcast (step 8).
function stage(steps: string[], state: Record<string, StepState>): Status | 'partial' {
  const statuses = steps.map((s) => state[s]?.status ?? 'pending')
  if (statuses.includes('failed')) return 'failed'
  if (statuses.includes('running')) return 'running'
  if (statuses.every((s) => s === 'done')) return 'done'
  return statuses.includes('done') ? 'partial' : 'pending'
}

export function Flow({ state }: { state: Record<string, StepState> }) {
  return (
    <ol className="flow" aria-label="Where the run is">
      {STAGES.map(({ name, note, steps }) => (
        <li key={name} className={stage(steps, state)}>
          <strong>{name}</strong>
          <span>{note}</span>
        </li>
      ))}
    </ol>
  )
}
