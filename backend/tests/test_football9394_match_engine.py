from statistics import mean

from backend.app.football9394.match_engine import FootballMatchEngine9394, FootballTactics9394, Footballer9394, TeamSheet9394


def player(i: int, pos: str, overall: int = 70) -> Footballer9394:
    gk = overall if pos == 'GK' else 10
    return Footballer9394(
        id=f'{pos}-{i}', name=f'{pos} {i}', position=pos, overall=overall,
        pace=overall, stamina=overall, technique=overall, short_pass=overall,
        long_pass=overall, creativity=overall, finishing=overall,
        heading=overall, tackling=overall, marking=overall,
        positioning=overall, discipline=70, leadership=70, goalkeeping=gk,
    )


def sheet(team_id: str, level: int = 70, tactics: FootballTactics9394 | None = None) -> TeamSheet9394:
    positions=['GK','RB','CB','CB','LB','RM','CM','CM','LM','ST','ST']
    starters=tuple(player(i,f'{pos}{team_id}',level) if pos!='GK' else player(i,'GK',level) for i,pos in enumerate(positions))
    # Make ids unique even though the helper embeds positions.
    starters=tuple(Footballer9394(**{**p.__dict__,'id':f'{team_id}-s-{i}'}) if hasattr(p,'__dict__') else p for i,p in enumerate(starters))
    # slots dataclasses have no __dict__; build explicitly instead.
    def clone(p,i,prefix):
        return Footballer9394(id=f'{team_id}-{prefix}-{i}',name=p.name,position=p.position,overall=p.overall,pace=p.pace,stamina=p.stamina,technique=p.technique,short_pass=p.short_pass,long_pass=p.long_pass,creativity=p.creativity,finishing=p.finishing,heading=p.heading,tackling=p.tackling,marking=p.marking,positioning=p.positioning,discipline=p.discipline,leadership=p.leadership,goalkeeping=p.goalkeeping)
    starters=tuple(clone(player(i,pos,level),i,'s') for i,pos in enumerate(positions))
    bench=tuple(clone(player(i,pos,level-2),i,'b') for i,pos in enumerate(['GK','DF','DF','MF','ST']))
    return TeamSheet9394(team_id,team_id,starters,bench,tactics or FootballTactics9394())


def test_engine_enforces_1993_94_matchday_squad_and_substitution_cap():
    engine=FootballMatchEngine9394()
    result=engine.simulate(sheet('HOME'),sheet('AWAY'),seed=42)
    assert result.home.substitutions <= 2
    assert result.away.substitutions <= 2
    assert result.home.possession + result.away.possession == 100
    assert result.played_minutes >= 91


def test_high_press_has_a_real_fatigue_and_discipline_tradeoff_over_many_matches():
    engine=FootballMatchEngine9394()
    high=FootballTactics9394(pressing='high',tempo='high')
    low=FootballTactics9394(pressing='low',tempo='slow')
    high_fouls=[]; low_fouls=[]
    for seed in range(80):
        high_fouls.append(engine.simulate(sheet('H',tactics=high),sheet('N'),seed=seed).home.fouls)
        low_fouls.append(engine.simulate(sheet('L',tactics=low),sheet('N'),seed=1000+seed).home.fouls)
    assert mean(high_fouls) > mean(low_fouls)


def test_stronger_side_scores_more_over_a_large_sample_without_guaranteed_results():
    engine=FootballMatchEngine9394()
    strong_goals=[]; weak_goals=[]; weak_wins=0
    for seed in range(220):
        result=engine.simulate(sheet('STRONG',78),sheet('WEAK',62),seed=seed)
        strong_goals.append(result.home.goals); weak_goals.append(result.away.goals)
        if result.away.goals > result.home.goals: weak_wins += 1
    assert mean(strong_goals) > mean(weak_goals)
    assert weak_wins > 0
    assert 1.4 < mean(strong_goals)+mean(weak_goals) < 4.0


def test_spanish_top_flight_profile_is_calibrated_near_1993_94_goal_environment():
    from backend.app.football9394.match_engine import SPAIN_PRIMERA_SIMULATION_1993_94
    from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
    from backend.app.football9394.team_builder import build_snapshot_team_sheet

    universe = default_runtime_snapshot()
    engine = FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94)
    sheets = {int(team["source_id"]): build_snapshot_team_sheet(universe, int(team["source_id"]))
              for team in universe.teams(league_id=1)}
    total_goals = 0
    fixtures = universe.league_calendar(1)
    for fixture in fixtures:
        home_id, away_id = int(fixture["home_team_id"]), int(fixture["away_team_id"])
        result = engine.simulate(
            sheets[home_id], sheets[away_id],
            seed=9394000 + int(fixture["matchday"]) * 100 + int(fixture["id"]),
        )
        total_goals += result.home.goals + result.away.goals

    observed = total_goals / len(fixtures)
    target = SPAIN_PRIMERA_SIMULATION_1993_94.target_goals_per_match
    assert target is not None
    assert abs(observed - target) < 0.08
