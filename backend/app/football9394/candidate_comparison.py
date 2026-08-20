from __future__ import annotations

"""Comparación A/B/C de candidatos, con el conocimiento que se tiene de cada uno.

El plan de profundidad la pide dos veces —en NF1, para cerrar el ojeo, y en NF2,
enlazada al plan de plantilla— y no existía en ninguno de los dos. Es la pieza
que cierra el bucle del ojeo: sin ella el usuario tiene tres informes sueltos y
ninguna forma de ponerlos uno al lado del otro, que es exactamente el momento en
que se decide un fichaje.

La regla que la gobierna es la misma que rige todo NF1: **no se compara la verdad
del simulador, se compara lo que el club sabe.** Un jugador con informe fiable se
enseña con su rango estrecho; uno del que sólo hay una referencia de oídas se
enseña con un rango ancho y confianza baja, y eso mismo es información útil —a
veces la mejor decisión es no fichar al que menos se conoce, aunque su
estimación central sea la más alta—.

Por eso el veredicto nunca dice "éste es mejor". Dice qué dice cada informe, cuánto
se fía el club de cada uno, en qué se diferencian y qué haría falta saber para
decidir con menos riesgo.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

# Cuánto se ensancha la horquilla cuando el conocimiento es pobre. Son puntos de
# media sobre 100: con un informe fiable el club acierta casi, con una referencia
# de oídas puede errar por diez.
# Los niveles son los de ``scouting.effective_knowledge``: 0 sin conocimiento,
# 4 conocimiento profundo. No se define aqui otra escala para no tener dos
# verdades sobre lo mismo.
UNCERTAINTY_BY_LEVEL = {0: 14, 1: 10, 2: 6, 3: 3, 4: 1}

LEVEL_LABELS = {
    0: "Sin datos",
    1: "Referencia de oídas",
    2: "Observado",
    3: "Informe fiable",
    4: "Conocimiento profundo",
}

# Un informe viejo vale menos aunque en su día fuera bueno.
STALE_AFTER_DAYS = 120


@dataclass(frozen=True, slots=True)
class CandidateView:
    """Lo que el club cree saber de un candidato, no lo que el motor sabe."""

    player_id: int
    display_name: str
    broad_position: str | None
    age: int | None
    club: str | None
    knowledge: int
    confidence: int
    estimate: int
    low: int
    high: int
    report_age_days: int | None
    stale: bool
    scout: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "player_id": self.player_id,
            "display_name": self.display_name,
            "broad_position": self.broad_position,
            "age": self.age,
            "club": self.club,
            "knowledge": self.knowledge,
            "knowledge_label": LEVEL_LABELS.get(self.knowledge, "?"),
            "confidence": self.confidence,
            "estimate": self.estimate,
            "range": {"low": self.low, "high": self.high},
            "report_age_days": self.report_age_days,
            "stale": self.stale,
            "scout": self.scout,
        }


def _as_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _report_age(report: dict[str, Any], today: date) -> int | None:
    raw = str(report.get("updated_on") or report.get("reported_on") or "")[:10]
    if not raw:
        return None
    try:
        year, month, day = (int(part) for part in raw.split("-"))
    except ValueError:
        return None
    return max(0, (today - date(year, month, day)).days)


def build_view(player: dict[str, Any], knowledge: dict[str, Any] | None, *, today: date) -> CandidateView:
    """Traduce el conocimiento del club en una lectura comparable.

    ``player`` debe ser la representación de mercado del jugador, no su fila
    cruda del universo. La diferencia no es formal: la ficha cruda lleva la media
    real del simulador y el mercado lleva la que el club cree. Al usar la cruda,
    Dubovský aparecia con 74 cuando el club solo podia estimar 71, y la
    comparacion se convertia en una filtracion.

    De ahi que se prefiera ``overall_range`` y el bloque ``scout`` si vienen: son
    la horquilla y el conocimiento que el propio mercado ya calcula, y tener dos
    formas distintas de decir lo mismo acabaria en dos verdades distintas.
    """
    # El bloque de ojeo de la representacion de mercado manda sobre el que se
    # pase suelto: ya incorpora el conocimiento estructural de la red del club,
    # que ``effective_knowledge`` por si sola no ve. Usando el suelto, un jugador
    # con seguimiento inicial y ojeador asignado salia como "Sin datos".
    report = dict(knowledge or {})
    scout = player.get("scout")
    if isinstance(scout, dict):
        for key in ("level", "stored_level", "age_days", "stale", "observer", "updated_on"):
            if scout.get(key) is not None:
                report[key] = scout[key]
        if scout.get("confidence_value") is not None:
            report["confidence"] = scout["confidence_value"]
    level = max(0, min(4, _as_int(report.get("level"), 0)))
    spread = UNCERTAINTY_BY_LEVEL[level]
    age_days = report.get("age_days")
    age_days = _as_int(age_days) if age_days is not None else _report_age(report, today)
    stale = bool(report.get("stale")) or (age_days is not None and age_days > STALE_AFTER_DAYS)
    if stale:
        # Un informe caducado no se descarta: se ensancha, que es lo que de
        # verdad le pasa al conocimiento cuando pasa el tiempo.
        spread += 4

    rango = player.get("overall_range")
    if isinstance(rango, (list, tuple)) and len(rango) == 2:
        low, high = _as_int(rango[0], 1), _as_int(rango[1], 99)
        estimate = round((low + high) / 2)
    else:
        estimate = _as_int(report.get("estimated_overall") or player.get("overall"), 60)
        low, high = estimate - spread, estimate + spread
    confidence = _as_int(report.get("confidence"), 25 if level == 0 else 60)
    if stale:
        confidence = max(5, confidence - 20)
        low, high = low - 2, high + 2

    return CandidateView(
        player_id=_as_int(player.get("source_id") or player.get("id")),
        display_name=str(player.get("display_name") or player.get("name") or "?"),
        broad_position=player.get("broad_position"),
        age=_as_int(player.get("age"), 0) or None,
        club=player.get("team_name") or player.get("club"),
        knowledge=level,
        confidence=max(0, min(100, confidence)),
        estimate=max(1, min(99, estimate)),
        low=max(1, min(99, low)),
        high=max(1, min(99, high)),
        report_age_days=age_days,
        stale=stale,
        scout=report.get("observer") or report.get("scout"),
    )


def _overlap(a: CandidateView, b: CandidateView) -> bool:
    return not (a.high < b.low or b.high < a.low)


def compare(views: Iterable[CandidateView]) -> dict[str, Any]:
    """Pone los candidatos uno al lado del otro sin decidir por el usuario.

    Deliberadamente no devuelve un ganador. Cuando dos horquillas se solapan, el
    club **no sabe** cuál es mejor, y decir lo contrario seria inventar una
    precision que el ojeo no tiene. Lo que si se puede decir es de quien se sabe
    mas y a quien habria que seguir observando.
    """
    rows = sorted(views, key=lambda v: (-v.estimate, -v.confidence, v.display_name))
    if not rows:
        return {"candidates": [], "verdict": "No hay candidatos que comparar.", "actions": []}

    best = rows[0]
    tied = [row for row in rows[1:] if _overlap(best, row)]
    weakest = min(rows, key=lambda v: (v.confidence, -v.high - v.low))

    if len(rows) == 1:
        verdict = (f"Sólo hay un candidato en la comparación: {best.display_name}, "
                   f"con {LEVEL_LABELS.get(best.knowledge, best.knowledge).lower()}.")
    elif tied:
        nombres = ", ".join(row.display_name for row in [best, *tied])
        verdict = (f"Con lo que el club sabe hoy no se puede separar a {nombres}: "
                   "sus horquillas se solapan.")
    else:
        verdict = (f"{best.display_name} destaca sobre el resto incluso tomando el peor caso "
                   f"de su horquilla ({best.low}) frente al mejor de los demás.")

    actions: list[dict[str, Any]] = []
    for row in rows:
        if row.knowledge <= 1:
            actions.append({"player_id": row.player_id, "action": "scout",
                            "reason": f"apenas hay información de {row.display_name}: "
                                      f"la horquilla va de {row.low} a {row.high}"})
        elif row.stale:
            actions.append({"player_id": row.player_id, "action": "rescout",
                            "reason": f"el informe de {row.display_name} tiene "
                                      f"{row.report_age_days} días y ha perdido precisión"})
    if tied and not actions:
        actions.append({"player_id": weakest.player_id, "action": "scout",
                        "reason": f"observar a {weakest.display_name} es lo que más "
                                  "estrecharía la comparación"})

    return {
        "candidates": [row.as_dict() for row in rows],
        "verdict": verdict,
        "undecidable": bool(tied),
        "best_known": best.player_id,
        "least_known": weakest.player_id,
        "actions": actions,
        "policy": ("se comparan informes, no la verdad del simulador: dos horquillas que se "
                   "solapan significan que el club todavía no sabe cuál es mejor"),
    }
