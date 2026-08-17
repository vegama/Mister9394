from __future__ import annotations

"""Long-career ageing, retirement and academy generation.

1993-94 remains the historical anchor. From the first rollover onward the save
becomes an alternate football history. Generated players are explicitly marked
as simulation-created and use the MDB's weighted country name pools.
"""

from datetime import date
from random import Random
from typing import Any, Iterable

from .player_identity import age_on
from .position_roles import MINIMUM_SENIOR_SQUAD_SIZE_9394, ROLES_9394, TARGET_SENIOR_SQUAD_SIZE_9394, squad_role_audit
from .source_catalog_runtime import HistoricalSourceCatalog9394, default_source_catalog

MIN_OVERALL = 32
MAX_OVERALL = 95

AGE_POLICY_DYNAMIC = "dynamic_from_birth_date"
AGE_POLICY_FROZEN = "frozen_attributes_dynamic"


def ensure_long_career_state(state: dict[str, Any]) -> None:
    state.setdefault("generated_players", {})
    state.setdefault("next_generated_player_id", 10_000_000)
    state.setdefault("retirement_history", [])
    state.setdefault("academy_history", [])
    # Frozen age is the product default: the historical cast remains in the
    # universe indefinitely, but development/injuries/form can still change
    # ability. Dynamic ageing remains available as an explicit alternative.
    state.setdefault("age_policy", AGE_POLICY_FROZEN)


def uses_frozen_age(state: dict[str, Any]) -> bool:
    ensure_long_career_state(state)
    return str(state.get("age_policy") or AGE_POLICY_FROZEN) == AGE_POLICY_FROZEN


def all_generated_players(state: dict[str, Any]) -> list[dict[str, Any]]:
    ensure_long_career_state(state)
    rows = state.get("generated_players") or {}
    return [dict(row) for _, row in sorted(rows.items(), key=lambda kv: int(kv[0]))]


def generated_player(state: dict[str, Any], player_id: int) -> dict[str, Any] | None:
    ensure_long_career_state(state)
    row = (state.get("generated_players") or {}).get(str(int(player_id)))
    return dict(row) if row else None


def _weighted_text(rng: Random, rows: list[dict[str, Any]], fallback: str) -> str:
    if not rows:
        return fallback
    weights = [max(1, int(row.get("weight") or 1)) for row in rows]
    return str(rng.choices(rows, weights=weights, k=1)[0].get("text") or fallback)


def _country_for_team(universe: Any, team_id: int) -> int | None:
    team = universe.team(int(team_id)) or {}
    league_id = (team.get("league") or {}).get("source_id") or team.get("league_id")
    league = universe.leagues_by_id.get(int(league_id)) if league_id is not None else None
    return int(league.get("country_id")) if league and league.get("country_id") is not None else None


def _broad_for_role(role_id: int) -> str:
    slot = ROLES_9394[role_id].squad_slot
    if slot == "GK": return "POR"
    if slot in {"RB", "LB", "CB"}: return "DEF"
    if slot == "ST": return "DEL"
    return "MED"


def _newgen_attributes(rng: Random, role_id: int, overall: int) -> dict[str, int]:
    slot = ROLES_9394[role_id].squad_slot
    base_keys = ["pace", "acceleration", "jumping", "stamina", "strength", "tackling", "work_rate", "aggression", "anticipation", "marking", "discipline", "positioning", "leadership", "consistency", "vision", "short_pass", "long_pass", "dribbling", "finishing", "heading", "off_ball", "shot_power", "free_kicks", "penalties", "technique"]
    values = {key: max(28, min(92, overall + rng.randint(-12, 12))) for key in base_keys}
    boosts: dict[str, tuple[str, ...]] = {
        "GK": ("positioning", "anticipation", "strength", "long_pass"),
        "RB": ("pace", "stamina", "tackling", "marking"), "LB": ("pace", "stamina", "tackling", "marking"),
        "CB": ("strength", "heading", "marking", "positioning", "tackling"),
        "DM": ("tackling", "positioning", "work_rate", "short_pass"),
        "CM": ("short_pass", "vision", "technique", "stamina"),
        "AM": ("vision", "dribbling", "technique", "finishing"),
        "RM": ("pace", "stamina", "dribbling", "off_ball"), "LM": ("pace", "stamina", "dribbling", "off_ball"),
        "RW": ("pace", "dribbling", "off_ball", "finishing"), "LW": ("pace", "dribbling", "off_ball", "finishing"),
        "ST": ("finishing", "off_ball", "heading", "shot_power"),
    }
    for key in boosts.get(slot, ()): values[key] = min(95, values[key] + rng.randint(5, 13))
    return values


def generate_academy_player(
    state: dict[str, Any], *, universe: Any, team_id: int, game_date: date, seed: int,
    catalog: HistoricalSourceCatalog9394 | None = None, players_by_team: dict[int, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    ensure_long_career_state(state)
    catalog = catalog or default_source_catalog()
    rng = Random(int(seed) ^ int(team_id) * 12011 ^ game_date.year * 9394)
    country_id = _country_for_team(universe, team_id) or 11
    pool = catalog.name_pool(country_id)
    country = catalog.countries_by_id.get(country_id) or {}
    first = _weighted_text(rng, list(pool.get("first_names") or []), "Carlos")
    surname1 = _weighted_text(rng, list(pool.get("surnames") or []), "García")
    surname2 = _weighted_text(rng, list(pool.get("surnames") or []), "") if country.get("uses_second_surname") else ""
    team = universe.team(int(team_id)) or {}
    academy = int(team.get("academy_level") or 0)
    squad = list((players_by_team or {}).get(int(team_id), ())) or [p for p in universe.players_by_team.get(int(team_id), ())]
    audit = squad_role_audit(squad)
    need_slots = [str(row["slot"]) for row in audit.get("needs") or [] for _ in range(max(1, int(row.get("shortage") or 0)))]
    desired_slot = rng.choice(need_slots) if need_slots else rng.choice(["GK", "RB", "LB", "CB", "DM", "CM", "AM", "RM", "LM", "RW", "LW", "ST"])
    role_candidates = [rid for rid, role in ROLES_9394.items() if role.squad_slot == desired_slot]
    role_id = rng.choice(role_candidates or [17])
    age = rng.choices([16, 17, 18, 19], weights=[1, 4, 4, 1], k=1)[0]
    birth = date(game_date.year - age, rng.randint(1, 12), rng.randint(1, 28))
    # Academy quality changes the distribution but never guarantees a star.
    overall = max(42, min(78, 51 + academy * 2 + rng.randint(-7, 9)))
    progression = max(2, min(9, 4 + academy // 2 + rng.randint(-2, 2)))
    pid = int(state["next_generated_player_id"]); state["next_generated_player_id"] = pid + 1
    role_ratings = {str(rid): 0 for rid in ROLES_9394}
    role_ratings[str(role_id)] = 100
    for rid, role in ROLES_9394.items():
        if rid != role_id and role.squad_slot == desired_slot:
            role_ratings[str(rid)] = rng.randint(65, 88)
    row = {
        "source_id": pid, "team_id": int(team_id), "display_name": surname1,
        "first_name": first, "surname1": surname1, "surname2": surname2 or None,
        "birth_date": birth.isoformat(), "birth_country_id": country_id, "international_country_id": country_id,
        "preferred_foot": rng.choice([1, 1, 1, 3, 2]), "shirt_number": None, "primary_role": role_id,
        "broad_position": _broad_for_role(role_id), "overall": overall, "category": overall,
        "height_cm": rng.randint(168, 194), "weight_kg": rng.randint(62, 88), "salary": 0, "release_clause": 0,
        "contract_start_year": game_date.year, "contract_end_year": game_date.year + 3,
        "loan": False, "initially_reserve": True, "retired": False,
        "attributes": _newgen_attributes(rng, role_id, overall),
        "birth_city_id": None, "naturalized_country_id": None, "basque_origin": False,
        "favorite_shirt_number": 0, "injury_proneness": rng.choices([0, 1, 2], weights=[78, 19, 3], k=1)[0],
        "progression_mean": progression, "fan_affection": 3, "academy_team_id": int(team_id),
        "previous_team_id": 0, "previous_team_years": 0, "buyback_option": 0,
        "role_ratings": role_ratings,
        "hidden_traits": {
            "individualist": rng.random() < .08, "killer_pass": rng.random() < .10, "holds_ball": rng.random() < .10,
            "long_shots": rng.random() < .10, "cuts_inside": rng.random() < .10, "first_time_play": rng.random() < .10,
            "dives": rng.random() < .04,
        },
        "generated": True, "generated_season": str(state.get("season")), "provenance": "career_generated_from_mdb_country_name_pool",
    }
    state["generated_players"][str(pid)] = row
    state.setdefault("player_team_overrides", {})[str(pid)] = int(team_id)
    state.setdefault("player_development", {})[str(pid)] = {
        "base_overall": overall, "overall": overall, "form": 65, "morale": 68, "condition": 100,
        "injury_days": 0, "current_injury": None, "injury_history": [], "season_minutes": 0, "season_appearances": 0, "season_starts": 0,
        "season_goals": 0, "season_assists": 0, "season_rating_total": 0.0, "season_rating_count": 0,
        "season_yellows": 0, "season_reds": 0, "development_points": 0.0,
        "physical_delta": 0, "technical_delta": 0, "retired": False,
    }
    return row


def apply_ageing_and_retirement(
    state: dict[str, Any], *, players: Iterable[dict[str, Any]], game_date: date, seed: int,
) -> list[dict[str, Any]]:
    ensure_long_career_state(state)
    if uses_frozen_age(state):
        return []
    events: list[dict[str, Any]] = []
    for player in players:
        pid = str(int(player["source_id"]))
        dev = state.setdefault("player_development", {}).setdefault(pid, {})
        if bool(dev.get("retired")):
            continue
        age = age_on(player, game_date)
        if age is None:
            continue
        rng = Random(int(seed) ^ int(pid) * 1543 ^ game_date.year * 97)
        progression = max(0, min(9, int(player.get("progression_mean") or 4)))
        overall = int(dev.get("overall") or player.get("overall") or player.get("category") or 60)
        drift = 0
        physical = int(dev.get("physical_delta") or 0)
        technical = int(dev.get("technical_delta") or 0)
        if age <= 20:
            if rng.random() < .42 + progression * .045: drift = 1
            if progression >= 7 and rng.random() < .18: drift += 1
        elif age <= 23:
            if rng.random() < .28 + progression * .035: drift = 1
        elif age <= 27:
            if rng.random() < .10 + progression * .018: drift = 1
        elif age <= 30:
            if rng.random() < .13: drift = -1
        elif age <= 32:
            if rng.random() < .42: drift = -1
            physical -= 1
        elif age <= 34:
            drift = -1 if rng.random() < .72 else 0
            physical -= 2
            if rng.random() < .22: technical -= 1
        else:
            drift = -1 - (1 if age >= 37 and rng.random() < .55 else 0)
            physical -= 2
            if rng.random() < .40: technical -= 1
        overall = max(MIN_OVERALL, min(MAX_OVERALL, overall + drift))
        dev["overall"] = overall
        dev["physical_delta"] = max(-18, min(8, physical))
        dev["technical_delta"] = max(-10, min(10, technical))
        retire_chance = 0.0
        if age >= 38: retire_chance = .66
        elif age == 37: retire_chance = .42
        elif age == 36: retire_chance = .27
        elif age == 35: retire_chance = .16
        elif age == 34: retire_chance = .07
        if overall <= 48 and age >= 32: retire_chance += .12
        if retire_chance and rng.random() < min(.92, retire_chance):
            dev["retired"] = True
            dev["retired_on"] = game_date.isoformat()
            state.setdefault("player_team_overrides", {})[pid] = 0
            event = {"kind": "player_retirement", "date": game_date.isoformat(), "player_id": int(pid), "age": age, "overall": overall}
            state["retirement_history"].append(event); events.append(event)
    state["retirement_history"] = state["retirement_history"][-2000:]
    return events


def generate_annual_academy_intake(
    state: dict[str, Any], *, universe: Any, team_ids: Iterable[int], game_date: date, seed: int,
    players_by_team: dict[int, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    ensure_long_career_state(state)
    if uses_frozen_age(state):
        return []
    events: list[dict[str, Any]] = []
    for team_id in sorted({int(x) for x in team_ids if int(x) != 0}):
        team = universe.team(team_id) or {}
        academy = int(team.get("academy_level") or 0)
        rng = Random(seed ^ team_id * 3907 ^ game_date.year)
        # Only prospects ready for the senior squad are materialised.  The
        # unseen academy can contain many more youngsters, but promoting one to
        # every club every summer would inflate senior rosters by hundreds of
        # players per year.  Promotions therefore fill real depth/vacancy gaps.
        current_size = len((players_by_team or {}).get(team_id, universe.players_by_team.get(team_id, ())))
        gap = max(0, TARGET_SENIOR_SQUAD_SIZE_9394 - current_size)
        if gap <= 0:
            continue
        mandatory = max(0, MINIMUM_SENIOR_SQUAD_SIZE_9394 - current_size)
        normal_promotion = 1 if mandatory == 0 else mandatory
        bonus = 1 if academy >= 2 and gap > normal_promotion and rng.random() < .28 else 0
        count = min(gap, normal_promotion + bonus)
        for index in range(count):
            player = generate_academy_player(state, universe=universe, team_id=team_id, game_date=game_date, seed=seed + index * 41, players_by_team=players_by_team)
            if players_by_team is not None:
                players_by_team.setdefault(team_id, []).append(player)
            event = {"kind": "academy_intake", "date": game_date.isoformat(), "team_id": team_id, "player_id": int(player["source_id"]), "name": player["display_name"], "age": age_on(player, game_date)}
            state["academy_history"].append(event); events.append(event)
    state["academy_history"] = state["academy_history"][-3000:]
    return events
