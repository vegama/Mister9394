from __future__ import annotations

"""NF4 tactical plan: phase behaviours, player jobs and familiarity.

The career keeps the compact 1993-94 engine vocabulary, but exposes a richer
football plan around it.  The plan is persistent and every option is translated
into an engine-visible behaviour rather than being cosmetic UI metadata.
"""

from datetime import date
from typing import Any, Iterable

TACTICAL_PLAN_SCHEMA_9394 = 1

BUILD_UP = {
    "patient": {"label": "Salida paciente", "directness": "short", "tempo": "slow"},
    "balanced": {"label": "Salida equilibrada", "directness": "mixed", "tempo": "normal"},
    "early": {"label": "Progresar pronto", "directness": "direct", "tempo": "high"},
}
FINAL_THIRD = {
    "mixed": "Variar el último pase",
    "crosses": "Cargar el área y centrar",
    "through": "Buscar pase entre líneas",
}
TRANSITION = {
    "hold": "Asegurar tras recuperar",
    "balanced": "Transición equilibrada",
    "counter": "Contraatacar al recuperar",
}
DUTIES = {"hold": "Guardar posición", "support": "Apoyar", "attack": "Llegar más"}
FREEDOM = {"disciplined": "Más disciplinado", "balanced": "Libertad normal", "expressive": "Más libertad"}
PLAYER_PRESS = {"low": "Presionar menos", "normal": "Presión normal", "high": "Presionar más"}
RECOVERY = {"normal": "Carga normal", "reduced": "Carga reducida", "recovery": "Recuperación", "rest": "Descanso individual"}


def ensure_tactical_plan_state(state: dict[str, Any]) -> dict[str, Any]:
    root = state.setdefault("tactical_plan", {})
    root.setdefault("schema", TACTICAL_PLAN_SCHEMA_9394)
    root.setdefault("build_up", "balanced")
    root.setdefault("final_third", "mixed")
    root.setdefault("transition", "balanced")
    root.setdefault("individual_instructions", {})
    root.setdefault("opposition_instructions", {})
    root.setdefault("set_piece_takers", {})
    root.setdefault("familiarity", {"overall": 62.0, "shape": 64.0, "possession": 61.0, "pressing": 61.0, "set_pieces": 58.0})
    root.setdefault("last_changed_on", None)
    root.setdefault("history", [])
    if root.get("build_up") not in BUILD_UP:
        root["build_up"] = "balanced"
    if root.get("final_third") not in FINAL_THIRD:
        root["final_third"] = "mixed"
    if root.get("transition") not in TRANSITION:
        root["transition"] = "balanced"
    return root


def _validate_player_instruction(payload: dict[str, Any]) -> dict[str, str]:
    duty = str(payload.get("duty") or "support")
    freedom = str(payload.get("freedom") or "balanced")
    pressing = str(payload.get("pressing") or "normal")
    if duty not in DUTIES:
        raise ValueError("función individual no válida")
    if freedom not in FREEDOM:
        raise ValueError("libertad individual no válida")
    if pressing not in PLAYER_PRESS:
        raise ValueError("presión individual no válida")
    return {"duty": duty, "freedom": freedom, "pressing": pressing}


def set_tactical_plan(
    state: dict[str, Any], *, build_up: str | None = None, final_third: str | None = None,
    transition: str | None = None, game_date: date | None = None,
) -> dict[str, Any]:
    root = ensure_tactical_plan_state(state)
    changed = False
    for key, value, allowed in (
        ("build_up", build_up, BUILD_UP), ("final_third", final_third, FINAL_THIRD), ("transition", transition, TRANSITION),
    ):
        if value is None:
            continue
        value = str(value)
        if value not in allowed:
            raise ValueError(f"{key}: instrucción táctica no válida")
        if root.get(key) != value:
            root[key] = value
            changed = True
    if changed:
        fam = root["familiarity"]
        # Tactical changes should matter, but not wipe out months of collective work.
        fam["overall"] = max(35.0, float(fam.get("overall") or 60.0) - 4.0)
        if build_up is not None:
            fam["possession"] = max(35.0, float(fam.get("possession") or 60.0) - 6.0)
        if transition is not None:
            fam["pressing"] = max(35.0, float(fam.get("pressing") or 60.0) - 3.0)
        root["last_changed_on"] = (game_date or date.today()).isoformat()
        root["history"].append({"date": root["last_changed_on"], "kind": "phase_plan_changed", "build_up": root["build_up"], "final_third": root["final_third"], "transition": root["transition"]})
        root["history"] = root["history"][-60:]
    return root


def set_individual_instruction(state: dict[str, Any], *, player_id: int, payload: dict[str, Any], game_date: date | None = None) -> dict[str, Any]:
    root = ensure_tactical_plan_state(state)
    pid = str(int(player_id))
    if payload.get("clear"):
        root["individual_instructions"].pop(pid, None)
    else:
        root["individual_instructions"][pid] = _validate_player_instruction(payload)
    root["last_changed_on"] = (game_date or date.today()).isoformat()
    root["familiarity"]["shape"] = max(35.0, float(root["familiarity"].get("shape") or 60.0) - 1.5)
    return root


def set_opposition_instruction(state: dict[str, Any], *, player_id: int, tight_mark: bool = False, press: bool = False, show_foot: str = "none") -> dict[str, Any]:
    root = ensure_tactical_plan_state(state)
    foot = str(show_foot or "none")
    if foot not in {"none", "left", "right"}:
        raise ValueError("pie de orientación no válido")
    pid = str(int(player_id))
    if not tight_mark and not press and foot == "none":
        root["opposition_instructions"].pop(pid, None)
    else:
        root["opposition_instructions"][pid] = {"tight_mark": bool(tight_mark), "press": bool(press), "show_foot": foot}
    return root


def set_piece_taker(state: dict[str, Any], *, kind: str, player_id: int | None) -> dict[str, Any]:
    root = ensure_tactical_plan_state(state)
    key = str(kind)
    if key not in {"corners", "free_kicks", "penalties"}:
        raise ValueError("tipo de lanzador no válido")
    if player_id is None:
        root["set_piece_takers"].pop(key, None)
    else:
        root["set_piece_takers"][key] = str(int(player_id))
    return root


def process_familiarity_day(state: dict[str, Any], *, training_session: str, training_quality: int, match_played: bool = False) -> dict[str, Any]:
    root = ensure_tactical_plan_state(state)
    fam = root["familiarity"]
    quality = max(1, min(20, int(training_quality)))
    q = .70 + quality / 40.0
    gains = {"overall": .06, "shape": .04, "possession": .02, "pressing": .02, "set_pieces": .01}
    if training_session in {"tactical", "match_preparation"}:
        gains.update({"overall": .24, "shape": .30, "possession": .20, "pressing": .20})
    elif training_session == "attack":
        gains.update({"overall": .12, "possession": .22})
    elif training_session == "defence":
        gains.update({"overall": .12, "pressing": .22, "shape": .16})
    elif training_session == "set_pieces":
        gains.update({"overall": .10, "set_pieces": .42})
    elif training_session == "rest":
        gains = {key: 0.0 for key in gains}
    if match_played:
        gains["overall"] += .30
        gains["shape"] += .20
        gains["possession"] += .12
        gains["pressing"] += .12
    for key, gain in gains.items():
        fam[key] = round(min(100.0, max(0.0, float(fam.get(key) or 60.0) + gain * q)), 2)
    return fam


def reset_opposition_instructions(state: dict[str, Any]) -> None:
    ensure_tactical_plan_state(state)["opposition_instructions"] = {}


def familiarity_label(value: float) -> str:
    n = float(value)
    if n >= 88:
        return "Automatizado"
    if n >= 75:
        return "Familiar"
    if n >= 60:
        return "Asimilando"
    if n >= 45:
        return "En aprendizaje"
    return "Poco trabajado"


def tactical_plan_snapshot(state: dict[str, Any], *, players: Iterable[dict[str, Any]] = (), opponent_players: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    root = ensure_tactical_plan_state(state)
    by_id = {int(p.get("source_id") or 0): p for p in players}
    opp_by_id = {int(p.get("source_id") or 0): p for p in opponent_players}
    individual = []
    for pid_text, row in root["individual_instructions"].items():
        pid = int(pid_text)
        p = by_id.get(pid)
        if p:
            individual.append({"player_id": pid, "name": p.get("display_name") or p.get("name"), **row,
                               "duty_label": DUTIES[row["duty"]], "freedom_label": FREEDOM[row["freedom"]], "pressing_label": PLAYER_PRESS[row["pressing"]]})
    opposition = []
    for pid_text, row in root["opposition_instructions"].items():
        pid = int(pid_text)
        p = opp_by_id.get(pid)
        opposition.append({"player_id": pid, "name": (p or {}).get("display_name") or (p or {}).get("name") or f"Jugador {pid}", **row})
    fam = {key: round(float(value), 1) for key, value in root["familiarity"].items()}
    return {
        "schema": TACTICAL_PLAN_SCHEMA_9394,
        "build_up": root["build_up"], "build_up_label": BUILD_UP[root["build_up"]]["label"],
        "final_third": root["final_third"], "final_third_label": FINAL_THIRD[root["final_third"]],
        "transition": root["transition"], "transition_label": TRANSITION[root["transition"]],
        "build_up_options": [{"key": k, "label": v["label"]} for k, v in BUILD_UP.items()],
        "final_third_options": [{"key": k, "label": v} for k, v in FINAL_THIRD.items()],
        "transition_options": [{"key": k, "label": v} for k, v in TRANSITION.items()],
        "duty_options": [{"key": k, "label": v} for k, v in DUTIES.items()],
        "freedom_options": [{"key": k, "label": v} for k, v in FREEDOM.items()],
        "player_press_options": [{"key": k, "label": v} for k, v in PLAYER_PRESS.items()],
        "individual_instructions": individual, "opposition_instructions": opposition,
        "set_piece_takers": dict(root["set_piece_takers"]),
        "familiarity": {**fam, "label": familiarity_label(fam.get("overall", 0))},
        "last_changed_on": root.get("last_changed_on"),
    }


def engine_tactics_payload(base: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    root = ensure_tactical_plan_state(state)
    payload = dict(base)
    payload["build_up"] = root["build_up"]
    payload["final_third"] = root["final_third"]
    payload["transition"] = root["transition"]
    return payload
