export function formatCalendarRows(rows, state, fallbackTeamId = 0) {
  const teamId = Number(state.team?.source_id || fallbackTeamId)
  const leagueName = state.team?.league?.name || 'Liga'
  return (rows || []).slice(-8).map(match => {
    const home = Number(match.home_team_id || 0)
    const away = Number(match.away_team_id || 0)
    const opponent = home === teamId ? (match.away_team || 'Rival por confirmar') : away === teamId ? (match.home_team || 'Rival por confirmar') : 'Rival por confirmar'
    const opponentId = home === teamId ? away : away === teamId ? home : null
    const venue = home === teamId ? 'Casa' : away === teamId ? 'Fuera' : 'Por confirmar'
    const postponed = Boolean(match.postponed) || String(match.schedule_status || '').toLowerCase() === 'postponed'
    const status = match.played ? `${match.home_goals}-${match.away_goals}` : postponed ? 'Aplazado' : Number(match.availability_count || 0) > 0 ? `Pendiente · ${match.availability_count} baja${Number(match.availability_count) === 1 ? '' : 's'}` : 'Pendiente'
    return { ...match, date:match.date || `Jornada ${match.matchday}`, raw_date:match.date, opponent, opponent_id:opponentId, venue, competition:match.competition_name || leagueName, status, postponed }
  })
}
