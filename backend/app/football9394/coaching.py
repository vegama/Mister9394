from __future__ import annotations

"""Source-backed coaches for the 1993-94 world.

The supplied MDB contains a rich Entrenador entity that the original importer
had accidentally dropped.  This module turns that source entity into gameplay
without converting coach quality into a flat team-rating bonus.

Safe gameplay effects:
- source primary formation/tactic drives AI shape;
- documented game tendency drives mentality;
- source pressing level is mapped to the engine's three bands;
- rotation preference changes substitution timing;
- quality + tendency + youth usage + relationship + player fit alter long-term
  development, never the player's instant base overall.

Individual coach assignments are marked mixed-edition in the source catalogue;
we preserve that provenance and do not claim every name/club pairing is already
historically curated for 23 October 1993.
"""

from datetime import date, datetime
from typing import Any

from .match_engine import FootballTactics9394
from .position_roles import FORMATION_SLOTS_9394
from .source_catalog_runtime import HistoricalSourceCatalog9394, default_source_catalog


_FORMATION_ALIASES = {
    "4-4-1": "4-4-1-1",
}


def _canonical_formation(source_tactic: dict[str, Any] | None) -> str:
    if not source_tactic:
        return "4-4-2"
    name = str(source_tactic.get("name") or "").strip()
    # The human-readable tactic name can be more specific than Tipo: the source
    # 4-2-3-1 template, for example, is broadly classified as 4-5-1 in Tipo.
    for formation in sorted(FORMATION_SLOTS_9394, key=len, reverse=True):
        if name.startswith(formation):
            return formation
    raw = str(source_tactic.get("formation_type") or "").strip()
    raw = _FORMATION_ALIASES.get(raw, raw)
    if raw in FORMATION_SLOTS_9394:
        return raw
    return "4-4-2"


def tactics_from_source_manager(manager: dict[str, Any] | None, *, variant: str = "primary") -> FootballTactics9394:
    if not manager:
        return FootballTactics9394()
    tactic = (manager.get("tactics") or {}).get(variant) or (manager.get("tactics") or {}).get("primary") or {}
    tendency = str(manager.get("game_tendency") or "normal")
    if variant == "attacking":
        mentality = "attacking"
    elif variant == "defensive":
        mentality = "defensive"
    else:
        mentality = {"defensive": "defensive", "normal": "balanced", "attacking": "attacking"}.get(tendency, "balanced")
    pressure_raw = tactic.get("pressing_level")
    # The source uses four pressure bands (0..3); the current engine has three.
    # This is a lossy UI/engine mapping, while raw source value remains in the
    # catalogue for a future four-band implementation.
    pressing = {0: "low", 1: "medium", 2: "high", 3: "high"}.get(pressure_raw, "medium")
    formation = _canonical_formation(tactic)
    width = "wide" if formation in {"4-3-3", "3-4-3", "5-2-3", "4-2-4"} else "narrow" if formation in {"4-3-1-2", "3-4-1-2"} else "normal"
    defensive_line = "low" if mentality == "defensive" else "high" if mentality == "attacking" and pressing == "high" else "medium"
    return FootballTactics9394(
        formation=formation,
        mentality=mentality,
        tempo="normal",
        pressing=pressing,
        directness="mixed",
        defensive_line=defensive_line,
        width=width,
        offside_trap=False,
        marking="zonal",
    )


def source_coach_for_team(
    universe: Any,
    team_id: int,
    *,
    catalog: HistoricalSourceCatalog9394 | None = None,
    manager_id: int | None = None,
) -> dict[str, Any] | None:
    team = universe.team(int(team_id)) if hasattr(universe, "team") else None
    if manager_id is None:
        manager_id = team.get("manager_id") if team else None
    if not isinstance(manager_id, int):
        return None
    catalog = catalog or default_source_catalog()
    manager = catalog.manager_with_tactics(manager_id)
    if manager is None:
        return None
    tactics = tactics_from_source_manager(manager, variant="primary")
    attacking = tactics_from_source_manager(manager, variant="attacking")
    defensive = tactics_from_source_manager(manager, variant="defensive")
    def payload(t: FootballTactics9394) -> dict[str, Any]:
        return {
            "formation": t.formation, "mentality": t.mentality, "tempo": t.tempo,
            "pressing": t.pressing, "directness": t.directness, "defensive_line": t.defensive_line,
            "width": t.width, "offside_trap": t.offside_trap, "marking": t.marking,
        }
    return {**manager, "engine_tactics": payload(tactics), "engine_attacking_tactics": payload(attacking), "engine_defensive_tactics": payload(defensive)}


def _age(player: dict[str, Any], game_date: date | None) -> int | None:
    raw = player.get("birth_date")
    if not raw or game_date is None:
        return None
    try:
        born = datetime.fromisoformat(str(raw)).date()
    except (TypeError, ValueError):
        return None
    return game_date.year - born.year - ((game_date.month, game_date.day) < (born.month, born.day))


def coaching_development_factor(
    manager: dict[str, Any] | None,
    player: dict[str, Any],
    *,
    game_date: date | None = None,
) -> float:
    """Return a restrained positive-development multiplier.

    The original editor explicitly says TendenciaJuego combined with CALIDAD
    influences player development.  It does not document an exact formula, so
    this function is intentionally conservative and transparent.  A great
    coach helps compatible players more; no coach grants an instant overall
    bonus and negative match consequences are not erased.
    """
    if not manager:
        return 1.0
    quality = int(manager.get("coaching_quality") or 60)
    factor = 0.88 + max(0, min(100, quality)) / 300.0  # 1.03 at 44; 1.19 at 93

    tendency = str(manager.get("game_tendency") or "normal")
    broad = str(player.get("broad_position") or "").upper()
    primary_role = player.get("primary_role")
    defensive_role = broad in {"POR", "DEF"} or primary_role in {0, 1, 2, 3, 4, 5, 6}
    attacking_role = broad == "DEL" or primary_role in {8, 11, 12, 15, 16, 17}
    if tendency == "defensive":
        factor += 0.08 if defensive_role else -0.025 if attacking_role else 0.02
    elif tendency == "attacking":
        factor += 0.08 if attacking_role else -0.025 if defensive_role else 0.02
    else:
        factor += 0.025

    age = _age(player, game_date)
    youth = str(manager.get("youth_usage") or "normal")
    if age is not None and age <= 23:
        factor += {"low": -0.05, "normal": 0.0, "high": 0.08}.get(youth, 0.0)

    relationship = str(manager.get("player_relationship") or "normal")
    factor += {"distant": -0.02, "normal": 0.0, "close": 0.035}.get(relationship, 0.0)

    # ProgresionMedia is a documented 0..9 source field.  It acts as a player's
    # own receptiveness/growth signal, not as an invented potential value.
    progression = player.get("progression_mean")
    if isinstance(progression, int):
        factor += (max(0, min(9, progression)) - 4) * 0.018

    preferred = manager.get("preferred_player_patterns") or []
    if preferred and isinstance(primary_role, int):
        if any(pattern.get("role_id") == primary_role for pattern in preferred):
            factor += 0.06

    return round(max(0.72, min(1.42, factor)), 4)


def substitution_threshold_adjustment(manager: dict[str, Any] | None) -> int:
    """Minutes/fatigue threshold shift from documented rotation frequency."""
    rotation = str((manager or {}).get("rotation_frequency") or "normal")
    # Lower threshold => coach changes tired players sooner/more readily.
    return {"high": -5, "normal": 0, "low": 5}.get(rotation, 0)
