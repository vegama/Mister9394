<script setup>
import { computed, ref } from 'vue'
const props=defineProps({teams:{type:Array,default:()=>[]},selectedTeam:{type:Object,default:null},squad:{type:Array,default:()=>[]},history:{type:Array,default:()=>[]},manager:{type:Object,default:()=>({})},tournaments:{type:Array,default:()=>[]},formatDate:{type:Function,required:true}})
const emit=defineEmits(['select-team','open-player','accept-job','resign-job','auto-selection'])
const scope=ref('usa94')
const rosterMode=ref('current')
const visibleTeams=computed(()=>scope.value==='usa94'?props.teams.filter(team=>team.qualified_1994):props.teams)
const wc=computed(()=>props.selectedTeam?.world_cup_1994||null)
const displaySquad=computed(()=>rosterMode.value==='historical'&&wc.value?.squad?.length?wc.value.squad:props.squad)
</script>
<template>
<section class="screen-grid national-screen modern-r7">
  <article class="football-panel national-list">
    <header class="workspace-heading compact"><div><small>Mundo internacional</small><h2>Selecciones</h2><p>{{teams.filter(t=>t.qualified_1994).length}} participantes USA 94 completas · {{teams.length}} selecciones funcionales.</p></div></header>
    <div class="national-scope-switch"><button type="button" :class="{active:scope==='usa94'}" @click="scope='usa94'">USA 94</button><button type="button" :class="{active:scope==='all'}" @click="scope='all'">Todas funcionales</button></div>
    <div class="national-list-scroll"><button v-for="nt in visibleTeams" :key="nt.country_id" type="button" class="national-row" :class="{active:selectedTeam?.country_id===nt.country_id}" @click="emit('select-team',nt)"><span><strong>{{nt.name}}</strong><small><template v-if="nt.qualified_1994">Grupo {{nt.world_cup_1994_group}} · </template>{{nt.eligible_players}} elegibles <template v-if="nt.depth_ready_40">· fondo ~40 ✓</template><template v-else>· faltan {{nt.depth_gap_to_40}} para 40</template></small></span><em v-if="nt.world_cup_1994_squad_complete" class="usa94-mini">22/22</em><b>{{nt.average_top_22}}</b></button></div>
  </article>
  <article class="football-panel national-squad">
    <header class="workspace-heading"><div><small>Carrera internacional</small><h2>{{manager?.country_name ? `Seleccionador · ${manager.country_name}` : (selectedTeam?.name||'Elige un país')}}</h2><p v-if="manager?.country_name">Reputación internacional {{manager.reputation}} · el elenco histórico permanece congelado, pero forma, desarrollo y decisiones sí cambian.</p><p v-else-if="selectedTeam">Convocatoria construida con el estado real de esta carrera.</p></div><div v-if="manager?.country_id" class="workspace-actions"><button type="button" class="secondary-action" @click="emit('auto-selection')">Auto convocatoria</button><button type="button" class="secondary-action" @click="emit('resign-job')">Dejar selección</button></div></header>
    <div v-if="wc" class="usa94-context"><div><small>MUNDIAL USA 1994 · GRUPO {{wc.group}}</small><strong>Convocatoria histórica {{wc.resolved_players}}/{{wc.squad_size}}</strong><span>Seleccionador: {{wc.head_coach || '—'}}</span></div><b :class="{ok:wc.complete}">{{wc.complete?'COMPLETA':'INCOMPLETA'}}</b></div>
    <div v-if="selectedTeam" class="national-roster-switch"><button type="button" :class="{active:rosterMode==='current'}" @click="rosterMode='current'">Convocatoria actual</button><button v-if="wc" type="button" :class="{active:rosterMode==='historical'}" @click="rosterMode='historical'">USA 94 · 22 históricos</button><span v-if="rosterMode==='current'&&manager?.country_id===selectedTeam?.country_id">Tus 22 guardados</span><span v-else-if="rosterMode==='historical'">Referencia histórica, no altera tu convocatoria</span></div>
    <div v-if="!manager?.country_id && manager?.job_offers?.length" class="decision-stack"><article v-for="offer in manager.job_offers" :key="offer.id" class="decision-card"><div><small>Oferta internacional</small><strong>{{offer.country_name}}</strong><p>{{offer.reason||'La federación cree que encajas con el proyecto.'}}</p></div><button type="button" class="primary-action" @click="emit('accept-job',offer.id)">Aceptar cargo</button></article></div>
    <div v-if="tournaments.length" class="international-strip"><article v-for="t in [...tournaments].reverse().slice(0,3)" :key="t.marker||t.year"><small>{{t.year}} · Mundial 24 equipos</small><span>Campeón</span><b>{{t.champion_name}}</b><span>Reglamento 1993-94</span></article></div>
    <div v-if="!selectedTeam" class="empty-football-state">Selecciona un país para consultar convocatoria, nivel y últimos partidos.</div>
    <template v-else><div class="international-strip"><article v-for="m in history" :key="`${m.date}-${m.home_country_id}-${m.away_country_id}`"><small>{{formatDate(m.date)}}</small><span>{{m.home_name}}</span><b>{{m.home_goals}}–{{m.away_goals}}</b><span>{{m.away_name}}</span></article><p v-if="!history.length">Todavía no ha llegado una ventana internacional.</p></div><div class="table-scroll"><table><thead><tr><th>Jugador</th><th>Club</th><th>Pos</th><th>Media</th><th>USA 94</th><th>Estado</th></tr></thead><tbody><tr v-for="p in displaySquad" :key="p.id"><td><button type="button" class="player-link" @click="emit('open-player',p)">{{p.display_name}}</button></td><td>{{p.team_name}}</td><td>{{p.position}}</td><td class="rating-cell">{{p.overall}}</td><td><span v-if="p.historical_squad_1994" class="usa94-player-badge">#{{p.world_cup_1994?.shirt_number}}</span><span v-else>—</span></td><td>{{p.status}}</td></tr></tbody></table></div></template>
  </article>
</section>
</template>
