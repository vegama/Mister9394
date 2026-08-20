<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import FootballPlayerProfileModal from '../features/football9394/FootballPlayerProfileModal.vue'
import FootballTeamProfileModal from '../features/football9394/FootballTeamProfileModal.vue'
import FootballMatchContextModal from '../features/football9394/FootballMatchContextModal.vue'
import ManagerSidebar from './components/ManagerSidebar.vue'
import CareerSetup from './components/CareerSetup.vue'
import ManagerTopbar from './components/ManagerTopbar.vue'
import ManagerCommandPalette from './components/ManagerCommandPalette.vue'
import DecisionFocusBar from './components/DecisionFocusBar.vue'
import FirstRunGuide from './components/FirstRunGuide.vue'
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
import { football9394Api, footballNetworkState } from './api.js'
import { useAsyncActionLock } from './composables/useAsyncActionLock.js'
import { useNavigationContext } from './composables/useNavigationContext.js'
import { useCareerState } from './composables/useCareerState.js'
import { useEntityNavigation } from './composables/useEntityNavigation.js'
import { useFirstRunGuide } from './composables/useFirstRunGuide.js'
import { useManagerShortcuts } from './composables/useManagerShortcuts.js'
import { useMarketActions } from './composables/useMarketActions.js'
import { formatCalendarRows } from './entityPresentation.js'

const productVersion=__MISTER9394_VERSION__

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
const { busy: matchActionBusy, run: withMatchAction } = useAsyncActionLock()
const { view, routeEntity, routeEntityTab, canGoBack, sectionTitle, navigationGroups, replaceRoute, openEntityRoute, setEntityTab, closeEntityRoute, navigateBack, reconcileRouteAfterCareerLoad } = useNavigationContext({
  liveMatch, lastMatchReport, matchActionBusy, flash, cancelPreviewAndNavigate,
})
const sectionContext = computed(() => view.value === 'match' ? 'DÍA DE PARTIDO' : (navigationGroups.find(group => group.items.some(item => item.id === view.value))?.label || 'Centro de mando'))
const careerCalendarRows = ref([])
const selectedCompetition = ref('league:1')
const notice = ref('')
const commandPaletteOpen = ref(false)
const decisionFocus = ref(null)
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
const activePlanNeed = ref(null)
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
const dataError = ref('')
const simulatedThroughMatchday = ref(7)
const managerDashboard = ref({position:null,points:0,recent_form:[],form_label:'Sin partidos',morale_average:70,unavailable_count:0,board_expectation:{title:'—'},board_confidence:'A la espera',pending_decisions:[]})
const selection = ref({starter_ids:[],bench_ids:[],starters:[],bench:[],valid:false,issues:[]})
const lineupDraft = ref([])
const benchDraft = ref([])

const controlledTeam = ref({source_id:null,name:'Sin club',long_name:'Sin club',league:null,members:null,budget:null,debt:null})
const controlledTeamId = computed(()=>Number(controlledTeam.value?.source_id||0))
const selectedLeagueOption = computed(()=>careerOptions.value.find(row=>Number(row.source_id)===Number(selectedLeagueId.value))||null)
const lineupDraftPlayers = computed(()=>lineupDraft.value.map(id=>squad.value.find(p=>Number(p.id)===Number(id))).filter(Boolean))
const benchDraftPlayers = computed(()=>benchDraft.value.map(id=>squad.value.find(p=>Number(p.id)===Number(id))).filter(Boolean))
const lineupDirty = computed(()=>{
 const savedStarters=[...(selection.value?.starter_ids||[])].map(Number).sort((a,b)=>a-b)
 const draftStarters=[...lineupDraft.value].map(Number).sort((a,b)=>a-b)
 const savedBench=[...(selection.value?.bench_ids||[])].map(Number).sort((a,b)=>a-b)
 const draftBench=[...benchDraft.value].map(Number).sort((a,b)=>a-b)
 return JSON.stringify(savedStarters)!==JSON.stringify(draftStarters) || JSON.stringify(savedBench)!==JSON.stringify(draftBench)
})
const matchdaySelectionComplete = computed(()=>lineupDraft.value.length===11 && benchDraft.value.length===5)
const isMatchDay = computed(()=>Boolean(nextMatch.value?.date && gameDate.value && String(nextMatch.value.date)===String(gameDate.value)))
const standings = ref([])
const competitionStandings = ref([])
const competitionProgress = ref(null)
const competitionDetail = ref(null)
const competitionViewMode = ref('table')
const squad = ref([])
const competitions = ref([])
async function refreshCandidateComparison(careerId){
 const ids=targets.value.slice(0,3).map(row=>Number(row[5])).filter(Boolean)
 if(!careerId||ids.length<2){candidateComparison.value=null;return}
 try{candidateComparison.value=await football9394Api.compareCandidates(careerId,ids)}
 catch{candidateComparison.value=null}
}
const targets = ref([])
// Veredicto de la comparacion A/B/C: lo calcula el servidor porque depende del
// conocimiento que el club tiene de cada candidato, no de lo que se ve en la
// tabla. Sin el, el panel enseña tres fichas y no dice si son separables.
const candidateComparison = ref(null)
const matches = ref([])
const nextMatch = ref(null)
const newsFeed = ref([])
const historyState = ref({season_recaps:[],season_archive:[],season_dossiers:[],honours:[],club_honours:[],career_milestones:[],board_history:[],ai_squad_audits:[]})
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
function applyCareerState(state){
 // Compact endpoints (live/start, live/advance, live/substitution…) deliberately
 // omit the career snapshot to keep the match loop light — see the v115
 // performance contract. Those responses are still valid, so treat a missing
 // state as "nothing to refresh" instead of throwing and aborting the caller.
 if(!state)return
 if(state.career_id)setCareerId(state.career_id)
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
 benchDraft.value=[...(state.selection?.bench_ids||[])]
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
 if(state.season_recaps||state.season_dossiers||state.career_milestones)historyState.value={...historyState.value,season_recaps:state.season_recaps||historyState.value.season_recaps,season_dossiers:state.season_dossiers||historyState.value.season_dossiers,career_milestones:state.career_milestones||historyState.value.career_milestones}
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
const calendarRowsForUi=(rows,state)=>formatCalendarRows(rows,state,controlledTeamId.value)
async function refreshCareerData(state){
 const [calendarRows,marketRows,competitionRows,newsRows,careerRows,projectRows,informationRows]=await Promise.all([
  football9394Api.careerCalendar(state.career_id),football9394Api.careerMarket(state.career_id,{query:marketQuery.value,position:marketPosition.value,freeAgents:marketFreeAgents.value,watched:marketWatchedOnly.value,limit:(marketQuery.value||marketPosition.value||marketFreeAgents.value||marketWatchedOnly.value)?30:10}),football9394Api.careerCompetitions(state.career_id),football9394Api.careerNews(state.career_id,{limit:80}),
  football9394Api.professionalCareer(state.career_id),football9394Api.boardProject(state.career_id),football9394Api.informationWorld(state.career_id,80),
 ])
 const recent=calendarRows.filter(m=>m.played).slice(-3);const upcoming=calendarRows.filter(m=>!m.played).slice(0,6)
 careerCalendarRows.value=calendarRows
 matches.value=calendarRowsForUi([...recent,...upcoming],state)
 targets.value=marketRows.map(p=>[p.display_name,p.position,p.team_name,p.overall??'—',p.estimated_transfer_value??0,p.id,p])
 if(restoredMarketTargetId.value){const target=targets.value.find(row=>Number(row[5])===Number(restoredMarketTargetId.value));if(target)chooseTarget(target);restoredMarketTargetId.value=null}
 await refreshCandidateComparison(state.career_id)
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
  if(state){applyCareerState(state);restoreMarketWorkspace(state.career_id);restoreDailyWorkspace(state.career_id);await refreshCareerData(state);await loadHistory();showCareerSetup.value=false;refreshFirstRunGuide();reconcileRouteAfterCareerLoad()}
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
  applyCareerState(state);await refreshCareerData(state);await loadHistory();showCareerSetup.value=false;view.value='home';refreshFirstRunGuide()
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
 const teamId=Number(row.team_id||controlledTeamId.value||0)||null
 const position=row.pos||row.position
 return {id:row.id,display_name:row.name||row.display_name,team_id:teamId,team_name:row.team_name||controlledTeam.value.name,photo_url:historicalPlayerPhoto(row.id),team_crest_url:historicalClubCrest(teamId),shirt_number:row.n??row.shirt_number,age:row.age,nationality:row.nationality,position,positions:position?[position]:[],overall:row.overall,overall_range:row.overall_range,overall_is_exact:row.overall_is_exact,attributes:{}}
}
function isStarter(playerId){return lineupDraft.value.includes(Number(playerId))}
function isBench(playerId){return benchDraft.value.includes(Number(playerId))}
function toggleStarter(player){
 const id=Number(player.id)
 if(player.status!=='DISP.'&&!isStarter(id)){flash(`${player.name} no está disponible.`);return}
 if(isStarter(id)){lineupDraft.value=lineupDraft.value.filter(x=>x!==id);return}
 if(lineupDraft.value.length>=11){flash('El once ya tiene 11 futbolistas. Sustituye o arrastra a este jugador sobre un titular.');return}
 if(isBench(id))benchDraft.value=benchDraft.value.filter(x=>x!==id)
 lineupDraft.value=[...lineupDraft.value,id]
}
function toggleBench(player){
 const id=Number(player.id)
 if(player.status!=='DISP.'&&!isBench(id)){flash(`${player.name} no está disponible.`);return}
 if(isStarter(id)){flash(`${player.name} ya está en el once titular.`);return}
 if(isBench(id)){benchDraft.value=benchDraft.value.filter(x=>x!==id);return}
 if(benchDraft.value.length>=5){flash('El banquillo ya tiene los 5 suplentes permitidos en 1993-94.');return}
 benchDraft.value=[...benchDraft.value,id]
}
function replaceStarterFromDrag({sourceId,targetId}){
 const source=Number(sourceId);const target=Number(targetId)
 if(!source||!target||source===target)return
 const sourcePlayer=squad.value.find(p=>Number(p.id)===source)
 if(!sourcePlayer||sourcePlayer.status!=='DISP.'){flash('Ese futbolista no está disponible para la convocatoria.');return}
 const targetIndex=lineupDraft.value.findIndex(id=>Number(id)===target)
 if(targetIndex<0)return
 if(isStarter(source)){
  const sourceIndex=lineupDraft.value.findIndex(id=>Number(id)===source)
  const next=[...lineupDraft.value];[next[sourceIndex],next[targetIndex]]=[next[targetIndex],next[sourceIndex]];lineupDraft.value=next;return
 }
 const nextStarters=[...lineupDraft.value];nextStarters[targetIndex]=source;lineupDraft.value=nextStarters
 const benchIndex=benchDraft.value.findIndex(id=>Number(id)===source)
 if(benchIndex>=0){const nextBench=[...benchDraft.value];nextBench[benchIndex]=target;benchDraft.value=nextBench}
 else if(benchDraft.value.length<5)benchDraft.value=[...benchDraft.value,target]
 flash(`${sourcePlayer.name} entra en el XI.`)
}
function replaceBenchFromDrag({sourceId,targetId}){
 const source=Number(sourceId);const target=Number(targetId||0)
 if(!source||source===target)return
 const sourcePlayer=squad.value.find(p=>Number(p.id)===source)
 if(!sourcePlayer||sourcePlayer.status!=='DISP.')return
 if(!target){
  if(isStarter(source)){flash(`${sourcePlayer.name} ya está en el XI. Arrástralo sobre un suplente para intercambiar posiciones.`);return}
  if(isBench(source))return
  if(benchDraft.value.length>=5){flash('El banquillo ya tiene 5 suplentes. Sustituye uno de ellos.');return}
  benchDraft.value=[...benchDraft.value,source];return
 }
 const targetBenchIndex=benchDraft.value.findIndex(id=>Number(id)===target)
 if(targetBenchIndex<0)return
 if(isStarter(source)){
  const starterIndex=lineupDraft.value.findIndex(id=>Number(id)===source)
  const nextStarters=[...lineupDraft.value];nextStarters[starterIndex]=target;lineupDraft.value=nextStarters
  const nextBench=[...benchDraft.value];nextBench[targetBenchIndex]=source;benchDraft.value=nextBench;return
 }
 const sourceBenchIndex=benchDraft.value.findIndex(id=>Number(id)===source)
 if(sourceBenchIndex>=0){const next=[...benchDraft.value];[next[sourceBenchIndex],next[targetBenchIndex]]=[next[targetBenchIndex],next[sourceBenchIndex]];benchDraft.value=next;return}
 const next=[...benchDraft.value];next[targetBenchIndex]=source;benchDraft.value=next
}
async function saveSelection({silent=false}={}){
 if(!careerId.value)return false
 if(lineupDraft.value.length!==11){flash('Completa los 11 titulares antes de guardar la convocatoria.');return false}
 if(benchDraft.value.length!==5){flash('Completa los 5 jugadores de banquillo antes de guardar la convocatoria.');return false}
 try{
  const result=await football9394Api.updateCareerSelection(careerId.value,{starterIds:lineupDraft.value,benchIds:benchDraft.value})
  applyCareerState(result.career);if(!silent)flash('Convocatoria completa guardada: 11 titulares + 5 suplentes.');return true
 }catch(error){flash(`No se pudo guardar la convocatoria: ${error.message}`);return false}
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
async function navigateFromSidebar(target){decisionFocus.value=null;await navigateTo(target)}
function returnToDecisionOrigin(){const target=decisionFocus.value?.returnView||'home';decisionFocus.value=null;view.value=target}
function showPendingDecisions(){decisionFocus.value=null;view.value='home'}
async function appointCaptain(player){
 if(!careerId.value)return
 try{const result=await football9394Api.setCaptain(careerId.value,Number(player.id));applyCareerState(result.career);flash(`${player.name} es el nuevo capitán.`)}catch(error){flash(`No se pudo cambiar la capitanía: ${error.message}`)}
}
async function assignStaffResponsibility(payload){
 if(!careerId.value||!payload?.key||!payload?.assignee)return
 try{
  const result=await football9394Api.assignStaffResponsibility(careerId.value,payload.key,payload.assignee)
  applyCareerState(result.career)
  const handoff=(result?.career?.staff?.recent_handoffs||[])[0]
  if(handoff?.responsibility===payload.key && Number(handoff?.affected_count||0)>0){
   flash(`Responsabilidad actualizada · ${Number(handoff.affected_count||0)} proceso(s) activo(s) reasignados sin perder el trabajo.`)
  }else{flash('Responsabilidad actualizada.')}
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
 activePlanNeed.value=need||null
 marketQuery.value=''
 marketPosition.value=need?.market_position||''
 await searchMarket()
 flash(need?.market_position?`Buscando ${need.label.toLowerCase()} según el plan de plantilla.`:'Mostrando mercado para ampliar la profundidad de plantilla.')
}
async function setTrainingRoleFocus(payload){
 if(!careerId.value||!payload?.playerId)return
 try{const result=await football9394Api.setTrainingRoleFocus(careerId.value,payload.playerId,payload.roleFocus);applyCareerState(result.career);flash('Adaptación de puesto guardada.')}catch(error){flash(`No se pudo cambiar el puesto: ${error.message}`)}
}
async function setSquadPlanDecision(payload){
 if(!careerId.value||!payload?.playerId)return
 try{const result=await football9394Api.setSquadPlanDecision(careerId.value,payload.playerId,payload.decision);applyCareerState(result.career);flash('Decisión de plantilla guardada.')}catch(error){flash(`No se pudo guardar la decisión: ${error.message}`)}
}
async function autoSelectLineup(){
 if(!careerId.value)return
 try{const result=await football9394Api.updateCareerSelection(careerId.value,{autoSelect:true});applyCareerState(result.career);flash('Mejor convocatoria disponible seleccionada: 11 + 5.')}catch(error){flash(`No se pudo seleccionar el once: ${error.message}`)}
}
async function autoSelectForCurrentTactics(){
 if(!careerId.value)return
 try{const tacticsResult=await football9394Api.updateCareerTactics(careerId.value,currentTactics());applyCareerState(tacticsResult.career)}catch(error){flash(`No se pudo guardar la táctica: ${error.message}`);return}
 await autoSelectLineup()
}
function playerNameById(id){const own=squad.value.find(p=>Number(p.id)===Number(id));if(own)return own.name;const target=targets.value.find(p=>Number(p[5])===Number(id));return target?.[0]||`Jugador #${id}`}
async function openDecision(decision){
 if(!decision?.action)return
 decisionFocus.value={...decision,returnView:'home'}
 await navigateTo(decision.action)
}
function flash(message){notice.value=message;window.setTimeout(()=>{notice.value=''},2200)}
async function promisePlayerRole(payload){
 if(!careerId.value||!payload?.player?.id||!payload?.role)return
 try{
  const result=await football9394Api.setRolePromise(careerId.value,payload.player.id,payload.role)
  applyCareerState(result.career)
  const detail=result.player||await football9394Api.careerPlayer(careerId.value,payload.player.id)
  selectedPlayer.value=decoratePlayer(detail)
  flash(`Rol acordado con ${detail.display_name||detail.name}: ${payload.role}.`)
 }catch(error){flash(`No se pudo acordar el rol: ${error.message}`)}
}
async function advance(){
 if(isAdvancing.value)return
 if(liveMatch.value){view.value='match';flash('Tienes un partido en directo pendiente.');return}
 if(!careerId.value){flash('La carrera todavía no está lista.');return}
 if(jobStatus.value==='dismissed'){view.value='career';flash('Estás sin club. Elige un nuevo proyecto para continuar tu carrera.');return}
 const blocker=managerDashboard.value?.blocking_decisions?.[0]
 if(blocker){await navigateTo(blocker.action||'home');flash(`Continuar detenido · ${blocker.title}`);return}
 isAdvancing.value=true
 try{
  const result=await football9394Api.advanceCareerUntilEvent(careerId.value,14)
  applyCareerState(result.career);await refreshCareerData(result.career)
  if(result.world_events?.some(e=>e.kind==='season_rollover')){
   await loadHistory()
   seasonEndRecap.value=historyState.value.season_recaps?.slice(-1)[0]||null
  }
  if(result.career_over){view.value='career';flash('El consejo ha terminado tu etapa en el club.');return}
  if(result.requires_decision&&result.decision){await navigateTo(result.decision.action||'home');flash(`Continuar detenido · ${result.decision.title}`);return}
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
 if(lineupDirty.value){const saved=await saveSelection({silent:true});if(!saved)return}
 try{const result=await football9394Api.updateCareerTactics(careerId.value,currentTactics());applyCareerState(result.career);flash('Táctica y convocatoria guardadas.')}catch(error){flash(`No se pudo guardar la táctica: ${error.message}`)}
}
async function startLive(){
 if(!careerId.value||!nextMatch.value){flash('No hay partido disponible.');return}
 if(!isMatchDay.value){flash(`La previa se abre el día del partido (${formatDateShort(nextMatch.value.date)}). Mientras tanto puedes preparar XI y táctica.`);return}
 if(lineupDirty.value){const saved=await saveSelection({silent:true});if(!saved){view.value='squad';return}}
 if(!selection.value?.valid || !matchdaySelectionComplete.value){view.value='squad';flash('La convocatoria debe quedar completa y legal: 11 titulares + 5 suplentes.');return}
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
 }catch(error){competitionStandings.value=[];competitionProgress.value=null;competitionDetail.value=null;flash(`No se pudo abrir la competición: ${error.message}`);if(routeEntity.value?.type==='competition')replaceRoute('competitions')}
}
const selectedCompetitionRuntime = computed(()=>competitionDetail.value)
const latestNews = computed(()=>newsFeed.value.slice(0,5))
const newsCategories = computed(()=>['Todas',...new Set(newsFeed.value.map(n=>n.category).filter(Boolean))])
const newsCategory = ref('Todas')
const { careerId, setCareerId, persistMarketWorkspace, restoreMarketWorkspace, persistDailyWorkspace, restoreDailyWorkspace } = useCareerState({
  marketQuery, marketPosition, marketFreeAgents, marketWatchedOnly, selectedTarget, restoredMarketTargetId,
  selectedCompetition, competitionViewMode, newsCategory,
})
const {
  selectedPlayer, selectedTeamProfile, selectedMatchContext, entityLoadError, entityLoading, playerTab,
  decoratePlayer, openPlayer, openTeam, openCompetitionEntity, openMatchEntity, openNewsEntity, retryRouteEntity,
} = useEntityNavigation({
  careerId, routeEntity, routeEntityTab, selectedCompetition, careerCalendarRows, controlledTeam,
  calendarRowsForUi, profileFor, historicalPlayerPhoto, historicalClubCrest, formatSourceMoney,
  openEntityRoute, setEntityTab, replaceRoute, flash,
})
const { firstRunGuideVisible, refreshFirstRunGuide, dismissFirstRunGuide } = useFirstRunGuide({ careerId, careerRecords })
const {
 searchMarket, toggleWatch, scoutMarketPlayer, inquireMarketPlayer, withdrawNegotiation,
 submitTransfer, counterNegotiation, toggleTransferListing, acceptIncomingOffer,
} = useMarketActions({
 careerId, targets, selectedTarget, selectedPlayer,
 marketQuery, marketPosition, marketFreeAgents, marketWatchedOnly,
 transferFee, transferSalary, transferYears, transferSquadRole,
 transferSigningBonus, transferReleaseClause, transferDealType, transferLoanWageShare,
 applyCareerState, refreshCareerData, flash, persistMarketWorkspace,
 historicalPlayerPhoto, historicalClubCrest, formatSourceMoney, formatDateShort,
})
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
watch(selectedLeagueId,()=>{const league=selectedLeagueOption.value;selectedTeamId.value=league?.teams?.[0]?.source_id??null})
watch(selectedCompetition,loadSelectedCompetitionTable)
watch(careerId,()=>{if(careerId.value)loadSelectedCompetitionTable()})
watch([marketQuery,marketPosition,marketFreeAgents,marketWatchedOnly],persistMarketWorkspace)
watch([selectedCompetition,competitionViewMode,newsCategory],persistDailyWorkspace)
useManagerShortcuts({ commandPaletteOpen, liveMatch, advance, navigateFromSidebar })
onMounted(loadHistoricalCareer)
</script>

<template>
<div class="m9394-shell">
  <a v-if="!showCareerSetup" class="m9394-skip-link" href="#m9394-main">Saltar al contenido</a>
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
      @navigate="navigateFromSidebar"
      @new-career="openCareerSetup"
    />
    <div class="manager-main">
      <ManagerTopbar
        :title="sectionTitle"
        :context="sectionContext"
        :date="currentDate"
        :matchday="currentMatchday"
        :pending-count="managerDashboard.pending_decisions?.length || 0"
        :preseason="preseason.active"
        :busy="isAdvancing"
        :version="productVersion"
        :continue-status="managerDashboard.continue_status"
        :can-go-back="canGoBack"
        @back="navigateBack"
        @advance="advance"
        @search="commandPaletteOpen=true"
      />
      <DecisionFocusBar
        v-if="decisionFocus && view!=='home'"
        :focus="decisionFocus"
        :view-label="sectionTitle"
        @back="returnToDecisionOrigin"
        @home="showPendingDecisions"
        @clear="decisionFocus=null"
      />

  <main id="m9394-main" class="m9394-workspace" tabindex="-1"><div v-if="dataError" class="data-error" role="alert"><strong>No hemos podido actualizar esta parte del juego.</strong><span>{{dataError}}</span></div>
    <FirstRunGuide
      v-if="view==='home' && firstRunGuideVisible"
      :dashboard="managerDashboard"
      :selection="selection"
      :lineup-dirty="lineupDirty"
      :next-match="nextMatch"
      @navigate="navigateTo"
      @open-decision="openDecision"
      @continue="advance"
      @dismiss="dismissFirstRunGuide"
    />
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
      :last-match-report="lastMatchReport"
      @navigate="navigateTo"
      @open-decision="openDecision"
      @start-live="startLive"
      @continue="advance"
    />

    <SquadWorkspace
      v-else-if="view==='squad'"
      :squad="squad"
      :lineup-draft="lineupDraft"
      :lineup-players="lineupDraftPlayers"
      :bench-draft="benchDraft"
      :bench-players="benchDraftPlayers"
      :formation="formation"
      :selection="selection"
      :dressing-room="dressingRoom"
      @toggle-starter="toggleStarter"
      @toggle-bench="toggleBench"
      @replace-starter="replaceStarterFromDrag"
      @replace-bench="replaceBenchFromDrag"
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
      @set-role-focus="setTrainingRoleFocus"
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
      :bench-players="benchDraftPlayers"
      :squad="squad"
      :lineup-draft="lineupDraft"
      :bench-draft="benchDraft"
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
      @replace-starter="replaceStarterFromDrag"
      @replace-bench="replaceBenchFromDrag"
      @toggle-starter="toggleStarter"
      @toggle-bench="toggleBench"
      @auto-select="autoSelectForCurrentTactics"
      @save-selection="saveSelection"
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
      @open-team="openTeam"
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
      :comparison="candidateComparison"
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
      :plan-need="activePlanNeed"
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
      @set-plan-decision="setSquadPlanDecision"
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
      @open-entity="openNewsEntity"
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
      :bench-draft="benchDraft"
      :bench-players="benchDraftPlayers"
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
      @open-match="openMatchEntity"
      @open-team="openTeam"
    />
  </main>
    </div>
  </div>

  <ManagerCommandPalette :open="commandPaletteOpen" :groups="navigationGroups" :active="view" @close="commandPaletteOpen=false" @navigate="navigateFromSidebar" />

  <SeasonEndOverlay
    v-if="seasonEndRecap"
    :recap="seasonEndRecap"
    :crest-for="historicalClubCrest"
    @close="seasonEndRecap=null"
    @open-champions="view='champions';seasonEndRecap=null"
    @open-history="view='history';seasonEndRecap=null"
    @open-workspace="navigateTo($event);seasonEndRecap=null"
  />
  <FootballPlayerProfileModal v-if="selectedPlayer" :player="selectedPlayer" :season="careerSeason" :tab="playerTab" @update:tab="playerTab=$event" @promise-role="promisePlayerRole" @scout-player="scoutMarketPlayer" @open-team="openTeam" @close="closeEntityRoute" />
  <FootballTeamProfileModal v-if="selectedTeamProfile" :detail="selectedTeamProfile" :crest-for="historicalClubCrest" :stadium-for="historicalStadiumPhoto" @open-player="openPlayer" @open-team="openTeam" @open-competition="openCompetitionEntity" @open-controlled-club="closeEntityRoute();navigateTo('club')" @close="closeEntityRoute" />
  <FootballMatchContextModal v-if="selectedMatchContext" :match="selectedMatchContext" :controlled-team-id="controlledTeamId" :crest-for="historicalClubCrest" :format-date="formatDateShort" @open-team="openTeam" @navigate="navigateTo" @close="closeEntityRoute" />
  <div v-if="entityLoading" class="entity-route-loading" role="status" aria-live="polite"><span aria-hidden="true"></span><strong>Abriendo contexto…</strong></div>
  <div v-else-if="entityLoadError && routeEntity" class="entity-route-error" role="alert"><span><small>NO SE PUDO ABRIR EL CONTEXTO</small><strong>{{entityLoadError}}</strong></span><button type="button" @click="retryRouteEntity">Reintentar</button><button type="button" class="secondary" @click="closeEntityRoute">Volver</button></div>
  <div v-if="footballNetworkState.slow.value" class="network-slow-indicator" role="status" aria-live="polite"><span aria-hidden="true"></span><strong>Procesando…</strong><small>No repitas la acción; te avisaremos cuando termine.</small></div>
  <div v-if="notice" class="notice" role="status">{{notice}}</div>
  </template>
</div>
</template>
