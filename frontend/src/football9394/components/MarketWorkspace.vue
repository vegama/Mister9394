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
  transferRoom: { type: Number, default: 0 },
  marketFlow: { type: Object, default: () => ({}) },
  activeNegotiations: { type: Array, default: () => [] },
  incomingOffers: { type: Array, default: () => [] },
  ownSquad: { type: Array, default: () => [] },
})
const emit = defineEmits([
  'update:query','update:position','update:freeAgents','update:watchedOnly','update:transferFee','update:transferSalary','update:transferYears',
  'search','watch','open-player','choose-target','submit','counter','accept-offer'
])

const money = value => value == null ? '—' : `${Number(value).toLocaleString('es-ES')} ptas.`
const playerName = id => props.ownSquad.find(p=>Number(p.id)===Number(id))?.name || props.targets.find(p=>Number(p[5])===Number(id))?.[0] || `Jugador #${id}`
const photo = id => id ? `/historical9394/players/${Number(id)}.jpg` : null
const dateShort = value => { if(!value)return '—'; const p=String(value).split('-'); return p.length===3?`${p[2]}/${p[1]}/${p[0]}`:String(value) }
</script>

<template>
  <section class="market-workspace redesigned-market">
    <article class="football-panel market-discovery">
      <header class="panel-feature-head">
        <div><small>RECLUTAMIENTO</small><h2>Mercado de fichajes</h2><p>Busca perfiles, crea una lista de seguimiento y abre una negociación sin perder los resultados.</p></div>
        <div class="market-window-status" :class="{closed:!period.open}"><span>{{period.open?'Mercado abierto':'Mercado cerrado'}}</span><strong>{{period.label}}</strong><small v-if="period.next_change">Cambio: {{dateShort(period.next_change)}}</small></div>
      </header>

      <div class="market-searchbar">
        <label class="market-search-main"><span>Jugador</span><input :value="query" type="search" placeholder="Nombre del jugador" @input="emit('update:query',$event.target.value)" @keyup.enter="emit('search')"></label>
        <label><span>Posición</span><select :value="position" @change="emit('update:position',$event.target.value)"><option value="">Todas</option><option value="POR">Portero</option><option value="LD">Lateral derecho</option><option value="LI">Lateral izquierdo</option><option value="CB">Central</option><option value="MCD">Mediocentro defensivo</option><option value="MC">Mediocentro</option><option value="MP">Mediapunta</option><option value="MD">Banda derecha</option><option value="MI">Banda izquierda</option><option value="ED">Extremo derecho</option><option value="EI">Extremo izquierdo</option><option value="DC">Delantero centro</option></select></label>
        <button type="button" class="filter-toggle" :class="{active:freeAgents}" @click="emit('update:freeAgents',!freeAgents)">Agentes libres</button>
        <button type="button" class="filter-toggle" :class="{active:watchedOnly}" @click="emit('update:watchedOnly',!watchedOnly)">Seguimiento</button>
        <button type="button" class="football-button primary market-search-button" @click="emit('search')">Buscar</button>
      </div>

      <div class="market-result-head"><span>Jugador</span><span>Pos.</span><span>Club</span><span>Media</span><span>Valor</span><span></span></div>
      <div class="market-results">
        <article v-for="t in targets" :key="t[5]" class="market-player-row" :class="{selected:selectedTarget?.[5]===t[5]}">
          <button type="button" class="watch-control" :class="{active:t[6]?.watched}" :title="t[6]?.watched?'Quitar de seguimiento':'Añadir a seguimiento'" @click="emit('watch',t)">{{t[6]?.watched?'★':'☆'}}</button>
          <button type="button" class="market-player-identity" @click="emit('open-player',{id:t[5],name:t[0],profile:t[6]})"><span class="market-photo"><img :src="photo(t[5])" alt="" @error="$event.currentTarget.style.display='none'"></span><span><strong>{{t[0]}}</strong><small>{{t[6]?.nationality || '—'}} · {{t[6]?.identity?.archetype || 'perfil'}}</small><small class="market-fit">Encaje {{t[6]?.tactical_fit?.label || '—'}} · {{t[6]?.market?.reason==='quiere_salir'?'quiere salir':t[6]?.market?.reason==='contrato_corto'?'contrato corto':t[6]?.market?.reason==='reserva'?'rol secundario':'sin señal de salida'}}</small></span></button>
          <span><b class="position-chip">{{t[1]}}</b></span><span class="market-club">{{t[2]}}</span><strong class="market-rating">{{t[3]}}</strong><span class="market-value">{{t[6]?.market?.free_agent?'LIBRE':money(t[4])}}</span><button type="button" class="football-button tiny" :disabled="!period.open" @click="emit('choose-target',t)">{{selectedTarget?.[5]===t[5]?'Seleccionado':'Negociar'}}</button>
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
          <div class="selected-target-summary"><span class="market-photo large"><img :src="photo(selectedTarget[5])" alt="" @error="$event.currentTarget.style.display='none'"></span><span><strong>{{selectedTarget[0]}}</strong><small>{{selectedTarget[1]}} · {{selectedTarget[2]}}</small><em>{{selectedTarget[6]?.market?.free_agent?'Agente libre':`Valor ${money(selectedTarget[4])}`}}</em><small>Encaje táctico: {{selectedTarget[6]?.tactical_fit?.label || '—'}} · satisfacción {{selectedTarget[6]?.squad_dynamics?.satisfaction ?? '—'}}</small></span></div>
          <div class="market-fit-rationale d6-market-fit"><small>POR QUÉ PUEDE ENCAJAR</small><span v-for="reason in selectedTarget[6]?.tactical_fit?.reasons || []" :key="reason">{{reason}}</span><span v-if="!(selectedTarget[6]?.tactical_fit?.reasons||[]).length">El informe no detecta una ventaja táctica específica.</span></div>
          <label><span>Traspaso</span><input :value="transferFee" type="number" min="0" :disabled="selectedTarget[6]?.market?.free_agent" @input="emit('update:transferFee',Number($event.target.value))"></label>
          <label><span>Ficha anual</span><input :value="transferSalary" type="number" min="0" @input="emit('update:transferSalary',Number($event.target.value))"></label>
          <label><span>Duración</span><select :value="transferYears" @change="emit('update:transferYears',Number($event.target.value))"><option v-for="year in [1,2,3,4,5,6]" :key="year" :value="year">{{year}} año{{year===1?'':'s'}}</option></select></label>
          <button type="button" class="football-button primary" :disabled="!period.open" @click="emit('submit')">Enviar oferta</button>
          <p>La respuesta llegará con el paso de los días; club, jugador y competencia pueden alterar las condiciones.</p>
        </div>
        <div v-else class="deal-empty">Selecciona un jugador de los resultados para preparar una oferta.</div>
      </article>

      <article class="football-panel negotiation-stack"><header class="simple-panel-head"><span><small>EN CURSO</small><strong>Negociaciones</strong></span><b>{{activeNegotiations.length}}</b></header><div v-for="n in activeNegotiations" :key="n.id" class="negotiation-card"><strong>{{playerName(n.player_id)}}</strong><span v-if="n.status==='waiting'">Esperando respuesta · {{dateShort(n.response_date)}}</span><template v-else><span>Contraoferta: {{money(n.counter_fee)}} · ficha {{money(n.counter_salary)}}</span><button class="football-button tiny" @click="emit('counter',n)">Responder</button></template></div><div v-if="!activeNegotiations.length" class="rail-empty">No hay negociaciones pendientes.</div></article>

      <article class="football-panel negotiation-stack"><header class="simple-panel-head"><span><small>ENTRADAS</small><strong>Ofertas recibidas</strong></span><b>{{incomingOffers.length}}</b></header><div v-for="o in incomingOffers" :key="o.id" class="negotiation-card"><strong>{{playerName(o.player_id)}}</strong><span>{{o.buyer_team_name}} · {{money(o.fee)}}</span><small>Caduca {{dateShort(o.expires_on)}}</small><button class="football-button tiny" @click="emit('accept-offer',o)">Aceptar</button></div><div v-if="!incomingOffers.length" class="rail-empty">No hay ofertas abiertas por tus jugadores.</div></article>
    </aside>
  </section>
</template>
