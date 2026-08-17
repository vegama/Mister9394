<script setup>
defineProps({
  selectedCompetition:{type:String,default:''}, competitions:{type:Array,default:()=>[]}, detail:{type:Object,default:null},
  viewMode:{type:String,default:'table'}, standings:{type:Array,default:()=>[]}, recentResults:{type:Array,default:()=>[]},
  calendarRows:{type:Array,default:()=>[]}, honours:{type:Array,default:()=>[]}, controlledTeamId:{type:Number,default:0},
  season:{type:String,default:'1993-94'}, crestFor:{type:Function,required:true}, formatDate:{type:Function,required:true},
  eventLabel:{type:Function,required:true},
})
const emit=defineEmits(['update:selectedCompetition','update:viewMode'])
const tabs=[['table','Clasificación'],['results','Resultados'],['calendar','Calendario'],['honours','Palmarés']]
</script>
<template>
<section class="screen-grid competition-screen modern-r7">
  <article class="football-panel competition-main">
    <header class="workspace-heading">
      <div><small>Temporada {{season}}</small><h2>Competiciones</h2><p>Clasificación, calendario, eliminatorias y memoria de la partida.</p></div>
      <select class="workspace-select" :value="selectedCompetition" @change="emit('update:selectedCompetition',$event.target.value)">
        <option v-for="c in competitions" :key="`${c.kind}:${c.source_id}`" :value="`${c.kind}:${c.source_id}`">{{c.country?`${c.country} · `:''}}{{c.name}}</option>
      </select>
    </header>
    <div class="competition-hero-strip">
      <div><small>{{detail?.country||'Internacional'}}</small><strong>{{detail?.name||'Competición'}}</strong><span>{{eventLabel(detail)}}</span></div>
      <div v-if="detail?.champion_team"><small>Campeón</small><b>{{detail.champion_team}}</b></div>
      <div v-if="detail?.rules?.foreigners"><small>Extranjeros</small><b>XI {{detail.rules.foreigners.max_starting??'∞'}} · convocatoria {{detail.rules.foreigners.max_squad??'∞'}}</b></div>
    </div>
    <nav class="segmented-tabs">
      <button v-for="tab in tabs" :key="tab[0]" type="button" :class="{active:viewMode===tab[0]}" @click="emit('update:viewMode',tab[0])">{{tab[1]}}</button>
    </nav>
    <div class="competition-content">
      <div v-if="viewMode==='table'&&standings.length" class="table-scroll"><table><thead><tr><th>Pos</th><th>Equipo</th><th>PJ</th><th>PG</th><th>PE</th><th>PP</th><th>GF</th><th>GC</th><th>DG</th><th>Pts</th></tr></thead><tbody><tr v-for="r in standings" :key="r.team_id" :class="{controlled:r.team_id===controlledTeamId}"><td><b>{{r.position}}º</b></td><td><strong>{{r.team_name}}</strong></td><td>{{r.played}}</td><td class="good-cell">{{r.wins}}</td><td class="warn-cell">{{r.draws}}</td><td class="bad-cell">{{r.losses}}</td><td>{{r.goals_for}}</td><td>{{r.goals_against}}</td><td>{{r.goal_difference>0?'+':''}}{{r.goal_difference}}</td><td class="points">{{r.points}}</td></tr></tbody></table></div>
      <div v-else-if="viewMode==='table'" class="empty-football-state">Esta competición no utiliza una tabla única. Consulta Resultados.</div>
      <div v-else-if="viewMode==='results'" class="fixture-stream"><article v-for="(r,index) in recentResults" :key="`${r.home_team_id}-${r.away_team_id}-${index}`" class="fixture-card finished"><small>{{r.date?formatDate(r.date):(r.stage||`Jornada ${r.round||r.matchday||'—'}`)}}</small><strong>{{r.home_team}}</strong><b>{{r.home_goals}}–{{r.away_goals}}</b><strong>{{r.away_team}}</strong></article><div v-if="!recentResults.length" class="empty-football-state">Todavía no hay resultados.</div></div>
      <div v-else-if="viewMode==='calendar'" class="fixture-stream"><article v-for="(r,index) in calendarRows" :key="`${r.home_team_id}-${r.away_team_id}-${index}`" class="fixture-card"><small>{{formatDate(r.date)}}</small><strong>{{r.home_team}}</strong><b>vs</b><strong>{{r.away_team}}</strong></article><div v-if="!calendarRows.length" class="empty-football-state">No hay partidos pendientes.</div></div>
      <div v-else class="honours-modern"><article v-for="h in honours" :key="`${h.season}-${h.team_id}`"><b>{{h.season}}</b><strong>{{h.team_name}}</strong><span>{{h.honour}}</span></article><div v-if="!honours.length" class="empty-football-state">El palmarés crecerá al cerrar la primera temporada.</div></div>
    </div>
  </article>
  <aside class="side-stack">
    <article class="football-panel"><h2>Participantes <small>{{detail?.participants?.length||0}}</small></h2><div class="participant-list modern-participants"><span v-for="p in (detail?.participants||[]).slice(0,48)" :key="p.team_id" :class="{controlled:p.team_id===controlledTeamId}"><img :src="crestFor(p.team_id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"><b>{{p.team_name}}</b></span></div></article>
    <article v-if="detail?.ties?.length" class="football-panel"><h2>Eliminatorias</h2><div class="tie-stack"><div v-for="(tie,index) in detail.ties" :key="index" class="tie-row"><strong>{{tie.team_a_name}}</strong><span>vs</span><strong>{{tie.team_b_name}}</strong><small>{{tie.legs?.length||0}} partido(s)</small></div></div></article>
    <article class="football-panel context-card"><h2>Mundo 93/94</h2><strong>{{competitions.length}} competiciones activas</strong><p>Los clubes necesarios para copas y mercado permanecen en el universo aunque no sean elegibles al crear carrera.</p></article>
  </aside>
</section>
</template>