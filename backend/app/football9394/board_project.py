from __future__ import annotations

"""NF10 · Board expectations and football-project construction.

The board only exposes decisions that alter football: competitive target,
squad/wage envelope, staff capacity, transfer resources and pressure to sell.
"""

from datetime import date, timedelta
from typing import Any


def _clip(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, round(float(value))))


def _season_key(date_text: str) -> str:
    current = date.fromisoformat(date_text)
    start = current.year if current.month >= 7 else current.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def _objective(expected_position: int, team_count: int) -> str:
    expected_position = max(1, int(expected_position))
    if expected_position <= max(2, round(team_count * .15)):
        return "Luchar por el título"
    if expected_position <= max(5, round(team_count * .35)):
        return "Clasificarse en la zona alta"
    if expected_position >= max(14, round(team_count * .75)):
        return "Mantener la categoría"
    return "Consolidarse en la categoría"


def _philosophy(team: dict[str, Any], club_score: float) -> list[dict[str, Any]]:
    members = int(team.get("members") or 0)
    rows = [
        {"key": "competitive", "label": "Competir según la dimensión del club", "weight": 5},
        {"key": "financial", "label": "No comprometer la estabilidad por un fichaje", "weight": 4},
    ]
    if club_score < 48:
        rows.append({"key": "value", "label": "Revalorizar plantilla y vender con sentido deportivo", "weight": 4})
    elif club_score >= 78:
        rows.append({"key": "ambition", "label": "Mantener una plantilla capaz de luchar por objetivos altos", "weight": 4})
    if members >= 35_000:
        rows.append({"key": "identity", "label": "Proteger la identidad competitiva ante la afición", "weight": 3})
    return rows


def ensure_board_project(state: dict[str, Any], *, team: dict[str, Any], club_score: float, expected_position: int, team_count: int, squad_size: int, staff_size: int, economy: dict[str, Any], date_text: str) -> None:
    projects = state.setdefault("board_projects", {})
    key = str(int(team.get("source_id") or state.get("team_id") or 0))
    existing = projects.get(key)
    season_key = _season_key(date_text)
    expected_position = max(1, int(expected_position))
    objective = _objective(expected_position, team_count)
    annual_wages = int(economy.get("annual_wages") or 0)
    if existing:
        existing.setdefault("requests", [])
        existing.setdefault("decisions", [])
        existing.setdefault("project_history", [])
        existing.setdefault("budget_adjustment", 0)
        existing.setdefault("max_staff_size", max(staff_size, 5))
        existing.setdefault("sale_pressure", None)
        existing.setdefault("season_key", season_key)
        if str(existing.get("season_key")) != season_key:
            existing["project_history"].append({
                "season": existing.get("season_key"), "objective": existing.get("objective"),
                "expected_position": existing.get("expected_position"), "support": existing.get("support"),
                "wage_ceiling": existing.get("wage_ceiling"), "closed_on": date_text,
            })
            existing["project_history"] = existing["project_history"][-12:]
            existing.update({
                "season_key": season_key, "objective": objective, "expected_position": expected_position,
                "team_count": int(team_count), "wage_ceiling": max(annual_wages, round(annual_wages * (1.08 if club_score >= 65 else 1.03))),
                "preferred_squad_size": max(18, min(24, int(squad_size) if squad_size >= 18 else 21)),
                "budget_adjustment": 0, "last_review_on": date_text,
            })
        return
    wage_ceiling = max(annual_wages, round(annual_wages * (1.08 if club_score >= 65 else 1.03)))
    projects[key] = {
        "team_id": int(team.get("source_id") or 0), "started_on": date_text, "season_key": season_key, "objective": objective,
        "expected_position": expected_position, "team_count": int(team_count), "philosophy": _philosophy(team, club_score),
        "wage_ceiling": wage_ceiling, "max_staff_size": max(int(staff_size), 5 + (1 if club_score >= 70 else 0)),
        "preferred_squad_size": max(18, min(24, int(squad_size) if squad_size >= 18 else 21)),
        "budget_adjustment": 0, "requests": [], "decisions": [], "project_history": [], "sale_pressure": None,
        "support": 55, "last_review_on": date_text,
    }


def update_board_project(*, state: dict[str, Any], team_id: int, board: dict[str, Any], economy: dict[str, Any], squad_size: int, staff_size: int, date_text: str) -> dict[str, Any]:
    project = state.setdefault("board_projects", {}).setdefault(str(int(team_id)), {"team_id": int(team_id), "requests": [], "decisions": []})
    board_score = int(board.get("score") or 50)
    projected = int(economy.get("projected_monthly_net") or 0)
    cash = int(economy.get("cash") or 0)
    reserve = int(economy.get("safety_reserve") or 0)
    debt = int(economy.get("debt") or 0)
    support = board_score
    if projected < 0:
        support -= min(12, abs(projected) / max(1, reserve) * 8)
    if squad_size < 18:
        support -= 8
    project["support"] = _clip(support)
    project["last_review_on"] = date_text
    project["current_staff_size"] = int(staff_size)
    project["current_squad_size"] = int(squad_size)
    project["current_annual_wages"] = int(economy.get("annual_wages") or 0)
    project["transfer_room"] = int(economy.get("transfer_room") or 0)

    # A sale request is a consequence of sustained financial stress, never a
    # random board message. It is cleared automatically once the hole is closed.
    pressure = project.get("sale_pressure")
    severe = cash < max(0, round(reserve * .35)) or (debt > max(cash, 1) * 2.2 and projected < 0)
    if severe and not pressure:
        required = max(1_000_000, reserve - cash, abs(projected) * 3)
        project["sale_pressure"] = {
            "created_on": date_text, "required_income": int(required), "remaining": int(required),
            "deadline": (date.fromisoformat(date_text) + timedelta(days=60)).isoformat(),
            "reason": "La estructura financiera obliga al consejo a pedir una venta antes de ampliar el gasto.",
            "status": "active",
        }
    elif pressure and pressure.get("status") == "active":
        recovered = cash >= reserve or projected >= 0
        if recovered or int(pressure.get("remaining") or 0) <= 0:
            pressure["status"] = "resolved"
            pressure["resolved_on"] = date_text
    return project


def register_sale_income(state: dict[str, Any], *, team_id: int, amount: int, date_text: str) -> dict[str, Any] | None:
    project = (state.get("board_projects") or {}).get(str(int(team_id)))
    if not project:
        return None
    pressure = project.get("sale_pressure")
    if not pressure or pressure.get("status") != "active":
        return None
    pressure["remaining"] = max(0, int(pressure.get("remaining") or 0) - max(0, int(amount)))
    if pressure["remaining"] == 0:
        pressure["status"] = "resolved"
        pressure["resolved_on"] = date_text
    return dict(pressure)


def submit_board_request(*, state: dict[str, Any], team_id: int, request_type: str, date_text: str, board_score: int, economy: dict[str, Any]) -> dict[str, Any]:
    project = (state.get("board_projects") or {}).get(str(int(team_id)))
    if project is None:
        raise KeyError("proyecto del consejo no inicializado")
    request_type = str(request_type)
    if request_type not in {"extra_transfer_budget", "expand_staff", "delay_sale_pressure"}:
        raise ValueError("petición al consejo no válida")
    serial = len(project.setdefault("requests", [])) + 1
    season_key = _season_key(date_text)
    request = {"id": f"board-request:{team_id}:{date_text}:{serial}", "date": date_text, "season": season_key, "type": request_type, "status": "rejected"}
    same_season_accepted = next((row for row in reversed(project.get("requests") or []) if row.get("type") == request_type and row.get("status") == "accepted" and row.get("season") == season_key), None)
    if same_season_accepted and request_type in {"extra_transfer_budget", "expand_staff"}:
        request["reason"] = "El consejo ya aprobó esta ampliación durante la temporada actual; el proyecto debe absorberla antes de volver a revisarla."
        project["requests"].append(request)
        project["requests"] = project["requests"][-40:]
        return dict(request)
    pressure = project.get("sale_pressure") or {}
    if request_type == "delay_sale_pressure" and pressure.get("extension_granted"):
        request["reason"] = "El consejo ya concedió una prórroga para esta misma necesidad de venta."
        project["requests"].append(request)
        project["requests"] = project["requests"][-40:]
        return dict(request)
    support = int(project.get("support") or board_score or 50)
    projected = int(economy.get("projected_monthly_net") or 0)
    cash = int(economy.get("cash") or 0)
    reserve = int(economy.get("safety_reserve") or 0)
    if request_type == "extra_transfer_budget":
        accepted = support >= 68 and projected >= 0 and cash >= reserve
        amount = max(1_000_000, round(max(cash, reserve) * .08)) if accepted else 0
        request.update({"status": "accepted" if accepted else "rejected", "amount": int(amount), "reason": "El consejo premia la estabilidad y amplía el margen." if accepted else "El consejo no ampliará gasto mientras el margen sea limitado."})
        if accepted:
            project["budget_adjustment"] = int(project.get("budget_adjustment") or 0) + amount
    elif request_type == "expand_staff":
        accepted = support >= 62 and projected >= 0
        request.update({"status": "accepted" if accepted else "rejected", "slots": 1 if accepted else 0, "reason": "Se autoriza una plaza adicional de staff." if accepted else "La estructura actual debe demostrar más rendimiento antes de crecer."})
        if accepted:
            project["max_staff_size"] = int(project.get("max_staff_size") or 5) + 1
    else:
        pressure = project.get("sale_pressure") or {}
        accepted = pressure.get("status") == "active" and support >= 72 and cash > 0
        request.update({"status": "accepted" if accepted else "rejected", "days": 30 if accepted else 0, "reason": "El consejo concede tiempo adicional por tu respaldo actual." if accepted else "La necesidad financiera pesa más que el respaldo deportivo."})
        if accepted:
            deadline = date.fromisoformat(str(pressure["deadline"]))
            pressure["deadline"] = (deadline + timedelta(days=30)).isoformat()
            pressure["extension_granted"] = True
    request["football_consequence"] = {
        "extra_transfer_budget": "Aumenta el margen para una incorporación, pero también el compromiso del proyecto.",
        "expand_staff": "Amplía la capacidad operativa del club para scouting, entrenamiento o área médica.",
        "delay_sale_pressure": "Compra tiempo para resolver la presión financiera sin eliminar la obligación.",
    }[request_type] if request.get("status") == "accepted" else "El proyecto mantiene sus límites actuales y la decisión queda registrada para la próxima revisión."
    project["requests"].append(request)
    project["requests"] = project["requests"][-40:]
    return dict(request)


def project_snapshot(state: dict[str, Any], team_id: int) -> dict[str, Any]:
    row = dict((state.get("board_projects") or {}).get(str(int(team_id))) or {})
    row["requests"] = [dict(x) for x in row.get("requests") or []][-12:]
    row["decisions"] = [dict(x) for x in row.get("decisions") or []][-12:]
    row["project_history"] = [dict(x) for x in row.get("project_history") or []][-12:]
    return row
