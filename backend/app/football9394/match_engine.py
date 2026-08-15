from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import exp
from random import Random
from typing import Iterable

from .laws import LAWS_1993_94, LawsOfGame9394


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _logistic(x: float) -> float:
    return 1.0 / (1.0 + exp(-x))


@dataclass(frozen=True, slots=True)
class Footballer9394:
    id: str
    name: str
    position: str
    overall: int
    pace: int = 60
    stamina: int = 60
    technique: int = 60
    short_pass: int = 60
    long_pass: int = 60
    creativity: int = 60
    finishing: int = 60
    heading: int = 60
    tackling: int = 60
    marking: int = 60
    positioning: int = 60
    discipline: int = 60
    leadership: int = 60
    goalkeeping: int = 10

    def __post_init__(self) -> None:
        for field_name in (
            "overall", "pace", "stamina", "technique", "short_pass", "long_pass",
            "creativity", "finishing", "heading", "tackling", "marking",
            "positioning", "discipline", "leadership", "goalkeeping",
        ):
            value = getattr(self, field_name)
            if not 1 <= int(value) <= 100:
                raise ValueError(f"{self.name}: {field_name} debe estar entre 1 y 100")


@dataclass(frozen=True, slots=True)
class SimulationProfile9394:
    """Competition/region calibration without changing the Laws of the Game.

    Historical competitions can share football semantics while differing in
    scoring environment, home advantage, physicality and tempo.  Profiles are
    explicit so a competition never inherits today's statistical environment.
    """

    id: str
    target_goals_per_match: float | None = None
    goal_conversion_multiplier: float = 1.0
    notable_attack_multiplier: float = 1.0
    foul_multiplier: float = 1.0
    home_advantage_rating: float = 2.4

    def __post_init__(self) -> None:
        if self.goal_conversion_multiplier <= 0 or self.notable_attack_multiplier <= 0 or self.foul_multiplier <= 0:
            raise ValueError("los multiplicadores de simulación deben ser positivos")


ERA_BASELINE_1993_94 = SimulationProfile9394(id="era_1993_94")
SPAIN_PRIMERA_SIMULATION_1993_94 = SimulationProfile9394(
    id="esp_primera_1993_94",
    target_goals_per_match=989 / 380,
    goal_conversion_multiplier=1.15,
)


@dataclass(frozen=True, slots=True)
class FootballTactics9394:
    formation: str = "4-4-2"
    mentality: str = "balanced"  # defensive | balanced | attacking
    tempo: str = "normal"  # slow | normal | high
    pressing: str = "medium"  # low | medium | high
    directness: str = "mixed"  # short | mixed | direct
    defensive_line: str = "medium"  # low | medium | high
    width: str = "normal"  # narrow | normal | wide
    offside_trap: bool = False
    marking: str = "zonal"  # zonal | man


@dataclass(frozen=True, slots=True)
class TeamSheet9394:
    team_id: str
    team_name: str
    starters: tuple[Footballer9394, ...]
    bench: tuple[Footballer9394, ...] = ()
    tactics: FootballTactics9394 = field(default_factory=FootballTactics9394)

    def validate(self, laws: LawsOfGame9394 = LAWS_1993_94) -> None:
        if len(self.starters) != laws.players_per_team:
            raise ValueError(f"{self.team_name}: deben iniciar exactamente {laws.players_per_team} jugadores")
        if len(self.bench) > laws.max_named_substitutes:
            raise ValueError(f"{self.team_name}: máximo {laws.max_named_substitutes} suplentes nombrados")
        ids = [player.id for player in (*self.starters, *self.bench)]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{self.team_name}: un futbolista no puede aparecer dos veces en el acta")
        goalkeepers = [p for p in self.starters if p.position.upper() in {"GK", "POR", "PORTERO"}]
        if not goalkeepers:
            raise ValueError(f"{self.team_name}: el once necesita portero")


@dataclass(frozen=True, slots=True)
class MatchEvent9394:
    minute: int
    kind: str
    team_id: str | None = None
    player_id: str | None = None
    player_name: str | None = None
    detail: str = ""


@dataclass(frozen=True, slots=True)
class TeamMatchStats9394:
    goals: int
    shots: int
    shots_on_target: int
    corners: int
    offsides: int
    fouls: int
    yellow_cards: int
    red_cards: int
    possession: int
    substitutions: int


@dataclass(frozen=True, slots=True)
class MatchResult9394:
    home_team_id: str
    away_team_id: str
    home: TeamMatchStats9394
    away: TeamMatchStats9394
    events: tuple[MatchEvent9394, ...]
    played_minutes: int


@dataclass(slots=True)
class _SideState:
    sheet: TeamSheet9394
    on_pitch: list[Footballer9394]
    bench: list[Footballer9394]
    fatigue: dict[str, float]
    yellow_by_player: dict[str, int]
    sent_off: set[str]
    goals: int = 0
    shots: int = 0
    shots_on_target: int = 0
    corners: int = 0
    offsides: int = 0
    fouls: int = 0
    yellows: int = 0
    reds: int = 0
    possession_ticks: int = 0
    substitutions: int = 0

    @classmethod
    def from_sheet(cls, sheet: TeamSheet9394) -> "_SideState":
        return cls(
            sheet=sheet,
            on_pitch=list(sheet.starters),
            bench=list(sheet.bench),
            fatigue={p.id: 0.0 for p in (*sheet.starters, *sheet.bench)},
            yellow_by_player={},
            sent_off=set(),
        )

    def available_players(self) -> list[Footballer9394]:
        return [p for p in self.on_pitch if p.id not in self.sent_off]

    def goalkeeper(self) -> Footballer9394:
        players = self.available_players()
        keepers = [p for p in players if p.position.upper() in {"GK", "POR", "PORTERO"}]
        return max(keepers or players, key=lambda p: p.goalkeeping)


class FootballMatchEngine9394:
    """First football-native 1993-94 match simulator.

    Match resolution is football-specific and deterministic for a given seed.
    The state is expressed in football terms: territory, shot creation,
    offside, fouls/cards, set pieces, fatigue and substitutions.  Later layers
    can replace probability functions without changing this public contract.
    """

    def __init__(
        self,
        laws: LawsOfGame9394 = LAWS_1993_94,
        profile: SimulationProfile9394 = ERA_BASELINE_1993_94,
    ):
        self.laws = laws
        self.profile = profile

    def simulate(self, home_sheet: TeamSheet9394, away_sheet: TeamSheet9394, *, seed: int = 1) -> MatchResult9394:
        home_sheet.validate(self.laws)
        away_sheet.validate(self.laws)
        rng = Random(seed)
        home = _SideState.from_sheet(home_sheet)
        away = _SideState.from_sheet(away_sheet)
        events: list[MatchEvent9394] = [MatchEvent9394(0, "kickoff", detail="Comienza el partido")]
        stoppage_first = rng.randint(0, 2)
        stoppage_second = rng.randint(1, 4)
        played_minutes = 90 + stoppage_second

        for minute in range(1, played_minutes + 1):
            if minute == 45:
                events.append(MatchEvent9394(45, "halftime", detail="Descanso"))
            if minute == 46:
                events.append(MatchEvent9394(46, "second_half", detail="Comienza la segunda parte"))

            self._accumulate_fatigue(home, minute)
            self._accumulate_fatigue(away, minute)
            if minute in (58, 70, 78):
                self._maybe_substitute(home, minute, rng, events)
                self._maybe_substitute(away, minute, rng, events)

            # The normal 90-minute clock excludes first-half added time in this
            # coarse engine; it is kept as an event/detail until the live clock
            # layer models stoppage explicitly.
            if minute == 45 and stoppage_first:
                events.append(MatchEvent9394(45, "stoppage_time", detail=f"{stoppage_first} min de añadido"))
            if minute == 90 and stoppage_second:
                events.append(MatchEvent9394(90, "stoppage_time", detail=f"{stoppage_second} min de añadido"))

            # Not every minute contains a notable attack.  A higher tempo and
            # attacking mentality produce more actions at the cost of fatigue.
            activity = (self._activity(home.sheet.tactics) + self._activity(away.sheet.tactics)) / 2
            activity = _clamp(activity * self.profile.notable_attack_multiplier, 0.20, 0.88)
            if rng.random() > activity:
                continue

            home_possession = self._possession_probability(home, away)
            attack, defend = (home, away) if rng.random() < home_possession else (away, home)
            attack.possession_ticks += 1
            self._resolve_attack(attack, defend, minute, rng, events)
            self._maybe_injury(attack, minute, rng, events)
            self._maybe_injury(defend, minute, rng, events)

        events.append(MatchEvent9394(played_minutes, "fulltime", detail="Final del partido"))
        total_possession = home.possession_ticks + away.possession_ticks
        home_poss = round(100 * home.possession_ticks / total_possession) if total_possession else 50
        away_poss = 100 - home_poss
        return MatchResult9394(
            home_team_id=home.sheet.team_id,
            away_team_id=away.sheet.team_id,
            home=self._stats(home, home_poss),
            away=self._stats(away, away_poss),
            events=tuple(events),
            played_minutes=played_minutes,
        )

    def _stats(self, side: _SideState, possession: int) -> TeamMatchStats9394:
        return TeamMatchStats9394(
            goals=side.goals,
            shots=side.shots,
            shots_on_target=side.shots_on_target,
            corners=side.corners,
            offsides=side.offsides,
            fouls=side.fouls,
            yellow_cards=side.yellows,
            red_cards=side.reds,
            possession=possession,
            substitutions=side.substitutions,
        )

    def _activity(self, tactics: FootballTactics9394) -> float:
        value = 0.53
        value += {"slow": -0.08, "normal": 0.0, "high": 0.07}.get(tactics.tempo, 0.0)
        value += {"defensive": -0.05, "balanced": 0.0, "attacking": 0.05}.get(tactics.mentality, 0.0)
        return _clamp(value, 0.36, 0.68)

    def _fatigue_multiplier(self, side: _SideState, player: Footballer9394) -> float:
        fatigue = side.fatigue.get(player.id, 0.0)
        return _clamp(1.0 - fatigue / 155.0, 0.66, 1.0)

    def _average(self, side: _SideState, attrs: Iterable[str]) -> float:
        players = side.available_players()
        if not players:
            return 1.0
        names = tuple(attrs)
        values = []
        for player in players:
            base = sum(float(getattr(player, attr)) for attr in names) / len(names)
            values.append(base * self._fatigue_multiplier(side, player))
        # A red card matters beyond losing one individual's rating.
        manpower = len(players) / self.laws.players_per_team
        return sum(values) / len(values) * (0.76 + 0.24 * manpower)

    def _possession_probability(self, home: _SideState, away: _SideState) -> float:
        home_mid = self._average(home, ("technique", "short_pass", "creativity", "positioning"))
        away_mid = self._average(away, ("technique", "short_pass", "creativity", "positioning"))
        home_bonus = self.profile.home_advantage_rating
        return _clamp(0.5 + (home_mid + home_bonus - away_mid) / 170.0, 0.27, 0.73)

    def _resolve_attack(self, attack: _SideState, defend: _SideState, minute: int, rng: Random, events: list[MatchEvent9394]) -> None:
        attack_t = attack.sheet.tactics
        defend_t = defend.sheet.tactics
        press = {"low": -0.01, "medium": 0.01, "high": 0.04}.get(defend_t.pressing, 0.0)
        discipline = self._average(defend, ("discipline",))
        foul_chance = _clamp((0.245 + press + (58.0 - discipline) / 720.0) * self.profile.foul_multiplier, 0.12, 0.46)
        if rng.random() < foul_chance:
            self._foul(defend, minute, rng, events)
            # Roughly one attacking free kick in four still develops into a shot.
            if rng.random() > 0.56:
                return

        direct = {"short": -0.02, "mixed": 0.0, "direct": 0.035}.get(attack_t.directness, 0.0)
        line = {"low": -0.015, "medium": 0.0, "high": 0.025}.get(defend_t.defensive_line, 0.0)
        trap = 0.03 if defend_t.offside_trap else 0.0
        pace = self._average(attack, ("pace", "positioning"))
        offside_chance = _clamp(0.045 + direct + line + trap - (pace - 60.0) / 1200.0, 0.015, 0.16)
        if rng.random() < offside_chance:
            attack.offsides += 1
            player = self._pick_attacker(attack, rng)
            events.append(MatchEvent9394(minute, "offside", attack.sheet.team_id, player.id, player.name, "Fuera de juego"))
            return

        creation = self._average(attack, ("technique", "short_pass", "creativity", "pace"))
        resistance = self._average(defend, ("tackling", "marking", "positioning", "stamina"))
        mentality = {"defensive": -0.16, "balanced": 0.0, "attacking": 0.16}.get(attack_t.mentality, 0.0)
        directness = {"short": 0.02, "mixed": 0.0, "direct": 0.03}.get(attack_t.directness, 0.0)
        shot_chance = _clamp(0.43 + (creation - resistance) / 210.0 + mentality + directness, 0.19, 0.69)
        if rng.random() >= shot_chance:
            # A broken attack can still earn a corner.
            if rng.random() < 0.16:
                attack.corners += 1
                events.append(MatchEvent9394(minute, "corner", attack.sheet.team_id, detail="Córner"))
            return

        shooter = self._pick_attacker(attack, rng)
        attack.shots += 1
        shot_skill = (shooter.finishing * 0.48 + shooter.technique * 0.22 + shooter.positioning * 0.18 + shooter.heading * 0.12)
        marking = self._average(defend, ("marking", "positioning"))
        on_target = _clamp(0.36 + (shot_skill - marking) / 220.0, 0.22, 0.67)
        if rng.random() >= on_target:
            events.append(MatchEvent9394(minute, "shot_off", attack.sheet.team_id, shooter.id, shooter.name, "Remate fuera"))
            return

        attack.shots_on_target += 1
        keeper = defend.goalkeeper()
        keeper_level = keeper.goalkeeping * 0.72 + keeper.positioning * 0.28
        chance_quality = shot_skill + (creation - resistance) * 0.22
        goal_probability = _clamp(
            (0.285 + (chance_quality - keeper_level) / 520.0) * self.profile.goal_conversion_multiplier,
            0.08,
            0.62,
        )
        if rng.random() < goal_probability:
            attack.goals += 1
            events.append(MatchEvent9394(minute, "goal", attack.sheet.team_id, shooter.id, shooter.name, "Gol"))
        else:
            # Saved/blocked shots yield corners at a plausible rate.
            if rng.random() < 0.27:
                attack.corners += 1
                events.append(MatchEvent9394(minute, "corner", attack.sheet.team_id, detail="Córner tras el remate"))
            events.append(MatchEvent9394(minute, "save", defend.sheet.team_id, keeper.id, keeper.name, "Parada"))

    def _pick_attacker(self, side: _SideState, rng: Random) -> Footballer9394:
        players = side.available_players()
        weights = []
        for p in players:
            pos = p.position.upper()
            role_weight = 2.4 if any(token in pos for token in ("ST", "FW", "DEL", "DC")) else 1.55 if any(token in pos for token in ("AM", "MP", "EXT", "W")) else 1.0 if any(token in pos for token in ("M", "MC")) else 0.45
            weights.append(max(0.1, role_weight * (0.6 + p.finishing / 120.0)))
        return rng.choices(players, weights=weights, k=1)[0]

    def _pick_defender_for_foul(self, side: _SideState, rng: Random) -> Footballer9394:
        players = side.available_players()
        weights = []
        for p in players:
            pos = p.position.upper()
            role_weight = 1.8 if any(token in pos for token in ("CB", "DF", "DEF", "LAT")) else 1.35 if any(token in pos for token in ("DM", "MC", "M")) else 0.7
            weights.append(role_weight * (1.25 - p.discipline / 180.0))
        return rng.choices(players, weights=weights, k=1)[0]

    def _foul(self, defend: _SideState, minute: int, rng: Random, events: list[MatchEvent9394]) -> None:
        player = self._pick_defender_for_foul(defend, rng)
        defend.fouls += 1
        events.append(MatchEvent9394(minute, "foul", defend.sheet.team_id, player.id, player.name, "Falta"))
        caution_chance = _clamp(0.10 + (60 - player.discipline) / 260.0, 0.06, 0.28)
        if rng.random() < caution_chance:
            previous = defend.yellow_by_player.get(player.id, 0)
            defend.yellow_by_player[player.id] = previous + 1
            defend.yellows += 1
            if previous >= 1:
                defend.reds += 1
                defend.sent_off.add(player.id)
                events.append(MatchEvent9394(minute, "second_yellow_red", defend.sheet.team_id, player.id, player.name, "Segunda amarilla y expulsión"))
            else:
                events.append(MatchEvent9394(minute, "yellow", defend.sheet.team_id, player.id, player.name, "Tarjeta amarilla"))
        elif rng.random() < 0.012:
            defend.reds += 1
            defend.sent_off.add(player.id)
            events.append(MatchEvent9394(minute, "red", defend.sheet.team_id, player.id, player.name, "Tarjeta roja"))

    def _accumulate_fatigue(self, side: _SideState, minute: int) -> None:
        t = side.sheet.tactics
        tempo = {"slow": 0.80, "normal": 1.0, "high": 1.22}.get(t.tempo, 1.0)
        press = {"low": 0.82, "medium": 1.0, "high": 1.24}.get(t.pressing, 1.0)
        for player in side.available_players():
            stamina_factor = 1.20 - player.stamina / 180.0
            side.fatigue[player.id] = min(100.0, side.fatigue.get(player.id, 0.0) + 0.43 * tempo * press * stamina_factor)

    def _maybe_substitute(self, side: _SideState, minute: int, rng: Random, events: list[MatchEvent9394]) -> None:
        if side.substitutions >= self.laws.max_used_substitutes or not side.bench:
            return
        candidates = [p for p in side.available_players() if p.position.upper() not in {"GK", "POR", "PORTERO"}]
        if not candidates:
            return
        tired = max(candidates, key=lambda p: side.fatigue.get(p.id, 0.0) - p.overall / 10.0)
        fatigue = side.fatigue.get(tired.id, 0.0)
        threshold = 25 if minute <= 60 else 31 if minute <= 72 else 35
        if fatigue < threshold and rng.random() > 0.16:
            return
        replacement = max(side.bench, key=lambda p: self._replacement_fit(p, tired))
        idx = side.on_pitch.index(tired)
        side.on_pitch[idx] = replacement
        side.bench.remove(replacement)
        side.substitutions += 1
        events.append(MatchEvent9394(minute, "substitution", side.sheet.team_id, replacement.id, replacement.name, f"Entra {replacement.name}; sale {tired.name}"))

    def _replacement_fit(self, replacement: Footballer9394, outgoing: Footballer9394) -> float:
        same_position = replacement.position.upper() == outgoing.position.upper()
        return replacement.overall + (12 if same_position else 0)

    def _maybe_injury(self, side: _SideState, minute: int, rng: Random, events: list[MatchEvent9394]) -> None:
        if rng.random() > 0.00125:
            return
        players = side.available_players()
        if not players:
            return
        player = rng.choice(players)
        events.append(MatchEvent9394(minute, "injury", side.sheet.team_id, player.id, player.name, "Problemas físicos"))
        # An injury does not always force the player off; when it does, the
        # historical two-substitute cap still applies.
        if side.substitutions < self.laws.max_used_substitutes and side.bench and rng.random() < 0.58:
            replacement = max(side.bench, key=lambda p: self._replacement_fit(p, player))
            idx = side.on_pitch.index(player)
            side.on_pitch[idx] = replacement
            side.bench.remove(replacement)
            side.substitutions += 1
            events.append(MatchEvent9394(minute, "injury_substitution", side.sheet.team_id, replacement.id, replacement.name, f"Entra {replacement.name}; sale lesionado {player.name}"))
