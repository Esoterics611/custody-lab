import { Fields } from './fields'
import type { Detail, StepState } from './stream'

function duration(state: StepState): string | null {
  if (state.started === undefined || state.ended === undefined) return null
  const ms = state.ended - state.started
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`
}

interface Props {
  n: number
  title: string
  state: StepState
  hidden?: string[] // detail keys shown elsewhere on the page
  children?: React.ReactNode // shown under the details
}

/** One numbered step: its title, status, duration and details. */
export function Step({ n, title, state, hidden = [], children }: Props) {
  const detail: Detail = Object.fromEntries(
    Object.entries(state.detail).filter(([key]) => !hidden.includes(key)),
  )
  return (
    <li className={`step ${state.status}`}>
      <div className="step-head">
        <span className="n">{n}</span>
        <h2>{title}</h2>
        {duration(state) && <span className="time">{duration(state)}</span>}
        <span className="status">{state.status}</span>
      </div>
      {Object.keys(detail).length > 0 && <Fields detail={detail} />}
      {children}
    </li>
  )
}
