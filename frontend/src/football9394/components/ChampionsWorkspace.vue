<script setup>
import { computed, ref, watch } from 'vue'
import PersonAvatar from '../../components/PersonAvatar.vue'

const props=defineProps({
  honours:{type:Array,default:()=>[]},
  seasonRecaps:{type:Array,default:()=>[]},
  crestFor:{type:Function,required:true},
})
const seasons=computed(()=>[...new Set((props.honours||[]).map(row=>row.season).filter(Boolean))].sort().reverse())
const selectedSeason=ref(seasons.value[0]||'')
const selectedHonour=ref(null)
const seasonHonours=computed(()=>props.honours.filter(row=>!selectedSeason.value||row.season===selectedSeason.value))
const managedRecap=computed(()=>props.seasonRecaps.find(row=>row.season===selectedSeason.value)||null)
watch(seasons,rows=>{if(rows.length&&!rows.includes(selectedSeason.value))selectedSeason.value=rows[0]},{immediate:true})
watch([selectedSeason,seasonHonours],()=>{selectedHonour.value=seasonHonours.value[0]||null},{immediate:true})
function kindLabel(kind){return kind==='league'?'Liga':kind==='tournament'?'Copa / torneo':'Competición'}
function managerPerson(row){const p=row?.champion_manager||{};return {...p,display_name:p.name,photo_url:p.id?`/historical9394/players/${Number(p.id)}.jpg`:null}}
function playerPerson(row){return {id:row.player_id,display_name:row.name,positions:[row.position],shirt_number:row.shirt_number,photo_url:`/historical9394/players/${Number(row.player_id)}.jpg`}}
</script>

<template>
<section class="champions-workspace screen-grid modern-r7">
  <article class="football-panel champions-main">
    <header class="workspace-heading champions-heading">
      <div><small>PALMARÉS DEL UNIVERSO</small><h2>Campeones</h2><p>Elige un título para recordar al campeón, su entrenador y la plantilla que lo consiguió.</p></div>
      <label class="champions-season-picker"><span>Temporada</span><select v-model="selectedSeason"><option v-for="season in seasons" :key="season" :value="season">{{season}}</option></select></label>
    </header>

    <div v-if="seasonHonours.length" class="champions-grid">
      <button v-for="honour in seasonHonours" :key="`${honour.season}-${honour.competition_kind}-${honour.source_id}`" type="button" class="champion-card" :class="{active:selectedHonour===honour}" @click="selectedHonour=honour">
        <span class="champion-crest"><img :src="crestFor(honour.team_id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"></span>
        <span class="champion-copy"><small>{{kindLabel(honour.competition_kind)}} · {{honour.season}}</small><strong>{{honour.competition_name}}</strong><span>{{honour.team_name}}</span></span>
        <b class="champion-mark">CAMPEÓN</b>
      </button>
    </div>
    <div v-else class="empty-football-state">Todavía no hay una temporada cerrada con campeones archivados.</div>

    <section v-if="selectedHonour" class="champion-story-card">
      <header class="champion-story-head">
        <div class="champion-story-title"><img :src="crestFor(selectedHonour.team_id)" alt=""><span><small>{{selectedHonour.competition_name}} · {{selectedHonour.season}}</small><h3>{{selectedHonour.team_name}}</h3><p>La foto fija del campeón en el momento de levantar el título.</p><div class="champion-context"><span v-if="selectedHonour.champion_points!=null"><small>Puntos</small><b>{{selectedHonour.champion_points}}</b></span><span v-if="selectedHonour.runner_up_team_name"><small>Subcampeón</small><b>{{selectedHonour.runner_up_team_name}}</b></span><span v-if="selectedHonour.margin_points!=null"><small>Margen</small><b>{{selectedHonour.margin_points}} pts</b></span></div></span></div>
        <b>CAMPEÓN</b>
      </header>
      <div class="champion-story-body">
        <article class="champion-manager-card">
          <small>ENTRENADOR CAMPEÓN</small>
          <PersonAvatar :person="managerPerson(selectedHonour)" :size="74" :height="92" decorative />
          <strong>{{selectedHonour.champion_manager?.name || 'Entrenador'}}</strong>
          <span>{{selectedHonour.champion_manager?.primary_tactic || 'Plan de juego histórico'}}<template v-if="selectedHonour.champion_manager?.game_tendency"> · {{selectedHonour.champion_manager.game_tendency}}</template></span>
        </article>
        <section class="champion-squad-block">
          <header><span><small>PLANTILLA CAMPEONA</small><strong>{{selectedHonour.champion_squad?.length || 0}} jugadores archivados</strong></span></header>
          <div v-if="selectedHonour.champion_squad?.length" class="champion-squad-grid">
            <article v-for="player in selectedHonour.champion_squad" :key="player.player_id" class="champion-player-card">
              <PersonAvatar :person="playerPerson(player)" :size="42" :height="55" :shirt-number="player.shirt_number" variant="player" decorative />
              <span><strong>{{player.name}}</strong><small>{{player.position}} · {{player.overall}}</small></span>
            </article>
          </div>
          <p v-else class="rail-empty">Los títulos archivados antes de esta mejora conservan campeón y competición; las nuevas temporadas guardarán también su plantilla y entrenador.</p>
        </section>
      </div>
    </section>
  </article>

  <aside class="side-stack">
    <article v-if="managedRecap" class="football-panel champions-managed-card">
      <small>TU TEMPORADA</small><h2>{{managedRecap.team_name}}</h2>
      <div class="champions-managed-position"><b>{{managedRecap.position??'—'}}º</b><span>{{managedRecap.league_name}}</span></div>
      <p>{{managedRecap.headline}}</p>
      <div v-if="managedRecap.titles?.length" class="managed-title-list"><span v-for="title in managedRecap.titles" :key="`${title.source_id}-${title.competition_kind}`">{{title.competition_name}}</span></div>
      <p v-else class="rail-empty">Sin títulos en esta temporada.</p>
    </article>
    <article class="football-panel champions-help">
      <small>HISTORIA VIVA</small><h2>El palmarés no se reinicia</h2><p>Cada temporada queda congelada con el equipo que fue campeón. Los fichajes o cambios de entrenador posteriores no reescriben esa fotografía.</p>
    </article>
  </aside>
</section>
</template>
