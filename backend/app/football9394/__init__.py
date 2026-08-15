"""Historical football domain for Míster 93/94.

Rules, competition formats, persistent career state and match semantics live
in this package so the football simulation has one explicit source of truth.
"""

from .laws import LAWS_1993_94
from .format_spec import CompetitionFormatSpec9394, CompetitionStageRules9394
from .match_engine import (
    ERA_BASELINE_1993_94,
    SPAIN_PRIMERA_SIMULATION_1993_94,
    FootballMatchEngine9394,
    FootballTactics9394,
    Footballer9394,
    SimulationProfile9394,
    TeamSheet9394,
)
from .pyramid import compute_relegations, select_eligible_promotions
from .registry import HistoricalCompetitionRegistry9394, UnresolvedHistoricalRulesError, default_registry_9394
from .standings import LeagueMatch9394, StandingRow9394, build_league_table
from .schedule import LeagueFixture9394, generate_double_round_robin, generate_round_robin_cycles, validate_league_fixtures
from .league_engine import LeagueSeason9394
from .knockout import KnockoutLeg9394, KnockoutResolution9394, KnockoutRoundRules9394, resolve_knockout_tie
from .readiness import CompetitionReadiness9394, UniverseReadiness9394, audit_competition_readiness
from .rules import CompetitionRules9394, SPAIN_PRIMERA_1993_94, SPAIN_SEGUNDA_1993_94, SCOTLAND_PREMIER_1993_94, FRANCE_DIVISION_1_1993_94, PORTUGAL_PRIMEIRA_1993_94, ITALY_SERIE_A_1993_94, ITALY_SERIE_B_1993_94, MEXICO_PRIMERA_1993_94, COLOMBIA_PRIMERA_A_1993, NETHERLANDS_EREDIVISIE_1993_94, NETHERLANDS_EERSTE_1993_94, NETHERLANDS_NACOMPETITIE_GROUP_1993_94, SPAIN_SEGUNDA_B_1993_94, SPAIN_SEGUNDA_B_PROMOTION_GROUP_1993_94, SPAIN_SEGUNDA_B_G1_1993_94, SPAIN_SEGUNDA_B_G2_1993_94, SPAIN_SEGUNDA_B_G3_1993_94, SPAIN_SEGUNDA_B_G4_1993_94

__all__ = [
    "LAWS_1993_94",
    "CompetitionFormatSpec9394",
    "CompetitionStageRules9394",
    "CompetitionRules9394",
    "SimulationProfile9394",
    "ERA_BASELINE_1993_94",
    "SPAIN_PRIMERA_SIMULATION_1993_94",
    "FootballMatchEngine9394",
    "FootballTactics9394",
    "Footballer9394",
    "TeamSheet9394",
    "SPAIN_PRIMERA_1993_94",
    "SPAIN_SEGUNDA_1993_94",
    "SCOTLAND_PREMIER_1993_94",
    "ITALY_SERIE_B_1993_94",
    "ITALY_SERIE_A_1993_94",
    "MEXICO_PRIMERA_1993_94",
    "COLOMBIA_PRIMERA_A_1993",
    "PORTUGAL_PRIMEIRA_1993_94",
    "FRANCE_DIVISION_1_1993_94",
    "NETHERLANDS_EREDIVISIE_1993_94",
    "NETHERLANDS_EERSTE_1993_94",
    "NETHERLANDS_NACOMPETITIE_GROUP_1993_94",
    "SPAIN_SEGUNDA_B_G1_1993_94",
    "SPAIN_SEGUNDA_B_G2_1993_94",
    "SPAIN_SEGUNDA_B_G3_1993_94",
    "SPAIN_SEGUNDA_B_G4_1993_94",
    "SPAIN_SEGUNDA_B_1993_94",
    "SPAIN_SEGUNDA_B_PROMOTION_GROUP_1993_94",
    "HistoricalCompetitionRegistry9394",
    "UnresolvedHistoricalRulesError",
    "LeagueMatch9394",
    "LeagueFixture9394",
    "LeagueSeason9394",
    "StandingRow9394",
    "build_league_table",
    "generate_double_round_robin",
    "generate_round_robin_cycles",
    "validate_league_fixtures",
    "default_registry_9394",
    "compute_relegations",
    "select_eligible_promotions",
    "KnockoutLeg9394",
    "KnockoutResolution9394",
    "KnockoutRoundRules9394",
    "resolve_knockout_tie",
    "CompetitionReadiness9394",
    "UniverseReadiness9394",
    "audit_competition_readiness",
]
