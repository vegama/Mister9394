export const ENTITY_TYPES = new Set(['player', 'team', 'competition', 'match'])
const ENTITY_TAB = /^[a-z][a-z0-9-]{0,31}$/

export function safeEntityTab(value) {
  const tab = String(value || '')
  return ENTITY_TAB.test(tab) ? tab : ''
}

export function parseNavigationHash(hash = window.location.hash) {
  const raw = String(hash || '').replace(/^#/, '')
  const queryAt = raw.indexOf('?')
  const path = queryAt >= 0 ? raw.slice(0, queryAt) : raw
  const search = queryAt >= 0 ? raw.slice(queryAt + 1) : ''
  const parts = path.split('/').filter(Boolean)
  const target = parts[0] || 'home'
  let entity = null
  if (parts.length >= 3 && ENTITY_TYPES.has(parts[1])) {
    try {
      entity = { type: parts[1], id: decodeURIComponent(parts.slice(2).join('/')) }
    } catch {
      entity = null
    }
  }
  let entityTab = ''
  try {
    entityTab = safeEntityTab(new URLSearchParams(search).get('entityTab'))
  } catch {}
  return { target, entity, entityTab }
}

export function buildNavigationHash(target, entity = null, { entityTab = '' } = {}) {
  const base = `#${target}`
  const path = entity?.type && entity?.id != null
    ? `${base}/${entity.type}/${encodeURIComponent(String(entity.id))}`
    : base
  const tab = safeEntityTab(entityTab)
  return tab && entity ? `${path}?entityTab=${encodeURIComponent(tab)}` : path
}
