from __future__ import annotations

"""Executable 1993 runtimes for the two unusual league systems already audited.

These are intentionally explicit rather than squeezed into the standard league
class: APSL used bonus points and shootout decisions; the inaugural J.League
ranked by wins and split the year into two independent series.
"""

from dataclasses import dataclass
from random import Random
from typing import Iterable

from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, MatchResult9394, TeamSheet9394
from .schedule import LeagueFixture9394, generate_double_round_robin
from .scoring import APSL_1993
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .team_builder import build_snapshot_team_sheet


@dataclass(frozen=True, slots=True)
class DecidedMatch9394:
    home_team_id: str
    away_team_id: str
    regulation_home_goals: int
    regulation_away_goals: int
    winner_team_id: str
    loser_team_id: str
    decided_by: str  # regulation | extra_time | shootout

    @property
    def goal_difference_home(self) -> int:
        return self.regulation_home_goals - self.regulation_away_goals


@dataclass(frozen=True, slots=True)
class SpecialStanding9394:
    team_id: str
    played: int
    wins: int
    losses: int
    goals_for: int
    goals_against: int
    points: int | None
    position: int


@dataclass(frozen=True, slots=True)
class APSLSeasonResult9394:
    regular_table: tuple[SpecialStanding9394, ...]
    regular_matches: tuple[DecidedMatch9394, ...]
    semifinal_winners: tuple[str, str]
    champion_team_id: str
    runner_up_team_id: str


@dataclass(frozen=True, slots=True)
class JLeagueStageResult9394:
    name: str
    table: tuple[SpecialStanding9394, ...]
    matches: tuple[DecidedMatch9394, ...]
    winner_team_id: str
    runner_up_team_id: str


@dataclass(frozen=True, slots=True)
class JLeagueSeasonResult9394:
    suntory: JLeagueStageResult9394
    nicos: JLeagueStageResult9394
    championship_teams: tuple[str, str]
    championship_aggregate: tuple[int, int]
    champion_team_id: str
    runner_up_team_id: str


def _strength(sheet: TeamSheet9394) -> float:
    return sum(player.overall for player in sheet.starters) / len(sheet.starters)


def _resolve_no_draw(
    result: MatchResult9394,
    home: TeamSheet9394,
    away: TeamSheet9394,
    *,
    seed: int,
    golden_goal: bool,
) -> DecidedMatch9394:
    if result.home.goals != result.away.goals:
        winner = home.team_id if result.home.goals > result.away.goals else away.team_id
        loser = away.team_id if winner == home.team_id else home.team_id
        return DecidedMatch9394(home.team_id, away.team_id, result.home.goals, result.away.goals, winner, loser, "regulation")

    rng = Random(seed ^ 0x9394A5)
    home_probability = max(0.30, min(0.70, 0.5 + (_strength(home) - _strength(away)) / 120.0))
    # Extra time is always played.  If it supplies a goal, that goal decides the
    # match; otherwise the historically declared shootout decides it.
    extra_time_goal = rng.random() < (0.46 if golden_goal else 0.38)
    winner = home.team_id if rng.random() < home_probability else away.team_id
    loser = away.team_id if winner == home.team_id else home.team_id
    return DecidedMatch9394(
        home.team_id, away.team_id, result.home.goals, result.away.goals,
        winner, loser, "extra_time" if extra_time_goal else "shootout",
    )


def _four_meeting_schedule(team_ids: list[str]) -> tuple[LeagueFixture9394, ...]:
    base = generate_double_round_robin(team_ids)
    max_round = max(f.round_number for f in base)
    second_cycle = tuple(
        LeagueFixture9394(f.round_number + max_round, f.home_team_id, f.away_team_id)
        for f in base
    )
    return tuple(base) + second_cycle


def _special_table(
    team_ids: Iterable[str],
    matches: Iterable[DecidedMatch9394],
    *,
    apsl: bool,
) -> tuple[SpecialStanding9394, ...]:
    raw = {team_id: {"p":0,"w":0,"l":0,"gf":0,"ga":0,"pts":0} for team_id in team_ids}
    match_list = tuple(matches)
    for match in match_list:
        h, a = raw[match.home_team_id], raw[match.away_team_id]
        h["p"] += 1; a["p"] += 1
        h["gf"] += match.regulation_home_goals; h["ga"] += match.regulation_away_goals
        a["gf"] += match.regulation_away_goals; a["ga"] += match.regulation_home_goals
        win, loss = raw[match.winner_team_id], raw[match.loser_team_id]
        win["w"] += 1; loss["l"] += 1
        if apsl:
            if match.decided_by == "shootout":
                home_decision = "shootout_win" if match.winner_team_id == match.home_team_id else "shootout_loss"
                away_decision = "shootout_win" if match.winner_team_id == match.away_team_id else "shootout_loss"
            elif match.decided_by == "extra_time":
                home_decision = "extra_time_win" if match.winner_team_id == match.home_team_id else "loss"
                away_decision = "extra_time_win" if match.winner_team_id == match.away_team_id else "loss"
            else:
                home_decision = "regulation_win" if match.winner_team_id == match.home_team_id else "loss"
                away_decision = "regulation_win" if match.winner_team_id == match.away_team_id else "loss"
            h["pts"] += APSL_1993.points_for(home_decision, goals_scored=match.regulation_home_goals)
            a["pts"] += APSL_1993.points_for(away_decision, goals_scored=match.regulation_away_goals)

    def h2h_wins(team_id: str, tied: set[str]) -> int:
        return sum(m.winner_team_id == team_id for m in match_list if m.home_team_id in tied and m.away_team_id in tied)

    if apsl:
        ordered = sorted(raw, key=lambda t:(-raw[t]["pts"],-raw[t]["w"],-(raw[t]["gf"]-raw[t]["ga"]),-raw[t]["gf"],t))
    else:
        # J.League 1993: wins, goal difference, goals scored, head-to-head.
        ordered = sorted(raw, key=lambda t:(-raw[t]["w"],-(raw[t]["gf"]-raw[t]["ga"]),-raw[t]["gf"],t))
        i = 0
        while i < len(ordered):
            key = (raw[ordered[i]]["w"], raw[ordered[i]]["gf"]-raw[ordered[i]]["ga"], raw[ordered[i]]["gf"])
            j = i + 1
            while j < len(ordered) and (raw[ordered[j]]["w"], raw[ordered[j]]["gf"]-raw[ordered[j]]["ga"], raw[ordered[j]]["gf"]) == key:
                j += 1
            if j-i > 1:
                tied = set(ordered[i:j])
                ordered[i:j] = sorted(ordered[i:j], key=lambda t:(-h2h_wins(t,tied),t))
            i = j

    return tuple(SpecialStanding9394(
        team_id=t, played=raw[t]["p"], wins=raw[t]["w"], losses=raw[t]["l"],
        goals_for=raw[t]["gf"], goals_against=raw[t]["ga"], points=raw[t]["pts"] if apsl else None,
        position=i,
    ) for i,t in enumerate(ordered,1))


def _play_decided(
    engine: FootballMatchEngine9394, home: TeamSheet9394, away: TeamSheet9394,
    *, seed: int, golden_goal: bool,
) -> DecidedMatch9394:
    return _resolve_no_draw(engine.simulate(home, away, seed=seed), home, away, seed=seed, golden_goal=golden_goal)


def simulate_apsl_1993(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 1209394,
) -> APSLSeasonResult9394:
    universe = universe or default_runtime_snapshot()
    teams = universe.teams(league_id=120)
    if len(teams) != 7:
        raise ValueError(f"APSL 1993: se esperaban 7 clubes y hay {len(teams)}")
    ids = [str(team["source_id"]) for team in teams]
    sheets = {team_id: build_snapshot_team_sheet(universe, int(team_id)) for team_id in ids}
    engine = FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)
    matches = []
    for index, fixture in enumerate(_four_meeting_schedule(ids)):
        matches.append(_play_decided(engine, sheets[fixture.home_team_id], sheets[fixture.away_team_id], seed=seed_base+index, golden_goal=False))
    table = _special_table(ids, matches, apsl=True)
    if not all(row.played == 24 for row in table):
        raise AssertionError("APSL 1993: el calendario regular no produjo 24 partidos por club")

    semifinal_pairs = ((table[0].team_id, table[3].team_id), (table[1].team_id, table[2].team_id))
    semifinal_winners = []
    for index, (home_id, away_id) in enumerate(semifinal_pairs):
        semifinal_winners.append(_play_decided(engine, sheets[home_id], sheets[away_id], seed=seed_base+1000+index, golden_goal=False).winner_team_id)
    finalist_a, finalist_b = semifinal_winners
    final = _play_decided(engine, sheets[finalist_a], sheets[finalist_b], seed=seed_base+1100, golden_goal=False)
    return APSLSeasonResult9394(table, tuple(matches), tuple(semifinal_winners), final.winner_team_id, final.loser_team_id)


def _simulate_j_stage(
    name: str, ids: list[str], sheets: dict[str, TeamSheet9394], engine: FootballMatchEngine9394, seed_base: int,
) -> JLeagueStageResult9394:
    matches = []
    for index, fixture in enumerate(generate_double_round_robin(ids)):
        matches.append(_play_decided(engine, sheets[fixture.home_team_id], sheets[fixture.away_team_id], seed=seed_base+index, golden_goal=True))
    table = _special_table(ids, matches, apsl=False)
    if not all(row.played == 18 for row in table):
        raise AssertionError(f"J.League {name}: cada club debe jugar 18 partidos")
    return JLeagueStageResult9394(name, table, tuple(matches), table[0].team_id, table[1].team_id)


def _two_leg_championship(
    engine: FootballMatchEngine9394, sheets: dict[str, TeamSheet9394], first: str, second: str, seed_base: int,
) -> tuple[str, str, tuple[int, int]]:
    leg1 = engine.simulate(sheets[first], sheets[second], seed=seed_base)
    leg2 = engine.simulate(sheets[second], sheets[first], seed=seed_base+1)
    first_goals = leg1.home.goals + leg2.away.goals
    second_goals = leg1.away.goals + leg2.home.goals
    if first_goals == second_goals:
        decider = _resolve_no_draw(leg2, sheets[second], sheets[first], seed=seed_base+2, golden_goal=True)
        winner = decider.winner_team_id
    else:
        winner = first if first_goals > second_goals else second
    loser = second if winner == first else first
    return winner, loser, (first_goals, second_goals)


def simulate_jleague_1993(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 1119394,
) -> JLeagueSeasonResult9394:
    universe = universe or default_runtime_snapshot()
    teams = universe.teams(league_id=111)
    if len(teams) != 10:
        raise ValueError(f"J.League 1993: se esperaban 10 clubes y hay {len(teams)}")
    ids = [str(team["source_id"]) for team in teams]
    sheets = {team_id: build_snapshot_team_sheet(universe, int(team_id)) for team_id in ids}
    engine = FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)
    suntory = _simulate_j_stage("Suntory Series", ids, sheets, engine, seed_base)
    nicos = _simulate_j_stage("NICOS Series", ids, sheets, engine, seed_base+10000)

    first, second = suntory.winner_team_id, nicos.winner_team_id
    if first == second:
        # Historical contingency: the two stage runners-up meet and the winner
        # earns the right to challenge the double stage winner.
        contender = _play_decided(
            engine, sheets[suntory.runner_up_team_id], sheets[nicos.runner_up_team_id],
            seed=seed_base+20000, golden_goal=True,
        ).winner_team_id
        first, second = first, contender
    winner, loser, aggregate = _two_leg_championship(engine, sheets, first, second, seed_base+21000)
    return JLeagueSeasonResult9394(suntory, nicos, (first, second), aggregate, winner, loser)
