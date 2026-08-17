from __future__ import annotations

"""Stadium context for the 1993-94 match engine.

The MDB stadium dimensions/grass/city are source data, but the catalogue mixes
editions.  Therefore the engine uses the physical structure with deliberately
small effects and carries the temporal-confidence flag through to the UI.
Climate is descriptive geography, not match-day weather.
"""

from typing import Any

from .match_engine import MatchVenue9394
from .source_catalog_runtime import default_source_catalog


def venue_for_team(universe: Any, team_id: int) -> MatchVenue9394 | None:
    team = universe.team(int(team_id)) if hasattr(universe, "team") else None
    if not team:
        return None
    stadium_id = team.get("stadium_id")
    if not isinstance(stadium_id, int):
        return None
    row = default_source_catalog().venue_context(stadium_id)
    if not row:
        return None
    city = row.get("city") or {}
    climate = row.get("climate") or {}
    width = int(row["width_m"]) if isinstance(row.get("width_m"), int) else None
    length = int(row["length_m"]) if isinstance(row.get("length_m"), int) else None
    grass = int(row["grass_quality"]) if isinstance(row.get("grass_quality"), int) else None
    # A few mixed-edition source rows contain impossible/placeholder pitch
    # dimensions. Keep the stadium identity but do not let corrupt dimensions
    # become gameplay.
    if width is not None and not 45 <= width <= 100: width = None
    if length is not None and not 80 <= length <= 130: length = None
    if grass is not None and not 0 <= grass <= 100: grass = None
    return MatchVenue9394(
        source_id=str(int(row["source_id"])),
        name=str(row.get("name") or team.get("name") or "Estadio"),
        city_name=(str(city.get("name")) if city.get("name") else None),
        width_m=width,
        length_m=length,
        grass_quality=grass,
        capacity=(int(row["capacity"]) if isinstance(row.get("capacity"), int) else None),
        climate_name=(str(climate.get("Nombre")) if climate.get("Nombre") else None),
        temporal_confidence=row.get("temporal_confidence"),
    )
