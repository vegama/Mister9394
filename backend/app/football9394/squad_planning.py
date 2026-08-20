from __future__ import annotations

"""NF2 compact first-team planning derived from the same squad logic used by AI."""

from typing import Any

from .career_ai import squad_audit
from .career_economy import effective_contract
from .position_roles import role_for_player

_SLOT_LABELS = {
    "GK":"Portería", "RB":"Lateral derecho", "LB":"Lateral izquierdo", "CB":"Central",
    "DM":"Mediocentro defensivo", "CM":"Mediocentro", "RM":"Banda derecha", "LM":"Banda izquierda",
    "AM":"Mediapunta", "RW":"Extremo derecho", "LW":"Extremo izquierdo", "ST":"Delantera", "DEPTH":"Profundidad general",
}

_MARKET_POSITIONS = {
    "GK":"POR", "RB":"LD", "LB":"LI", "CB":"CB", "DM":"MCD", "CM":"MC",
    "RM":"MD", "LM":"MI", "AM":"MP", "RW":"ED", "LW":"EI", "ST":"DC", "DEPTH":"",
}


def squad_plan_snapshot(
    *, players: list[dict[str, Any]], development: dict[str, dict[str, Any]], contract_overrides: dict[str, dict[str, Any]], current_year: int,
    decisions: dict[str, str] | None = None,
) -> dict[str, Any]:
    decisions = decisions or {}
    audit = squad_audit(players, development)
    priorities: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for need in audit.get("needs") or []:
        shortage = int(need.get("shortage") or 0)
        average = float(need.get("average") or 0)
        slot = str(need.get("slot") or "DEPTH")
        score = shortage * 40 + max(0, 70 - round(average))
        base_row = {
            "slot": slot, "label": _SLOT_LABELS.get(slot, slot), "shortage": shortage,
            "count": int(need.get("count") or 0), "minimum": int(need.get("minimum") or 0),
            "average": average, "priority_score": score, "market_position": _MARKET_POSITIONS.get(slot, ""),
        }
        coverage.append({**base_row, "status": "Déficit" if shortage else "Mejorable" if average < 66 else "Cubierto"})
        if shortage <= 0 and average >= 66:
            continue
        priorities.append({
            **base_row,
            "priority": "Urgente" if shortage >= 1 else "Mejorable",
            "action": "Buscar incorporación" if shortage else "Buscar competencia",
        })
    if int(audit.get("depth_shortage") or 0) > 0:
        priorities.insert(0, {
            "slot":"DEPTH", "label":"Profundidad general", "shortage":int(audit["depth_shortage"]),
            "count":int(audit.get("squad_size") or 0), "minimum":int(audit.get("minimum_squad_size") or 0),
            "average":0.0, "priority_score":100 + int(audit["depth_shortage"]) * 10,
            "priority":"Urgente", "action":"Ampliar plantilla", "market_position":"",
        })
    priorities.sort(key=lambda row: (-int(row["priority_score"]), row["label"]))
    coverage.sort(key=lambda row: (0 if row["status"] == "Déficit" else 1 if row["status"] == "Mejorable" else 2, -int(row["priority_score"]), row["label"]))
    if not priorities and coverage:
        weakest = coverage[0]
        priorities.append({**weakest, "priority": "Estable", "action": "Mantener seguimiento"})


    expiring=[]; succession=[]; surplus=[]
    counts=dict(audit.get("counts") or {})
    for player in players:
        pid=int(player["source_id"])
        overall=int((development.get(str(pid)) or {}).get("overall") or player.get("overall") or player.get("category") or 60)
        contract=effective_contract(player, overall=overall, override=contract_overrides.get(str(pid)))
        slot=role_for_player(player).squad_slot
        row={
            "player_id":pid, "name":str(player.get("display_name") or player.get("name") or pid), "slot":slot,
            "slot_label":_SLOT_LABELS.get(slot,slot), "overall":overall, "contract_end_year":int(contract.get("end_year") or 0),
            "decision":str(decisions.get(str(pid)) or "seguimiento"),
        }
        if int(contract.get("end_year") or 9999) <= int(current_year) + 1:
            expiring.append({**row,"reason":"Contrato próximo a terminar","action":"Renovar o preparar sustituto"})
        if overall >= 72 and int(contract.get("end_year") or 9999) <= int(current_year) + 2:
            succession.append({**row,"reason":"Pieza importante con horizonte contractual corto","action":"Proteger continuidad"})
        minimum=next((int(n.get("minimum") or 0) for n in audit.get("needs") or [] if str(n.get("slot"))==slot),0)
        if int(counts.get(slot) or 0) >= minimum + 2 and overall < 63:
            surplus.append({**row,"reason":"Exceso de efectivos en su demarcación","action":"Valorar salida"})
    expiring.sort(key=lambda row:(row["contract_end_year"],-row["overall"]))
    succession.sort(key=lambda row:(row["contract_end_year"],-row["overall"]))
    surplus.sort(key=lambda row:(row["overall"],row["name"]))
    return {
        "squad_size":int(audit.get("squad_size") or 0), "minimum_squad_size":int(audit.get("minimum_squad_size") or 0),
        "target_squad_size":int(audit.get("target_squad_size") or 0), "coverage_ok":bool(audit.get("coverage_ok")),
        "primary_need":audit.get("primary_need") or (priorities[0]["slot"] if priorities else None), "priorities":priorities[:8], "coverage":coverage, "expiring":expiring[:10],
        "succession":succession[:8], "surplus":surplus[:8],
        "decisions": {str(k): str(v) for k, v in decisions.items() if any(int(p.get("source_id") or 0) == int(k) for p in players)},
        "decision_options": [{"key":"seguimiento","label":"Seguimiento"},{"key":"renovar","label":"Renovar"},{"key":"vender","label":"Vender"},{"key":"ceder","label":"Ceder"},{"key":"sustituto","label":"Buscar sustituto"},{"key":"desarrollar","label":"Desarrollar"}],
    }
