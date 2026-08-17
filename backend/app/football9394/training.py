from __future__ import annotations

"""NF3 training, workload and injury-risk layer for Míster 93/94.

The goal is deliberately compact: a weekly plan must create meaningful trade-offs
without turning the game into a session-calendar spreadsheet.  The persistent
player-development row remains the canonical place for condition/fatigue; this
module owns the club plan, individual focus and the daily training pulse.
"""

from datetime import date
from random import Random
from typing import Any, Callable

from .medical import register_match_injury

TRAINING_SCHEMA_9394 = 1

SESSION_SPECS: dict[str, dict[str, Any]] = {
    "recovery": {"label": "Recuperación", "load": 2, "condition": 2, "development": 0.0},
    "physical": {"label": "Físico", "load": 12, "condition": -3, "development": 0.025},
    "tactical": {"label": "Táctica", "load": 7, "condition": -1, "development": 0.018},
    "attack": {"label": "Ataque", "load": 8, "condition": -1, "development": 0.020},
    "defence": {"label": "Defensa", "load": 8, "condition": -1, "development": 0.020},
    "set_pieces": {"label": "Balón parado", "load": 6, "condition": 0, "development": 0.015},
    "match_preparation": {"label": "Preparación de partido", "load": 5, "condition": 0, "development": 0.012},
    "rest": {"label": "Descanso", "load": 0, "condition": 3, "development": 0.0},
}

INTENSITY_SPECS: dict[str, dict[str, Any]] = {
    "low": {"label": "Baja", "load_mult": 0.72, "dev_mult": 0.75},
    "normal": {"label": "Normal", "load_mult": 1.0, "dev_mult": 1.0},
    "high": {"label": "Alta", "load_mult": 1.28, "dev_mult": 1.17},
}

FOCUS_SPECS: dict[str, dict[str, Any]] = {
    "none": {"label": "Sin foco individual", "attributes": ()},
    "physical": {"label": "Físico", "attributes": ("stamina", "strength", "acceleration")},
    "technique": {"label": "Técnica", "attributes": ("technique", "dribbling")},
    "passing": {"label": "Pase y visión", "attributes": ("short_pass", "long_pass", "vision")},
    "finishing": {"label": "Finalización", "attributes": ("finishing", "off_ball", "shot_power")},
    "defending": {"label": "Defensa", "attributes": ("tackling", "marking", "positioning")},
    "goalkeeping": {"label": "Portería", "attributes": ("goalkeeping", "reflexes", "positioning")},
}

RECOVERY_SPECS: dict[str, dict[str, Any]] = {
    "normal": {"label": "Carga normal", "load_mult": 1.0, "condition_bonus": 0},
    "reduced": {"label": "Carga reducida", "load_mult": 0.62, "condition_bonus": 1},
    "recovery": {"label": "Recuperación", "load_mult": 0.28, "condition_bonus": 2},
    "rest": {"label": "Descanso individual", "load_mult": 0.0, "condition_bonus": 3},
}

MATCH_PREP_SPECS: dict[str, str] = {
    "balanced": "Equilibrada", "opponent": "Específica del rival", "attacking": "Ataque", "defensive": "Defensa", "set_pieces": "Balón parado",
}

# Monday..Sunday. It is intentionally a sensible football default rather than a
# historical claim about any specific club's exact 1993 microcycle.
_DEFAULT_WEEK = ["recovery", "physical", "tactical", "attack", "set_pieces", "match_preparation", "rest"]
_DAY_LABELS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def ensure_training_state(state: dict[str, Any]) -> dict[str, Any]:
    root = state.setdefault("training", {})
    root.setdefault("schema", TRAINING_SCHEMA_9394)
    root.setdefault("intensity", "normal")
    root.setdefault("weekly_plan", list(_DEFAULT_WEEK))
    root.setdefault("individual_focus", {})
    root.setdefault("individual_recovery", {})
    root.setdefault("match_preparation_focus", "balanced")
    root.setdefault("history", [])
    root.setdefault("last_processed_on", None)
    plan = list(root.get("weekly_plan") or [])[:7]
    while len(plan) < 7:
        plan.append(_DEFAULT_WEEK[len(plan)])
    root["weekly_plan"] = [row if row in SESSION_SPECS else _DEFAULT_WEEK[i] for i, row in enumerate(plan)]
    if root.get("intensity") not in INTENSITY_SPECS:
        root["intensity"] = "normal"
    return root


def set_training_plan(state: dict[str, Any], *, intensity: str | None = None, weekly_plan: list[str] | None = None) -> dict[str, Any]:
    root = ensure_training_state(state)
    if intensity is not None:
        key = str(intensity)
        if key not in INTENSITY_SPECS:
            raise ValueError("intensidad de entrenamiento no válida")
        root["intensity"] = key
    if weekly_plan is not None:
        if len(weekly_plan) != 7:
            raise ValueError("el plan semanal debe contener exactamente siete días")
        cleaned = [str(row) for row in weekly_plan]
        invalid = [row for row in cleaned if row not in SESSION_SPECS]
        if invalid:
            raise ValueError(f"sesión de entrenamiento no válida: {invalid[0]}")
        root["weekly_plan"] = cleaned
    return root


def set_individual_focus(state: dict[str, Any], *, player_id: int, focus: str) -> dict[str, Any]:
    root = ensure_training_state(state)
    key = str(focus)
    if key not in FOCUS_SPECS:
        raise ValueError("foco individual no válido")
    if key == "none":
        root["individual_focus"].pop(str(int(player_id)), None)
    else:
        root["individual_focus"][str(int(player_id))] = key
    return root


def set_individual_recovery(state: dict[str, Any], *, player_id: int, recovery: str) -> dict[str, Any]:
    root = ensure_training_state(state)
    key = str(recovery)
    if key not in RECOVERY_SPECS:
        raise ValueError("plan individual de recuperación no válido")
    if key == "normal":
        root["individual_recovery"].pop(str(int(player_id)), None)
    else:
        root["individual_recovery"][str(int(player_id))] = key
    return root


def set_match_preparation_focus(state: dict[str, Any], *, focus: str) -> dict[str, Any]:
    root = ensure_training_state(state)
    key = str(focus)
    if key not in MATCH_PREP_SPECS:
        raise ValueError("foco de preparación de partido no válido")
    root["match_preparation_focus"] = key
    return root


def _risk_label(score: int) -> str:
    if score >= 70:
        return "Muy alto"
    if score >= 52:
        return "Alto"
    if score >= 34:
        return "Moderado"
    return "Bajo"


def _training_recommendation(*, injury_days: int, condition: int, load: int, risk: int) -> str:
    if injury_days > 0:
        return "Rehabilitación: no debe completar la carga normal del grupo."
    if risk >= 70 or condition <= 62:
        return "Reducir carga y priorizar recuperación."
    if risk >= 52 or load >= 48:
        return "Vigilar: conviene rebajar la siguiente sesión exigente."
    if condition <= 76:
        return "Carga controlada; evitar acumular trabajo físico intenso."
    return "Puede completar la carga prevista."


def _ensure_player_load(row: dict[str, Any]) -> None:
    row.setdefault("training_load", 0)
    row.setdefault("fatigue", 0)
    row.setdefault("injury_risk", 12)
    row.setdefault("last_training_session", None)


def _player_risk(player: dict[str, Any], row: dict[str, Any]) -> int:
    _ensure_player_load(row)
    proneness = max(0, min(3, int(player.get("injury_proneness") or 0)))
    condition = max(0, min(100, int(row.get("condition") or 100)))
    load = max(0, int(row.get("training_load") or 0))
    fatigue = max(0, int(row.get("fatigue") or 0))
    score = 10 + proneness * 9 + max(0, 82 - condition) * 0.75 + max(0, load - 28) * 0.65 + fatigue * 0.28
    if int(row.get("injury_days") or 0) > 0:
        score = max(score, 58)
    return max(5, min(92, round(score)))


def _focus_evidence(row: dict[str, Any], focus: str, amount: float) -> None:
    spec = FOCUS_SPECS.get(focus) or FOCUS_SPECS["none"]
    if not spec["attributes"] or amount <= 0:
        return
    points = row.setdefault("attribute_points", {})
    for key in spec["attributes"]:
        points[key] = round(float(points.get(key) or 0.0) + amount, 4)


def session_for_date(state: dict[str, Any], *, game_date: date, next_match_date: date | None = None) -> str:
    root = ensure_training_state(state)
    # A match tomorrow overrides the generic calendar with specific preparation;
    # a match today is treated as rest here because match load is applied by the
    # match-development system itself.
    if next_match_date is not None:
        delta = (next_match_date - game_date).days
        if delta == 0:
            return "rest"
        if delta == 1:
            return "match_preparation"
    return str(root["weekly_plan"][game_date.weekday()])


def process_training_day(
    state: dict[str, Any], *, game_date: date, players: list[dict[str, Any]], development: dict[str, dict[str, Any]],
    effectiveness: dict[str, Any], seed: int, next_match_date: date | None = None,
) -> list[dict[str, Any]]:
    root = ensure_training_state(state)
    if root.get("last_processed_on") == game_date.isoformat():
        return []
    session = session_for_date(state, game_date=game_date, next_match_date=next_match_date)
    spec = SESSION_SPECS[session]
    intensity = str(root.get("intensity") or "normal")
    intensity_spec = INTENSITY_SPECS[intensity]
    quality = max(1, min(20, int(effectiveness.get("quality") or 10)))
    # Better coaches extract a little more development for slightly less fatigue.
    efficiency = max(0.82, min(1.12, 1.04 - (quality - 10) * 0.012))
    dev_quality = max(0.72, min(1.30, 0.78 + quality * 0.026))
    events: list[dict[str, Any]] = []
    risk_rows: list[tuple[int, int]] = []

    for player in players:
        pid = int(player["source_id"])
        row = development.setdefault(str(pid), {})
        _ensure_player_load(row)
        injury_days = max(0, int(row.get("injury_days") or 0))
        if injury_days > 0:
            # Injured players follow rehab; they do not receive the normal team load.
            row["training_load"] = max(0, int(row.get("training_load") or 0) - 2)
            row["fatigue"] = max(0, int(row.get("fatigue") or 0) - 2)
            row["last_training_session"] = "rehab"
            risk = _player_risk(player, row)
            row["injury_risk"] = risk
            risk_rows.append((risk, pid))
            continue

        recovery = str(root.get("individual_recovery", {}).get(str(pid)) or "normal")
        recovery_spec = RECOVERY_SPECS.get(recovery) or RECOVERY_SPECS["normal"]
        load_add = round(float(spec["load"]) * float(intensity_spec["load_mult"]) * efficiency * float(recovery_spec["load_mult"]))
        condition_delta = int(spec["condition"]) + int(recovery_spec["condition_bonus"])
        if session not in {"rest", "recovery"}:
            condition_delta -= max(0, round((float(intensity_spec["load_mult"]) - 1.0) * 3))
        row["training_load"] = max(0, min(100, int(row.get("training_load") or 0) + load_add))
        row["fatigue"] = max(0, min(100, int(row.get("fatigue") or 0) + max(0, round(load_add * .55))))
        row["condition"] = max(0, min(100, int(row.get("condition") or 100) + condition_delta))
        row["last_training_session"] = session
        focus = str(root.get("individual_focus", {}).get(str(pid)) or "none")
        evidence = float(spec["development"]) * float(intensity_spec["dev_mult"]) * dev_quality * max(.15, float(recovery_spec["load_mult"]))
        _focus_evidence(row, focus, evidence)
        risk = _player_risk(player, row)
        row["injury_risk"] = risk
        risk_rows.append((risk, pid))

        # Training injuries are deliberately uncommon. Workload and proneness do
        # not guarantee one; they only tilt a small deterministic daily chance.
        exposure = 1.25 if session == "physical" else 1.0 if session in {"attack", "defence", "tactical"} else .55
        chance = max(0.00008, min(0.018, (0.0005 + max(0, risk - 24) * 0.00012) * exposure * float(intensity_spec["load_mult"]) * max(.18, float(recovery_spec["load_mult"]))))
        rng = Random(int(seed) ^ pid * 8191 ^ game_date.toordinal() * 131 ^ sum(map(ord, session)))
        if rng.random() < chance:
            injury = register_match_injury(row, player, seed=int(seed) + 700_000 + pid, game_date=game_date)
            injury["context"] = "training"
            row["current_injury"] = dict(injury)
            history = list(row.get("injury_history") or [])
            if history:
                history[-1] = {**history[-1], "context": "training"}
                row["injury_history"] = history[-30:]
            row["condition"] = min(int(row.get("condition") or 100), 48)
            events.append({
                "kind": "training_injury", "date": game_date.isoformat(), "player_id": pid,
                "player_name": str(player.get("display_name") or player.get("name") or pid),
                "injury": injury.get("name"), "expected_days": int(injury.get("expected_days") or 0),
                "session": spec["label"],
            })

    root["last_processed_on"] = game_date.isoformat()
    root.setdefault("history", []).append({
        "date": game_date.isoformat(), "session": session, "session_label": spec["label"],
        "intensity": intensity, "intensity_label": intensity_spec["label"],
        "responsible": str(effectiveness.get("assignee_name") or "Cuerpo técnico"),
        "quality": quality, "high_risk_count": sum(1 for risk, _ in risk_rows if risk >= 52),
        "injuries": len(events),
    })
    root["history"] = root["history"][-45:]
    return events


def training_snapshot(
    state: dict[str, Any], *, players: list[dict[str, Any]], development: dict[str, dict[str, Any]],
    effectiveness: dict[str, Any], game_date: date, next_match_date: date | None = None,
) -> dict[str, Any]:
    root = ensure_training_state(state)
    today = session_for_date(state, game_date=game_date, next_match_date=next_match_date)
    player_rows: list[dict[str, Any]] = []
    for player in players:
        pid = int(player["source_id"])
        row = development.setdefault(str(pid), {})
        _ensure_player_load(row)
        risk = _player_risk(player, row)
        row["injury_risk"] = risk
        focus = str(root.get("individual_focus", {}).get(str(pid)) or "none")
        recovery = str(root.get("individual_recovery", {}).get(str(pid)) or "normal")
        condition = max(0, min(100, int(row.get("condition") or 100)))
        load = max(0, min(100, int(row.get("training_load") or 0)))
        player_rows.append({
            "player_id": pid, "name": str(player.get("display_name") or player.get("name") or pid),
            "position": str(player.get("position") or player.get("broad_position") or "—"),
            "condition": condition, "training_load": load, "fatigue": max(0, int(row.get("fatigue") or 0)),
            "injury_days": max(0, int(row.get("injury_days") or 0)),
            "risk": risk, "risk_label": _risk_label(risk),
            "focus": focus, "focus_label": FOCUS_SPECS[focus]["label"],
            "recovery": recovery, "recovery_label": RECOVERY_SPECS[recovery]["label"],
            "recommendation": _training_recommendation(injury_days=int(row.get("injury_days") or 0), condition=condition, load=load, risk=risk),
        })
    player_rows.sort(key=lambda item: (-int(item["risk"]), int(item["condition"]), item["name"]))
    week = [
        {"day_index": idx, "day": _DAY_LABELS[idx], "session": session, "label": SESSION_SPECS[session]["label"]}
        for idx, session in enumerate(root["weekly_plan"])
    ]
    return {
        "schema": TRAINING_SCHEMA_9394,
        "intensity": root["intensity"], "intensity_label": INTENSITY_SPECS[root["intensity"]]["label"],
        "today": {"session": today, "label": SESSION_SPECS[today]["label"]},
        "weekly_plan": week,
        "session_options": [{"key": key, "label": value["label"]} for key, value in SESSION_SPECS.items()],
        "intensity_options": [{"key": key, "label": value["label"]} for key, value in INTENSITY_SPECS.items()],
        "focus_options": [{"key": key, "label": value["label"]} for key, value in FOCUS_SPECS.items()],
        "recovery_options": [{"key": key, "label": value["label"]} for key, value in RECOVERY_SPECS.items()],
        "match_preparation_focus": root.get("match_preparation_focus") or "balanced",
        "match_preparation_focus_label": MATCH_PREP_SPECS.get(str(root.get("match_preparation_focus") or "balanced"), "Equilibrada"),
        "match_preparation_options": [{"key": key, "label": label} for key, label in MATCH_PREP_SPECS.items()],
        "responsibility": dict(effectiveness),
        "players": player_rows,
        "high_risk_count": sum(1 for row in player_rows if int(row["risk"]) >= 52),
        "very_high_risk_count": sum(1 for row in player_rows if int(row["risk"]) >= 70),
        "average_load": round(sum(int(row["training_load"]) for row in player_rows) / max(1, len(player_rows))),
        "average_condition": round(sum(int(row["condition"]) for row in player_rows) / max(1, len(player_rows))),
        "recent_sessions": list(root.get("history") or [])[-10:][::-1],
    }
