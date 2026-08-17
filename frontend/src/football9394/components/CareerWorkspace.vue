<script setup>
import { computed } from 'vue'
const props=defineProps({career:{type:Object,default:()=>({})},jobStatus:{type:String,default:'active'},formatMoney:{type:Function,required:true},formatDate:{type:Function,required:true}})
const emit=defineEmits(['apply-job','accept-job','resign'])
const contract=computed(()=>props.career.active_contract||{})
const countryRows=computed(()=>Object.entries(props.career.reputation_by_country||{}).sort((a,b)=>Number(b[1])-Number(a[1])))
</script>
<template>
<section class="screen-grid career-screen modern-r7">
  <article class="football-panel career-main">
    <header class="workspace-heading"><div><small>TRAYECTORIA PROFESIONAL</small><h2>Tu carrera</h2><p>Reputación, contrato, candidaturas y proyectos viven contigo aunque cambies de club o país.</p></div><span class="status-chip" :class="jobStatus==='active'?'positive':'negative'">{{jobStatus==='active'?'Con club':'Sin club'}}</span></header>
    <div class="economy-kpis modern-kpis">
      <div class="hero-kpi"><small>Reputación</small><b>{{career.reputation ?? 50}}<em>/100</em></b><span>global</span></div>
      <div><small>Contrato</small><b>{{contract.team_name||'Sin contrato'}}</b></div>
      <div><small>Vence</small><b>{{formatDate(contract.expires_on)}}</b></div>
      <div><small>Salario anual</small><b>{{contract.annual_salary?formatMoney(contract.annual_salary):'—'}}</b></div>
    </div>
    <section v-if="contract.team_id" class="finance-flow"><h3>Proyecto contratado</h3><div><span><small>Club</small><b>{{contract.team_name}}</b></span><span><small>Competición</small><b>{{contract.league_name}}</b></span><span><small>Objetivo</small><b>{{contract.expected_position}}º esperado</b></span><span><small>Duración</small><b>{{contract.years}} temporada{{contract.years===1?'':'s'}}</b></span></div></section>
    <div v-if="jobStatus==='active'" class="financial-guidance"><strong>Tu contrato no te encierra</strong><p>Puedes escuchar otros proyectos o dimitir. Ambas decisiones quedan en tu historial y alteran relaciones futuras.</p><button type="button" class="football-button" @click="emit('resign')">Dimitir del club</button></div>

    <section class="career-market-section"><header class="workspace-heading compact"><div><small>MERCADO DE BANQUILLOS</small><h3>Vacantes y clubes en revisión</h3><p>La lista nace del estado real de los banquillos, la presión y tu reputación local.</p></div></header>
      <div class="career-job-offers">
        <article v-for="job in career.available_jobs||[]" :key="job.id"><small>{{job.country}} · {{job.league_name}}</small><strong>{{job.team_name}}</strong><span>{{job.position}}º ahora · expectativa {{job.expected_position}}º</span><em>Encaje {{Math.round(job.suitability)}}/100 · presión {{job.manager_pressure}}/100</em><button type="button" class="football-button" @click="emit('apply-job',job.id)">Presentar candidatura</button></article>
        <div v-if="!career.available_jobs?.length" class="empty-football-state">No hay un banquillo compatible en revisión ahora mismo.</div>
      </div>
    </section>
    <section v-if="career.career_offers?.length" class="career-market-section"><header class="workspace-heading compact"><div><small>PROPUESTAS</small><h3>Ofertas sobre la mesa</h3></div></header><div class="career-job-offers"><article v-for="offer in career.career_offers" :key="offer.id"><small>{{offer.league_name}}</small><strong>{{offer.team_name}}</strong><span>{{offer.project_preview?.objective||'Proyecto deportivo'}}</span><em>Encaje {{Math.round(offer.suitability||0)}}/100</em><button type="button" class="football-button primary" @click="emit('accept-job',offer.id)">Aceptar proyecto</button></article></div></section>
  </article>
  <aside class="side-stack">
    <article class="football-panel"><h2>Reputación por país</h2><div class="ledger-list"><p v-for="([country,value]) in countryRows" :key="country" class="ledger-row"><span>{{country}}</span><b>{{Math.round(value)}}/100</b></p><p v-if="!countryRows.length" class="rail-empty">Tu reputación local crecerá al competir en otros países.</p></div></article>
    <article class="football-panel"><h2>Relaciones con clubes</h2><div class="career-relationship-grid"><article v-for="row in [...(career.relationships||[])].sort((a,b)=>(Number(b.trust||0)+Number(b.respect||0))-(Number(a.trust||0)+Number(a.respect||0))).slice(0,6)" :key="row.team_id"><strong>{{row.team_name||`Club ${row.team_id}`}}</strong><span>Confianza {{row.trust}} · respeto {{row.respect}}</span><small>{{row.last_reason||'Relación profesional sin episodio reciente.'}}</small></article><p v-if="!career.relationships?.length" class="rail-empty">Las relaciones aparecerán al negociar tu carrera con otros clubes.</p></div></article>
    <article class="football-panel"><h2>Últimas entrevistas</h2><div class="manager-change-list"><article v-for="row in [...(career.interviews||[])].reverse().slice(0,6)" :key="row.id"><time>{{formatDate(row.date)}}</time><strong>{{row.team_name}}</strong><span>{{row.status==='passed'?'Entrevista superada':'Candidatura rechazada'}} · encaje {{Math.round(row.project_fit||0)}}/100</span></article><p v-if="!career.interviews?.length" class="rail-empty">Todavía no has pasado por una entrevista.</p></div></article>
    <article class="football-panel"><h2>Etapas</h2><div class="manager-change-list"><article v-for="row in [...(career.tenures||[])].reverse().slice(0,6)" :key="`${row.team_id}-${row.started_on}`"><time>{{formatDate(row.started_on)}} → {{formatDate(row.ended_on)}}</time><strong>{{row.team_name}}</strong><span>{{row.reason==='resigned'?'Dimisión':row.reason==='dismissed'?'Destitución':'Etapa cerrada'}}</span></article><p v-if="!career.tenures?.length" class="rail-empty">Tu primera etapa todavía está en curso.</p></div></article>
  </aside>
</section>
</template>
