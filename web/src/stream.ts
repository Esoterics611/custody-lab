// The server's streaming endpoints answer a POST with one JSON object per line (NDJSON); see
// src/custody_lab/demo/server.py.

export type Status = 'pending' | 'running' | 'done' | 'failed'
export type Detail = Record<string, unknown>

/** One event from POST /api/runs. */
export interface DemoEvent {
  step: string
  status: Exclude<Status, 'pending'>
  title: string
  detail: Detail
  at_ms: number // since the run started, stamped by the server
}

export interface StepState {
  status: Status
  detail: Detail // the step's running and done details, merged
  started?: number // at_ms of the running event
  ended?: number // at_ms of the done or failed event
}

async function* lines(body: ReadableStream<Uint8Array>): AsyncGenerator<string> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const complete = buffer.split('\n')
    buffer = complete.pop() ?? ''
    yield* complete.filter(Boolean)
  }
  if (buffer) yield buffer
}

/** POST `body` to `url` and call `each` with every object the response streams back. */
export async function post<T>(url: string, body: unknown, each: (item: T) => void): Promise<void> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)
  for await (const line of lines(response.body)) each(JSON.parse(line) as T)
}
