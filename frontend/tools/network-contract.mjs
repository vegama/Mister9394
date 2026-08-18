import { createFootballRequestTransport } from '../src/football9394/requestTransport.js'

const wait = ms => new Promise(resolve => setTimeout(resolve, ms))
const response = (body, { ok = true, status = 200 } = {}) => ({
  ok,
  status,
  async text() { return typeof body === 'string' ? body : JSON.stringify(body) },
})

const failures = []
const check = (condition, label) => {
  if (!condition) failures.push(label)
  else console.log(`PASS ${label}`)
}

// Duplicate destructive requests must share one in-flight operation.
{
  let calls = 0
  const transport = createFootballRequestTransport({
    fetchImpl: async () => { calls += 1; await wait(20); return response({ ok: true }) },
    slowMs: 200,
    timeoutMs: 1000,
  })
  const options = { method: 'POST', body: JSON.stringify({ player_id: 7 }) }
  const first = transport.request('/negotiations', options)
  const second = transport.request('/negotiations', options)
  check(first === second, 'double-click shares same promise')
  await Promise.all([first, second])
  check(calls === 1, 'double-click performs one mutation')
}

// GET requests are not deduplicated because they can represent independent refreshes.
{
  let calls = 0
  const transport = createFootballRequestTransport({ fetchImpl: async () => { calls += 1; return response({ ok: true }) } })
  await Promise.all([transport.request('/career'), transport.request('/career')])
  check(calls === 2, 'GET refreshes remain independent')
}

// Slow-state feedback appears after the threshold and always clears.
{
  let slow = 0
  let pending = 0
  const transport = createFootballRequestTransport({
    fetchImpl: async () => { await wait(30); return response({ ok: true }) },
    slowMs: 5,
    timeoutMs: 500,
    onSlow: delta => { slow += delta },
    onPending: delta => { pending += delta },
  })
  const request = transport.request('/slow')
  await wait(12)
  check(slow === 1 && pending === 1, 'slow request exposes progress state')
  await request
  check(slow === 0 && pending === 0, 'slow/pending state clears after success')
}

// Offline / unreachable backend becomes player-facing copy.
{
  let lastError = ''
  const transport = createFootballRequestTransport({
    fetchImpl: async () => { throw new TypeError('Failed to fetch') },
    onError: message => { if (message) lastError = message },
  })
  try { await transport.request('/offline') } catch (error) {
    check(error.message.includes('No se puede conectar con el juego'), 'offline error is player-facing')
  }
  check(lastError.includes('No se puede conectar con el juego'), 'offline error reaches global feedback state')
}

// Timeout must abort and explain what the player should do.
{
  const transport = createFootballRequestTransport({
    fetchImpl: (_path, options) => new Promise((_resolve, reject) => {
      options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
    }),
    slowMs: 5,
    timeoutMs: 15,
  })
  const started = Date.now()
  try { await transport.request('/timeout', { method: 'POST' }) } catch (error) {
    check(error.message.includes('tardando demasiado'), 'timeout uses actionable copy')
    check(Date.now() - started < 250, 'timeout aborts instead of hanging')
  }
}

// Technical 500 copy must not leak raw internal terminology.
{
  const transport = createFootballRequestTransport({
    fetchImpl: async () => response({ detail: 'Internal Server Error' }, { ok: false, status: 500 }),
  })
  try { await transport.request('/broken') } catch (error) {
    check(error.message === 'No se pudo completar la operación (HTTP 500).', 'HTTP 500 is sanitized')
  }
}

if (failures.length) {
  console.error('Network contract FAILED')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}
console.log('Network contract PASS: dedupe + slow feedback + offline + timeout + sanitized server errors')
