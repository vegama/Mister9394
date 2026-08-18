<script setup>
import { computed } from 'vue'
import BaseModal from '../../components/BaseModal.vue'
import PersonAvatar from '../../components/PersonAvatar.vue'
import UiTabs from '../../components/ui/UiTabs.vue'

const props = defineProps({
  player: { type: Object, required: true },
  tab: { type: String, default: 'profile' },
  embedded: { type: Boolean, default: false },
  season: { type: String, default: '1993-94' },
})
const emit = defineEmits(['close', 'update:tab', 'promise-role', 'scout-player', 'open-team'])

const tabs = [
  { id: 'profile', label: 'Resumen' }, { id: 'attributes', label: 'Atributos' },
  { id: 'season', label: 'Temporada' }, { id: 'contract', label: 'Contrato' },
  { id: 'medical', label: 'Lesiones' }, { id: 'career', label: 'Historial' },
  { id: 'scout', label: 'Informe' },
]
const tabModel = computed({ get: () => props.tab, set: value => emit('update:tab', value) })
const p = computed(() => props.player || {})
const displayName = computed(() => p.value.display_name || p.value.full_name || p.value.name || 'Jugador')
const overall = computed(() => Number(p.value.overall ?? p.value.rating ?? 0))
const overallDisplay = computed(() => { const r=p.value.overall_range; return p.value.overall_is_exact===false && Array.isArray(r) ? `${r[0]}–${r[1]}` : (overall.value || '—') })
const positions = computed(() => {
  const raw = p.value.positions
  if (Array.isArray(raw)) return raw
  if (raw && typeof raw === 'object') return [raw.primary, ...(raw.secondary || [])].filter(Boolean)
  return [p.value.position].filter(Boolean)
})
const positionProfiles = computed(() => p.value.position_profiles || [])
const attributes = computed(() => p.value.attributes || {})
const attributeLabels = {
  technique:'Técnica', short_pass:'Pase corto', long_pass:'Pase largo', crossing:'Centro', dribbling:'Regate', finishing:'Finalización',
  heading:'Cabeza', set_pieces:'Balón parado', pace:'Velocidad', acceleration:'Aceleración', stamina:'Resistencia', strength:'Fuerza', jumping:'Salto', agility:'Agilidad',
  positioning:'Colocación', anticipation:'Anticipación', vision:'Visión', off_ball:'Desmarque', discipline:'Disciplina', leadership:'Liderazgo', aggression:'Agresividad', consistency:'Regularidad',
  work_rate:'Trabajo', tackling:'Entrada', marking:'Marcaje', interception:'Intercepción', goalkeeping:'Portero', reflexes:'Reflejos', aerial_goalkeeping:'Juego aéreo', shot_power:'Potencia', free_kicks:'Faltas', penalties:'Penaltis',
}
const attributeGroups = computed(() => [
  ['TÉCNICOS', [['Técnica','technique'],['Pase corto','short_pass'],['Pase largo','long_pass'],['Centro','crossing'],['Regate','dribbling'],['Finalización','finishing'],['Remate cabeza','heading'],['Balón parado','set_pieces'],['Potencia','shot_power'],['Faltas','free_kicks'],['Penaltis','penalties']]],
  ['FÍSICOS', [['Velocidad','pace'],['Aceleración','acceleration'],['Resistencia','stamina'],['Fuerza','strength'],['Salto','jumping'],['Agilidad','agility']]],
  ['MENTALES', [['Colocación','positioning'],['Anticipación','anticipation'],['Visión','vision'],['Desmarque','off_ball'],['Trabajo','work_rate'],['Disciplina','discipline'],['Liderazgo','leadership'],['Agresividad','aggression'],['Regularidad','consistency']]],
  ['DEFENSIVOS / PORTERO', [['Entrada','tackling'],['Marcaje','marking'],['Intercepción','interception'],['Portero','goalkeeping'],['Reflejos','reflexes'],['Juego aéreo','aerial_goalkeeping']]],
])
const valueOf = key => {
  const value = attributes.value?.[key] ?? p.value?.[key]
  return Number.isFinite(Number(value)) ? Number(value) : '—'
}
const rangeOf = key => { const r=p.value.attribute_ranges?.[key]; return Array.isArray(r)?`${r[0]}–${r[1]}`:null }
const displayAttribute = key => rangeOf(key) || valueOf(key)
const toneFor = value => {
  const n=Number(value); if(!Number.isFinite(n)) return 'unknown'
  if(n>=90)return 'world'; if(n>=82)return 'elite'; if(n>=72)return 'good'; if(n>=60)return 'average'; return 'weak'
}
const topAttributes = computed(() => Object.entries(attributeLabels).map(([key,label])=>({key,label,value:valueOf(key)})).filter(x=>Number.isFinite(Number(x.value)) && Number(x.value)>0).sort((a,b)=>Number(b.value)-Number(a.value)).slice(0,7))
const seasonStats = computed(() => p.value.season_stats || {})
const contract = computed(() => p.value.contract || {})
const medical = computed(() => p.value.medical || {})
const scout = computed(() => p.value.scout || {})
const identity = computed(() => p.value.identity || {})
const dynamics = computed(() => p.value.squad_dynamics || {})
const managerRelationship = computed(() => p.value.manager_relationship || {})
const rolePromise = computed(() => p.value.role_promise || null)
const tacticalFit = computed(() => p.value.tactical_fit || {})
const development = computed(() => p.value.development || {})
const clubMonogram = computed(() => String(p.value.team_name || 'FC').split(/\s+/).filter(Boolean).slice(0,2).map(v=>v[0]).join('').toUpperCase())
const playerAssetId = computed(() => Number(p.value.id ?? p.value.source_id ?? 0) || null)
const photoPerson = computed(() => ({...p.value, photo_url: p.value.photo_url || (playerAssetId.value ? `/historical9394/players/${playerAssetId.value}.jpg` : null)}))
const crestUrl = computed(() => p.value.team_crest_url || (p.value.team_id ? `/historical9394/clubs/${Number(p.value.team_id)}.gif` : null))
const ratingLabel = computed(() => { if(p.value.overall_is_exact===false)return scout.value.knowledge||'ESTIMACIÓN'; const v=overall.value; return v>=92?'REFERENCIA MUNDIAL':v>=86?'ESTRELLA':v>=80?'ALTO NIVEL':v>=72?'TITULAR DE NIVEL':v>=64?'COMPETITIVO':'DESARROLLO' })
const satisfactionTone = computed(() => Number(dynamics.value.satisfaction ?? 70) >= 70 ? 'good' : Number(dynamics.value.satisfaction ?? 70) >= 48 ? 'warn' : 'bad')
const availabilityLabel = computed(() => {
  const status=String(p.value.status || '')
  if(status && status!=='Disponible')return status
  return medical.value.status || status || 'Disponible'
})
const rolePromiseStatus = computed(() => ({active:'En curso',on_track:'Bien encaminada',at_risk:'En riesgo',kept:'Cumplida',broken:'Incumplida'}[rolePromise.value?.status] || rolePromise.value?.status || '—'))
const fitReasons = computed(() => tacticalFit.value.reasons || [])
const bodySummary = computed(() => [p.value.age!=null?`${p.value.age} años`:null,p.value.height_cm?`${Math.round(p.value.height_cm)} cm`:null,p.value.weight_kg?`${Math.round(p.value.weight_kg)} kg`:null,p.value.preferred_foot?`Pie ${String(p.value.preferred_foot).toLowerCase()}`:null].filter(Boolean).join(' · '))
const pitchStyle = profile => {
  const slot=String(profile?.squad_slot||'').toUpperCase()
  const map={GK:[50,88],RB:[84,69],LB:[16,69],CB:[50,68],DM:[50,55],CM:[50,45],RM:[84,43],LM:[16,43],AM:[50,31],RW:[82,20],LW:[18,20],ST:[50,13]}
  const [left,top]=map[slot]||[50,45]
  let dx=0
  if(slot==='CB') dx=(Number(profile.source_id||0)%3-1)*18
  if(slot==='CM') dx=(Number(profile.source_id||0)%3-1)*16
  return {left:`${left+dx}%`,top:`${top}%`}
}
</script>

<template>
<BaseModal :embedded="embedded" size="full" layer="entity" panel-class="football9394-player-modal player-profile-v2" close-label="Cerrar ficha del jugador" aria-label="Ficha futbolista 1993-94" @close="emit('close')">
  <template #header>
    <div class="player-hero-v2">
      <button v-if="player.team_id" type="button" class="player-hero-club player-hero-club-link" :aria-label="`Abrir ficha de ${player.team_name||'club'}`" @click="emit('open-team',player.team_id)"><div class="player-hero-crest"><img v-if="crestUrl" :src="crestUrl" alt=""><span v-else>{{clubMonogram}}</span></div><small>{{player.team_name || 'SIN CLUB'}}</small><span>Ver club →</span></button>
      <div v-else class="player-hero-club"><div class="player-hero-crest"><img v-if="crestUrl" :src="crestUrl" alt=""><span v-else>{{clubMonogram}}</span></div><small>{{player.team_name || 'SIN CLUB'}}</small></div>
      <div class="player-hero-copy">
        <span class="player-eyebrow">#{{player.shirt_number ?? '—'}} · {{positions[0] || player.position || 'Sin demarcación'}} · {{player.nationality || '—'}}</span>
        <h2>{{displayName}}</h2>
        <p>{{bodySummary || 'Perfil histórico'}} </p>
        <div class="player-hero-tags"><span v-if="player.historical_squad_1994" class="usa94-profile-tag">USA 94 · {{player.nationality}} · #{{player.world_cup_1994?.shirt_number}}</span><span>{{identity.archetype || 'Perfil por definir'}}</span><span>{{dynamics.role || 'Plantilla'}}</span><span :class="availabilityLabel==='Disponible'?'ok':'alert'">{{availabilityLabel}}</span></div>
        <div v-if="player.league_suspension_active_for_next_match" class="player-profile-availability-alert"><b>Sanción para el próximo partido de liga</b><span>{{player.league_suspension_reason || 'Sanción disciplinaria'}} · {{player.league_suspension_matches}} partido{{Number(player.league_suspension_matches)===1?'':'s'}}</span></div>
      </div>
      <div class="player-hero-rating"><small>NIVEL ACTUAL</small><b>{{overallDisplay}}</b><strong>{{ratingLabel}}</strong></div>
      <div class="player-hero-photo"><PersonAvatar :person="photoPerson" :size="188" :height="252" decorative /></div>
    </div>
    <div class="player-pulse-strip">
      <span><small>Encaje con tu plan</small><b>{{tacticalFit.label || '—'}}<em v-if="tacticalFit.score">{{tacticalFit.score}}/100</em></b></span>
      <span><small>Forma</small><b>{{player.form ?? '—'}}<em>actual</em></b></span>
      <span><small>Moral</small><b>{{player.morale ?? '—'}}<em>vestuario</em></b></span>
      <span><small>Jerarquía</small><b>{{dynamics.role || '—'}}<em>{{dynamics.satisfaction ?? 70}}/100</em></b></span>
      <span><small>Valor estimado</small><b>{{player.market_value_display || '—'}}</b></span>
      <span><small>Contrato</small><b>{{contract.end || '—'}}<em v-if="contract.salary_display">{{contract.salary_display}}</em></b></span>
    </div>
  </template>

  <div class="f9394-profile-shell player-profile-v2-shell">
    <UiTabs v-model="tabModel" class="f9394-profile-tabs" :items="tabs" aria-label="Secciones de la ficha" />

    <section v-if="tabModel==='profile'" class="player-overview-v2">
      <main class="player-overview-main">
        <article class="player-story-card">
          <div class="player-story-heading"><small>IDENTIDAD FUTBOLÍSTICA</small><h3>{{identity.archetype || 'Perfil por definir'}}</h3><p>{{identity.description || 'Sus roles y atributos irán definiendo cómo puede ayudarte.'}}</p></div>
          <div class="player-traits-v2"><span v-for="trait in identity.traits || []" :key="trait.code" :class="`trait-${trait.polarity||'neutral'}`" :title="trait.effect">{{trait.label}}</span><span v-if="!(identity.traits||[]).length">Sin tendencia destacada</span></div>
          <div class="player-fit-story"><div><small>POR QUÉ ENCAJA</small><strong>{{tacticalFit.label || 'Sin evaluar'}} · {{tacticalFit.score ?? '—'}}/100</strong></div><ul><li v-for="reason in fitReasons" :key="reason">{{reason}}</li><li v-if="!fitReasons.length">El encaje depende de las órdenes, el puesto y los compañeros elegidos.</li></ul></div>
        </article>

        <article class="player-role-card-v2">
          <header><div><small>DEMARCACIONES</small><h3>Dónde puede jugar</h3></div><span>{{positions.length}} perfil{{positions.length===1?'':'es'}}</span></header>
          <div class="player-role-layout">
            <div class="player-position-pitch"><div class="pitch-lines"><i></i></div><span v-for="profile in positionProfiles" :key="profile.source_id" class="role-map-token" :class="{primary:profile.primary}" :style="pitchStyle(profile)"><b>{{profile.code}}</b><small>{{profile.aptitude}}</small></span><span v-if="!positionProfiles.length" class="role-map-token primary" style="left:50%;top:20%"><b>{{player.position_short || '—'}}</b><small>100</small></span></div>
            <div class="role-profile-list"><div v-for="profile in positionProfiles" :key="profile.source_id"><span><strong>{{profile.name}}</strong><small>{{profile.squad_slot}}<template v-if="profile.primary"> · natural</template></small></span><b>{{profile.aptitude}}</b></div><div v-if="!positionProfiles.length"><span><strong>{{positions[0] || 'Sin posición'}}</strong><small>posición principal</small></span><b>100</b></div></div>
          </div>
        </article>

        <article class="player-season-v2">
          <header><div><small>TEMPORADA {{props.season}}</small><h3>Qué está aportando</h3></div><button type="button" class="text-action" @click="tabModel='season'">Ver detalle →</button></header>
          <div class="player-season-kpis"><span><small>PARTIDOS</small><b>{{seasonStats.appearances ?? 0}}</b><em>{{seasonStats.starts ?? 0}} titular</em></span><span><small>MINUTOS</small><b>{{seasonStats.minutes ?? 0}}</b></span><span><small>GOLES</small><b>{{seasonStats.goals ?? 0}}</b></span><span><small>ASISTENCIAS</small><b>{{seasonStats.assists ?? 0}}</b></span><span><small>NOTA MEDIA</small><b>{{seasonStats.average_rating ?? '—'}}</b></span></div>
        </article>
      </main>

      <aside class="player-overview-rail">
        <article class="player-ability-card"><header><small>LO QUE LE HACE DIFERENTE</small><h3>Mejores recursos</h3></header><div class="ability-list-v2"><div v-for="item in topAttributes" :key="item.key"><span>{{item.label}}</span><div><i :style="{width:`${item.value}%`}"></i></div><b :class="toneFor(item.value)">{{item.value}}</b></div></div><button type="button" class="text-action full" @click="tabModel='attributes'">Todos los atributos →</button></article>

        <article class="player-situation-card"><header><small>VESTUARIO</small><h3>Situación</h3></header><div class="situation-score"><span><small>Jerarquía</small><strong>{{dynamics.role || '—'}}</strong></span><b :class="satisfactionTone">{{dynamics.satisfaction ?? 70}}<em>/100</em></b></div><div v-if="managerRelationship.label" class="manager-relationship-line"><span><small>RELACIÓN CONTIGO</small><strong>{{managerRelationship.label}}</strong></span><b>{{managerRelationship.trust}}/100</b></div><div v-if="rolePromise" class="role-promise-line"><span><small>ROL ACORDADO</small><strong>{{rolePromise.role}}</strong></span><b :class="rolePromise.status==='at_risk'?'bad':'good'">{{rolePromiseStatus}}</b><em>{{rolePromise.starts || 0}}/{{rolePromise.team_matches || 0}} titular · {{rolePromise.remaining_matches ?? 0}} partidos restantes</em></div><label v-if="managerRelationship.label" class="role-promise-action"><span>Acordar un rol</span><select value="" @change="event => { if(event.target.value){ emit('promise-role',{player:p,role:event.target.value}); event.target.value='' } }"><option value="">Elegir…</option><option>Figura</option><option>Titular</option><option>Rotación</option><option>Promesa</option><option>Fondo de plantilla</option></select></label><p v-if="dynamics.reasons?.length">{{dynamics.reasons.join(' · ')}}</p><p v-else>Sin conflicto relevante con su rol actual.</p><div v-if="dynamics.wants_move" class="player-tension-warning">Quiere abandonar el club.</div></article>

        <article class="player-detail-facts"><header><small>PERFIL</small><h3>Datos clave</h3></header><dl><div><dt>Pie</dt><dd>{{player.preferred_foot || '—'}}</dd></div><div><dt>Regularidad</dt><dd>{{valueOf('consistency')}}</dd></div><div><dt>Afecto afición</dt><dd>{{development.fan_affection ?? '—'}}<template v-if="development.fan_affection!=null">/9</template></dd></div><div><dt>Propensión lesión</dt><dd>{{medical.injury_proneness ?? '—'}}</dd></div><div><dt>Dorsal favorito</dt><dd>{{player.favorite_shirt_number || player.preferred_number || '—'}}</dd></div></dl></article>
      </aside>
    </section>

    <section v-else-if="tabModel==='attributes'" class="f9394-attribute-groups">
      <article v-for="group in attributeGroups" :key="group[0]" class="f9394-card"><h3>{{group[0]}}</h3><div v-for="item in group[1]" :key="item[1]" class="f9394-attribute-line"><span>{{item[0]}}</span><div class="f9394-meter"><i :style="{width:`${Number(valueOf(item[1]))||0}%`}"></i></div><b :class="toneFor(valueOf(item[1]))">{{displayAttribute(item[1])}}</b></div></article>
    </section>

    <section v-else-if="tabModel==='season'" class="f9394-card"><h3>TEMPORADA {{props.season}}</h3><div class="f9394-stat-grid"><div><span>PJ</span><b>{{seasonStats.appearances??0}}</b></div><div><span>TIT</span><b>{{seasonStats.starts??0}}</b></div><div><span>MIN</span><b>{{seasonStats.minutes??0}}</b></div><div><span>GOL</span><b>{{seasonStats.goals??0}}</b></div><div><span>ASI</span><b>{{seasonStats.assists??0}}</b></div><div><span>TA</span><b>{{seasonStats.yellow_cards??0}}</b></div><div><span>TR</span><b>{{seasonStats.red_cards??0}}</b></div><div><span>MEDIA</span><b>{{seasonStats.average_rating??'—'}}</b></div></div><p class="f9394-report" v-if="player.international_stats?.caps"><b>Selección:</b> {{player.international_stats.caps}} internacionalidades · {{player.international_stats.goals}} goles · {{player.international_stats.assists}} asistencias · {{player.international_stats.tournament_caps}} partidos de torneo.</p><div class="f9394-table-wrap" v-if="player.match_history?.length"><table><thead><tr><th>FECHA</th><th>COMPETICIÓN</th><th>RIVAL</th><th>RES.</th><th>G</th><th>A</th><th>TIROS</th><th>OC.</th><th>FIRMA</th><th>NOTA</th></tr></thead><tbody><tr v-for="(row,index) in [...player.match_history].reverse()" :key="`${row.date}-${index}`"><td>{{row.date}}</td><td>{{row.competition}}</td><td>#{{row.opponent_team_id}}</td><td>{{row.result}}</td><td>{{row.goals}}</td><td>{{row.assists}}</td><td>{{row.observable?.shots??0}}</td><td>{{row.observable?.chances_created??0}}</td><td>{{row.signature ? `${row.signature.primary} · ${row.signature.secondary}` : "—"}}</td><td><b :class="toneFor((Number(row.rating)-4)*16.6)">{{row.rating}}</b></td></tr></tbody></table></div><p v-else class="f9394-report">Todavía no ha disputado partidos detallados bajo tu dirección.</p></section>

    <section v-else-if="tabModel==='contract'" class="f9394-tab-grid f9394-contract-tab"><div class="f9394-card"><h3>CONTRATO</h3><dl class="f9394-data-grid"><div><dt>Inicio</dt><dd>{{contract.start||'—'}}</dd></div><div><dt>Final</dt><dd>{{contract.end||'—'}}</dd></div><div><dt>Ficha anual</dt><dd>{{contract.salary_display||'—'}}</dd></div><div><dt>Cláusula</dt><dd>{{contract.release_clause_display||'—'}}</dd></div><div><dt>Cesión</dt><dd>{{contract.loan?'Sí':'No'}}</dd></div><div><dt>Equipo propietario</dt><dd>{{contract.parent_club_name||player.team_name||'—'}}</dd></div></dl></div><div class="f9394-card"><h3>SITUACIÓN</h3><dl class="f9394-data-grid"><div><dt>Valor</dt><dd>{{player.market_value_display||'—'}}</dd></div><div><dt>Transferible</dt><dd>{{player.transfer_listed?'Sí':'No'}}</dd></div><div><dt>Cedido hasta</dt><dd>{{contract.loan_end||'—'}}</dd></div><div><dt>Dorsal favorito</dt><dd>{{player.preferred_number??player.favorite_shirt_number??'—'}}</dd></div></dl></div></section>

    <section v-else-if="tabModel==='medical'" class="f9394-card"><h3>HISTORIAL MÉDICO</h3><div class="f9394-medical-banner"><b>{{medical.status||'Disponible'}}</b><span>{{medical.current_injury?.name||'Sin lesión actual'}}</span></div><dl v-if="medical.current_injury" class="f9394-data-grid f9394-current-injury"><div><dt>Zona</dt><dd>{{medical.current_injury.body_area||'—'}}<template v-if="medical.current_injury.laterality"> · {{medical.current_injury.laterality}}</template></dd></div><div><dt>Vuelta prevista</dt><dd v-if="medical.current_injury.expected_return">{{medical.current_injury.expected_return}}</dd><dd v-else-if="medical.current_injury.estimated_return_from">{{medical.current_injury.estimated_return_from}} → {{medical.current_injury.estimated_return_to}}</dd><dd v-else>—</dd></div><div><dt>Días restantes</dt><dd>{{medical.current_injury.estimated_days_range ? `${medical.current_injury.estimated_days_range[0]}–${medical.current_injury.estimated_days_range[1]}` : (medical.injury_days??'—')}}</dd></div><div><dt>Recaída</dt><dd>{{medical.current_injury.recurrence?'Sí':'No'}}</dd></div></dl><p v-if="medical.assessment" class="f9394-report"><b>{{medical.assessment.responsible}}</b> · confianza {{medical.assessment.confidence}}% · {{medical.assessment.recommendation}}</p><div class="f9394-table-wrap"><table><thead><tr><th>LESIÓN</th><th>ZONA</th><th>LADO</th><th>INICIO</th><th>ALTA</th><th>DÍAS</th><th>RECAÍDA</th></tr></thead><tbody><tr v-for="(injury,index) in medical.history||[]" :key="`${injury.start}-${index}`"><td>{{injury.name}}</td><td>{{injury.body_area||'—'}}</td><td>{{injury.laterality||'—'}}</td><td>{{injury.start||'—'}}</td><td>{{injury.end||injury.expected_return||'—'}}</td><td>{{injury.days??'—'}}</td><td>{{injury.recurrence?'Sí':'No'}}</td></tr><tr v-if="!(medical.history||[]).length"><td colspan="7">Sin lesiones registradas.</td></tr></tbody></table></div></section>

    <section v-else-if="tabModel==='career'" class="f9394-card"><h3>TRAYECTORIA · LIGA</h3><p class="f9394-report">El histórico de temporada registra exclusivamente la competición de liga. Copa y competiciones europeas no inflan estos totales ni la nota media liguera.</p><div class="f9394-table-wrap"><table><thead><tr><th>TEMPORADA</th><th>PJ</th><th>TIT</th><th>MIN</th><th>G</th><th>A</th><th>TA</th><th>TR</th><th>MEDIA</th></tr></thead><tbody><tr v-for="(row,index) in player.career_seasons||[]" :key="`${row.season}-${index}`"><td><b>{{row.season}}</b></td><td>{{row.appearances??0}}</td><td>{{row.starts??0}}</td><td>{{row.minutes??0}}</td><td>{{row.goals??0}}</td><td>{{row.assists??0}}</td><td>{{row.yellow_cards??0}}</td><td>{{row.red_cards??0}}</td><td><b>{{row.average_rating??'—'}}</b></td></tr><tr v-if="!(player.career_seasons||[]).length"><td colspan="9">La trayectoria liguera de esta carrera se irá archivando al cerrar cada temporada.</td></tr></tbody></table></div></section>

    <section v-else-if="tabModel==='scout'" class="f9394-tab-grid"><div class="f9394-card"><h3>INFORME DEL TÉCNICO / OJEADOR</h3><p class="f9394-report">{{scout.summary||'Todavía no existe un informe suficiente sobre este jugador.'}}</p><dl class="f9394-data-grid"><div><dt>Conocimiento</dt><dd>{{scout.knowledge||'—'}}</dd></div><div><dt>Confianza</dt><dd>{{scout.confidence||'—'}}</dd></div><div><dt>Rol recomendado</dt><dd>{{scout.recommended_role||'—'}}</dd></div><div><dt>Encaje táctico</dt><dd>{{scout.tactical_fit||tacticalFit.label||'—'}}</dd></div></dl><button v-if="scout.level && scout.level<4" type="button" class="football-button primary" @click="emit('scout-player',p)">{{scout.level>=3?'Profundizar informe':'Encargar informe'}}</button></div><div class="f9394-card"><h3>PUNTOS FUERTES</h3><ul><li v-for="item in scout.strengths||[]" :key="item">{{item}}</li><li v-if="!(scout.strengths||[]).length">Consulta los atributos destacados del resumen.</li></ul><h3>PUNTOS DÉBILES</h3><ul><li v-for="item in scout.weaknesses||[]" :key="item">{{item}}</li><li v-if="!(scout.weaknesses||[]).length">Sin datos suficientes.</li></ul></div></section>
  </div>
</BaseModal>
</template>
