<script setup>
import { computed } from 'vue'
import LineupPitch from './LineupPitch.vue'
import PersonAvatar from '../../components/PersonAvatar.vue'

const props = defineProps({
  team:{type:Object,default:()=>({})},
  controlledTeamId:{type:Number,default:0},
  season:{type:String,default:'1993-94'},
  squad:{type:Array,default:()=>[]},
  lineupPlayers:{type:Array,default:()=>[]},
  formation:{type:String,default:'4-4-2'},
  tacticalIdentity:{type:Object,default:()=>({})},
  standings:{type:Array,default:()=>[]},
  nextMatch:{type:Object,default:null},
  sourceManager:{type:Object,default:null},
  venue:{type:Object,default:null},
  finances:{type:Object,default:()=>({})},
  clubStatus:{type:Object,default:()=>({})},
  currentBoard:{type:Object,default:()=>({})},
  careerRecords:{type:Object,default:()=>({})},
  managerCareer:{type:Object,default:()=>({reputation:50,job_offers:[],tenures:[],current_tenure:{}})},
  boardProject:{type:Object,default:()=>({objective:'',philosophy:[],requests:[],sale_pressure:null,support:55})},
  agePolicy:{type:String,default:'frozen_attributes_dynamic'},
  dashboard:{type:Object,default:()=>({})},
  jobStatus:{type:String,default:'active'},
  crestFor:{type:Function,required:true},stadiumFor:{type:Function,required:true},formatMoney:{type:Function,required:true},trendLabel:{type:Function,required:true},boardClass:{type:Function,required:true},formatDate:{type:Function,required:true},
})
const emit = defineEmits(['open-player','navigate','accept-job','board-request'])

const standing = computed(() => {
  const index = props.standings.findIndex(row => Number(row?.[8]) === Number(props.controlledTeamId))
  const row = index >= 0 ? props.standings[index] : null
  return {position:index >= 0 ? index + 1 : null, row}
})
const topPlayers = computed(() => [...props.squad].sort((a,b)=>Number(b.overall||0)-Number(a.overall||0)).slice(0,4))
const unavailable = computed(() => props.squad.filter(p=>p.status!=='DISP.'))
const tensions = computed(() => props.squad.filter(p => p.profile?.squad_dynamics?.wants_move || Number(p.profile?.squad_dynamics?.satisfaction ?? 70) <= 42))
const nextOpponent = computed(() => {
  if(!props.nextMatch) return null
  const home = Number(props.nextMatch.home_team_id) === Number(props.controlledTeamId)
  return {name: home ? props.nextMatch.away_team : props.nextMatch.home_team, venue:home?'Casa':'Fuera', date:props.nextMatch.date, competition:props.nextMatch.competition_name || props.team.league?.name || 'Competición'}
})
const form = computed(() => props.dashboard.recent_form || [])
const managerStyle = computed(() => {
  const m=props.sourceManager||{}
  const tendency={attacking:'Ofensivo',defensive:'Defensivo',normal:'Equilibrado'}[m.game_tendency]||'—'
  return [m.primary_tactic,tendency].filter(Boolean).join(' · ')
})
const academyLabel = computed(() => ({0:'Básica',1:'Buena',2:'Muy buena',3:'Élite'}[Number(props.team.academy_level)] || '—'))
const honours = computed(() => {
  const h=props.team.honours||{}
  return Number(h.national_leagues||0)+Number(h.national_cups||0)+Number(h.continental||0)+Number(h.continental_2||0)+Number(h.continental_3||0)+Number(h.continental_supercups||0)+Number(h.national_supercups||0)
})
const moneyPulse = computed(() => Number(props.finances.cash||0) - Number(props.finances.debt||0))
const withHistoricalPhoto = person => {
  const id = Number(person?.id ?? person?.source_id ?? 0) || null
  return {...(person||{}), photo_url: person?.photo_url || (id ? `/historical9394/players/${id}.jpg` : null)}
}
</script>

<template>
<section class="club-hq">
  <article class="club-hero-v2" :style="team.stadium_id?{backgroundImage:`linear-gradient(90deg,rgba(7,16,13,.94) 0%,rgba(7,16,13,.74) 50%,rgba(7,16,13,.32) 100%),url(${stadiumFor(team.stadium_id)})`}:{}">
    <div class="club-hero-main">
      <img class="club-hero-crest" :src="crestFor(controlledTeamId)" alt="">
      <div class="club-hero-copy">
        <small>{{team.league?.name || 'Competición'}} · {{season}}</small>
        <h2>{{team.long_name||team.name}}</h2>
        <p>{{venue?.name || 'Estadio histórico'}}<template v-if="venue?.capacity"> · {{Number(venue.capacity).toLocaleString('es-ES')}} espectadores</template><template v-if="team.members"> · {{Number(team.members).toLocaleString('es-ES')}} socios</template></p>
        <div class="club-hero-tags"><span>{{clubStatus.tier || 'CLUB'}}</span><span>{{formation}}</span><span>{{tacticalIdentity.formation_label || 'Plan propio'}}</span></div>
      </div>
    </div>
    <div class="club-hero-scoreboard">
      <span class="club-position"><small>POSICIÓN</small><b>{{standing.position ? `${standing.position}º` : '—'}}</b><em>{{standing.row?.[7] ?? 0}} pts</em></span>
      <span><small>FORMA</small><b class="form-dots"><i v-for="(r,i) in form.slice(-5)" :key="i" :class="String(r).toLowerCase()">{{r}}</i><i v-if="!form.length">—</i></b></span>
      <span><small>CONSEJO</small><b>{{currentBoard.score ?? '—'}}<em>/100</em></b><strong>{{currentBoard.label || 'A la espera'}}</strong></span>
    </div>
  </article>

  <section v-if="jobStatus==='dismissed'" class="manager-career-crossroads">
    <div class="career-crossroads-copy"><small>TU CARRERA CONTINÚA</small><h3>Te han destituido. Ahora eliges qué entrenador quieres ser.</h3><p>Tu reputación, récords y memoria viajan contigo. El nuevo club conserva exactamente su clasificación y calendario de esta temporada.</p><span>Reputación <b>{{managerCareer.reputation ?? 50}}</b>/100</span></div>
    <div class="career-job-offers">
      <article v-for="offer in managerCareer.job_offers||[]" :key="offer.id">
        <small>{{offer.league_name}} · {{offer.position}}º ahora</small><strong>{{offer.team_name}}</strong><span>Expectativa previa: {{offer.expected_position}}º · proyecto {{Math.round(offer.club_score)}}/100</span><em v-if="offer.manager_pressure">Presión del banquillo: {{offer.manager_pressure}}/100</em><button type="button" class="football-button primary" @click="emit('accept-job',offer.id)">Aceptar proyecto</button>
      </article>
      <div v-if="!managerCareer.job_offers?.length" class="empty-football-state">No hay una propuesta compatible en este momento.</div>
    </div>
  </section>

  <div class="club-story-grid">
    <main class="club-story-main">
      <article class="club-section club-pulse">
        <header><div><small>AHORA MISMO</small><h3>Pulso deportivo</h3></div><button type="button" class="text-action" @click="emit('navigate','competitions')">Ver competición →</button></header>
        <div class="club-pulse-grid">
          <div class="pulse-primary"><small>Balance liguero</small><strong>{{standing.row ? `${standing.row[2]}G · ${standing.row[3]}E · ${standing.row[4]}P` : 'Sin partidos'}}</strong><span v-if="standing.row">{{standing.row[5]}} goles a favor · {{standing.row[6]}} en contra</span><span v-else>La temporada todavía no ha empezado.</span></div>
          <div class="pulse-next" v-if="nextOpponent"><small>PRÓXIMO PARTIDO · {{nextOpponent.venue}}</small><strong>{{nextOpponent.name}}</strong><span>{{nextOpponent.competition}}<template v-if="nextOpponent.date"> · {{formatDate(nextOpponent.date)}}</template></span><button type="button" @click="emit('navigate','home')">Preparar partido</button></div>
          <div class="pulse-next quiet" v-else><small>CALENDARIO</small><strong>Sin partido inmediato</strong><span>Continúa para alcanzar el siguiente acontecimiento.</span></div>
        </div>
      </article>

      <article class="club-section club-lineup-section">
        <header><div><small>IDENTIDAD EN EL CAMPO</small><h3>Tu equipo</h3></div><button type="button" class="text-action" @click="emit('navigate','tactics')">Editar táctica →</button></header>
        <div class="club-lineup-layout">
          <LineupPitch :formation="formation" :players="lineupPlayers" compact />
          <div class="club-plan-copy">
            <span class="plan-kicker">TU PLAN ACTUAL</span>
            <strong>{{tacticalIdentity.formation_label || formation}}</strong>
            <p>{{tacticalIdentity.summary || `Estructura ${formation}. La identidad real emerge de las órdenes y de los futbolistas elegidos.`}}</p>
            <dl><div><dt>Sistema</dt><dd>{{formation}}</dd></div><div><dt>XI definido</dt><dd>{{lineupPlayers.length}}/11</dd></div><div><dt>Bajas</dt><dd>{{unavailable.length}}</dd></div><div><dt>Tensión</dt><dd :class="tensions.length?'warn-cell':'good-cell'">{{tensions.length ? `${tensions.length} casos` : 'Controlada'}}</dd></div></dl>
          </div>
        </div>
      </article>

      <article class="club-section club-stars">
        <header><div><small>VESTUARIO</small><h3>Futbolistas que definen al equipo</h3></div><button type="button" class="text-action" @click="emit('navigate','squad')">Plantilla completa →</button></header>
        <div class="club-star-grid">
          <button v-for="player in topPlayers" :key="player.id" type="button" class="club-star-card" @click="emit('open-player',player)">
            <span class="club-star-photo"><PersonAvatar :person="withHistoricalPhoto(player)" :size="52" :height="72" :shirt-number="player.n" variant="player" decorative /></span>
            <span class="club-star-copy"><small>#{{player.n}} · {{player.pos}}</small><strong>{{player.name}}</strong><em>{{player.profile?.identity?.archetype || 'Futbolista de plantilla'}}</em></span>
            <b>{{player.overall}}</b>
          </button>
        </div>
      </article>
    </main>

    <aside class="club-story-rail">
      <article class="club-section club-source-manager">
        <header><div><small>CONTEXTO HISTÓRICO</small><h3>{{managerCareer.tenures?.length ? 'Entrenador antes de tu llegada' : 'Entrenador al inicio'}}</h3></div></header>
        <div class="source-manager-body" v-if="sourceManager">
          <span class="source-manager-photo"><PersonAvatar :person="withHistoricalPhoto(sourceManager)" :size="58" :height="76" decorative /></span>
          <div><strong>{{sourceManager.display_name}}</strong><p>{{managerStyle}}</p><small>Calidad {{sourceManager.coaching_quality ?? '—'}} · ojo {{sourceManager.player_judgement || '—'}} <template v-if="agePolicy!=='frozen_attributes_dynamic'"> · cantera {{sourceManager.youth_usage || '—'}}</template></small></div>
        </div>
        <p class="source-context-note">Referencia de la base histórica. En el club que diriges, las decisiones tácticas y de plantilla son tuyas.</p>
      </article>

      <article class="club-section board-compact">
        <header><div><small>CONSEJO Y PROYECTO</small><h3>{{boardProject.objective || dashboard.board_expectation?.title || 'Objetivo del club'}}</h3></div><span class="board-mini-score" :class="boardClass(currentBoard.risk)">{{boardProject.support ?? currentBoard.score ?? '—'}}</span></header>
        <p>{{currentBoard.reasons?.[0]?.text || 'El consejo evalúa resultados, sostenibilidad y construcción del proyecto.'}}</p>
        <div class="board-mini-components"><span><small>Tope salarial</small><b>{{boardProject.wage_ceiling?formatMoney(boardProject.wage_ceiling):'—'}}</b></span><span><small>Staff máx.</small><b>{{boardProject.max_staff_size??'—'}}</b></span><span><small>Plantilla ideal</small><b>{{boardProject.preferred_squad_size??'—'}}</b></span></div>
        <div v-if="boardProject.sale_pressure?.status==='active'" class="dismissed-banner">Venta exigida · faltan {{formatMoney(boardProject.sale_pressure.remaining)}} antes del {{formatDate(boardProject.sale_pressure.deadline)}}</div>
        <ul v-if="boardProject.philosophy?.length" class="board-philosophy"><li v-for="item in boardProject.philosophy" :key="item.key">{{item.label}}</li></ul>
        <div v-if="jobStatus==='active'" class="board-request-actions"><button type="button" class="text-action" @click="emit('board-request','extra_transfer_budget')">Pedir más presupuesto</button><button type="button" class="text-action" @click="emit('board-request','expand_staff')">Ampliar staff</button><button v-if="boardProject.sale_pressure?.status==='active'" type="button" class="text-action" @click="emit('board-request','delay_sale_pressure')">Pedir 30 días</button></div>
        <div v-if="jobStatus==='dismissed'" class="dismissed-banner">Etapa en este club finalizada · tu carrera sigue abierta</div>
      </article>

      <article class="club-section career-memory-card">
        <header><div><small>MEMORIA DE TU ETAPA</small><h3>Lo que ya has dejado aquí</h3></div></header>
        <div class="career-memory-balance">
          <span><b>{{careerRecords.matches_managed || 0}}</b><small>partidos</small></span>
          <span><b>{{careerRecords.wins || 0}}-{{careerRecords.draws || 0}}-{{careerRecords.losses || 0}}</b><small>V · E · D</small></span>
        </div>
        <dl>
          <div><dt>Mayor victoria</dt><dd>{{careerRecords.biggest_win ? `${careerRecords.biggest_win.result} vs ${careerRecords.biggest_win.opponent_name}` : 'Aún por escribir'}}</dd></div>
          <div><dt>Mejor racha</dt><dd>{{careerRecords.longest_win_streak || 0}} victorias</dd></div>
          <div><dt>Sin perder</dt><dd>{{careerRecords.longest_unbeaten_streak || 0}} partidos</dd></div>
        </dl>
      </article>

      <article class="club-section club-identity-facts">
        <header><div><small>CLUB</small><h3>Identidad</h3></div></header>
        <dl>
          <div><dt>Presidente</dt><dd>{{team.president || '—'}}</dd></div>
          <div><dt>Evolución</dt><dd v-if="agePolicy==='frozen_attributes_dynamic'">Edad congelada · sin cantera/newgens</dd><dd v-else>{{team.youth_residence || team.training_ground || '—'}} · {{academyLabel}}</dd></div>
          <div><dt>Estadio</dt><dd>{{venue?.name || `#${team.stadium_id || '—'}`}}</dd></div>
          <div><dt>Palmarés base</dt><dd>{{honours}} títulos registrados</dd></div>
        </dl>
      </article>

      <article class="club-section club-money-snapshot">
        <header><div><small>RECURSOS</small><h3>Margen para decidir</h3></div><button type="button" class="text-action" @click="emit('navigate','economy')">Economía →</button></header>
        <strong>{{formatMoney(finances.cash)}}</strong><span>Tesorería · ptas.</span>
        <div class="money-detail"><small>Deuda</small><b>{{formatMoney(finances.debt)}}</b></div><div class="money-detail"><small>Balance caja/deuda</small><b :class="moneyPulse>=0?'good-cell':'bad-cell'">{{formatMoney(moneyPulse)}}</b></div>
      </article>
    </aside>
  </div>
</section>
</template>
