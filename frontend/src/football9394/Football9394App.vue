<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import FootballPlayerProfileModal from '../features/football9394/FootballPlayerProfileModal.vue'
import { football9394Api } from './api.js'

const sections = [
  ['home','Inicio'],['squad','Plantilla'],['tactics','Tácticas'],['competitions','Competiciones'],
  ['market','Fichajes'],['national','Selecciones'],['club','Club'],['calendar','Calendario'],
]
const view = ref('home')
const careerId = ref('')
const careerOptions = ref([])
const showCareerSetup = ref(false)
const selectedLeagueId = ref(null)
const selectedTeamId = ref(null)
const careerSeason = ref('1993-94')
const totalMatchdays = ref(38)
const gameDate = ref('1993-10-23')
const currentDate = computed(() => {
 const [y,m,d]=String(gameDate.value||'1993-10-23').split('-')
 const months=['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC']
 return `${d} ${months[Number(m)-1]||m} ${y}`
})
const currentMatchday = computed(() => nextMatch.value?.matchday ?? Math.min(totalMatchdays.value, simulatedThroughMatchday.value + 1))
const formation = ref('4-4-2')
const mentality = ref('balanced')
const tempo = ref('normal')
const pressing = ref('medium')
const directness = ref('mixed')
const defensiveLine = ref('medium')
const marking = ref('zonal')
const selectedPlayer = ref(null)
const playerTab = ref('profile')
const selectedCompetition = ref('league:1')
const notice = ref('')
const finances = ref({cash:0,starting_budget:0,debt:0,transfer_spend:0,transfer_income:0,matchday_income:0})
const selectedTarget = ref(null)
const transferFee = ref(0)
const transferSalary = ref(0)
const transferYears = ref(3)
const nationalTeams = ref([])
const selectedNationalTeam = ref(null)
const nationalSquad = ref([])
const internationalHistory = ref([])
const specialProgress = ref({})
const tournamentProgress = ref({})
const recentWorldEvents = ref([])
const aiTransfers = ref([])
const loadingHistoricalData = ref(true)
const dataError = ref('')
const simulatedThroughMatchday = ref(7)
const managerDashboard = ref({position:null,points:0,recent_form:[],form_label:'Sin partidos',morale_average:70,unavailable_count:0,board_expectation:{title:'—'},board_confidence:'A la espera',pending_decisions:[]})
const selection = ref({starter_ids:[],bench_ids:[],starters:[],bench:[],valid:false,issues:[]})
const lineupDraft = ref([])

const controlledTeam = ref({source_id:null,name:'Sin club',long_name:'Sin club',league:null,members:null,budget:null,debt:null})
const controlledTeamId = computed(()=>Number(controlledTeam.value?.source_id||0))
const selectedLeagueOption = computed(()=>careerOptions.value.find(row=>Number(row.source_id)===Number(selectedLeagueId.value))||null)
const setupTeams = computed(()=>selectedLeagueOption.value?.teams||[])
const selectedSetupTeam = computed(()=>setupTeams.value.find(team=>Number(team.source_id)===Number(selectedTeamId.value))||null)
const lineupDraftPlayers = computed(()=>lineupDraft.value.map(id=>squad.value.find(p=>Number(p.id)===Number(id))).filter(Boolean))
const standings = ref([])
const competitionStandings = ref([])
const competitionProgress = ref(null)
const squad = ref([])
const competitions = ref([])
const targets = ref([])
const matches = ref([])
const nextMatch = ref(null)
const news = ref([
 ['HOY','La temporada utiliza el snapshot histórico normalizado de la base de datos.'],
 ['HOY','Los resultados mostrados pertenecen a esta partida simulada; no se presentan como resultados históricos reales.'],
])

const selectedCompetitionInfo = computed(()=>competitions.value.find(c=>`${c.kind}:${c.source_id}`===selectedCompetition.value)||null)
const tableWindow = computed(()=>{
 const rows=standings.value
 const index=rows.findIndex(r=>r[8]===controlledTeamId.value)
 if(index<0)return rows.slice(0,7)
 return rows.slice(Math.max(0,index-3),Math.min(rows.length,index+4))
})
const competitionStatusLabel = computed(()=>{
 const row=selectedCompetitionInfo.value
 if(!row)return 'Cargando reglamento…'
 if(row.simulation_ready)return 'REGLAMENTO 1993-94 CERTIFICADO'
 if(row.rule_status==='historical_conflict')return 'CONFLICTO HISTÓRICO BLOQUEADO'
 if(row.rule_status==='structure_verified')return 'ESTRUCTURA VERIFICADA · REGLAS PENDIENTES'
 return 'REGLAMENTO PENDIENTE'
})

function historicalPlayerPhoto(id){return id?`/historical9394/players/${Number(id)}.jpg`:null}
function historicalClubCrest(id){return id?`/historical9394/clubs/${Number(id)}.gif`:null}
function historicalStadiumPhoto(id){return id?`/historical9394/stadiums/${Number(id)}.jpg`:null}
function formatSourceMoney(value){
 if(value==null)return '—'
 return `${Number(value).toLocaleString('es-ES')} ptas.`
}
function toSquadRow(player){
 return {
  id:player.id,n:player.shirt_number??'—',name:player.display_name,pos:player.position,age:player.age??'—',overall:player.overall??'—',
  form:player.form??'—',morale:player.morale??'—',status:String(player.status||'').startsWith('Lesionado')?'LES.':player.status==='Disponible'?'DISP.':player.status==='Retirado'?'RET.':'NO DISP.',nationality:player.nationality,
  contractEnd:player.contract?.end??'—',salary:player.contract?.salary??0,
  profile:player,
 }
}
function standingsFromState(rows){
 return rows.map(r=>[r.team_name,r.played,r.wins,r.draws,r.losses,r.goals_for,r.goals_against,r.points,r.team_id])
}
function applyCareerState(state){
 if(state.career_id){careerId.value=state.career_id;window.localStorage?.setItem('mister9394-career-id',state.career_id)}
 if(state.game_date)gameDate.value=state.game_date
 if(state.season)careerSeason.value=state.season
 if(state.total_matchdays)totalMatchdays.value=state.total_matchdays
 controlledTeam.value=state.team||controlledTeam.value
 if(state.league_id!=null)selectedCompetition.value=`league:${state.league_id}`
 squad.value=(state.squad||[]).map(toSquadRow)
 standings.value=standingsFromState(state.standings||[])
 nextMatch.value=state.next_match
 simulatedThroughMatchday.value=state.completed_matchday ?? state.through_matchday ?? 0
 finances.value=state.finances||finances.value
 specialProgress.value=state.special_progress||specialProgress.value
 tournamentProgress.value=state.tournament_progress||tournamentProgress.value
 internationalHistory.value=state.international_history||internationalHistory.value
 recentWorldEvents.value=state.recent_world_events||recentWorldEvents.value
 aiTransfers.value=state.ai_transfer_history||aiTransfers.value
 managerDashboard.value=state.manager_dashboard||managerDashboard.value
 selection.value=state.selection||selection.value
 lineupDraft.value=[...(state.selection?.starter_ids||[])]
 if(state.tactics){
  formation.value=state.tactics.formation||formation.value;mentality.value=state.tactics.mentality||mentality.value
  tempo.value=state.tactics.tempo||tempo.value;pressing.value=state.tactics.pressing||pressing.value
  directness.value=state.tactics.directness||directness.value;defensiveLine.value=state.tactics.defensive_line||defensiveLine.value
  marking.value=state.tactics.marking||marking.value
 }
}
function calendarRowsForUi(rows,state){
 const teamId=Number(state.team?.source_id||controlledTeamId.value)
 const leagueName=state.team?.league?.name||'Liga'
 return (rows||[]).slice(-8).map(m=>{
  const opponent=Number(m.home_team_id)===teamId?m.away_team:m.home_team
  const venue=Number(m.home_team_id)===teamId?'Casa':'Fuera'
  const status=m.played?`${m.home_goals}-${m.away_goals}`:'Pendiente'
  return [m.date||`Jornada ${m.matchday}`,opponent,venue,leagueName,status,m.id]
 })
}
async function refreshCareerData(state){
 const [calendarRows,marketRows]=await Promise.all([
  football9394Api.careerCalendar(state.career_id),football9394Api.careerMarket(state.career_id,{limit:10}),
 ])
 const recent=calendarRows.filter(m=>m.played).slice(-3);const upcoming=calendarRows.filter(m=>!m.played).slice(0,6)
 matches.value=calendarRowsForUi([...recent,...upcoming],state)
 targets.value=marketRows.map(p=>[p.display_name,p.position,p.team_name,p.overall??'—',p.estimated_transfer_value??0,p.id,p])
}
async function loadHistoricalCareer(){
 loadingHistoricalData.value=true;dataError.value=''
 try{
  const [options,competitionRows,nationalRows]=await Promise.all([football9394Api.careerOptions(),football9394Api.competitions(),football9394Api.nationalTeams()])
  careerOptions.value=options.leagues||[];competitions.value=competitionRows;nationalTeams.value=nationalRows
  if(careerOptions.value.length){selectedLeagueId.value=careerOptions.value[0].source_id;selectedTeamId.value=careerOptions.value[0].teams?.[0]?.source_id??null}
  let state=null
  const savedId=window.localStorage?.getItem('mister9394-career-id')
  if(savedId){try{state=await football9394Api.career(savedId)}catch{window.localStorage?.removeItem('mister9394-career-id')}}
  if(state){applyCareerState(state);await refreshCareerData(state);showCareerSetup.value=false}
  else showCareerSetup.value=true
 }catch(error){
  dataError.value=error.message||String(error);showCareerSetup.value=true
  flash(`No se pudo cargar Míster 93/94: ${dataError.value}`)
 }finally{loadingHistoricalData.value=false}
}
async function startCareer(){
 if(!selectedLeagueId.value||!selectedTeamId.value){flash('Selecciona una liga y un equipo.');return}
 loadingHistoricalData.value=true;dataError.value=''
 try{
  const state=await football9394Api.createCareer({teamId:Number(selectedTeamId.value),leagueId:Number(selectedLeagueId.value),seed:9394,throughMatchday:0})
  applyCareerState(state);await refreshCareerData(state);showCareerSetup.value=false;view.value='home'
  flash(`Carrera iniciada · ${state.team.name}`)
 }catch(error){dataError.value=error.message||String(error);flash(`No se pudo crear la carrera: ${dataError.value}`)}
 finally{loadingHistoricalData.value=false}
}
function openCareerSetup(){
 const currentLeague=Number(controlledTeam.value?.league?.source_id||selectedLeagueId.value||careerOptions.value[0]?.source_id||0)
 selectedLeagueId.value=currentLeague||null
 const league=careerOptions.value.find(row=>Number(row.source_id)===Number(selectedLeagueId.value))
 selectedTeamId.value=league?.teams?.some(t=>Number(t.source_id)===controlledTeamId.value)?controlledTeamId.value:(league?.teams?.[0]?.source_id??null)
 showCareerSetup.value=true
}
function profileFor(row){
 if(row.profile)return {...row.profile,photo_url:historicalPlayerPhoto(row.profile.id),role:'—',market_value_display:formatSourceMoney(row.profile.estimated_transfer_value),team_crest_url:historicalClubCrest(row.profile.team_id)}
 return {id:row.id,display_name:row.name,team_id:controlledTeamId.value,team_name:controlledTeam.value.name,photo_url:historicalPlayerPhoto(row.id),team_crest_url:historicalClubCrest(controlledTeamId.value),shirt_number:row.n,age:row.age,nationality:row.nationality,position:row.pos,positions:[row.pos],overall:row.overall,attributes:{}}
}
function isStarter(playerId){return lineupDraft.value.includes(Number(playerId))}
function toggleStarter(player){
 const id=Number(player.id)
 if(player.status!=='DISP.'&&!isStarter(id)){flash(`${player.name} no está disponible.`);return}
 if(isStarter(id)){lineupDraft.value=lineupDraft.value.filter(x=>x!==id);return}
 if(lineupDraft.value.length>=11){flash('El once ya tiene 11 futbolistas. Quita uno antes de añadir otro.');return}
 lineupDraft.value=[...lineupDraft.value,id]
}
async function saveSelection(){
 if(!careerId.value)return
 try{
  const result=await football9394Api.updateCareerSelection(careerId.value,{starterIds:lineupDraft.value})
  applyCareerState(result.career);flash('Once y convocatoria guardados.')
 }catch(error){flash(`No se pudo guardar el once: ${error.message}`)}
}
async function autoSelectLineup(){
 if(!careerId.value)return
 try{const result=await football9394Api.updateCareerSelection(careerId.value,{autoSelect:true});applyCareerState(result.career);flash('Mejor once disponible seleccionado.')}catch(error){flash(`No se pudo seleccionar el once: ${error.message}`)}
}
function openDecision(decision){if(decision?.action)view.value=decision.action}
function flash(message){notice.value=message;window.setTimeout(()=>{notice.value=''},2200)}
function openPlayer(row){selectedPlayer.value=profileFor(row);playerTab.value='profile'}
async function advance(){
 if(!careerId.value){flash('La carrera todavía no está lista.');return}
 try{
  const result=await football9394Api.advanceCareer(careerId.value)
  applyCareerState(result.career)
  if(result.world_events?.length){
   const event=result.world_events[result.world_events.length-1]
   if(event.kind==='international_friendly')news.value.unshift(['HOY',`${event.home_name} ${event.home_goals}-${event.away_goals} ${event.away_name} · amistoso de la partida.`])
   else if(event.kind==='ai_transfer')news.value.unshift(['HOY','El mercado internacional se ha movido: un club de la IA ha cerrado un traspaso.'])
  }
  if(result.requires_match&&result.next_match)flash(`DÍA DE PARTIDO · ${result.next_match.home_team} - ${result.next_match.away_team}`)
  else flash(`Día avanzado · ${result.date}`)
 }catch(error){flash(`No se pudo avanzar: ${error.message}`)}
}
async function simulateControlledMatch(){
 if(!nextMatch.value||!careerId.value){flash('No hay próximo partido cargado.');return}
 try{
  const tactics={formation:formation.value,mentality:mentality.value,tempo:tempo.value,pressing:pressing.value,directness:directness.value,defensive_line:defensiveLine.value,marking:marking.value,width:'normal',offside_trap:false}
  await football9394Api.updateCareerTactics(careerId.value,tactics)
  const newState=await football9394Api.playNextCareerMatchday(careerId.value)
  applyCareerState(newState)
  const played=newState.played_match
  const last=newState.last_controlled_result
  if(played?.fixture_type==='tournament') news.value.unshift(['HOY',`${played.competition_name} · ${played.stage}: ${played.home_goals}-${played.away_goals}. Resultado persistido por el motor 1993-94.`])
  else if(last)news.value.unshift(['HOY',`${last.home_team} ${last.home_goals}-${last.away_goals} ${last.away_team}. Resultado persistido por el motor 1993-94.`])
  await refreshCareerData(newState)
  if(played?.fixture_type==='tournament') flash(`FINAL · ${played.competition_name} · ${played.home_goals}-${played.away_goals}`)
  else flash(last?`FINAL · ${last.home_team} ${last.home_goals}-${last.away_goals} ${last.away_team}`:'Partido completado')
 }catch(error){flash(`No se pudo simular: ${error.message}`)}
}

function chooseTarget(row){
 selectedTarget.value=row
 transferFee.value=Math.round(Number(row[4]||0)*0.9)
 transferSalary.value=Number(row[6]?.contract?.salary||0)
 transferYears.value=3
}
async function submitTransfer(){
 if(!selectedTarget.value||!careerId.value)return
 try{
  const result=await football9394Api.negotiateTransfer(careerId.value,selectedTarget.value[5],{feeOffer:Number(transferFee.value),salaryOffer:Number(transferSalary.value),contractYears:Number(transferYears.value)})
  applyCareerState(result.career)
  if(result.decision.accepted){
   flash(`${selectedTarget.value[0]} fichado por ${formatSourceMoney(result.decision.fee)}`)
   selectedTarget.value=null
   const marketRows=await football9394Api.careerMarket(careerId.value,{limit:10})
   targets.value=marketRows.map(p=>[p.display_name,p.position,p.team_name,p.overall??'—',p.estimated_transfer_value??0,p.id,p])
  }else{
   transferFee.value=result.decision.counter_fee||transferFee.value
   transferSalary.value=result.decision.counter_salary||transferSalary.value
   const counter=result.decision.counter_salary?` · ficha ${formatSourceMoney(result.decision.counter_salary)}`:''
   flash(`Oferta rechazada · contraoferta ${formatSourceMoney(result.decision.counter_fee)}${counter}`)
  }
 }catch(error){flash(`Negociación fallida: ${error.message}`)}
}
async function renewPlayer(row){
 if(!careerId.value||!row?.id)return
 try{
  const salary=Math.max(0,Number(row.salary||row.profile?.contract?.salary||0))
  const result=await football9394Api.renewContract(careerId.value,row.id,{years:3,salaryOffer:salary})
  applyCareerState(result.career)
  if(result.decision.accepted)flash(`${row.name} renovado hasta ${result.career.squad.find(p=>p.id===row.id)?.contract?.end||'nuevo contrato'}`)
  else flash(`Renovación rechazada · pide ${formatSourceMoney(result.decision.counter_salary)}`)
 }catch(error){flash(`No se pudo renovar: ${error.message}`)}
}
async function openNationalTeam(team){
 selectedNationalTeam.value=team
 try{
  const data=await football9394Api.nationalTeam(team.country_id,careerId.value)
  nationalSquad.value=data.squad||[]
 }catch(error){flash(`No se pudo cargar la selección: ${error.message}`)}
}

async function loadSelectedCompetitionTable(){
 if(!careerId.value)return
 const [kind,id]=String(selectedCompetition.value).split(':')
 if(kind!=='league'){competitionStandings.value=[];competitionProgress.value=null;return}
 try{
  const data=await football9394Api.careerLeagueStandings(careerId.value,Number(id))
  competitionStandings.value=data.rows||[]
  competitionProgress.value=data
 }catch{competitionStandings.value=[];competitionProgress.value=null}
}
const selectedCompetitionRuntime = computed(()=>{
 const [kind,id]=String(selectedCompetition.value).split(':')
 if(kind==='tournament')return tournamentProgress.value[id]||null
 if(kind==='league'&&specialProgress.value[id])return specialProgress.value[id]
 return competitionProgress.value
})
const selectedNationalHistory = computed(()=>{
 const id=selectedNationalTeam.value?.country_id
 if(!id)return []
 return internationalHistory.value.filter(m=>m.home_country_id===id||m.away_country_id===id).slice(-6).reverse()
})
watch(selectedLeagueId,()=>{const league=selectedLeagueOption.value;selectedTeamId.value=league?.teams?.[0]?.source_id??null})
watch(selectedCompetition,loadSelectedCompetitionTable)
watch(careerId,()=>{if(careerId.value)loadSelectedCompetitionTable()})

onMounted(loadHistoricalCareer)
</script>

<template>
<div class="m9394-shell">
  <section v-if="showCareerSetup" class="career-setup football-frame">
    <div class="career-setup-card football-panel">
      <div class="m9394-brand setup-brand"><span class="m9394-ball">⚽</span><div><strong>MÍSTER 93/94</strong><small>NUEVA CARRERA</small></div></div>
      <h1>Empieza tu carrera</h1>
      <p>Elige una competición y el club que vas a dirigir. El mundo seguirá simulando el resto de ligas y competiciones.</p>
      <label>LIGA
        <select v-model.number="selectedLeagueId"><option v-for="league in careerOptions" :key="league.source_id" :value="league.source_id">{{league.country}} · {{league.name}} · {{league.team_count}} clubes</option></select>
      </label>
      <label>EQUIPO
        <select v-model.number="selectedTeamId"><option v-for="team in setupTeams" :key="team.source_id" :value="team.source_id">{{team.long_name || team.name}}</option></select>
      </label>
      <div v-if="selectedSetupTeam" class="setup-club-preview">
        <img class="setup-crest" :src="historicalClubCrest(selectedSetupTeam.source_id)" alt="">
        <div class="setup-club-copy"><strong>{{selectedSetupTeam.long_name || selectedSetupTeam.name}}</strong><span>{{selectedSetupTeam.squad_size}} jugadores · núcleo {{selectedSetupTeam.average_top_11}}/100</span><small>{{selectedSetupTeam.members ?? '—'}} socios · presupuesto {{formatSourceMoney(selectedSetupTeam.budget)}} · deuda {{formatSourceMoney(selectedSetupTeam.debt)}}</small></div>
        <img v-if="selectedSetupTeam.stadium_id" class="setup-stadium" :src="historicalStadiumPhoto(selectedSetupTeam.stadium_id)" alt="">
        <div class="setup-top-players"><span v-for="p in selectedSetupTeam.top_players" :key="p.id"><img :src="historicalPlayerPhoto(p.id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"><b>{{p.name}}</b><small>{{p.position}} · {{p.overall}}</small></span></div>
      </div>
      <div class="career-setup-meta"><span>Temporada inicial 1993-94</span><span>{{selectedLeagueOption?.rounds || '—'}} partidos por club / formato histórico</span></div>
      <button type="button" class="football-button primary start-career" :disabled="loadingHistoricalData||!selectedTeamId" @click="startCareer">{{loadingHistoricalData?'CREANDO PARTIDA…':'EMPEZAR CARRERA'}}</button>
      <button v-if="careerId" type="button" class="football-button" @click="showCareerSetup=false">VOLVER A LA CARRERA ACTUAL</button>
      <div v-if="dataError" class="data-error">{{dataError}}</div>
    </div>
  </section>
  <template v-else>
  <header class="m9394-top football-frame">
    <div class="m9394-brand"><span class="m9394-ball">⚽</span><div><strong>MÍSTER 93/94</strong><small>MANAGER DE FÚTBOL</small></div></div>
    <div class="m9394-context"><strong>{{ controlledTeam.name }}</strong><span>{{ controlledTeam.league?.name || 'Sin liga' }} · {{ controlledTeam.league?.country || '' }}</span></div>
    <div class="m9394-date"><b>{{ currentDate }}</b><span>Jornada {{currentMatchday}}</span></div>
    <button type="button" class="football-button" @click="openCareerSetup">NUEVA CARRERA</button>
    <button type="button" class="football-button primary" @click="advance">CONTINUAR <i>▶</i></button>
  </header>

  <nav class="m9394-nav football-frame" aria-label="Secciones principales">
    <button v-for="item in sections" :key="item[0]" type="button" class="football-button nav-button" :class="{active:view===item[0]}" @click="view=item[0]">{{ item[1] }}</button>
  </nav>

  <main class="m9394-workspace football-frame"><div v-if="dataError" class="data-error">Error de datos: {{dataError}}</div>
    <section v-if="view==='home'" class="screen-grid home-screen">
      <article class="football-panel next-match"><h2>PRÓXIMO PARTIDO</h2><div v-if="nextMatch" class="match-poster"><div><small v-if="nextMatch.fixture_type==='tournament'">{{nextMatch.competition_name}} · {{nextMatch.stage}}</small><small v-else>LIGA · JORNADA {{nextMatch.matchday}}</small><b>{{nextMatch.home_team}}</b><span>{{nextMatch.home_team_id===controlledTeamId?'Nuestro campo':'Rival'}}</span></div><strong>VS</strong><div><small>PARTIDA {{careerSeason}}</small><b>{{nextMatch.away_team}}</b><span>{{nextMatch.away_team_id===controlledTeamId?'Nuestro equipo':'Rival'}}</span></div></div><div v-else class="empty-football-state">{{loadingHistoricalData?'Cargando calendario histórico…':'Sin próximo partido'}}</div><div class="decision-row"><button type="button" class="football-button" @click="view='tactics'">PREPARAR PARTIDO</button><button type="button" class="football-button" @click="simulateControlledMatch">SIMULAR PARTIDO</button><button type="button" class="football-button" @click="view='squad'">CONVOCATORIA</button></div></article>
      <article class="football-panel mini-table"><h2>CLASIFICACIÓN</h2><table><tbody><tr v-for="(r,i) in tableWindow" :key="r[0]" :class="{controlled:r[8]===controlledTeamId}"><td>{{ standings.indexOf(r)+1 }}º</td><td>{{r[0]}}</td><td class="points">{{r[7]}}</td></tr></tbody></table><button type="button" class="football-button compact" @click="view='competitions'">VER COMPLETA</button></article>
      <article class="football-panel inbox"><h2>BANDEJA DEL MÍSTER</h2><button v-for="d in managerDashboard.pending_decisions" :key="d.kind" type="button" class="news-row decision-news" @click="openDecision(d)"><b>{{d.priority==='high'?'URGENTE':'PEND.'}}</b><span><strong>{{d.title}}</strong><small>{{d.detail}}</small></span></button><button v-for="n in news.slice(0,2)" :key="n[0]+n[1]" type="button" class="news-row secondary-news"><b>{{n[0]}}</b><span>{{n[1]}}</span></button><div v-if="!managerDashboard.pending_decisions?.length" class="inbox-clear">No hay decisiones obligatorias. Puedes continuar.</div></article>
      <article class="football-panel status"><h2>ESTADO DEL EQUIPO</h2><div class="status-grid"><div class="metric green"><small>FORMA</small><b>{{managerDashboard.form_label}}</b></div><div class="metric yellow"><small>MORAL</small><b>{{managerDashboard.morale_average}}</b></div><div class="metric blue"><small>POSICIÓN</small><b>{{managerDashboard.position?`${managerDashboard.position}º`:'—'}}</b></div><div class="metric red"><small>NO DISP.</small><b>{{managerDashboard.unavailable_count}}</b></div></div><div class="form-strip"><span v-for="(r,i) in managerDashboard.recent_form" :key="i" :class="`form-${r}`">{{r}}</span></div><p>Objetivo del consejo: <b>{{managerDashboard.board_expectation?.title}}</b></p><p>Confianza: <strong>{{managerDashboard.board_confidence}}</strong></p></article>
    </section>

    <section v-else-if="view==='squad'" class="screen-grid squad-screen">
      <article class="football-panel roster"><h2>PLANTILLA · PRIMER EQUIPO <small>{{lineupDraft.length}}/11 TITULARES</small></h2><table><thead><tr><th>XI</th><th>Nº</th><th>JUGADOR</th><th>POS</th><th>EDAD</th><th>MEDIA</th><th>FORMA</th><th>MORAL</th><th>CONTRATO</th><th>EST.</th><th></th></tr></thead><tbody><tr v-for="p in squad" :key="p.id" :class="{selectedStarter:isStarter(p.id)}" @dblclick="openPlayer(p)"><td><button type="button" class="lineup-toggle" :class="{active:isStarter(p.id)}" @click.stop="toggleStarter(p)">{{isStarter(p.id)?'✓':'+'}}</button></td><td>{{p.n}}</td><td><button type="button" class="player-link" @click="openPlayer(p)">{{p.name}}</button></td><td>{{p.pos}}</td><td>{{p.age}}</td><td class="rating-cell">{{p.overall}}</td><td class="good-cell">{{p.form}}</td><td class="warn-cell">{{p.morale}}</td><td>{{p.contractEnd}}</td><td :class="p.status==='LES.'?'bad-cell':'good-text'">{{p.status}}</td><td><button type="button" class="football-button tiny" @click.stop="renewPlayer(p)">RENOVAR</button></td></tr></tbody></table></article>
      <aside class="football-panel lineup"><h2>ONCE REAL · {{formation}}</h2><div class="lineup-sheet"><div v-for="p in lineupDraftPlayers" :key="p.id" class="lineup-player"><img :src="historicalPlayerPhoto(p.id)" alt="" @error="$event.currentTarget.style.visibility='hidden'"><span><b>{{p.name}}</b><small>{{p.pos}} · {{p.overall}}</small></span></div></div><p v-if="selection.issues?.length" class="selection-error">{{selection.issues.join(' ')}}</p><div class="decision-row vertical"><button type="button" class="football-button" @click="autoSelectLineup">MEJOR ONCE DISPONIBLE</button><button type="button" class="football-button primary" @click="saveSelection">GUARDAR ONCE Y CONVOCATORIA</button><button type="button" class="football-button" @click="view='tactics'">EDITAR TÁCTICA</button></div></aside>
    </section>

    <section v-else-if="view==='tactics'" class="screen-grid tactics-screen">
      <article class="football-panel"><h2>FORMACIÓN</h2><div class="formation-row"><button v-for="f in ['4-4-2','4-3-3','3-5-2','5-3-2']" :key="f" type="button" class="football-button" :class="{active:formation===f}" @click="formation=f">{{f}}</button></div><div class="big-pitch football-pitch"><span class="tactic-label">{{formation}}</span></div></article>
      <article class="football-panel"><h2>ÓRDENES DEL EQUIPO</h2><div class="order-grid"><label>MENTALIDAD<select v-model="mentality"><option value="balanced">Equilibrada</option><option value="defensive">Defensiva</option><option value="attacking">Ofensiva</option></select></label><label>RITMO<select v-model="tempo"><option value="normal">Normal</option><option value="slow">Lento</option><option value="high">Alto</option></select></label><label>PRESIÓN<select v-model="pressing"><option value="medium">Media</option><option value="low">Baja</option><option value="high">Alta</option></select></label><label>PASE<select v-model="directness"><option value="mixed">Mixto</option><option value="short">Corto</option><option value="direct">Directo</option></select></label><label>LÍNEA DEFENSIVA<select v-model="defensiveLine"><option value="medium">Media</option><option value="low">Baja</option><option value="high">Alta</option></select></label><label>MARCAJE<select v-model="marking"><option value="zonal">Zonal</option><option value="man">Al hombre</option></select></label></div><div class="era-note"><b>FÚTBOL 1993-94</b><p>Las órdenes son deliberadamente claras. La profundidad está en cómo interactúan jugadores, cansancio, rival y contexto; no en cincuenta sliders.</p></div></article>
    </section>

    <section v-else-if="view==='competitions'" class="screen-grid competition-screen">
      <article class="football-panel standings"><h2>CLASIFICACIÓN</h2><div class="toolbar"><select v-model="selectedCompetition"><option v-for="c in competitions" :key="`${c.kind}:${c.source_id}`" :value="`${c.kind}:${c.source_id}`">{{c.country?`${c.country} · `:''}}{{c.name}}</option></select><b>{{competitionStatusLabel}}</b></div><table v-if="competitionStandings.length"><thead><tr><th>POS</th><th>EQUIPO</th><th>PJ</th><th>PG</th><th>PE</th><th>PP</th><th>GF</th><th>GC</th><th>DG</th><th>PTS</th></tr></thead><tbody><tr v-for="r in competitionStandings" :key="r.team_id" :class="{controlled:r.team_id===controlledTeamId}"><td>{{r.position}}º</td><td>{{r.team_name}}</td><td>{{r.played}}</td><td class="good-cell">{{r.wins}}</td><td class="warn-cell">{{r.draws}}</td><td class="bad-cell">{{r.losses}}</td><td class="blue-cell">{{r.goals_for}}</td><td class="bad-cell">{{r.goals_against}}</td><td>{{r.goal_difference>0?'+':''}}{{r.goal_difference}}</td><td class="points">{{r.points}}</td></tr></tbody></table><div v-else class="competition-readiness"><strong>{{selectedCompetitionInfo?.name}}</strong><span>{{selectedCompetitionInfo?.country}}</span><p>{{competitionStatusLabel}}</p><small v-if="selectedCompetitionInfo?.simulation_ready">Competición activa de la MDB con runtime histórico 1993-94 certificado.</small><small v-else>La competición permanece visible, pero el motor no inventará reglas hasta certificar su formato histórico.</small></div></article>
      <aside class="side-stack"><article class="football-panel rules"><h2>REGLAS 1993-94</h2><template v-if="selectedCompetition==='league:1'"><p><b>Victoria</b> 2 puntos</p><p><b>Empate</b> 1 punto</p><p><b>Descenso</b> 19º y 20º</p><p><b>Promoción</b> 17º y 18º</p><p>Los filiales no pueden compartir categoría con el primer equipo.</p></template><template v-else><p><b>Estado</b> {{competitionStatusLabel}}</p><p v-if="selectedCompetitionRuntime"><b>Progreso de partida</b> {{selectedCompetitionRuntime.stage || `Jornada ${selectedCompetitionRuntime.completed_round}`}} · {{selectedCompetitionRuntime.result_count ?? selectedCompetitionRuntime.event_count ?? 0}} eventos/partidos</p><p v-if="selectedCompetitionInfo?.format_id"><b>Formato</b> {{selectedCompetitionInfo.format_id}}</p><p v-if="selectedCompetitionInfo?.ruleset_id"><b>Ruleset</b> {{selectedCompetitionInfo.ruleset_id}}</p><p v-if="selectedCompetitionInfo?.pyramid_floor"><b>Suelo de pirámide</b> Sin descenso deportivo mientras no exista una categoría inferior en los datos.</p><p>Sin fallback moderno: si no está certificado, queda bloqueado.</p></template></article><article class="football-panel"><h2>ESTADO DEL MUNDO</h2><div class="fixture-list"><p>{{competitions.length}} competiciones activas</p><p>Brasil / APSL / J.League: avance incremental</p><p>Copas UEFA y Copa del Rey: calendario de fases persistente</p></div></article></aside>
    </section>

    <section v-else-if="view==='market'" class="screen-grid market-screen">
      <article class="football-panel"><h2>FICHAJES · SEGUIMIENTO</h2><div class="target-row target-head"><span>JUGADOR</span><span>POS</span><span>CLUB</span><span>MEDIA</span><span>VALOR</span><span></span></div><div v-for="t in targets" :key="t[0]" class="target-row"><strong>{{t[0]}}</strong><span>{{t[1]}}</span><small>{{t[2]}}</small><b>{{t[3]}}</b><span>{{formatSourceMoney(t[4])}}</span><button type="button" class="football-button tiny" @click="chooseTarget(t)">NEGOCIAR</button></div></article>
      <aside class="football-panel market-summary"><h2>MERCADO</h2><div class="budget"><small>CAJA DISPONIBLE</small><b>{{formatSourceMoney(finances.cash)}}</b></div><p>Las ofertas alteran plantilla, contrato y caja. Los demás clubes también fichan y renuevan por sí mismos.</p><div v-if="selectedTarget" class="transfer-box"><strong>{{selectedTarget[0]}}</strong><label>Traspaso<input v-model.number="transferFee" type="number" min="0"></label><label>Ficha anual<input v-model.number="transferSalary" type="number" min="0"></label><label>Años<input v-model.number="transferYears" type="number" min="1" max="6"></label><button type="button" class="football-button primary" @click="submitTransfer">ENVIAR OFERTA</button></div><button v-else type="button" class="football-button" @click="flash('Usa el listado para iniciar una negociación')">BUSCAR JUGADOR</button><div class="ai-market"><small>ÚLTIMOS MOVIMIENTOS IA</small><p v-for="m in aiTransfers.slice(-4).reverse()" :key="`${m.date}-${m.player_id}`">{{m.date}} · {{formatSourceMoney(m.fee)}}</p><p v-if="!aiTransfers.length">Aún no hay operaciones IA en esta partida.</p></div></aside>
    </section>

    <section v-else-if="view==='national'" class="screen-grid national-screen">
      <article class="football-panel national-list"><h2>SELECCIONES</h2><button v-for="nt in nationalTeams" :key="nt.country_id" type="button" class="national-row" :class="{active:selectedNationalTeam?.country_id===nt.country_id}" @click="openNationalTeam(nt)"><strong>{{nt.name}}</strong><span>{{nt.eligible_players}} elegibles</span><b>{{nt.average_top_22}}</b></button></article>
      <article class="football-panel national-squad"><h2>{{selectedNationalTeam?.name || 'SELECCIONA UN PAÍS'}}</h2><div v-if="!selectedNationalTeam" class="empty-football-state">Las selecciones se forman con PaisInternacional de la MDB. La edad permanece congelada, pero el estado de carrera sí afecta la convocatoria.</div><template v-else><div class="national-history"><small>PARTIDOS DE LA PARTIDA · AMISTOSOS GENERADOS, NO RESULTADOS HISTÓRICOS</small><p v-for="m in selectedNationalHistory" :key="`${m.date}-${m.home_country_id}-${m.away_country_id}`"><b>{{m.date}}</b> {{m.home_name}} {{m.home_goals}}-{{m.away_goals}} {{m.away_name}}</p><p v-if="!selectedNationalHistory.length">Todavía no ha llegado una ventana internacional.</p></div><table><thead><tr><th>JUGADOR</th><th>CLUB</th><th>POS</th><th>MEDIA</th><th>FORMA</th><th>ESTADO</th></tr></thead><tbody><tr v-for="p in nationalSquad" :key="p.id"><td><button type="button" class="player-link" @click="selectedPlayer=p;playerTab='profile'">{{p.display_name}}</button></td><td>{{p.team_name}}</td><td>{{p.position}}</td><td class="rating-cell">{{p.overall}}</td><td class="good-cell">{{p.form ?? '—'}}</td><td>{{p.status}}</td></tr></tbody></table></template></article>
    </section>

    <section v-else-if="view==='club'" class="screen-grid club-screen">
      <article class="football-panel club-hero-modern"><h2>{{controlledTeam.name}}</h2><div class="club-identity"><img class="club-real-crest" :src="historicalClubCrest(controlledTeamId)" alt=""><div><strong>{{controlledTeam.long_name}}</strong><span>Estadio histórico #{{controlledTeam.stadium_id || '—'}}</span><small>{{controlledTeam.league?.name}} · Temporada {{careerSeason}}</small></div><img v-if="controlledTeam.stadium_id" class="club-stadium-photo" :src="historicalStadiumPhoto(controlledTeam.stadium_id)" alt=""></div><div class="club-metrics"><div><small>Caja de carrera</small><b>{{formatSourceMoney(finances.cash)}}</b></div><div><small>Ingresos partidos</small><b>{{formatSourceMoney(finances.matchday_income)}}</b></div><div><small>Ingresos comerciales</small><b>{{formatSourceMoney(finances.commercial_income)}}</b></div><div><small>Gasto salarial</small><b>{{formatSourceMoney(finances.wage_expense)}}</b></div><div><small>Operación</small><b>{{formatSourceMoney(finances.operating_expense)}}</b></div><div><small>Traspasos</small><b>{{formatSourceMoney(finances.transfer_spend)}}</b></div><div><small>Socios</small><b>{{controlledTeam.members ?? '—'}}</b></div><div><small>Plantilla</small><b>{{squad.length}}</b></div></div></article>
      <aside class="football-panel"><h2>CONSEJO</h2><div class="board-goal"><small>OBJETIVO</small><b>{{managerDashboard.board_expectation?.title}}</b><span>Posición esperada: {{managerDashboard.board_expectation?.expected_position || '—'}}ª · Confianza {{managerDashboard.board_confidence}}</span></div><div class="board-goal"><small>ECONOMÍA</small><b>{{finances.net_operating>=0?'EQUILIBRADA':'TENSIÓN'}}</b><span>Se contabilizan salarios, operación, deuda, ingresos comerciales y taquilla.</span></div><div class="board-goal"><small>EDAD</small><b>CONGELADA</b><span>Los futbolistas evolucionan por rendimiento y lesiones, no por edad.</span></div></aside>
    </section>

    <section v-else-if="view==='calendar'" class="screen-grid calendar-screen">
      <article class="football-panel"><h2>CALENDARIO</h2><div class="calendar-row calendar-head"><span>FECHA</span><span>RIVAL</span><span>SEDE</span><span>COMPETICIÓN</span><span>ESTADO</span></div><div v-for="m in matches" :key="m[0]+m[1]" class="calendar-row"><b>{{m[0]}}</b><strong>{{m[1]}}</strong><span>{{m[2]}}</span><span>{{m[3]}}</span><em>{{m[4]}}</em></div></article>
      <aside class="football-panel"><h2>SEMANA</h2><div class="week-plan"><button type="button" class="plan active">SÁB · Viaje</button><button type="button" class="plan">DOM · Partido</button><button type="button" class="plan">LUN · Recuperación</button><button type="button" class="plan">MAR · Entrenamiento</button></div></aside>
    </section>
  </main>

  <FootballPlayerProfileModal v-if="selectedPlayer" :player="selectedPlayer" :season="careerSeason" :tab="playerTab" @update:tab="playerTab=$event" @close="selectedPlayer=null" />
  <div v-if="notice" class="notice" role="status">{{notice}}</div>
  </template>
</div>
</template>
