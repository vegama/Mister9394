<script setup>
import { computed } from 'vue'

const props = defineProps({
  match: { type: Object, default: null },
  season: { type: String, default: '1993-94' },
  formation: { type: String, default: '4-4-2' },
  tacticalIdentity: { type: Object, default: () => ({}) },
  events: { type: Array, default: () => [] },
  outgoingId: { type: [Number, String], default: null },
  incomingId: { type: [Number, String], default: null },
  leagueName: { type: String, default: '' },
})
const emit = defineEmits(['update:outgoingId','update:incomingId','advance','chance','close','substitute','open-tactics','back'])

const statusLabel = computed(() => props.match?.status === 'halftime' ? 'DESCANSO' : props.match?.status === 'finished' ? 'FINAL' : props.match?.minute === 0 ? 'PREVIA' : 'EN JUEGO')
const notableKinds = new Set(['goal','chance','penalty','penalty_saved','free_kick','free_kick_chance','set_piece_chance','defensive_error','second_ball','shot_off','save','corner','yellow','red','second_yellow_red','injury','injury_substitution','tactical_adjustment','halftime','fulltime'])
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
const resultSummary = computed(() => {
  if(props.match?.status!=='finished')return ''
  const gf=Number(ownStats.value?.goals||0), ga=Number(opponentStats.value?.goals||0)
  const verdict=gf>ga?'Victoria':gf<ga?'Derrota':'Empate'
  const shots=Number(ownStats.value?.shots||0)-Number(opponentStats.value?.shots||0)
  const shotText=shots>2?'generaste más volumen de tiro':shots<-2?'el rival generó más remates':'el volumen de tiro estuvo equilibrado'
  return `${verdict}: ${gf}-${ga}. ${shotText}.`
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

      <div class="live-command-bar">
        <div><small>PLAN ACTUAL</small><strong>{{formation}} · {{tacticalIdentity.formation_label}}</strong><span class="live-context-line"><template v-if="match.venue?.name">{{match.venue.name}}<template v-if="match.venue?.city_name"> · {{match.venue.city_name}}</template></template><template v-if="match.referee?.name"> · Árbitro: {{match.referee.name}}</template></span></div>
        <div class="live-controls"><button class="football-button" @click="emit('advance',1)" :disabled="match.status==='finished'">1 min</button><button class="football-button primary" @click="emit('advance',5)" :disabled="match.status==='finished'">5 min</button><button class="football-button" @click="emit('advance',15)" :disabled="match.status==='finished'">15 min</button><button class="football-button" @click="emit('chance')" :disabled="match.status==='finished'">Hasta ocasión</button><button v-if="match.status==='halftime'" class="football-button primary" @click="emit('advance',1)">Segunda parte</button><button v-if="match.status==='finished'" class="football-button primary" @click="emit('close')">Cerrar partido</button></div>
      </div>

      <div class="match-world-context d8-world-context">
        <span><small>RIVAL</small><strong>{{opponent.team_name || (ownHome?match.away_team_name:match.home_team_name)}}</strong><em>{{coachStyle}}</em></span>
        <span><small>ÁRBITRO</small><strong>{{match.referee?.name || 'Sin designación'}}</strong><em>{{refereeStyle}}</em></span>
        <span><small>ESCENARIO</small><strong>{{match.venue?.name || 'Estadio por confirmar'}}</strong><em><template v-if="match.venue?.capacity">{{Number(match.venue.capacity).toLocaleString('es-ES')}} espectadores</template><template v-if="match.venue?.width_m && match.venue?.length_m"> · {{match.venue.length_m}}×{{match.venue.width_m}} m</template></em></span>
      </div>

      <div class="live-layout">
        <article class="football-panel live-commentary modern-commentary" :class="{ preflight: match.minute===0, finished: match.status==='finished' }">
          <header class="simple-panel-head"><span><small>{{match.minute===0?'ANTES DEL PARTIDO':match.status==='finished'?'POSTPARTIDO':'RELATO'}}</small><strong>{{match.minute===0?'Todo preparado':match.status==='finished'?'Partido terminado':'Directo'}}</strong></span></header>
          <div v-if="match.minute===0" class="match-preview-v2 d7-match-preview">
            <div class="preview-primary"><small>PLAN DEL RIVAL</small><strong>{{opponent.manager?.display_name || 'Entrenador rival'}} · {{opponent.tactics?.formation || '—'}}</strong><span>{{knownTacticalPlan}}</span><em v-if="opponentReport.name">Informe de {{opponentReport.name}} · {{opponentReport.quality_label || 'calidad por evaluar'}} · confianza {{opponentReport.confidence || '—'}}%</em></div>
            <div class="preview-counterplan"><small>CÓMO TE HAN PREPARADO</small><strong>{{preparationLabel}}</strong><span v-if="preparation.context?.phase">Contexto: {{preparation.context.phase}} · intensidad {{preparation.preparation_intensity || 'media'}}</span><span v-for="(item,index) in preparation.adjustments || []" :key="index">{{item}}</span><span v-if="!(preparation.adjustments||[]).length">Mantienen su identidad base; no han encontrado una contramedida clara.</span><em v-if="preparation.phase_focus">{{preparation.phase_focus}}</em><em v-if="preparation.learning_note">Memoria del técnico: {{preparation.learning_note}}</em><em v-if="preparation.threat_profile?.labels?.length">Te señalan: {{preparation.threat_profile.labels.join(' · ')}}</em></div>
            <div class="preview-key-players"><small>HOMBRES A VIGILAR</small><span v-for="p in opponent.key_players || []" :key="p.id"><b>{{p.display_name}}</b><em>{{p.position}} · {{p.identity}} · nivel {{opponentPlayerLevel(p)}}<template v-if="p.overall_is_exact === false"> estimado</template></em></span><span v-if="!(opponent.key_players||[]).length"><b>Sin informe previo</b><em>El partido revelará sus amenazas.</em></span></div>
            <div class="preview-ready"><b>XI confirmado: {{match.controlled_on_pitch.length}}</b><span>{{match.controlled_bench.length}} en banquillo · máximo 2 cambios</span><em>El reloj no corre hasta que tú decidas.</em></div>
          </div>
          <div v-if="match.minute===0" class="preflight-selection d9-preflight-selection">
            <header><span><small>TU EQUIPO</small><strong>Último control antes de empezar</strong></span><em>{{formation}} · {{tacticalIdentity.formation_label || 'plan actual'}}</em></header>
            <div class="preflight-selection-grid"><span v-for="p in match.controlled_on_pitch" :key="p.id"><b>{{p.display_name}}</b><em>{{p.position}} · {{p.match_condition}}%</em></span></div>
            <footer><b>Banquillo</b><span>{{(match.controlled_bench || []).map(p=>p.display_name).join(' · ') || 'Sin suplentes disponibles'}}</span></footer>
          </div>
          <div v-if="match.status==='finished'" class="match-post-v2 d7-match-post">
            <div class="post-verdict"><small>LECTURA INMEDIATA</small><strong>{{resultSummary}}</strong><span>{{ownStats?.possession ?? 50}}% posesión · {{ownStats?.shots ?? 0}} tiros · {{ownStats?.shots_on_target ?? 0}} a puerta</span></div>
            <div class="post-causes"><small>MOMENTOS QUE CAMBIARON EL PARTIDO</small><span v-for="(e,index) in decisiveEvents" :key="`${e.minute}-${e.kind}-${index}`"><b>{{e.minute}}'</b><em>{{e.detail || e.player_name || e.kind}}</em></span><span v-if="!decisiveEvents.length"><b>—</b><em>Partido sin un punto de ruptura claro.</em></span></div>
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

          <article v-if="match.status!=='finished'" class="football-panel live-bench modern-live-bench"><header class="simple-panel-head"><span><small>BANQUILLO</small><strong>Cambios</strong></span><b>Máx. 2</b></header>
            <label><span>Sale</span><select :value="outgoingId ?? ''" @change="emit('update:outgoingId', $event.target.value ? Number($event.target.value) : null)"><option value="">Selecciona titular</option><option v-for="p in match.controlled_on_pitch" :key="p.id" :value="p.id">{{p.display_name}} · {{p.position}} · {{p.match_condition}}%</option></select></label>
            <label><span>Entra</span><select :value="incomingId ?? ''" @change="emit('update:incomingId', $event.target.value ? Number($event.target.value) : null)"><option value="">Selecciona suplente</option><option v-for="p in match.controlled_bench" :key="p.id" :value="p.id">{{p.display_name}} · {{p.position}} · {{p.match_condition}}%</option></select></label>
            <div class="bench-actions"><button class="football-button primary" @click="emit('substitute')" :disabled="match.status==='finished'">Hacer cambio</button><button class="football-button" @click="emit('open-tactics')" :disabled="match.status==='finished'">Ajustar táctica</button></div>
          </article>
        </aside>
      </div>
    </template>
    <div v-else class="football-panel empty-football-state">No hay partido en directo. <button class="football-button" @click="emit('back')">Volver</button></div>
  </section>
</template>
