<script setup>
import { computed } from 'vue'

const props=defineProps({recap:{type:Object,required:true},crestFor:{type:Function,required:true}})
defineEmits(['close','open-champions','open-history','open-workspace'])
const awards=computed(()=>{
  const row=props.recap?.league_awards||{}
  return [
    ['Mejor jugador',row.best_player,'average_rating','nota'],
    ['Máximo goleador',row.top_scorer,'goals','goles'],
    ['Máximo asistente',row.top_assister,'assists','asist.'],
    ['Mejor portero',row.best_goalkeeper,'average_rating','nota'],
  ].filter(item=>item[1])
})
const majorChampions=computed(()=>[...(props.recap?.champions||[])].slice(0,8))
const teamOfSeason=computed(()=>props.recap?.league_awards?.team_of_season||[])
const leagueChampion=computed(()=>props.recap?.champions?.find(row=>row.competition_kind==='league'&&Number(row.source_id)===Number(props.recap?.league_id))||null)
const summer=computed(()=>props.recap?.next_season_briefing||null)
const milestones=computed(()=>[...(props.recap?.milestones||[])].sort((a,b)=>Number(b.importance||0)-Number(a.importance||0)).slice(0,6))
const movementLabel=computed(()=>props.recap?.movement?.reason==='promotion'?'ASCENSO':props.recap?.movement?.reason==='relegation'?'DESCENSO':null)
function photo(id){return id?`/historical9394/players/${Number(id)}.jpg`:''}
</script>

<template>
<div class="season-end-backdrop" role="dialog" aria-modal="true" aria-label="Fin de temporada">
  <section class="season-end-screen">
    <header class="season-end-hero">
      <div class="season-end-club"><img :src="crestFor(recap.team_id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"></div>
      <div><small>FIN DE TEMPORADA · {{recap.season}}</small><h1>{{recap.headline}}</h1><p>{{recap.team_name}} · {{recap.league_name}}</p><b v-if="movementLabel" class="season-end-movement">{{movementLabel}}</b></div>
      <button class="season-end-close" type="button" aria-label="Cerrar" @click="$emit('close')">×</button>
    </header>

    <div class="season-end-summary">
      <span><small>Posición</small><b>{{recap.position??'—'}}º</b></span>
      <span><small>Puntos</small><b>{{recap.points??'—'}}</b></span>
      <span><small>Balance</small><b>{{recap.wins??0}}V · {{recap.draws??0}}E · {{recap.losses??0}}D</b></span>
      <span><small>Goles</small><b>{{recap.goals_for??0}}–{{recap.goals_against??0}}</b></span>
    </div>

    <section v-if="milestones.length" class="season-end-section season-end-milestones">
      <header><small>MOMENTOS DE LA TEMPORADA</small><h2>Lo que quedará en la memoria</h2></header>
      <div class="season-end-milestones-grid"><article v-for="item in milestones" :key="item.key"><small>{{item.kind.replaceAll('_',' ').toUpperCase()}}</small><strong>{{item.title}}</strong><span>{{item.summary}}</span></article></div>
    </section>

    <section v-if="awards.length" class="season-end-section">
      <header><small>PREMIOS DE LIGA</small><h2>Los protagonistas de {{recap.season}}</h2></header>
      <div class="season-awards-grid">
        <article v-for="award in awards" :key="award[0]" class="season-award-card">
          <img :src="photo(award[1].player_id)" alt="" @error="$event.currentTarget.style.display='none'">
          <div><small>{{award[0]}}</small><strong>{{award[1].name}}</strong><span>{{award[1].team_name}}</span><b>{{award[1][award[2]]}} {{award[3]}}</b></div>
        </article>
      </div>
    </section>

    <section v-if="teamOfSeason.length" class="season-end-section season-end-xi">
      <header><small>XI DE LA TEMPORADA</small><h2>El once que marcó la liga</h2></header>
      <div class="season-end-xi-grid">
        <article v-for="player in teamOfSeason" :key="player.player_id">
          <img :src="photo(player.player_id)" alt="" @error="$event.currentTarget.style.display='none'">
          <span><strong>{{player.name}}</strong><small>{{player.position}} · {{player.team_name}}</small><b>{{player.average_rating}} nota</b></span>
        </article>
      </div>
      <aside v-if="leagueChampion?.champion_manager" class="season-end-coach">
        <img v-if="leagueChampion.champion_manager.id" :src="photo(leagueChampion.champion_manager.id)" alt="" @error="$event.currentTarget.style.display='none'">
        <span><small>ENTRENADOR CAMPEÓN</small><strong>{{leagueChampion.champion_manager.name}}</strong><em>{{leagueChampion.team_name}}</em></span>
      </aside>
    </section>

    <section v-if="summer" class="season-end-section season-transition-briefing">
      <header><small>NUEVA TEMPORADA · {{summer.season}}</small><h2>{{summer.headline}}</h2><p>{{summer.summary}}</p></header>
      <div class="season-transition-checklist">
        <button v-for="item in summer.checklist" :key="item.key" type="button" :class="item.status" @click="$emit('open-workspace',item.action)">
          <span><small>{{item.label}}</small><strong>{{item.detail}}</strong></span><b>{{item.status==='ready'||item.status==='done'?'✓':'→'}}</b>
        </button>
      </div>
      <div v-if="summer.priorities?.length" class="season-transition-priorities">
        <small>LO QUE REQUIERE TU ATENCIÓN</small>
        <button v-for="item in summer.priorities" :key="`${item.kind}-${item.label}`" type="button" :class="item.priority" @click="$emit('open-workspace',item.action)">
          <span><strong>{{item.label}}</strong><em>{{item.detail}}</em></span><b>→</b>
        </button>
      </div>
    </section>

    <section class="season-end-bottom">
      <div class="season-end-section season-end-titles">
        <header><small>CAMPEONES</small><h2>La temporada que queda para la historia</h2></header>
        <div class="season-end-champions">
          <article v-for="honour in majorChampions" :key="`${honour.competition_kind}-${honour.source_id}`"><img :src="crestFor(honour.team_id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"><div><small>{{honour.competition_name}}</small><strong>{{honour.team_name}}</strong></div></article>
        </div>
      </div>
      <div class="season-end-section season-end-board">
        <header><small>CONSEJO</small><h2>{{recap.board?.label||'Temporada evaluada'}}</h2></header>
        <div class="season-end-board-score"><b>{{recap.board?.score??'—'}}</b><span>/ 100</span></div>
        <p>{{recap.qualified_for?.length?`Clasificado para ${recap.qualified_for.join(', ')}.`:'Sin clasificación europea para la próxima temporada.'}}</p>
      </div>
    </section>

    <footer class="season-end-actions">
      <button class="secondary-action" type="button" @click="$emit('open-champions')">Ver todos los campeones</button>
      <button class="secondary-action" type="button" @click="$emit('open-history')">Abrir historia</button>
      <button class="primary-action" type="button" @click="$emit('close')">Continuar a la nueva temporada</button>
    </footer>
  </section>
</div>
</template>
