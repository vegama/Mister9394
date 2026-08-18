<script setup>
import { computed, ref, watch } from 'vue'
import UiPageHeader from '../../components/ui/UiPageHeader.vue'
import UiProcessTrail from '../../components/ui/UiProcessTrail.vue'
import UiActionDock from '../../components/ui/UiActionDock.vue'

const props = defineProps({
  training: { type: Object, default: () => ({ weekly_plan: [], players: [], session_options: [], intensity_options: [], focus_options: [], responsibility: {} }) },
})
const emit = defineEmits(['save-plan','set-focus','set-recovery','set-match-preparation','open-staff'])

const localIntensity = ref('normal')
const localWeek = ref([])
watch(() => props.training, value => {
  localIntensity.value = value?.intensity || 'normal'
  localWeek.value = (value?.weekly_plan || []).map(row => row.session)
}, { immediate: true, deep: true })

const topRisk = computed(() => (props.training?.players || []).slice(0, 8))
const medicalCases = computed(() => props.training?.medical?.cases || [])
const planDirty = computed(() => {
  const currentIntensity = props.training?.intensity || 'normal'
  const currentWeek = (props.training?.weekly_plan || []).map(row => row.session)
  return localIntensity.value !== currentIntensity || JSON.stringify(localWeek.value) !== JSON.stringify(currentWeek)
})

const trainingProcessSteps = computed(() => {
  const process = props.training?.process || {}
  return [
    { id:'need', label:'Necesidad', detail:process.need || 'Planificar la semana' },
    { id:'owner', label:'Responsable', detail:process.owner || props.training?.responsibility?.assignee_name || 'Mánager' },
    { id:'work', label:'Trabajo', detail:process.status || (planDirty.value ? 'Cambios pendientes' : 'Plan preparado') },
    { id:'next', label:'Siguiente paso', detail:process.next_step || 'Ejecutar la siguiente sesión' },
    { id:'impact', label:'Consecuencia', detail:process.consequence || 'Carga, forma y riesgo evolucionan' },
  ]
})
const activeTrainingStep = computed(() => props.training?.process?.requires_action || planDirty.value ? 'work' : 'next')
const riskClass = value => value >= 70 ? 'very-high' : value >= 52 ? 'high' : value >= 34 ? 'medium' : 'low'
const conditionClass = value => value < 65 ? 'danger' : value < 78 ? 'warn' : 'ok'
function save(){ emit('save-plan', { intensity: localIntensity.value, weekly_plan: [...localWeek.value] }) }
function resetPlan(){
  localIntensity.value = props.training?.intensity || 'normal'
  localWeek.value = (props.training?.weekly_plan || []).map(row => row.session)
}
</script>

<template>
  <section class="training-workspace">
    <UiPageHeader eyebrow="PREPARACIÓN DEL PRIMER EQUIPO" title="Entrenamiento y carga" description="Planifica la semana sin perder de vista condición, fatiga, riesgo y quién ejecuta cada decisión." :status="planDirty?'Cambios sin guardar':'Plan sincronizado'">
      <template #actions><div class="training-owner" :class="training.responsibility_mode"><small>RESPONSABLE · {{training.responsibility_mode==='delegated'?'DELEGADO':'CONTROL DIRECTO'}}</small><strong>{{training.responsibility?.assignee_name || 'Tú (mánager)'}}</strong><span>{{training.responsibility?.quality_label || 'Decisión directa'}} · carga {{training.responsibility?.workload_label || '—'}}</span><button type="button" class="football-button tiny secondary" @click="emit('open-staff')">Cambiar delegación</button></div></template>
    </UiPageHeader>

    <article class="training-continuity football-panel">
      <span><small>CÓMO SE EJECUTA</small><strong>{{training.responsibility_mode==='delegated'?'Tú marcas el plan; el staff lo ejecuta':'Tú decides y ejecutas el plan'}}</strong></span>
      <p>{{training.responsibility_note || 'Los cambios de entrenamiento se aplican a la planificación de la siguiente sesión.'}}</p>
      <span class="training-save-state" :class="{dirty:planDirty}"><small>PLAN SEMANAL</small><strong>{{planDirty?'Cambios sin guardar':'Guardado'}}</strong></span>
    </article>

    <article class="football-panel training-process-shell" :class="{attention:training.process?.requires_action}">
      <UiProcessTrail :steps="trainingProcessSteps" :active-step="activeTrainingStep" aria-label="Flujo de entrenamiento" />
      <div class="training-process-summary"><span><small>SIGUIENTE PASO</small><strong>{{training.process?.next_step || 'Ejecutar la siguiente sesión'}}</strong></span><span><small>CONSECUENCIA</small><strong>{{training.process?.consequence || 'La carga, la forma y el riesgo evolucionarán con el trabajo.'}}</strong></span></div>
    </article>

    <div class="training-kpis">
      <article><small>SESIÓN DE HOY</small><strong>{{training.today?.label || '—'}}</strong></article>
      <article><small>CARGA MEDIA</small><strong>{{training.average_load ?? '—'}} / 100</strong></article>
      <article><small>CONDICIÓN MEDIA</small><strong>{{training.average_condition ?? '—'}}%</strong></article>
      <article :class="{alert:training.high_risk_count>0}"><small>RIESGO ALTO</small><strong>{{training.high_risk_count || 0}} jugadores</strong></article>
    </div>

    <article class="football-panel match-prep-card">
      <header class="simple-panel-head"><span><small>PRÓXIMO PARTIDO</small><strong>Preparación específica</strong></span><em>{{training.match_preparation_focus_label || 'Equilibrada'}}</em></header>
      <div class="match-prep-control"><p>El foco de la víspera orienta el trabajo táctico y la familiaridad sin crear una sesión extra.</p><select :value="training.match_preparation_focus || 'balanced'" @change="emit('set-match-preparation',$event.target.value)"><option v-for="opt in training.match_preparation_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select></div>
    </article>

    <div class="training-grid">
      <article class="football-panel training-plan-card">
        <header class="simple-panel-head"><span><small>MICROCICLO</small><strong>Plan semanal</strong></span><label class="intensity-control"><span>Intensidad</span><select v-model="localIntensity"><option v-for="opt in training.intensity_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select></label></header>
        <div class="week-plan">
          <label v-for="(row,index) in training.weekly_plan || []" :key="row.day_index"><span>{{row.day}}</span><select v-model="localWeek[index]"><option v-for="opt in training.session_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select></label>
        </div>
        <UiActionDock class="training-actions" eyebrow="PLAN SEMANAL" :title="planDirty?'Revisa y guarda el microciclo':'El microciclo está guardado'" detail="Los días de partido y la víspera pueden ajustar automáticamente la sesión para evitar incoherencias con el calendario." :status="planDirty?'Hay cambios que todavía no afectan a las próximas sesiones.':'Los cambios guardados alimentarán carga, condición y riesgo.'" :tone="planDirty?'warning':'neutral'"><button v-if="planDirty" type="button" class="football-button secondary" @click="resetPlan">Descartar cambios</button><button type="button" class="football-button primary" :disabled="!planDirty" @click="save">{{planDirty?'Guardar plan':'Plan guardado'}}</button></UiActionDock>
      </article>

      <article class="football-panel risk-card">
        <header class="simple-panel-head"><span><small>ÁREA MÉDICA · {{training.medical?.responsibility?.assignee_name || 'Cuerpo médico'}}</small><strong>Disponibilidad y riesgo</strong></span><b>{{training.medical?.action_required || 0}} requieren revisión</b></header>
        <p class="medical-data-note">{{training.medical?.data_note || 'El diagnóstico y la estimación de recuperación se actualizan con la evolución del jugador.'}}</p>
        <div v-if="medicalCases.length" class="risk-list">
          <div v-for="player in medicalCases" :key="player.player_id" class="risk-row medical-case">
            <span class="risk-player"><strong>{{player.name}}</strong><small>{{player.observed?'OBSERVADO · lesión activa':'OBSERVADO · disponible'}} · ESTIMACIÓN: {{player.estimate}}</small></span>
            <span class="risk-meter"><i :style="{width:`${player.risk}%`}" :class="riskClass(player.risk)"></i></span>
            <b :class="riskClass(player.risk)">{{player.risk_label}}</b>
            <small>{{player.recommendation}}</small>
          </div>
        </div>
        <div v-else class="risk-list">
          <div v-for="player in topRisk" :key="player.player_id" class="risk-row">
            <span class="risk-player"><strong>{{player.name}}</strong><small>{{player.position}} · condición {{player.condition}}%</small></span><span class="risk-meter"><i :style="{width:`${player.risk}%`}" :class="riskClass(player.risk)"></i></span><b :class="riskClass(player.risk)">{{player.risk_label}}</b><small>{{player.recommendation}}</small>
          </div>
        </div>
      </article>
    </div>

    <article class="football-panel individual-card">
      <header class="simple-panel-head"><span><small>TRABAJO INDIVIDUAL</small><strong>Plantilla</strong></span><em>El foco acelera lentamente evidencia específica; no regala atributos.</em></header>
      <div class="training-table-head"><span>Jugador</span><span>Condición</span><span>Carga</span><span>Riesgo</span><span>Foco individual</span><span>Recuperación</span></div>
      <div class="training-table">
        <div v-for="player in training.players || []" :key="player.player_id" class="training-player-row">
          <span><strong>{{player.name}}</strong><small>{{player.position}}</small></span>
          <b :class="conditionClass(player.condition)">{{player.condition}}%</b>
          <span>{{player.training_load}} / 100</span>
          <b :class="riskClass(player.risk)">{{player.risk_label}}</b>
          <select :value="player.focus" :disabled="player.injury_days>0" @change="emit('set-focus',{playerId:player.player_id,focus:$event.target.value})"><option v-for="opt in training.focus_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select>
          <select :value="player.recovery || 'normal'" @change="emit('set-recovery',{playerId:player.player_id,recovery:$event.target.value})"><option v-for="opt in training.recovery_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select>
        </div>
      </div>
    </article>
  </section>
</template>

<style scoped>
.training-workspace{display:grid;gap:14px}.training-hero{display:flex;justify-content:space-between;gap:28px;padding:20px}.training-hero h2{margin:3px 0 6px}.training-hero p{max-width:760px;margin:0;color:var(--text-soft,#687386)}.training-owner{min-width:240px;display:grid;align-content:center;gap:4px;padding:12px 14px;background:var(--surface-soft,#f5f7fa);border:1px solid transparent;border-radius:10px}.training-owner.delegated{border-color:#8ab29a}.training-owner.direct{border-color:#8aa8ca}.training-owner button{justify-self:start;margin-top:4px}.training-owner small,.training-kpis small,.training-hero>div>small,.training-continuity small{font-size:11px;font-weight:800;letter-spacing:.08em;color:var(--text-soft,#687386)}.training-owner span{font-size:11px;color:var(--text-soft,#687386)}.training-continuity{display:grid;grid-template-columns:minmax(200px,.7fr) minmax(320px,1.5fr) minmax(140px,.5fr);gap:18px;align-items:center;padding:11px 14px}.training-process-shell{padding:12px}.training-process-summary{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:9px;padding-top:9px;border-top:1px solid var(--line,#d7dde6)}.training-process-summary span{display:grid;gap:2px}.training-process-summary small{font-size:11px;font-weight:900;letter-spacing:.08em;color:var(--text-soft,#687386)}.training-process-summary strong{font-size:11px;line-height:1.4}.training-process-shell.attention{border-color:#b86a3c}.training-process{display:grid;grid-template-columns:1.1fr .7fr .65fr 1.15fr 1.4fr;gap:8px;padding:11px 13px}.training-process.attention{border-color:#b86a3c}.training-process span{display:grid;gap:2px;padding-right:8px;border-right:1px solid var(--line,#d7dde6)}.training-process span:last-child{border-right:0}.training-process small{font-size:11px;font-weight:800;letter-spacing:.08em;color:var(--text-soft,#687386)}.training-process strong{font-size:11px;line-height:1.35}.training-continuity>span{display:grid;gap:2px}.training-continuity p{margin:0;font-size:11px;color:var(--text-soft,#687386)}.training-save-state{padding-left:14px;border-left:1px solid var(--line,#d7dde6)}.training-save-state.dirty strong{color:#a05a2a}.training-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.training-kpis article{display:grid;gap:4px;padding:13px 15px;background:var(--surface,#fff);border:1px solid var(--line,#d7dde6);border-radius:10px}.training-kpis article.alert{border-color:#c98946}.match-prep-card{padding:14px 16px}.match-prep-control{display:flex;justify-content:space-between;align-items:center;gap:16px}.match-prep-control p{margin:0;color:var(--text-soft,#687386);font-size:11px}.match-prep-control select{min-width:220px}.training-grid{display:grid;grid-template-columns:1.08fr .92fr;gap:14px}.training-plan-card,.risk-card,.individual-card{padding:16px}.intensity-control{display:flex;align-items:center;gap:8px}.intensity-control span{font-size:11px;color:var(--text-soft,#687386)}select{min-height:34px;border:1px solid var(--line,#d7dde6);border-radius:7px;background:var(--surface,#fff);padding:0 8px}.week-plan{display:grid;grid-template-columns:repeat(7,1fr);gap:7px;margin-top:14px}.week-plan label{display:grid;gap:5px}.week-plan label>span{font-size:11px;font-weight:800;color:var(--text-soft,#687386)}.week-plan select{width:100%;font-size:11px}.training-actions{display:flex;justify-content:space-between;align-items:center;gap:14px;margin-top:14px}.training-actions p{margin:0;font-size:11px;color:var(--text-soft,#687386)}.training-action-buttons{display:flex;gap:7px;flex-shrink:0}.medical-data-note{margin:8px 0 0;padding:8px 9px;border-radius:8px;background:var(--surface-soft,#f5f7fa);font-size:11px;line-height:1.45;color:var(--text-soft,#687386)}.risk-list{display:grid;gap:8px;margin-top:12px}.risk-row{display:grid;grid-template-columns:1.3fr .75fr .55fr;gap:8px 12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line,#e3e7ed)}.risk-row>small{grid-column:1/-1;color:var(--text-soft,#687386);font-size:11px}.risk-player{display:grid}.risk-player small{font-size:11px;color:var(--text-soft,#687386)}.risk-meter{height:5px;background:var(--surface-soft,#eef1f5);border-radius:5px;overflow:hidden}.risk-meter i{display:block;height:100%;background:currentColor}.low{color:#397a56}.medium,.warn{color:#a07420}.high{color:#b75b31}.very-high,.danger{color:#a93636}.ok{color:#397a56}.individual-card em{font-size:11px;color:var(--text-soft,#687386)}.training-table-head,.training-player-row{display:grid;grid-template-columns:1.8fr .65fr .65fr .75fr 1.05fr 1fr;gap:12px;align-items:center}.training-table-head{padding:10px 8px;font-size:11px;font-weight:800;color:var(--text-soft,#687386);border-bottom:1px solid var(--line,#d7dde6)}.training-player-row{padding:9px 8px;border-bottom:1px solid var(--line,#e3e7ed)}.training-player-row>span:first-child{display:grid}.training-player-row small{font-size:11px;color:var(--text-soft,#687386)}@media(max-width:1200px){.training-process{grid-template-columns:1fr 1fr}.training-process span{border-right:0;border-bottom:1px solid var(--line,#d7dde6);padding-bottom:7px}.week-plan{grid-template-columns:repeat(4,1fr)}.training-grid{grid-template-columns:1fr}.training-continuity{grid-template-columns:1fr 1fr}.training-save-state{grid-column:1/-1;padding:8px 0 0;border-left:0;border-top:1px solid var(--line,#d7dde6)}}@media(max-width:900px){.training-kpis{grid-template-columns:1fr 1fr}.training-hero{display:grid}.training-continuity{grid-template-columns:1fr}.training-table-head{display:none}.training-player-row{grid-template-columns:1.5fr .6fr .6fr .8fr}.training-player-row select{grid-column:1/-1}.week-plan{grid-template-columns:1fr 1fr}.training-actions{align-items:stretch;flex-direction:column}.training-action-buttons{justify-content:flex-end}}
</style>
