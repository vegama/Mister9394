from __future__ import annotations

"""Runtime index for the normalized 1993-94 historical snapshot.

The Access database is an import source, not a runtime dependency.  This module
loads the normalized JSON produced by the historical import pipeline and
indexes it by the original MDB ids.  Keeping those ids in the API makes every
club/player/competition traceable back to the source database.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from functools import lru_cache
import json
try:
    import orjson
except ImportError:  # pragma: no cover - compatibility fallback
    orjson = None
from pathlib import Path
from typing import Any

from .mdb_import import HISTORICAL_COUNTRY_NAMES
from .player_identity import age_on as player_age_on
from .position_roles import ROLES_9394, role_api

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SNAPSHOT_PATH = REPO_ROOT / "data" / "football9394" / "historical_snapshot.json"
DEFAULT_GAME_DATE = date(1993, 10, 23)

# These names only affect presentation. Unknown ids remain visible rather than
# being guessed so data-quality work can resolve them later.
PRESENTATION_COUNTRIES = {
    **HISTORICAL_COUNTRY_NAMES,
    13: "Arabia Saudí",
    14: "Argelia",
    15: "Australia",
    16: "Austria",
    17: "Bélgica",
    19: "Bolivia",
    21: "Bulgaria",
    20: "Bosnia y Herzegovina",
    22: "Canadá",
    23: "Chile",
    28: "Corea del Sur",
    31: "Croacia",
    33: "Dinamarca",
    36: "Eslovaquia",
    40: "Rusia",
    41: "Finlandia",
    42: "Ghana",
    44: "Irlanda del Norte",
    45: "Gales",
    46: "Irlanda",
    47: "Grecia",
    56: "Marruecos",
    59: "Nigeria",
    60: "Noruega",
    61: "República Checa",
    62: "Brasil",
    66: "Camerún",
    68: "Paraguay",
    70: "Polonia",
    72: "Rumanía",
    75: "Yugoslavia",
    79: "Suecia",
    80: "Suiza",
    84: "Turquía",
    85: "Ucrania",
    87: "Mozambique",
    93: "Hungría",
    117: "Cabo Verde",
    120: "Guinea Ecuatorial",
    # Selecciones que sólo pasaron a ser jugables al incorporar las
    # convocatorias reales de la Copa África, la Copa América y la Copa Asia:
    # antes no llegaban a once futbolistas y por eso no se catalogaban.
    # Los nombres son los de 1993, que es cuando transcurre la partida: el 88
    # es Zaire, no la República Democrática del Congo, que no existe hasta 1997.
    12: "Angola",
    24: "China",
    29: "Costa de Marfil",
    34: "Ecuador",
    35: "Egipto",
    48: "Irán",
    69: "Perú",
    74: "Senegal",
    77: "Sierra Leona",
    78: "Sudáfrica",
    83: "Túnez",
    86: "Venezuela",
    88: "Zaire",
    103: "Gabón",
    112: "Zambia",
    124: "Kenia",
    169: "Liberia",
    203: "Tailandia",
    # Países que ya venían nombrados en el catálogo fuente pero no aquí, así que
    # sus futbolistas enseñaban un número en vez de una nacionalidad. Son pocos
    # jugadores cada uno y ninguno reúne plantilla para ser selección jugable
    # —de eso ya se encarga el filtro de ``national_team_catalog``—, pero la
    # ficha tiene que decir de dónde es la gente.
    8: "Albania",
    18: "Bielorrusia",
    25: "Chipre",
    30: "Costa Rica",
    37: "Eslovenia",
    39: "Estonia",
    49: "Israel",
    54: "Macedonia",
    65: "Islandia",
    67: "Malí",
    76: "Montenegro",
    81: "Togo",
    92: "Guatemala",
    104: "Georgia",
    106: "Honduras",
    107: "Jamaica",
    110: "Nueva Zelanda",
    115: "Benín",
    119: "Guadalupe",
    121: "Guinea-Bissau",
    125: "Madagascar",
    126: "Panamá",
    130: "Azerbaiyán",
    131: "Islas Feroe",
    147: "El Salvador",
    149: "Etiopía",
    150: "Fiyi",
    151: "Gambia",
    170: "Libia",
    173: "Malawi",
    185: "Papúa Nueva Guinea",
    194: "Santo Tomé y Príncipe",
    200: "Surinam",
    213: "República del Congo",
    218: "Palestina",
    219: "San Vicente",
}

FOOT_NAMES = {1: "Derecha", 2: "Izquierda", 3: "Ambas"}
BROAD_POSITION_NAMES = {
    "POR": "POR",
    "DEF": "DEF",
    "MED": "MED",
    "DEL": "DEL",
}


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError):
        return None


def age_on(value: Any, when: date = DEFAULT_GAME_DATE) -> int | None:
    born = _parse_date(value)
    if born is None:
        return None
    return when.year - born.year - ((when.month, when.day) < (born.month, born.day))


def _display_money(value: Any) -> str | None:
    if value in (None, 0, "0"):
        return None
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return None
    # The source stores peseta-era monetary values with heterogeneous scales;
    # expose the source number faithfully until the monetary importer is fully
    # calibrated instead of silently applying a modern conversion.
    return f"{amount:,} ptas.".replace(",", ".")


@dataclass(slots=True)
class FootballUniverseSnapshot9394:
    payload: dict[str, Any]
    leagues_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    tournaments_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    teams_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    players_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    players_by_team: dict[int, list[dict[str, Any]]] = field(init=False, default_factory=dict)
    teams_by_league: dict[int, list[dict[str, Any]]] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self.leagues_by_id = {int(row["source_id"]): row for row in self.payload.get("leagues", [])}
        self.tournaments_by_id = {int(row["source_id"]): row for row in self.payload.get("tournaments", [])}
        self.teams_by_id = {int(row["source_id"]): row for row in self.payload.get("teams", [])}
        self.players_by_id = {int(row["source_id"]): row for row in self.payload.get("players", [])}
        self.players_by_team: dict[int, list[dict[str, Any]]] = {}
        for player in self.payload.get("players", []):
            if player.get("retired"):
                continue
            self.players_by_team.setdefault(int(player["team_id"]), []).append(player)
        for rows in self.players_by_team.values():
            rows.sort(key=lambda p: ((p.get("shirt_number") is None), p.get("shirt_number") or 999, p.get("display_name") or ""))
        self.teams_by_league: dict[int, list[dict[str, Any]]] = {}
        for team in self.payload.get("teams", []):
            league_id = team.get("league_id")
            if isinstance(league_id, int):
                self.teams_by_league.setdefault(league_id, []).append(team)
        for rows in self.teams_by_league.values():
            rows.sort(key=lambda t: ((t.get("league_position") is None), t.get("league_position") or 999, t.get("name") or ""))

    @property
    def counts(self) -> dict[str, int]:
        return dict(self.payload.get("source_counts") or {})

    def universe_summary(self) -> dict[str, Any]:
        enrichment = dict(self.payload.get("world_cup_1994_enrichment") or {})
        return {
            "season": self.payload.get("season", "1993-94"),
            "counts": self.counts,
            "runtime_counts": {
                "teams": len(self.teams_by_id),
                "players": len(self.players_by_id),
                "market_container_teams": sum(1 for row in self.payload.get("teams", []) if row.get("market_container")),
                "world_cup_1994_added_players": int(enrichment.get("added_players") or 0),
            },
            "world_cup_1994_enrichment": enrichment,
            "default_team_id": 16 if 16 in self.teams_by_id else next((tid for tid,row in self.teams_by_id.items() if not row.get("market_container")), None),
            "competitions": {
                "leagues": len(self.leagues_by_id),
                "tournaments": len(self.tournaments_by_id),
            },
        }

    def competitions(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for league in self.payload.get("leagues", []):
            rows.append({
                "kind": "league",
                "source_id": int(league["source_id"]),
                "name": league["name"],
                "country": league.get("country"),
                "country_id": league.get("country_id"),
                "team_count": league.get("team_count"),
                "level": league.get("level"),
                "turns": league.get("turns"),
                "admitted": bool(league.get("admitted", True)),
                "signable": bool(league.get("signable", False)),
            })
        for tournament in self.payload.get("tournaments", []):
            country_id = tournament.get("country_id")
            rows.append({
                "kind": "tournament",
                "source_id": int(tournament["source_id"]),
                "name": tournament["name"],
                "country": PRESENTATION_COUNTRIES.get(country_id) if country_id else None,
                "country_id": country_id,
                "continent_id": tournament.get("continent_id"),
                "entrants": tournament.get("entrants"),
                "admitted": bool(tournament.get("admitted", True)),
            })
        return rows

    def career_competitions(self) -> list[dict[str, Any]]:
        """Competitions intended to be active in the original MDB selector.

        `Liga.ADMITIDA` is kept separate from historical presence: non-admitted
        1993 rows remain in the normalized snapshot for data provenance and
        transfers, but are not inserted into a new career.  Tournaments in this
        snapshot are already filtered by `Torneo.Admitido` and season overlap.
        """
        rows = [row for row in self.competitions() if bool(row.get("admitted"))]
        # Domestic cups absent from the imported MDB selector are derived only
        # for career play.  Keeping them out of ``competitions()`` preserves
        # source provenance while making them first-class in the living world.
        from .domestic_cups import domestic_cup_competition_rows
        known={(str(row.get("kind")), int(row.get("source_id") or 0)) for row in rows}
        for row in domestic_cup_competition_rows():
            key=(str(row["kind"]), int(row["source_id"]))
            if key not in known:
                rows.append(row); known.add(key)
        return rows

    def team(self, team_id: int) -> dict[str, Any] | None:
        row = self.teams_by_id.get(team_id)
        if row is None:
            return None
        league = self.leagues_by_id.get(row.get("league_id"))
        return {
            **row,
            "league": ({
                "source_id": league["source_id"], "name": league["name"], "country": league.get("country")
            } if league else None),
            "squad_size": len(self.players_by_team.get(team_id, ())),
        }

    def teams(self, *, league_id: int | None = None) -> list[dict[str, Any]]:
        source = self.teams_by_league.get(league_id, []) if league_id is not None else self.payload.get("teams", [])
        return [self.team(int(row["source_id"])) for row in source]

    def player_api(self, row: dict[str, Any], *, game_date: date = DEFAULT_GAME_DATE) -> dict[str, Any]:
        team = self.teams_by_id.get(int(row["team_id"]))
        country_id = row.get("international_country_id") or row.get("birth_country_id")
        overall = row.get("overall") or row.get("category")
        attributes = dict(row.get("attributes") or {})
        broad = str(row.get("broad_position") or "").strip().upper() or None
        specialist = role_api(row)
        source_ratings = {str(key): int(value or 0) for key, value in dict(row.get("role_ratings") or {}).items()}
        primary_role = row.get("primary_role")
        position_profiles: list[dict[str, Any]] = []
        for role_id, role in ROLES_9394.items():
            rating = int(source_ratings.get(str(role_id), 0) or 0)
            if role_id == primary_role:
                rating = max(100, rating)
            if rating <= 0:
                continue
            position_profiles.append({
                "source_id": role_id,
                "code": role.code,
                "name": role.name,
                "squad_slot": role.squad_slot,
                "side": role.side,
                "aptitude": rating,
                "primary": role_id == primary_role,
            })
        position_profiles.sort(key=lambda item: (not item["primary"], -int(item["aptitude"]), int(item["source_id"])))
        hidden_traits = {key: bool(value) for key, value in dict(row.get("hidden_traits") or {}).items() if bool(value)}
        status = "Disponible" if not row.get("retired") else "Retirado"
        return {
            "id": int(row["source_id"]),
            "source_id": int(row["source_id"]),
            "team_id": int(row["team_id"]),
            "team_name": team.get("name") if team else None,
            "display_name": row.get("display_name"),
            "first_name": row.get("first_name"),
            "surname1": row.get("surname1"),
            "surname2": row.get("surname2"),
            "birth_date": row.get("birth_date"),
            "age": player_age_on(row, game_date),
            "nationality": PRESENTATION_COUNTRIES.get(country_id, f"País {country_id}" if country_id else "—"),
            "nationality_id": country_id,
            "basque_origin": bool(row.get("basque_origin")),
            "position": specialist["name"],
            "position_short": specialist["code"],
            "positions": [profile["name"] for profile in position_profiles] or [specialist["name"]],
            "position_profiles": position_profiles,
            "source_role_ratings": source_ratings,
            "primary_role": primary_role,
            "specialist_role": specialist,
            "broad_position": broad,
            "preferred_foot": FOOT_NAMES.get(row.get("preferred_foot"), "—"),
            "shirt_number": row.get("shirt_number"),
            "favorite_shirt_number": row.get("favorite_shirt_number"),
            "height_cm": row.get("height_cm"),
            "weight_kg": row.get("weight_kg"),
            "overall": overall,
            "category": row.get("category"),
            "form": None,
            "morale": None,
            "condition": None,
            "status": status,
            "loan": bool(row.get("loan")),
            "initially_reserve": bool(row.get("initially_reserve")),
            "attributes": attributes,
            "source_traits": hidden_traits,
            "development": {
                "progression_mean": row.get("progression_mean"),
                "fan_affection": row.get("fan_affection"),
                "academy_team_id": row.get("academy_team_id"),
                "previous_team_id": row.get("previous_team_id"),
                "previous_team_years": row.get("previous_team_years"),
                "buyback_option": bool(row.get("buyback_option")),
            },
            "salary": row.get("salary"),
            "release_clause": row.get("release_clause"),
            "contract": {
                "start": str(row.get("contract_start_year")) if row.get("contract_start_year") else None,
                "end": str(row.get("contract_end_year")) if row.get("contract_end_year") else None,
                "salary_display": _display_money(row.get("salary")),
                "release_clause_display": _display_money(row.get("release_clause")),
                "loan": bool(row.get("loan")),
                "parent_club_name": team.get("name") if team else None,
            },
            "medical": {
                "status": status,
                "history": [],
                "injury_proneness": row.get("injury_proneness"),
            },
            "season_stats": {},
            "career": [],
            "scout": {},
            "historical_squad_1994": bool(row.get("historical_squad_1994")),
            "world_cup_1994": dict(row.get("world_cup_1994") or {}) or None,
            "historical_data_source": row.get("historical_data_source"),
            "attribute_source": row.get("attribute_source"),
            "historical_club_1994": row.get("historical_club_1994"),
            "market_container_origin": row.get("market_container_origin"),
        }

    def player(self, player_id: int, *, game_date: date = DEFAULT_GAME_DATE) -> dict[str, Any] | None:
        row = self.players_by_id.get(player_id)
        return self.player_api(row, game_date=game_date) if row else None

    def squad(self, team_id: int, *, game_date: date = DEFAULT_GAME_DATE) -> list[dict[str, Any]]:
        return [self.player_api(row, game_date=game_date) for row in self.players_by_team.get(team_id, ())]

    def league_calendar(self, league_id: int) -> list[dict[str, Any]]:
        rows = [row for row in self.payload.get("league_calendar_rows", []) if int(row.get("league_id", -1)) == league_id]
        return sorted(rows, key=lambda r: (r.get("matchday", 0), r.get("id", 0)))

    def team_calendar(self, team_id: int) -> list[dict[str, Any]]:
        team = self.team(team_id)
        if not team or not team.get("league"):
            return []
        league_id = int(team["league"]["source_id"])
        output: list[dict[str, Any]] = []
        for row in self.league_calendar(league_id):
            home_id, away_id = int(row["home_team_id"]), int(row["away_team_id"])
            if team_id not in (home_id, away_id):
                continue
            home, away = self.team(home_id), self.team(away_id)
            output.append({**row, "home_team": home["name"] if home else str(home_id),
                           "away_team": away["name"] if away else str(away_id),
                           "venue": "Casa" if home_id == team_id else "Fuera",
                           "opponent_id": away_id if home_id == team_id else home_id,
                           "opponent": (away["name"] if home_id == team_id and away else home["name"] if home else "—")})
        return output

    def search_players(self, query: str = "", *, limit: int = 20, exclude_team_id: int | None = None) -> list[dict[str, Any]]:
        normalized = " ".join(query.casefold().split())
        candidates = []
        for row in self.payload.get("players", []):
            if exclude_team_id is not None and int(row["team_id"]) == exclude_team_id:
                continue
            name = str(row.get("display_name") or "")
            if normalized and normalized not in name.casefold():
                continue
            candidates.append(row)
        candidates.sort(key=lambda p: (-(int(p.get("overall") or p.get("category") or 0)), p.get("display_name") or ""))
        return [self.player_api(row) for row in candidates[:max(1, min(limit, 100))]]


def load_runtime_snapshot(path: str | Path = DEFAULT_SNAPSHOT_PATH) -> FootballUniverseSnapshot9394:
    snapshot_path = Path(path)
    # The bundled historical universe is ~22 MB and dominates a true cold
    # process start. orjson already ships with the desktop backend for career
    # saves and parses UTF-8 bytes around 2x faster than stdlib json here. Keep
    # the stdlib fallback so source/development environments remain compatible.
    if orjson is not None:
        payload = orjson.loads(snapshot_path.read_bytes())
    else:
        with snapshot_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    return FootballUniverseSnapshot9394(payload)


@lru_cache(maxsize=1)
def default_runtime_snapshot() -> FootballUniverseSnapshot9394:
    return load_runtime_snapshot(DEFAULT_SNAPSHOT_PATH)
