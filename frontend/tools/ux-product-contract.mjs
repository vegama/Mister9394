import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

const root = process.cwd()
const problems = []
const read = file => readFileSync(resolve(root, file), 'utf8')
const requireText = (file, markers, label=file) => {
  const text = read(file)
  for (const marker of markers) if (!text.includes(marker)) problems.push(`${label}: falta ${marker}`)
}

for (const file of [
  'src/components/ui/UiPageHeader.vue',
  'src/components/ui/UiActionDock.vue',
  'src/components/ui/UiProcessTrail.vue',
  'src/components/ui/UiEmptyState.vue',
  'src/components/ui/UiDataTable.vue',
  'src/football9394/components/DecisionFocusBar.vue',
  'src/football9394/components/ManagerCommandPalette.vue',
  'src/football9394/components/FirstRunGuide.vue',
  'src/football9394/composables/useEntityNavigation.js',
  'src/football9394/composables/useFirstRunGuide.js',
  'src/football9394/composables/useManagerShortcuts.js',
  'src/football9394/navigationRoute.js',
  'src/football9394/requestTransport.js',
  'src/features/football9394/FootballTeamProfileModal.vue',
  'src/features/football9394/FootballMatchContextModal.vue',
  'src/styles/football9394-primitives.css',
]) if (!existsSync(resolve(root, file))) problems.push(`falta primitiva UX: ${file}`)

requireText('src/football9394/navigationRoute.js', ['parseNavigationHash', 'buildNavigationHash', 'safeEntityTab', 'ENTITY_TYPES'], 'serialización de ruta')
requireText('src/football9394/composables/useNavigationContext.js', [
  "label: 'HOY'", "label: 'EQUIPO'", "label: 'CLUB'", "label: 'TEMPORADA'", "label: 'CARRERA Y MUNDO'",
  'popstate', 'hashchange', 'history.pushState', 'routeEntity', 'routeEntityTab', 'setEntityTab', 'canGoBack', 'navigateBack', 'openEntityRoute', 'closeEntityRoute', 'parseNavigationHash', 'buildNavigationHash',
], 'arquitectura/navegación')
requireText('src/football9394/Football9394App.vue', [
  'ManagerCommandPalette', 'DecisionFocusBar', 'decisionFocus', 'openDecision', 'FootballTeamProfileModal', 'FootballMatchContextModal', 'useEntityNavigation', 'footballNetworkState', 'retryRouteEntity', 'Saltar al contenido', 'id="m9394-main"',
], 'shell de producto')
requireText('src/football9394/composables/useEntityNavigation.js', ['syncRouteEntity', 'careerPlayer', 'careerTeam', 'careerCalendar', 'routeEntityTab', 'setEntityTab'], 'navegación de entidades')
requireText('src/football9394/composables/useFirstRunGuide.js', ['mister9394:first-run-guide:v1', 'matches_managed'], 'estado onboarding')
requireText('src/football9394/composables/useManagerShortcuts.js', ['commandPaletteOpen', 'navigateFromSidebar', "key === 'c'"], 'atajos expertos')
requireText('src/football9394/components/ManagerTopbar.vue', ['Ctrl/⌘ + K', '<kbd>Ctrl K</kbd>', 'Ir a…', 'canGoBack', 'Volver al contexto anterior'], 'Topbar')
requireText('src/football9394/components/ManagerCommandPalette.vue', ['ArrowDown', 'ArrowUp', 'aria-activedescendant', 'keyboard-active', 'trapTab', 'focusBeforeOpen', 'aria-modal="true"'], 'Palette experta/accesible')
requireText('src/football9394/components/FirstRunGuide.vue', ['PRIMER DÍA', '11 + 5', 'Ctrl/⌘ + K', 'open-decision'], 'Onboarding contextual')
requireText('src/football9394/components/SquadWorkspace.vue', [
  'UiPageHeader', 'UiDataTable', 'UiEmptyState', 'UiActionDock', "mister9394:squad-view:v1", 'sessionStorage.setItem',
], 'Plantilla')
requireText('src/football9394/components/TacticsWorkspace.vue', [
  'UiPageHeader', 'UiProcessTrail', 'UiActionDock', 'Plan para la 2ª parte',
], 'Tácticas')
requireText('src/football9394/components/MarketWorkspace.vue', [
  'UiPageHeader', 'UiProcessTrail', 'UiEmptyState', 'UiActionDock', 'Aceptar oferta',
], 'Mercado')
requireText('src/football9394/components/StaffWorkspace.vue', ['UiPageHeader', 'UiEmptyState', 'Ir al área'], 'Staff')
requireText('src/football9394/components/TrainingWorkspace.vue', ['UiPageHeader', 'UiProcessTrail', 'UiActionDock', 'trainingProcessSteps'], 'Entrenamiento')
requireText('src/football9394/components/CalendarWorkspace.vue', ['UiPageHeader', 'UiDataTable', 'UiEmptyState', 'Sin partido programado', 'open-match', 'open-team'], 'Calendario')
requireText('src/football9394/components/NewsWorkspace.vue', ['UiPageHeader', 'UiEmptyState', 'hechos suficientes', 'open-entity', 'Ver jugador', 'Ver club', 'Ver competición'], 'Noticias')
requireText('src/football9394/components/CompetitionsWorkspace.vue', ['UiPageHeader', 'UiDataTable', 'UiEmptyState', 'open-team'], 'Competiciones')
requireText('src/features/football9394/FootballPlayerProfileModal.vue', ['open-team', 'Ver club →'], 'Ficha jugador')
requireText('src/features/football9394/FootballTeamProfileModal.vue', ['open-player', 'open-team', 'open-competition', 'PLANTILLA ACTUAL DE LA PARTIDA'], 'Ficha club')
requireText('src/features/football9394/FootballMatchContextModal.vue', ['open-team', 'SIGUIENTE PASO', 'Preparar el partido'], 'Ficha partido')
requireText('src/football9394/components/CareerWorkspace.vue', ['UiPageHeader', 'UiEmptyState'], 'Carrera')
requireText('src/football9394/api.js', ['footballNetworkState', 'slowRequests', 'createFootballRequestTransport'], 'Estado de red')
requireText('src/football9394/requestTransport.js', ['timeoutMs = 15000', 'slowMs = 500', 'inflightMutations', 'No se puede conectar con el juego', 'userFacingRequestError'], 'Red, timeout y doble envío')
requireText('src/styles/football9394-product.css', ['entity-route-error', 'network-slow-indicator', 'topbar-back', 'm9394-skip-link', 'clip-path:inset(50%)'], 'Feedback runtime/accesibilidad')
requireText('src/styles/football9394-shell.css', ['position:fixed;left:0;right:0;top:auto;bottom:0', 'overscroll-behavior-x:contain', 'env(safe-area-inset-bottom)'], 'Responsive móvil/zoom')

const primitives = read('src/styles/football9394-primitives.css')
for (const m of primitives.matchAll(/font-size\s*:\s*(\d+(?:\.\d+)?)px/gi)) {
  if (Number(m[1]) < 11) problems.push(`primitivas: tamaño ${m[1]}px por debajo del suelo de 11px`)
}
if (!primitives.includes('prefers-reduced-motion')) problems.push('primitivas: falta soporte prefers-reduced-motion')
if (!primitives.includes(':focus-visible')) problems.push('primitivas: falta contrato focus-visible')

if (problems.length) {
  console.error('UX product contract FAILED')
  for (const p of problems) console.error(`- ${p}`)
  process.exit(1)
}
console.log('UX product contract PASS: navigation + entities + runtime feedback + onboarding + keyboard accessibility + core workspaces')
