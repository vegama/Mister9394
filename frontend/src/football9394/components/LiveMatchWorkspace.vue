<script setup>
import { computed } from 'vue'
import PersonAvatar from '../../components/PersonAvatar.vue'

const props = defineProps({
  match: { type: Object, default: null },
  season: { type: String, default: '1993-94' },
  formation: { type: String, default: '4-4-2' },
  tacticalIdentity: { type: Object, default: () => ({}) },
  events: { type: Array, default: () => [] },
  outgoingId: { type: [Number, String], default: null },
  incomingId: { type: [Number, String], default: null },
  leagueName: { type: String, default: '' },
  busy: { type: Boolean, default: false },
  dashboard: { type: Object, default: () => ({}) }, nextMatch: { type: Object, default: null },
})
const emit = defineEmits(['update:outgoingId','update:incomingId','advance','chance','simulate','close','substitute','open-tactics','edit-lineup','back'])

const statusLabel = computed(() => props.match?.status === 'halftime' ? 'DESCANSO' : props.match?.status === 'finished' ? 'FINAL' : props.match?.minute === 0 ? 'PREVIA' : 'EN JUEGO')
const notableKinds = new Set(['goal','chance','penalty','penalty_saved','free_kick','free_kick_chance','set_piece_chance','defensive_error','second_ball','shot_off','save','corner','yellow','red','second_yellow_red','injury','injury_forced_off','injury_substitution','tactical_adjustment','halftime','fulltime'])
const eventClass = event => notableKinds.has(event?.kind) ? 'notable' : 'routine'
const ownHome = computed(() => Number(props.match?.controlled_team_id||0) === Number(props.match?.home_team_id||0))
const ownStats = computed(() => ownHome.value ? props.match?.home : props.match?.away)
const opponentStats = computed(() => ownHome.value ? props.match?.away : props.match?.home)
const opponent = computed(() => props.match?.opponent_context || {})
const opponentReport = computed(() => opponent.value?.report || {})
const opponentPlayerLevel = player => {
  if (player?.overall !== null && player?.overall !== undefined) return String(player.overall)
  const range = player?.overall_range
  return Array.isArray(range) && range.length === 2 ? `${range[0]}–${range[1]}` : '—'
}
const knownTacticalPlan = computed(() => {
  const tactics = opponent.value?.tactics || {}
  const fields = [
    tactics.formation && `sistema ${tactics.formation}`,
    tactics.mentality && `mentalidad ${tactics.mentality}`,
    tactics.tempo && `ritmo ${tactics.tempo}`,
    tactics.pressing && `presión ${tactics.pressing}`,
    tactics.directness && `juego ${tactics.directness}`,
  ].filter(Boolean)
  return fields.join(' · ') || 'Plan rival por confirmar'
})
const preparation = computed(() => opponent.value?.preparation || {})
const preparationLabel = computed(() => {
  const sample=Number(preparation.value?.observed_sample||0)
  const predict=Number(preparation.value?.observed_predictability||0)
  if(!sample)return 'Sin historial suficiente: preparación general de plantilla'
  if(predict>=75)return `Te consideran previsible · ${sample} partidos estudiados`
  if(predict>=55)return `Han detectado tendencias · ${sample} partidos estudiados`
  return `Patrón difícil de leer · ${sample} partidos estudiados`
})
const coachStyle = computed(() => {
  const quality = Number(opponentReport.value?.quality || 0)
  if (quality && quality < 12) return 'Informe parcial del rival'
  const m=opponent.value?.manager || {}
  const bits=[m.primary_tactic,m.game_tendency && `tendencia ${m.game_tendency}`,m.rotation_frequency && `rotación ${m.rotation_frequency}`].filter(Boolean)
  return bits.join(' · ') || knownTacticalPlan.value
})
const refereeStyle = computed(() => {
  const r=props.match?.referee
  if(!r)return 'Sin perfil arbitral para esta competición'
  const yellow=Number(r.yellow_tendency||0)
  const discipline=yellow>=5.5?'tarjeta fácil':yellow<=3.3?'permisivo':'criterio medio'
  return `${discipline}${r.quality?` · calidad ${r.quality}`:''}`
})
const decisiveEvents = computed(() => [...(props.events||[])].filter(e=>['goal','penalty','penalty_saved','defensive_error','tactical_adjustment','red','second_yellow_red','set_piece_chance'].includes(e.kind)).slice(-6).reverse())
const lineupPhoto = id => id ? `/historical9394/players/${Number(id)}.jpg` : null
const lineupPerson = p => ({...(p||{}),positions:[p?.position].filter(Boolean),photo_url:lineupPhoto(p?.id)})
const homeLineup = computed(() => ownHome.value ? (props.match?.controlled_on_pitch || []) : (props.match?.opponent_on_pitch || []))
const awayLineup = computed(() => ownHome.value ? (props.match?.opponent_on_pitch || []) : (props.match?.controlled_on_pitch || []))
const playerLabel = id => [...(props.match?.controlled_on_pitch||[]),...(props.match?.controlled_forced_off||[]),...(props.match?.controlled_bench||[])].find(p=>Number(p.id)===Number(id))?.display_name || `Jugador #${id}`
const resultSummary = computed(() => {
  if(props.match?.status!=='finished')return ''
  const gf=Number(ownStats.value?.goals||0), ga=Number(opponentStats.value?.goals||0)
  const verdict=gf>ga?'Victoria':gf<ga?'Derrota':'Empate'
  const shots=Number(ownStats.value?.shots||0)-Number(opponentStats.value?.shots||0)
  const shotText=shots>2?'generaste más volumen de tiro':shots<-2?'el rival generó más remates':'el volumen de tiro estuvo equilibrado'
  return `${verdict}: ${gf}-${ga}. ${shotText}.`
})
const performanceRows = computed(() => [...(props.match?.controlled_performance || [])].sort((a,b)=>Number(b.rating||0)-Number(a.rating||0)))
const bestPerformers = computed(() => performanceRows.value.slice(0,5))
const nextOpponentName = computed(() => {
  if(!props.nextMatch)return 'Por confirmar'
  const controlled=Number(props.match?.controlled_team_id||0)
  return Number(props.nextMatch.home_team_id||0)===controlled ? (props.nextMatch.away_team || 'Rival') : (props.nextMatch.home_team || 'Rival')
})
const postPosition = computed(() => props.dashboard?.position ? `${props.dashboard.position}º · ${props.dashboard.points ?? 0} pts` : `${props.dashboard?.points ?? 0} pts`)
const substitutionsRemaining = computed(() => Number(props.match?.controlled_substitutions_remaining ?? Math.max(0, 2-Number(ownStats.value?.substitutions||0))))
const substitutionsUsed = computed(() => Math.max(0, 2-substitutionsRemaining.value))
const canSubstitute = computed(() => props.match?.minute>0 && props.match?.status!=='finished' && substitutionsRemaining.value>0 && (props.match?.controlled_bench||[]).length>0)
const forcedOff = computed(() => props.match?.controlled_forced_off || [])
const replaceablePlayers = computed(() => {
  const seen=new Set(); const rows=[]
  for(const player of [...forcedOff.value,...(props.match?.controlled_on_pitch||[])]){const id=Number(player.id);if(!seen.has(id)){seen.add(id);rows.push(player)}}
  return rows
})
</script>

<template>
  <section class="live-match-screen redesigned-live">
    <template v-if="match">
      <article class="football-panel live-scoreboard modern-scoreboard">
        <div class="score-team home"><small>{{match.fixture?.competition_name || leagueName || 'PARTIDO'}}</small><strong>{{match.home_team_name}}</strong><span>Local</span></div>
        <div class="live-score"><span>{{match.minute}}'</span><b>{{match.home?.goals}} <i>–</i> {{match.away?.goals}}</b><em>{{statusLabel}}</em></div>
        <div class="score-team away"><small>{{season}}</small><strong>{{match.away_team_name}}</strong><span>Visitante</span></div>
      </article>

      <div class="live-command-bar" :aria-busy="busy">
        <div><small>PLAN ACTUAL</small><strong>{{formation}} · {{tacticalIdentity.formation_label}}</strong><span class="live-context-line"><template v-if="match.venue?.name">{{match.venue.name}}<template v-if="match.venue?.city_name"> · {{match.venue.city_name}}</template></template><template v-if="match.referee?.name"> · Árbitro: {{match.referee.name}}</template></span></div>
        <div v-if="match.minute===0" class="live-controls prematch-controls"><button class="football-button" :disabled="busy" @click="emit('edit-lineup')">Revisar XI</button><button class="football-button" :disabled="busy" @click="emit('open-tactics')">Táctica</button><button class="football-button result-button" :disabled="busy" @click="emit('simulate')">{{busy?'Procesando…':'Resultado'}}</button><button class="football-button primary" :disabled="busy" @click="emit('advance',1)">{{busy?'Procesando…':'Comenzar partido'}}</button></div>
        <div v-else-if="match.status==='halftime'" class="live-controls halftime-controls"><span class="halftime-label">Descanso · revisa táctica y cambios</span><button class="football-button" :disabled="busy" @click="emit('open-tactics')">Táctica</button><button class="football-button primary" :disabled="busy" @click="emit('advance',1)">{{busy?'Procesando…':'Comenzar 2ª parte'}}</button></div>
        <div v-else class="live-controls"><button class="football-button" @click="emit('advance',1)" :disabled="busy||match.status==='finished'">1 min</button><button class="football-button primary" @click="emit('advance',5)" :disabled="busy||match.status==='finished'">{{busy?'…':'5 min'}}</button><button class="football-button" @click="emit('advance',15)" :disabled="busy||match.status==='finished'">15 min</button><button class="football-button" @click="emit('chance')" :disabled="busy||match.status==='finished'">Hasta ocasión</button><button v-if="match.status==='finished'" class="football-button primary" :disabled="busy" @click="emit('close')">{{busy?'Cerrando…':'Cerrar partido'}}</button></div>
      </div>

      <div class="match-world-context d8-world-context">
        <span><small>RIVAL</small><strong>{{opponent.team_name || (ownHome?match.away_team_name:match.home_team_name)}}</strong><em>{{coachStyle}}</em></span>
        <span><small>ÁRBITRO</small><strong>{{match.referee?.name || 'Sin designación'}}</strong><em>{{refereeStyle}}</em></span>
        <span><small>ESCENARIO</small><strong>{{match.venue?.name || 'Estadio por confirmar'}}</strong><em><template v-if="match.venue?.capacity">{{Number(match.venue.capacity).toLocaleString('es-ES')}} espectadores</template><template v-if="match.venue?.width_m && match.venue?.length_m"> · {{match.venue.length_m}}×{{match.venue.width_m}} m</template></em></span>
      </div>

      <div class="live-layout">
        <article class="football-panel live-commentary modern-commentary" :class="{ preflight: match.minute===0, finished: match.status==='finished' }">
          <header class="simple-panel-head"><span><small>{{match.minute===0?'ANTES DEL PARTIDO':match.status==='finished'?'POSTPARTIDO':'RELATO'}}</small><strong>{{match.minute===0?'Todo preparado':match.status==='finished'?'Partido terminado':'Directo'}}</strong></span></header>
          <section v-if="match.minute===0" class="prematch-elevens" aria-label="Onces titulares confirmados">
            <header><span><small>ONCES CONFIRMADOS</small><strong>Los 22 que empiezan el partido</strong></span><em>{{match.fixture?.competition_name || leagueName || 'Partido'}}</em></header>
            <div class="prematch-elevens-grid">
              <article class="prematch-xi home-xi"><div class="prematch-xi-title"><strong>{{match.home_team_name}}</strong><span>Local</span></div><ol><li v-for="p in homeLineup" :key="p.id"><span class="prematch-player-photo"><PersonAvatar :person="lineupPerson(p)" :size="30" :height="38" :shirt-number="p.shirt_number || p.number" variant="player" decorative /><i>{{p.shirt_number || p.number || '•'}}</i></span><span><b>{{p.display_name}}</b><small>{{p.position || '—'}}</small></span></li></ol></article>
              <div class="prematch-versus"><b>VS</b><span>{{formation}}<template v-if="opponent.tactics?.formation"> · {{opponent.tactics.formation}}</template></span></div>
              <article class="prematch-xi away-xi"><div class="prematch-xi-title"><strong>{{match.away_team_name}}</strong><span>Visitante</span></div><ol><li v-for="p in awayLineup" :key="p.id"><span class="prematch-player-photo"><PersonAvatar :person="lineupPerson(p)" :size="30" :height="38" :shirt-number="p.shirt_number || p.number" variant="player" decorative /><i>{{p.shirt_number || p.number || '•'}}</i></span><span><b>{{p.display_name}}</b><small>{{p.position || '—'}}</small></span></li></ol></article>
            </div>
          </section>
          <div v-if="match.minute===0" class="match-preview-v2 d7-match-preview">
            <div class="preview-primary"><small>PLAN DEL RIVAL</small><strong>{{opponent.manager?.display_name || 'Entrenador rival'}} · {{opponent.tactics?.formation || '—'}}</strong><span>{{knownTacticalPlan}}</span><em v-if="opponentReport.name">Informe de {{opponentReport.name}} · {{opponentReport.quality_label || 'calidad por evaluar'}} · confianza {{opponentReport.confidence || '—'}}%</em></div>
            <div class="preview-counterplan"><small>CÓMO TE HAN PREPARADO</small><strong>{{preparationLabel}}</strong><span v-if="preparation.context?.phase">Contexto: {{preparation.context.phase}} · intensidad {{preparation.preparation_intensity || 'media'}}</span><span v-for="(item,index) in preparation.adjustments || []" :key="index">{{item}}</span><span v-if="!(preparation.adjustments||[]).length">Mantienen su identidad base; no han encontrado una contramedida clara.</span><em v-if="preparation.phase_focus">{{preparation.phase_focus}}</em><em v-if="preparation.learning_note">Memoria del técnico: {{preparation.learning_note}}</em><em v-if="preparation.threat_profile?.labels?.length">Te señalan: {{preparation.threat_profile.labels.join(' · ')}}</em></div>
            <div class="preview-key-players"><small>HOMBRES A VIGILAR</small><span v-for="p in opponent.key_players || []" :key="p.id"><b>{{p.display_name}}</b><em>{{p.position}} · {{p.identity}} · nivel {{opponentPlayerLevel(p)}}<template v-if="p.overall_is_exact === false"> estimado</template></em></span><span v-if="!(opponent.key_players||[]).length"><b>Sin informe previo</b><em>El partido revelará sus amenazas.</em></span></div>
            <div class="preview-ready"><b>XI confirmado: {{match.controlled_on_pitch.length}}</b><span>{{match.controlled_bench.length}} en banquillo · máximo 2 cambios</span><em>El reloj no corre hasta que tú decidas.</em></div>
          </div>
          <div v-if="match.minute===0" class="preflight-selection d9-preflight-selection">
            <header><span><small>TU EQUIPO</small><strong>Último control antes de empezar</strong></span><em>{{formation}} · {{tacticalIdentity.formation_label || 'plan actual'}}</em></header>
            <div class="preflight-note"><b>La previa todavía es reversible.</b><span>“Revisar XI” cancela esta previa y reconstruirá los onces con tus cambios. “Táctica” mantiene el XI y aplica el ajuste al partido.</span></div>
            <div v-if="(match.controlled_absences||[]).length" class="preflight-note"><b>Bajas conocidas antes del partido</b><span>{{match.controlled_absences.map(row=>`${row.name}: ${row.status}`).join(' · ')}}</span></div>
            <div class="preflight-selection-grid"><span v-for="p in match.controlled_on_pitch" :key="p.id"><b>{{p.display_name}}</b><em>{{p.position}} · {{p.match_condition}}%</em></span></div>
            <footer><b>Banquillo</b><span>{{(match.controlled_bench || []).map(p=>p.display_name).join(' · ') || 'Sin suplentes disponibles'}}</span></footer>
          </div>
          <div v-if="match.status==='finished'" class="match-post-v2 d7-match-post">
            <div class="post-verdict"><small>LECTURA INMEDIATA</small><strong>{{resultSummary}}</strong><span>{{ownStats?.possession ?? 50}}% posesión · {{ownStats?.shots ?? 0}} tiros · {{ownStats?.shots_on_target ?? 0}} a puerta</span></div>
            <div class="post-causes"><small>MOMENTOS QUE CAMBIARON EL PARTIDO</small><span v-for="(e,index) in decisiveEvents" :key="`${e.minute}-${e.kind}-${index}`"><b>{{e.minute}}'</b><em>{{e.detail || e.player_name || e.kind}}</em></span><span v-if="!decisiveEvents.length"><b>—</b><em>Partido sin un punto de ruptura claro.</em></span></div>
            <div v-if="match.diagnosis" class="post-diagnosis"><small>DIAGNÓSTICO DEL CUERPO TÉCNICO</small><strong>{{match.diagnosis.verdict}} · {{match.diagnosis.score}}</strong><span v-for="reason in match.diagnosis.reasons || []" :key="reason">{{reason}}</span><em v-for="action in match.diagnosis.next_actions || []" :key="action">→ {{action}}</em></div>
            <div v-if="match.committed" class="post-impact"><small>CONSECUENCIAS YA APLICADAS</small><span><b>Clasificación</b><strong>{{postPosition}}</strong></span><span><b>Moral</b><strong>{{dashboard.morale_average ?? '—'}}/100</strong></span><span><b>Consejo</b><strong>{{dashboard.board_confidence || 'A la espera'}}</strong></span><span><b>Siguiente</b><strong>{{nextOpponentName}}</strong><em>{{nextMatch?.date || 'fecha por confirmar'}}</em></span></div>
            <div v-if="bestPerformers.length" class="post-ratings"><small>NOTAS DEL EQUIPO</small><span v-for="row in bestPerformers" :key="row.player_id"><b>{{row.name || playerLabel(row.player_id)}}</b><strong>{{row.rating}}</strong><em>{{row.started?'Titular':'Suplente'}} · fatiga {{row.fatigue}}%</em></span></div>
          </div>
          <div v-if="match.minute>0" class="commentary-feed"><p v-for="(e,index) in events" :key="`${e.minute}-${e.kind}-${index}`" :class="[`event-${e.kind}`,eventClass(e)]"><b>{{e.minute}}'</b><span>{{e.detail || e.player_name || e.kind}}</span></p><div v-if="!events.length" class="match-kickoff-empty"><b>{{match.minute}}'</b><span>El relato aparecerá aquí cuando empiece a rodar el balón.</span></div></div>
        </article>

        <aside class="side-stack live-side-stack">
          <article class="football-panel live-stats modern-live-stats"><header class="simple-panel-head"><span><small>DATOS</small><strong>Partido</strong></span></header>
            <div class="live-stat-head"><span>{{match.home_team_name}}</span><span>{{match.away_team_name}}</span></div>
            <div class="live-stat-row"><b>{{match.home?.possession}}%</b><span>Posesión</span><b>{{match.away?.possession}}%</b></div>
            <div class="possession-track"><i :style="{width:`${match.home?.possession || 50}%`}"></i></div>
            <div class="live-stat-row"><b>{{match.home?.shots}}</b><span>Tiros</span><b>{{match.away?.shots}}</b></div><div class="live-stat-row"><b>{{match.home?.shots_on_target}}</b><span>A puerta</span><b>{{match.away?.shots_on_target}}</b></div><div class="live-stat-row"><b>{{match.home?.corners}}</b><span>Córners</span><b>{{match.away?.corners}}</b></div><div class="live-stat-row"><b>{{match.home?.fouls}}</b><span>Faltas</span><b>{{match.away?.fouls}}</b></div><div class="live-stat-row"><b>{{match.home?.yellow_cards}}</b><span>Amarillas</span><b>{{match.away?.yellow_cards}}</b></div><div class="live-stat-row"><b>{{match.home?.red_cards}}</b><span>Rojas</span><b>{{match.away?.red_cards}}</b></div><div class="live-stat-row"><b>{{match.home?.offsides}}</b><span>Fueras de juego</span><b>{{match.away?.offsides}}</b></div>
          </article>

          <article v-if="match.minute>0 && match.status!=='finished' && (match.bench_advice||[]).length" class="football-panel bench-advice"><header class="simple-panel-head"><span><small>CUERPO TÉCNICO</small><strong>Lectura del partido</strong></span><b>{{match.bench_advice.length}}</b></header><div v-for="item in match.bench_advice" :key="`${item.kind}-${item.title}`" class="bench-advice-row" :class="item.priority"><strong>{{item.title}}</strong><span>{{item.detail}}</span><em v-if="item.suggested_change">Ajuste sugerido disponible en Tácticas</em></div></article>
          <article v-if="match.minute>0 && (match.controlled_performance||[]).length" class="football-panel live-performance"><header class="simple-panel-head"><span><small>RENDIMIENTO</small><strong>Lectura individual</strong></span></header><div class="performance-grid"><span v-for="row in match.controlled_performance.slice(0,8)" :key="row.player_id"><b>{{playerLabel(row.player_id)}}</b><strong>{{row.rating}}</strong><em>fatiga {{row.fatigue}}%</em></span></div></article>

          <article v-if="match.minute>0 && match.status!=='finished'" class="football-panel live-bench modern-live-bench"><header class="simple-panel-head"><span><small>BANQUILLO</small><strong>Cambios</strong></span><b>{{substitutionsUsed}}/2 usados</b></header>
            <div v-if="(match.controlled_sent_off||[]).length" class="live-dismissal-note"><b>Con {{match.controlled_on_pitch.length}} jugadores</b><span>{{(match.controlled_sent_off||[]).map(p=>p.display_name).join(' · ')}} expulsado. Una roja no se puede reemplazar.</span></div>
            <div v-if="forcedOff.length" class="live-forced-injury-note"><b>{{forcedOff.map(p=>p.display_name).join(' · ')}} no puede continuar</b><span v-if="substitutionsRemaining>0">Sustitución necesaria. El futbolista ya no participa mientras preparas el cambio.</span><span v-else>Sin cambios disponibles: el equipo continúa con {{match.controlled_on_pitch.length}} jugadores.</span></div>
            <div v-if="substitutionsRemaining===0" class="live-sub-limit"><b>Sin cambios disponibles</b><span>Has utilizado los dos permitidos en 1993-94.</span></div>
            <label><span>Sale</span><select :disabled="busy||!canSubstitute" :value="outgoingId ?? ''" @change="emit('update:outgoingId', $event.target.value ? Number($event.target.value) : null)"><option value="">{{forcedOff.length?'Selecciona al lesionado que debe salir':'Selecciona jugador en campo'}}</option><option v-for="p in replaceablePlayers" :key="p.id" :value="p.id">{{forcedOff.some(row=>Number(row.id)===Number(p.id))?'LESIONADO · ':''}}{{p.display_name}} · {{p.position}} · {{p.match_condition}}%</option></select></label>
            <label><span>Entra</span><select :disabled="busy||!canSubstitute" :value="incomingId ?? ''" @change="emit('update:incomingId', $event.target.value ? Number($event.target.value) : null)"><option value="">Selecciona suplente</option><option v-for="p in match.controlled_bench" :key="p.id" :value="p.id">{{p.display_name}} · {{p.position}} · {{p.match_condition}}%</option></select></label>
            <div class="bench-actions"><button class="football-button primary" @click="emit('substitute')" :disabled="busy||!canSubstitute">{{busy?'Procesando…':'Hacer cambio'}}</button><button class="football-button" @click="emit('open-tactics')" :disabled="busy">Ajustar táctica</button></div>
          </article>
        </aside>
      </div>
    </template>
    <div v-else class="football-panel empty-football-state">No hay partido en directo. <button class="football-button" @click="emit('back')">Volver</button></div>
  </section>
</template>

<style scoped>
.bench-advice-row{display:grid;gap:4px;padding:10px 0;border-bottom:1px solid var(--line,#d7dde6)}.bench-advice-row:last-child{border-bottom:0}.bench-advice-row span,.bench-advice-row em{font-size:11px;color:var(--text-soft,#687386)}.bench-advice-row.high strong{font-weight:900}.performance-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px}.performance-grid span{display:grid;grid-template-columns:1fr auto;gap:2px 8px;padding:7px;border-radius:8px;background:var(--surface-soft,#f5f7fa)}.performance-grid span em{grid-column:1/3;font-size:10px;color:var(--text-soft,#687386)}.post-diagnosis{display:grid;gap:5px;padding:12px;border-radius:10px;background:var(--surface-soft,#f5f7fa)}.post-diagnosis small{font-size:10px;font-weight:900;letter-spacing:.08em}.post-diagnosis span,.post-diagnosis em{font-size:11px}.post-diagnosis em{color:var(--text-soft,#687386)}
.preflight-note{display:grid;gap:2px;margin:8px 0;padding:8px 10px;border:1px solid var(--line,#d7dde6);border-radius:8px;background:var(--surface-soft,#f5f7fa)}.preflight-note b{font-size:11px}.preflight-note span{font-size:11px;color:var(--text-soft,#687386)}.prematch-controls{flex-wrap:wrap}
.post-impact{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;padding:12px;border:1px solid var(--line,#d7dde6);border-radius:10px}.post-impact>small,.post-ratings>small{grid-column:1/-1;font-size:11px;font-weight:900;letter-spacing:.08em;color:var(--text-soft,#687386)}.post-impact>span{display:grid;gap:2px}.post-impact b{font-size:11px;color:var(--text-soft,#687386)}.post-impact strong{font-size:12px}.post-impact em{font-size:11px;font-style:normal;color:var(--text-soft,#687386)}.post-ratings{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:7px;padding:12px;border:1px solid var(--line,#d7dde6);border-radius:10px}.post-ratings>span{display:grid;grid-template-columns:1fr auto;gap:2px 6px}.post-ratings>span b{font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.post-ratings>span strong{font-size:13px}.post-ratings>span em{grid-column:1/-1;font-size:11px;font-style:normal;color:var(--text-soft,#687386)}@media(max-width:1000px){.post-impact{grid-template-columns:1fr 1fr}.post-ratings{grid-template-columns:1fr 1fr}}
.live-dismissal-note,.live-sub-limit,.live-forced-injury-note{display:grid;gap:3px;padding:8px 10px;margin-bottom:8px;border:1px solid var(--line,#d7dde6);border-radius:8px;background:var(--surface-soft,#f5f7fa)}.live-dismissal-note b,.live-sub-limit b,.live-forced-injury-note b{font-size:11px}.live-dismissal-note span,.live-sub-limit span,.live-forced-injury-note span{font-size:11px;color:var(--text-soft,#687386)}.halftime-label{font-size:11px;font-weight:800;color:var(--text-soft,#687386);align-self:center}
</style>
