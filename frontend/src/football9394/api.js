async function footballRequest(path, options={}){
  const response=await fetch(path,{headers:{'Content-Type':'application/json',...(options.headers||{})},...options})
  const text=await response.text()
  let body=null
  try{body=text?JSON.parse(text):null}catch{body={detail:text||'Respuesta no válida'}}
  if(!response.ok) throw new Error(body?.detail||`Error HTTP ${response.status}`)
  return body
}

export const football9394Api={
  health:()=>footballRequest('/api/football9394/health'),
  universe:()=>footballRequest('/api/football9394/universe'),
  competitions:()=>footballRequest('/api/football9394/competitions'),
  ruleAudit:()=>footballRequest('/api/football9394/rule-audit'),
  team:(teamId)=>footballRequest(`/api/football9394/teams/${teamId}`),
  squad:(teamId)=>footballRequest(`/api/football9394/teams/${teamId}/squad`),
  teamCalendar:(teamId)=>footballRequest(`/api/football9394/teams/${teamId}/calendar`),
  player:(playerId)=>footballRequest(`/api/football9394/players/${playerId}`),
  searchPlayers:({query='',limit=20,excludeTeamId=null}={})=>{
    const params=new URLSearchParams({query,limit:String(limit)})
    if(excludeTeamId!=null)params.set('exclude_team_id',String(excludeTeamId))
    return footballRequest(`/api/football9394/players?${params}`)
  },
  careerOptions:()=>footballRequest('/api/football9394/career-options'),
  createCareer:({teamId=16,leagueId=null,seed=9394,throughMatchday=0,agePolicy='frozen_attributes_dynamic'}={})=>footballRequest('/api/football9394/careers',{method:'POST',body:JSON.stringify({team_id:teamId,league_id:leagueId,seed,through_matchday:throughMatchday,age_policy:agePolicy})}),
  career:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}`),
  careerCalendar:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/calendar`),
  advanceCareer:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/advance`,{method:'POST'}),
  advanceCareerUntilEvent:(careerId,maxDays=14)=>footballRequest(`/api/football9394/careers/${careerId}/advance-until-event?max_days=${Number(maxDays)}`,{method:'POST'}),
  playNextCareerMatchday:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/play-next`,{method:'POST'}),
  updateCareerTactics:(careerId,tactics)=>footballRequest(`/api/football9394/careers/${careerId}/tactics`,{method:'PUT',body:JSON.stringify(tactics)}),
  updateCareerSelection:(careerId,{starterIds=null,benchIds=null,autoSelect=false}={})=>footballRequest(`/api/football9394/careers/${careerId}/selection`,{method:'PUT',body:JSON.stringify({starter_ids:starterIds,bench_ids:benchIds,auto_select:autoSelect})}),
  careerDashboard:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/dashboard`),
  acceptManagerJob:(careerId,offerId)=>footballRequest(`/api/football9394/careers/${careerId}/jobs/${encodeURIComponent(offerId)}/accept`,{method:'POST'}),
  professionalCareer:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/professional-career`),
  applyManagerJob:(careerId,opportunityId)=>footballRequest(`/api/football9394/careers/${careerId}/jobs/${encodeURIComponent(opportunityId)}/apply`,{method:'POST'}),
  resignManagerJob:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/job/resign`,{method:'POST'}),
  acceptNationalJob:(careerId,offerId)=>footballRequest(`/api/football9394/careers/${careerId}/national-job/${encodeURIComponent(offerId)}/accept`,{method:'POST'}),
  resignNationalJob:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/national-job/resign`,{method:'POST'}),
  autoNationalSelection:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/national-selection/auto`,{method:'PUT'}),
  setNationalSelection:(careerId,playerIds)=>footballRequest(`/api/football9394/careers/${careerId}/national-selection`,{method:'PUT',body:JSON.stringify({player_ids:playerIds})}),
  setCaptain:(careerId,playerId)=>footballRequest(`/api/football9394/careers/${careerId}/captain/${Number(playerId)}`,{method:'POST'}),
  careerBoard:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/board`),
  boardProject:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/board-project`),
  boardRequest:(careerId,requestType)=>footballRequest(`/api/football9394/careers/${careerId}/board-project/requests/${encodeURIComponent(requestType)}`,{method:'POST'}),
  careerStaff:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/staff`),
  assignStaffResponsibility:(careerId,key,assignee)=>footballRequest(`/api/football9394/careers/${careerId}/staff/responsibilities/${encodeURIComponent(key)}`,{method:'PUT',body:JSON.stringify({assignee})}),
  careerScouting:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/scouting`),
  careerTraining:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/training`),
  updateTraining:(careerId,{intensity=null,weeklyPlan=null}={})=>footballRequest(`/api/football9394/careers/${careerId}/training`,{method:'PUT',body:JSON.stringify({intensity,weekly_plan:weeklyPlan})}),
  setTrainingFocus:(careerId,playerId,focus)=>footballRequest(`/api/football9394/careers/${careerId}/training/players/${Number(playerId)}`,{method:'PUT',body:JSON.stringify({focus})}),
  setTrainingRecovery:(careerId,playerId,recovery)=>footballRequest(`/api/football9394/careers/${careerId}/training/recovery/${Number(playerId)}`,{method:'PUT',body:JSON.stringify({recovery})}),
  setMatchPreparation:(careerId,focus)=>footballRequest(`/api/football9394/careers/${careerId}/training/match-preparation`,{method:'PUT',body:JSON.stringify({focus})}),
  tacticalPlan:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/tactical-plan`),
  updateTacticalPlan:(careerId,payload)=>footballRequest(`/api/football9394/careers/${careerId}/tactical-plan`,{method:'PUT',body:JSON.stringify(payload)}),
  setTacticalPlayerInstruction:(careerId,playerId,payload)=>footballRequest(`/api/football9394/careers/${careerId}/tactical-plan/players/${Number(playerId)}`,{method:'PUT',body:JSON.stringify(payload)}),
  setOppositionInstruction:(careerId,playerId,payload)=>footballRequest(`/api/football9394/careers/${careerId}/tactical-plan/opposition/${Number(playerId)}`,{method:'PUT',body:JSON.stringify(payload)}),
  setSetPieceTaker:(careerId,kind,playerId)=>footballRequest(`/api/football9394/careers/${careerId}/tactical-plan/set-pieces/${encodeURIComponent(kind)}`,{method:'PUT',body:JSON.stringify({player_id:playerId})}),
  staffReports:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/staff-reports`),
  matchBriefing:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/match-briefing`),
  scoutPlayer:(careerId,playerId)=>footballRequest(`/api/football9394/careers/${careerId}/scouting/${Number(playerId)}`,{method:'POST'}),
  careerSquadPlan:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/squad-plan`),
  careerNews:(careerId,{category='',limit=80}={})=>{const params=new URLSearchParams({limit:String(limit)});if(category)params.set('category',category);return footballRequest(`/api/football9394/careers/${careerId}/news?${params}`)},
  informationWorld:(careerId,limit=80)=>footballRequest(`/api/football9394/careers/${careerId}/information-world?limit=${Number(limit)}`),
  careerCompetitions:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/competitions`),
  careerCompetition:(careerId,kind,sourceId)=>footballRequest(`/api/football9394/careers/${careerId}/competitions/${encodeURIComponent(kind)}/${Number(sourceId)}`),
  careerHistory:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/history`),
  careerLeagueStandings:(careerId,sourceId)=>footballRequest(`/api/football9394/careers/${careerId}/leagues/${sourceId}/standings`),
  careerMarket:(careerId,{query='',limit=20,position='',freeAgents=false,watched=false}={})=>{
    const params=new URLSearchParams({query,limit:String(limit)})
    if(position)params.set('position',position)
    if(freeAgents)params.set('free_agents','true')
    if(watched)params.set('watched','true')
    return footballRequest(`/api/football9394/careers/${careerId}/market?${params}`)
  },
  negotiateTransfer:(careerId,playerId,{feeOffer,salaryOffer=0,contractYears=3})=>footballRequest(`/api/football9394/careers/${careerId}/transfers/${playerId}`,{method:'POST',body:JSON.stringify({fee_offer:feeOffer,salary_offer:salaryOffer,contract_years:contractYears})}),
  careerPlayer:(careerId,playerId)=>footballRequest(`/api/football9394/careers/${careerId}/players/${playerId}`),
  setRolePromise:(careerId,playerId,role)=>footballRequest(`/api/football9394/careers/${careerId}/players/${Number(playerId)}/role-promise`,{method:'POST',body:JSON.stringify({role})}),
  respondDressingConcern:(careerId,concernId,response)=>footballRequest(`/api/football9394/careers/${careerId}/dressing-room/concerns/${encodeURIComponent(concernId)}`,{method:'POST',body:JSON.stringify({response})}),
  disciplinePlayer:(careerId,playerId,action)=>footballRequest(`/api/football9394/careers/${careerId}/players/${Number(playerId)}/discipline`,{method:'POST',body:JSON.stringify({action})}),
  liveMatch:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/live`),
  startLiveMatch:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/live/start`,{method:'POST'}),
  advanceLiveMatch:(careerId,minutes=5)=>footballRequest(`/api/football9394/careers/${careerId}/live/advance`,{method:'POST',body:JSON.stringify({minutes})}),
  updateLiveTactics:(careerId,tactics)=>footballRequest(`/api/football9394/careers/${careerId}/live/tactics`,{method:'PUT',body:JSON.stringify(tactics)}),
  liveSubstitution:(careerId,outgoingId,incomingId)=>footballRequest(`/api/football9394/careers/${careerId}/live/substitution`,{method:'POST',body:JSON.stringify({outgoing_id:outgoingId,incoming_id:incomingId})}),
  finishLiveMatch:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/live/finish`,{method:'POST'}),
  marketFlow:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/market-flow`),
  watchPlayer:(careerId,playerId,watched=true)=>footballRequest(`/api/football9394/careers/${careerId}/watchlist/${playerId}`,{method:'POST',body:JSON.stringify({watched})}),
  marketInquiry:(careerId,playerId)=>footballRequest(`/api/football9394/careers/${careerId}/market-inquiry/${Number(playerId)}`,{method:'POST'}),
  openNegotiation:(careerId,{playerId,feeOffer,salaryOffer=0,contractYears=3,squadRole='rotation',signingBonus=0,releaseClause=null,dealType='transfer',loanWageShare=100})=>footballRequest(`/api/football9394/careers/${careerId}/negotiations`,{method:'POST',body:JSON.stringify({player_id:playerId,fee_offer:feeOffer,salary_offer:salaryOffer,contract_years:contractYears,squad_role:squadRole,signing_bonus:signingBonus,release_clause:releaseClause,deal_type:dealType,loan_wage_share:loanWageShare})}),
  counterNegotiation:(careerId,negotiationId,{feeOffer,salaryOffer=0,contractYears=3,loanWageShare=null})=>footballRequest(`/api/football9394/careers/${careerId}/negotiations/${negotiationId}`,{method:'PUT',body:JSON.stringify({fee_offer:feeOffer,salary_offer:salaryOffer,contract_years:contractYears,loan_wage_share:loanWageShare})}),
  withdrawNegotiation:(careerId,negotiationId)=>footballRequest(`/api/football9394/careers/${careerId}/negotiations/${encodeURIComponent(negotiationId)}`,{method:'DELETE'}),
  listPlayer:(careerId,playerId,askingPrice=0)=>footballRequest(`/api/football9394/careers/${careerId}/transfer-list/${playerId}`,{method:'POST',body:JSON.stringify({asking_price:askingPrice})}),
  unlistPlayer:(careerId,playerId)=>footballRequest(`/api/football9394/careers/${careerId}/transfer-list/${playerId}`,{method:'DELETE'}),
  acceptIncomingOffer:(careerId,offerId)=>footballRequest(`/api/football9394/careers/${careerId}/incoming-offers/${offerId}/accept`,{method:'POST'}),
  renewContract:(careerId,playerId,{years=3,salaryOffer=null}={})=>footballRequest(`/api/football9394/careers/${careerId}/contracts/${playerId}/renew`,{method:'POST',body:JSON.stringify({years,salary_offer:salaryOffer})}),
  careerEconomy:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/economy`),
  careerWorld:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/world`),
  nationalTeams:()=>footballRequest('/api/football9394/national-teams'),
  nationalTeam:(countryId,careerId='')=>footballRequest(`/api/football9394/national-teams/${countryId}${careerId?`?career_id=${encodeURIComponent(careerId)}`:''}`),
  bootstrapCareer:(teamId=16,throughMatchday=7)=>footballRequest(`/api/football9394/career/bootstrap?team_id=${teamId}&through_matchday=${throughMatchday}`),
  leagueCalendar:(leagueId)=>footballRequest(`/api/football9394/leagues/${leagueId}/calendar`),
  rules:(competition)=>footballRequest(`/api/football9394/rules/${encodeURIComponent(competition)}`),
  simulateMatch:(payload)=>footballRequest('/api/football9394/matches/simulate',{method:'POST',body:JSON.stringify(payload)}),
  simulateWorldSeason:(seed=9394)=>footballRequest('/api/football9394/world/seasons/simulate',{method:'POST',body:JSON.stringify({seed})}),
}
