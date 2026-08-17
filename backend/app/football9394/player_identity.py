from __future__ import annotations

"""Source-backed football identity for Míster 93/94.

The MDB already describes footballers with specialist roles, secondary-role
aptitudes, fine attributes and seven explicit hidden tendencies.  This module
turns those source values into explainable gameplay identity.  Labels are
presentation/gameplay interpretations; raw source values remain authoritative.
"""

from datetime import date, datetime
from hashlib import sha256
from typing import Any

from .position_roles import role_for_player

REFERENCE_DATE_9394 = date(1993, 10, 23)


def _num(player: dict[str, Any], key: str, fallback: int = 60) -> int:
    attrs = player.get("attributes") or {}
    raw = attrs.get(key, player.get(key))
    try:
        return max(1, min(100, int(round(float(raw)))))
    except (TypeError, ValueError):
        return fallback


def birth_date(player: dict[str, Any]) -> date | None:
    raw = player.get("birth_date")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        try:
            return date.fromisoformat(str(raw)[:10])
        except (TypeError, ValueError):
            return None


def age_on(player: dict[str, Any], on_date: date = REFERENCE_DATE_9394) -> int | None:
    born = birth_date(player)
    if born is not None:
        return on_date.year - born.year - ((on_date.month, on_date.day) < (born.month, born.day))
    # Some reconstructed 1993-94 squads expose a verified season age but not a
    # full date of birth.  Preserve that source-backed age instead of inventing
    # a January 1 birth date.  The product's canonical career mode freezes age,
    # so this value intentionally remains stable across later seasons.
    raw = player.get("historical_age_1993_94")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


_SOURCE_TRAITS = {
    "individualist": ("Individualista", "Busca resolver por sí mismo con mayor frecuencia.", "warning"),
    "killer_pass": ("Último pase", "Intenta pases que rompen líneas y generan ocasiones.", "positive"),
    "holds_ball": ("Conserva el balón", "Tiende a proteger la posesión antes de acelerar.", "neutral"),
    "long_shots": ("Tiro lejano", "Acepta más remates desde media distancia.", "positive"),
    "cuts_inside": ("Va hacia dentro", "Desde banda busca zonas interiores con frecuencia.", "neutral"),
    "first_time_play": ("Primer toque", "Acelera la circulación y finaliza de primeras.", "positive"),
    "dives": ("Piscinero", "Busca provocar faltas y penaltis; también aumenta el riesgo disciplinario.", "warning"),
}


def source_trait_api(player: dict[str, Any]) -> list[dict[str, str]]:
    raw = player.get("hidden_traits") or {}
    return [
        {"code": code, "label": label, "effect": effect, "polarity": polarity, "provenance": "mdb_source"}
        for code, (label, effect, polarity) in _SOURCE_TRAITS.items()
        if bool(raw.get(code))
    ]


def player_archetype(player: dict[str, Any]) -> tuple[str, str]:
    slot = role_for_player(player).squad_slot
    pace, stamina, strength = _num(player, "pace"), _num(player, "stamina"), _num(player, "strength")
    technique, short_pass, long_pass = _num(player, "technique"), _num(player, "short_pass"), _num(player, "long_pass")
    vision, dribbling = _num(player, "vision", technique), _num(player, "dribbling", technique)
    finishing, heading = _num(player, "finishing"), _num(player, "heading")
    tackling, marking, positioning = _num(player, "tackling"), _num(player, "marking"), _num(player, "positioning")
    aggression, anticipation = _num(player, "aggression"), _num(player, "anticipation")
    work_rate, off_ball = _num(player, "work_rate"), _num(player, "off_ball", positioning)

    def avg(*values: int) -> float:
        return sum(values) / len(values)

    if slot == "GK":
        if avg(long_pass, short_pass, technique) >= avg(positioning, anticipation, strength) - 2:
            return "Portero iniciador", "Puede iniciar juego y variar la salida desde portería."
        return "Portero de área", "Su valor principal está en colocación, mando y protección del área."
    if slot in {"RB", "LB"}:
        attack = avg(pace, stamina, dribbling, off_ball, short_pass)
        defend = avg(marking, tackling, positioning, strength, anticipation)
        if attack >= defend + 5:
            return "Lateral ofensivo", "Necesita campo para recorrer banda y acompañar los ataques."
        if defend >= attack + 6:
            return "Lateral marcador", "Destaca protegiendo su zona y en el duelo defensivo."
        return "Lateral completo", "Combina apoyo ofensivo, recorrido y responsabilidad defensiva."
    if slot == "CB":
        build = avg(long_pass, vision, technique, positioning, anticipation)
        duel = avg(tackling, marking, strength, aggression, heading)
        if build >= duel + 5:
            return "Líbero constructor", "Lee el juego e inicia ataques desde la última línea."
        if heading + strength >= 165:
            return "Central aéreo", "Gana peso defendiendo centros y atacando el balón parado."
        return "Central marcador", "Su impacto nace del duelo, la anticipación y la defensa del área."
    if slot == "DM":
        build = avg(vision, short_pass, long_pass, technique, positioning)
        recover = avg(tackling, work_rate, aggression, marking, stamina)
        return ("Organizador retrasado", "Da sentido a la primera posesión y cambia la orientación.") if build >= recover + 4 else ("Mediocentro recuperador", "Protege a los centrales y sostiene el trabajo defensivo.")
    if slot == "CM":
        create = avg(vision, short_pass, technique, long_pass)
        run = avg(stamina, work_rate, off_ball, pace, tackling)
        if run >= create + 5:
            return "Centrocampista todoterreno", "Aporta recorrido, ayudas y llegadas de área a área."
        if create >= run + 5:
            return "Organizador", "Necesita balón y compañeros que ataquen lo que él ve."
        return "Centrocampista mixto", "Combina circulación, trabajo y llegada."
    if slot == "AM":
        create = avg(vision, technique, short_pass, dribbling)
        score = avg(finishing, off_ball, technique, pace)
        return ("Segundo punta", "Ataca el área y busca terminar jugadas.") if score >= create + 5 else ("Mediapunta creador", "Encuentra el último pase entre líneas.")
    if slot in {"RM", "LM", "RW", "LW"}:
        vertical = avg(pace, dribbling, off_ball, stamina)
        create = avg(vision, short_pass, technique, long_pass)
        score = avg(finishing, off_ball, pace, technique)
        if score >= max(vertical, create) + 4:
            return "Extremo goleador", "Parte desde banda, pero su mayor peligro aparece atacando el área."
        if create >= vertical + 4:
            return "Extremo creador", "Genera ventajas con técnica, pase y recepción abierta."
        return "Extremo vertical", "Su amenaza principal es ganar metros y desbordar."
    target = avg(heading, strength, positioning, finishing)
    poacher = avg(finishing, off_ball, anticipation, pace)
    link = avg(technique, vision, short_pass, strength)
    if target >= max(poacher, link) + 4:
        return "Delantero referencia", "Fija centrales, disputa juego directo y ofrece amenaza aérea."
    if link >= max(poacher, target) + 4:
        return "Delantero asociativo", "Conecta ataques y facilita llegadas desde atrás."
    return "Finalizador", "Ataca espacios y vive de convertir las ocasiones del equipo."


def gameplay_traits(player: dict[str, Any]) -> list[dict[str, str]]:
    out = source_trait_api(player)
    consistency = _num(player, "consistency")
    leadership = _num(player, "leadership")
    discipline = _num(player, "discipline")
    aggression = _num(player, "aggression")
    heading = _num(player, "heading")
    jumping = _num(player, "jumping")
    free_kicks = _num(player, "free_kicks")
    penalties = _num(player, "penalties")
    vision = _num(player, "vision")
    short_pass = _num(player, "short_pass")
    work_rate = _num(player, "work_rate")
    stamina = _num(player, "stamina")

    def add(code: str, label: str, effect: str, polarity: str = "positive") -> None:
        if not any(row["code"] == code for row in out):
            out.append({"code": code, "label": label, "effect": effect, "polarity": polarity, "provenance": "derived_from_mdb_attributes"})

    if consistency >= 84:
        add("consistent", "Regular", "Reduce la variación de rendimiento entre partidos.")
    elif consistency <= 52:
        add("inconsistent", "Irregular", "Puede alternar actuaciones muy distintas.", "warning")
    if leadership >= 84:
        add("leader", "Líder", "Ayuda a sostener al equipo en contextos adversos.")
    if discipline <= 54 and aggression >= 72:
        add("card_risk", "Al límite", "Su agresividad aumenta faltas y riesgo de tarjeta.", "warning")
    if heading >= 84 and jumping >= 78:
        add("aerial", "Dominio aéreo", "Gana peso en centros, córners y juego directo.")
    if free_kicks >= 86:
        add("free_kick", "Especialista en faltas", "Es amenaza real en libres directos.")
    if penalties >= 86:
        add("penalty", "Penaltis", "Es una opción fiable desde los once metros.")
    if vision >= 84 and short_pass >= 80:
        add("creator", "Creador", "Tiene más peso en progresión y último pase.")
    if work_rate >= 84 and stamina >= 80:
        add("engine", "Motor", "Tolera mejor presión, recorridos y ritmos altos.")
    return out[:8]


def tactical_fit(player: dict[str, Any], tactics: Any) -> dict[str, Any]:
    """Explain compatibility with a tactical plan without changing base ability."""
    press = (_num(player, "work_rate") + _num(player, "stamina") + _num(player, "aggression")) / 3
    possession = (_num(player, "short_pass") + _num(player, "vision") + _num(player, "technique")) / 3
    direct = (_num(player, "long_pass") + _num(player, "strength") + max(_num(player, "pace"), _num(player, "heading"))) / 3
    wide = (_num(player, "pace") + _num(player, "dribbling") + _num(player, "stamina")) / 3
    compact = (_num(player, "positioning") + _num(player, "short_pass") + _num(player, "anticipation")) / 3
    defend_high = (_num(player, "pace") + _num(player, "anticipation") + _num(player, "positioning")) / 3
    score = 62.0
    reasons: list[str] = []
    if getattr(tactics, "pressing", "medium") == "high":
        score += (press - 65) * .18; reasons.append("trabajo para presión alta")
    if getattr(tactics, "directness", "mixed") == "short":
        score += (possession - 65) * .20; reasons.append("calidad para asociarse")
    elif getattr(tactics, "directness", "mixed") == "direct":
        score += (direct - 65) * .18; reasons.append("recursos para juego directo")
    if getattr(tactics, "width", "normal") == "wide":
        score += (wide - 65) * .13; reasons.append("recorrido para dar amplitud")
    elif getattr(tactics, "width", "normal") == "narrow":
        score += (compact - 65) * .13; reasons.append("lectura para jugar por dentro")
    if getattr(tactics, "defensive_line", "medium") == "high":
        score += (defend_high - 65) * .14; reasons.append("velocidad/lectura para línea alta")
    score = max(20.0, min(100.0, score))
    return {"score": round(score, 1), "label": "Excelente" if score >= 80 else "Bueno" if score >= 68 else "Neutro" if score >= 55 else "Difícil", "reasons": reasons}


def match_consistency_multiplier(player: dict[str, Any], *, seed: int) -> float:
    """Stable per-match ability noise driven by source Consistencia.

    It changes execution inside one match, never the stored overall rating.
    """
    consistency = _num(player, "consistency", 65)
    spread = 0.105 - consistency * 0.00075  # ~6.6% at 52, ~4.2% at 84
    digest = sha256(f"m9394:{player.get('source_id')}:{seed}:consistency".encode()).digest()
    unit = int.from_bytes(digest[:4], "big") / 2**32
    centered = (unit - .5) * 2
    return max(.87, min(1.13, 1.0 + centered * spread))
