from __future__ import annotations

"""Lazy runtime access to the deep MDB-derived source catalogue.

The main historical snapshot stays fast to load.  Rich source entities such as
coaches, referees, injury definitions and weighted newgen names are indexed only
when a subsystem actually asks for them.
"""

from dataclasses import dataclass, field
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_CATALOG_PATH = REPO_ROOT / "data" / "football9394" / "historical_source_catalog.json"


@dataclass(slots=True)
class HistoricalSourceCatalog9394:
    payload: dict[str, Any]
    managers_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    referees_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    stadiums_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    countries_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    cities_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    regions_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    climates_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    continents_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    roles_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    patterns_by_id: dict[int, dict[str, Any]] = field(init=False, default_factory=dict)
    tactics_by_name: dict[str, dict[str, Any]] = field(init=False, default_factory=dict)
    referees_by_league: dict[int, list[dict[str, Any]]] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self.managers_by_id = {int(row["source_id"]): row for row in self.payload.get("managers", [])}
        self.referees_by_id = {int(row["source_id"]): row for row in self.payload.get("referees", [])}
        self.stadiums_by_id = {int(row["source_id"]): row for row in self.payload.get("stadiums", [])}
        self.countries_by_id = {int(row["source_id"]): row for row in self.payload.get("countries", [])}
        self.cities_by_id = {int(row["source_id"]): row for row in self.payload.get("cities", [])}
        self.regions_by_id = {int(row["source_id"]): row for row in self.payload.get("regions", [])}
        self.climates_by_id = {int(row["Id"]): row for row in self.payload.get("climates", []) if isinstance(row.get("Id"), int)}
        self.continents_by_id = {int(row["source_id"]): row for row in self.payload.get("continents", [])}
        self.roles_by_id = {int(row["source_id"]): row for row in self.payload.get("roles", [])}
        self.patterns_by_id = {int(row["source_id"]): row for row in self.payload.get("player_patterns", [])}
        self.tactics_by_name = {str(row["name"]): row for row in self.payload.get("tactics", [])}
        for referee in self.payload.get("referees", []):
            league_id = referee.get("league_id")
            if isinstance(league_id, int):
                self.referees_by_league.setdefault(league_id, []).append(referee)
        for rows in self.referees_by_league.values():
            rows.sort(key=lambda row: (-int(row.get("quality") or 0), str(row.get("display_name") or "")))

    @property
    def counts(self) -> dict[str, int]:
        return dict(self.payload.get("counts") or {})

    def manager(self, manager_id: int | None) -> dict[str, Any] | None:
        return self.managers_by_id.get(int(manager_id)) if isinstance(manager_id, int) else None

    def tactic(self, name: str | None) -> dict[str, Any] | None:
        return self.tactics_by_name.get(str(name)) if name else None

    def manager_with_tactics(self, manager_id: int | None) -> dict[str, Any] | None:
        manager = self.manager(manager_id)
        if manager is None:
            return None
        return {
            **manager,
            "tactics": {
                "primary": self.tactic(manager.get("primary_tactic")),
                "attacking": self.tactic(manager.get("attacking_tactic")),
                "defensive": self.tactic(manager.get("defensive_tactic")),
            },
            "preferred_player_patterns": [
                self.patterns_by_id[pattern_id]
                for pattern_id in manager.get("preferred_player_pattern_ids", [])
                if pattern_id in self.patterns_by_id
            ],
        }

    def stadium(self, stadium_id: int | None) -> dict[str, Any] | None:
        return self.stadiums_by_id.get(int(stadium_id)) if isinstance(stadium_id, int) else None

    def venue_context(self, stadium_id: int | None) -> dict[str, Any] | None:
        stadium = self.stadium(stadium_id)
        if stadium is None:
            return None
        city = self.cities_by_id.get(int(stadium.get("city_id"))) if isinstance(stadium.get("city_id"), int) else None
        climate = self.climates_by_id.get(int(city.get("climate_id"))) if city and isinstance(city.get("climate_id"), int) else None
        region = self.regions_by_id.get(int(city.get("region_id"))) if city and isinstance(city.get("region_id"), int) else None
        return {**stadium, "city": city, "climate": climate, "region": region}

    def referees_for_league(self, league_id: int) -> list[dict[str, Any]]:
        return list(self.referees_by_league.get(int(league_id), ()))

    def name_pool(self, country_id: int) -> dict[str, list[dict[str, Any]]]:
        return dict((self.payload.get("name_pools") or {}).get(str(int(country_id))) or {})


def load_source_catalog(path: str | Path = DEFAULT_SOURCE_CATALOG_PATH) -> HistoricalSourceCatalog9394:
    return HistoricalSourceCatalog9394(json.loads(Path(path).read_text(encoding="utf-8")))


@lru_cache(maxsize=1)
def default_source_catalog() -> HistoricalSourceCatalog9394:
    return load_source_catalog(DEFAULT_SOURCE_CATALOG_PATH)
