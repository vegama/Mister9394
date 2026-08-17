<script setup>
defineProps({economy:{type:Object,default:()=>({})},formatMoney:{type:Function,required:true}})
const emit=defineEmits(['open-player'])
</script>
<template>
<section class="screen-grid economy-screen modern-r7">
  <article class="football-panel economy-main">
    <header class="workspace-heading"><div><small>Dirección financiera</small><h2>Economía</h2><p>Liquidez, salarios, deuda y margen real para decidir.</p></div><span class="status-chip" :class="Number(economy.projected_monthly_net||0)>=0?'positive':'negative'">{{economy.status||'—'}}</span></header>
    <div class="economy-kpis modern-kpis"><div class="hero-kpi"><small>Caja</small><b>{{formatMoney(economy.cash)}}</b><span>liquidez</span></div><div><small>Margen traspasos</small><b>{{formatMoney(economy.transfer_room)}}</b></div><div><small>Masa salarial / año</small><b>{{formatMoney(economy.annual_wages)}}</b></div><div><small>Balance mensual</small><b :class="Number(economy.projected_monthly_net)>=0?'good-text':'bad-cell'">{{formatMoney(economy.projected_monthly_net)}}</b></div><div><small>Deuda</small><b>{{formatMoney(economy.debt)}}</b></div><div><small>Reserva recomendada</small><b>{{formatMoney(economy.safety_reserve)}}</b></div></div>
    <section class="finance-flow"><h3>Flujo mensual</h3><div><span><small>Comercial</small><b class="good-text">+{{formatMoney(economy.monthly_commercial_income)}}</b></span><span><small>Salarios</small><b class="bad-cell">-{{formatMoney(economy.monthly_wages)}}</b></span><span><small>Operación</small><b class="bad-cell">-{{formatMoney(economy.monthly_operating_expense)}}</b></span><span><small>Deuda</small><b class="bad-cell">-{{formatMoney(economy.monthly_debt_service)}}</b></span></div></section>
    <div class="financial-guidance"><strong>Margen prudente</strong><p>El juego reserva un colchón de seguridad: tener dinero en caja no significa poder gastarlo todo.</p></div>
  </article>
  <aside class="side-stack">
    <article class="football-panel"><h2>Fichas más altas</h2><div class="salary-list"><button v-for="row in economy.top_salaries" :key="row.player_id" type="button" class="salary-row salary-button" @click="emit('open-player',{id:row.player_id,name:row.name})"><span><strong>{{row.name}}</strong><small>hasta {{row.end_year}}</small></span><b>{{formatMoney(row.salary)}}</b></button><p v-if="!economy.top_salaries?.length" class="rail-empty">Sin datos salariales.</p></div></article>
    <article class="football-panel"><h2>Últimos movimientos</h2><div class="ledger-list"><p v-for="(row,index) in (economy.recent_ledger||[]).slice(-10).reverse()" :key="`${row.date}-${index}`" class="ledger-row"><span><small>{{row.date}}</small>{{row.kind}}</span><b :class="Number(row.amount)>=0?'good-text':'bad-cell'">{{Number(row.amount)>=0?'+':''}}{{formatMoney(row.amount)}}</b></p><p v-if="!economy.recent_ledger?.length" class="rail-empty">Todavía no hay movimientos registrados.</p></div></article>
    <article v-if="economy.contract_data_note" class="football-panel context-card"><h2>Origen de datos</h2><p>{{economy.contract_data_note}}</p></article>
  </aside>
</section>
</template>