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
from pathlib import Path
from typing import Any

from .mdb_import import HISTORICAL_COUNTRY_NAMES

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SNAPSHOT_PATH = REPO_ROOT / "data" / "football9394" / "historical_snapshot.json"
DEFAULT_GAME_DATE = date(1993, 10, 23)

# These names only affect presentation. Unknown ids remain visible rather than
# being guessed so data-quality work can resolve them later.
PRESENTATION_COUNTRIES = {
    **HISTORICAL_COUNTRY_NAMES,
    20: "Bosnia y Herzegovina",
    62: "Brasil",
    87: "Mozambique",
    117: "Cabo Verde",
    120: "Guinea Ecuatorial",
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
        return {
            "season": self.payload.get("season", "1993-94"),
            "counts": self.counts,
            "default_team_id": 16 if 16 in self.teams_by_id else next(iter(self.teams_by_id), None),
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
        return [row for row in self.competitions() if bool(row.get("admitted"))]

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
            "age": age_on(row.get("birth_date"), game_date),
            "nationality": PRESENTATION_COUNTRIES.get(country_id, f"País {country_id}" if country_id else "—"),
            "nationality_id": country_id,
            "position": BROAD_POSITION_NAMES.get(broad, broad or "—"),
            "position_short": BROAD_POSITION_NAMES.get(broad, broad or "—"),
            "positions": [BROAD_POSITION_NAMES.get(broad, broad)] if broad else [],
            "primary_role": row.get("primary_role"),
            "preferred_foot": FOOT_NAMES.get(row.get("preferred_foot"), "—"),
            "shirt_number": row.get("shirt_number"),
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
            "medical": {"status": status, "history": []},
            "season_stats": {},
            "career": [],
            "scout": {},
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
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return FootballUniverseSnapshot9394(payload)


@lru_cache(maxsize=1)
def default_runtime_snapshot() -> FootballUniverseSnapshot9394:
    return load_runtime_snapshot(DEFAULT_SNAPSHOT_PATH)
