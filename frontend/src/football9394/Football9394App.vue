<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import FootballPlayerProfileModal from '../features/football9394/FootballPlayerProfileModal.vue'
import ManagerSidebar from './components/ManagerSidebar.vue'
import CareerSetup from './components/CareerSetup.vue'
import ManagerTopbar from './components/ManagerTopbar.vue'
import HomeDashboard from './components/HomeDashboard.vue'
import SquadWorkspace from './components/SquadWorkspace.vue'
import TacticsWorkspace from './components/TacticsWorkspace.vue'
import LiveMatchWorkspace from './components/LiveMatchWorkspace.vue'
import MarketWorkspace from './components/MarketWorkspace.vue'
import CompetitionsWorkspace from './components/CompetitionsWorkspace.vue'
import EconomyWorkspace from './components/EconomyWorkspace.vue'
import NewsWorkspace from './components/NewsWorkspace.vue'
import NationalWorkspace from './components/NationalWorkspace.vue'
import ClubWorkspace from './components/ClubWorkspace.vue'
import StaffWorkspace from './components/StaffWorkspace.vue'
import TrainingWorkspace from './components/TrainingWorkspace.vue'
import HistoryWorkspace from './components/HistoryWorkspace.vue'
import CalendarWorkspace from './components/CalendarWorkspace.vue'
import CareerWorkspace from './components/CareerWorkspace.vue'
import ChampionsWorkspace from './components/ChampionsWorkspace.vue'
import SeasonEndOverlay from './components/SeasonEndOverlay.vue'
import { football9394Api } from './api.js'

const navigationGroups = [
  { label: 'GESTIÓN', items: [
    { id: 'home', label: 'Inicio' },
    { id: 'squad', label: 'Plantilla' },
    { id: 'tactics', label: 'Tácticas' },
    { id: 'training', label: 'Entrenamiento' },
    { id: 'market', label: 'Mercado' },
    { id: 'staff', label: 'Cuerpo técnico' },
  ] },
  { label: 'TEMPORADA', items: [
    { id: 'competitions', label: 'Competiciones' },
    { id: 'calendar', label: 'Calendario' },
    { id: 'news', label: 'Noticias' },
  ] },
  { label: 'CLUB Y MUNDO', items: [
    { id: 'club', label: 'Club' },
    { id: 'career', label: 'Carrera' },
    { id: 'economy', label: 'Economía' },
    { id: 'national', label: 'Selecciones' },
    { id: 'history', label: 'Historia' },
    { id: 'champions', label: 'Campeones' },
  ] },
]
const view = ref('home')
const sectionTitle = computed(() => navigationGroups.flatMap(group => group.items).find(item => item.id === view.value)?.label || 'Inicio')
const careerId = ref('')
const careerOptions = ref([])
const showCareerSetup = ref(false)
const selectedLeagueId = ref(null)
const selectedTeamId = ref(null)
const selectedAgePolicy = ref('frozen_attributes_dynamic')
const careerSeason = ref('1993-94')
const totalMatchdays = ref(38)
const gameDate = ref('1993-10-23')
const careerAgePolicy = ref('frozen_attributes_dynamic')
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
const width = ref('normal')
const offsideTrap = ref(false)
const buildUp = ref('balanced')
const finalThird = ref('mixed')
const transition = ref('balanced')
const tacticalIdentity = ref({formation_label:'Equilibrio clásico'})
const liveMatch = ref(null)
const liveOutgoingId = ref(null)
const liveIncomingId = ref(null)
const lastMatchReport = ref(null)
const selectedPlayer = ref(null)
const playerTab = ref('profile')
const selectedCompetition = ref('league:1')
const notice = ref('')
const seasonEndRecap = ref(null)
const isAdvancing = ref(false)
const finances = ref({cash:0,starting_budget:0,debt:0,transfer_spend:0,transfer_income:0,matchday_income:0})
const selectedTarget = ref(null)
const transferFee = ref(0)
const transferSalary = ref(0)
const transferYears = ref(3)
const transferSquadRole = ref('rotation')
const transferSigningBonus = ref(0)
const transferReleaseClause = ref(null)
const transferDealType = ref('transfer')
const transferLoanWageShare = ref(100)
const marketQuery = ref('')
const marketPosition = ref('')
const marketFreeAgents = ref(false)
const marketWatchedOnly = ref(false)
const restoredMarketTargetId = ref(null)
const marketFlow = ref({watchlist:[],negotiations:[],listings:[],incoming_offers:[]})
const economy = ref({currency:{code:'ESP',name:'pesetas',label:'ptas.'},cash:0,debt:0,source_budget:0,transfer_budget_total:0,transfer_budget_remaining:0,wage_budget_annual:0,wage_room_annual:0,wage_budget_usage_pct:0,monthly_wages:0,annual_wages:0,monthly_commercial_income:0,monthly_membership_income:0,monthly_television_income:0,monthly_sponsorship_income:0,monthly_operating_expense:0,monthly_debt_service:0,monthly_debt_interest:0,monthly_debt_principal:0,projected_monthly_net:0,safety_reserve:0,transfer_room:0,status:'—',top_salaries:[],recent_ledger:[],contract_data_note:''})
const nationalTeams = ref([])
const selectedNationalTeam = ref(null)
const nationalSquad = ref([])
const internationalHistory = ref([])
const internationalManager = ref({country_id:null,country_name:null,reputation:35,job_offers:[],selection:[]})
const internationalTournaments = ref([])
const specialProgress = ref({})
const tournamentProgress = ref({})
const recentWorldEvents = ref([])
const aiTransfers = ref([])
const loadingHistoricalData = ref(true)
const matchActionBusy = ref(false)
const dataError = ref('')
const simulatedThroughMatchday = ref(7)
const managerDashboard = ref({position:null,points:0,recent_form:[],form_label:'Sin partidos',morale_average:70,unavailable_count:0,board_expectation:{title:'—'},board_confidence:'A la espera',pending_decisions:[]})
const selection = ref({starter_ids:[],bench_ids:[],starters:[],bench:[],valid:false,issues:[]})
const lineupDraft = ref([])

const controlledTeam = ref({source_id:null,name:'Sin club',long_name:'Sin club',league:null,members:null,budget:null,debt:null})
const controlledTeamId = computed(()=>Number(controlledTeam.value?.source_id||0))
const selectedLeagueOption = computed(()=>careerOptions.value.find(row=>Number(row.source_id)===Number(selectedLeagueId.value))||null)
const lineupDraftPlayers = computed(()=>lineupDraft.value.map(id=>squad.value.find(p=>Number(p.id)===Number(id))).filter(Boolean))
const lineupDirty = computed(()=>{const saved=[...(selection.value?.starter_ids||[])].map(Number).sort((a,b)=>a-b);const draft=[...lineupDraft.value].map(Number).sort((a,b)=>a-b);return JSON.stringify(saved)!==JSON.stringify(draft)})
const isMatchDay = computed(()=>Boolean(nextMatch.value?.date && gameDate.value && String(nextMatch.value.date)===String(gameDate.value)))
const standings = ref([])
const competitionStandings = ref([])
const competitionProgress = ref(null)
const competitionDetail = ref(null)
const competitionViewMode = ref('table')
const squad = ref([])
const competitions = ref([])
const targets = ref([])
const matches = ref([])
const nextMatch = ref(null)
const newsFeed = ref([])
const historyState = ref({season_recaps:[],season_archive:[],season_dossiers:[],honours:[],club_honours:[],board_history:[],ai_squad_audits:[]})
const latestAiAudit = ref(null)
const jobStatus = ref('active')
const preseason = ref({active:false,label:'Temporada oficial',friendlies:[],pace:'event_driven'})
const marketPeriod = ref({open:true,label:'Mercado',phase:'in_season',activity:'low'})
const clubStatus = ref({score:50,tier:'MEDIO',trend:0,history:[]})
const sourceManager = ref(null)
const venueContext = ref(null)
const storylines = ref([])
const storylineArchive = ref([])
const rivalries = ref([])
const managerWorld = ref({history:[],pressure:{},unemployed_count:0})
const careerRecords = ref({biggest_win:null,biggest_defeat:null,highest_scoring_match:null,longest_win_streak:0,longest_unbeaten_streak:0,matches_managed:0,wins:0,draws:0,losses:0})
const userManager = ref({reputation:50,job_offers:[],tenures:[],current_tenure:{}})
const professionalCareer = ref({employment_status:'employed',reputation:50,reputation_by_country:{},active_contract:{},available_jobs:[],career_offers:[],applications:[],interviews:[],relationships:[],career_memories:[],tenures:[]})
const boardProject = ref({objective:'',philosophy:[],requests:[],sale_pressure:null,support:55})
const informationWorld = ref({threads:[],media_reputation:{credibility:50,pressure:35,relationship:50}})
const dressingRoom = ref({captain_id:null,leaders:[],competitions:[],mentorships:[],recent_events:[]})
const reencounters = ref([])
const staffState = ref({members:[],responsibilities:[],manager_responsibility_count:0,generated_count:0,provenance_note:''})
const scoutingState = ref({active:[],recent_reports:[],responsibility:{}})
const squadPlan = ref({priorities:[],expiring:[],succession:[],surplus:[]})
const trainingState = ref({weekly_plan:[],players:[],session_options:[],intensity_options:[],focus_options:[],recovery_options:[],match_preparation_options:[],responsibility:{},high_risk_count:0,very_high_risk_count:0})
const tacticalPlan = ref({build_up:'balanced',final_third:'mixed',transition:'balanced',familiarity:{overall:62,label:'Asimilando'},individual_instructions:[],opposition_instructions:[],set_piece_takers:{}})
const staffReports = ref({reports:[],urgent_count:0})
const matchBriefing = ref(null)

const selectedCompetitionInfo = computed(()=>competitions.value.find(c=>`${c.kind}:${c.source_id}`===selectedCompetition.value)||null)
const tableWindow = computed(()=>{
 const rows=standings.value
 const index=rows.findIndex(r=>r[8]===controlledTeamId.value)
 if(index<0)return rows.slice(0,7)
 return rows.slice(Math.max(0,index-3),Math.min(rows.length,index+4))
})
const activeNegotiations = computed(()=>[...(marketFlow.value.negotiations||[])].filter(n=>['waiting','countered'].includes(n.status)).reverse())
const openIncomingOffers = computed(()=>[...(marketFlow.value.incoming_offers||[])].filter(o=>o.status==='open').reverse())
const liveEvents = computed(()=>[...(liveMatch.value?.events||[])].slice(-18).reverse())
const controlledLiveHome = computed(()=>Number(liveMatch.value?.home_team_id||0)===controlledTeamId.value)
const liveOwnStats = computed(()=>controlledLiveHome.value?liveMatch.value?.home:liveMatch.value?.away)
const liveOppStats = computed(()=>controlledLiveHome.value?liveMatch.value?.away:liveMatch.value?.home)
function historicalPlayerPhoto(id){return id?`/historical9394/players/${Number(id)}.jpg`:null}
function historicalClubCrest(id){return id?`/historical9394/clubs/${Number(id)}.gif`:null}
function historicalStadiumPhoto(id){return id?`/historical9394/stadiums/${Number(id)}.jpg`:null}
function formatSourceMoney(value){
 if(value==null)return '—'
 return `${Number(value).toLocaleString('es-ES')} ptas.`
}
function formatDateShort(value){
 if(!value)return '—'
 const parts=String(value).split('-');return parts.length===3?`${parts[2]}/${parts[1]}/${parts[0]}`:String(value)
}
function eventLabel(row){return row?.stage || row?.progress?.stage || 'Temporada en curso'}
function trendLabel(value){const n=Number(value||0);return n>0?`▲ +${n}`:n<0?`▼ ${n}`:'● ESTABLE'}
function boardClass(risk){return String(risk||'').includes('ALTO')?'risk-high':risk==='RIESGO'?'risk-danger':risk==='VIGILANCIA'?'risk-watch':'risk-safe'}
function toSquadRow(player){
 const compactStatus = player.status==='Retirado'?'RET.':Number(player.injury_days||0)>0?'LES.':player.league_suspension_active_for_next_match?'SANC.':player.status==='Disponible'?'DISP.':'NO DISP.'
 return {
  id:player.id,n:player.shirt_number??'—',name:player.display_name,pos:player.position,age:player.age??'—',overall:player.overall??'—',
  form:player.form??'—',morale:player.morale??'—',status:compactStatus,nationality:player.nationality,
  contractEnd:player.contract?.end??'—',salary:player.contract?.salary??0,
  profile:player,
 }
}
function standingsFromState(rows){
 return rows.map(r=>[r.team_name,r.played,r.wins,r.draws,r.losses,r.goals_for,r.goals_against,r.points,r.team_id])
}
function marketWorkspaceStorageKey(id=careerId.value){return id?`mister9394-market-workspace:${id}`:''}
function persistMarketWorkspace(){
 const key=marketWorkspaceStorageKey();if(!key)return
 try{window.sessionStorage?.setItem(key,JSON.stringify({query:marketQuery.value,position:marketPosition.value,freeAgents:marketFreeAgents.value,watchedOnly:marketWatchedOnly.value,selectedTargetId:selectedTarget.value?.[5]??null}))}catch{}
}
function restoreMarketWorkspace(id){
 const key=marketWorkspaceStorageKey(id);if(!key)return
 try{
  const raw=JSON.parse(window.sessionStorage?.getItem(key)||'null');if(!raw)return
  marketQuery.value=String(raw.query||'');marketPosition.value=String(raw.position||'');marketFreeAgents.value=Boolean(raw.freeAgents);marketWatchedOnly.value=Boolean(raw.watchedOnly);restoredMarketTargetId.value=raw.selectedTargetId?Number(raw.selectedTargetId):null
 }catch{}
}
function applyCareerState(state){
 if(state.career_id){careerId.value=state.career_id;window.localStorage?.setItem('mister9394-career-id',state.career_id)}
 if(state.game_date)gameDate.value=state.game_date
 if(state.season)careerSeason.value=state.season
 if(state.age_policy)careerAgePolicy.value=state.age_policy
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
 internationalManager.value=state.international_manager||internationalManager.value
 internationalTournaments.value=state.international_tournaments||internationalTournaments.value
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
  width.value=state.tactics.width||width.value;offsideTrap.value=Boolean(state.tactics.offside_trap)
  buildUp.value=state.tactics.build_up||buildUp.value;finalThird.value=state.tactics.final_third||finalThird.value;transition.value=state.tactics.transition||transition.value
 }
 tacticalIdentity.value=state.tactical_identity||tacticalIdentity.value
 economy.value=state.economy||economy.value
 marketFlow.value=state.market_flow||marketFlow.value
 liveMatch.value=state.live_match||null
 lastMatchReport.value=state.last_match_report||lastMatchReport.value
 if(state.news_feed)newsFeed.value=state.news_feed
 if(state.season_recaps||state.season_dossiers)historyState.value={...historyState.value,season_recaps:state.season_recaps||historyState.value.season_recaps,season_dossiers:state.season_dossiers||historyState.value.season_dossiers}
 latestAiAudit.value=state.latest_ai_squad_audit||latestAiAudit.value
 jobStatus.value=state.job_status||'active'
 preseason.value=state.preseason||preseason.value
 marketPeriod.value=state.market_period||state.market_flow?.period||marketPeriod.value
 clubStatus.value=state.club_status||state.manager_dashboard?.club_status||clubStatus.value
 sourceManager.value=state.source_manager||sourceManager.value
 venueContext.value=state.venue||venueContext.value
 if(state.storylines)storylines.value=state.storylines
 if(state.storyline_archive)storylineArchive.value=state.storyline_archive
 if(state.rivalries)rivalries.value=state.rivalries
 if(state.manager_world)managerWorld.value=state.manager_world
 if(state.career_records)careerRecords.value=state.career_records
 if(state.user_manager)userManager.value=state.user_manager
 if(state.professional_career)professionalCareer.value=state.professional_career
 if(state.board_project)boardProject.value=state.board_project
 if(state.information_world)informationWorld.value=state.information_world
 if(state.dressing_room)dressingRoom.value=state.dressing_room
 if(state.reencounters)reencounters.value=state.reencounters
 if(state.staff)staffState.value=state.staff
 if(state.scouting)scoutingState.value=state.scouting
 if(state.squad_plan)squadPlan.value=state.squad_plan
 if(state.training)trainingState.value=state.training
 if(state.tactical_plan){tacticalPlan.value=state.tactical_plan;buildUp.value=state.tactical_plan.build_up||buildUp.value;finalThird.value=state.tactical_plan.final_third||finalThird.value;transition.value=state.tactical_plan.transition||transition.value}
 if(state.staff_reports)staffReports.value=state.staff_reports
 if(Object.prototype.hasOwnProperty.call(state,'match_briefing'))matchBriefing.value=state.match_briefing
}
function calendarRowsForUi(rows,state){
 const teamId=Number(state.team?.source_id||controlledTeamId.value)
 const leagueName=state.team?.league?.name||'Liga'
 return (rows||[]).slice(-8).map(m=>{
  const home=Number(m.home_team_id||0), away=Number(m.away_team_id||0)
  const opponent=home===teamId?(m.away_team||'Rival por confirmar'):away===teamId?(m.home_team||'Rival por confirmar'):'Rival por confirmar'
  const venue=home===teamId?'Casa':away===teamId?'Fuera':'Por confirmar'
  const postponed=Boolean(m.postponed)||String(m.schedule_status||'').toLowerCase()==='postponed'
  const status=m.played?`${m.home_goals}-${m.away_goals}`:postponed?'Aplazado':Number(m.availability_count||0)>0?`Pendiente · ${m.availability_count} baja${Number(m.availability_count)===1?'':'s'}`:'Pendiente'
  return [m.date||`Jornada ${m.matchday}`,opponent,venue,m.competition_name||leagueName,status,m.id]
 })
}
async function refreshCareerData(state){
 const [calendarRows,marketRows,competitionRows,newsRows,careerRows,projectRows,informationRows]=await Promise.all([
  football9394Api.careerCalendar(state.career_id),football9394Api.careerMarket(state.career_id,{query:marketQuery.value,position:marketPosition.value,freeAgents:marketFreeAgents.value,watched:marketWatchedOnly.value,limit:(marketQuery.value||marketPosition.value||marketFreeAgents.value||marketWatchedOnly.value)?30:10}),football9394Api.careerCompetitions(state.career_id),football9394Api.careerNews(state.career_id,{limit:80}),
  football9394Api.professionalCareer(state.career_id),football9394Api.boardProject(state.career_id),football9394Api.informationWorld(state.career_id,80),
 ])
 const recent=calendarRows.filter(m=>m.played).slice(-3);const upcoming=calendarRows.filter(m=>!m.played).slice(0,6)
 matches.value=calendarRowsForUi([...recent,...upcoming],state)
 targets.value=marketRows.map(p=>[p.display_name,p.position,p.team_name,p.overall??'—',p.estimated_transfer_value??0,p.id,p])
 if(restoredMarketTargetId.value){const target=targets.value.find(row=>Number(row[5])===Number(restoredMarketTargetId.value));if(target)chooseTarget(target);restoredMarketTargetId.value=null}
 competitions.value=competitionRows;newsFeed.value=newsRows;professionalCareer.value=careerRows;boardProject.value=projectRows;informationWorld.value=informationRows
 if(!competitionRows.some(c=>`${c.kind}:${c.source_id}`===selectedCompetition.value)&&competitionRows.length)selectedCompetition.value=`${competitionRows[0].kind}:${competitionRows[0].source_id}`
 await loadSelectedCompetitionTable()
}
async function loadHistory(){
 if(!careerId.value)return
 try{historyState.value=await football9394Api.careerHistory(careerId.value)}catch(error){flash(`No se pudo cargar el historial: ${error.message}`)}
}
async function loadHistoricalCareer(){
 loadingHistoricalData.value=true;dataError.value=''
 try{
  const [options,nationalRows]=await Promise.all([football9394Api.careerOptions(),football9394Api.nationalTeams()])
  careerOptions.value=options.leagues||[];nationalTeams.value=nationalRows
  if(careerOptions.value.length){selectedLeagueId.value=careerOptions.value[0].source_id;selectedTeamId.value=careerOptions.value[0].teams?.[0]?.source_id??null}
  let state=null
  const savedId=window.localStorage?.getItem('mister9394-career-id')
  if(savedId){try{state=await football9394Api.career(savedId)}catch{window.localStorage?.removeItem('mister9394-career-id')}}
  if(state){applyCareerState(state);restoreMarketWorkspace(state.career_id);await refreshCareerData(state);await loadHistory();showCareerSetup.value=false;reconcileRouteAfterCareerLoad()}
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
  const state=await football9394Api.createCareer({teamId:Number(selectedTeamId.value),leagueId:Number(selectedLeagueId.value),seed:9394,throughMatchday:0,agePolicy:selectedAgePolicy.value})
  applyCareerState(state);await refreshCareerData(state);await loadHistory();showCareerSetup.value=false;view.value='home'
  flash(`Carrera iniciada · ${state.team.name}`)
 }catch(error){dataError.value=error.message||String(error);flash(`No se pudo crear la carrera: ${dataError.value}`)}
 finally{loadingHistoricalData.value=false}
}
function openCareerSetup(){
 if(liveMatch.value && liveMatch.value.status!=='finished'){
  view.value='match';flash('Termina o resuelve el partido antes de abrir otra carrera.');return
 }
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
async function saveSelection({silent=false}={}){
 if(!careerId.value)return false
 try{
  const result=await football9394Api.updateCareerSelection(careerId.value,{starterIds:lineupDraft.value})
  applyCareerState(result.career);if(!silent)flash('Once y convocatoria guardados.');return true
 }catch(error){flash(`No se pudo guardar el once: ${error.message}`);return false}
}
async function goToTacticsFromSquad(){
 if(lineupDirty.value){const saved=await saveSelection({silent:true});if(!saved)return;flash('Once guardado. Ya puedes ajustar el plan.')}
 view.value='tactics'
}
async function cancelPreviewAndNavigate(target='squad'){
 if(!careerId.value||!liveMatch.value||Number(liveMatch.value.minute||0)!==0){view.value=target;return}
 await withMatchAction(async()=>{
  try{const result=await football9394Api.cancelLivePreview(careerId.value);applyCareerState(result.career);liveMatch.value=null;view.value=target;flash(target==='squad'?'Previa anulada. Puedes modificar el once.':'Previa anulada.')}catch(error){view.value='match';flash(`No se pudo volver a la preparación: ${error.message}`)}
 })
}
async function navigateTo(target){
 if(matchActionBusy.value && liveMatch.value){view.value='match';flash('Hay una acción de partido en curso.');return}
 if(liveMatch.value && liveMatch.value.status!=='finished'){
  const minute=Number(liveMatch.value.minute||0)
  if(minute>0 && !['match','tactics'].includes(target)){view.value='match';flash('El partido está en juego. Usa Directo, Táctica o Cambios hasta el final.');return}
  if(minute===0 && !['match','tactics'].includes(target)){await cancelPreviewAndNavigate(target);return}
 }
 view.value=target
}
async function appointCaptain(player){
 if(!careerId.value)return
 try{const result=await football9394Api.setCaptain(careerId.value,Number(player.id));applyCareerState(result.career);flash(`${player.name} es el nuevo capitán.`)}catch(error){flash(`No se pudo cambiar la capitanía: ${error.message}`)}
}
async function assignStaffResponsibility(payload){
 if(!careerId.value||!payload?.key||!payload?.assignee)return
 try{
  const result=await football9394Api.assignStaffResponsibility(careerId.value,payload.key,payload.assignee)
  applyCareerState(result.career)
  flash('Responsabilidad actualizada.')
 }catch(error){flash(`No se pudo cambiar la responsabilidad: ${error.message}`)}
}
async function saveTrainingPlan(payload){
 if(!careerId.value)return
 try{const result=await football9394Api.updateTraining(careerId.value,{intensity:payload?.intensity,weeklyPlan:payload?.weekly_plan});applyCareerState(result.career);flash('Plan semanal de entrenamiento guardado.')}catch(error){flash(`No se pudo guardar el entrenamiento: ${error.message}`)}
}
async function setTrainingFocus(payload){
 if(!careerId.value||!payload?.playerId)return
 try{const result=await football9394Api.setTrainingFocus(careerId.value,payload.playerId,payload.focus);applyCareerState(result.career);flash('Trabajo individual actualizado.')}catch(error){flash(`No se pudo cambiar el foco: ${error.message}`)}
}
async function setTrainingRecovery(payload){
 if(!careerId.value||!payload?.playerId)return
 try{const result=await football9394Api.setTrainingRecovery(careerId.value,payload.playerId,payload.recovery);applyCareerState(result.career);flash('Recuperación individual actualizada.')}catch(error){flash(`No se pudo cambiar la recuperación: ${error.message}`)}
}
async function setMatchPreparation(focus){
 if(!careerId.value)return
 try{const result=await football9394Api.setMatchPreparation(careerId.value,focus);applyCareerState(result.career);flash('Preparación del rival actualizada.')}catch(error){flash(`No se pudo cambiar la preparación: ${error.message}`)}
}
async function saveTacticalPhase(payload){
 if(!careerId.value)return
 try{const result=await football9394Api.updateTacticalPlan(careerId.value,payload);applyCareerState(result.career);flash('Plan por fases actualizado.')}catch(error){flash(`No se pudo actualizar el plan: ${error.message}`)}
}
async function setTacticalPlayerInstruction(payload){
 if(!careerId.value||!payload?.playerId)return
 try{const result=await football9394Api.setTacticalPlayerInstruction(careerId.value,payload.playerId,payload.instruction||{});applyCareerState(result.career);flash('Instrucción individual guardada.')}catch(error){flash(`No se pudo guardar la instrucción: ${error.message}`)}
}
async function setOppositionInstruction(payload){
 if(!careerId.value||!payload?.playerId)return
 try{const result=await football9394Api.setOppositionInstruction(careerId.value,payload.playerId,payload.instruction||{});applyCareerState(result.career);flash('Instrucción sobre el rival guardada.')}catch(error){flash(`No se pudo preparar al rival: ${error.message}`)}
}
async function setSetPieceTaker(payload){
 if(!careerId.value||!payload?.kind)return
 try{const result=await football9394Api.setSetPieceTaker(careerId.value,payload.kind,payload.playerId||null);applyCareerState(result.career);flash('Lanzador actualizado.')}catch(error){flash(`No se pudo cambiar el lanzador: ${error.message}`)}
}
async function respondDressingConcern(payload){
 if(!careerId.value||!payload?.id)return
 try{const result=await football9394Api.respondDressingConcern(careerId.value,payload.id,payload.response);applyCareerState(result.career);flash('Situación de vestuario gestionada.')}catch(error){flash(`No se pudo gestionar: ${error.message}`)}
}
async function disciplineSquadPlayer(payload){
 if(!careerId.value||!payload?.playerId)return
 try{const result=await football9394Api.disciplinePlayer(careerId.value,payload.playerId,payload.action);applyCareerState(result.career);flash('Decisión disciplinaria registrada.')}catch(error){flash(`No se pudo aplicar la medida: ${error.message}`)}
}
async function applyPlanNeed(need){
 marketQuery.value=''
 marketPosition.value=need?.market_position||''
 await searchMarket()
 flash(need?.market_position?`Buscando ${need.label.toLowerCase()} según el plan de plantilla.`:'Mostrando mercado para ampliar la profundidad de plantilla.')
}
async function autoSelectLineup(){
 if(!careerId.value)return
 try{const result=await football9394Api.updateCareerSelection(careerId.value,{autoSelect:true});applyCareerState(result.career);flash('Mejor once disponible seleccionado.')}catch(error){flash(`No se pudo seleccionar el once: ${error.message}`)}
}
function playerNameById(id){const own=squad.value.find(p=>Number(p.id)===Number(id));if(own)return own.name;const target=targets.value.find(p=>Number(p[5])===Number(id));return target?.[0]||`Jugador #${id}`}
async function openDecision(decision){if(decision?.action)await navigateTo(decision.action)}
function flash(message){notice.value=message;window.setTimeout(()=>{notice.value=''},2200)}
async function openPlayer(row){
 selectedPlayer.value=profileFor(row);playerTab.value='profile'
 if(!careerId.value||!row?.id)return
 try{const detail=await football9394Api.careerPlayer(careerId.value,row.id);selectedPlayer.value={...detail,photo_url:historicalPlayerPhoto(detail.id),team_crest_url:historicalClubCrest(detail.team_id),market_value_display:detail.transfer_value_is_exact?formatSourceMoney(detail.estimated_transfer_value):`≈ ${formatSourceMoney(detail.estimated_transfer_value)}`}}catch{}
}
async function promisePlayerRole(payload){
 if(!careerId.value||!payload?.player?.id||!payload?.role)return
 try{
  const result=await football9394Api.setRolePromise(careerId.value,payload.player.id,payload.role)
  applyCareerState(result.career)
  const detail=result.player||await football9394Api.careerPlayer(careerId.value,payload.player.id)
  selectedPlayer.value={...detail,photo_url:historicalPlayerPhoto(detail.id),team_crest_url:historicalClubCrest(detail.team_id),market_value_display:formatSourceMoney(detail.estimated_transfer_value)}
  flash(`Rol acordado con ${detail.display_name||detail.name}: ${payload.role}.`)
 }catch(error){flash(`No se pudo acordar el rol: ${error.message}`)}
}
async function advance(){
 if(isAdvancing.value)return
 if(liveMatch.value){view.value='match';flash('Tienes un partido en directo pendiente.');return}
 if(!careerId.value){flash('La carrera todavía no está lista.');return}
 if(jobStatus.value==='dismissed'){view.value='career';flash('Estás sin club. Elige un nuevo proyecto para continuar tu carrera.');return}
 isAdvancing.value=true
 try{
  const result=await football9394Api.advanceCareerUntilEvent(careerId.value,14)
  applyCareerState(result.career);await refreshCareerData(result.career)
  if(result.world_events?.some(e=>e.kind==='season_rollover')){
   await loadHistory()
   seasonEndRecap.value=historyState.value.season_recaps?.slice(-1)[0]||null
  }
  if(result.career_over){view.value='career';flash('El consejo ha terminado tu etapa en el club.');return}
  if(result.requires_match&&result.next_match)flash(`DÍA DE PARTIDO · ${result.next_match.home_team} - ${result.next_match.away_team}`)
  else if(result.advanced_days>1)flash(`Continuado ${result.advanced_days} días · ${result.date}`)
  else flash(`Día avanzado · ${result.date}`)
 }catch(error){flash(`No se pudo avanzar: ${error.message}`)}
 finally{isAdvancing.value=false}
}

async function acceptManagerJob(offerId){
 if(!careerId.value)return
 try{const state=await football9394Api.acceptManagerJob(careerId.value,offerId);applyCareerState(state);await refreshCareerData(state);view.value='home';flash(`Nueva etapa: ${state.team?.name||'club aceptado'}.`)}catch(error){flash(`No se pudo aceptar el banquillo: ${error.message}`)}
}
async function applyManagerJob(opportunityId){
 if(!careerId.value)return
 try{const result=await football9394Api.applyManagerJob(careerId.value,opportunityId);professionalCareer.value=result.professional_career||professionalCareer.value;const passed=Boolean(result.passed);flash(passed?'Entrevista superada: tienes una oferta sobre la mesa.':'El club ha elegido otro perfil para este proyecto.')}catch(error){flash(`No se pudo presentar la candidatura: ${error.message}`)}
}
async function resignManagerJob(){
 if(!careerId.value)return
 try{const result=await football9394Api.resignManagerJob(careerId.value);const state=result.career;applyCareerState(state);await refreshCareerData(state);view.value='career';flash('Etapa cerrada. Tu historial y reputación continúan contigo.')}catch(error){flash(`No se pudo dimitir: ${error.message}`)}
}
async function requestBoardProject(requestType){
 if(!careerId.value)return
 try{const result=await football9394Api.boardRequest(careerId.value,requestType);if(result.career)applyCareerState(result.career);boardProject.value=result.project||boardProject.value;economy.value=result.economy||economy.value;flash(result.request?.status==='accepted'?'El consejo acepta la petición.':`El consejo rechaza la petición: ${result.request?.reason||'sin margen suficiente'}.`)}catch(error){flash(`No se pudo elevar la petición: ${error.message}`)}
}

function currentTactics(){return {formation:formation.value,mentality:mentality.value,tempo:tempo.value,pressing:pressing.value,directness:directness.value,defensive_line:defensiveLine.value,marking:marking.value,width:width.value,offside_trap:Boolean(offsideTrap.value),build_up:buildUp.value,final_third:finalThird.value,transition:transition.value}}
async function saveTactics(){
 if(!careerId.value)return
 try{const result=await football9394Api.updateCareerTactics(careerId.value,currentTactics());applyCareerState(result.career);flash('Táctica guardada. Sus efectos se aplicarán al próximo minuto jugado.')}catch(error){flash(`No se pudo guardar la táctica: ${error.message}`)}
}
async function withMatchAction(task){
 if(matchActionBusy.value)return null
 matchActionBusy.value=true
 try{return await task()}finally{matchActionBusy.value=false}
}
async function startLive(){
 if(!careerId.value||!nextMatch.value){flash('No hay partido disponible.');return}
 if(!isMatchDay.value){flash(`La previa se abre el día del partido (${formatDateShort(nextMatch.value.date)}). Mientras tanto puedes preparar XI y táctica.`);return}
 if(lineupDirty.value){const saved=await saveSelection({silent:true});if(!saved){view.value='squad';return}}
 if(!selection.value?.valid){view.value='squad';flash('El once debe ser legal antes de abrir la previa.');return}
 await withMatchAction(async()=>{
  try{await football9394Api.updateCareerTactics(careerId.value,currentTactics());const result=await football9394Api.startLiveMatch(careerId.value);applyCareerState(result.career);liveMatch.value=result.match;view.value='match';flash('Previa preparada. Revisa los dos onces y decide si jugar o ver el resultado.')}catch(error){flash(`No se pudo abrir la previa: ${error.message}`)}
 })
}
async function commitFinishedLiveMatch(){
 if(!careerId.value||!liveMatch.value||liveMatch.value.status!=='finished'||liveMatch.value.committed)return
 const result=await football9394Api.finishLiveMatch(careerId.value)
 lastMatchReport.value=result.match;applyCareerState(result.career);liveMatch.value=result.match;await refreshCareerData(result.career)
}
async function advanceLive(minutes=5){
 if(!careerId.value||!liveMatch.value)return
 await withMatchAction(async()=>{
  try{const result=await football9394Api.advanceLiveMatch(careerId.value,minutes);applyCareerState(result.career);liveMatch.value=result.match;if(result.match?.status==='finished')await commitFinishedLiveMatch()}catch(error){flash(`Directo detenido: ${error.message}`)}
 })
}
async function advanceToChance(){
 if(!liveMatch.value||liveMatch.value.status==='finished')return
 const notable=new Set(['shot_off','save','goal','corner','yellow','red','second_yellow_red','injury','injury_forced_off','halftime','fulltime'])
 await withMatchAction(async()=>{
  try{for(let i=0;i<20;i++){const before=(liveMatch.value.events||[]).length;const result=await football9394Api.advanceLiveMatch(careerId.value,1);applyCareerState(result.career);liveMatch.value=result.match;const fresh=(liveMatch.value.events||[]).slice(before);if(fresh.some(e=>notable.has(e.kind))||liveMatch.value.status!=='live')break}if(liveMatch.value?.status==='finished')await commitFinishedLiveMatch()}catch(error){flash(`Directo detenido: ${error.message}`)}
 })
}
async function applyLiveTactics(){
 if(!careerId.value||!liveMatch.value)return
 await withMatchAction(async()=>{
  try{const result=await football9394Api.updateLiveTactics(careerId.value,currentTactics());liveMatch.value=result.match||result;view.value='match';flash(`Ajuste aplicado en el ${liveMatch.value.minute}'`)}catch(error){flash(`No se pudo cambiar la táctica: ${error.message}`)}
 })
}
async function makeLiveSubstitution(){
 if(!liveOutgoingId.value||!liveIncomingId.value){flash('Selecciona quién sale y quién entra.');return}
 await withMatchAction(async()=>{
  try{const result=await football9394Api.liveSubstitution(careerId.value,Number(liveOutgoingId.value),Number(liveIncomingId.value));liveMatch.value=result.match||result;liveOutgoingId.value=null;liveIncomingId.value=null;flash('Cambio realizado.')}catch(error){flash(`Cambio no válido: ${error.message}`)}
 })
}
async function closeLiveMatch(){
 if(liveMatch.value?.committed){lastMatchReport.value=liveMatch.value;liveMatch.value=null;view.value='home';flash('Postpartido cerrado.');return}
 await withMatchAction(async()=>{
  try{const result=await football9394Api.finishLiveMatch(careerId.value);lastMatchReport.value=result.match;applyCareerState(result.career);await refreshCareerData(result.career);view.value='home';flash(`FINAL · ${result.match.home_team_name} ${result.match.home.goals}-${result.match.away.goals} ${result.match.away_team_name}`)}catch(error){flash(`No se pudo cerrar el partido: ${error.message}`)}
 })
}
async function simulateFromPreview(){
 if(!careerId.value||!liveMatch.value||Number(liveMatch.value.minute||0)!==0){flash('El resultado instantáneo sólo está disponible en la previa.');return}
 await withMatchAction(async()=>{
  try{const result=await football9394Api.simulateLiveMatch(careerId.value);applyCareerState(result.career);lastMatchReport.value=result.match;liveMatch.value=result.match;await refreshCareerData(result.career);view.value='match';flash(`FINAL · ${result.match.home_team_name} ${result.match.home.goals}-${result.match.away.goals} ${result.match.away_team_name}`)}catch(error){flash(`No se pudo simular: ${error.message}`)}
 })
}
function chooseTarget(row){
 selectedTarget.value=row
 transferFee.value=Math.round(Number(row[4]||0)*0.9)
 transferSalary.value=Number(row[6]?.contract?.salary||row[6]?.market?.minimum_salary_hint||0)
 transferYears.value=3
 persistMarketWorkspace()
}
async function searchMarket(){
 if(!careerId.value)return
 try{const rows=await football9394Api.careerMarket(careerId.value,{query:marketQuery.value,limit:30,position:marketPosition.value,freeAgents:marketFreeAgents.value,watched:marketWatchedOnly.value});targets.value=rows.map(p=>[p.display_name,p.position,p.team_name||'Libre',p.overall??'—',p.estimated_transfer_value??p.market?.market_value??0,p.id,p]);persistMarketWorkspace()}catch(error){flash(`Búsqueda fallida: ${error.message}`)}
}
async function toggleWatch(target){
 try{const watched=!Boolean(target[6]?.watched);const result=await football9394Api.watchPlayer(careerId.value,target[5],watched);applyCareerState(result.career);target[6].watched=watched;flash(watched?'Añadido a seguimiento.':'Eliminado del seguimiento.')}catch(error){flash(`No se pudo actualizar seguimiento: ${error.message}`)}
}

async function scoutMarketPlayer(playerOrTarget){
 if(!careerId.value)return
 const id=Number(Array.isArray(playerOrTarget)?playerOrTarget[5]:playerOrTarget?.id)
 if(!id)return
 try{
  const result=await football9394Api.scoutPlayer(careerId.value,id)
  applyCareerState(result.career)
  if(selectedPlayer.value?.id===id){
   const detail=await football9394Api.careerPlayer(careerId.value,id)
   selectedPlayer.value={...detail,photo_url:historicalPlayerPhoto(detail.id),team_crest_url:historicalClubCrest(detail.team_id),market_value_display:detail.transfer_value_is_exact?formatSourceMoney(detail.estimated_transfer_value):`≈ ${formatSourceMoney(detail.estimated_transfer_value)}`}
  }
  await searchMarket()
  flash(`Informe encargado · previsto ${formatDateShort(result.assignment.due_on)}.`)
 }catch(error){flash(`No se pudo encargar el informe: ${error.message}`)}
}
async function inquireMarketPlayer(playerOrTarget){
 if(!careerId.value)return
 const id=Number(Array.isArray(playerOrTarget)?playerOrTarget[5]:playerOrTarget?.id)
 if(!id)return
 try{const result=await football9394Api.marketInquiry(careerId.value,id);applyCareerState(result.career);flash(`Consulta: ${result.inquiry.note}`)}catch(error){flash(`No se pudo consultar: ${error.message}`)}
}
async function withdrawNegotiation(row){
 try{const result=await football9394Api.withdrawNegotiation(careerId.value,row.id);applyCareerState(result.career);flash('Negociación retirada.')}catch(error){flash(`No se pudo retirar: ${error.message}`)}
}
async function submitTransfer(){
 if(!selectedTarget.value||!careerId.value)return
 try{const result=await football9394Api.openNegotiation(careerId.value,{playerId:selectedTarget.value[5],feeOffer:Number(transferFee.value),salaryOffer:Number(transferSalary.value),contractYears:Number(transferYears.value),squadRole:transferSquadRole.value,signingBonus:Number(transferSigningBonus.value||0),releaseClause:transferReleaseClause.value?Number(transferReleaseClause.value):null,dealType:transferDealType.value,loanWageShare:Number(transferLoanWageShare.value||0)});applyCareerState(result.career);selectedTarget.value=null;persistMarketWorkspace();flash(`Oferta enviada · respuesta prevista ${result.negotiation.response_date}`)}catch(error){flash(`Negociación fallida: ${error.message}`)}
}
async function counterNegotiation(row){
 try{const result=await football9394Api.counterNegotiation(careerId.value,row.id,{feeOffer:Number(row.counter_fee??row.fee_offer),salaryOffer:Number(row.counter_salary??row.salary_offer),contractYears:Number(row.contract_years||3),loanWageShare:row.deal_type==='loan'?Number(row.counter_wage_share??row.loan_wage_share??100):null});applyCareerState(result.career);flash(`Contraoferta enviada · respuesta ${result.negotiation.response_date}`)}catch(error){flash(`No se pudo responder: ${error.message}`)}
}
async function toggleTransferListing(row){
 try{const listed=Boolean(row.profile?.transfer_listed);const result=listed?await football9394Api.unlistPlayer(careerId.value,row.id):await football9394Api.listPlayer(careerId.value,row.id,Number(row.profile?.estimated_transfer_value||0));applyCareerState(result.career);flash(listed?'Jugador retirado del mercado.':'Jugador puesto en el mercado.')}catch(error){flash(`No se pudo cambiar su situación: ${error.message}`)}
}
async function acceptIncomingOffer(offer){
 try{const result=await football9394Api.acceptIncomingOffer(careerId.value,offer.id);applyCareerState(result.career);await refreshCareerData(result.career);flash(`Venta cerrada por ${formatSourceMoney(result.transfer.fee)}`)}catch(error){flash(`No se pudo aceptar: ${error.message}`)}
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
  selectedNationalTeam.value={...team,...data}
  nationalSquad.value=data.squad||[]
 }catch(error){flash(`No se pudo cargar la selección: ${error.message}`)}
}
async function acceptNationalJob(offerId){
 if(!careerId.value)return
 try{const result=await football9394Api.acceptNationalJob(careerId.value,offerId);applyCareerState(result.career);const country=nationalTeams.value.find(row=>Number(row.country_id)===Number(result.career.international_manager?.country_id));if(country)await openNationalTeam(country);flash(`Seleccionador de ${result.career.international_manager?.country_name||'la selección'}.`)}catch(error){flash(`No se pudo aceptar la selección: ${error.message}`)}
}
async function resignNationalJob(){
 if(!careerId.value)return
 try{const result=await football9394Api.resignNationalJob(careerId.value);applyCareerState(result.career);flash('Has dejado el cargo de seleccionador.')}catch(error){flash(`No se pudo dejar la selección: ${error.message}`)}
}
async function autoNationalSelection(){
 if(!careerId.value)return
 try{const result=await football9394Api.autoNationalSelection(careerId.value);applyCareerState(result.career);const country=nationalTeams.value.find(row=>Number(row.country_id)===Number(result.career.international_manager?.country_id));if(country)await openNationalTeam(country);flash('Convocatoria de 22 jugadores actualizada.')}catch(error){flash(`No se pudo actualizar la convocatoria: ${error.message}`)}
}

async function loadSelectedCompetitionTable(){
 if(!careerId.value||!selectedCompetition.value)return
 const [kind,id]=String(selectedCompetition.value).split(':')
 try{
  const data=await football9394Api.careerCompetition(careerId.value,kind,Number(id))
  competitionDetail.value=data;competitionStandings.value=data.standings||[];competitionProgress.value=data
  if(!competitionStandings.value.length&&competitionViewMode.value==='table')competitionViewMode.value='results'
 }catch(error){competitionStandings.value=[];competitionProgress.value=null;competitionDetail.value=null;flash(`No se pudo abrir la competición: ${error.message}`)}
}
const selectedCompetitionRuntime = computed(()=>competitionDetail.value)
const latestNews = computed(()=>newsFeed.value.slice(0,5))
const newsCategories = computed(()=>['Todas',...new Set(newsFeed.value.map(n=>n.category).filter(Boolean))])
const newsCategory = ref('Todas')
const filteredNews = computed(()=>newsCategory.value==='Todas'?newsFeed.value:newsFeed.value.filter(n=>n.category===newsCategory.value))
const latestRecap = computed(()=>historyState.value.season_recaps?.slice(-1)[0]||null)
const currentBoard = computed(()=>managerDashboard.value.board||{score:null,label:managerDashboard.value.board_confidence,risk:'ESTABLE',reasons:[],components:{}})
const competitionRecentResults = computed(()=>[...(competitionDetail.value?.results||[])].slice(-24).reverse())
const competitionCalendarRows = computed(()=>[...(competitionDetail.value?.calendar||[])].filter(r=>!r.played).slice(0,28))
const competitionHonours = computed(()=>[...(competitionDetail.value?.honours||[])].reverse())
const selectedNationalHistory = computed(()=>{
 const id=selectedNationalTeam.value?.country_id
 if(!id)return []
 return internationalHistory.value.filter(m=>m.home_country_id===id||m.away_country_id===id).slice(-6).reverse()
})
function handleShortcut(event){
 if(event.ctrlKey||event.metaKey||event.altKey)return
 const tag=String(event.target?.tagName||'').toLowerCase();if(['input','select','textarea','button'].includes(tag))return
 const key=String(event.key||'').toLowerCase()
 const routes={i:'home',p:'squad',t:'tactics',m:'market',f:'staff',g:'competitions',a:'calendar',n:'news',e:'economy',s:'national',h:'history',r:'career'}
 if(key==='c'||key===' '){event.preventDefault();advance()}
 else if(routes[key])navigateTo(routes[key])
}
const validViews=new Set(navigationGroups.flatMap(group=>group.items.map(item=>item.id)).concat(['match']))
let syncingHistory=false
function replaceRoute(target){
 syncingHistory=true;view.value=target;window.history.replaceState({view:target},'',`#${target}`);queueMicrotask(()=>{syncingHistory=false})
}
function reconcileRouteAfterCareerLoad(){
 const route=String(window.location.hash||'').replace(/^#/,'')
 if(liveMatch.value && liveMatch.value.status!=='finished'){
  const minute=Number(liveMatch.value.minute||0)
  if(minute>0 && !['match','tactics'].includes(route)){replaceRoute('match');flash('Partido recuperado tras recargar. Continúa desde el directo.');return}
  if(minute===0 && !['match','tactics'].includes(route)){replaceRoute('match');flash('Previa recuperada tras recargar. Puedes revisar XI o táctica antes de empezar.');return}
 }
 if(route==='match' && !liveMatch.value){
  if(lastMatchReport.value?.committed){liveMatch.value=lastMatchReport.value;replaceRoute('match');return}
  replaceRoute('home');return
 }
 if(route && validViews.has(route))view.value=route
}
async function applyRouteFromLocation(){
 const route=String(window.location.hash||'').replace(/^#/,'')
 if(!route||!validViews.has(route)||route===view.value)return
 if(matchActionBusy.value && liveMatch.value){replaceRoute('match');flash('Hay una acción de partido en curso.');return}
 if(liveMatch.value && liveMatch.value.status!=='finished'){
  const minute=Number(liveMatch.value.minute||0)
  if(minute>0 && !['match','tactics'].includes(route)){replaceRoute('match');flash('El partido está en juego. Usa Directo, Táctica o Cambios hasta el final.');return}
  if(minute===0 && !['match','tactics'].includes(route)){
   syncingHistory=true
   await cancelPreviewAndNavigate(route)
   window.history.replaceState({view:route},'',`#${route}`)
   queueMicrotask(()=>{syncingHistory=false})
   return
  }
 }
 syncingHistory=true;view.value=route;queueMicrotask(()=>{syncingHistory=false})
}
watch(selectedLeagueId,()=>{const league=selectedLeagueOption.value;selectedTeamId.value=league?.teams?.[0]?.source_id??null})
watch(selectedCompetition,loadSelectedCompetitionTable)
watch(careerId,()=>{if(careerId.value)loadSelectedCompetitionTable()})
watch([marketQuery,marketPosition,marketFreeAgents,marketWatchedOnly],persistMarketWorkspace)
watch(view,next=>{
 if(syncingHistory||!validViews.has(next))return
 const hash=`#${next}`
 if(window.location.hash!==hash)window.history.pushState({view:next},'',hash)
})
onMounted(()=>{
 applyRouteFromLocation();loadHistoricalCareer()
 window.addEventListener('keydown',handleShortcut)
 window.addEventListener('popstate',applyRouteFromLocation)
 window.addEventListener('hashchange',applyRouteFromLocation)
})
onBeforeUnmount(()=>{
 window.removeEventListener('keydown',handleShortcut)
 window.removeEventListener('popstate',applyRouteFromLocation)
 window.removeEventListener('hashchange',applyRouteFromLocation)
})
</script>

<template>
<div class="m9394-shell">
  <CareerSetup
    v-if="showCareerSetup"
    :career-options="careerOptions"
    :selected-league-id="selectedLeagueId"
    :selected-team-id="selectedTeamId" :age-policy="selectedAgePolicy"
    :loading="loadingHistoricalData"
    :current-career-id="careerId"
    :error="dataError"
    @update:selected-league-id="selectedLeagueId=$event"
    @update:selected-team-id="selectedTeamId=$event"
    @update:age-policy="selectedAgePolicy=$event"
    @start="startCareer"
    @back="showCareerSetup=false"
  />
  <template v-else>
  <div class="manager-layout">
    <ManagerSidebar
      :groups="navigationGroups"
      :active="view"
      :club="controlledTeam"
      :season="careerSeason"
      :crest-url="historicalClubCrest(controlledTeamId)"
      @navigate="navigateTo"
      @new-career="openCareerSetup"
    />
    <div class="manager-main">
      <ManagerTopbar
        :title="sectionTitle"
        :date="currentDate"
        :matchday="currentMatchday"
        :pending-count="managerDashboard.pending_decisions?.length || 0"
        :preseason="preseason.active"
        :busy="isAdvancing"
        @advance="advance"
      />

  <main class="m9394-workspace"><div v-if="dataError" class="data-error">Error de datos: {{dataError}}</div>
    <HomeDashboard
      v-if="view==='home'"
      :next-match="nextMatch"
      :season="careerSeason"
      :controlled-team-id="controlledTeamId"
      :loading="loadingHistoricalData"
      :team="controlledTeam"
      :squad="squad"
      :preseason="preseason"
      :market-period="marketPeriod"
      :club-status="clubStatus"
      :table-window="tableWindow"
      :standings="standings"
      :dashboard="managerDashboard"
      :latest-news="latestNews"
      :current-board="currentBoard"
      :storylines="storylines"
      :rivalries="rivalries"
      :selection="selection"
      :formation="formation"
      :game-date="gameDate"
      :lineup-dirty="lineupDirty"
      @navigate="navigateTo"
      @start-live="startLive"
      @continue="advance"
    />

    <SquadWorkspace
      v-else-if="view==='squad'"
      :squad="squad"
      :lineup-draft="lineupDraft"
      :lineup-players="lineupDraftPlayers"
      :formation="formation"
      :selection="selection"
      :dressing-room="dressingRoom"
      @toggle-starter="toggleStarter"
      @open-player="openPlayer"
      @renew="renewPlayer"
      @toggle-listing="toggleTransferListing"
      @auto-select="autoSelectLineup"
      @save-selection="saveSelection"
      @open-tactics="goToTacticsFromSquad"
      @set-captain="appointCaptain"
      @respond-concern="respondDressingConcern"
      @discipline="disciplineSquadPlayer"
    />

    <StaffWorkspace
      v-else-if="view==='staff'"
      :staff="staffState"
      :reports="staffReports"
      @assign="assignStaffResponsibility"
      @open-action="navigateTo"
    />

    <TrainingWorkspace
      v-else-if="view==='training'"
      :training="trainingState"
      @save-plan="saveTrainingPlan"
      @set-focus="setTrainingFocus"
      @set-recovery="setTrainingRecovery"
      @set-match-preparation="setMatchPreparation"
      @open-staff="navigateTo('staff')"
    />

    <TacticsWorkspace
      v-else-if="view==='tactics'"
      :formation="formation"
      :mentality="mentality"
      :tempo="tempo"
      :pressing="pressing"
      :directness="directness"
      :defensive-line="defensiveLine"
      :marking="marking"
      :width="width"
      :offside-trap="offsideTrap"
      :identity="tacticalIdentity"
      :plan="tacticalPlan"
      :briefing="matchBriefing"
      :players="lineupDraftPlayers"
      :live="Boolean(liveMatch)"
      :live-status="liveMatch?.status || ''"
      :live-minute="Number(liveMatch?.minute || 0)"
      :next-match="nextMatch"
      :game-date="gameDate"
      :selection="selection"
      :busy="matchActionBusy"
      :controlled-team-id="controlledTeamId"
      @update:formation="formation=$event"
      @update:mentality="mentality=$event"
      @update:tempo="tempo=$event"
      @update:pressing="pressing=$event"
      @update:directness="directness=$event"
      @update:defensive-line="defensiveLine=$event"
      @update:marking="marking=$event"
      @update:width="width=$event"
      @update:offside-trap="offsideTrap=$event"
      @save="saveTactics"
      @save-phase="saveTacticalPhase"
      @set-player-instruction="setTacticalPlayerInstruction"
      @set-opposition-instruction="setOppositionInstruction"
      @set-piece-taker="setSetPieceTaker"
      @apply-live="applyLiveTactics"
      @open-squad="cancelPreviewAndNavigate('squad')"
      @start-live="startLive"
    />

    <LiveMatchWorkspace
      v-else-if="view==='match'"
      :match="liveMatch"
      :season="careerSeason"
      :formation="formation"
      :tactical-identity="tacticalIdentity"
      :events="liveEvents"
      :outgoing-id="liveOutgoingId"
      :incoming-id="liveIncomingId"
      :league-name="controlledTeam.league?.name || ''"
      :busy="matchActionBusy"
      :dashboard="managerDashboard"
      :next-match="nextMatch"
      @update:outgoing-id="liveOutgoingId=$event"
      @update:incoming-id="liveIncomingId=$event"
      @advance="advanceLive"
      @chance="advanceToChance"
      @simulate="simulateFromPreview"
      @close="closeLiveMatch"
      @substitute="makeLiveSubstitution"
      @open-tactics="view='tactics'"
      @edit-lineup="cancelPreviewAndNavigate('squad')"
      @back="view='home'"
    />


    <CompetitionsWorkspace
      v-else-if="view==='competitions'"
      :selected-competition="selectedCompetition"
      :competitions="competitions"
      :detail="competitionDetail"
      :view-mode="competitionViewMode"
      :standings="competitionStandings"
      :recent-results="competitionRecentResults"
      :calendar-rows="competitionCalendarRows"
      :honours="competitionHonours"
      :controlled-team-id="controlledTeamId"
      :season="careerSeason"
      :crest-for="historicalClubCrest"
      :format-date="formatDateShort"
      :event-label="eventLabel"
      @update:selected-competition="selectedCompetition=$event"
      @update:view-mode="competitionViewMode=$event"
    />

    <MarketWorkspace
      v-else-if="view==='market'"
      :period="marketPeriod"
      :query="marketQuery"
      :position="marketPosition"
      :free-agents="marketFreeAgents"
      :watched-only="marketWatchedOnly"
      :targets="targets"
      :selected-target="selectedTarget"
      :transfer-fee="transferFee"
      :transfer-salary="transferSalary"
      :transfer-years="transferYears"
      :transfer-squad-role="transferSquadRole"
      :transfer-signing-bonus="transferSigningBonus"
      :transfer-release-clause="transferReleaseClause"
      :transfer-deal-type="transferDealType"
      :transfer-loan-wage-share="transferLoanWageShare"
      :transfer-room="economy.transfer_room"
      :market-flow="marketFlow"
      :active-negotiations="activeNegotiations"
      :incoming-offers="openIncomingOffers"
      :own-squad="squad"
      :scouting="scoutingState"
      :squad-plan="squadPlan"
      @update:query="marketQuery=$event"
      @update:position="marketPosition=$event"
      @update:free-agents="marketFreeAgents=$event"
      @update:watched-only="marketWatchedOnly=$event"
      @update:transfer-fee="transferFee=$event"
      @update:transfer-salary="transferSalary=$event"
      @update:transfer-years="transferYears=$event"
      @update:transfer-squad-role="transferSquadRole=$event"
      @update:transfer-signing-bonus="transferSigningBonus=$event"
      @update:transfer-release-clause="transferReleaseClause=$event"
      @update:transfer-deal-type="transferDealType=$event"
      @update:transfer-loan-wage-share="transferLoanWageShare=$event"
      @search="searchMarket"
      @apply-plan="applyPlanNeed"
      @watch="toggleWatch"
      @scout="scoutMarketPlayer"
      @inquire="inquireMarketPlayer"
      @open-player="openPlayer"
      @choose-target="chooseTarget"
      @submit="submitTransfer"
      @counter="counterNegotiation"
      @withdraw="withdrawNegotiation"
      @accept-offer="acceptIncomingOffer"
    />


    <EconomyWorkspace
      v-else-if="view==='economy'"
      :economy="economy"
      :format-money="formatSourceMoney"
      @open-player="openPlayer"
    />

    <NewsWorkspace
      v-else-if="view==='news'"
      :categories="newsCategories"
      :category="newsCategory"
      :news="filteredNews"
      :manager-world="managerWorld"
      :information-world="informationWorld"
      :format-date="formatDateShort"
      @update:category="newsCategory=$event"
    />


    <NationalWorkspace
      v-else-if="view==='national'"
      :teams="nationalTeams"
      :selected-team="selectedNationalTeam"
      :squad="nationalSquad"
      :history="selectedNationalHistory"
      :manager="internationalManager"
      :tournaments="internationalTournaments"
      :format-date="formatDateShort"
      @select-team="openNationalTeam"
      @open-player="openPlayer({id:$event.id,name:$event.display_name,profile:$event})"
      @accept-job="acceptNationalJob"
      @resign-job="resignNationalJob"
      @auto-selection="autoNationalSelection"
    />

    <ClubWorkspace
      v-else-if="view==='club'"
      :team="controlledTeam"
      :controlled-team-id="controlledTeamId"
      :season="careerSeason"
      :squad="squad"
      :lineup-players="lineupDraftPlayers"
      :formation="formation"
      :tactical-identity="tacticalIdentity"
      :standings="standings"
      :next-match="nextMatch"
      :source-manager="sourceManager"
      :venue="venueContext"
      :finances="finances"
      :club-status="clubStatus"
      :current-board="currentBoard"
      :storylines="storylines"
      :rivalries="rivalries"
      :career-records="careerRecords"
      :manager-career="userManager"
      :board-project="boardProject"
      :age-policy="careerAgePolicy"
      :dashboard="managerDashboard"
      :job-status="jobStatus"
      :crest-for="historicalClubCrest"
      :stadium-for="historicalStadiumPhoto"
      :format-money="formatSourceMoney"
      :trend-label="trendLabel"
      :board-class="boardClass"
      :format-date="formatDateShort"
      @open-player="openPlayer"
      @navigate="navigateTo"
      @accept-job="acceptManagerJob"
      @board-request="requestBoardProject"
    />

    <CareerWorkspace
      v-else-if="view==='career'"
      :career="professionalCareer"
      :job-status="jobStatus"
      :format-money="formatSourceMoney"
      :format-date="formatDateShort"
      @apply-job="applyManagerJob"
      @accept-job="acceptManagerJob"
      @resign="resignManagerJob"
    />

    <HistoryWorkspace
      v-else-if="view==='history'"
      :latest-recap="latestRecap"
      :history-state="historyState"
      :latest-ai-audit="latestAiAudit"
      :career-records="careerRecords"
      :storyline-archive="storylineArchive"
      :manager-career="userManager"
    />

    <ChampionsWorkspace
      v-else-if="view==='champions'"
      :honours="historyState.honours||[]"
      :season-recaps="historyState.season_recaps||[]"
      :crest-for="historicalClubCrest"
    />

    <CalendarWorkspace
      v-else-if="view==='calendar'"
      :matches="matches"
      :preseason="preseason"
      :market-period="marketPeriod"
      :calendar-state="managerDashboard.calendar_context || {}"
      :format-date="formatDateShort"
    />
  </main>
    </div>
  </div>

  <SeasonEndOverlay
    v-if="seasonEndRecap"
    :recap="seasonEndRecap"
    :crest-for="historicalClubCrest"
    @close="seasonEndRecap=null"
    @open-champions="view='champions';seasonEndRecap=null"
    @open-history="view='history';seasonEndRecap=null"
    @open-workspace="navigateTo($event);seasonEndRecap=null"
  />
  <FootballPlayerProfileModal v-if="selectedPlayer" :player="selectedPlayer" :season="careerSeason" :tab="playerTab" @update:tab="playerTab=$event" @promise-role="promisePlayerRole" @scout-player="scoutMarketPlayer" @close="selectedPlayer=null" />
  <div v-if="notice" class="notice" role="status">{{notice}}</div>
  </template>
</div>
</template>
