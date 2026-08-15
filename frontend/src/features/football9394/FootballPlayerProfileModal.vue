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
const emit = defineEmits(['close', 'update:tab'])

const tabs = [
  { id: 'profile', label: 'INFORMACIÓN' },
  { id: 'attributes', label: 'PARÁMETROS' },
  { id: 'season', label: 'TEMPORADA' },
  { id: 'contract', label: 'CONTRATO' },
  { id: 'medical', label: 'LESIONES' },
  { id: 'career', label: 'HISTORIAL' },
  { id: 'scout', label: 'INFORME' },
]
const tabModel = computed({ get: () => props.tab, set: value => emit('update:tab', value) })
const p = computed(() => props.player || {})
const displayName = computed(() => p.value.display_name || p.value.full_name || p.value.name || 'Jugador')
const overall = computed(() => Number(p.value.overall ?? p.value.rating ?? 0))
const stars = computed(() => {
  const filled = Math.max(0, Math.min(5, Math.round(overall.value / 20)))
  return `${'★'.repeat(filled)}${'☆'.repeat(5-filled)}`
})
const positions = computed(() => {
  const raw = p.value.positions
  if (Array.isArray(raw)) return raw
  if (raw && typeof raw === 'object') return [raw.primary, ...(raw.secondary || [])].filter(Boolean)
  return [p.value.position].filter(Boolean)
})
const attributes = computed(() => p.value.attributes || {})
const attributeGroups = computed(() => [
  ['TÉCNICOS', [
    ['Técnica', 'technique'], ['Pase corto', 'short_pass'], ['Pase largo', 'long_pass'],
    ['Centro', 'crossing'], ['Regate', 'dribbling'], ['Finalización', 'finishing'],
    ['Remate cabeza', 'heading'], ['Balón parado', 'set_pieces'],
  ]],
  ['FÍSICOS', [
    ['Velocidad', 'pace'], ['Aceleración', 'acceleration'], ['Resistencia', 'stamina'],
    ['Fuerza', 'strength'], ['Salto', 'jumping'], ['Agilidad', 'agility'],
  ]],
  ['MENTALES', [
    ['Colocación', 'positioning'], ['Anticipación', 'anticipation'], ['Visión', 'vision'],
    ['Desmarque', 'off_ball'], ['Disciplina', 'discipline'], ['Liderazgo', 'leadership'],
    ['Agresividad', 'aggression'], ['Regularidad', 'consistency'],
  ]],
  ['DEFENSIVOS / PORTERO', [
    ['Entrada', 'tackling'], ['Marcaje', 'marking'], ['Intercepción', 'interception'],
    ['Portero', 'goalkeeping'], ['Reflejos', 'reflexes'], ['Juego aéreo', 'aerial_goalkeeping'],
  ]],
])
const valueOf = key => {
  const value = attributes.value?.[key] ?? p.value?.[key]
  return Number.isFinite(Number(value)) ? Number(value) : '—'
}
const toneFor = value => {
  const n = Number(value)
  if (!Number.isFinite(n)) return 'unknown'
  if (n >= 85) return 'elite'
  if (n >= 70) return 'good'
  if (n >= 55) return 'average'
  return 'weak'
}
const seasonStats = computed(() => p.value.season_stats || {})
const contract = computed(() => p.value.contract || {})
const medical = computed(() => p.value.medical || {})
const scout = computed(() => p.value.scout || {})
const clubMonogram = computed(() => String(p.value.team_name || 'FC').split(/\s+/).filter(Boolean).slice(0,2).map(v=>v[0]).join('').toUpperCase())
const photoPerson = computed(() => ({...p.value, photo_url: p.value.photo_url || (p.value.id ? `/historical9394/players/${Number(p.value.id)}.jpg` : null)}))
const crestUrl = computed(() => p.value.team_crest_url || (p.value.team_id ? `/historical9394/clubs/${Number(p.value.team_id)}.gif` : null))
const ratingLabel = computed(() => { const v=Number(overall.value||0); return v>=90?'EXCELENTE':v>=82?'MUY BUENO':v>=74?'BUENO':v>=65?'CORRECTO':'IRREGULAR' })
</script>

<template>
  <BaseModal
    :embedded="embedded"
    size="full"
    layer="entity"
    panel-class="football9394-player-modal"
    close-label="Cerrar ficha del jugador"
    aria-label="Ficha futbolista 1993-94"
    @close="emit('close')"
  >
    <template #header>
      <div class="f9394-player-titlebar">
        <div class="f9394-player-window-label">FICHA DEL JUGADOR</div>
        <div class="f9394-player-identity-strip">
          <div class="f9394-club-crest" :title="player.team_name || 'Club'"><img v-if="crestUrl" :src="crestUrl" alt=""><span v-else>{{ clubMonogram }}</span></div>
          <div class="f9394-player-title">
            <small>{{ player.shirt_number ? `${player.shirt_number} · ` : '' }}{{ player.team_name || 'SIN CLUB' }}</small>
            <strong>{{ displayName }}</strong>
            <span>{{ positions.join(' / ') || 'Sin demarcación' }} · {{ player.nationality || 'Nacionalidad desconocida' }}</span>
          </div>
          <div class="f9394-photo-slot"><PersonAvatar class="f9394-avatar" :person="photoPerson" :size="56" :height="77" decorative /></div>
        </div>
        <div class="f9394-player-metric-strip">
          <div class="f9394-small-metric edad"><span>EDAD</span><b>{{ player.age ?? '—' }} AÑOS</b></div>
          <div class="f9394-small-metric altura"><span>ALTURA</span><b>{{ player.height_cm ? `${(player.height_cm/100).toFixed(2)} M` : '—' }}</b></div>
          <div class="f9394-small-metric peso"><span>PESO</span><b>{{ player.weight_kg ? `${player.weight_kg} KG` : '—' }}</b></div>
          <div class="f9394-small-metric pais"><span>NACIONALIDAD</span><b>{{ player.nationality || '—' }}</b></div>
          <div class="f9394-header-metric media"><span>MEDIA</span><b>{{ overall || '—' }}</b></div>
          <div class="f9394-header-metric forma"><span>FORMA</span><b>{{ player.form ?? '—' }}</b></div>
          <div class="f9394-header-metric moral"><span>MORAL</span><b>{{ player.morale ?? '—' }}</b></div>
          <div class="f9394-header-metric contrato"><span>CONTRATO</span><b>{{ contract.end || '—' }}</b></div>
        </div>
      </div>
    </template>

    <div class="f9394-profile-shell">
      <UiTabs v-model="tabModel" class="f9394-profile-tabs" :items="tabs" aria-label="Secciones de la ficha" />

      <section v-if="tabModel==='profile'" class="f9394-profile-tab">
        <div class="f9394-profile-maincol">
          <div class="f9394-card f9394-personal-card">
            <h3>INFORMACIÓN DEL JUGADOR</h3>
            <dl class="f9394-data-grid">
              <div><dt>Nacionalidad</dt><dd>{{ player.nationality || '—' }}</dd></div>
              <div><dt>Pie</dt><dd>{{ player.preferred_foot || '—' }}</dd></div>
              <div><dt>Estado</dt><dd>{{ medical.status || player.status || 'Disponible' }}</dd></div>
              <div><dt>Rol</dt><dd>{{ player.role || '—' }}</dd></div>
              <div><dt>Valor</dt><dd>{{ player.market_value_display || '—' }}</dd></div>
              <div><dt>Cláusula</dt><dd>{{ contract.release_clause_display || '—' }}</dd></div>
            </dl>
          </div>
          <div class="f9394-card f9394-quick-attributes">
            <h3>ATRIBUTOS DESTACADOS</h3>
            <div v-for="key in ['technique','short_pass','positioning','pace','finishing','stamina']" :key="key" class="f9394-attribute-line">
              <span>{{ ({pace:'Velocidad',stamina:'Resistencia',technique:'Técnica',short_pass:'Pase corto',finishing:'Remate',positioning:'Creatividad'})[key] }}</span>
              <div class="f9394-meter"><i :style="{width:`${Number(valueOf(key))||0}%`}"></i></div>
              <b :class="toneFor(valueOf(key))">{{ valueOf(key) }}</b>
            </div>
          </div>
        </div>

        <div class="f9394-profile-sidecol">
          <div class="f9394-rating-card"><span>CALIFICACIÓN</span><b>{{ ratingLabel }}</b><small>{{ stars }}</small></div>
          <div class="f9394-card f9394-season-mini"><h3>TEMPORADA {{ props.season }}</h3><div class="f9394-season-tiles"><div><span>PJ</span><b>{{ seasonStats.appearances ?? 0 }}</b></div><div><span>GOL</span><b>{{ seasonStats.goals ?? 0 }}</b></div><div><span>AST</span><b>{{ seasonStats.assists ?? 0 }}</b></div></div></div>
          <div class="f9394-card f9394-role-card">
            <div class="f9394-mini-pitch" aria-label="Demarcación natural del jugador">
              <i class="center-circle"></i><div class="f9394-role-token"></div>
            </div>
          </div>
        </div>
      </section>

      <section v-else-if="tabModel==='attributes'" class="f9394-attribute-groups">
        <article v-for="group in attributeGroups" :key="group[0]" class="f9394-card">
          <h3>{{ group[0] }}</h3>
          <div v-for="item in group[1]" :key="item[1]" class="f9394-attribute-line">
            <span>{{ item[0] }}</span>
            <div class="f9394-meter"><i :style="{width:`${Number(valueOf(item[1]))||0}%`}"></i></div>
            <b :class="toneFor(valueOf(item[1]))">{{ valueOf(item[1]) }}</b>
          </div>
        </article>
      </section>

      <section v-else-if="tabModel==='season'" class="f9394-card">
        <h3>TEMPORADA {{ props.season }}</h3>
        <div class="f9394-stat-grid">
          <div><span>PJ</span><b>{{ seasonStats.appearances ?? 0 }}</b></div>
          <div><span>TIT</span><b>{{ seasonStats.starts ?? 0 }}</b></div>
          <div><span>MIN</span><b>{{ seasonStats.minutes ?? 0 }}</b></div>
          <div><span>GOL</span><b>{{ seasonStats.goals ?? 0 }}</b></div>
          <div><span>ASI</span><b>{{ seasonStats.assists ?? 0 }}</b></div>
          <div><span>TA</span><b>{{ seasonStats.yellow_cards ?? 0 }}</b></div>
          <div><span>TR</span><b>{{ seasonStats.red_cards ?? 0 }}</b></div>
          <div><span>MEDIA</span><b>{{ seasonStats.average_rating ?? '—' }}</b></div>
        </div>
        <div class="f9394-table-wrap" v-if="seasonStats.by_competition?.length">
          <table><thead><tr><th>COMPETICIÓN</th><th>PJ</th><th>TIT</th><th>MIN</th><th>G</th><th>A</th><th>TA</th><th>TR</th><th>NOTA</th></tr></thead>
          <tbody><tr v-for="row in seasonStats.by_competition" :key="row.competition_id || row.name"><td>{{ row.name }}</td><td>{{ row.appearances }}</td><td>{{ row.starts }}</td><td>{{ row.minutes }}</td><td>{{ row.goals }}</td><td>{{ row.assists }}</td><td>{{ row.yellow_cards }}</td><td>{{ row.red_cards }}</td><td>{{ row.average_rating }}</td></tr></tbody></table>
        </div>
      </section>

      <section v-else-if="tabModel==='contract'" class="f9394-tab-grid f9394-contract-tab">
        <div class="f9394-card"><h3>CONTRATO</h3><dl class="f9394-data-grid">
          <div><dt>Inicio</dt><dd>{{ contract.start || '—' }}</dd></div><div><dt>Final</dt><dd>{{ contract.end || '—' }}</dd></div>
          <div><dt>Ficha anual</dt><dd>{{ contract.salary_display || '—' }}</dd></div><div><dt>Cláusula</dt><dd>{{ contract.release_clause_display || '—' }}</dd></div>
          <div><dt>Cesión</dt><dd>{{ contract.loan ? 'Sí' : 'No' }}</dd></div><div><dt>Equipo propietario</dt><dd>{{ contract.parent_club_name || player.team_name || '—' }}</dd></div>
        </dl></div>
        <div class="f9394-card"><h3>SITUACIÓN</h3><dl class="f9394-data-grid">
          <div><dt>Valor</dt><dd>{{ player.market_value_display || '—' }}</dd></div><div><dt>Transferible</dt><dd>{{ player.transfer_listed ? 'Sí' : 'No' }}</dd></div>
          <div><dt>Cedido hasta</dt><dd>{{ contract.loan_end || '—' }}</dd></div><div><dt>Dorsal favorito</dt><dd>{{ player.preferred_number ?? '—' }}</dd></div>
        </dl></div>
      </section>

      <section v-else-if="tabModel==='medical'" class="f9394-card">
        <h3>HISTORIAL MÉDICO</h3>
        <div class="f9394-medical-banner"><b>{{ medical.status || 'Disponible' }}</b><span>{{ medical.current_injury?.name || 'Sin lesión actual' }}</span></div>
        <div class="f9394-table-wrap"><table><thead><tr><th>LESIÓN</th><th>ZONA</th><th>LADO</th><th>INICIO</th><th>ALTA</th><th>DÍAS</th><th>RECAÍDA</th></tr></thead>
        <tbody><tr v-for="(injury,index) in medical.history || []" :key="`${injury.start}-${index}`"><td>{{ injury.name }}</td><td>{{ injury.body_area || '—' }}</td><td>{{ injury.laterality || '—' }}</td><td>{{ injury.start || '—' }}</td><td>{{ injury.end || injury.expected_return || '—' }}</td><td>{{ injury.days ?? '—' }}</td><td>{{ injury.recurrence ? 'Sí' : 'No' }}</td></tr><tr v-if="!(medical.history||[]).length"><td colspan="7">Sin lesiones registradas.</td></tr></tbody></table></div>
      </section>

      <section v-else-if="tabModel==='career'" class="f9394-card">
        <h3>TRAYECTORIA</h3>
        <div class="f9394-table-wrap"><table><thead><tr><th>TEMPORADA</th><th>CLUB</th><th>COMPETICIÓN</th><th>PJ</th><th>G</th><th>A</th></tr></thead>
        <tbody><tr v-for="(row,index) in player.career || []" :key="`${row.season}-${row.club_id}-${index}`"><td>{{ row.season }}</td><td>{{ row.club_name }}</td><td>{{ row.competition_name || '—' }}</td><td>{{ row.appearances ?? 0 }}</td><td>{{ row.goals ?? 0 }}</td><td>{{ row.assists ?? 0 }}</td></tr><tr v-if="!(player.career||[]).length"><td colspan="6">Sin historial registrado.</td></tr></tbody></table></div>
      </section>

      <section v-else-if="tabModel==='scout'" class="f9394-tab-grid">
        <div class="f9394-card"><h3>INFORME DEL TÉCNICO / OJEADOR</h3><p class="f9394-report">{{ scout.summary || 'Todavía no existe un informe suficiente sobre este jugador.' }}</p><dl class="f9394-data-grid"><div><dt>Conocimiento</dt><dd>{{ scout.knowledge || '—' }}</dd></div><div><dt>Confianza</dt><dd>{{ scout.confidence || '—' }}</dd></div><div><dt>Rol recomendado</dt><dd>{{ scout.recommended_role || '—' }}</dd></div><div><dt>Encaje táctico</dt><dd>{{ scout.tactical_fit || '—' }}</dd></div></dl></div>
        <div class="f9394-card"><h3>PUNTOS FUERTES</h3><ul><li v-for="item in scout.strengths || []" :key="item">{{ item }}</li><li v-if="!(scout.strengths||[]).length">Sin datos suficientes.</li></ul><h3>PUNTOS DÉBILES</h3><ul><li v-for="item in scout.weaknesses || []" :key="item">{{ item }}</li><li v-if="!(scout.weaknesses||[]).length">Sin datos suficientes.</li></ul></div>
      </section>
      <div class="f9394-profile-actions"><button type="button">ENTRENAMIENTO</button><button type="button">LESIONADOS</button><button type="button">ESTADÍSTICAS</button></div>
    </div>
  </BaseModal>
</template>
