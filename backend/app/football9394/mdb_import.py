from __future__ import annotations

"""Row-level importer for the historical 1993-94 slice of the supplied MDB.

The source database contains multiple editing eras.  We therefore never infer
"historical" from row order or from a modern competition date accidentally left
in a record.  League rows are activated only when their explicit edition marker
is 1993; knockout tournaments are activated when their declared competition
window overlaps the 1993-07-01 .. 1994-06-30 season.

The importer is read-only and keeps source ids so every normalized record can be
traced back to the MDB during later rule/data audits.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .mdb_jet4 import Jet4MDB

SEASON_START = datetime(1993, 7, 1)
SEASON_END = datetime(1994, 6, 30, 23, 59, 59)

# The MDB has no physical country table in its catalog; these ids are the
# countries needed by the explicit 1993 league slice.  Keep the mapping small
# and auditable rather than guessing all ids from later-edition records.
HISTORICAL_COUNTRY_NAMES: dict[int, str] = {
    1: "Francia",
    2: "Uruguay",
    3: "Países Bajos",
    4: "Alemania",
    5: "Italia",
    6: "Inglaterra",
    10: "Portugal",
    11: "España",
    26: "Colombia",
    38: "Estados Unidos",
    43: "Escocia",
    50: "Japón",
    62: "Brasil",
    63: "Argentina",
    64: "México",
}


@dataclass(frozen=True, slots=True)
class HistoricalLeagueRow9394:
    source_id: int
    country_id: int
    country: str
    name: str
    short_name: str
    level: int
    team_count: int
    turns: int
    yellow_card_cycle: int | None
    max_foreigners_starting: int | None
    max_foreigners_squad: int | None
    prefer_nationals: bool
    source_start: datetime | None
    source_end: datetime | None
    source_edition: str
    admitted: bool
    signable: bool
    source_rule_hints: dict[str, Any]


@dataclass(frozen=True, slots=True)
class HistoricalTournamentRow9394:
    source_id: int
    name: str
    short_name: str
    country_id: int | None
    continent_id: int | None
    tournament_type: int | None
    two_legged: bool
    two_legged_qualifying: bool
    two_legged_final: bool
    away_goals: bool
    start: datetime
    end: datetime
    entrants: int | None
    round1_teams: int | None
    round2_teams: int | None
    round3_teams: int | None
    playoff_teams: int | None
    final_stage_teams: int | None
    knockout_teams: int | None
    group1_count: int | None
    group1_qualifiers: int | None
    max_foreigners_starting: int | None
    max_foreigners_squad: int | None
    admitted: bool
    source_rule_hints: dict[str, Any]


@dataclass(frozen=True, slots=True)
class HistoricalTeamRow9394:
    source_id: int
    name: str
    long_name: str
    short_name: str
    initials: str | None
    league_id: int | None
    league_position: int | None
    stadium_id: int | None
    manager_id: int | None
    members: int | None
    budget: int | None
    debt: int | None
    reserve_of: int | None
    reserve_step: int | None
    academy_level: int | None
    squad_building_style: int | None
    sporting_director_level: int | None
    women_flag: bool
    activation_reason: str
    familiar_name: str | None
    very_short_name: str | None
    president: str | None
    secondary_stadium_id: int | None
    training_ground: str | None
    youth_residence: str | None
    main_rival_id: int | None
    regional_rival_id: int | None
    honours: dict[str, int | None]
    academy_style: int | None
    special_academy_pattern_id: int | None
    initial_points_sanction: int | None
    fifa_registration_ban_until: datetime | None


@dataclass(frozen=True, slots=True)
class HistoricalPlayerRow9394:
    source_id: int
    team_id: int
    display_name: str
    first_name: str | None
    surname1: str | None
    surname2: str | None
    birth_date: datetime | None
    birth_country_id: int | None
    international_country_id: int | None
    preferred_foot: int | None
    shirt_number: int | None
    primary_role: int | None
    broad_position: str | None
    overall: int | None
    category: int | None
    height_cm: float | None
    weight_kg: float | None
    salary: int | None
    release_clause: int | None
    contract_start_year: int | None
    contract_end_year: int | None
    loan: bool
    initially_reserve: bool
    retired: bool
    attributes: dict[str, int | float | None]
    birth_city_id: int | None
    naturalized_country_id: int | None
    basque_origin: bool
    favorite_shirt_number: int | None
    injury_proneness: int | None
    progression_mean: int | None
    fan_affection: int | None
    academy_team_id: int | None
    previous_team_id: int | None
    previous_team_years: int | None
    buyback_option: int | None
    role_ratings: dict[str, int]
    hidden_traits: dict[str, bool]


@dataclass(frozen=True, slots=True)
class HistoricalSnapshot9394:
    leagues: tuple[HistoricalLeagueRow9394, ...]
    tournaments: tuple[HistoricalTournamentRow9394, ...]
    teams: tuple[HistoricalTeamRow9394, ...]
    players: tuple[HistoricalPlayerRow9394, ...]
    tournament_participants: dict[int, tuple[int, ...]]
    league_calendar_rows: tuple[dict[str, int], ...]
    source_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "season": "1993-94",
            "leagues": [asdict(row) for row in self.leagues],
            "tournaments": [asdict(row) for row in self.tournaments],
            "teams": [asdict(row) for row in self.teams],
            "players": [asdict(row) for row in self.players],
            "tournament_participants": {
                str(k): list(v) for k, v in sorted(self.tournament_participants.items())
            },
            "league_calendar_rows": list(self.league_calendar_rows),
            "source_counts": dict(self.source_counts),
        }


def _as_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return int(value) if isinstance(value, bool) else None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dt(value: Any) -> datetime | None:
    return value if isinstance(value, datetime) else None


def _clean_name(*parts: Any) -> str:
    return " ".join(str(part).strip() for part in parts if part and str(part).strip())


def _overlaps_season(start: Any, end: Any) -> bool:
    start_dt, end_dt = _dt(start), _dt(end)
    return bool(start_dt and end_dt and start_dt <= SEASON_END and end_dt >= SEASON_START)


def _active_league(row: dict[str, Any]) -> bool:
    marker = str(row.get("EdicionTemporada") or "").strip()
    return marker == "1993"


def _active_tournament(row: dict[str, Any]) -> bool:
    return bool(row.get("Admitido")) and _overlaps_season(
        row.get("InicioCompeticion"), row.get("FinCompeticion")
    )


# Historical source repairs: clubs that belong to an admitted 1993 competition
# but were moved to a later league row inside the mixed-era MDB.  They remain
# source-backed clubs; this only widens the snapshot selection and never mutates
# the original Access database.
HISTORICAL_EXTRA_TEAM_IDS_9394 = {1825}  # Fortaleza EC, participant in Brazil Série A 1993


def _unique_ids(values: Iterable[Any]) -> tuple[int, ...]:
    return tuple(sorted({int(value) for value in values if isinstance(value, int) and value > 0}))


def load_historical_snapshot(path: str | Path) -> HistoricalSnapshot9394:
    db = Jet4MDB(path)
    raw_leagues = db.rows("Liga")
    raw_tournaments = db.rows("Torneo")
    raw_teams = db.rows("Equipo")
    raw_players = db.rows("Jugador")
    raw_calendar_league = db.rows("CalendarioLiga")
    raw_calendar_tournament = db.rows("CalendarioTorneo")
    raw_calendar_tournament_no_cwc = db.rows("CalendarioTorneoSinRecopa")
    raw_calendar_tournament_final = db.rows("CalendarioTorneoFinal")

    league_rows = [row for row in raw_leagues if _active_league(row)]
    tournament_rows = [row for row in raw_tournaments if _active_tournament(row)]
    league_ids = {int(row["Id"]) for row in league_rows if isinstance(row.get("Id"), int)}
    tournament_ids = {int(row["Id"]) for row in tournament_rows if isinstance(row.get("Id"), int)}

    participant_ids: dict[int, set[int]] = {tid: set() for tid in tournament_ids}
    for source in (raw_calendar_tournament, raw_calendar_tournament_no_cwc):
        for row in source:
            tid, team_id = row.get("Torneo"), row.get("Equipo")
            if tid in participant_ids and isinstance(team_id, int) and team_id > 0:
                participant_ids[tid].add(team_id)

    domestic_team_ids = {
        int(row["Id"]) for row in raw_teams
        if isinstance(row.get("Id"), int) and row.get("Liga") in league_ids
    }
    continental_team_ids = set().union(*participant_ids.values()) if participant_ids else set()
    active_team_ids = domestic_team_ids | continental_team_ids | HISTORICAL_EXTRA_TEAM_IDS_9394

    normalized_leagues = tuple(
        HistoricalLeagueRow9394(
            source_id=int(row["Id"]),
            country_id=int(row["IdPais"]),
            country=HISTORICAL_COUNTRY_NAMES.get(int(row["IdPais"]), f"País {row['IdPais']}"),
            name=str(row.get("Nombre") or "Liga"),
            short_name=str(row.get("NombreCorto") or row.get("Nombre") or "Liga"),
            level=_as_int(row.get("Nivel")) or 1,
            team_count=_as_int(row.get("NumeroEquipos")) or 0,
            turns=_as_int(row.get("NumVueltas")) or 0,
            yellow_card_cycle=_as_int(row.get("CicloAmarillas")),
            max_foreigners_starting=_as_int(row.get("Ex11")),
            max_foreigners_squad=_as_int(row.get("ExPlantilla")),
            prefer_nationals=bool(row.get("PrefFichNacionales")),
            source_start=_dt(row.get("InicioCompeticion")),
            source_end=_dt(row.get("FinCompeticion")),
            source_edition=str(row.get("EdicionTemporada") or ""),
            admitted=bool(row.get("ADMITIDA")),
            signable=bool(row.get("FICHABLE")),
            source_rule_hints={
                "P1": _as_int(row.get("P1")), "P2": _as_int(row.get("P2")),
                "P3": _as_int(row.get("P3")), "P4": _as_int(row.get("P4")),
                "P5": _as_int(row.get("P5")), "P6": _as_int(row.get("P6")),
                "PY": _as_int(row.get("PY")), "PZ": _as_int(row.get("PZ")),
                "positions": [_as_int(row.get(f"Pos{i}")) for i in range(1, 14)],
                "CC": _as_int(row.get("CC")),
                "days": {day: _as_int(row.get(source)) for day, source in {
                    "monday": "Lunes", "tuesday": "Martes", "wednesday": "Miercoles",
                    "thursday": "Jueves", "friday": "Viernes", "saturday": "Sabado",
                    "sunday": "Domingo",
                }.items()},
                "winter_break": bool(row.get("Paron_navidad")),
                "old_glories": bool(row.get("ViejasGlorias")),
                "var": bool(row.get("VAR")),
            },
        )
        for row in sorted(league_rows, key=lambda r: (int(r.get("IdPais") or 0), int(r.get("Nivel") or 0), int(r.get("Id") or 0)))
    )

    final_venue_hints: dict[int, list[dict[str, Any]]] = {}
    for row in raw_calendar_tournament_final:
        tournament_id = _as_int(row.get("Torneo"))
        if tournament_id not in tournament_ids:
            continue
        final_venue_hints.setdefault(tournament_id, []).append({
            "stadium_id": _as_int(row.get("Estadio")),
            "fixed": bool(row.get("Fijo")),
            "all_matches": bool(row.get("Todo")),
        })

    normalized_tournaments = tuple(
        HistoricalTournamentRow9394(
            source_id=int(row["Id"]),
            name=str(row.get("Nombre") or "Torneo"),
            short_name=str(row.get("Nombre_corto") or row.get("Nombre") or "Torneo"),
            country_id=_as_int(row.get("Pais")),
            continent_id=_as_int(row.get("Continente")),
            tournament_type=_as_int(row.get("Tipo")),
            two_legged=bool(row.get("Ida_y_vuelta")),
            two_legged_qualifying=bool(row.get("Ida_y_vuelta_clas")),
            two_legged_final=bool(row.get("Ida_y_vuelta_final")),
            away_goals=bool(row.get("ValorDobleGolesFueraDeCasa")),
            start=_dt(row.get("InicioCompeticion")) or SEASON_START,
            end=_dt(row.get("FinCompeticion")) or SEASON_END,
            entrants=_as_int(row.get("Inscritos")),
            round1_teams=_as_int(row.get("Num_equipos_ronda1")),
            round2_teams=_as_int(row.get("Num_equipos_ronda2")),
            round3_teams=_as_int(row.get("Num_equipos_ronda3")),
            playoff_teams=_as_int(row.get("Num_equipos_playoffs")),
            final_stage_teams=_as_int(row.get("Num_equipos_fase_final")),
            knockout_teams=_as_int(row.get("Num_equipos_eliminatorias")),
            group1_count=_as_int(row.get("Num_grupos_fase1")),
            group1_qualifiers=_as_int(row.get("Fase_grupos1_clasifican")),
            max_foreigners_starting=_as_int(row.get("Ex11")),
            max_foreigners_squad=_as_int(row.get("ExPlantilla")),
            admitted=bool(row.get("Admitido")),
            source_rule_hints={
                "friendly": bool(row.get("Amistoso")),
                "promotion_type": _as_int(row.get("TipoAscenso")),
                "supercup": bool(row.get("Supercopa")),
                "level": _as_int(row.get("Nivel")),
                "group2_count": _as_int(row.get("Num_grupos_fase2")),
                "group2_qualifiers": _as_int(row.get("Fase_grupos2_clasifican")),
                "group1_to_minor_competition_position": _as_int(row.get("Pos_fase1_a_comp_menor")),
                "repeat_group_champions": bool(row.get("duplicar_campeones_de_grupo")),
                "guests": _as_int(row.get("Invitados")),
                "invited_confederation": _as_int(row.get("ConfederacionInvitada")),
                "every_n_years": _as_int(row.get("Cada_x_años")),
                "third_place_final": bool(row.get("Final_consolacion")),
                "maximum_audience": _as_int(row.get("Maxima_audiencia")),
                "winter_break": bool(row.get("Paron_navidad")),
                "previous_champion_id": _as_int(row.get("CampeonAnterior")),
                "previous_runner_up_id": _as_int(row.get("SubcampeonAnterior")),
                "champion_to_final_stage": bool(row.get("Campeon_a_fase_final")),
                "minor_champion_to_final_stage": bool(row.get("Campeon_torneo_menor_a_fase_final")),
                "host_friendly_id": _as_int(row.get("AnfitrionAmistoso")),
                "final_venue_hints": list(final_venue_hints.get(int(row["Id"]), ())),
                "days": {day: _as_int(row.get(source)) for day, source in {
                    "monday": "Lunes", "tuesday": "Martes", "wednesday": "Miercoles",
                    "thursday": "Jueves", "friday": "Viernes", "saturday": "Sabado",
                    "sunday": "Domingo",
                }.items()},
            },
        )
        for row in sorted(tournament_rows, key=lambda r: int(r.get("Id") or 0))
    )

    normalized_teams: list[HistoricalTeamRow9394] = []
    for row in raw_teams:
        team_id = row.get("Id")
        if not isinstance(team_id, int) or team_id not in active_team_ids:
            continue
        reason = ("domestic_league" if team_id in domestic_team_ids else
                  "continental_participant" if team_id in continental_team_ids else
                  "historical_source_repair")
        normalized_teams.append(HistoricalTeamRow9394(
            source_id=team_id,
            name=str(row.get("Nombre") or row.get("NombreCorto") or f"Equipo {team_id}"),
            long_name=str(row.get("NombreLargo") or row.get("Nombre") or f"Equipo {team_id}"),
            short_name=str(row.get("NombreCorto") or row.get("Nombre") or f"Equipo {team_id}"),
            initials=str(row.get("Siglas")) if row.get("Siglas") else None,
            league_id=_as_int(row.get("Liga")),
            league_position=_as_int(row.get("Posicion")),
            stadium_id=_as_int(row.get("Estadio")),
            manager_id=_as_int(row.get("Entrenador")),
            members=_as_int(row.get("Socios")),
            budget=_as_int(row.get("Presupuesto")),
            debt=_as_int(row.get("Deuda")),
            reserve_of=_as_int(row.get("Filial_de")),
            reserve_step=_as_int(row.get("Peldanyo_filial")),
            academy_level=_as_int(row.get("Nivel_cantera")),
            squad_building_style=_as_int(row.get("Confeccion_plantilla")),
            sporting_director_level=_as_int(row.get("Secretario_tecnico_estrella")),
            women_flag=bool(row.get("Femenino")),
            activation_reason=reason,
            familiar_name=str(row.get("NombreFamiliar")) if row.get("NombreFamiliar") else None,
            very_short_name=str(row.get("NombreMuyCorto")) if row.get("NombreMuyCorto") else None,
            president=str(row.get("Presidente")) if row.get("Presidente") else None,
            secondary_stadium_id=_as_int(row.get("EstadioSecundario")),
            training_ground=str(row.get("CiudadDeportiva")) if row.get("CiudadDeportiva") else None,
            youth_residence=str(row.get("ResidenciaJuveniles")) if row.get("ResidenciaJuveniles") else None,
            main_rival_id=_as_int(row.get("MaximoRival")),
            regional_rival_id=_as_int(row.get("MaximoRivalRegional")),
            honours={
                "intercontinental": _as_int(row.get("PalmaresIntercontinentales")),
                "continental": _as_int(row.get("PalmaresContinentales")),
                "continental_2": _as_int(row.get("PalmaresContinentales2")),
                "continental_3": _as_int(row.get("PalmaresContinentales3")),
                "continental_4": _as_int(row.get("PalmaresContinentales4")),
                "continental_supercups": _as_int(row.get("PalmaresSuperCopasContinentales")),
                "national_leagues": _as_int(row.get("PalmaresLigasNacionales")),
                "national_cups": _as_int(row.get("PalmaresCopasNacionales")),
                "national_cups_2": _as_int(row.get("PalmaresCopasNacionales2")),
                "national_supercups": _as_int(row.get("PalmaresSuperCopasNacionales")),
            },
            academy_style=_as_int(row.get("Estilo_cantera")),
            special_academy_pattern_id=_as_int(row.get("Canterano_especial")),
            initial_points_sanction=_as_int(row.get("SancionPuntosInicialesLiga")),
            fifa_registration_ban_until=_dt(row.get("SancionFIFAFichajesNoJueganHasta")),
        ))

    player_attribute_map = {
        "pace": "Velocidad", "acceleration": "Aceleracion", "jumping": "Salto",
        "stamina": "Resistencia", "strength": "PotenciaFisica", "tackling": "Entradas",
        "work_rate": "Lucha", "aggression": "Agresividad", "anticipation": "Anticipacion",
        "marking": "Marcaje", "discipline": "Disciplina", "positioning": "Colocacion",
        "leadership": "Liderazgo", "consistency": "Regularidad", "vision": "VisionJuego",
        "short_pass": "PaseCorto", "long_pass": "PaseLargo", "dribbling": "Regate",
        "finishing": "Finalizacion", "heading": "RemCabeza", "off_ball": "Desmarque",
        "shot_power": "PotTiro", "free_kicks": "Faltas", "penalties": "Penaltis",
        "technique": "Calidad",
    }
    normalized_players: list[HistoricalPlayerRow9394] = []
    for row in raw_players:
        team_id = row.get("CodEquipo")
        player_id = row.get("Id")
        if not isinstance(player_id, int) or not isinstance(team_id, int) or team_id not in active_team_ids:
            continue
        attributes = {key: _as_int(row.get(source)) for key, source in player_attribute_map.items()}
        normalized_players.append(HistoricalPlayerRow9394(
            source_id=player_id,
            team_id=team_id,
            display_name=str(row.get("Apodo") or _clean_name(row.get("Nombre"), row.get("Apellido1"), row.get("Apellido2")) or f"Jugador {player_id}"),
            first_name=str(row.get("Nombre")) if row.get("Nombre") else None,
            surname1=str(row.get("Apellido1")) if row.get("Apellido1") else None,
            surname2=str(row.get("Apellido2")) if row.get("Apellido2") else None,
            birth_date=_dt(row.get("FechaNacimiento")),
            birth_country_id=_as_int(row.get("PaisNacimiento")),
            international_country_id=_as_int(row.get("PaisInternacional")),
            preferred_foot=_as_int(row.get("Pierna")),
            shirt_number=_as_int(row.get("Dorsal")),
            primary_role=_as_int(row.get("RolPrincipal")),
            broad_position=str(row.get("DEM")) if row.get("DEM") else None,
            overall=(_as_int(row.get("Media_forzada")) if (_as_int(row.get("Media_forzada")) or 0) > 0 else _as_int(row.get("Categoria"))),
            category=_as_int(row.get("Categoria")),
            height_cm=_as_float(row.get("Altura")),
            weight_kg=_as_float(row.get("Peso")),
            salary=_as_int(row.get("Sueldo")),
            release_clause=_as_int(row.get("ClausulaRescision")),
            contract_start_year=_as_int(row.get("AnyoInicioContrato")),
            contract_end_year=_as_int(row.get("AnyoFinContrato")),
            loan=bool(row.get("ContratoCesion")),
            initially_reserve=bool(row.get("InicialmenteEnFilial")),
            retired=bool(row.get("Retirado")),
            attributes=attributes,
            birth_city_id=_as_int(row.get("CiudadNacimiento")),
            naturalized_country_id=_as_int(row.get("PaisNacionalizado")),
            basque_origin=bool(row.get("OrigenVasco")),
            favorite_shirt_number=_as_int(row.get("DorsalFavorito")),
            injury_proneness=_as_int(row.get("Lesiones")),
            progression_mean=_as_int(row.get("ProgresionMedia")),
            fan_affection=_as_int(row.get("AfectoActualAficion")),
            academy_team_id=_as_int(row.get("CanteranoDe")),
            previous_team_id=_as_int(row.get("EquipoAnterior")),
            previous_team_years=_as_int(row.get("AñosEquipoAnterior")),
            buyback_option=_as_int(row.get("OpcionRecompra")),
            role_ratings={str(role_id): (_as_int(row.get(f"Rol{role_id + 1}")) or 0) for role_id in range(18)},
            hidden_traits={
                "individualist": bool(row.get("Oculto_individualista")),
                "killer_pass": bool(row.get("Oculto_ultimo_pase")),
                "holds_ball": bool(row.get("Oculto_conservar_balon")),
                "long_shots": bool(row.get("Oculto_tiro_media_distancia")),
                "cuts_inside": bool(row.get("Oculto_tiende_al_centro")),
                "first_time_play": bool(row.get("Oculto_primer_toque")),
                "dives": bool(row.get("Oculto_piscinero")),
            },
        ))

    league_calendar_rows = tuple(
        {
            "id": int(row["Id"]), "league_id": int(row["Liga"]),
            "matchday": int(row["Jornada"]), "home_team_id": int(row["Local"]),
            "away_team_id": int(row["Visitante"]),
        }
        for row in raw_calendar_league
        if row.get("Liga") in league_ids and all(isinstance(row.get(k), int) for k in ("Id", "Liga", "Jornada", "Local", "Visitante"))
    )

    return HistoricalSnapshot9394(
        leagues=normalized_leagues,
        tournaments=normalized_tournaments,
        teams=tuple(sorted(normalized_teams, key=lambda row: row.source_id)),
        players=tuple(sorted(normalized_players, key=lambda row: row.source_id)),
        tournament_participants={tid: _unique_ids(ids) for tid, ids in participant_ids.items()},
        league_calendar_rows=league_calendar_rows,
        source_counts={
            "all_leagues": len(raw_leagues),
            "historical_leagues": len(normalized_leagues),
            "admitted_historical_leagues": sum(row.admitted for row in normalized_leagues),
            "non_admitted_historical_leagues": sum(not row.admitted for row in normalized_leagues),
            "all_tournaments": len(raw_tournaments),
            "historical_tournaments": len(normalized_tournaments),
            "all_teams": len(raw_teams),
            "historical_teams": len(normalized_teams),
            "domestic_teams": len(domestic_team_ids),
            "continental_only_teams": len(active_team_ids - domestic_team_ids),
            "all_players": len(raw_players),
            "historical_players": len(normalized_players),
            "league_calendar_rows": len(league_calendar_rows),
        },
    )
