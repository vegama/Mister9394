<script setup>
import { computed } from 'vue'

const props = defineProps({
  staff: { type: Object, default: () => ({ members: [], responsibilities: [] }) },
})
const emit = defineEmits(['assign'])

const areas = computed(() => {
  const rows = props.staff?.responsibilities || []
  const order = ['Primer equipo', 'Scouting', 'Mercado', 'Salud', 'Desarrollo']
  return order
    .map(area => ({ area, rows: rows.filter(row => row.area === area) }))
    .filter(group => group.rows.length)
})

function primarySkill(member) {
  const role = String(member?.role || '')
  const key = role === 'physio' ? 'physiotherapy'
    : role === 'sporting_director' ? 'negotiation'
    : role === 'chief_scout' ? 'market_knowledge'
    : role === 'scout' ? 'judging_player'
    : role === 'goalkeeping_coach' ? 'goalkeeping'
    : role === 'assistant_manager' ? 'tactical'
    : 'coaching'
  return { label: member?.skill_labels?.[key] || key, value: member?.skills?.[key] ?? '—' }
}

function qualityClass(value) {
  const n = Number(value || 0)
  if (!value) return 'direct'
  if (n >= 17) return 'excellent'
  if (n >= 14) return 'strong'
  if (n >= 11) return 'reliable'
  return 'limited'
}
</script>

<template>
  <section class="staff-workspace">
    <header class="staff-hero">
      <div>
        <span class="staff-kicker">CUERPO TÉCNICO · NF0 OPERATIVO</span>
        <h1>Personas y responsabilidades</h1>
        <p>Decide qué llevas tú y qué delegas. Competencia y carga ya afectan a informes, scouting, salud y negociación; no es una preferencia decorativa.</p>
      </div>
      <div class="staff-summary">
        <strong>{{ staff.members?.length || 0 }}</strong>
        <span>empleados</span>
        <small>{{ staff.manager_responsibility_count || 0 }} tareas bajo tu control directo</small>
      </div>
    </header>

    <div class="staff-grid">
      <article v-for="member in staff.members || []" :key="member.id" class="staff-card">
        <div class="staff-card-head">
          <div>
            <small>{{ member.role_label }}</small>
            <h3>{{ member.name }}</h3>
          </div>
          <span class="staff-load" :class="String(member.workload_label || '').toLowerCase()">{{ member.workload_label }}</span>
        </div>
        <div class="staff-skill">
          <span>{{ primarySkill(member).label }}</span>
          <strong>{{ primarySkill(member).value }}/20</strong>
        </div>
        <div class="staff-mini-skills">
          <span>Táctica <b>{{ member.skills?.tactical ?? '—' }}</b></span>
          <span>Entrenamiento <b>{{ member.skills?.coaching ?? '—' }}</b></span>
          <span>Jugadores <b>{{ member.skills?.judging_player ?? '—' }}</b></span>
          <span>Negociación <b>{{ member.skills?.negotiation ?? '—' }}</b></span>
        </div>
        <footer>
          <span>{{ member.workload || 0 }} responsabilidades</span>
          <span v-if="member.generated" class="staff-provenance">Generado por la carrera</span>
        </footer>
      </article>
    </div>

    <div class="staff-responsibilities">
      <div class="staff-section-title">
        <div>
          <span class="staff-kicker">DELEGACIÓN</span>
          <h2>Quién hace qué</h2>
        </div>
        <p>Cambiar el responsable se guarda inmediatamente y altera la calidad operativa de esa tarea.</p>
      </div>

      <section v-for="group in areas" :key="group.area" class="staff-area">
        <h3>{{ group.area }}</h3>
        <div class="staff-responsibility" v-for="row in group.rows" :key="row.key">
          <div class="responsibility-copy">
            <strong>{{ row.label }}</strong>
            <p>{{ row.description }}</p>
            <small>Competencia clave: {{ row.skill_label }}</small>
          </div>
          <div class="responsibility-owner">
            <label :for="`responsibility-${row.key}`">Responsable</label>
            <select
              :id="`responsibility-${row.key}`"
              :value="row.assignee"
              @change="emit('assign', { key: row.key, assignee: $event.target.value })"
            >
              <option v-for="candidate in row.eligible_assignees" :key="candidate.id" :value="candidate.id">
                {{ candidate.name }} · {{ candidate.role_label }}
              </option>
            </select>
          </div>
          <div class="responsibility-quality" :class="qualityClass(row.quality)">
            <small>Calidad estimada</small>
            <strong>{{ row.quality_label }}</strong>
            <span v-if="row.quality">{{ row.quality }}/20 · carga {{ row.workload_label.toLowerCase() }}</span>
            <span v-else>Decisión bajo tu control</span>
          </div>
        </div>
      </section>
    </div>

    <p class="staff-note">{{ staff.provenance_note }}</p>
  </section>
</template>

<style scoped>
.staff-workspace{display:grid;gap:22px;padding-bottom:28px}.staff-hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;padding:24px;border:1px solid var(--line,#d7dde6);background:var(--surface,#fff);border-radius:14px}.staff-hero h1,.staff-section-title h2{margin:4px 0 7px}.staff-hero p,.staff-section-title p,.responsibility-copy p{margin:0;color:var(--text-soft,#687386)}.staff-kicker{font-size:11px;font-weight:800;letter-spacing:.12em;color:var(--accent,#2457a6)}.staff-summary{min-width:180px;padding:15px 18px;border-radius:12px;background:var(--surface-soft,#f3f6fa);display:grid}.staff-summary strong{font-size:28px}.staff-summary span{font-weight:700}.staff-summary small{margin-top:7px;color:var(--text-soft,#687386)}.staff-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:12px}.staff-card{border:1px solid var(--line,#d7dde6);background:var(--surface,#fff);border-radius:12px;padding:15px;display:grid;gap:13px}.staff-card-head{display:flex;justify-content:space-between;gap:12px}.staff-card-head small{font-size:11px;text-transform:uppercase;color:var(--text-soft,#687386)}.staff-card-head h3{margin:3px 0 0;font-size:16px}.staff-load{align-self:start;border-radius:999px;background:var(--surface-soft,#f3f6fa);padding:4px 8px;font-size:10px;font-weight:800;text-transform:uppercase}.staff-skill{display:flex;justify-content:space-between;padding:10px 0;border-top:1px solid var(--line,#d7dde6);border-bottom:1px solid var(--line,#d7dde6)}.staff-mini-skills{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;font-size:12px;color:var(--text-soft,#687386)}.staff-mini-skills span{display:flex;justify-content:space-between;gap:8px}.staff-card footer{display:flex;justify-content:space-between;gap:8px;font-size:10px;color:var(--text-soft,#687386)}.staff-provenance{font-weight:700}.staff-responsibilities{display:grid;gap:18px}.staff-section-title{display:flex;justify-content:space-between;gap:24px;align-items:end}.staff-area{display:grid;gap:8px}.staff-area>h3{margin:0 0 3px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-soft,#687386)}.staff-responsibility{display:grid;grid-template-columns:minmax(260px,1.45fr) minmax(220px,1fr) minmax(150px,.65fr);gap:16px;align-items:center;padding:14px 16px;border:1px solid var(--line,#d7dde6);background:var(--surface,#fff);border-radius:11px}.responsibility-copy p{font-size:12px;margin:4px 0}.responsibility-copy small,.responsibility-owner label,.responsibility-quality small{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-soft,#687386)}.responsibility-owner{display:grid;gap:5px}.responsibility-owner select{width:100%;min-height:36px}.responsibility-quality{display:grid;gap:2px;border-left:3px solid var(--line,#d7dde6);padding-left:12px}.responsibility-quality.excellent,.responsibility-quality.strong{border-left-color:#2d8a55}.responsibility-quality.reliable{border-left-color:#b48619}.responsibility-quality.limited{border-left-color:#b64c4c}.responsibility-quality.direct{border-left-color:var(--accent,#2457a6)}.responsibility-quality span{font-size:11px;color:var(--text-soft,#687386)}.staff-note{font-size:11px;color:var(--text-soft,#687386);margin:0}@media(max-width:900px){.staff-hero,.staff-section-title{align-items:stretch;flex-direction:column}.staff-responsibility{grid-template-columns:1fr}.responsibility-quality{border-left:0;border-top:3px solid var(--line,#d7dde6);padding:9px 0 0}}
</style>
