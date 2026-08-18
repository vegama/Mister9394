<script setup>
import { computed, ref } from 'vue'

const props=defineProps({
  careerOptions:{type:Array,default:()=>[]}, selectedLeagueId:{type:[Number,String],default:null},
  selectedTeamId:{type:[Number,String],default:null}, loading:{type:Boolean,default:false},
  currentCareerId:{type:String,default:''}, error:{type:String,default:''}, agePolicy:{type:String,default:'frozen_attributes_dynamic'},
})
const emit=defineEmits(['update:selectedLeagueId','update:selectedTeamId','update:agePolicy','start','back'])
const leagueQuery=ref('')
const clubQuery=ref('')
const league=computed(()=>props.careerOptions.find(row=>Number(row.source_id)===Number(props.selectedLeagueId))||null)
const teams=computed(()=>league.value?.teams||[])
const team=computed(()=>teams.value.find(row=>Number(row.source_id)===Number(props.selectedTeamId))||null)
const filteredLeagues=computed(()=>{
  const q=leagueQuery.value.trim().toLowerCase()
  return q?props.careerOptions.filter(r=>`${r.country} ${r.name}`.toLowerCase().includes(q)):props.careerOptions
})
const filteredTeams=computed(()=>{
  const q=clubQuery.value.trim().toLowerCase()
  return q?teams.value.filter(r=>`${r.long_name||r.name}`.toLowerCase().includes(q)):teams.value
})
const clubCrest=id=>id?`/historical9394/clubs/${Number(id)}.gif`:null
const stadiumPhoto=id=>id?`/historical9394/stadiums/${Number(id)}.jpg`:null
const playerPhoto=id=>id?`/historical9394/players/${Number(id)}.jpg`:null
const money=value=>value==null?'—':`${Number(value).toLocaleString('es-ES')} ptas.`
function chooseLeague(id){clubQuery.value='';emit('update:selectedLeagueId',Number(id))}
</script>

<template>
<section class="career-setup redesigned-career-setup">
  <div class="career-setup-shell">
    <header class="career-setup-header">
      <div class="setup-logo"><span class="brand-mark" aria-hidden="true"><span></span><i></i></span><div><strong>Míster 93/94</strong><small>Nueva carrera</small></div></div>
      <div><h1>¿Dónde empieza tu historia?</h1><p>Elige una competición y un club. El mundo conserva las plantillas, reglas y formatos de 1993-94; la interfaz no necesita quedarse en 1993.</p></div>
      <button v-if="currentCareerId" type="button" class="football-button" @click="emit('back')">Volver a mi carrera</button>
    </header>

    <div class="career-browser">
      <section class="career-browser-column leagues">
        <div class="browser-column-head"><span><small>Paso 1</small><strong>Competición</strong></span><input v-model="leagueQuery" type="search" placeholder="Buscar país o liga…" aria-label="Buscar competición"></div>
        <div class="league-card-list">
          <button v-for="item in filteredLeagues" :key="item.source_id" type="button" class="league-choice" :class="{active:Number(selectedLeagueId)===Number(item.source_id)}" @click="chooseLeague(item.source_id)">
            <span><small>{{item.country}}</small><strong>{{item.name}}</strong></span><b>{{item.team_count}}</b>
          </button>
        </div>
      </section>

      <section class="career-browser-column clubs">
        <div class="browser-column-head"><span><small>Paso 2</small><strong>Club</strong></span><input v-model="clubQuery" type="search" placeholder="Buscar club…" aria-label="Buscar club"></div>
        <div class="club-choice-grid">
          <button v-for="item in filteredTeams" :key="item.source_id" type="button" class="club-choice" :class="{active:Number(selectedTeamId)===Number(item.source_id)}" @click="emit('update:selectedTeamId',Number(item.source_id))">
            <span class="club-choice-crest"><img :src="clubCrest(item.source_id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"></span>
            <span><strong>{{item.name}}</strong><small>{{item.squad_size}} jugadores · XI {{item.average_top_11}}</small></span>
          </button>
          <div v-if="!filteredTeams.length" class="setup-empty">No hay clubes con ese filtro.</div>
        </div>
      </section>

      <aside class="career-club-preview">
        <template v-if="team">
          <div class="setup-stadium-cover" :style="team.stadium_id?{backgroundImage:`linear-gradient(0deg,rgba(10,22,17,.82),rgba(10,22,17,.25)),url(${stadiumPhoto(team.stadium_id)})`}:{}">
            <img class="setup-crest" :src="clubCrest(team.source_id)" alt="">
            <div><small>{{league?.country}} · {{league?.name}}</small><h2>{{team.long_name||team.name}}</h2></div>
          </div>
          <div class="setup-club-facts"><span><small>Plantilla</small><b>{{team.squad_size}}</b></span><span><small>Nivel XI</small><b>{{team.average_top_11}}</b></span><span><small>Socios</small><b>{{team.members??'—'}}</b></span><span><small>Presupuesto fichajes</small><b>{{money(team.budget)}}</b></span><span><small>Deuda</small><b>{{money(team.debt)}}</b></span><span><small>Formato</small><b>{{league?.rounds||'—'}} partidos</b></span></div>
          <div class="setup-top-players"><h3>Referentes</h3><span v-for="p in team.top_players" :key="p.id"><span class="setup-player-photo"><img :src="playerPhoto(p.id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"></span><b>{{p.name}}</b><small>{{p.position}} · {{p.overall}}</small></span></div>
          <div class="setup-era-note"><b>Temporada 1993-94 · pesetas</b><span>Reglas, mercado y competiciones históricas activas. Las cifras económicas jugables se muestran en ptas.</span></div>
          <div class="setup-age-policy">
            <h3>Evolución de jugadores</h3>
            <button type="button" class="age-policy-choice" :class="{active:agePolicy==='frozen_attributes_dynamic'}" @click="emit('update:agePolicy','frozen_attributes_dynamic')">
              <strong>Reparto eterno</strong><span>La edad queda congelada. No hay retiradas ni cantera/newgens, pero los atributos evolucionan por fútbol, entrenador, forma y lesiones.</span>
            </button>
            <button type="button" class="age-policy-choice" :class="{active:agePolicy==='dynamic_from_birth_date'}" @click="emit('update:agePolicy','dynamic_from_birth_date')">
              <strong>Carrera cronológica</strong><span>Envejecimiento, retirada y reposición de cantera activados.</span>
            </button>
          </div>
          <button type="button" class="football-button primary start-career" :disabled="loading||!selectedTeamId" @click="emit('start')">{{loading?'Creando partida…':'Empezar con '+team.name}}</button>
        </template>
        <div v-else class="setup-empty preview">Selecciona un club para ver su punto de partida.</div>
        <div v-if="error" class="data-error">{{error}}</div>
      </aside>
    </div>
  </div>
</section>
</template>
