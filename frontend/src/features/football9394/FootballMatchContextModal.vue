<script setup>
import { computed } from 'vue'
import BaseModal from '../../components/BaseModal.vue'

const props=defineProps({match:{type:Object,required:true},controlledTeamId:{type:Number,default:0},crestFor:{type:Function,required:true},formatDate:{type:Function,required:true}})
const emit=defineEmits(['close','open-team','navigate'])
const homeId=computed(()=>Number(props.match?.home_team_id||0))
const awayId=computed(()=>Number(props.match?.away_team_id||0))
const mine=computed(()=>[homeId.value,awayId.value].includes(Number(props.controlledTeamId||0)))
const score=computed(()=>props.match?.played?`${props.match.home_goals??'—'}–${props.match.away_goals??'—'}`:'vs')
const stateLabel=computed(()=>props.match?.played?'Partido disputado':props.match?.postponed?'Partido aplazado':'Partido pendiente')
</script>

<template>
<BaseModal size="large" layer="entity" panel-class="football9394-match-context" close-label="Cerrar contexto del partido" :aria-label="`Partido ${match.home_team||''} ${match.away_team||''}`" @close="emit('close')">
 <template #header>
  <div class="match-context-heading"><div><small>{{match.competition_name||match.competition||'Partido'}} · {{formatDate(match.raw_date||match.date)}}</small><h2>{{stateLabel}}</h2><p v-if="match.matchday">Jornada {{match.matchday}}<template v-if="match.fixture_type==='friendly'"> · Amistoso</template></p></div><span :class="['match-context-state',{played:match.played}]">{{match.status||stateLabel}}</span></div>
 </template>
 <div class="match-context-body">
  <div class="match-context-scoreboard">
   <button type="button" class="match-context-team" @click="emit('open-team',homeId)"><img :src="crestFor(homeId)" alt="" @error="$event.currentTarget.style.visibility='hidden'"><strong>{{match.home_team||'Local'}}</strong><span>Ver club →</span></button>
   <div class="match-context-score"><small>{{match.venue==='Casa'?'Tu estadio':match.venue==='Fuera'?'Estadio rival':'Sede por confirmar'}}</small><b>{{score}}</b><span>{{match.played?'Resultado final':'Próximo compromiso'}}</span></div>
   <button type="button" class="match-context-team" @click="emit('open-team',awayId)"><img :src="crestFor(awayId)" alt="" @error="$event.currentTarget.style.visibility='hidden'"><strong>{{match.away_team||'Visitante'}}</strong><span>Ver club →</span></button>
  </div>
  <div class="match-context-explanation">
   <article><small>QUÉ ESTÁ PASANDO</small><strong v-if="match.played">El resultado ya forma parte de la carrera.</strong><strong v-else-if="match.postponed">El encuentro no se jugará en su fecha original.</strong><strong v-else>Este encuentro está pendiente en tu agenda.</strong><p v-if="match.played">Clasificación, moral, sanciones, lesiones y noticias posteriores ya deben reflejar sus consecuencias.</p><p v-else-if="match.postponed">El calendario conservará el contexto hasta que exista una nueva fecha válida.</p><p v-else>La convocatoria, la disponibilidad y el plan táctico deben estar preparados antes de llegar al directo.</p></article>
   <article><small>SIGUIENTE PASO</small><strong v-if="!match.played && mine">Preparar el partido</strong><strong v-else-if="match.played">Revisar las consecuencias</strong><strong v-else>Explorar protagonistas</strong><p v-if="!match.played && mine">Puedes ir a Tácticas sin perder este partido del historial: Atrás devolverá este contexto.</p><p v-else-if="match.played">La ficha sirve de puente hacia los dos clubes; el detalle estadístico avanzado permanece en el postpartido cuando existe acta.</p><p v-else>Abre cualquiera de los dos clubes para seguir el hilo sin memorizar rutas.</p></article>
  </div>
  <div class="match-context-actions"><button v-if="!match.played && mine" type="button" class="football-button primary" @click="emit('navigate','tactics')">Abrir Tácticas</button><button v-if="match.played && mine" type="button" class="football-button" @click="emit('navigate','home')">Volver a Inicio</button></div>
 </div>
</BaseModal>
</template>
