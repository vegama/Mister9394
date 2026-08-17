from __future__ import annotations

"""Source-backed referee selection and disciplinary profile."""

from typing import Any

from .match_engine import RefereeProfile9394
from .source_catalog_runtime import HistoricalSourceCatalog9394, default_source_catalog


def referee_profile_from_source(row: dict[str, Any] | None) -> RefereeProfile9394 | None:
    if not row:
        return None
    return RefereeProfile9394(
        source_id=str(row["source_id"]),
        name=str(row.get("display_name") or f"Árbitro {row['source_id']}"),
        yellow_tendency=float(row["yellow_tendency"] if row.get("yellow_tendency") is not None else 4.5),
        red_tendency=float(row["red_tendency"] if row.get("red_tendency") is not None else 0.45),
        quality=int(row["quality"] if row.get("quality") is not None else 65),
        temporal_confidence=row.get("temporal_confidence"),
    )


def referee_for_match(
    league_id: int,
    *,
    seed: int,
    catalog: HistoricalSourceCatalog9394 | None = None,
) -> RefereeProfile9394 | None:
    """Pick one source referee deterministically from the league pool.

    The pool membership and card parameters are useful source structure.  The
    catalogue carries temporal-confidence metadata because names/DOBs mix
    database editions; the game must not silently present DOB as historical.
    """
    catalog = catalog or default_source_catalog()
    pool = catalog.referees_for_league(int(league_id))
    if not pool:
        return None
    # Deterministic but not quality-ranked assignment: every source referee can
    # receive matches and replaying a save with the same seed gives the same ref.
    row = pool[abs(int(seed)) % len(pool)]
    return referee_profile_from_source(row)
