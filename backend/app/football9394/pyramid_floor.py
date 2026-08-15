from __future__ import annotations

"""Career boundary policy for partially represented national pyramids.

The source MDB is authoritative for the divisions we currently simulate, but it
is not a complete world pyramid.  Product rule: the lowest represented admitted
league in each country is a *closed floor* for sporting relegation.  Clubs can
still be promoted out of that floor and replaced by relegated clubs from the
level above, but nobody is sent into an invented lower division.

Reserve-team incompatibility is different from sporting relegation.  If a parent
club drops into the reserve's division, the reserve cannot remain alongside it;
that structural exit is kept explicit so the family rule is not violated even
though the lower division itself is outside the represented world.
"""

from dataclasses import dataclass
from typing import Any, Iterable


_RELEGATION_FIELDS = (
    "relegated_team_ids",
    "relegated_team_id",
    "direct_relegated_team_id",
    "relegated_to_tercera",
    "direct_or_forced_relegated",
)


@dataclass(frozen=True, slots=True)
class PyramidFloor9394:
    country: str
    lowest_level: int
    league_source_ids: tuple[int, ...]


def active_pyramid_floors(competitions: Iterable[dict[str, Any]]) -> dict[str, PyramidFloor9394]:
    """Return the lowest represented admitted league level for every country."""
    by_country: dict[str, list[dict[str, Any]]] = {}
    for row in competitions:
        if row.get("kind") != "league" or not bool(row.get("admitted", True)):
            continue
        country = str(row.get("country") or "").strip()
        level = row.get("level")
        if not country or level is None:
            continue
        by_country.setdefault(country, []).append(row)

    floors: dict[str, PyramidFloor9394] = {}
    for country, rows in by_country.items():
        lowest = max(int(row["level"]) for row in rows)
        ids = tuple(sorted(int(row["source_id"]) for row in rows if int(row["level"]) == lowest))
        floors[country] = PyramidFloor9394(country=country, lowest_level=lowest, league_source_ids=ids)
    return floors


def is_floor_league(row: dict[str, Any], floors: dict[str, PyramidFloor9394]) -> bool:
    if row.get("kind") != "league" or not bool(row.get("admitted", True)):
        return False
    country = str(row.get("country") or "").strip()
    floor = floors.get(country)
    if floor is None:
        return False
    try:
        return int(row.get("source_id")) in floor.league_source_ids
    except (TypeError, ValueError):
        return False


def apply_closed_floor_to_output(
    output: dict[str, Any], *, source_row: dict[str, Any], floors: dict[str, PyramidFloor9394]
) -> dict[str, Any]:
    """Suppress sporting relegation from the lowest represented division.

    Historical engines may still calculate who *would* have occupied relegation
    places.  Those values are retained under ``historical_relegation_candidates``
    for QA, while gameplay movement fields are cleared.  Forced reserve-team
    exits are preserved separately as structural exits because a reserve cannot
    share a division with its parent.
    """
    result = dict(output)
    if not is_floor_league(source_row, floors):
        result.setdefault("relegation_enabled", True)
        result.setdefault("pyramid_floor", False)
        return result

    historical: list[int | str] = []
    structural = tuple(result.get("forced_reserve_relegated") or ())
    for field in _RELEGATION_FIELDS:
        value = result.get(field)
        if value is None:
            continue
        values = value if isinstance(value, (tuple, list, set)) else (value,)
        for item in values:
            if item not in historical:
                historical.append(item)
        if field == "relegated_team_id" or field == "direct_relegated_team_id":
            result[field] = None
        else:
            result[field] = ()

    # Forced reserve exits are not sporting relegations.  They leave the
    # represented pyramid only when required to keep parent/reserve categories
    # legal; they are not used to fill ordinary relegation quotas.
    result["structural_exit_team_ids"] = structural
    result["historical_relegation_candidates"] = tuple(historical)
    result["relegation_enabled"] = False
    result["pyramid_floor"] = True
    result["pyramid_floor_reason"] = "lowest_represented_division_has_no_sporting_relegation"
    return result
