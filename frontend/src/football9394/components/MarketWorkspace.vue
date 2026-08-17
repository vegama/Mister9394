<script setup>
const props = defineProps({
  period: { type: Object, default: () => ({}) },
  query: { type: String, default: '' },
  position: { type: String, default: '' },
  freeAgents: { type: Boolean, default: false },
  watchedOnly: { type: Boolean, default: false },
  targets: { type: Array, default: () => [] },
  selectedTarget: { type: Array, default: null },
  transferFee: { type: Number, default: 0 },
  transferSalary: { type: Number, default: 0 },
  transferYears: { type: Number, default: 3 },
  transferSquadRole: { type: String, default: 'rotation' },
  transferSigningBonus: { type: Number, default: 0 },
  transferReleaseClause: { type: Number, default: null },
  transferDealType: { type: String, default: 'transfer' },
  transferLoanWageShare: { type: Number, default: 100 },
  transferRoom: { type: Number, default: 0 },
  marketFlow: { type: Object, default: () => ({}) },
  activeNegotiations: { type: Array, default: () => [] },
  incomingOffers: { type: Array, default: () => [] },
  ownSquad: { type: Array, default: () => [] },
  scouting: { type: Object, default: () => ({ active: [], recent_reports: [], responsibility: {} }) },
  squadPlan: { type: Object, default: () => ({ priorities: [], expiring: [], succession: [], surplus: [] }) },
})
const emit = defineEmits([
  'update:query','update:position','update:freeAgents','update:watchedOnly','update:transferFee','update:transferSalary','update:transferYears','update:transferSquadRole','update:transferSigningBonus','update:transferReleaseClause','update:transferDealType','update:transferLoanWageShare',
  'search','apply-plan','watch','scout','inquire','open-player','choose-target','submit','counter','withdraw','accept-offer'
])

const money = value => value == null ? '—' : `${Number(value).toLocaleString('es-ES')} ptas.`
const playerName = id => props.ownSquad.find(p=>Number(p.id)===Number(id))?.name || props.targets.find(p=>Number(p[5])===Number(id))?.[0] || `Jugador #${id}`
const photo = id => id ? `/historical9394/players/${Number(id)}.jpg` : null
const dateShort = value => { if(!value)return '—'; const p=String(value).split('-'); return p.length===3?`${p[2]}/${p[1]}/${p[0]}`:String(value) }

const knowledgeText = t => { const scout=t?.[6]?.scout||{}; return scout.stale ? `${scout.knowledge || 'Informe'} · ${scout.freshness || 'desactualizado'}` : (scout.knowledge || 'Sin informe') }
const overallText = t => {
  const p=t?.[6]||{}; const r=p.overall_range
  return p.overall_is_exact ? String(p.overall ?? '—') : Array.isArray(r) ? `${r[0]}–${r[1]}` : '—'
}
const valueText = t => {
  const p=t?.[6]||{}; if(p.market?.free_agent)return 'LIBRE'
  const r=p.market?.value_range
  if(!p.transfer_value_is_exact && Array.isArray(r) && r[1]>0)return `≈ ${money(p.estimated_transfer_value)}`
  return money(p.estimated_transfer_value)
}
const scoutingTask = id => (props.scouting?.active||[]).find(row=>Number(row.player_id)===Number(id))
const roleText = value => ({star:'Figura',starter:'Titular',rotation:'Rotación',prospect:'Proyecto',depth:'Fondo de plantilla'})[value] || value || 'Rotación'
const stanceText = value => ({free:'Libre',open:'Abierto a negociar',negotiable:'Negociable',difficult:'Difícil'})[value] || value || 'Por confirmar'
</script>

<template>
  <section class="market-workspace redesigned-market">
    <article class="football-panel market-discovery">
      <header class="panel-feature-head">
        <div><small>RECLUTAMIENTO</small><h2>Mercado de fichajes</h2><p>Busca perfiles, crea una lista de seguimiento y abre una negociación sin perder los resultados.</p></div>
        <div class="market-window-status" :class="{closed:!period.open}"><span>{{period.open?'Mercado abierto':'Mercado cerrado'}}</span><strong>{{period.label}}</strong><small v-if="period.next_change">Cambio: {{dateShort(period.next_change)}}</small></div>
      </header>

      <div v-if="(squadPlan.priorities||[]).length" class="market-plan-strip">
        <div class="market-plan-title"><span><small>PLANIFICACIÓN DE PLANTILLA</small><strong>Necesidades detectadas</strong></span><em>{{squadPlan.squad_size}} / {{squadPlan.target_squad_size}} jugadores objetivo</em></div>
        <div class="market-plan-priorities"><button type="button" v-for="need in (squadPlan.priorities||[]).slice(0,4)" :key="need.slot" @click="emit('apply-plan',need)"><b>{{need.label}}</b><span>{{need.priority}} · {{need.action}}</span><small v-if="need.slot!=='DEPTH'">{{need.count}} efectivos · nivel {{need.average}}</small><small v-else>Faltan {{need.shortage}} para el mínimo</small><em>Buscar perfiles →</em></button></div>
      </div>

      <div class="market-searchbar">
        <label class="market-search-main"><span>Jugador</span><input :value="query" type="search" placeholder="Nombre del jugador" @input="emit('update:query',$event.target.value)" @keyup.enter="emit('search')"></label>
        <label><span>Posición</span><select :value="position" @change="emit('update:position',$event.target.value)"><option value="">Todas</option><option value="POR">Portero</option><option value="LD">Lateral derecho</option><option value="LI">Lateral izquierdo</option><option value="CB">Central</option><option value="MCD">Mediocentro defensivo</option><option value="MC">Mediocentro</option><option value="MP">Mediapunta</option><option value="MD">Banda derecha</option><option value="MI">Banda izquierda</option><option value="ED">Extremo derecho</option><option value="EI">Extremo izquierdo</option><option value="DC">Delantero centro</option></select></label>
        <button type="button" class="filter-toggle" :class="{active:freeAgents}" @click="emit('update:freeAgents',!freeAgents)">Agentes libres</button>
        <button type="button" class="filter-toggle" :class="{active:watchedOnly}" @click="emit('update:watchedOnly',!watchedOnly)">Seguimiento</button>
        <button type="button" class="football-button primary market-search-button" @click="emit('search')">Buscar</button>
      </div>

      <div class="market-result-head"><span>Jugador</span><span>Pos.</span><span>Club</span><span>Nivel</span><span>Valor</span><span></span></div>
      <div class="market-results">
        <article v-for="t in targets" :key="t[5]" class="market-player-row" :class="{selected:selectedTarget?.[5]===t[5]}">
          <button type="button" class="watch-control" :class="{active:t[6]?.watched}" :title="t[6]?.watched?'Quitar de seguimiento':'Añadir a seguimiento'" @click="emit('watch',t)">{{t[6]?.watched?'★':'☆'}}</button>
          <button type="button" class="market-player-identity" @click="emit('open-player',{id:t[5],name:t[0],profile:t[6]})"><span class="market-photo"><img :src="photo(t[5])" alt="" @error="$event.currentTarget.style.display='none'"></span><span><strong>{{t[0]}}</strong><small>{{t[6]?.nationality || '—'}} · {{t[6]?.identity?.archetype || 'perfil'}}</small><small class="market-knowledge">{{knowledgeText(t)}}<template v-if="t[6]?.scout?.confidence"> · confianza {{t[6].scout.confidence}}</template></small><small class="market-fit">Encaje {{t[6]?.tactical_fit?.label || '—'}} · {{t[6]?.market?.reason==='quiere_salir'?'quiere salir':t[6]?.market?.reason==='contrato_corto'?'contrato corto':t[6]?.market?.reason==='reserva'?'rol secundario':'sin señal de salida'}}</small></span></button>
          <span><b class="position-chip">{{t[1]}}</b></span><span class="market-club">{{t[2]}}</span><strong class="market-rating" :title="t[6]?.overall_is_exact?'Dato conocido':'Rango estimado por scouting'">{{overallText(t)}}</strong><span class="market-value">{{valueText(t)}}</span><span class="market-row-actions"><button type="button" class="football-button tiny secondary" :disabled="Boolean(scoutingTask(t[5])) || t[6]?.scout?.level>=4 || (scouting.available_capacity??1)<=0" @click="emit('scout',t)">{{scoutingTask(t[5])?`Informe ${dateShort(scoutingTask(t[5]).due_on)}`:t[6]?.scout?.level>=3?'Profundizar':(scouting.available_capacity??1)<=0?'Sin capacidad':'Ojear'}}</button><button type="button" class="football-button tiny secondary" :disabled="!period.open || t[6]?.market?.free_agent" @click="emit('inquire',t)">Consultar</button><button type="button" class="football-button tiny" :disabled="!period.open" @click="emit('choose-target',t)">{{selectedTarget?.[5]===t[5]?'Seleccionado':'Negociar'}}</button></span>
        </article>
        <div v-if="!targets.length" class="market-empty"><b>Busca un perfil</b><span>Los resultados aparecerán aquí conservando filtros y contexto.</span></div>
      </div>
    </article>

    <aside class="market-deal-rail">
      <article class="football-panel deal-card">
        <header class="simple-panel-head"><span><small>OPERACIÓN</small><strong>{{selectedTarget?selectedTarget[0]:'Sin jugador seleccionado'}}</strong></span></header>
        <div class="deal-budget"><small>Margen de traspasos</small><b>{{money(transferRoom)}}</b></div>
        <div v-if="marketFlow.foreign_rule" class="quota-modern"><span><small>Extranjeros</small><b>{{marketFlow.foreign_count}} / {{marketFlow.foreign_rule.max_squad ?? '∞'}}</b></span><p>La IA utiliza el mismo límite de inscripción.</p></div>
        <div v-if="selectedTarget" class="deal-form">
          <div class="selected-target-summary"><span class="market-photo large"><img :src="photo(selectedTarget[5])" alt="" @error="$event.currentTarget.style.display='none'"></span><span><strong>{{selectedTarget[0]}}</strong><small>{{selectedTarget[1]}} · {{selectedTarget[2]}}</small><em>{{selectedTarget[6]?.market?.free_agent?'Agente libre':`Valor ${valueText(selectedTarget)}`}}</em><small>{{knowledgeText(selectedTarget)}} · encaje táctico {{selectedTarget[6]?.tactical_fit?.label || 'por evaluar'}}</small></span></div>
          <div class="market-fit-rationale d6-market-fit"><small>POR QUÉ PUEDE ENCAJAR</small><span v-for="reason in selectedTarget[6]?.tactical_fit?.reasons || []" :key="reason">{{reason}}</span><span v-if="!(selectedTarget[6]?.tactical_fit?.reasons||[]).length">El informe no detecta una ventaja táctica específica.</span></div>
          <label><span>Tipo de operación</span><select :value="transferDealType" @change="emit('update:transferDealType',$event.target.value)"><option value="transfer">Traspaso</option><option value="loan" :disabled="selectedTarget[6]?.market?.free_agent">Cesión hasta 30 de junio</option></select></label>
          <label><span>{{transferDealType==='loan'?'Cuota de cesión':'Traspaso'}}</span><input :value="transferFee" type="number" min="0" :disabled="selectedTarget[6]?.market?.free_agent" @input="emit('update:transferFee',Number($event.target.value))"></label>
          <label v-if="transferDealType==='transfer'"><span>Ficha anual</span><input :value="transferSalary" type="number" min="0" @input="emit('update:transferSalary',Number($event.target.value))"></label>
          <label v-else><span>Porcentaje de ficha asumido</span><input :value="transferLoanWageShare" type="number" min="0" max="100" @input="emit('update:transferLoanWageShare',Number($event.target.value))"></label>
          <label v-if="transferDealType==='transfer'"><span>Duración</span><select :value="transferYears" @change="emit('update:transferYears',Number($event.target.value))"><option v-for="year in [1,2,3,4,5,6]" :key="year" :value="year">{{year}} año{{year===1?'':'s'}}</option></select></label>
          <label><span>Rol prometido</span><select :value="transferSquadRole" @change="emit('update:transferSquadRole',$event.target.value)"><option value="star">Figura</option><option value="starter">Titular</option><option value="rotation">Rotación</option><option value="prospect">Proyecto</option><option value="depth">Fondo de plantilla</option></select></label>
          <label v-if="transferDealType==='transfer'"><span>Prima de fichaje</span><input :value="transferSigningBonus" type="number" min="0" @input="emit('update:transferSigningBonus',Number($event.target.value))"></label>
          <label v-if="transferDealType==='transfer'"><span>Cláusula de rescisión</span><input :value="transferReleaseClause ?? ''" type="number" min="0" placeholder="Sin cláusula" @input="emit('update:transferReleaseClause',$event.target.value?Number($event.target.value):null)"></label>
          <button type="button" class="football-button primary" :disabled="!period.open" @click="emit('submit')">Enviar oferta</button>
          <p>La respuesta llegará con el paso de los días; club, jugador y competencia pueden alterar las condiciones.</p>
        </div>
        <div v-else class="deal-empty">Selecciona un jugador de los resultados para preparar una oferta.</div>
      </article>

      <article v-if="(marketFlow.inquiries||[]).length" class="football-panel negotiation-stack inquiry-stack"><header class="simple-panel-head"><span><small>CONSULTAS</small><strong>Disponibilidad orientativa</strong></span><b>{{marketFlow.inquiries.length}}</b></header><div v-for="row in marketFlow.inquiries.slice(-4).reverse()" :key="row.id" class="negotiation-card"><strong>{{row.player_name || playerName(row.player_id)}}</strong><span>{{row.stance_label || stanceText(row.stance)}} · {{row.asking_range?.length===2?`${money(row.asking_range[0])}–${money(row.asking_range[1])}`:'precio por concretar'}}</span><small>{{row.handled_by || row.handler_name || 'Responsable de mercado'}} · confianza {{row.confidence ?? '—'}}%</small></div></article>

      <article class="football-panel negotiation-stack scouting-stack"><header class="simple-panel-head"><span><small>OJEADORES · {{scouting.responsibility?.assignee_name || 'Responsable'}}</small><strong>Informes en curso</strong></span><b>{{scouting.used_capacity || 0}} / {{scouting.capacity || 1}}</b></header><div v-for="task in scouting.active || []" :key="task.id" class="negotiation-card"><strong>{{task.player_name}}</strong><span>{{task.responsible}} · informe previsto {{dateShort(task.due_on)}}</span><small>{{task.scope_label || 'Seguimiento'}}<template v-if="task.travel_days"> · {{task.travel_days}} d de desplazamiento</template> · objetivo: {{task.target_level>=4?'conocimiento profundo':'informe fiable'}}</small></div><div v-if="!(scouting.active||[]).length" class="rail-empty">No hay informes en curso. Puedes negociar sin informe, asumiendo más incertidumbre.</div><div v-if="scouting.stale_reports" class="rail-empty">{{scouting.stale_reports}} informe{{scouting.stale_reports===1?'':'s'}} necesita{{scouting.stale_reports===1?'':'n'}} actualización.</div></article>

      <article class="football-panel negotiation-stack"><header class="simple-panel-head"><span><small>EN CURSO</small><strong>Negociaciones</strong></span><b>{{activeNegotiations.length}}</b></header><div v-for="n in activeNegotiations" :key="n.id" class="negotiation-card"><strong>{{playerName(n.player_id)}}</strong><span v-if="n.status==='waiting'">Esperando respuesta · {{dateShort(n.response_date)}}</span><template v-else><span>Contraoferta: {{money(n.counter_fee)}} · ficha {{money(n.counter_salary)}}</span><button class="football-button tiny" @click="emit('counter',n)">Responder</button></template><small>{{n.deal_type==='loan'?'Cesión':'Traspaso'}} · rol {{roleText(n.squad_role)}}<template v-if="n.deal_type==='loan'"> · ficha {{n.loan_wage_share}}%</template><template v-else-if="n.signing_bonus"> · prima {{money(n.signing_bonus)}}</template></small><button type="button" class="football-button tiny secondary" @click="emit('withdraw',n)">Retirar</button></div><div v-if="!activeNegotiations.length" class="rail-empty">No hay negociaciones pendientes.</div></article>

      <article class="football-panel negotiation-stack"><header class="simple-panel-head"><span><small>ENTRADAS</small><strong>Ofertas recibidas</strong></span><b>{{incomingOffers.length}}</b></header><div v-for="o in incomingOffers" :key="o.id" class="negotiation-card"><strong>{{playerName(o.player_id)}}</strong><span>{{o.buyer_team_name}} · {{money(o.fee)}}</span><small>Caduca {{dateShort(o.expires_on)}}</small><button class="football-button tiny" @click="emit('accept-offer',o)">Aceptar</button></div><div v-if="!incomingOffers.length" class="rail-empty">No hay ofertas abiertas por tus jugadores.</div></article>
    </aside>
  </section>
</template>

<style scoped>
.market-plan-strip{display:grid;gap:10px;margin:12px 0 16px;padding:12px;border:1px solid var(--line,#d7dde6);border-radius:10px;background:var(--surface-soft,#f5f7fa)}.market-plan-title{display:flex;justify-content:space-between;gap:12px;align-items:end}.market-plan-title span{display:grid}.market-plan-title small{font-size:10px;letter-spacing:.08em;font-weight:800;color:var(--text-soft,#687386)}.market-plan-title em{font-size:11px;color:var(--text-soft,#687386)}.market-plan-priorities{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.market-plan-priorities button{display:grid;gap:2px;padding:9px;text-align:left;background:var(--surface,#fff);border:1px solid transparent;border-radius:8px;cursor:pointer;color:inherit}.market-plan-priorities button:hover{border-color:var(--line,#d7dde6)}.market-plan-priorities button em{font-size:10px;font-style:normal;font-weight:700;margin-top:3px}.market-plan-priorities span,.market-plan-priorities small,.market-knowledge{font-size:10px;color:var(--text-soft,#687386)}.market-row-actions{display:flex;gap:5px;justify-content:flex-end}.market-row-actions .football-button{white-space:nowrap}@media(max-width:1100px){.market-plan-priorities{grid-template-columns:1fr 1fr}.market-row-actions{flex-direction:column}}
</style>
