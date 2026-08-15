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
  createCareer:({teamId=16,leagueId=null,seed=9394,throughMatchday=7}={})=>footballRequest('/api/football9394/careers',{method:'POST',body:JSON.stringify({team_id:teamId,league_id:leagueId,seed,through_matchday:throughMatchday})}),
  career:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}`),
  careerCalendar:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/calendar`),
  advanceCareer:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/advance`,{method:'POST'}),
  playNextCareerMatchday:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/play-next`,{method:'POST'}),
  updateCareerTactics:(careerId,tactics)=>footballRequest(`/api/football9394/careers/${careerId}/tactics`,{method:'PUT',body:JSON.stringify(tactics)}),
  updateCareerSelection:(careerId,{starterIds=null,benchIds=null,autoSelect=false}={})=>footballRequest(`/api/football9394/careers/${careerId}/selection`,{method:'PUT',body:JSON.stringify({starter_ids:starterIds,bench_ids:benchIds,auto_select:autoSelect})}),
  careerDashboard:(careerId)=>footballRequest(`/api/football9394/careers/${careerId}/dashboard`),
  careerLeagueStandings:(careerId,sourceId)=>footballRequest(`/api/football9394/careers/${careerId}/leagues/${sourceId}/standings`),
  careerMarket:(careerId,{query='',limit=20}={})=>footballRequest(`/api/football9394/careers/${careerId}/market?query=${encodeURIComponent(query)}&limit=${limit}`),
  negotiateTransfer:(careerId,playerId,{feeOffer,salaryOffer=0,contractYears=3})=>footballRequest(`/api/football9394/careers/${careerId}/transfers/${playerId}`,{method:'POST',body:JSON.stringify({fee_offer:feeOffer,salary_offer:salaryOffer,contract_years:contractYears})}),
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
