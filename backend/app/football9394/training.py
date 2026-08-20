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

TRAINING_SCHEMA_9394 = 2

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

ROLE_FOCUS_SPECS = {
    "none": "Sin adaptación de puesto", "goalkeeper": "Portería", "defender": "Defensa", "fullback": "Lateral", "midfielder": "Mediocentro", "winger": "Banda", "attacker": "Ataque",
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
    root.setdefault("mode", "auto")
    root.setdefault("intensity", "normal")
    root.setdefault("weekly_plan", list(_DEFAULT_WEEK))
    root.setdefault("individual_focus", {})
    root.setdefault("individual_role_focus", {})
    root.setdefault("individual_focus_source", {})
    root.setdefault("individual_recovery", {})
    root.setdefault("match_preparation_focus", "balanced")
    root.setdefault("match_preparation_mode", "auto")
    root.setdefault("individual_recovery_source", {})
    root.setdefault("auto_decision", {})
    root.setdefault("history", [])
    root.setdefault("last_processed_on", None)
    plan = list(root.get("weekly_plan") or [])[:7]
    while len(plan) < 7:
        plan.append(_DEFAULT_WEEK[len(plan)])
    root["weekly_plan"] = [row if row in SESSION_SPECS else _DEFAULT_WEEK[i] for i, row in enumerate(plan)]
    if root.get("intensity") not in INTENSITY_SPECS:
        root["intensity"] = "normal"
    if root.get("mode") not in {"auto", "manual"}:
        root["mode"] = "auto"
    if root.get("match_preparation_mode") not in {"auto", "manual"}:
        root["match_preparation_mode"] = "auto"
    return root


def set_training_mode(state: dict[str, Any], mode: str) -> dict[str, Any]:
    root = ensure_training_state(state)
    key = str(mode or "auto")
    if key not in {"auto", "manual"}:
        raise ValueError("modo de entrenamiento no válido")
    root["mode"] = key
    return root


def set_training_plan(state: dict[str, Any], *, intensity: str | None = None, weekly_plan: list[str] | None = None, mode: str | None = None) -> dict[str, Any]:
    root = ensure_training_state(state)
    if mode is not None:
        set_training_mode(state, mode)
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
    if (intensity is not None or weekly_plan is not None) and str(mode or "") != "auto":
        root["mode"] = "manual"
    return root


def set_individual_focus(state: dict[str, Any], *, player_id: int, focus: str) -> dict[str, Any]:
    root = ensure_training_state(state)
    key = str(focus)
    if key not in FOCUS_SPECS:
        raise ValueError("foco individual no válido")
    pid = str(int(player_id))
    if key == "none":
        root["individual_focus"].pop(pid, None)
    else:
        root["individual_focus"][pid] = key
    root.setdefault("individual_focus_source", {})[pid] = "manual"
    return root

def set_individual_role_focus(state: dict[str, Any], *, player_id: int, role_focus: str) -> dict[str, Any]:
    root = ensure_training_state(state)
    key = str(role_focus)
    if key not in ROLE_FOCUS_SPECS:
        raise ValueError("adaptación de puesto no válida")
    pid = str(int(player_id))
    if key == "none": root["individual_role_focus"].pop(pid, None)
    else: root["individual_role_focus"][pid] = key
    return root


def set_individual_recovery(state: dict[str, Any], *, player_id: int, recovery: str) -> dict[str, Any]:
    root = ensure_training_state(state)
    key = str(recovery)
    if key not in RECOVERY_SPECS:
        raise ValueError("plan individual de recuperación no válido")
    pid = str(int(player_id))
    if key == "normal":
        root["individual_recovery"].pop(pid, None)
    else:
        root["individual_recovery"][pid] = key
    root.setdefault("individual_recovery_source", {})[pid] = "manual"
    return root


def set_match_preparation_focus(state: dict[str, Any], *, focus: str) -> dict[str, Any]:
    root = ensure_training_state(state)
    key = str(focus)
    if key == "auto":
        root["match_preparation_mode"] = "auto"
        return root
    if key not in MATCH_PREP_SPECS:
        raise ValueError("foco de preparación de partido no válido")
    root["match_preparation_focus"] = key
    root["match_preparation_mode"] = "manual"
    return root


def apply_auto_training_plan(
    state: dict[str, Any], *, game_date: date, players: list[dict[str, Any]],
    development: dict[str, dict[str, Any]], effectiveness: dict[str, Any],
    next_match_date: date | None = None, own_strength: float | None = None,
    opponent_strength: float | None = None, opposition_report_quality: int = 10,
) -> dict[str, Any]:
    """Let the staff run training/preparation while preserving manager tactics.

    This only controls workload, weekly sessions and match-preparation focus. It
    never changes formation, XI, squad selection or the manager's base tactics.
    """
    root = ensure_training_state(state)
    condition_values=[]; load_values=[]; high_risk=0
    for player in players:
        pid=str(int(player.get("source_id") or 0)); row=development.get(pid) or {}
        condition=max(0,min(100,int(row.get("condition") or 100)))
        load=max(0,min(100,int(row.get("training_load") or 0)))
        risk=_player_risk(player,row)
        condition_values.append(condition); load_values.append(load)
        if risk >= 52: high_risk += 1
        source=root.setdefault("individual_recovery_source",{}).get(pid)
        if source != "manual":
            if int(row.get("injury_days") or 0)>0 or risk>=70 or condition<=62:
                root["individual_recovery"][pid]="recovery"; root["individual_recovery_source"][pid]="auto"
            elif risk>=52 or condition<=74:
                root["individual_recovery"][pid]="reduced"; root["individual_recovery_source"][pid]="auto"
            else:
                root["individual_recovery"].pop(pid,None); root["individual_recovery_source"].pop(pid,None)
        focus_source=root.setdefault("individual_focus_source",{}).get(pid)
        if focus_source != "manual":
            position=str(player.get("position") or player.get("broad_position") or "").casefold()
            if any(token in position for token in ("portero","goalkeeper","gk")):
                auto_focus="goalkeeping"
            elif any(token in position for token in ("central","lateral","defensa","defender","libero")):
                auto_focus="defending"
            elif any(token in position for token in ("delantero","punta","forward","striker")):
                auto_focus="finishing"
            elif any(token in position for token in ("extremo","winger")):
                auto_focus="technique"
            elif any(token in position for token in ("medio","centrocampista","midfield")):
                auto_focus="passing"
            else:
                auto_focus="physical"
            root["individual_focus"][pid]=auto_focus
            root["individual_focus_source"][pid]="auto"
    avg_condition=round(sum(condition_values)/max(1,len(condition_values)))
    avg_load=round(sum(load_values)/max(1,len(load_values)))
    days_to_match=(next_match_date-game_date).days if next_match_date is not None else None
    quality=max(1,min(20,int(effectiveness.get("quality") or 10)))
    if root.get("mode") == "auto":
        if avg_condition < 76 or high_risk >= max(2, len(players)//8) or (days_to_match is not None and days_to_match <= 2):
            intensity="low"
        elif (days_to_match is None or days_to_match >= 5) and avg_condition >= 87 and avg_load < 34 and quality >= 12:
            intensity="high"
        else:
            intensity="normal"
        root["intensity"] = intensity
        plan=list(_DEFAULT_WEEK)
        # With a congested calendar the staff removes the heavy physical block.
        if days_to_match is not None and days_to_match <= 3:
            plan=["recovery","tactical","recovery","tactical","set_pieces","match_preparation","rest"]
        elif high_risk >= max(2, len(players)//7):
            plan=["recovery","tactical","physical","attack","set_pieces","match_preparation","rest"]
        root["weekly_plan"] = plan
    if root.get("match_preparation_mode") == "auto":
        own=float(own_strength or 0.0); opp=float(opponent_strength or 0.0)
        if own and opp and opp >= own + 3.0:
            focus="defensive"; rationale="El rival parte con más nivel: el staff prioriza bloque, coberturas y control de pérdidas."
        elif own and opp and own >= opp + 5.0:
            focus="attacking"; rationale="El staff ve una ventaja de nivel y prepara mecanismos para llevar el partido a campo rival."
        elif int(opposition_report_quality) >= 13:
            focus="opponent"; rationale="El informe del rival es suficientemente fiable para preparar amenazas y patrones concretos."
        else:
            focus="balanced"; rationale="La información del rival todavía no justifica desviar el microciclo del plan equilibrado."
        root["match_preparation_focus"] = focus
    else:
        rationale="Has fijado manualmente el foco del próximo partido; el staff mantiene esa excepción."
    root["auto_decision"]={
        "date":game_date.isoformat(), "training_mode":root.get("mode"),
        "match_preparation_mode":root.get("match_preparation_mode"),
        "intensity":root.get("intensity"), "average_condition":avg_condition, "average_load":avg_load,
        "high_risk_count":high_risk, "days_to_match":days_to_match,
        "preparation_focus":root.get("match_preparation_focus"), "rationale":rationale,
        "responsible":str(effectiveness.get("assignee_name") or "Cuerpo técnico"),
    }
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
        role_focus = str(root.get("individual_role_focus", {}).get(str(pid)) or "none")
        evidence = float(spec["development"]) * float(intensity_spec["dev_mult"]) * dev_quality * max(.15, float(recovery_spec["load_mult"]))
        _focus_evidence(row, focus, evidence)
        if role_focus != "none":
            familiarity = row.setdefault("role_familiarity", {})
            familiarity[role_focus] = min(100, round(float(familiarity.get(role_focus) or 0) + evidence * 3.5, 2))
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
        role_focus = str(root.get("individual_role_focus", {}).get(str(pid)) or "none")
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
            "focus_source": (root.get("individual_focus_source") or {}).get(str(pid)) or "auto",
            "role_focus": role_focus, "role_focus_label": ROLE_FOCUS_SPECS.get(role_focus, ROLE_FOCUS_SPECS["none"]),
            "role_familiarity": round(float((row.get("role_familiarity") or {}).get(role_focus) or 0), 1) if role_focus != "none" else None,
            "recovery": recovery, "recovery_label": RECOVERY_SPECS[recovery]["label"],
            "recovery_source": (root.get("individual_recovery_source") or {}).get(str(pid)) or "auto",
            "recommendation": _training_recommendation(injury_days=int(row.get("injury_days") or 0), condition=condition, load=load, risk=risk),
        })
    player_rows.sort(key=lambda item: (-int(item["risk"]), int(item["condition"]), item["name"]))
    week = [
        {"day_index": idx, "day": _DAY_LABELS[idx], "session": session, "label": SESSION_SPECS[session]["label"]}
        for idx, session in enumerate(root["weekly_plan"])
    ]
    delegated = str(effectiveness.get("source") or "") == "delegated_staff"
    responsibility_note = (
        f"{effectiveness.get('assignee_name') or 'El responsable'} ejecuta el plan con calidad "
        f"{effectiveness.get('quality_label') or 'operativa'}. Tus cambios aquí son instrucciones de trabajo y se aplican desde la siguiente sesión."
        if delegated else
        "Tú controlas directamente el entrenamiento. La carga de responsabilidades del mánager puede reducir la calidad efectiva si acumulas demasiadas tareas."
    )
    return {
        "schema": TRAINING_SCHEMA_9394,
        "mode": root.get("mode") or "auto", "mode_label": "Automático (staff)" if root.get("mode") == "auto" else "Manual",
        "mode_options": [{"key":"auto","label":"Automático (staff)"},{"key":"manual","label":"Manual"}],
        "intensity": root["intensity"], "intensity_label": INTENSITY_SPECS[root["intensity"]]["label"],
        "today": {"session": today, "label": SESSION_SPECS[today]["label"]},
        "weekly_plan": week,
        "session_options": [{"key": key, "label": value["label"]} for key, value in SESSION_SPECS.items()],
        "intensity_options": [{"key": key, "label": value["label"]} for key, value in INTENSITY_SPECS.items()],
        "focus_options": [{"key": key, "label": value["label"]} for key, value in FOCUS_SPECS.items()],
        "role_focus_options": [{"key": key, "label": label} for key, label in ROLE_FOCUS_SPECS.items()],
        "recovery_options": [{"key": key, "label": value["label"]} for key, value in RECOVERY_SPECS.items()],
        "match_preparation_focus": root.get("match_preparation_focus") or "balanced",
        "match_preparation_focus_label": MATCH_PREP_SPECS.get(str(root.get("match_preparation_focus") or "balanced"), "Equilibrada"),
        "match_preparation_mode": root.get("match_preparation_mode") or "auto",
        "match_preparation_options": [{"key":"auto","label":"Automático (staff)"}] + [{"key": key, "label": label} for key, label in MATCH_PREP_SPECS.items()],
        "auto_decision": dict(root.get("auto_decision") or {}),
        "responsibility": dict(effectiveness),
        "responsibility_mode": "delegated" if delegated else "direct",
        "responsibility_note": responsibility_note,
        "players": player_rows,
        "high_risk_count": sum(1 for row in player_rows if int(row["risk"]) >= 52),
        "very_high_risk_count": sum(1 for row in player_rows if int(row["risk"]) >= 70),
        "average_load": round(sum(int(row["training_load"]) for row in player_rows) / max(1, len(player_rows))),
        "average_condition": round(sum(int(row["condition"]) for row in player_rows) / max(1, len(player_rows))),
        "recent_sessions": list(root.get("history") or [])[-10:][::-1],
    }
