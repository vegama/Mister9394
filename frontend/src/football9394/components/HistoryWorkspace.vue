<script setup>
import { computed } from 'vue'
const props=defineProps({latestRecap:{type:Object,default:null},historyState:{type:Object,default:()=>({})},latestAiAudit:{type:Object,default:null},careerRecords:{type:Object,default:()=>({})},storylineArchive:{type:Array,default:()=>[]},managerCareer:{type:Object,default:()=>({reputation:50,tenures:[],current_tenure:{}})}})
const dossiers=computed(()=>[...(props.historyState.season_dossiers||[])].reverse())
const timeline=computed(()=>dossiers.value.length?dossiers.value:[...(props.historyState.season_recaps||[])].reverse().map(recap=>({season:recap.season,managed_recap:recap,manager_segments:[]})))
const milestones=computed(()=>[...(props.historyState.career_milestones||[])].sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))||Number(b.importance||0)-Number(a.importance||0)))
const majorMilestones=computed(()=>milestones.value.filter(row=>Number(row.importance||0)>=7).slice(0,14))
function dossierHeadline(row){return row.managed_recap?.headline||`${row.season}: temporada archivada`}
function dossierMeta(row){
 const segs=row.manager_segments||[]
 if(segs.length)return segs.map(s=>`${s.team_name}${s.final_table_row?.position?` · ${s.final_table_row.position}º`:''}`).join(' → ')
 const recap=row.managed_recap||{}
 return `${recap.league_name||'Competición'} · ${recap.position??'—'}º`
}

function seasonScore(row){
 const recap=row?.managed_recap||row||{}; const titles=(recap.titles||[]).length; const pos=Number(recap.position||99); const movement=recap.movement?.reason
 return titles*100 + (movement==='promotion'?70:movement==='relegation'?-70:0) + Math.max(0,30-pos)
}
const completedSeasons=computed(()=>timeline.value.filter(row=>row?.managed_recap||row?.position))
const bestSeason=computed(()=>[...completedSeasons.value].sort((a,b)=>seasonScore(b)-seasonScore(a))[0]||null)
const worstSeason=computed(()=>[...completedSeasons.value].sort((a,b)=>seasonScore(a)-seasonScore(b))[0]||null)
function tenureReason(reason){return ({dismissed:'Destitución',resigned:'Dimisión',left_for_job:'Cambio de proyecto',season_end:'Fin de temporada'}[reason]||reason||'Etapa cerrada')}
</script>
<template>
<section class="screen-grid history-screen modern-r7">
  <article class="football-panel history-main"><header class="workspace-heading"><div><small>Archivo de carrera</small><h2>Historia</h2><p>Temporadas, títulos y protagonistas permanecen aunque el universo siga cambiando.</p></div></header>
    <div v-if="latestRecap" class="latest-recap modern-recap"><small>Última temporada cerrada</small><h3>{{latestRecap.headline}}</h3><div class="recap-grid"><span><small>Liga</small><b>{{latestRecap.position??'—'}}º · {{latestRecap.points??'—'}} pts</b></span><span><small>Balance</small><b>{{latestRecap.wins??0}}V {{latestRecap.draws??0}}E {{latestRecap.losses??0}}D</b></span><span><small>Europa siguiente</small><b>{{latestRecap.qualified_for?.join(', ')||'No'}}</b></span><span><small>Consejo</small><b>{{latestRecap.board?.label||'—'}} · {{latestRecap.board?.score??'—'}}</b></span></div><div class="recap-protagonists"><p v-if="latestRecap.top_scorer"><small>Máximo goleador</small><strong>{{latestRecap.top_scorer.name}}</strong><span>{{latestRecap.top_scorer.goals}} goles</span></p><p v-if="latestRecap.player_of_season"><small>Jugador de la temporada</small><strong>{{latestRecap.player_of_season.name}}</strong><span>{{latestRecap.player_of_season.average_rating}}</span></p></div></div>
    <div class="season-timeline modern-timeline"><article v-for="row in timeline" :key="row.season"><b>{{row.season}}</b><div><strong>{{dossierHeadline(row)}}</strong><span>{{dossierMeta(row)}}</span><small v-if="row.manager_segments?.length>1">{{row.manager_segments.length}} proyectos dirigidos en la misma temporada</small><small v-else-if="row.managed_recap?.titles?.length">{{row.managed_recap.titles.map(t=>t.competition_name).join(' · ')}}</small><small v-if="row.managed_recap?.player_of_season">Figura: {{row.managed_recap.player_of_season.name}} · {{row.managed_recap.player_of_season.average_rating}}</small><small v-if="row.managed_recap?.top_scorer">Goleador: {{row.managed_recap.top_scorer.name}} · {{row.managed_recap.top_scorer.goals}} goles</small></div></article><div v-if="!timeline.length" class="empty-football-state">Tu primera temporada todavía está en marcha.</div></div>
    <section class="career-milestone-archive">
      <header><div><small>HITOS CANÓNICOS</small><h3>Los capítulos que definen tu carrera</h3></div></header>
      <article v-for="item in majorMilestones" :key="item.key" :class="`milestone-${item.kind}`"><time>{{item.date}}</time><div><small>{{item.season}} · importancia {{item.importance}}/10</small><strong>{{item.title}}</strong><p>{{item.summary}}</p></div></article>
      <div v-if="!majorMilestones.length" class="empty-football-state">Los grandes hitos aparecerán cuando la carrera produzca títulos, ascensos, descensos, rivalidades o cambios de proyecto.</div>
    </section>
    <section class="career-story-archive">
      <header><div><small>MEMORIA DE LA PARTIDA</small><h3>Historias que ya dejaron huella</h3></div></header>
      <article v-for="story in [...storylineArchive].reverse().slice(0,6)" :key="story.key">
        <span>{{story.resolved_on || story.updated_on || story.started_on}}</span><div><strong>{{story.title}}</strong><p>{{story.summary}}</p></div>
      </article>
      <div v-if="!storylineArchive.length" class="empty-football-state">Las primeras historias de tu etapa todavía se están escribiendo.</div>
    </section>
  </article>
  <aside class="side-stack"><article class="football-panel manager-career-path"><small>TRAYECTORIA DEL MÁNAGER</small><h2>Tu carrera</h2><div class="manager-reputation-history"><b>{{managerCareer.reputation??50}}</b><span>reputación actual</span></div><div class="manager-tenure-list"><article v-for="tenure in [...(managerCareer.tenures||[])].reverse().slice(0,5)" :key="`${tenure.team_id}-${tenure.started_on}`"><strong>{{tenure.team_name||`Club ${tenure.team_id}`}}</strong><span>{{tenure.started_on}} → {{tenure.ended_on}}</span><small>{{tenureReason(tenure.reason)}}</small></article><article v-if="managerCareer.current_tenure?.team_id" class="current"><strong>{{managerCareer.current_tenure.team_name||`Club ${managerCareer.current_tenure.team_id}`}}</strong><span>Desde {{managerCareer.current_tenure.started_on}}</span><small>Etapa actual</small></article></div></article><article v-if="bestSeason" class="football-panel career-season-extremes"><small>LECTURA DE CARRERA</small><h2>Mejor y peor temporada</h2><div><span><small>MEJOR</small><strong>{{bestSeason.season}}</strong><em>{{dossierHeadline(bestSeason)}}</em></span><span v-if="worstSeason"><small>PEOR</small><strong>{{worstSeason.season}}</strong><em>{{dossierHeadline(worstSeason)}}</em></span></div></article><article class="football-panel career-records-history"><small>TU ETAPA</small><h2>Récords personales</h2><div class="history-record-grid"><span><b>{{careerRecords.matches_managed||0}}</b><small>partidos</small></span><span><b>{{careerRecords.wins||0}}</b><small>victorias</small></span><span><b>{{careerRecords.longest_win_streak||0}}</b><small>racha victorias</small></span><span><b>{{careerRecords.longest_unbeaten_streak||0}}</b><small>sin perder</small></span></div><p v-if="careerRecords.biggest_win"><strong>Mayor victoria:</strong> {{careerRecords.biggest_win.result}} ante {{careerRecords.biggest_win.opponent_name}}</p><p v-else class="rail-empty">Tu primera gran marca todavía está por llegar.</p></article><article class="football-panel"><h2>Palmarés del club</h2><div class="honours-modern compact"><article v-for="h in [...(historyState.club_honours||[])].reverse()" :key="`${h.season}-${h.source_id}`"><b>{{h.season}}</b><strong>{{h.competition_name}}</strong></article></div><p v-if="!historyState.club_honours?.length" class="rail-empty">Aún no has añadido títulos.</p></article><article class="football-panel audit-card"><h2>Salud de plantillas IA</h2><template v-if="latestAiAudit"><div class="ai-audit-score"><b>{{latestAiAudit.coverage_ok}} / {{latestAiAudit.club_count}}</b><span>clubes con cobertura mínima completa</span></div><p>{{latestAiAudit.emergency_signings}} incorporaciones de emergencia.</p></template><p v-else class="rail-empty">La primera auditoría global se registra en julio.</p></article></aside>
</section>
</template>
