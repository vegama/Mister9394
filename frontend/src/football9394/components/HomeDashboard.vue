<script setup>
import { computed } from 'vue'

const props = defineProps({
  nextMatch: { type: Object, default: null }, season: { type: String, default: '1993-94' }, controlledTeamId: { type: Number, default: 0 }, loading: { type: Boolean, default: false },
  team: { type: Object, default: () => ({}) }, squad: { type: Array, default: () => [] },
  preseason: { type: Object, default: () => ({}) }, marketPeriod: { type: Object, default: () => ({}) }, clubStatus: { type: Object, default: () => ({}) },
  tableWindow: { type: Array, default: () => [] }, standings: { type: Array, default: () => [] }, dashboard: { type: Object, default: () => ({}) }, latestNews: { type: Array, default: () => [] }, currentBoard: { type: Object, default: () => ({}) },
  storylines: { type: Array, default: () => [] }, rivalries: { type: Array, default: () => [] },
})
const emit = defineEmits(['navigate','start-live','simulate'])
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
const storyAction = story => story.kind==='transfer_saga'?'market':story.kind==='player_tension'?'squad':story.kind==='rivalry'?'tactics':'competitions'
const storyLabel = story => ({table_pressure:'TEMPORADA',streak:'RACHA',player_tension:'VESTUARIO',transfer_saga:'MERCADO',rivalry:'RIVALIDAD',manager_change:'BANQUILLOS'}[story.kind]||'HISTORIA')
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
        <div v-else class="home-empty-match"><strong>{{loading?'Cargando calendario histórico…':'No hay partido inmediato'}}</strong><span>Continúa para avanzar hasta el siguiente acontecimiento relevante.</span></div>
        <div class="home-matchday-actions">
          <button type="button" class="football-button" @click="emit('navigate','tactics')">Preparar plan</button>
          <button v-if="hasMatchDecision" type="button" class="football-button primary" @click="emit('start-live')">Jugar partido</button>
          <button v-if="hasMatchDecision" type="button" class="football-button" @click="emit('simulate')">Resultado rápido</button>
          <button type="button" class="football-button" @click="emit('navigate','squad')">Plantilla</button>
        </div>
      </div>
      <div class="home-season-score">
        <span><small>POSICIÓN</small><b>{{dashboard.position?`${dashboard.position}º`:'—'}}</b><em>{{dashboard.points ?? 0}} pts</em></span>
        <span><small>FORMA</small><b class="word-score">{{dashboard.form_label || 'Sin partidos'}}</b><div class="form-strip"><i v-for="(r,i) in dashboard.recent_form" :key="i" :class="`form-${r}`">{{r}}</i></div></span>
        <span><small>MORAL</small><b>{{dashboard.morale_average ?? '—'}}</b><em>{{dashboard.unavailable_count||0}} baja{{Number(dashboard.unavailable_count||0)===1?'':'s'}}</em></span>
      </div>
    </article>

    <section v-if="storylines.length" class="home-storyline-strip" aria-label="Historias abiertas de la carrera">
      <button v-for="story in storylines.slice(0,3)" :key="story.id" type="button" class="career-story-pulse" :class="{urgent:story.priority==='high'}" @click="emit('navigate',storyAction(story))">
        <span><small>{{storyLabel(story)}}</small><strong>{{story.title}}</strong><em>{{story.summary}}</em></span><b>{{story.intensity}}</b>
      </button>
    </section>

    <div class="home-story-layout">
      <main class="home-story-main">
        <article class="football-panel home-decisions-v2">
          <header class="editorial-head"><span><small>AHORA</small><h2>Lo que necesita tu decisión</h2></span><b v-if="dashboard.pending_decisions?.length">{{dashboard.pending_decisions.length}}</b></header>
          <div v-if="dashboard.pending_decisions?.length" class="decision-stack-v2">
            <button v-for="d in dashboard.pending_decisions" :key="`${d.kind}-${d.title}`" type="button" class="decision-story" :class="{urgent:d.priority==='high'}" @click="emit('navigate',d.action)"><span class="decision-marker">{{d.priority==='high'?'!':'•'}}</span><span><small>{{d.priority==='high'?'URGENTE':'PENDIENTE'}}</small><strong>{{d.title}}</strong><em>{{d.detail}}</em></span><i>→</i></button>
          </div>
          <div v-else class="inbox-clear editorial-clear"><b>Sin asuntos pendientes</b><span>El mundo puede avanzar. Continuar parará cuando aparezca una decisión real.</span></div>
        </article>

        <article class="football-panel home-squad-story">
          <header class="editorial-head"><span><small>VESTUARIO</small><h2>Los nombres que marcan tu momento</h2></span><button type="button" @click="emit('navigate','squad')">Ver plantilla →</button></header>
          <div class="home-star-trio">
            <button v-for="p in topPlayers" :key="p.id" type="button" class="home-star" @click="emit('navigate','squad')"><span class="home-star-photo"><img :src="photo(p.id)" alt="" @error="$event.currentTarget.style.display='none'"></span><span><small>{{p.pos}} · {{p.profile?.squad_dynamics?.role || 'Plantilla'}}</small><strong>{{p.name}}</strong><em>{{p.profile?.identity?.archetype || 'Perfil futbolístico'}} · {{p.overall}}</em></span></button>
          </div>
          <div class="home-concerns" v-if="concerns.length"><small>ATENCIÓN EN PLANTILLA</small><span v-for="p in concerns" :key="p.id"><b>{{p.name}}</b><em v-if="p.status!=='DISP.'">{{p.status}}</em><em v-else-if="p.profile?.squad_dynamics?.wants_move">quiere salir</em><em v-else>satisfacción {{p.profile?.squad_dynamics?.satisfaction}}/100</em></span></div>
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
