import { onBeforeUnmount, onMounted } from 'vue'

export function useManagerShortcuts({ commandPaletteOpen, liveMatch, advance, navigateFromSidebar }) {
  function handleShortcut(event) {
    const key = String(event.key || '').toLowerCase()
    if ((event.ctrlKey || event.metaKey) && key === 'k') {
      event.preventDefault()
      commandPaletteOpen.value = !commandPaletteOpen.value
      return
    }
    if (key === 'escape' && commandPaletteOpen.value) {
      commandPaletteOpen.value = false
      return
    }
    if (event.ctrlKey || event.metaKey || event.altKey) return
    const tag = String(event.target?.tagName || '').toLowerCase()
    if (['input', 'select', 'textarea', 'button'].includes(tag)) return
    const routes = { i:'home', p:'squad', t:'tactics', m:'market', f:'staff', g:'competitions', a:'calendar', n:'news', e:'economy', s:'national', h:'history', r:'career' }
    if (key === 'c' || key === ' ') {
      event.preventDefault()
      advance()
    } else if (routes[key]) navigateFromSidebar(routes[key])
  }

  onMounted(() => window.addEventListener('keydown', handleShortcut))
  onBeforeUnmount(() => window.removeEventListener('keydown', handleShortcut))

  return { handleShortcut }
}
