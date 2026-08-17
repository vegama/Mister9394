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
    acceleration: int = 60
    strength: int = 60
    work_rate: int = 60
    aggression: int = 60
    anticipation: int = 60
    consistency: int = 70
    vision: int = 60
    dribbling: int = 60
    off_ball: int = 60
    shot_power: int = 60
    free_kicks: int = 50
    penalties: int = 50
    jumping: int = 60
    injury_proneness: int = 0
    individualist: bool = False
    killer_pass: bool = False
    holds_ball: bool = False
    long_shots: bool = False
    cuts_inside: bool = False
    first_time_play: bool = False
    dives: bool = False
    role_code: str = ""
    squad_slot: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "overall", "pace", "stamina", "technique", "short_pass", "long_pass",
            "creativity", "finishing", "heading", "tackling", "marking",
            "positioning", "discipline", "leadership", "goalkeeping", "acceleration",
            "strength", "work_rate", "aggression", "anticipation", "consistency",
            "vision", "dribbling", "off_ball", "shot_power", "free_kicks", "penalties", "jumping",
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
    goal_conversion_multiplier=1.17,
)


@dataclass(frozen=True, slots=True)
class RefereeProfile9394:
    source_id: str
    name: str
    yellow_tendency: float = 4.5
    red_tendency: float = 0.45
    quality: int = 65
    temporal_confidence: str | None = None

    def __post_init__(self) -> None:
        if self.yellow_tendency < 0 or self.red_tendency < 0:
            raise ValueError("las tendencias arbitrales no pueden ser negativas")
        if not 1 <= int(self.quality) <= 100:
            raise ValueError("la calidad arbitral debe estar entre 1 y 100")




@dataclass(frozen=True, slots=True)
class MatchVenue9394:
    source_id: str
    name: str
    city_name: str | None = None
    width_m: int | None = None
    length_m: int | None = None
    grass_quality: int | None = None
    capacity: int | None = None
    climate_name: str | None = None
    temporal_confidence: str | None = None

    def __post_init__(self) -> None:
        if self.width_m is not None and not 45 <= int(self.width_m) <= 100:
            raise ValueError("anchura de campo fuera de rango")
        if self.length_m is not None and not 80 <= int(self.length_m) <= 130:
            raise ValueError("longitud de campo fuera de rango")
        if self.grass_quality is not None and not 0 <= int(self.grass_quality) <= 100:
            raise ValueError("calidad del césped fuera de rango")


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
    build_up: str = "balanced"  # patient | balanced | early
    final_third: str = "mixed"  # mixed | crosses | through
    transition: str = "balanced"  # hold | balanced | counter

    def __post_init__(self) -> None:
        allowed = {
            "formation": {"4-4-2", "4-3-3", "4-2-3-1", "4-5-1", "4-4-1-1", "4-3-1-2", "4-2-4", "3-5-2", "3-4-3", "3-4-1-2", "5-3-2", "5-4-1", "5-2-3"},
            "mentality": {"defensive", "balanced", "attacking"},
            "tempo": {"slow", "normal", "high"},
            "pressing": {"low", "medium", "high"},
            "directness": {"short", "mixed", "direct"},
            "defensive_line": {"low", "medium", "high"},
            "width": {"narrow", "normal", "wide"},
            "marking": {"zonal", "man"},
            "build_up": {"patient", "balanced", "early"},
            "final_third": {"mixed", "crosses", "through"},
            "transition": {"hold", "balanced", "counter"},
        }
        for field_name, values in allowed.items():
            if getattr(self, field_name) not in values:
                raise ValueError(f"{field_name}: opción táctica 1993-94 no válida")


def tactical_identity_9394(tactics: FootballTactics9394) -> dict[str, float | str]:
    """Human-readable tactical fingerprint used by engine, API and UX.

    Values are small on purpose: the squad remains more important than a
    dropdown, while combinations can create clearly different football.
    """
    formation = {
        "4-4-2": (0.00, 0.00, 0.00, "Equilibrio clásico"),
        "4-3-3": (0.035, 0.010, -0.010, "Tres atacantes y amplitud ofensiva"),
        "4-2-3-1": (0.020, 0.035, 0.015, "Doble pivote y tres líneas de creación"),
        "4-5-1": (-0.010, 0.030, 0.025, "Densidad de centro del campo y una referencia"),
        "4-4-1-1": (0.005, 0.020, 0.010, "Dos líneas de cuatro y mediapunta"),
        "4-3-1-2": (0.025, 0.025, -0.005, "Rombo interior y dos puntas"),
        "4-2-4": (0.065, -0.020, -0.025, "Cuatro atacantes y mucho riesgo"),
        "3-5-2": (0.015, 0.035, -0.005, "Superioridad interior y carrileros"),
        "3-4-3": (0.055, 0.015, -0.020, "Tres centrales y tres atacantes"),
        "3-4-1-2": (0.035, 0.025, -0.010, "Mediapunta entre líneas y dos puntas"),
        "5-3-2": (-0.020, -0.010, 0.040, "Bloque protegido y salida con dos puntas"),
        "5-4-1": (-0.035, -0.005, 0.055, "Bloque de cinco y cuatro por delante"),
        "5-2-3": (0.015, -0.015, 0.025, "Cinco atrás y tres amenazas de salida"),
    }[tactics.formation]
    return {
        "attack": formation[0],
        "possession": formation[1],
        "defence": formation[2],
        "formation_label": formation[3],
        "risk": {"defensive": -0.12, "balanced": 0.0, "attacking": 0.14}[tactics.mentality],
        "tempo_load": {"slow": -0.12, "normal": 0.0, "high": 0.16}[tactics.tempo],
        "press_intensity": {"low": -0.10, "medium": 0.0, "high": 0.15}[tactics.pressing],
        "directness_bias": {"short": -0.06, "mixed": 0.0, "direct": 0.08}[tactics.directness],
        "line_risk": {"low": -0.06, "medium": 0.0, "high": 0.08}[tactics.defensive_line],
        "width_attack": {"narrow": -0.025, "normal": 0.0, "wide": 0.035}[tactics.width],
        "marking_contact": 0.035 if tactics.marking == "man" else 0.0,
        "offside_aggression": 0.045 if tactics.offside_trap else 0.0,
        "build_up_control": {"patient": 0.045, "balanced": 0.0, "early": -0.025}[tactics.build_up],
        "final_third_cross": {"mixed": 0.0, "crosses": 0.065, "through": -0.015}[tactics.final_third],
        "final_third_through": {"mixed": 0.0, "crosses": -0.015, "through": 0.065}[tactics.final_third],
        "transition_attack": {"hold": -0.045, "balanced": 0.0, "counter": 0.060}[tactics.transition],
    }


@dataclass(frozen=True, slots=True)
class TeamSheet9394:
    team_id: str
    team_name: str
    starters: tuple[Footballer9394, ...]
    bench: tuple[Footballer9394, ...] = ()
    tactics: FootballTactics9394 = field(default_factory=FootballTactics9394)
    manager_source_id: str | None = None
    manager_name: str | None = None
    manager_quality: int | None = None
    manager_tendency: str = "normal"
    rotation_frequency: str = "normal"
    set_piece_usage: str = "normal"
    manager_discipline: str = "balanced"
    tactical_familiarity: int = 70
    individual_instructions: dict[str, dict[str, str]] = field(default_factory=dict)
    opposition_instructions: dict[str, dict[str, object]] = field(default_factory=dict)
    set_piece_takers: dict[str, str] = field(default_factory=dict)
    attacking_tactics: FootballTactics9394 | None = None
    defensive_tactics: FootballTactics9394 | None = None

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
    secondary_player_id: str | None = None
    secondary_player_name: str | None = None


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
    referee_id: str | None = None
    referee_name: str | None = None
    referee_source_confidence: str | None = None
    venue_id: str | None = None
    venue_name: str | None = None
    venue_city: str | None = None
    venue_source_confidence: str | None = None


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
    match_form: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_sheet(cls, sheet: TeamSheet9394) -> "_SideState":
        return cls(
            sheet=sheet,
            on_pitch=list(sheet.starters),
            bench=list(sheet.bench),
            fatigue={p.id: 0.0 for p in (*sheet.starters, *sheet.bench)},
            yellow_by_player={},
            sent_off=set(),
            match_form={p.id: 1.0 for p in (*sheet.starters, *sheet.bench)},
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

    def simulate(self, home_sheet: TeamSheet9394, away_sheet: TeamSheet9394, *, seed: int = 1, referee: RefereeProfile9394 | None = None, venue: MatchVenue9394 | None = None) -> MatchResult9394:
        home_sheet.validate(self.laws)
        away_sheet.validate(self.laws)
        rng = Random(seed)
        home = _SideState.from_sheet(home_sheet)
        away = _SideState.from_sheet(away_sheet)
        self._roll_match_form(home, rng)
        self._roll_match_form(away, rng)
        events: list[MatchEvent9394] = [MatchEvent9394(0, "kickoff", detail="Comienza el partido")]
        stoppage_first = rng.randint(0, 2)
        stoppage_second = rng.randint(1, 4)
        played_minutes = 90 + stoppage_second

        for minute in range(1, played_minutes + 1):
            if minute == 45:
                events.append(MatchEvent9394(45, "halftime", detail="Descanso"))
            if minute == 46:
                events.append(MatchEvent9394(46, "second_half", detail="Comienza la segunda parte"))

            self._accumulate_fatigue(home, minute, venue=venue)
            self._accumulate_fatigue(away, minute, venue=venue)
            if minute in (58, 70, 78):
                self._maybe_manager_adjustment(home, away, minute, events)
                self._maybe_manager_adjustment(away, home, minute, events)
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
            activity = (self._activity(home.sheet.tactics, venue=venue) + self._activity(away.sheet.tactics, venue=venue)) / 2
            activity = _clamp(activity * self.profile.notable_attack_multiplier, 0.20, 0.88)
            if rng.random() > activity:
                continue

            home_possession = self._possession_probability(home, away, venue=venue)
            attack, defend = (home, away) if rng.random() < home_possession else (away, home)
            attack.possession_ticks += 1
            self._resolve_attack(attack, defend, minute, rng, events, referee=referee, venue=venue)
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
            referee_id=(referee.source_id if referee else None),
            referee_name=(referee.name if referee else None),
            referee_source_confidence=(referee.temporal_confidence if referee else None),
            venue_id=(venue.source_id if venue else None),
            venue_name=(venue.name if venue else None),
            venue_city=(venue.city_name if venue else None),
            venue_source_confidence=(venue.temporal_confidence if venue else None),
        )

    def _roll_match_form(self, side: _SideState, rng: Random) -> None:
        for player in (*side.sheet.starters, *side.sheet.bench):
            # Source Consistencia narrows or widens match-to-match execution.
            spread = max(.018, .105 - int(player.consistency) * .00082)
            side.match_form[player.id] = _clamp(1.0 + rng.uniform(-spread, spread), .88, 1.12)

    def _maybe_manager_adjustment(self, side: _SideState, opponent: _SideState, minute: int, events: list[MatchEvent9394]) -> None:
        """React to score *and* observable match problems.

        P5 keeps coaching causal: a good manager does not add rating points.
        Instead, from the second half onward, he can respond to being outshot,
        losing the midfield or failing to turn superiority into chances.
        """
        if not side.sheet.manager_source_id:
            return
        score = side.goals - opponent.goals
        quality = int(side.sheet.manager_quality or 60)
        current = side.sheet.tactics
        target = None
        detail = None
        if score < 0 and minute >= (70 if quality < 60 else 58):
            target = side.sheet.attacking_tactics or replace(current, mentality="attacking", tempo="high", pressing="high", defensive_line="high")
            detail = f"{side.sheet.manager_name or 'El entrenador'} arriesga para buscar el empate"
        elif score > 0 and minute >= (80 if side.sheet.manager_tendency == "attacking" else 68):
            target = side.sheet.defensive_tactics or replace(current, mentality="defensive", tempo="slow", defensive_line="low")
            detail = f"{side.sheet.manager_name or 'El entrenador'} protege la ventaja"
        elif quality >= 72 and minute >= 58 and opponent.shots >= side.shots + 4:
            # The opponent is producing too much.  A source defensive variant is
            # preferred; otherwise the coach reduces the space behind the line.
            target = side.sheet.defensive_tactics or replace(current, defensive_line="low", pressing="medium", mentality="balanced")
            detail = f"{side.sheet.manager_name or 'El entrenador'} corrige el plan: el rival estaba llegando demasiado"
        elif quality >= 76 and minute >= 58 and opponent.possession_ticks > max(8, side.possession_ticks * 1.45):
            # Regain a foothold instead of receiving a hidden possession bonus.
            target = replace(current, pressing="high", directness="short" if current.directness != "direct" else "mixed")
            detail = f"{side.sheet.manager_name or 'El entrenador'} intenta recuperar el centro del campo"
        elif quality >= 82 and minute >= 70 and score == 0 and side.shots >= opponent.shots + 4 and current.mentality != "attacking":
            target = replace(current, mentality="attacking", tempo="high")
            detail = f"{side.sheet.manager_name or 'El entrenador'} detecta superioridad y acelera para ir a por el partido"
        if target is not None and target != current:
            side.sheet = replace(side.sheet, tactics=target)
            events.append(MatchEvent9394(minute, "tactical_adjustment", side.sheet.team_id, detail=detail or "Ajuste táctico"))

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

    def _activity(self, tactics: FootballTactics9394, *, venue: MatchVenue9394 | None = None) -> float:
        identity = tactical_identity_9394(tactics)
        value = 0.53
        value += {"slow": -0.08, "normal": 0.0, "high": 0.07}[tactics.tempo]
        value += {"defensive": -0.05, "balanced": 0.0, "attacking": 0.05}[tactics.mentality]
        value += float(identity["attack"]) * 0.55
        value += {"hold": -0.035, "balanced": 0.0, "counter": 0.035}[tactics.transition]
        value += {"patient": -0.025, "balanced": 0.0, "early": 0.025}[tactics.build_up]
        if venue and venue.grass_quality is not None:
            # A poor surface suppresses clean high-tempo sequences a little; a
            # pristine one helps, but the team quality remains overwhelmingly
            # more important than the stadium.
            grass = _clamp((int(venue.grass_quality) - 70) / 900.0, -.035, .035)
            value += grass * (1.15 if tactics.directness == "short" else .65)
        return _clamp(value, 0.34, 0.72)

    def _fatigue_multiplier(self, side: _SideState, player: Footballer9394) -> float:
        fatigue = side.fatigue.get(player.id, 0.0)
        physical = _clamp(1.0 - fatigue / 155.0, 0.66, 1.0)
        return physical * float(side.match_form.get(player.id, 1.0))

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

    def _possession_probability(self, home: _SideState, away: _SideState, *, venue: MatchVenue9394 | None = None) -> float:
        home_mid = self._average(home, ("technique", "short_pass", "creativity", "positioning"))
        away_mid = self._average(away, ("technique", "short_pass", "creativity", "positioning"))
        home_id = tactical_identity_9394(home.sheet.tactics)
        away_id = tactical_identity_9394(away.sheet.tactics)
        home_style = float(home_id["possession"]) + ({"short": .035, "mixed": 0.0, "direct": -.025}[home.sheet.tactics.directness]) + float(home_id["build_up_control"])
        away_style = float(away_id["possession"]) + ({"short": .035, "mixed": 0.0, "direct": -.025}[away.sheet.tactics.directness]) + float(away_id["build_up_control"])
        home_style -= max(0.0, 62.0 - float(home.sheet.tactical_familiarity)) / 700.0
        away_style -= max(0.0, 62.0 - float(away.sheet.tactical_familiarity)) / 700.0
        press_swing = ({"low": -.010, "medium": 0.0, "high": .018}[home.sheet.tactics.pressing] - {"low": -.010, "medium": 0.0, "high": .018}[away.sheet.tactics.pressing])
        # Source-backed ``conservar balón`` is a behavioural tendency, not a
        # hidden rating boost.  A side containing more such players is slightly
        # better at keeping possessions alive, with a deliberately small cap so
        # that midfield quality and tactical intent remain dominant.
        home_holders = sum(1 for player in home.available_players() if player.holds_ball)
        away_holders = sum(1 for player in away.available_players() if player.holds_ball)
        hold_swing = _clamp((home_holders - away_holders) * .003, -.018, .018)
        surface_swing = 0.0
        if venue and venue.grass_quality is not None and int(venue.grass_quality) < 65:
            roughness = (65 - int(venue.grass_quality)) / 1000.0
            if home.sheet.tactics.directness == "short": surface_swing -= roughness
            if away.sheet.tactics.directness == "short": surface_swing += roughness
        home_bonus = self.profile.home_advantage_rating
        return _clamp(0.5 + (home_mid + home_bonus - away_mid) / 170.0 + home_style - away_style + press_swing + hold_swing + surface_swing, 0.24, 0.76)

    def _resolve_attack(self, attack: _SideState, defend: _SideState, minute: int, rng: Random, events: list[MatchEvent9394], *, referee: RefereeProfile9394 | None = None, venue: MatchVenue9394 | None = None) -> None:
        attack_t = attack.sheet.tactics
        defend_t = defend.sheet.tactics
        press = {"low": -0.01, "medium": 0.01, "high": 0.04}.get(defend_t.pressing, 0.0)
        targeted_orders = [row for pid, row in (defend.sheet.opposition_instructions or {}).items() if any(str(p.id) == str(pid) for p in attack.available_players())]
        extra_press = min(.018, sum(1 for row in targeted_orders if row.get("press")) * .0045)
        extra_mark = min(.018, sum(1 for row in targeted_orders if row.get("tight_mark")) * .0045)
        marking_contact = (0.026 if defend_t.marking == "man" else -0.004) + extra_mark
        press += extra_press
        discipline = self._average(defend, ("discipline",))
        aggression = self._average(defend, ("aggression", "work_rate"))
        divers = sum(1 for p in attack.available_players() if p.dives)
        # ``Piscinero`` already makes a foul/penalty appeal more likely.  The
        # source trait also carries a small downside: occasionally the referee
        # identifies simulation and cautions the offender.  Keep this rare; it
        # is a behavioural consequence, not a blanket discipline penalty.
        diving_candidates = [p for p in attack.available_players() if p.dives]
        if diving_candidates and rng.random() < min(.010, len(diving_candidates) * .0015):
            diver = rng.choice(diving_candidates)
            previous = int(attack.yellow_by_player.get(diver.id, 0))
            attack.yellow_by_player[diver.id] = previous + 1
            attack.yellows += 1
            events.append(MatchEvent9394(minute, "yellow", attack.sheet.team_id, diver.id, diver.name, "Amonestado por simulación"))
            if previous >= 1:
                attack.reds += 1
                attack.sent_off.add(diver.id)
                events.append(MatchEvent9394(minute, "red", attack.sheet.team_id, diver.id, diver.name, "Segunda amarilla por simulación"))
        foul_chance = _clamp(
            (0.235 + press + marking_contact + (58.0 - discipline) / 720.0 + (aggression - 65.0) / 1600.0 + divers * .0025)
            * self.profile.foul_multiplier,
            0.10, 0.49,
        )
        if rng.random() < foul_chance:
            self._foul(defend, minute, rng, events, referee=referee)
            # The coarse engine has no x/y coordinates. Only a small share of
            # attacking fouls are treated as being inside/directly around the area.
            if rng.random() < (0.010 + divers * .0015):
                self._resolve_penalty(attack, defend, minute, rng, events)
                return
            if rng.random() < .075:
                self._resolve_free_kick(attack, defend, minute, rng, events)
                return
            if rng.random() > 0.56:
                return

        direct = {"short": -0.02, "mixed": 0.0, "direct": 0.035}.get(attack_t.directness, 0.0)
        line = {"low": -0.015, "medium": 0.0, "high": 0.028}.get(defend_t.defensive_line, 0.0)
        trap = 0.045 if defend_t.offside_trap else 0.0
        pace = self._average(attack, ("pace", "off_ball", "anticipation"))
        offside_chance = _clamp(0.043 + direct + line + trap - (pace - 60.0) / 1100.0, 0.012, 0.19)
        if rng.random() < offside_chance:
            attack.offsides += 1
            player = self._pick_attacker(attack, rng)
            events.append(MatchEvent9394(minute, "offside", attack.sheet.team_id, player.id, player.name, "Fuera de juego"))
            return

        creation = self._average(attack, ("technique", "short_pass", "vision", "off_ball"))
        resistance = self._average(defend, ("tackling", "marking", "positioning", "anticipation"))
        attack_id = tactical_identity_9394(attack_t); defend_id = tactical_identity_9394(defend_t)
        familiarity_penalty = max(0.0, 65.0 - float(attack.sheet.tactical_familiarity)) / 420.0
        mentality = {"defensive": -0.15, "balanced": 0.0, "attacking": 0.15}.get(attack_t.mentality, 0.0)
        directness = {"short": 0.018, "mixed": 0.0, "direct": 0.028}.get(attack_t.directness, 0.0)
        width = {"narrow": .018 if attack_t.directness == "short" else -.015, "normal": 0.0, "wide": .032}.get(attack_t.width, 0.0)
        if venue and venue.width_m is not None:
            pitch_width = _clamp((int(venue.width_m) - 68) / 260.0, -.025, .025)
            if attack_t.width == "wide": width += pitch_width
            elif attack_t.width == "narrow": width -= pitch_width * .45
        defensive_marking = .026 if defend_t.marking == "man" else .012
        shape_attack = float(attack_id["attack"]); shape_defence = float(defend_id["defence"])
        line_risk = 0.0
        if defend_t.defensive_line == "high" and pace >= 70:
            line_risk += min(.055, (pace - 68) / 420.0)
        if defend_t.offside_trap and pace >= 74:
            line_risk += .018
        defensive_error = False
        error_pressure = ({"low": -.006, "medium": .0, "high": .018}.get(attack_t.pressing, 0.0)
                          + max(0.0, (68.0 - resistance) / 1100.0))
        if rng.random() < _clamp(.018 + error_pressure, .008, .065):
            defensive_error = True
            resistance -= 8.0
            events.append(MatchEvent9394(minute, "defensive_error", defend.sheet.team_id, detail=f"{defend.sheet.team_name} pierde el control bajo presión"))
        phase_bonus = float(attack_id["transition_attack"]) * .35
        if attack_t.final_third == "through" and creation >= resistance:
            phase_bonus += .018
        elif attack_t.final_third == "crosses" and attack_t.width == "wide":
            phase_bonus += .015
        shot_chance = _clamp(0.42 + (creation - resistance) / 210.0 + mentality + directness + width + shape_attack - shape_defence - defensive_marking + line_risk + phase_bonus - familiarity_penalty + (.035 if defensive_error else 0.0), 0.16, 0.74)
        if rng.random() >= shot_chance:
            corner_chance = 0.13 + ({"narrow": -0.025, "normal": 0.0, "wide": 0.065}.get(attack_t.width, 0.0))
            if rng.random() < corner_chance:
                attack.corners += 1
                events.append(MatchEvent9394(minute, "corner", attack.sheet.team_id, detail="Córner"))
                routine = {"low": .27, "normal": .32, "high": .38}.get(attack.sheet.set_piece_usage, .32)
                if rng.random() < routine:
                    self._resolve_corner(attack, defend, minute, rng, events)
            return

        creator = self._pick_creator(attack, rng)
        shooter = self._pick_attacker(attack, rng)
        if shooter.id == creator.id:
            alternatives = [p for p in attack.available_players() if p.id != shooter.id]
            if alternatives:
                creator = max(alternatives, key=lambda p: p.vision + p.short_pass + (18 if p.killer_pass else 0))
        chance_type, chance_detail = self._chance_type(attack, shooter, creator, rng)
        events.append(MatchEvent9394(minute, "chance", attack.sheet.team_id, creator.id, creator.name, chance_detail, shooter.id, shooter.name))

        attack.shots += 1
        shot_skill = shooter.finishing * 0.40 + shooter.technique * 0.18 + shooter.off_ball * 0.16 + shooter.anticipation * 0.10 + shooter.heading * 0.08 + shooter.shot_power * 0.08
        if chance_type == "cross":
            shot_skill = shooter.heading * .38 + shooter.jumping * .20 + shooter.finishing * .22 + shooter.positioning * .20
        elif chance_type == "long_shot":
            shot_skill = shooter.shot_power * .34 + shooter.technique * .24 + shooter.finishing * .20 + shooter.vision * .10 + shooter.consistency * .12 - 6
        elif chance_type == "individual":
            shot_skill = shooter.dribbling * .28 + shooter.finishing * .34 + shooter.pace * .16 + shooter.technique * .22
        elif chance_type == "through_ball":
            shot_skill += max(0, creator.vision - 65) * .10 + (4 if creator.killer_pass else 0)
        if shooter.first_time_play and chance_type in {"cross", "through_ball", "combination"}:
            shot_skill += 3.5
        marking_level = self._average(defend, ("marking", "positioning", "anticipation"))
        on_target = _clamp(0.355 + (shot_skill - marking_level) / 225.0, 0.20, 0.68)
        if chance_type == "long_shot":
            on_target -= .045
        if rng.random() >= on_target:
            events.append(MatchEvent9394(minute, "shot_off", attack.sheet.team_id, shooter.id, shooter.name, "Remate fuera"))
            return

        attack.shots_on_target += 1
        keeper = defend.goalkeeper()
        keeper_level = keeper.goalkeeping * 0.68 + keeper.positioning * 0.22 + keeper.anticipation * .10
        chance_quality = shot_skill + (creation - resistance) * 0.20
        goal_probability = _clamp(
            (0.275 + (chance_quality - keeper_level) / 525.0) * self.profile.goal_conversion_multiplier,
            0.07, 0.60,
        )
        if chance_type == "long_shot": goal_probability *= .78
        if chance_type == "cross": goal_probability *= .91
        if rng.random() < goal_probability:
            attack.goals += 1
            events.append(MatchEvent9394(minute, "goal", attack.sheet.team_id, shooter.id, shooter.name, f"Gol · {chance_detail.lower()}"))
            # Individual carries and long shots are less likely to have a formal assist.
            assist_chance = .38 if chance_type in {"individual", "long_shot"} else .82
            if creator.id != shooter.id and rng.random() < assist_chance:
                events.append(MatchEvent9394(minute, "assist", attack.sheet.team_id, creator.id, creator.name, f"Asistencia de {creator.name}", shooter.id, shooter.name))
        else:
            if rng.random() < 0.25:
                attack.corners += 1
                events.append(MatchEvent9394(minute, "corner", attack.sheet.team_id, detail="Córner tras el remate"))
            events.append(MatchEvent9394(minute, "save", defend.sheet.team_id, keeper.id, keeper.name, "Parada"))
            # A small share of saves remain alive: second balls are a visible
            # football cause, not an extra anonymous goal roll.
            rebound_control = self._average(attack, ("off_ball", "anticipation", "work_rate"))
            defensive_reaction = self._average(defend, ("positioning", "anticipation", "work_rate"))
            rebound_chance = _clamp(.055 + (rebound_control - defensive_reaction) / 700.0, .025, .105)
            if rng.random() < rebound_chance:
                rebounder = self._pick_attacker(attack, rng)
                events.append(MatchEvent9394(minute, "second_ball", attack.sheet.team_id, rebounder.id, rebounder.name, f"{rebounder.name} llega al rechace"))
                attack.shots += 1
                rebound_on_target = _clamp(.42 + (rebounder.finishing - defend.goalkeeper().goalkeeping) / 360.0, .26, .62)
                if rng.random() < rebound_on_target:
                    attack.shots_on_target += 1
                    rebound_goal = _clamp((.19 + (rebounder.finishing + rebounder.anticipation - keeper.goalkeeping - 70) / 620.0) * self.profile.goal_conversion_multiplier, .07, .42)
                    if rng.random() < rebound_goal:
                        attack.goals += 1
                        events.append(MatchEvent9394(minute, "goal", attack.sheet.team_id, rebounder.id, rebounder.name, "Gol tras aprovechar un rechace"))
                    else:
                        events.append(MatchEvent9394(minute, "save", defend.sheet.team_id, keeper.id, keeper.name, "Segunda parada tras el rechace"))
                else:
                    events.append(MatchEvent9394(minute, "shot_off", attack.sheet.team_id, rebounder.id, rebounder.name, "Remate del rechace fuera"))

    def _pick_creator(self, side: _SideState, rng: Random) -> Footballer9394:
        players = side.available_players()
        weights = []
        for p in players:
            slot = p.squad_slot or p.position.upper()
            role = 1.55 if slot in {"CM", "AM", "RM", "LM", "RW", "LW"} else 1.0 if slot in {"DM", "ST"} else .55
            trait = 1.23 if p.killer_pass else .92 if p.individualist else 1.0
            instruction = (side.sheet.individual_instructions or {}).get(str(p.id), {})
            freedom = {"disciplined": .90, "balanced": 1.0, "expressive": 1.13}.get(str(instruction.get("freedom") or "balanced"), 1.0)
            duty = {"hold": .88, "support": 1.0, "attack": 1.07}.get(str(instruction.get("duty") or "support"), 1.0)
            weights.append(max(.1, role * trait * freedom * duty * (p.vision * .50 + p.short_pass * .34 + p.technique * .16)))
        return rng.choices(players, weights=weights, k=1)[0]

    def _chance_type(self, side: _SideState, shooter: Footballer9394, creator: Footballer9394, rng: Random) -> tuple[str, str]:
        t = side.sheet.tactics
        if t.final_third == "crosses" and (shooter.heading >= 64 or creator.squad_slot in {"RM", "LM", "RW", "LW"}) and rng.random() < .58:
            return "cross", f"{creator.name} ejecuta el plan y busca el área con un centro"
        if t.final_third == "through" and (creator.killer_pass or creator.vision >= 70) and rng.random() < .58:
            return "through_ball", f"{creator.name} insiste en el pase entre líneas previsto"
        if shooter.long_shots and rng.random() < .34:
            return "long_shot", f"{shooter.name} encuentra espacio para probar desde media distancia"
        if shooter.individualist and shooter.dribbling >= 70 and rng.random() < .30:
            return "individual", f"{shooter.name} rompe la jugada con una acción individual"
        if t.width == "wide" and (shooter.heading >= 68 or creator.squad_slot in {"RM", "LM", "RW", "LW"}) and rng.random() < .44:
            return "cross", f"{creator.name} lleva el ataque por fuera y pone el balón al área"
        if creator.killer_pass or (creator.vision >= 78 and rng.random() < .46):
            return "through_ball", f"{creator.name} encuentra el último pase entre líneas"
        if t.directness == "direct":
            return "direct", f"{side.sheet.team_name} progresa con juego directo hacia {shooter.name}"
        if t.directness == "short":
            return "combination", f"{side.sheet.team_name} enlaza una combinación corta antes del remate"
        return "open_play", f"{side.sheet.team_name} convierte la posesión en una ocasión clara"

    def _resolve_penalty(self, attack: _SideState, defend: _SideState, minute: int, rng: Random, events: list[MatchEvent9394]) -> None:
        preferred = str((attack.sheet.set_piece_takers or {}).get("penalties") or "")
        taker = next((p for p in attack.available_players() if str(p.id) == preferred), None) or max(attack.available_players(), key=lambda p: p.penalties * .70 + p.finishing * .20 + p.consistency * .10)
        keeper = defend.goalkeeper()
        attack.shots += 1; attack.shots_on_target += 1
        events.append(MatchEvent9394(minute, "penalty", attack.sheet.team_id, taker.id, taker.name, "Penalti"))
        probability = _clamp(.70 + (taker.penalties - keeper.goalkeeping) / 520.0, .55, .88)
        if rng.random() < probability:
            attack.goals += 1
            events.append(MatchEvent9394(minute, "goal", attack.sheet.team_id, taker.id, taker.name, "Gol de penalti"))
        else:
            events.append(MatchEvent9394(minute, "penalty_saved", defend.sheet.team_id, keeper.id, keeper.name, "El portero detiene el penalti"))

    def _resolve_free_kick(self, attack: _SideState, defend: _SideState, minute: int, rng: Random, events: list[MatchEvent9394]) -> None:
        preferred = str((attack.sheet.set_piece_takers or {}).get("free_kicks") or "")
        taker = next((p for p in attack.available_players() if str(p.id) == preferred), None) or max(attack.available_players(), key=lambda p: p.free_kicks * .68 + p.shot_power * .18 + p.technique * .14)
        keeper = defend.goalkeeper()
        attack.shots += 1
        events.append(MatchEvent9394(minute, "free_kick_chance", attack.sheet.team_id, taker.id, taker.name, "Falta directa en zona de remate"))
        routine = {"low": -.008, "normal": 0.0, "high": .012}.get(attack.sheet.set_piece_usage, 0.0)
        on_target = _clamp(.25 + (taker.free_kicks - 55) / 180.0 + routine, .18, .62)
        if rng.random() >= on_target:
            events.append(MatchEvent9394(minute, "shot_off", attack.sheet.team_id, taker.id, taker.name, "La falta se marcha fuera")); return
        attack.shots_on_target += 1
        goal = _clamp(.075 + (taker.free_kicks + taker.shot_power - keeper.goalkeeping - 80) / 700.0, .035, .25)
        if rng.random() < goal:
            attack.goals += 1; events.append(MatchEvent9394(minute, "goal", attack.sheet.team_id, taker.id, taker.name, "Gol de falta directa"))
        else:
            events.append(MatchEvent9394(minute, "save", defend.sheet.team_id, keeper.id, keeper.name, "Parada en la falta"))

    def _resolve_corner(self, attack: _SideState, defend: _SideState, minute: int, rng: Random, events: list[MatchEvent9394]) -> None:
        preferred = str((attack.sheet.set_piece_takers or {}).get("corners") or "")
        taker = next((p for p in attack.available_players() if str(p.id) == preferred), None) or max(attack.available_players(), key=lambda p: p.free_kicks * .38 + p.long_pass * .38 + p.technique * .24)
        targets = [p for p in attack.available_players() if p.id != taker.id]
        if not targets: return
        target = max(targets, key=lambda p: p.heading * .48 + p.jumping * .30 + p.strength * .12 + p.positioning * .10)
        attack.shots += 1
        events.append(MatchEvent9394(minute, "set_piece_chance", attack.sheet.team_id, taker.id, taker.name, f"{taker.name} busca a {target.name} en el córner", target.id, target.name))
        defence = self._average(defend, ("heading", "jumping", "marking", "positioning"))
        aerial = target.heading * .42 + target.jumping * .28 + target.strength * .15 + target.positioning * .15
        routine = {"low": -.012, "normal": 0.0, "high": .018}.get(attack.sheet.set_piece_usage, 0.0)
        on_target = _clamp(.30 + (aerial - defence) / 260.0 + routine, .20, .58)
        if rng.random() >= on_target:
            events.append(MatchEvent9394(minute, "shot_off", attack.sheet.team_id, target.id, target.name, "Remate de cabeza fuera")); return
        attack.shots_on_target += 1
        keeper = defend.goalkeeper()
        goal = _clamp(.105 + (aerial - keeper.goalkeeping) / 600.0, .045, .25)
        if rng.random() < goal:
            attack.goals += 1
            events.append(MatchEvent9394(minute, "goal", attack.sheet.team_id, target.id, target.name, "Gol tras saque de esquina"))
            events.append(MatchEvent9394(minute, "assist", attack.sheet.team_id, taker.id, taker.name, f"Asistencia de {taker.name}", target.id, target.name))
        else:
            events.append(MatchEvent9394(minute, "save", defend.sheet.team_id, keeper.id, keeper.name, "Parada tras el córner"))

    def _pick_attacker(self, side: _SideState, rng: Random) -> Footballer9394:
        players = side.available_players()
        weights = []
        for p in players:
            pos = p.position.upper()
            slot = p.squad_slot or pos
            role_weight = 2.5 if slot == "ST" else 1.72 if slot in {"AM", "RW", "LW"} else 1.15 if slot in {"CM", "RM", "LM"} else 0.52
            movement = .62 + p.finishing / 170.0 + p.off_ball / 260.0
            if p.cuts_inside and slot in {"RW", "LW", "RM", "LM"}: movement *= 1.16
            if p.individualist: movement *= 1.10
            instruction = (side.sheet.individual_instructions or {}).get(str(p.id), {})
            movement *= {"hold": .78, "support": 1.0, "attack": 1.24}.get(str(instruction.get("duty") or "support"), 1.0)
            weights.append(max(0.1, role_weight * movement))
        return rng.choices(players, weights=weights, k=1)[0]

    def _pick_defender_for_foul(self, side: _SideState, rng: Random) -> Footballer9394:
        players = side.available_players()
        weights = []
        for p in players:
            pos = p.position.upper()
            role_weight = 1.8 if any(token in pos for token in ("CB", "DF", "DEF", "LAT")) else 1.35 if any(token in pos for token in ("DM", "MC", "M")) else 0.7
            weights.append(role_weight * (1.05 + p.aggression / 180.0) * (1.30 - p.discipline / 220.0))
        return rng.choices(players, weights=weights, k=1)[0]

    def _foul(self, defend: _SideState, minute: int, rng: Random, events: list[MatchEvent9394], *, referee: RefereeProfile9394 | None = None) -> None:
        player = self._pick_defender_for_foul(defend, rng)
        defend.fouls += 1
        events.append(MatchEvent9394(minute, "foul", defend.sheet.team_id, player.id, player.name, "Falta"))
        caution_chance = _clamp(0.10 + (60 - player.discipline) / 260.0, 0.06, 0.28)
        if referee is not None:
            caution_chance *= _clamp(float(referee.yellow_tendency) / 4.5, 0.62, 1.55)
            caution_chance = _clamp(caution_chance, 0.04, 0.38)
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
        else:
            direct_red_chance = 0.012
            if referee is not None:
                direct_red_chance *= _clamp(float(referee.red_tendency) / 0.45, 0.45, 1.85)
            if rng.random() >= direct_red_chance:
                return
            defend.reds += 1
            defend.sent_off.add(player.id)
            events.append(MatchEvent9394(minute, "red", defend.sheet.team_id, player.id, player.name, "Tarjeta roja"))

    def _accumulate_fatigue(self, side: _SideState, minute: int, *, venue: MatchVenue9394 | None = None) -> None:
        t = side.sheet.tactics
        tempo = {"slow": 0.80, "normal": 1.0, "high": 1.22}.get(t.tempo, 1.0)
        press = {"low": 0.82, "medium": 1.0, "high": 1.24}.get(t.pressing, 1.0)
        marking = 1.08 if t.marking == "man" else 1.0
        width = 1.04 if t.width == "wide" else .98 if t.width == "narrow" else 1.0
        transition = {"hold": .94, "balanced": 1.0, "counter": 1.08}.get(t.transition, 1.0)
        pitch_load = 1.0
        if venue and venue.width_m and venue.length_m:
            pitch_load = _clamp((int(venue.width_m) * int(venue.length_m)) / (68 * 105), .94, 1.07)
        for player in side.available_players():
            stamina_factor = 1.24 - player.stamina / 190.0
            work_factor = 1.04 + max(0, player.work_rate - 70) / 650.0
            individual_press = {"low": .92, "normal": 1.0, "high": 1.10}.get(str((side.sheet.individual_instructions or {}).get(str(player.id), {}).get("pressing") or "normal"), 1.0)
            side.fatigue[player.id] = min(100.0, side.fatigue.get(player.id, 0.0) + 0.43 * tempo * press * marking * width * transition * individual_press * pitch_load * stamina_factor * work_factor)

    def _maybe_substitute(self, side: _SideState, minute: int, rng: Random, events: list[MatchEvent9394]) -> None:
        if side.substitutions >= self.laws.max_used_substitutes or not side.bench:
            return
        candidates = [p for p in side.available_players() if p.position.upper() not in {"GK", "POR", "PORTERO"}]
        if not candidates:
            return
        tired = max(candidates, key=lambda p: side.fatigue.get(p.id, 0.0) - p.overall / 10.0)
        fatigue = side.fatigue.get(tired.id, 0.0)
        threshold = 25 if minute <= 60 else 31 if minute <= 72 else 35
        threshold += {"high": -5, "normal": 0, "low": 5}.get(side.sheet.rotation_frequency, 0)
        if fatigue < threshold and rng.random() > 0.16:
            return
        replacement = max(side.bench, key=lambda p: self._replacement_fit(p, tired))
        idx = side.on_pitch.index(tired)
        side.on_pitch[idx] = replacement
        side.bench.remove(replacement)
        side.substitutions += 1
        events.append(MatchEvent9394(minute, "substitution", side.sheet.team_id, replacement.id, replacement.name, f"Entra {replacement.name}; sale {tired.name}", tired.id, tired.name))

    def _replacement_fit(self, replacement: Footballer9394, outgoing: Footballer9394) -> float:
        same_position = replacement.position.upper() == outgoing.position.upper()
        return replacement.overall + (12 if same_position else 0)

    def _maybe_injury(self, side: _SideState, minute: int, rng: Random, events: list[MatchEvent9394]) -> None:
        players = side.available_players()
        if not players:
            return
        proneness = sum(int(p.injury_proneness) for p in players) / len(players)
        fatigue = sum(float(side.fatigue.get(p.id, 0.0)) for p in players) / len(players)
        chance = 0.00105 * (1.0 + proneness * .24) * (1.0 + max(0.0, fatigue - 35.0) / 180.0)
        if rng.random() > chance:
            return
        weights = [1.0 + int(p.injury_proneness) * .55 + float(side.fatigue.get(p.id, 0.0)) / 150.0 for p in players]
        player = rng.choices(players, weights=weights, k=1)[0]
        events.append(MatchEvent9394(minute, "injury", side.sheet.team_id, player.id, player.name, "Problemas físicos"))
        # An injury does not always force the player off; when it does, the
        # historical two-substitute cap still applies.
        if side.substitutions < self.laws.max_used_substitutes and side.bench and rng.random() < 0.58:
            replacement = max(side.bench, key=lambda p: self._replacement_fit(p, player))
            idx = side.on_pitch.index(player)
            side.on_pitch[idx] = replacement
            side.bench.remove(replacement)
            side.substitutions += 1
            events.append(MatchEvent9394(minute, "injury_substitution", side.sheet.team_id, replacement.id, replacement.name, f"Entra {replacement.name}; sale lesionado {player.name}", player.id, player.name))
