<script setup>
import { computed } from 'vue'
import BaseModal from '../../components/BaseModal.vue'
import UiDataTable from '../../components/ui/UiDataTable.vue'
import UiEmptyState from '../../components/ui/UiEmptyState.vue'

const props=defineProps({
  detail:{type:Object,required:true},
  crestFor:{type:Function,required:true},
  stadiumFor:{type:Function,required:true},
})
const emit=defineEmits(['close','open-player','open-team','open-competition','open-controlled-club'])
const team=computed(()=>props.detail?.team||{})
const manager=computed(()=>props.detail?.manager||{})
const standing=computed(()=>props.detail?.standing||null)
const status=computed(()=>props.detail?.club_status||{})
const venue=computed(()=>props.detail?.venue||null)
const mainRival=computed(()=>props.detail?.main_rival||null)
const regionalRival=computed(()=>props.detail?.regional_rival||null)
const squad=computed(()=>props.detail?.squad||[])
const honours=computed(()=>team.value.honours||{})
const honourTotal=computed(()=>Object.values(honours.value).reduce((sum,value)=>sum+(Number(value)||0),0))
const knownOverall=row=>{
  if(row?.overall_is_exact===false && Array.isArray(row?.overall_range))return `${row.overall_range[0]}–${row.overall_range[1]}`
  return row?.overall ?? '—'
}
const statusLabel=computed(()=>{
  const tier=String(status.value.tier||'').trim()
  const score=Number(status.value.score)
  return tier ? `${tier}${Number.isFinite(score)?` · ${Math.round(score)}/100`:''}` : 'Proyecto en curso'
})
</script>

<template>
<BaseModal size="full" layer="entity" panel-class="football9394-team-modal" close-label="Cerrar ficha del club" :aria-label="`Ficha de ${team.name||'club'}`" @close="emit('close')">
  <template #header>
    <div class="team-profile-hero">
      <div class="team-profile-crest"><img :src="crestFor(team.source_id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"></div>
      <div class="team-profile-copy"><small>{{team.league?.country||'Mundo 93/94'}} · {{detail.season}}</small><h2>{{team.long_name||team.name}}</h2><p>{{team.league?.name||'Sin competición liguera'}}<template v-if="team.president"> · Presidente: {{team.president}}</template></p><div class="team-profile-tags"><span>{{statusLabel}}</span><span>{{detail.squad_size}} futbolistas</span><span v-if="team.members">{{Number(team.members).toLocaleString('es-ES')}} socios</span><span v-if="honourTotal">{{honourTotal}} títulos registrados</span></div></div>
      <div class="team-profile-manager"><small>ENTRENADOR</small><strong>{{manager.name||'Sin entrenador'}}</strong><span>{{manager.user_managed?'Tu proyecto actual':'Responsable del primer equipo'}}</span></div>
    </div>
  </template>

  <div class="team-profile-shell">
    <main class="team-profile-main">
      <section class="team-profile-summary-grid">
        <article><small>LIGA</small><strong>{{team.league?.name||'—'}}</strong><button v-if="team.league?.source_id" type="button" class="text-action" @click="emit('open-competition',{kind:'league',sourceId:team.league.source_id})">Ver competición →</button></article>
        <article><small>SITUACIÓN</small><strong v-if="standing">{{standing.position}}º · {{standing.points}} pts</strong><strong v-else>Sin tabla disponible</strong><span v-if="standing">{{standing.played}} PJ · {{standing.wins}}G {{standing.draws}}E {{standing.losses}}P</span></article>
        <article><small>IDENTIDAD</small><strong>{{team.initials||team.short_name||team.name}}</strong><span>Cantera nivel {{team.academy_level??'—'}} · estilo {{team.squad_building_style??'—'}}</span></article>
        <article><small>RIVALIDADES</small><button v-if="mainRival" type="button" class="text-action team-profile-rival" @click="emit('open-team',mainRival.id)">{{mainRival.name}} →</button><strong v-else>Sin rival principal registrado</strong><button v-if="regionalRival && regionalRival.id!==mainRival?.id" type="button" class="text-action team-profile-rival secondary" @click="emit('open-team',regionalRival.id)">Regional: {{regionalRival.name}} →</button></article>
      </section>

      <section class="football-panel team-profile-squad"><header class="section-heading"><div><small>PLANTILLA ACTUAL DE LA PARTIDA</small><h3>{{team.name}}</h3></div><span>{{squad.length}} jugadores</span></header>
        <UiDataTable v-if="squad.length" sticky aria-label="Plantilla del club"><table><thead><tr><th>#</th><th>Jugador</th><th>Posición</th><th>Nac.</th><th>Nivel conocido</th><th>Estado</th></tr></thead><tbody><tr v-for="player in squad" :key="player.id"><td>{{player.shirt_number??'—'}}</td><td><button type="button" class="player-link entity-link" @click="emit('open-player',player)">{{player.display_name}}</button></td><td>{{player.position||'—'}}</td><td>{{player.nationality||'—'}}</td><td><b>{{knownOverall(player)}}</b></td><td>{{player.status||'—'}}</td></tr></tbody></table></UiDataTable>
        <UiEmptyState v-else title="No hay futbolistas disponibles en esta ficha" detail="El club existe en el universo, pero la carrera no tiene ahora mismo jugadores sénior activos asociados." hint="La plantilla puede cambiar por contratos, fichajes, cesiones o transiciones de temporada." />
      </section>
    </main>

    <aside class="team-profile-rail">
      <article class="football-panel team-stadium-card"><div v-if="team.stadium_id" class="team-stadium-image"><img :src="stadiumFor(team.stadium_id)" alt="" @error="$event.currentTarget.style.display='none'"></div><small>ESTADIO</small><strong>{{venue?.name || (team.stadium_id?'Estadio histórico':'Sin estadio enlazado')}}</strong><span v-if="venue?.city_name">{{venue.city_name}}<template v-if="venue.capacity"> · {{Number(venue.capacity).toLocaleString('es-ES')}} espectadores</template></span><span>{{team.training_ground||'Instalaciones sin detalle adicional'}}</span></article>
      <article class="football-panel"><small>PALMARÉS HISTÓRICO</small><h3>{{honourTotal}} títulos</h3><dl class="team-honours-list"><div><dt>Ligas</dt><dd>{{honours.national_leagues??0}}</dd></div><div><dt>Copas</dt><dd>{{honours.national_cups??0}}</dd></div><div><dt>Europa I</dt><dd>{{honours.continental??0}}</dd></div><div><dt>Europa II</dt><dd>{{honours.continental_2??0}}</dd></div><div><dt>Europa III</dt><dd>{{honours.continental_3??0}}</dd></div></dl></article>
      <button v-if="detail.controlled" type="button" class="football-button primary full" @click="emit('open-controlled-club')">Abrir gestión del club</button>
    </aside>
  </div>
</BaseModal>
</template>
