import { readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'

const files = [
  'src/styles/core.css',
  ...readdirSync(resolve(process.cwd(), 'src/styles'))
    .filter(name => name.startsWith('football9394-') && name.endsWith('.css'))
    .map(name => `src/styles/${name}`),
]
const problems = []
for (const file of files) {
  const text = readFileSync(resolve(process.cwd(), file), 'utf8')
  for (const match of text.matchAll(/font-size\s*:\s*(\d+(?:\.\d+)?)px/gi)) {
    const size = Number(match[1])
    if (size < 11) problems.push(`${file}: tamaño tipográfico ${size}px por debajo del suelo de 11px`)
  }
  const legacyPatterns = [
    [/Georgia\s*,|Times New Roman/i, 'tipografía serif retro'],
    [/box-shadow\s*:\s*inset\s+-?1px\s+-?1px/i, 'bisel retro'],
    [/#c9c7bd|#b9bab1|#113a76/i, 'paleta legacy de la ficha 0.3.1'],
  ]
  for (const [pattern, label] of legacyPatterns) if (pattern.test(text)) problems.push(`${file}: reaparece ${label}`)
}


const requiredWorkspaces = [
  'src/football9394/components/HomeDashboard.vue',
  'src/football9394/components/SquadWorkspace.vue',
  'src/football9394/components/LineupPitch.vue',
  'src/football9394/components/TacticsWorkspace.vue',
  'src/football9394/components/LiveMatchWorkspace.vue',
  'src/football9394/components/MarketWorkspace.vue',
  'src/football9394/components/CompetitionsWorkspace.vue',
  'src/football9394/components/EconomyWorkspace.vue',
  'src/football9394/components/NewsWorkspace.vue',
  'src/football9394/components/NationalWorkspace.vue',
  'src/football9394/components/ClubWorkspace.vue',
  'src/football9394/components/HistoryWorkspace.vue',
  'src/football9394/components/CalendarWorkspace.vue',
  'src/football9394/components/CareerSetup.vue',
]
for (const file of requiredWorkspaces) {
  try { readFileSync(resolve(process.cwd(), file), 'utf8') }
  catch { problems.push(`falta workspace moderno requerido: ${file}`) }
}
const rootApp = readFileSync(resolve(process.cwd(), 'src/football9394/Football9394App.vue'), 'utf8')
const navigationContext = readFileSync(resolve(process.cwd(), 'src/football9394/composables/useNavigationContext.js'), 'utf8')
const navigationSurface = `${rootApp}\n${navigationContext}`
const entityPresentation = readFileSync(resolve(process.cwd(), 'src/football9394/entityPresentation.js'), 'utf8')
for (const legacyInline of [
  `<section v-if="view==='home'"`,
  `<section v-else-if="view==='squad'"`,
  `<section v-else-if="view==='tactics'"`,
  `<section v-else-if="view==='match'"`,
  `<section v-else-if="view==='market'"`,
  `<section v-else-if="view==='competitions'"`,
  `<section v-else-if="view==='economy'"`,
  `<section v-else-if="view==='news'"`,
  `<section v-else-if="view==='national'"`,
  `<section v-else-if="view==='club'"`,
  `<section v-else-if="view==='history'"`,
  `<section v-else-if="view==='calendar'"`,
]) {
  if (rootApp.includes(legacyInline)) problems.push(`workspace core ha vuelto al monolito raíz: ${legacyInline}`)
}


const setup = readFileSync(resolve(process.cwd(), 'src/football9394/components/CareerSetup.vue'), 'utf8')
for (const required of ['career-browser','league-choice','club-choice','setup-stadium-cover']) {
  if (!setup.includes(required)) problems.push(`R8 incompleto: falta ${required} en CareerSetup`)
}
for (const required of ['popstate','hashchange','history.pushState','isAdvancing']) {
  if (!navigationSurface.includes(required)) problems.push(`R9 incompleto: falta ${required} en navegación/continuar`)
}


// D1-D3 reference-surface contract: the modern product must present football
// identity before generic admin cards. These markers intentionally describe
// composition, not implementation details, so refactors can preserve the gate.
const playerProfile = readFileSync(resolve(process.cwd(), 'src/features/football9394/FootballPlayerProfileModal.vue'), 'utf8')
for (const required of ['player-hero-v2','player-overview-v2','player-position-pitch','player-story-card','player-ability-card']) {
  if (!playerProfile.includes(required)) problems.push(`D2 ficha jugador incompleta: falta ${required}`)
}
for (const forbidden of ['★★★★★','Muy bueno</']) {
  if (playerProfile.includes(forbidden)) problems.push(`D2 ficha jugador vuelve a una valoración redundante: ${forbidden}`)
}

const clubWorkspace = readFileSync(resolve(process.cwd(), 'src/football9394/components/ClubWorkspace.vue'), 'utf8')
for (const required of ['club-hq','club-hero-v2','club-lineup-layout','club-star-grid','source-manager-body']) {
  if (!clubWorkspace.includes(required)) problems.push(`D3 ficha club incompleta: falta ${required}`)
}
for (const required of ['LineupPitch','nextMatch','sourceManager','venue','tacticalIdentity']) {
  if (!clubWorkspace.includes(required)) problems.push(`D3 club deja de priorizar contexto futbolístico: falta ${required}`)
}


// D4-D8 propagation contract: football-first hierarchy must extend beyond the
// two reference cards into the daily loop, squad/tactics, market and matchday.
const homeDashboard = readFileSync(resolve(process.cwd(), 'src/football9394/components/HomeDashboard.vue'), 'utf8')
for (const required of ['home-command-center','home-matchday-hero','home-decisions-v2','home-squad-story','home-news-v2']) {
  if (!homeDashboard.includes(required)) problems.push(`D4 Inicio incompleto: falta ${required}`)
}
const squadWorkspace = readFileSync(resolve(process.cwd(), 'src/football9394/components/SquadWorkspace.vue'), 'utf8')
for (const required of ['d6-squad-pulse','lineupFit','tensions','fragileStarters']) {
  if (!squadWorkspace.includes(required)) problems.push(`D6 Plantilla no expone decisiones profundas: falta ${required}`)
}
const tacticsWorkspace = readFileSync(resolve(process.cwd(), 'src/football9394/components/TacticsWorkspace.vue'), 'utf8')
for (const required of ['d6-tactical-fit','tactical-people-layer','averageFit','weakFits']) {
  if (!tacticsWorkspace.includes(required)) problems.push(`D6 Táctica no explica quién ejecuta el plan: falta ${required}`)
}
const marketWorkspace = readFileSync(resolve(process.cwd(), 'src/football9394/components/MarketWorkspace.vue'), 'utf8')
for (const required of ['d6-market-fit','tactical_fit?.reasons']) {
  if (!marketWorkspace.includes(required)) problems.push(`D6 Mercado no explica el encaje: falta ${required}`)
}
const liveWorkspace = readFileSync(resolve(process.cwd(), 'src/football9394/components/LiveMatchWorkspace.vue'), 'utf8')
for (const required of ['d7-match-preview','d7-match-post','d8-world-context','opponent_context','refereeStyle','decisiveEvents']) {
  if (!liveWorkspace.includes(required)) problems.push(`D7-D8 jornada de partido incompleta: falta ${required}`)
}

// v1.0 Wave 2: the core daily loop must be state-aware and reversible before kickoff.
for (const required of ['home-readiness-strip','runPrimaryMatchAction','selectionReady','isMatchDay']) {
  if (!homeDashboard.includes(required)) problems.push(`v1.0 Inicio no orienta el siguiente paso: falta ${required}`)
}
for (const required of ['lineup-flow-actions','hasLineupChanges','Guardar y abrir táctica']) {
  if (!squadWorkspace.includes(required)) problems.push(`v1.0 XI/Plantilla pierde continuidad: falta ${required}`)
}
for (const required of ['match-prep-flow','Guardar e ir a la previa','open-squad','start-live']) {
  if (!tacticsWorkspace.includes(required)) problems.push(`v1.0 Táctica pierde el flujo XI→previa: falta ${required}`)
}
for (const required of ['Revisar XI','preflight-note','edit-lineup','post-impact','CONSECUENCIAS YA APLICADAS','NOTAS DEL EQUIPO']) {
  if (!liveWorkspace.includes(required)) problems.push(`v1.0 Previa no permite corrección segura: falta ${required}`)
}
for (const required of ['lineupDirty','isMatchDay','cancelPreviewAndNavigate','cancelLivePreview','commitFinishedLiveMatch','Hay una acción de partido en curso','El partido está en juego. Usa Directo, Táctica o Cambios']) {
  if (!rootApp.includes(required)) problems.push(`v1.0 continuidad del bucle principal no conectada: falta ${required}`)
}
// v1.0 Wave 3 destructive navigation + match incident contract. Reload and
// browser history must restore the only safe match surface, while the bench
// must expose historical substitution limits and irreversible dismissals.
for (const required of ['reconcileRouteAfterCareerLoad','replaceRoute','lastMatchReport.value?.committed','applyRouteFromLocation']) {
  if (!navigationSurface.includes(required)) problems.push(`v1.0 navegación destructiva no protegida: falta ${required}`)
}
for (const required of ['controlled_sent_off','substitutionsRemaining','Descanso · revisa táctica y cambios',"match.minute>0 && match.status!=='finished'",'Sin cambios disponibles']) {
  if (!liveWorkspace.includes(required)) problems.push(`v1.0 incidencias de partido no protegidas: falta ${required}`)
}
// v1.0 Wave 4: chained edge cases must be visible, not merely simulated.
for (const required of ['controlled_forced_off','controlled_absences','injury_forced_off','no puede continuar','replaceablePlayers','Bajas conocidas antes del partido']) {
  if (!liveWorkspace.includes(required)) problems.push(`v1.0 lesión sin cambios no está explicada en el banquillo: falta ${required}`)
}
for (const required of ['liveStatus','atHalftime','Plan para la 2ª parte','Aplicar para la 2ª parte','briefing.own_absences','TUS BAJAS']) {
  if (!tacticsWorkspace.includes(required)) problems.push(`v1.0 ajuste táctico de descanso no está contextualizado: falta ${required}`)
}
const calendarWorkspace = readFileSync(resolve(process.cwd(), 'src/football9394/components/CalendarWorkspace.vue'), 'utf8')
for (const required of ['calendarState','Sin partido programado','availability_count']) {
  if (!calendarWorkspace.includes(required)) problems.push(`v1.0 calendario vacío/aplazado no tiene estado explícito: falta ${required}`)
}
for (const required of ['league_suspension_active_for_next_match','Sanción para el próximo partido de liga']) {
  if (!playerProfile.includes(required)) problems.push(`v1.0 ficha no explica la sanción activa: falta ${required}`)
}
for (const required of ['calendar_context','Rival por confirmar','availability_count']) {
  if (!rootApp.includes(required) && !homeDashboard.includes(required) && !entityPresentation.includes(required)) problems.push(`v1.0 disponibilidad/calendario no comparten contexto: falta ${required}`)
}

// V1.0-I daily UX: Home must separate actionable decisions from work that is
// merely in progress, explain why Continue stops, and preserve everyday context.
for (const required of ['home-blocking-note','Quién está trabajando y qué falta','QUÉ CAMBIÓ','decision-next','decision-impact']) {
  if (!homeDashboard.includes(required)) problems.push(`V1.0-I Inicio no explica el trabajo cotidiano: falta ${required}`)
}
for (const required of ['blocking_decisions','continue_status','persistDailyWorkspace','restoreDailyWorkspace','Continuar detenido']) {
  if (!rootApp.includes(required)) problems.push(`V1.0-I Continuar/persistencia no está conectado: falta ${required}`)
}
// V1.0-J match closure: the post-match view must expose the complete league
// round and the consequence chain, and Home must keep that round visible.
for (const required of ['RESULTADOS DE LA COMPETICIÓN','roundSummary','nextAbsences','BAJAS PARA EL SIGUIENTE PARTIDO']) {
  if (!liveWorkspace.includes(required)) problems.push(`V1.0-J postpartido incompleto: falta ${required}`)
}
for (const required of ['lastMatchReport','lastRoundResults','ÚLTIMA JORNADA','home-round-grid']) {
  if (!homeDashboard.includes(required) && !rootApp.includes(required)) problems.push(`V1.0-J resultados de jornada no persisten en Inicio: falta ${required}`)
}

const topbar = readFileSync(resolve(process.cwd(), 'src/football9394/components/ManagerTopbar.vue'), 'utf8')
for (const required of ['continueStatus',"continueStatus?.state==='blocked'","continueStatus?.label || 'Continuar'"]) {
  if (!topbar.includes(required) && !rootApp.includes(required)) problems.push(`V1.0-I topbar no comunica la interrupción: falta ${required}`)
}

// D9 Chromium layout fixes discovered by the 1920x1080 visual pass. The
// preview must carry useful team information instead of an empty commentary
// canvas, finished matches must not keep dead substitution controls, and the
// tactical execution list must be bounded so Save remains on screen.
for (const required of ['d9-preflight-selection', "match.status!=='finished'", "match.minute>0"]) {
  if (!liveWorkspace.includes(required)) problems.push(`D9 partido vuelve a desperdiciar el viewport: falta ${required}`)
}

// v0.10 living-career contract: the simulation must expose persistent memory,
// not merely transient widgets.
for (const required of ['home-storyline-strip','careerRecords','storylineArchive']) {
  if (!rootApp.includes(required) && !homeDashboard.includes(required)) problems.push(`v0.10 memoria de carrera incompleta: falta ${required}`)
}
for (const required of ['career-memory-card','MEMORIA DE TU ETAPA']) {
  if (!clubWorkspace.includes(required)) problems.push(`v0.10 Club no conserva memoria del mánager: falta ${required}`)
}
const newsWorkspace = readFileSync(resolve(process.cwd(), 'src/football9394/components/NewsWorkspace.vue'), 'utf8')
for (const required of ['managerWorld','manager-carousel','Mercado de banquillos']) {
  if (!newsWorkspace.includes(required)) problems.push(`v0.10 mundo de entrenadores no visible: falta ${required}`)
}
const historyWorkspace = readFileSync(resolve(process.cwd(), 'src/football9394/components/HistoryWorkspace.vue'), 'utf8')
for (const required of ['career-story-archive','careerRecords','storylineArchive','Récords personales']) {
  if (!historyWorkspace.includes(required)) problems.push(`v0.10 Historia no archiva la partida viva: falta ${required}`)
}

// v0.11 manager mobility: dismissal must open a career decision instead of a game-over wall.
for (const required of ['managerCareer','manager-career-crossroads','accept-job','TU CARRERA CONTINÚA']) {
  if (!clubWorkspace.includes(required)) problems.push(`v0.11 movilidad del mánager incompleta: falta ${required}`)
}
for (const required of ['managerCareer','manager-career-path','TRAYECTORIA DEL MÁNAGER']) {
  if (!historyWorkspace.includes(required)) problems.push(`v0.11 trayectoria del mánager no visible: falta ${required}`)
}
for (const required of ['acceptManagerJob','userManager']) {
  if (!rootApp.includes(required)) problems.push(`v0.11 flujo de cambio de club no conectado: falta ${required}`)
}


// v0.15 frozen-age + dressing-room contract. Frozen age must be a deliberate
// career choice and the squad surface must expose social football depth.
for (const required of ['frozen_attributes_dynamic','Reparto eterno','cantera/newgens']) {
  if (!setup.includes(required)) problems.push(`v0.15 edad congelada incompleta en Nueva carrera: falta ${required}`)
}
for (const required of ['dressing-room-card','captain-badge','BATALLAS POR EL PUESTO','TUTELAS']) {
  if (!squadWorkspace.includes(required)) problems.push(`v0.15 vestuario profundo incompleto: falta ${required}`)
}
for (const required of ['dressingRoom','appointCaptain','setCaptain']) {
  if (!rootApp.includes(required)) problems.push(`v0.15 capitanía/vestuario no conectado: falta ${required}`)
}
for (const required of ['role-promise-line','ROL ACORDADO','Acordar un rol','promise-role']) {
  if (!playerProfile.includes(required)) problems.push(`v0.15 promesas de rol incompletas en ficha: falta ${required}`)
}
for (const required of ['promisePlayerRole','setRolePromise']) {
  if (!rootApp.includes(required)) problems.push(`v0.15 promesas de rol no conectadas: falta ${required}`)
}


// v0.16 tactical AI 2.0 + frozen 1993-94 rules. Rival preparation must be
// visible and explainable instead of silently reading the user's current screen.
for (const required of ['preview-counterplan','preparationLabel','CÓMO TE HAN PREPARADO']) {
  if (!liveWorkspace.includes(required)) problems.push(`v0.16 preparación rival no visible: falta ${required}`)
}
// v0.17 closes P5: the preview must expose competitive context and any
// longitudinal coach memory instead of keeping those new causal layers hidden.
for (const required of ['preparation.context?.phase','preparation.preparation_intensity','preparation.phase_focus','preparation.learning_note','Memoria del técnico']) {
  if (!liveWorkspace.includes(required)) problems.push(`v0.17 cierre P5 no visible: falta ${required}`)
}

const managerCss = files
  .filter(file => file.startsWith('src/styles/football9394-'))
  .map(file => readFileSync(resolve(process.cwd(), file), 'utf8'))
  .join('\n')
for (const required of [
  '.modern-commentary.preflight,.modern-commentary.finished{min-height:0}',
  '.tactical-player-fit-list{display:grid',
  'max-height:172px;overflow:auto',
  '.switch-order>span small{color:var(--f-muted);font-size:11px',
]) {
  if (!managerCss.includes(required)) problems.push(`D9 contrato 1920x1080 incompleto: falta ${required}`)
}

if (problems.length) {
  console.error('UI quality gate FAILED')
  for (const problem of problems) console.error(`- ${problem}`)
  process.exit(1)
}
console.log('UI quality gate OK: R1-R10 + D1-D9 + v0.10-v0.11 + v0.15-v0.17 + v1.0 core-loop/destructive continuity preserved')
