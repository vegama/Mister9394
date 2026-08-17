from __future__ import annotations

"""Board confidence and manager-risk model for the persistent 1993-94 career.

The board never judges from a single result.  Confidence is decomposed into
sporting trajectory, short-term form and financial stewardship so every change
can be explained to the player.
"""

from typing import Any


def _clip(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, round(value)))


def confidence_label(score: int) -> str:
    if score >= 82: return "Excelente"
    if score >= 68: return "Alta"
    if score >= 50: return "Estable"
    if score >= 34: return "En vigilancia"
    if score >= 18: return "Bajo presión"
    return "Crítica"


def risk_label(score: int) -> str:
    if score >= 68: return "SEGURO"
    if score >= 50: return "ESTABLE"
    if score >= 34: return "VIGILANCIA"
    if score >= 18: return "RIESGO"
    return "RIESGO ALTO"


def evaluate_board(
    *, expectation: dict[str, Any], position: int | None, played: int,
    recent_form: list[str], projected_monthly_net: int, cash: int, debt: int,
    previous_score: int | None = None,
) -> dict[str, Any]:
    expected = int(expectation.get("expected_position") or max(1, position or 1))
    actual = int(position or expected)
    table_size = max(2, int(expectation.get("team_count") or 20))
    position_delta = expected - actual

    # Position matters progressively as the season advances.  In September a
    # three-place swing is noise; in spring it is a real signal.
    progress = min(1.0, max(.12, played / max(1, (table_size - 1) * 2)))
    sporting = 50 + position_delta * (3.0 + 4.0 * progress)

    form_points = sum(3 if r == "V" else 1 if r == "E" else 0 for r in recent_form)
    form_max = max(1, len(recent_form) * 3)
    form = 50 if not recent_form else 25 + 55 * form_points / form_max

    economy = 55.0
    reasons: list[dict[str, Any]] = []
    if projected_monthly_net >= 0:
        economy += 10
        reasons.append({"kind":"economy","impact":8,"text":"La gestión mensual mantiene el club en equilibrio."})
    else:
        scale = min(25, abs(projected_monthly_net) / max(1, cash + abs(projected_monthly_net)) * 40)
        economy -= scale
        reasons.append({"kind":"economy","impact":-round(scale),"text":"La proyección mensual es negativa y reduce el margen del club."})
    if debt > max(1, cash) * 1.5:
        economy -= 8
        reasons.append({"kind":"debt","impact":-8,"text":"La deuda pesa mucho respecto a la caja disponible."})

    if position_delta >= 3:
        reasons.insert(0,{"kind":"sporting","impact":min(24,position_delta*4),"text":f"El equipo marcha {position_delta} puestos por encima de la expectativa."})
    elif position_delta > 0:
        reasons.insert(0,{"kind":"sporting","impact":position_delta*3,"text":"La clasificación está por encima del objetivo previsto."})
    elif position_delta <= -4:
        reasons.insert(0,{"kind":"sporting","impact":max(-28,position_delta*4),"text":f"El equipo está {abs(position_delta)} puestos por debajo de la expectativa."})
    elif position_delta < 0:
        reasons.insert(0,{"kind":"sporting","impact":position_delta*3,"text":"La clasificación está algo por debajo del objetivo."})
    else:
        reasons.insert(0,{"kind":"sporting","impact":2,"text":"El equipo está exactamente donde el consejo esperaba."})

    if recent_form:
        if form_points >= max(8, form_max * .72):
            reasons.append({"kind":"form","impact":8,"text":"La dinámica reciente refuerza la confianza."})
        elif form_points <= max(2, form_max * .28):
            reasons.append({"kind":"form","impact":-9,"text":"La mala racha reciente preocupa al consejo."})

    raw = sporting * .62 + form * .23 + economy * .15
    # Confidence is intentionally inertial: one result cannot swing the job.
    score = _clip(raw if previous_score is None else previous_score * .35 + raw * .65)
    return {
        "score": score,
        "label": confidence_label(score),
        "risk": risk_label(score),
        "expected_position": expected,
        "actual_position": actual,
        "position_delta": position_delta,
        "played": int(played),
        "components": {"sporting": _clip(sporting), "form": _clip(form), "economy": _clip(economy)},
        "reasons": reasons[:5],
        "critical": score < 18 and played >= 10,
    }


def apply_board_review(state: dict[str, Any], review: dict[str, Any], *, date: str, trigger: str) -> dict[str, Any]:
    state.setdefault("board_history", [])
    state.setdefault("board_warning_count", 0)
    state.setdefault("job_status", "active")
    previous = state.get("board_state") or {}
    changed = int(previous.get("score") or -1) != int(review["score"])
    row = {**review, "date": date, "trigger": trigger}
    state["board_state"] = row
    if review.get("critical"):
        state["board_warning_count"] = int(state.get("board_warning_count") or 0) + 1
    elif int(review["score"]) >= 28:
        state["board_warning_count"] = 0
    # Dismissal is possible, but only after two separate critical reviews and
    # at least twelve league matches. This avoids arbitrary three-game firings.
    if review.get("critical") and int(review.get("played") or 0) >= 12 and int(state["board_warning_count"]) >= 2:
        state["job_status"] = "dismissed"
        row["dismissed"] = True
    if changed or trigger in {"season_start", "season_end", "monthly"}:
        state["board_history"].append(row)
        state["board_history"] = state["board_history"][-80:]
    return row
