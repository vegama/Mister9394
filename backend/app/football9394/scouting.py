from __future__ import annotations

"""NF1 scouting knowledge for the persistent 1993-94 career.

The source database always keeps the canonical truth.  This module controls how
much of that truth reaches the manager.  Knowledge is persistent, reports take
calendar time and the responsible staff member changes report speed/confidence.
"""

from datetime import date, timedelta
from random import Random
from typing import Any, Callable
import unicodedata
from uuid import uuid4

SCOUTING_SCHEMA_9394 = 1

LEVEL_LABELS = {
    0: "Desconocido",
    1: "Referencia básica",
    2: "Seguimiento inicial",
    3: "Informe fiable",
    4: "Conocimiento profundo",
}

_ATTRIBUTE_LABELS = {
    "technique": "técnica", "short_pass": "pase corto", "long_pass": "pase largo",
    "crossing": "centro", "dribbling": "regate", "finishing": "finalización",
    "heading": "juego aéreo", "pace": "velocidad", "acceleration": "aceleración",
    "stamina": "resistencia", "strength": "fuerza", "positioning": "colocación",
    "anticipation": "anticipación", "vision": "visión", "off_ball": "desmarque",
    "work_rate": "trabajo", "tackling": "entrada", "marking": "marcaje",
    "interception": "intercepción", "goalkeeping": "portería", "reflexes": "reflejos",
}


def ensure_scouting_state(state: dict[str, Any]) -> None:
    state.setdefault("scouting_knowledge", {})
    state.setdefault("scouting_assignments", {})


def _entry(state: dict[str, Any], player_id: int) -> dict[str, Any]:
    ensure_scouting_state(state)
    return state["scouting_knowledge"].setdefault(str(int(player_id)), {
        "player_id": int(player_id), "level": 0, "confidence": 0,
        "first_seen": None, "updated_on": None, "reports": 0,
        "source": None, "observer": None,
    })


def register_reference(state: dict[str, Any], *, player_id: int, game_date: date, source: str = "market_reference") -> dict[str, Any]:
    row = _entry(state, player_id)
    if int(row.get("level") or 0) < 1:
        row.update({"level": 1, "confidence": max(25, int(row.get("confidence") or 0)), "source": source})
    row["first_seen"] = row.get("first_seen") or game_date.isoformat()
    row["updated_on"] = row.get("updated_on") or game_date.isoformat()
    return row




def _norm_country(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(ch for ch in text if not unicodedata.combining(ch)).strip()


_EUROPE = {_norm_country(x) for x in (
    "España","Portugal","Francia","Italia","Inglaterra","Escocia","Bélgica","Países Bajos","Alemania",
    "Grecia","Turquía","Rusia","Austria","Suiza","Dinamarca","Suecia","Noruega","Finlandia","Irlanda",
    "Polonia","Chequia","Eslovaquia","Hungría","Rumanía","Bulgaria","Croacia","Serbia","Eslovenia","Ucrania",
)}


def scouting_geography(home_country: str | None, target_country: str | None) -> dict[str, Any]:
    home = _norm_country(home_country); target = _norm_country(target_country)
    if home and target and home == target:
        return {"scope": "domestic", "scope_label": "Mercado nacional", "travel_days": 0}
    if home in _EUROPE and target in _EUROPE:
        return {"scope": "europe", "scope_label": "Desplazamiento europeo", "travel_days": 2}
    if not target:
        return {"scope": "unknown", "scope_label": "Ubicación por confirmar", "travel_days": 2}
    return {"scope": "long_distance", "scope_label": "Desplazamiento de larga distancia", "travel_days": 5}


def knowledge_at_date(row: dict[str, Any], game_date: date) -> dict[str, Any]:
    result = dict(row)
    updated = result.get("updated_on")
    if not updated:
        result.update({"age_days": None, "stale": False, "freshness": "Sin informe"})
        return result
    try:
        age = max(0, (game_date - date.fromisoformat(str(updated))).days)
    except ValueError:
        age = 0
    level = max(0, min(4, int(result.get("level") or 0)))
    confidence = max(0, min(100, int(result.get("confidence") or 0)))
    # Reports age rather than disappearing. After a month confidence slowly
    # erodes; after several months a once-deep dossier no longer behaves like
    # live omniscience. A new report restores it.
    if age > 30:
        confidence = max(20 if level else 0, confidence - (age - 30) // 4)
    effective_level = level
    if age >= 240 and effective_level >= 3:
        effective_level -= 1
    if age >= 420 and effective_level >= 3:
        effective_level -= 1
    result.update({
        "level": effective_level, "stored_level": level, "confidence": confidence, "age_days": age,
        "stale": age >= 75,
        "freshness": "Actual" if age < 30 else "Envejeciendo" if age < 75 else "Desactualizado" if age < 180 else "Antiguo",
    })
    return result

def start_scouting(
    state: dict[str, Any], *, player_id: int, game_date: date, effectiveness: dict[str, Any], player_name: str,
    capacity: int = 1, geography: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_scouting_state(state)
    pid = int(player_id)
    active = [task for task in state["scouting_assignments"].values() if task.get("status") == "active"]
    for task in active:
        if int(task.get("player_id") or 0) == pid:
            raise ValueError("ya hay un informe de scouting en curso para este jugador")
    capacity = max(1, int(capacity))
    if len(active) >= capacity:
        raise ValueError(f"capacidad de scouting completa ({len(active)}/{capacity}); espera un informe o redistribuye responsabilidades")
    knowledge = register_reference(state, player_id=pid, game_date=game_date, source="scouting_assignment")
    quality = max(1, min(20, int(effectiveness.get("quality") or 10)))
    current = int(knowledge.get("level") or 1)
    # A first proper report takes roughly one week. Deep knowledge takes a bit
    # longer and a strong specialist can cut several days, never to instant.
    base_days = 9 if current < 3 else 11
    geography = dict(geography or {"scope": "unknown", "scope_label": "Ubicación por confirmar", "travel_days": 2})
    travel_days = max(0, min(8, int(geography.get("travel_days") or 0)))
    days = max(3, base_days - max(0, quality - 8) // 3 + travel_days)
    task_id = str(uuid4())
    task = {
        "id": task_id, "player_id": pid, "player_name": str(player_name),
        "status": "active", "started_on": game_date.isoformat(),
        "due_on": (game_date + timedelta(days=days)).isoformat(), "days": days,
        "target_level": 3 if current < 3 else 4,
        "responsible": str(effectiveness.get("assignee_name") or "Cuerpo técnico"),
        "responsible_role": str(effectiveness.get("assignee_role") or "Responsable de scouting"),
        "quality_at_start": quality,
        "scope": str(geography.get("scope") or "unknown"),
        "scope_label": str(geography.get("scope_label") or "Ubicación por confirmar"),
        "travel_days": travel_days,
        "capacity_at_start": capacity,
    }
    state["scouting_assignments"][task_id] = task
    return dict(task)


def process_scouting_day(
    state: dict[str, Any], *, game_date: date, effectiveness: dict[str, Any], player_lookup: Callable[[int], dict[str, Any] | None]
) -> list[dict[str, Any]]:
    ensure_scouting_state(state)
    events: list[dict[str, Any]] = []
    for task in state["scouting_assignments"].values():
        if task.get("status") != "active" or date.fromisoformat(str(task["due_on"])) > game_date:
            continue
        pid = int(task["player_id"])
        quality = max(1, min(20, int(task.get("quality_at_start") or effectiveness.get("quality") or 10)))
        player = player_lookup(pid)
        if player is None:
            task.update({"status": "cancelled", "completed_on": game_date.isoformat(), "reason": "player_unavailable"})
            continue
        row = _entry(state, pid)
        target = max(int(row.get("level") or 1), int(task.get("target_level") or 3))
        confidence = max(int(row.get("confidence") or 0), min(96, 42 + quality * 3 + (8 if target >= 4 else 0)))
        row.update({
            "level": target, "confidence": confidence, "updated_on": game_date.isoformat(),
            "reports": int(row.get("reports") or 0) + 1, "source": "scout_report",
            "observer": str(task.get("responsible") or effectiveness.get("assignee_name") or "Cuerpo técnico"),
        })
        task.update({"status": "completed", "completed_on": game_date.isoformat(), "result_level": target, "confidence": confidence})
        events.append({
            "kind": "scouting_report_ready", "date": game_date.isoformat(), "player_id": pid,
            "player_name": str(player.get("display_name") or player.get("name") or task.get("player_name") or pid),
            "knowledge_level": target, "confidence": confidence, "responsible": row["observer"],
        })
    return events


def scouting_snapshot(state: dict[str, Any], *, game_date: date | None = None, capacity: int | None = None) -> dict[str, Any]:
    ensure_scouting_state(state)
    active = [dict(row) for row in state["scouting_assignments"].values() if row.get("status") == "active"]
    completed = [dict(row) for row in state["scouting_assignments"].values() if row.get("status") == "completed"]
    active.sort(key=lambda row: str(row.get("due_on") or ""))
    completed.sort(key=lambda row: str(row.get("completed_on") or ""), reverse=True)
    cap = max(1, int(capacity or 1))
    knowledge_rows = []
    if game_date is not None:
        for row in state["scouting_knowledge"].values():
            if int(row.get("level") or 0) <= 0:
                continue
            knowledge_rows.append(knowledge_at_date(row, game_date))
    return {
        "schema": SCOUTING_SCHEMA_9394, "active": active, "recent_reports": completed[:12],
        "capacity": cap, "used_capacity": len(active), "available_capacity": max(0, cap - len(active)),
        "known_players": len(knowledge_rows),
        "stale_reports": sum(1 for row in knowledge_rows if row.get("stale")),
    }


def _truth_overall(api: dict[str, Any]) -> int:
    return int(api.get("overall") or 60)


def _stable_error(*, state: dict[str, Any], player_id: int, level: int, spread: int) -> int:
    rng = Random(int(state.get("seed") or 9394) ^ int(player_id) * 65537 ^ int(level) * 997)
    return rng.randint(-spread, spread)


def _range(center: int, radius: int, lo: int = 1, hi: int = 100) -> list[int]:
    return [max(lo, center - radius), min(hi, center + radius)]


def _attribute_report(attributes: dict[str, Any]) -> tuple[list[str], list[str]]:
    rows = []
    for key, value in attributes.items():
        try: rows.append((int(value), key))
        except (TypeError, ValueError): continue
    rows.sort(reverse=True)
    strengths = [f"Destaca por {_ATTRIBUTE_LABELS.get(key, key.replace('_', ' '))}" for value, key in rows[:3] if value >= 68]
    weaknesses = [f"Ofrece dudas en {_ATTRIBUTE_LABELS.get(key, key.replace('_', ' '))}" for value, key in sorted(rows)[:2] if value <= 58]
    return strengths, weaknesses


def external_player_view(
    state: dict[str, Any], *, api: dict[str, Any], player_id: int, game_date: date, effectiveness: dict[str, Any]
) -> dict[str, Any]:
    """Redact canonical data according to persistent scouting knowledge."""
    pid = int(player_id)
    stored_knowledge = register_reference(state, player_id=pid, game_date=game_date)
    knowledge = knowledge_at_date(stored_knowledge, game_date)
    level = max(1, min(4, int(knowledge.get("level") or 1)))
    confidence = max(int(knowledge.get("confidence") or 0), 25 if level == 1 else 40)
    true_overall = _truth_overall(api)
    staff_quality = max(1, min(20, int(effectiveness.get("quality") or 10)))
    spread = {1: 9, 2: 7, 3: 3, 4: 0}[level]
    error = 0 if level == 4 else _stable_error(state=state, player_id=pid, level=level, spread=max(1, spread // 2))
    estimated = max(40, min(99, true_overall + error))
    overall_range = _range(estimated, spread, 35, 99)
    true_value = int(api.get("estimated_transfer_value") or (api.get("market") or {}).get("market_value") or 0)
    value_radius = {1: .42, 2: .30, 3: .14, 4: 0.0}[level]
    value_error_pct = 0 if level == 4 else _stable_error(state=state, player_id=pid + 17011, level=level, spread={1:22,2:14,3:6,4:0}[level])
    value_estimate = max(0, round(true_value * (1 + value_error_pct / 100.0))) if true_value else 0
    value_range = [max(0, round(value_estimate * (1 - value_radius))), round(value_estimate * (1 + value_radius))] if true_value else [0, 0]
    attrs = dict(api.get("attributes") or {})
    visible_attrs: dict[str, Any] = {}
    attr_ranges: dict[str, list[int]] = {}
    if level >= 4:
        visible_attrs = attrs
    elif level >= 3:
        radius = 3 if staff_quality >= 14 else 5
        for key, value in attrs.items():
            try:
                v = int(value)
            except (TypeError, ValueError):
                continue
            attr_ranges[key] = _range(v + _stable_error(state=state, player_id=pid + sum(map(ord, key)), level=level, spread=2), radius)
    elif level >= 2:
        for key, value in attrs.items():
            try: v = int(value)
            except (TypeError, ValueError): continue
            if v >= 72:
                attr_ranges[key] = _range(v + _stable_error(state=state, player_id=pid + sum(map(ord, key)), level=level, spread=4), 7)
    strengths, weaknesses = _attribute_report(attrs) if level >= 3 else ([], [])
    result = dict(api)
    result["overall"] = true_overall if level >= 4 else estimated
    result["overall_is_exact"] = level >= 4
    result["overall_range"] = overall_range
    result["overall_estimate"] = true_overall if level >= 4 else estimated if level >= 2 else None
    result["attributes"] = visible_attrs
    result["attribute_ranges"] = attr_ranges
    result["estimated_transfer_value"] = true_value if level >= 4 else value_estimate
    result["transfer_value_is_exact"] = level >= 4
    market = dict(result.get("market") or {})
    market["market_value"] = true_value if level >= 4 else value_estimate
    market["value_range"] = value_range
    market["value_is_exact"] = level >= 4
    salary_hint = int(market.get("minimum_salary_hint") or 0)
    if level < 4 and salary_hint:
        salary_error = _stable_error(state=state, player_id=pid + 27011, level=level, spread={1:20,2:12,3:5,4:0}[level])
        market["minimum_salary_hint"] = max(0, round(salary_hint * (1 + salary_error / 100.0)))
        market["salary_hint_is_exact"] = False
    result["market"] = market
    contract = dict(result.get("contract") or {})
    if level < 4:
        salary = int(contract.get("salary") or 0)
        if salary:
            salary_error = _stable_error(state=state, player_id=pid + 37011, level=level, spread={1:24,2:14,3:6,4:0}[level])
            salary_estimate = max(0, round(salary * (1 + salary_error / 100.0)))
            contract["salary"] = salary_estimate
            contract["salary_display"] = f"≈ {salary_estimate:,} ptas.".replace(",", ".")
            contract["salary_is_exact"] = False
        contract.pop("release_clause_display", None)
    result["contract"] = contract
    if level < 3:
        result["tactical_fit"] = {"label": "Por evaluar", "score": None, "reasons": []}
        result["squad_dynamics"] = {"role": None, "satisfaction": None, "wants_move": bool((result.get("market") or {}).get("wants_move"))}
        result["medical"] = {"status": (result.get("medical") or {}).get("status", "Sin información suficiente"), "injury_days": result.get("injury_days", 0), "current_injury": (result.get("medical") or {}).get("current_injury"), "history": []}
    result["scout"] = {
        "level": level, "knowledge": LEVEL_LABELS[level], "confidence": f"{confidence}%",
        "confidence_value": confidence, "updated_on": knowledge.get("updated_on"),
        "age_days": knowledge.get("age_days"), "stale": bool(knowledge.get("stale")), "freshness": knowledge.get("freshness"),
        "stored_level": knowledge.get("stored_level", level),
        "observer": knowledge.get("observer") or effectiveness.get("assignee_name"),
        "summary": (
            "Sólo disponemos de una referencia básica. Envía un ojeador para reducir la incertidumbre."
            if level == 1 else
            "Hay indicios útiles, pero todavía faltan observaciones para cerrar el perfil."
            if level == 2 else
            "El informe ya permite valorar el fichaje con una incertidumbre reducida."
            if level == 3 else
            "El cuerpo técnico considera que conoce el perfil con profundidad."
        ),
        "strengths": strengths, "weaknesses": weaknesses,
        "recommended_role": (api.get("identity") or {}).get("archetype") if level >= 3 else None,
        "tactical_fit": (api.get("tactical_fit") or {}).get("label") if level >= 3 else None,
        "overall_range": overall_range, "value_range": value_range,
    }
    return result
