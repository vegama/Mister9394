<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  training: { type: Object, default: () => ({ weekly_plan: [], players: [], session_options: [], intensity_options: [], focus_options: [], responsibility: {} }) },
})
const emit = defineEmits(['save-plan','set-focus','set-recovery','set-match-preparation'])

const localIntensity = ref('normal')
const localWeek = ref([])
watch(() => props.training, value => {
  localIntensity.value = value?.intensity || 'normal'
  localWeek.value = (value?.weekly_plan || []).map(row => row.session)
}, { immediate: true, deep: true })

const topRisk = computed(() => (props.training?.players || []).slice(0, 8))
const riskClass = value => value >= 70 ? 'very-high' : value >= 52 ? 'high' : value >= 34 ? 'medium' : 'low'
const conditionClass = value => value < 65 ? 'danger' : value < 78 ? 'warn' : 'ok'
function save(){ emit('save-plan', { intensity: localIntensity.value, weekly_plan: [...localWeek.value] }) }
</script>

<template>
  <section class="training-workspace">
    <header class="training-hero football-panel">
      <div><small>PREPARACIÓN DEL PRIMER EQUIPO</small><h2>Entrenamiento y carga</h2><p>Planifica la semana sin perder de vista condición, fatiga y riesgo. La calidad del responsable modifica cuánto trabajo útil obtiene el equipo de cada sesión.</p></div>
      <div class="training-owner"><small>RESPONSABLE</small><strong>{{training.responsibility?.assignee_name || 'Tú (mánager)'}}</strong><span>{{training.responsibility?.quality_label || 'Decisión directa'}} · carga {{training.responsibility?.workload_label || '—'}}</span></div>
    </header>

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
        <div class="training-actions"><p>Los días de partido y la víspera pueden ajustar automáticamente la sesión para evitar incoherencias con el calendario.</p><button type="button" class="football-button primary" @click="save">Guardar plan</button></div>
      </article>

      <article class="football-panel risk-card">
        <header class="simple-panel-head"><span><small>ÁREA MÉDICA + PREPARACIÓN</small><strong>Jugadores a vigilar</strong></span><b>{{training.very_high_risk_count || 0}} críticos</b></header>
        <div class="risk-list">
          <div v-for="player in topRisk" :key="player.player_id" class="risk-row">
            <span class="risk-player"><strong>{{player.name}}</strong><small>{{player.position}} · condición {{player.condition}}%</small></span>
            <span class="risk-meter"><i :style="{width:`${player.risk}%`}" :class="riskClass(player.risk)"></i></span>
            <b :class="riskClass(player.risk)">{{player.risk_label}}</b>
            <small>{{player.recommendation}}</small>
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
.training-workspace{display:grid;gap:14px}.training-hero{display:flex;justify-content:space-between;gap:28px;padding:20px}.training-hero h2{margin:3px 0 6px}.training-hero p{max-width:760px;margin:0;color:var(--text-soft,#687386)}.training-owner{min-width:220px;display:grid;align-content:center;gap:3px;padding:12px 14px;background:var(--surface-soft,#f5f7fa);border-radius:10px}.training-owner small,.training-kpis small,.training-hero>div>small{font-size:10px;font-weight:800;letter-spacing:.08em;color:var(--text-soft,#687386)}.training-owner span{font-size:11px;color:var(--text-soft,#687386)}.training-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.training-kpis article{display:grid;gap:4px;padding:13px 15px;background:var(--surface,#fff);border:1px solid var(--line,#d7dde6);border-radius:10px}.training-kpis article.alert{border-color:#c98946}.match-prep-card{padding:14px 16px}.match-prep-control{display:flex;justify-content:space-between;align-items:center;gap:16px}.match-prep-control p{margin:0;color:var(--text-soft,#687386);font-size:11px}.match-prep-control select{min-width:220px}.training-grid{display:grid;grid-template-columns:1.08fr .92fr;gap:14px}.training-plan-card,.risk-card,.individual-card{padding:16px}.intensity-control{display:flex;align-items:center;gap:8px}.intensity-control span{font-size:11px;color:var(--text-soft,#687386)}select{min-height:34px;border:1px solid var(--line,#d7dde6);border-radius:7px;background:var(--surface,#fff);padding:0 8px}.week-plan{display:grid;grid-template-columns:repeat(7,1fr);gap:7px;margin-top:14px}.week-plan label{display:grid;gap:5px}.week-plan label>span{font-size:10px;font-weight:800;color:var(--text-soft,#687386)}.week-plan select{width:100%;font-size:11px}.training-actions{display:flex;justify-content:space-between;align-items:center;gap:14px;margin-top:14px}.training-actions p{margin:0;font-size:11px;color:var(--text-soft,#687386)}.risk-list{display:grid;gap:8px;margin-top:12px}.risk-row{display:grid;grid-template-columns:1.3fr .75fr .55fr;gap:8px 12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line,#e3e7ed)}.risk-row>small{grid-column:1/-1;color:var(--text-soft,#687386);font-size:10px}.risk-player{display:grid}.risk-player small{font-size:10px;color:var(--text-soft,#687386)}.risk-meter{height:5px;background:var(--surface-soft,#eef1f5);border-radius:5px;overflow:hidden}.risk-meter i{display:block;height:100%;background:currentColor}.low{color:#397a56}.medium,.warn{color:#a07420}.high{color:#b75b31}.very-high,.danger{color:#a93636}.ok{color:#397a56}.individual-card em{font-size:10px;color:var(--text-soft,#687386)}.training-table-head,.training-player-row{display:grid;grid-template-columns:1.8fr .65fr .65fr .75fr 1.05fr 1fr;gap:12px;align-items:center}.training-table-head{padding:10px 8px;font-size:10px;font-weight:800;color:var(--text-soft,#687386);border-bottom:1px solid var(--line,#d7dde6)}.training-player-row{padding:9px 8px;border-bottom:1px solid var(--line,#e3e7ed)}.training-player-row>span:first-child{display:grid}.training-player-row small{font-size:10px;color:var(--text-soft,#687386)}@media(max-width:1200px){.week-plan{grid-template-columns:repeat(4,1fr)}.training-grid{grid-template-columns:1fr}}@media(max-width:900px){.training-kpis{grid-template-columns:1fr 1fr}.training-hero{display:grid}.training-table-head{display:none}.training-player-row{grid-template-columns:1.5fr .6fr .6fr .8fr}.training-player-row select{grid-column:1/-1}.week-plan{grid-template-columns:1fr 1fr}}
</style>
