function defaultFetch(...args) {
  return fetch(...args)
}

export function userFacingRequestError(error, { timedOut = false } = {}) {
  if (timedOut) return new Error('La operación está tardando demasiado. El servidor sigue sin responder; vuelve a intentarlo sin repetir varias veces la acción.')
  if (error instanceof TypeError) return new Error('No se puede conectar con el juego. Comprueba que Míster 93/94 siga abierto y vuelve a intentarlo.')
  return error instanceof Error ? error : new Error(String(error || 'No se pudo completar la operación.'))
}

export function mutationKey(path, options) {
  const method = String(options?.method || 'GET').toUpperCase()
  if (method === 'GET' || method === 'HEAD') return ''
  return `${method}:${path}:${String(options?.body || '')}`
}

export function createFootballRequestTransport({
  fetchImpl = defaultFetch,
  slowMs = 500,
  timeoutMs = 15000,
  onPending = () => {},
  onSlow = () => {},
  onError = () => {},
} = {}) {
  const inflightMutations = new Map()

  async function perform(path, options = {}) {
    onPending(1)
    onError('')
    let slow = false
    let timedOut = false
    const controller = new AbortController()
    const slowTimer = setTimeout(() => {
      slow = true
      onSlow(1)
    }, slowMs)
    const timeoutTimer = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, timeoutMs)
    try {
      const response = await fetchImpl(path, {
        headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
        ...options,
        signal: options.signal || controller.signal,
      })
      const text = await response.text()
      let body = null
      try { body = text ? JSON.parse(text) : null } catch { body = { detail: text || 'Respuesta no válida' } }
      if (!response.ok) {
        const detail = String(body?.detail || '').trim()
        const safeDetail = !detail || /^(internal server error|null|undefined|exception)$/i.test(detail)
          ? `No se pudo completar la operación (HTTP ${response.status}).`
          : detail
        throw new Error(safeDetail)
      }
      return body
    } catch (error) {
      const friendly = userFacingRequestError(error, { timedOut })
      onError(friendly.message)
      throw friendly
    } finally {
      clearTimeout(slowTimer)
      clearTimeout(timeoutTimer)
      if (slow) onSlow(-1)
      onPending(-1)
    }
  }

  function request(path, options = {}) {
    const key = mutationKey(path, options)
    if (key && inflightMutations.has(key)) return inflightMutations.get(key)
    const operation = perform(path, options)
    if (key) {
      inflightMutations.set(key, operation)
      operation.finally(() => {
        if (inflightMutations.get(key) === operation) inflightMutations.delete(key)
      }).catch(() => {})
    }
    return operation
  }

  return { request, inflightMutations }
}
