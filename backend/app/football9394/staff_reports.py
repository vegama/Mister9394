from __future__ import annotations

"""NF5 staff interpretations: actionable opinions, not omniscient truth."""

from datetime import date
from typing import Any, Callable


def _confidence(quality: int) -> tuple[int, str]:
    score = max(35, min(96, 42 + int(quality) * 3))
    return score, "Alta" if score >= 82 else "Media" if score >= 64 else "Limitada"


def build_staff_reports(
    *, game_date: date, effects: Callable[[str], dict[str, Any]], training: dict[str, Any], scouting: dict[str, Any],
    squad_plan: dict[str, Any], dressing_room: dict[str, Any], negotiations: list[dict[str, Any]],
    squad: list[dict[str, Any]], tactical_plan: dict[str, Any], next_match: dict[str, Any] | None,
) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []

    def add(key: str, area: str, title: str, detail: str, *, urgency: str = "normal", action: str = "home", evidence: str = "") -> None:
        effect = effects(key)
        q = int(effect.get("quality") or 10)
        conf, conf_label = _confidence(q)
        reports.append({
            "id": f"{game_date.isoformat()}:{key}:{len(reports)}", "area": area, "title": title, "detail": detail,
            "urgency": urgency, "action": action, "evidence": evidence,
            "author": effect.get("assignee_name") or "Tú (mánager)", "role": effect.get("assignee_role") or "Mánager",
            "quality": q, "quality_label": effect.get("quality_label") or "Decisión directa",
            "confidence": conf, "confidence_label": conf_label,
        })

    risky = [p for p in training.get("players") or [] if int(p.get("risk") or 0) >= 52]
    if risky:
        names = ", ".join(p["name"] for p in risky[:3])
        add("medical_assessment", "Salud", f"{len(risky)} jugadores con carga de riesgo", f"Conviene reducir carga a {names}{'…' if len(risky)>3 else ''}.", urgency="high" if any(int(p.get("risk") or 0)>=70 for p in risky) else "normal", action="training", evidence="Carga, condición y antecedentes recientes")
    else:
        add("medical_assessment", "Salud", "Sin alertas físicas graves", "La plantilla puede mantener el microciclo previsto, con vigilancia normal.", action="training", evidence="Condición y carga del primer equipo")

    priorities = list(squad_plan.get("priorities") or [])
    if priorities:
        top = priorities[0]
        add("recruitment_search", "Plantilla", f"Prioridad: {top.get('label') or top.get('slot')}", str(top.get("reason") or top.get("detail") or "La cobertura de plantilla merece seguimiento."), urgency="high" if int(top.get("severity") or 0)>=70 else "normal", action="market", evidence="Cobertura por puesto, contratos y sucesión")

    active = list(scouting.get("active") or [])
    recent = list(scouting.get("recent_reports") or [])
    add("recruitment_search", "Scouting", f"{len(active)} informes en curso · {len(recent)} recientes", "La precisión depende de la profundidad y antigüedad de cada dossier.", action="market", evidence="Capacidad, desplazamiento y frescura de informes")

    tensions = [p for p in squad if bool((p.get("squad_dynamics") or {}).get("wants_move")) or int((p.get("squad_dynamics") or {}).get("satisfaction") or 70) < 45]
    if tensions:
        names = ", ".join(str(p.get("display_name")) for p in tensions[:3])
        add("match_preparation", "Vestuario", f"Hay {len(tensions)} focos de tensión", f"{names} necesitan una decisión futbolística clara: minutos, rol, contrato o salida.", urgency="high", action="squad", evidence="Satisfacción, rol prometido y relación con el mánager")
    else:
        add("match_preparation", "Vestuario", "Jerarquía estable", "No detecto un conflicto que requiera intervención inmediata.", action="squad", evidence="Liderazgo, satisfacción y promesas")

    fam = tactical_plan.get("familiarity") or {}
    if float(fam.get("overall") or 0) < 70:
        add("first_team_training", "Táctica", f"Familiaridad {fam.get('label','en desarrollo')}", "El equipo todavía perderá algo de precisión al ejecutar el plan; las sesiones tácticas y los partidos la consolidan.", action="tactics", evidence="Familiaridad de estructura, posesión, presión y balón parado")
    elif next_match:
        add("opposition_reports", "Partido", "Plan suficientemente asimilado", "Puedes preparar ajustes específicos del rival sin rehacer la estructura base.", action="tactics", evidence="Plan del equipo y próximo rival")

    pending = [n for n in negotiations if n.get("status") in {"waiting", "countered"}]
    if pending:
        add("transfer_negotiation", "Mercado", f"{len(pending)} negociación{'es' if len(pending)!=1 else ''} abierta{'s' if len(pending)!=1 else ''}", "No todas requieren subir la oferta: revisa interés del jugador, competencia y coste de oportunidad.", urgency="high" if any(n.get("status")=="countered" for n in pending) else "normal", action="market", evidence="Estado de negociación, agente y alternativas")

    reports.sort(key=lambda r: ({"high": 0, "normal": 1, "low": 2}.get(r["urgency"], 1), r["area"], r["title"]))
    return {"date": game_date.isoformat(), "reports": reports[:12], "urgent_count": sum(1 for r in reports if r["urgency"] == "high")}
