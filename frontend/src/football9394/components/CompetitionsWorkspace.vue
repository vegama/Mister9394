<script setup>
import UiPageHeader from '../../components/ui/UiPageHeader.vue'
import UiEmptyState from '../../components/ui/UiEmptyState.vue'
import UiDataTable from '../../components/ui/UiDataTable.vue'
defineProps({
  selectedCompetition:{type:String,default:''}, competitions:{type:Array,default:()=>[]}, detail:{type:Object,default:null},
  viewMode:{type:String,default:'table'}, standings:{type:Array,default:()=>[]}, recentResults:{type:Array,default:()=>[]},
  calendarRows:{type:Array,default:()=>[]}, honours:{type:Array,default:()=>[]}, controlledTeamId:{type:Number,default:0},
  season:{type:String,default:'1993-94'}, crestFor:{type:Function,required:true}, formatDate:{type:Function,required:true},
  eventLabel:{type:Function,required:true},
})
const emit=defineEmits(['update:selectedCompetition','update:viewMode','open-team'])
const tabs=[['table','Clasificación'],['results','Resultados'],['calendar','Calendario'],['honours','Palmarés']]
</script>
<template>
<section class="screen-grid competition-screen modern-r7">
  <article class="football-panel competition-main">
    <UiPageHeader :eyebrow="`TEMPORADA ${season}`" title="Competiciones" description="Clasificación, resultados, próximos partidos y palmarés dentro de un mismo contexto competitivo." :status="detail?.name || `${competitions.length} activas`">
      <template #actions><label class="workspace-switcher"><span>Competición</span><select class="workspace-select" :value="selectedCompetition" @change="emit('update:selectedCompetition',$event.target.value)"><option v-for="c in competitions" :key="`${c.kind}:${c.source_id}`" :value="`${c.kind}:${c.source_id}`">{{c.country?`${c.country} · `:''}}{{c.name}}</option></select></label></template>
    </UiPageHeader>
    <div class="competition-hero-strip">
      <div><small>{{detail?.country||'Internacional'}}</small><strong>{{detail?.name||'Competición'}}</strong><span>{{eventLabel(detail)}}</span></div>
      <div v-if="detail?.champion_team"><small>Campeón</small><b>{{detail.champion_team}}</b></div>
      <div v-if="detail?.rules?.foreigners"><small>Extranjeros</small><b>XI {{detail.rules.foreigners.max_starting??'∞'}} · convocatoria {{detail.rules.foreigners.max_squad??'∞'}}</b></div>
    </div>
    <nav class="segmented-tabs">
      <button v-for="tab in tabs" :key="tab[0]" type="button" :class="{active:viewMode===tab[0]}" @click="emit('update:viewMode',tab[0])">{{tab[1]}}</button>
    </nav>
    <div class="competition-content">
      <UiDataTable v-if="viewMode==='table'&&standings.length" class="table-scroll" aria-label="Clasificación de la competición" sticky><table><thead><tr><th>Pos</th><th>Equipo</th><th>PJ</th><th>PG</th><th>PE</th><th>PP</th><th>GF</th><th>GC</th><th>DG</th><th>Pts</th></tr></thead><tbody><tr v-for="r in standings" :key="r.team_id" :class="{controlled:r.team_id===controlledTeamId}"><td><b>{{r.position}}º</b></td><td><button type="button" class="entity-link" @click="emit('open-team',r.team_id)">{{r.team_name}}</button></td><td>{{r.played}}</td><td class="good-cell">{{r.wins}}</td><td class="warn-cell">{{r.draws}}</td><td class="bad-cell">{{r.losses}}</td><td>{{r.goals_for}}</td><td>{{r.goals_against}}</td><td>{{r.goal_difference>0?'+':''}}{{r.goal_difference}}</td><td class="points">{{r.points}}</td></tr></tbody></table></UiDataTable>
      <UiEmptyState v-else-if="viewMode==='table'" title="Esta competición no utiliza una tabla única" detail="Su formato se resuelve por eliminatorias, grupos u otra estructura sin clasificación general única." hint="Consulta Resultados para seguir el estado real del torneo." />
      <div v-else-if="viewMode==='results'" class="fixture-stream"><article v-for="(r,index) in recentResults" :key="`${r.home_team_id}-${r.away_team_id}-${index}`" class="fixture-card finished"><small>{{r.date?formatDate(r.date):(r.stage||`Jornada ${r.round||r.matchday||'—'}`)}}</small><button type="button" class="fixture-team-link" @click="emit('open-team',r.home_team_id)">{{r.home_team}}</button><b>{{r.home_goals}}–{{r.away_goals}}</b><button type="button" class="fixture-team-link" @click="emit('open-team',r.away_team_id)">{{r.away_team}}</button></article><UiEmptyState v-if="!recentResults.length" title="Todavía no hay resultados" detail="La competición aún no ha registrado partidos resueltos en esta partida." hint="Los resultados aparecerán aquí en cuanto se dispute la primera jornada o eliminatoria." /></div>
      <div v-else-if="viewMode==='calendar'" class="fixture-stream"><article v-for="(r,index) in calendarRows" :key="`${r.home_team_id}-${r.away_team_id}-${index}`" class="fixture-card"><small>{{formatDate(r.date)}}</small><button type="button" class="fixture-team-link" @click="emit('open-team',r.home_team_id)">{{r.home_team}}</button><b>vs</b><button type="button" class="fixture-team-link" @click="emit('open-team',r.away_team_id)">{{r.away_team}}</button></article><UiEmptyState v-if="!calendarRows.length" title="No hay partidos pendientes" detail="No existe ahora mismo un emparejamiento futuro cargado para esta competición." hint="Puede ser normal entre fases; el calendario se actualizará cuando el torneo determine los siguientes partidos." /></div>
      <div v-else class="honours-modern"><article v-for="h in honours" :key="`${h.season}-${h.team_id}`"><b>{{h.season}}</b><strong>{{h.team_name}}</strong><span>{{h.honour}}</span></article><UiEmptyState v-if="!honours.length" title="El palmarés todavía está vacío" detail="El palmarés crecerá al cerrar la primera temporada y conservará los campeones de esta partida." hint="Los títulos quedarán disponibles como memoria histórica de la carrera." /></div>
    </div>
  </article>
  <aside class="side-stack">
    <article class="football-panel"><h2>Participantes <small>{{detail?.participants?.length||0}}</small></h2><div class="participant-list modern-participants"><button v-for="p in (detail?.participants||[]).slice(0,48)" :key="p.team_id" type="button" :class="{controlled:p.team_id===controlledTeamId}" @click="emit('open-team',p.team_id)"><img :src="crestFor(p.team_id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"><b>{{p.team_name}}</b></button></div></article>
    <article v-if="detail?.ties?.length" class="football-panel"><h2>Eliminatorias</h2><div class="tie-stack"><div v-for="(tie,index) in detail.ties" :key="index" class="tie-row"><strong>{{tie.team_a_name}}</strong><span>vs</span><strong>{{tie.team_b_name}}</strong><small>{{tie.legs?.length||0}} partido(s)</small></div></div></article>
    <article class="football-panel context-card"><h2>Mundo 93/94</h2><strong>{{competitions.length}} competiciones activas</strong><p>Los clubes necesarios para copas y mercado permanecen en el universo aunque no sean elegibles al crear carrera.</p></article>
  </aside>
</section>
</template>