<script setup>
import { computed } from 'vue'

const props = defineProps({
  nextMatch: { type: Object, default: null }, season: { type: String, default: '1993-94' }, controlledTeamId: { type: Number, default: 0 }, loading: { type: Boolean, default: false },
  team: { type: Object, default: () => ({}) }, squad: { type: Array, default: () => [] },
  preseason: { type: Object, default: () => ({}) }, marketPeriod: { type: Object, default: () => ({}) }, clubStatus: { type: Object, default: () => ({}) },
  tableWindow: { type: Array, default: () => [] }, standings: { type: Array, default: () => [] }, dashboard: { type: Object, default: () => ({}) }, latestNews: { type: Array, default: () => [] }, currentBoard: { type: Object, default: () => ({}) },
  storylines: { type: Array, default: () => [] }, rivalries: { type: Array, default: () => [] },
  selection: { type: Object, default: () => ({starter_ids:[],bench_ids:[],valid:false,issues:[]}) },
  formation: { type: String, default: '4-4-2' }, gameDate: { type: String, default: '' }, lineupDirty: { type: Boolean, default: false },
  lastMatchReport: { type: Object, default: null },
})
const emit = defineEmits(['navigate','open-decision','start-live','continue'])
const dateShort = value => { if(!value)return '—'; const p=String(value).split('-'); return p.length===3?`${p[2]}/${p[1]}/${p[0]}`:String(value) }
const matchContext = row => { if(!row)return 'SIN PARTIDO'; if(row.fixture_type==='friendly')return 'PRETEMPORADA · AMISTOSO'; if(row.fixture_type==='tournament')return `${row.competition_name||'COPA'} · ${row.stage||''}`; return `LIGA · JORNADA ${row.matchday||'—'}` }
const trendLabel = value => { const n=Number(value||0); return n>0?`▲ +${n}`:n<0?`▼ ${n}`:'● ESTABLE' }
const boardClass = risk => String(risk||'').includes('ALTO')?'risk-high':risk==='RIESGO'?'risk-danger':risk==='VIGILANCIA'?'risk-watch':'risk-safe'
const crest = id => id ? `/historical9394/clubs/${Number(id)}.gif` : null
const photo = id => id ? `/historical9394/players/${Number(id)}.jpg` : null

const topPlayers = computed(() => [...props.squad].sort((a,b)=>Number(b.overall||0)-Number(a.overall||0)).slice(0,3))
const concerns = computed(() => props.squad.filter(p => p.status !== 'DISP.' || p.profile?.squad_dynamics?.wants_move || Number(p.profile?.squad_dynamics?.satisfaction||100)<45).slice(0,3))
const nextOpponent = computed(() => {
  if (!props.nextMatch) return null
  const home = Number(props.nextMatch.home_team_id) === Number(props.controlledTeamId)
  return { id: home ? props.nextMatch.away_team_id : props.nextMatch.home_team_id, name: home ? props.nextMatch.away_team : props.nextMatch.home_team, venue: home ? 'En casa' : 'Fuera' }
})
const hasMatchDecision = computed(() => Boolean(props.nextMatch))
const isMatchDay = computed(() => Boolean(props.nextMatch?.date && props.gameDate && String(props.nextMatch.date)===String(props.gameDate)))
const selectionReady = computed(() => Boolean(!props.lineupDirty && props.selection?.valid && (props.selection?.starter_ids || []).length===11 && (props.selection?.bench_ids || []).length===5))
const unavailableStarters = computed(() => {
  const ids=new Set((props.selection?.starter_ids || []).map(Number))
  return props.squad.filter(p=>ids.has(Number(p.id)) && p.status!=='DISP.')
})
const matchReadiness = computed(() => [
  {label:'Convocatoria',value:props.lineupDirty?'Sin guardar':selectionReady.value?'11 + 5 lista':'Revisar',ok:selectionReady.value,action:'squad'},
  {label:'Sistema',value:props.formation || '—',ok:true,action:'tactics'},
  {label:'Bajas en XI',value:String(unavailableStarters.value.length),ok:unavailableStarters.value.length===0,action:'squad'},
  {label:'Partido',value:isMatchDay.value?'Hoy':dateShort(props.nextMatch?.date),ok:isMatchDay.value,action:isMatchDay.value?'match':'calendar'},
])
const primaryMatchAction = computed(() => {
  if(!props.nextMatch)return {label:'Continuar',kind:'continue'}
  if(!selectionReady.value)return {label:'Completar convocatoria',kind:'navigate',target:'squad'}
  if(isMatchDay.value)return {label:'Ir a la previa',kind:'start-live'}
  return {label:'Preparar plan',kind:'navigate',target:'tactics'}
})
function runPrimaryMatchAction(){
 const action=primaryMatchAction.value
 if(action.kind==='continue')emit('continue')
 else if(action.kind==='start-live')emit('start-live')
 else emit('navigate',action.target)
}
const storyAction = story => story.kind==='transfer_saga'?'market':story.kind==='player_tension'?'squad':story.kind==='rivalry'?'tactics':'competitions'
const storyLabel = story => ({table_pressure:'TEMPORADA',streak:'RACHA',player_tension:'VESTUARIO',transfer_saga:'MERCADO',rivalry:'RIVALIDAD',manager_change:'BANQUILLOS'}[story.kind]||'HISTORIA')
const summerBriefing = computed(()=>props.dashboard?.summer_briefing?.season===props.season ? props.dashboard.summer_briefing : null)
const blockingDecision = computed(()=>props.dashboard?.blocking_decisions?.[0] || null)
const activeProcesses = computed(()=>props.dashboard?.active_processes || [])
const recentChanges = computed(()=>props.dashboard?.recent_changes || [])
const lastRoundSummary = computed(()=>props.lastMatchReport?.round_summary || null)
const lastRoundResults = computed(()=>lastRoundSummary.value?.results || [])
</script>

<template>
  <section class="home-command-center d4-home">
    <article class="home-matchday-hero">
      <div class="home-matchday-copy">
        <small class="home-kicker">{{matchContext(nextMatch)}} · {{season}}</small>
        <div v-if="nextMatch" class="home-matchup-v2">
          <div class="home-club-lockup"><img :src="crest(controlledTeamId)" alt="" @error="$event.currentTarget.style.display='none'"><span><small>TU EQUIPO</small><strong>{{team.name || (nextMatch.home_team_id===controlledTeamId?nextMatch.home_team:nextMatch.away_team)}}</strong></span></div>
          <b class="home-versus">vs</b>
          <div class="home-club-lockup opponent"><img :src="crest(nextOpponent?.id)" alt="" @error="$event.currentTarget.style.display='none'"><span><small>{{nextOpponent?.venue}}</small><strong>{{nextOpponent?.name}}</strong></span></div>
        </div>
        <div v-else class="home-empty-match"><strong>{{loading?'Cargando calendario histórico…':(dashboard.calendar_context?.label || 'No hay partido inmediato')}}</strong><span>{{dashboard.calendar_context?.detail || 'Continúa para avanzar hasta el siguiente acontecimiento relevante.'}}</span></div>
        <div class="home-matchday-actions">
          <button type="button" class="football-button primary" @click="runPrimaryMatchAction">{{primaryMatchAction.label}}</button>
          <button v-if="hasMatchDecision" type="button" class="football-button" @click="emit('navigate','squad')">Plantilla</button>
          <button v-if="hasMatchDecision" type="button" class="football-button" @click="emit('navigate','tactics')">Táctica</button>
          <button v-if="hasMatchDecision && !isMatchDay" type="button" class="football-button" @click="emit('continue')">Continuar</button>
        </div>
      </div>
      <div class="home-season-score">
        <span><small>POSICIÓN</small><b>{{dashboard.position?`${dashboard.position}º`:'—'}}</b><em>{{dashboard.points ?? 0}} pts</em></span>
        <span><small>FORMA</small><b class="word-score">{{dashboard.form_label || 'Sin partidos'}}</b><div class="form-strip"><i v-for="(r,i) in dashboard.recent_form" :key="i" :class="`form-${r}`">{{r}}</i></div></span>
        <span><small>MORAL</small><b>{{dashboard.morale_average ?? '—'}}</b><em>{{dashboard.unavailable_count||0}} baja{{Number(dashboard.unavailable_count||0)===1?'':'s'}}</em></span>
      </div>
    </article>

    <section v-if="summerBriefing" class="home-summer-briefing" aria-label="Transición de temporada">
      <header><span><small>NUEVA TEMPORADA · {{summerBriefing.season}}</small><strong>{{summerBriefing.headline}}</strong><em>{{summerBriefing.summary}}</em></span><b>{{summerBriefing.action_required||0}} pendientes</b></header>
      <div>
        <button v-for="item in summerBriefing.checklist" :key="item.key" type="button" :class="item.status" @click="emit('navigate',item.action)"><span><small>{{item.label}}</small><strong>{{item.detail}}</strong></span><b>{{item.status==='ready'||item.status==='done'?'✓':'→'}}</b></button>
      </div>
    </section>

    <section v-if="nextMatch" class="home-readiness-strip" aria-label="Preparación del próximo partido">
      <button v-for="item in matchReadiness" :key="item.label" type="button" :class="{ready:item.ok,attention:!item.ok}" @click="item.action==='match' ? emit('start-live') : emit('navigate',item.action)">
        <small>{{item.label}}</small><strong>{{item.value}}</strong><span>{{item.ok?'✓':'→'}}</span>
      </button>
    </section>

    <section v-if="storylines.length" class="home-storyline-strip" aria-label="Historias abiertas de la carrera">
      <button v-for="story in storylines.slice(0,3)" :key="story.id" type="button" class="career-story-pulse" :class="{urgent:story.priority==='high'}" @click="emit('navigate',storyAction(story))">
        <span><small>{{storyLabel(story)}}</small><strong>{{story.title}}</strong><em>{{story.summary}}</em></span><b>{{story.intensity}}</b>
      </button>
    </section>

    <div class="home-story-layout">
      <main class="home-story-main">
        <article class="football-panel home-decisions-v2">
          <header class="editorial-head"><span><small>AHORA</small><h2>Lo que necesita tu decisión</h2></span><b v-if="dashboard.pending_decisions?.length">{{dashboard.pending_decisions.length}}</b></header>
          <div v-if="blockingDecision" class="home-blocking-note"><span><small>CONTINUAR SE DETIENE AQUÍ</small><strong>{{blockingDecision.title}}</strong></span><button type="button" @click="emit('open-decision',blockingDecision)">Resolver →</button></div>
          <div v-if="dashboard.pending_decisions?.length" class="decision-stack-v2">
            <button v-for="d in dashboard.pending_decisions" :key="`${d.kind}-${d.title}`" type="button" class="decision-story" :class="{urgent:d.priority==='high',blocking:d.blocking}" @click="emit('open-decision',d)">
              <span class="decision-marker">{{d.priority==='high'?'!':'•'}}</span>
              <span class="decision-copy"><small>{{d.status || (d.priority==='high'?'URGENTE':'PENDIENTE')}} · {{d.owner || 'Tú (mánager)'}}</small><strong>{{d.title}}</strong><em>{{d.detail}}</em><span class="decision-next"><b>Siguiente:</b> {{d.next_step}}</span><span class="decision-impact"><b>Si esperas:</b> {{d.consequence}}</span></span><i>→</i>
            </button>
          </div>
          <div v-else class="inbox-clear editorial-clear"><b>Sin asuntos pendientes</b><span>El mundo puede avanzar. Continuar parará cuando aparezca una decisión real.</span></div>
        </article>

        <article class="football-panel home-processes-v2">
          <header class="editorial-head"><span><small>EN CURSO</small><h2>Quién está trabajando y qué falta</h2></span></header>
          <div v-if="activeProcesses.length" class="process-stack-v2">
            <button v-for="p in activeProcesses" :key="p.id" type="button" class="process-story" @click="emit('navigate',p.action)"><span><small>{{p.area}} · {{p.status}}</small><strong>{{p.title}}</strong><em>{{p.owner}}</em><span>{{p.next_step}}</span><i>{{p.consequence}}</i></span><b>{{p.requires_action?'!':'→'}}</b></button>
          </div>
          <div v-else class="inbox-clear editorial-clear"><b>Nadie espera por ti</b><span>No hay procesos activos que necesiten seguimiento. Puedes avanzar con tranquilidad.</span></div>
        </article>

        <article class="football-panel home-changes-v2">
          <header class="editorial-head"><span><small>QUÉ CAMBIÓ</small><h2>Desde los últimos avances</h2></span></header>
          <div v-if="recentChanges.length" class="change-stack-v2">
            <button v-for="c in recentChanges" :key="`${c.id}-${c.date}`" type="button" class="change-story" @click="emit('navigate',c.action)"><time>{{dateShort(c.date)}}</time><span><small>{{c.area}}</small><strong>{{c.title}}</strong><em>{{c.detail}}</em></span><i>→</i></button>
          </div>
          <div v-else class="inbox-clear editorial-clear"><b>Sin cambios relevantes</b><span>Cuando el mundo cambie tu contexto, aparecerá aquí con su origen y destino.</span></div>
        </article>

        <article class="football-panel home-squad-story">
          <header class="editorial-head"><span><small>VESTUARIO</small><h2>Los nombres que marcan tu momento</h2></span><button type="button" @click="emit('navigate','squad')">Ver plantilla →</button></header>
          <div class="home-star-trio">
            <button v-for="p in topPlayers" :key="p.id" type="button" class="home-star" @click="emit('navigate','squad')"><span class="home-star-photo"><img :src="photo(p.id)" alt="" @error="$event.currentTarget.style.display='none'"></span><span><small>{{p.pos}} · {{p.profile?.squad_dynamics?.role || 'Plantilla'}}</small><strong>{{p.name}}</strong><em>{{p.profile?.identity?.archetype || 'Perfil futbolístico'}} · {{p.overall}}</em></span></button>
          </div>
          <div class="home-concerns" v-if="concerns.length"><small>ATENCIÓN EN PLANTILLA</small><span v-for="p in concerns" :key="p.id"><b>{{p.name}}</b><em v-if="p.status!=='DISP.'">{{p.profile?.status || p.status}}</em><em v-else-if="p.profile?.squad_dynamics?.wants_move">quiere salir</em><em v-else>satisfacción {{p.profile?.squad_dynamics?.satisfaction}}/100</em></span></div>
        </article>

        <article class="football-panel home-news-v2">
          <header class="editorial-head"><span><small>MUNDO</small><h2>Qué está pasando</h2></span><button type="button" @click="emit('navigate','news')">Noticias →</button></header>
          <button v-for="n in latestNews.slice(0,4)" :key="n.id" type="button" class="news-story-v2" @click="emit('navigate','news')"><time>{{dateShort(n.date)}}</time><span><small>{{n.category}}</small><strong>{{n.headline}}</strong></span><i>→</i></button>
          <div v-if="!latestNews.length" class="rail-empty">Aún no hay noticias relevantes.</div>
        </article>
      </main>

      <aside class="home-story-rail">
        <article class="football-panel home-table-v2">
          <header class="editorial-head compact"><span><small>COMPETICIÓN</small><h3>Tu zona de la tabla</h3></span><button type="button" @click="emit('navigate','competitions')">Completa →</button></header>
          <div class="table-window-v2"><div v-for="r in tableWindow" :key="r[8]" :class="{controlled:r[8]===controlledTeamId}"><b>{{standings.indexOf(r)+1}}</b><span>{{r[0]}}</span><strong>{{r[7]}} pts</strong></div></div>
        </article>

        <article v-if="lastRoundResults.length" class="football-panel home-round-v2">
          <header class="editorial-head compact"><span><small>ÚLTIMA JORNADA</small><h3>{{lastRoundSummary.label}}</h3></span><button type="button" @click="emit('navigate','competitions')">Competición →</button></header>
          <div class="home-round-grid"><span v-for="row in lastRoundResults" :key="row.fixture_id" :class="{controlled:row.controlled}"><em>{{row.home_team}}</em><strong>{{row.home_goals}}–{{row.away_goals}}</strong><em>{{row.away_team}}</em></span></div>
        </article>

        <article class="football-panel home-board-v2">
          <header class="editorial-head compact"><span><small>CONSEJO</small><h3>{{dashboard.board_expectation?.title || 'Objetivo'}}</h3></span></header>
          <div class="board-confidence-v2" :class="boardClass(currentBoard.risk)"><small>Confianza</small><strong>{{dashboard.board_confidence || 'A la espera'}}</strong><b v-if="currentBoard.score!=null">{{currentBoard.score}}/100</b></div>
          <button type="button" class="text-action full" @click="emit('navigate','club')">Contexto del club →</button>
        </article>

        <article class="football-panel home-rhythm-v2"><small>RITMO DE CARRERA</small><strong>{{preseason.active?'Pretemporada':'Temporada oficial'}}</strong><span>{{preseason.active?'Avances cortos para construir la plantilla':'Avance por partidos y decisiones importantes'}}</span><b :class="marketPeriod.open?'good-text':'bad-cell'">{{marketPeriod.label}}</b><em>{{clubStatus.tier || 'CLUB'}} · {{trendLabel(clubStatus.trend)}}</em></article>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.home-readiness-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:-4px 0 12px}.home-readiness-strip button{display:grid;grid-template-columns:1fr auto;gap:2px 8px;text-align:left;padding:10px 12px;border:1px solid var(--line,#d7dde6);border-radius:9px;background:var(--surface,#fff);cursor:pointer}.home-readiness-strip button small{grid-column:1/-1;font-size:11px;font-weight:900;letter-spacing:.08em;color:var(--text-soft,#687386)}.home-readiness-strip button strong{font-size:13px}.home-readiness-strip button span{font-weight:900}.home-readiness-strip button.attention{border-color:color-mix(in srgb,var(--warning,#b26b00) 45%,var(--line,#d7dde6))}.home-readiness-strip button.ready span{color:var(--success,#237a45)}@media(max-width:900px){.home-readiness-strip{grid-template-columns:1fr 1fr}}
.home-summer-briefing{display:grid;gap:10px;margin:0 0 12px;padding:13px 14px;border:1px solid #cbded1;border-radius:11px;background:#f4faf6}.home-summer-briefing>header{display:flex;justify-content:space-between;gap:16px;align-items:start}.home-summer-briefing>header span{display:grid;gap:2px}.home-summer-briefing>header small{font-size:11px;font-weight:900;letter-spacing:.08em;color:var(--f-action,#236b4f)}.home-summer-briefing>header strong{font-size:16px}.home-summer-briefing>header em{font-size:11px;font-style:normal;color:var(--text-soft,#687386)}.home-summer-briefing>header>b{white-space:nowrap;padding:5px 8px;border-radius:999px;background:#fff;font-size:11px}.home-summer-briefing>div{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.home-summer-briefing button{display:grid;grid-template-columns:1fr auto;gap:6px;align-items:center;padding:9px 10px;border:1px solid var(--line,#d7dde6);border-radius:8px;background:#fff;text-align:left;cursor:pointer}.home-summer-briefing button span{display:grid;gap:2px;min-width:0}.home-summer-briefing button small{font-size:11px;color:var(--text-soft,#687386);font-weight:850}.home-summer-briefing button strong{font-size:11px;line-height:1.3}.home-summer-briefing button.ready,.home-summer-briefing button.done{border-color:#bdd8c8}.home-summer-briefing button.attention{border-color:#e1be82;background:#fffaf0}@media(max-width:900px){.home-summer-briefing>div{grid-template-columns:1fr 1fr}}@media(max-width:650px){.home-summer-briefing>div{grid-template-columns:1fr}.home-summer-briefing>header{display:grid}}
.home-blocking-note{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 14px;border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--f-gold) 10%,var(--surface));}.home-blocking-note>span{display:grid;gap:2px}.home-blocking-note small{font-size:11px;font-weight:900;letter-spacing:.08em;color:var(--f-gold)}.home-blocking-note strong{font-size:12px}.home-blocking-note button{border:0;background:transparent;color:var(--f-gold);font-size:11px;font-weight:900;cursor:pointer}.decision-copy{display:grid!important;gap:3px}.decision-next,.decision-impact{font-size:11px;line-height:1.35;color:var(--text-soft)}.decision-next b{color:var(--f-green)}.decision-impact b{color:var(--f-gold)}.decision-story.blocking{box-shadow:inset 3px 0 var(--f-gold)}
.process-stack-v2,.change-stack-v2{display:grid}.process-story{display:grid;grid-template-columns:minmax(0,1fr) 28px;gap:10px;align-items:center;padding:13px 16px;border:0;border-bottom:1px solid var(--line);background:transparent;color:inherit;text-align:left;cursor:pointer}.process-story:last-child,.change-story:last-child{border-bottom:0}.process-story:hover,.change-story:hover{background:color-mix(in srgb,var(--f-action) 6%,transparent)}.process-story>span{display:grid;gap:2px}.process-story small,.change-story small{font-size:11px;font-weight:900;letter-spacing:.07em;color:var(--f-action)}.process-story strong,.change-story strong{font-size:12px}.process-story em{font-size:11px;font-style:normal;color:var(--f-green)}.process-story span>span,.process-story span>i{font-size:11px;font-style:normal;line-height:1.35;color:var(--text-soft)}.process-story>b{font-size:15px;color:var(--f-action)}.change-story{display:grid;grid-template-columns:76px minmax(0,1fr) 20px;gap:10px;align-items:start;padding:12px 16px;border:0;border-bottom:1px solid var(--line);background:transparent;color:inherit;text-align:left;cursor:pointer}.change-story time{font-size:11px;color:var(--text-soft);font-weight:800}.change-story>span{display:grid;gap:2px}.change-story em{font-size:11px;font-style:normal;line-height:1.35;color:var(--text-soft)}.change-story>i{font-style:normal;color:var(--f-action)}

.home-round-grid{display:grid}.home-round-grid>span{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:7px;align-items:center;padding:8px 12px;border-bottom:1px solid var(--line);font-size:11px}.home-round-grid>span:last-child{border-bottom:0}.home-round-grid>span.controlled{background:color-mix(in srgb,var(--f-action) 9%,transparent);font-weight:850}.home-round-grid em{font-style:normal;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.home-round-grid em:last-child{text-align:right}.home-round-grid strong{font-size:12px}
</style>
