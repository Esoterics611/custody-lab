import { Fragment, useState } from 'react'
import type { Detail } from './stream'

// Hashes, keys, signatures and addresses: 40 or more letters and digits with no break.
const LONG = /([0-9a-z]{40,})/i

function isRecord(value: unknown): value is Detail {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function label(key: string): string {
  return key.replaceAll('_', ' ')
}

/** A long value shown by its ends, with the whole value on hover and a copy button. */
export function Hex({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1200)
    } catch {
      // clipboard refused (not a secure context); the value is still in the tooltip
    }
  }
  return (
    <span className="hex" title={text}>
      <code>
        {text.slice(0, 10)}…{text.slice(-8)}
      </code>
      <button type="button" className="copy" onClick={copy} aria-label={`Copy ${text}`}>
        {copied ? 'copied' : 'copy'}
      </button>
    </span>
  )
}

export function Text({ text }: { text: string }) {
  const parts = text.split(LONG)
  return <>{parts.map((part, i) => (i % 2 ? <Hex key={i} text={part} /> : part))}</>
}

function Value({ value }: { value: unknown }) {
  if (typeof value === 'boolean') return <>{value ? 'yes' : 'no'}</>
  if (Array.isArray(value)) {
    if (value.length === 0) return <>none</>
    if (value.every(isRecord)) return <Table rows={value} />
    return <>{value.map(String).join(', ')}</>
  }
  if (isRecord(value)) return <Fields detail={value} />
  return <Text text={String(value)} />
}

function Table({ rows }: { rows: Detail[] }) {
  const columns = Object.keys(rows[0])
  return (
    <div className="table-wrap">
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
    </div>
  )
}

export function Fields({ detail }: { detail: Detail }) {
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
