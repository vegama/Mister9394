<script setup>
import { computed } from 'vue'
import UiPageHeader from '../../components/ui/UiPageHeader.vue'
import UiEmptyState from '../../components/ui/UiEmptyState.vue'

const props = defineProps({
  staff: { type: Object, default: () => ({ members: [], responsibilities: [] }) },
  reports: { type: Object, default: () => ({ reports: [], urgent_count: 0 }) },
})
const emit = defineEmits(['assign','open-action'])

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
    <UiPageHeader eyebrow="CUERPO TÉCNICO" title="Personas y responsabilidades" description="Decide qué llevas tú y qué delegas. La competencia, la carga y los traspasos de responsabilidad afectan al trabajo real del club." :status="`${staff.active_process_count || 0} procesos vivos`">
      <template #actions><div class="staff-summary"><strong>{{ staff.members?.length || 0 }}</strong><span>empleados</span><small>{{ staff.manager_responsibility_count || 0 }} tareas bajo tu control directo</small></div></template>
    </UiPageHeader>

    <article v-if="staff.recent_handoffs?.length" class="staff-handoff-banner">
      <span><small>ÚLTIMO CAMBIO DE RESPONSABLE</small><strong>{{staff.recent_handoffs[0].from_name}} → {{staff.recent_handoffs[0].to_name}}</strong></span>
      <p>{{staff.recent_handoffs[0].label}} · {{staff.recent_handoffs[0].affected_count}} proceso{{staff.recent_handoffs[0].affected_count===1?'':'s'}} activo{{staff.recent_handoffs[0].affected_count===1?'':'s'}} transferido{{staff.recent_handoffs[0].affected_count===1?'':'s'}} sin perder estado.</p>
    </article>

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

    <article class="staff-reports-panel">
      <div class="staff-section-title"><div><span class="staff-kicker">NF5 · INFORMACIÓN DEL STAFF</span><h2>Qué te está diciendo el club</h2></div><b>{{reports.urgent_count || 0}} urgentes</b></div>
      <div class="staff-decision-strip" :class="{attention:(reports.urgent_count||0)>0}">
        <span><small>DECISIONES / SEGUIMIENTO</small><strong v-if="reports.urgent_count">Hay {{reports.urgent_count}} asunto{{reports.urgent_count===1?'':'s'}} que necesita{{reports.urgent_count===1?'':'n'}} tu atención</strong><strong v-else>No hay decisiones urgentes bloqueando el avance</strong></span>
        <p>Los informes no son mensajes aislados: cada uno abre directamente el sistema donde puedes resolver o supervisar el problema.</p>
      </div>
      <div class="staff-report-grid">
        <UiEmptyState v-if="!(reports.reports||[]).length" icon="✓" title="No hay informes que requieran revisión" description="Cuando un miembro del staff detecte algo relevante, aparecerá aquí con autor, evidencia y destino de resolución." />
        <div v-for="report in reports.reports || []" :key="report.id" class="staff-report" :class="report.urgency">
          <span><small>{{report.area}} · {{report.author}}</small><strong>{{report.title}}</strong></span>
          <p>{{report.detail}}</p><footer><em>{{report.confidence_label}} · {{report.confidence}}% confianza</em><b>{{report.evidence}}</b><button type="button" class="football-button tiny" @click="emit('open-action',report.action)">Ir a {{report.area}} →</button></footer>
        </div>
      </div>
    </article>

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
            <div class="responsibility-title"><strong>{{ row.label }}</strong><span class="responsibility-mode" :class="row.mode">{{row.mode_label || (row.assignee==='manager'?'Control directo':'Delegado')}}</span></div>
            <p>{{ row.description }}</p>
            <small>Competencia clave: {{ row.skill_label }}</small>
            <em>{{row.effect}}</em>
            <div v-if="row.active_process_count" class="responsibility-processes">
              <b>{{row.active_process_count}} proceso{{row.active_process_count===1?'':'s'}} activo{{row.active_process_count===1?'':'s'}}</b>
              <span v-for="process in row.active_processes.slice(0,3)" :key="process.id">{{process.title}} · {{process.status}}<template v-if="process.due_on"> · {{process.due_on}}</template></span>
              <small>Si cambias responsable, estos trabajos pasan al nuevo dueño y el traspaso queda registrado.</small>
            </div>
            <div v-if="row.last_handoff" class="responsibility-last-handoff">Último traspaso: {{row.last_handoff.from_name}} → {{row.last_handoff.to_name}} · {{row.last_handoff.affected_count}} proceso(s)</div>
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
            <button type="button" class="football-button tiny secondary responsibility-open" @click="emit('open-action',row.workspace || 'home')">Ir al área →</button>
          </div>
        </div>
      </section>
    </div>

    <p class="staff-note">{{ staff.provenance_note }}</p>
  </section>
</template>

<style scoped>
.staff-workspace{display:grid;gap:22px;padding-bottom:28px}.staff-hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;padding:24px;border:1px solid var(--line,#d7dde6);background:var(--surface,#fff);border-radius:14px}.staff-hero h1,.staff-section-title h2{margin:4px 0 7px}.staff-hero p,.staff-section-title p,.responsibility-copy p{margin:0;color:var(--text-soft,#687386)}.staff-kicker{font-size:11px;font-weight:800;letter-spacing:.12em;color:var(--accent,#2457a6)}.staff-summary{min-width:180px;padding:15px 18px;border-radius:12px;background:var(--surface-soft,#f3f6fa);display:grid}.staff-summary strong{font-size:28px}.staff-summary span{font-weight:700}.staff-summary small{margin-top:7px;color:var(--text-soft,#687386)}.staff-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:12px}.staff-card{border:1px solid var(--line,#d7dde6);background:var(--surface,#fff);border-radius:12px;padding:15px;display:grid;gap:13px}.staff-card-head{display:flex;justify-content:space-between;gap:12px}.staff-card-head small{font-size:11px;text-transform:uppercase;color:var(--text-soft,#687386)}.staff-card-head h3{margin:3px 0 0;font-size:16px}.staff-load{align-self:start;border-radius:999px;background:var(--surface-soft,#f3f6fa);padding:4px 8px;font-size:11px;font-weight:800;text-transform:uppercase}.staff-skill{display:flex;justify-content:space-between;padding:10px 0;border-top:1px solid var(--line,#d7dde6);border-bottom:1px solid var(--line,#d7dde6)}.staff-mini-skills{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;font-size:12px;color:var(--text-soft,#687386)}.staff-mini-skills span{display:flex;justify-content:space-between;gap:8px}.staff-card footer{display:flex;justify-content:space-between;gap:8px;font-size:11px;color:var(--text-soft,#687386)}.staff-provenance{font-weight:700}.staff-handoff-banner{display:flex;justify-content:space-between;gap:20px;align-items:center;padding:12px 15px;border:1px solid var(--line,#d7dde6);border-radius:11px;background:var(--surface-soft,#f3f6fa)}.staff-handoff-banner span{display:grid;gap:2px}.staff-handoff-banner small{font-size:11px;font-weight:800;letter-spacing:.08em;color:var(--text-soft,#687386)}.staff-handoff-banner p{margin:0;max-width:620px;font-size:11px;color:var(--text-soft,#687386)}.staff-reports-panel{display:grid;gap:12px}.staff-report-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.staff-report{padding:13px 14px;border:1px solid var(--line,#d7dde6);border-left:4px solid var(--accent,#2457a6);border-radius:10px;background:var(--surface,#fff)}.staff-report.high{border-left-color:#b64c4c}.staff-report>span{display:grid}.staff-report p{margin:7px 0;color:var(--text-soft,#687386);font-size:12px}.staff-report footer{display:flex;justify-content:space-between;gap:12px;font-size:11px;color:var(--text-soft,#687386)}.staff-report footer b{font-weight:500;text-align:right}.staff-responsibilities{display:grid;gap:18px}.staff-section-title{display:flex;justify-content:space-between;gap:24px;align-items:end}.staff-area{display:grid;gap:8px}.staff-area>h3{margin:0 0 3px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-soft,#687386)}.staff-responsibility{display:grid;grid-template-columns:minmax(260px,1.45fr) minmax(220px,1fr) minmax(150px,.65fr);gap:16px;align-items:center;padding:14px 16px;border:1px solid var(--line,#d7dde6);background:var(--surface,#fff);border-radius:11px}.responsibility-copy p{font-size:12px;margin:4px 0}.responsibility-copy small,.responsibility-owner label,.responsibility-quality small{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-soft,#687386)}.responsibility-owner{display:grid;gap:5px}.responsibility-owner select{width:100%;min-height:36px}.responsibility-quality{display:grid;gap:2px;border-left:3px solid var(--line,#d7dde6);padding-left:12px}.responsibility-quality.excellent,.responsibility-quality.strong{border-left-color:#2d8a55}.responsibility-quality.reliable{border-left-color:#b48619}.responsibility-quality.limited{border-left-color:#b64c4c}.responsibility-quality.direct{border-left-color:var(--accent,#2457a6)}.responsibility-quality span{font-size:11px;color:var(--text-soft,#687386)}.staff-decision-strip{display:flex;justify-content:space-between;gap:20px;align-items:center;padding:11px 13px;border:1px solid var(--line,#d7dde6);border-radius:10px;background:var(--surface-soft,#f3f6fa)}.staff-decision-strip.attention{border-color:#b64c4c}.staff-decision-strip span{display:grid;gap:2px}.staff-decision-strip small{font-size:11px;font-weight:800;letter-spacing:.08em;color:var(--text-soft,#687386)}.staff-decision-strip p{max-width:520px;margin:0;font-size:11px;color:var(--text-soft,#687386)}.responsibility-title{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.responsibility-mode{font-size:11px;font-weight:800;padding:3px 7px;border-radius:999px;background:var(--surface-soft,#eef2f6);color:var(--text-soft,#687386)}.responsibility-mode.direct{color:var(--accent,#2457a6)}.responsibility-mode.delegated{color:#397a56}.responsibility-copy em{display:block;margin-top:6px;font-size:11px;font-style:normal;color:var(--text-soft,#687386)}.responsibility-processes{display:grid;gap:2px;margin-top:8px;padding:8px 9px;border:1px solid var(--line,#d7dde6);border-radius:8px;background:var(--surface-soft,#f3f6fa)}.responsibility-processes b{font-size:11px}.responsibility-processes span,.responsibility-processes small,.responsibility-last-handoff{font-size:11px;color:var(--text-soft,#687386)}.responsibility-last-handoff{margin-top:5px;font-weight:700}.responsibility-open{margin-top:6px;justify-self:start}.staff-note{font-size:11px;color:var(--text-soft,#687386);margin:0}@media(max-width:900px){.staff-handoff-banner{align-items:stretch;flex-direction:column}.staff-decision-strip{align-items:stretch;flex-direction:column}.staff-report-grid{grid-template-columns:1fr}.staff-hero,.staff-section-title{align-items:stretch;flex-direction:column}.staff-responsibility{grid-template-columns:1fr}.responsibility-quality{border-left:0;border-top:3px solid var(--line,#d7dde6);padding:9px 0 0}}
</style>
