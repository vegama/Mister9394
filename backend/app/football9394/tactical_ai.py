from __future__ import annotations

"""Source-coach tactical planning and opponent-specific preparation.

P5 deliberately keeps the match engine readable.  AI clubs do not receive
hidden rating bonuses for having a good manager.  Better coaches instead:

* choose a source-backed plan that fits their own squad;
* scout the opponent's *observable* recent habits rather than reading the
  user's last-second tactical screen;
* identify a small number of concrete threats;
* make restrained, explainable counter-adjustments; and
* react to what is actually happening during the match.

The resulting plan is deterministic for the same football state.  This makes it
possible to explain a decision in the UI and regression-test it without turning
coaching into an opaque dice roll.
"""

from collections import Counter
from dataclasses import asdict, replace
from typing import Any, Iterable

from .coaching import tactics_from_source_manager
from .match_engine import FootballTactics9394
from .player_identity import tactical_fit
from .position_roles import assign_players_to_formation, role_for_player


def _overall(player: dict[str, Any]) -> int:
    return int(player.get("overall") or player.get("category") or 60)


def _attr(player: dict[str, Any], key: str, default: int = 60) -> int:
    attrs = player.get("attributes") or {}
    raw = attrs.get(key, player.get(key, default))
    try:
        return max(1, min(100, int(raw)))
    except (TypeError, ValueError):
        return default


def _formation_fit(players: list[dict[str, Any]], formation: str) -> tuple[float, list[dict[str, Any]]]:
    assigned = assign_players_to_formation(players, formation)
    if len(assigned) < 11:
        return -9999.0, assigned
    score = sum(_overall(row["player"]) - float(row["penalty"]) * 1.8 for row in assigned)
    score += sum(1.4 for row in assigned if role_for_player(row["player"]).squad_slot == row["slot"])
    return score, assigned


def _plan_fit(players: list[dict[str, Any]], tactics: FootballTactics9394) -> float:
    score, assigned = _formation_fit(players, tactics.formation)
    if score < 0:
        return score
    xi = [row["player"] for row in assigned]
    compatibility = sum(float(tactical_fit(player, tactics)["score"]) for player in xi) / 11.0
    return score + (compatibility - 60.0) * 1.35


def ai_tactics_for_squad(players: Iterable[dict[str, Any]], manager: dict[str, Any] | None = None) -> FootballTactics9394:
    """Pick a plan that balances the coach's ideas and actual squad."""
    squad = list(players)
    if len(squad) < 11:
        return tactics_from_source_manager(manager)
    source_plan = tactics_from_source_manager(manager)
    formations: list[str] = [source_plan.formation]
    raw_tactics = (manager or {}).get("tactics") or {}
    from .coaching import _canonical_formation  # same source mapping by design
    for key in ("attacking", "defensive"):
        formation = _canonical_formation(raw_tactics.get(key))
        if formation not in formations:
            formations.append(formation)
    for fallback in ("4-4-2", "4-3-3", "4-5-1", "4-4-1-1", "3-5-2", "5-3-2"):
        if fallback not in formations:
            formations.append(fallback)

    quality = int((manager or {}).get("coaching_quality") or 60)
    relationship = str((manager or {}).get("player_relationship") or "normal")
    adherence = 16.0 + max(0, min(100, quality) - 50) * .16
    if relationship == "distant":
        adherence += 2.5
    elif relationship == "close":
        adherence -= 1.0

    candidates: list[tuple[float, FootballTactics9394]] = []
    for rank, formation in enumerate(formations):
        plan = replace(source_plan, formation=formation)
        if formation in {"4-3-3", "3-4-3"}:
            plan = replace(plan, width="wide")
        elif formation in {"4-3-1-2", "3-4-1-2"}:
            plan = replace(plan, width="narrow")
        score = _plan_fit(squad, plan)
        if formation == source_plan.formation:
            score += adherence
        elif rank <= 2:
            score += adherence * .55
        candidates.append((score, plan))
    candidates.sort(key=lambda row: row[0], reverse=True)
    return candidates[0][1]


# ---------------------------------------------------------------------------
# P5 · observable tactical memory


def ensure_tactical_memory_state(state: dict[str, Any]) -> None:
    memory = state.setdefault("tactical_memory", {})
    memory.setdefault("managed_history", [])
    memory.setdefault("rival_learning", {})


def tactical_context_for_fixture(fixture: dict[str, Any] | None) -> dict[str, Any]:
    """Reduce a fixture to the public context a coach can prepare for.

    P5 treats league football, group football and knockout football as different
    scouting environments.  The helper intentionally uses only fixture metadata
    that both clubs know before kickoff; it never inspects hidden user choices.
    """
    row = dict(fixture or {})
    kind = str(row.get("fixture_type") or row.get("kind") or row.get("competition_kind") or "unknown")
    competition_id = row.get("competition_id") or row.get("source_id")
    stage = str(row.get("stage") or "").strip()
    lowered = stage.casefold()
    explicit_phase = str(row.get("phase") or "").strip()
    if explicit_phase:
        phase = explicit_phase
    elif kind == "league":
        phase = "league"
    elif kind == "tournament":
        if "final" in lowered and "semi" not in lowered:
            phase = "final"
        elif row.get("group") is not None or "grupo" in lowered or "group" in lowered:
            phase = "group"
        elif int(row.get("leg") or 0) == 2:
            phase = "second_leg_knockout"
        else:
            phase = "knockout"
    elif kind == "friendly":
        phase = "friendly"
    else:
        phase = "generic"
    return {
        "competition_kind": kind,
        "competition_id": int(competition_id) if str(competition_id or "").isdigit() else None,
        "competition_name": str(row.get("competition_name") or ""),
        "stage": stage,
        "phase": phase,
        "leg": int(row.get("leg") or 0) or None,
        "group": row.get("group"),
    }


def record_managed_tactical_usage(
    state: dict[str, Any], *, date_text: str, opponent_team_id: int, tactics: FootballTactics9394 | dict[str, Any],
    competition_context: dict[str, Any] | None = None,
) -> None:
    """Remember the public tactical shape used in an official managed match.

    This is what future opponents are allowed to scout.  The AI never reads a
    last-second user change before kickoff; it sees only habits already exposed
    in prior matches.
    """
    ensure_tactical_memory_state(state)
    payload = asdict(tactics) if isinstance(tactics, FootballTactics9394) else dict(tactics)
    context = tactical_context_for_fixture(competition_context)
    row = {
        "date": str(date_text), "opponent_team_id": int(opponent_team_id),
        "competition_kind": context["competition_kind"], "competition_id": context["competition_id"],
        "competition_name": context["competition_name"], "stage": context["stage"], "phase": context["phase"],
        **{key: payload.get(key) for key in (
            "formation", "mentality", "tempo", "pressing", "directness",
            "defensive_line", "width", "offside_trap", "marking",
        )},
    }
    history = state["tactical_memory"]["managed_history"]
    history.append(row)
    state["tactical_memory"]["managed_history"] = history[-40:]


def _mode(rows: list[dict[str, Any]], key: str, fallback: Any) -> tuple[Any, float]:
    values = [row.get(key) for row in rows if row.get(key) is not None]
    if not values:
        return fallback, 0.0
    counts = Counter(values)
    value, count = counts.most_common(1)[0]
    return value, count / len(values)


def expected_managed_tactics(
    state: dict[str, Any], *, fallback: FootballTactics9394 | dict[str, Any] | None = None, sample: int = 6,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return what a rival scout could reasonably predict from recent matches."""
    ensure_tactical_memory_state(state)
    if isinstance(fallback, FootballTactics9394):
        base = asdict(fallback)
    else:
        base = {**asdict(FootballTactics9394()), **(fallback or {})}
    history = list(state["tactical_memory"].get("managed_history") or [])
    wanted = tactical_context_for_fixture(context)
    if context and history:
        # Same competition and same phase matter most, but recent generic
        # evidence is still used.  This lets a manager expose one pattern in
        # league play and another in Europe without either becoming invisible.
        ranked: list[tuple[int, int, dict[str, Any]]] = []
        for index, row in enumerate(history):
            score = 0
            if row.get("competition_kind") == wanted.get("competition_kind"):
                score += 3
            if wanted.get("competition_id") is not None and row.get("competition_id") == wanted.get("competition_id"):
                score += 3
            if row.get("phase") == wanted.get("phase"):
                score += 2
            ranked.append((score, index, row))
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        rows = [row for _, _, row in ranked[:max(1, int(sample))]]
        rows.sort(key=lambda row: str(row.get("date") or ""))
    else:
        rows = history[-max(1, int(sample)):]
    if not rows:
        return {"tactics": base, "sample_size": 0, "context_sample_size": 0, "predictability": 0, "summary": "Sin patrón suficiente", "context": wanted}
    confidence_parts: list[float] = []
    predicted: dict[str, Any] = {}
    for key in ("formation", "mentality", "tempo", "pressing", "directness", "defensive_line", "width", "marking"):
        predicted[key], confidence = _mode(rows, key, base.get(key))
        confidence_parts.append(confidence)
    predicted["offside_trap"], confidence = _mode(rows, "offside_trap", base.get("offside_trap", False))
    confidence_parts.append(confidence)
    predictability = round(sum(confidence_parts) / len(confidence_parts) * 100)
    tactics = {**base, **predicted}
    context_sample = sum(
        1 for row in rows
        if row.get("competition_kind") == wanted.get("competition_kind")
        and (wanted.get("competition_id") is None or row.get("competition_id") == wanted.get("competition_id"))
    ) if context else 0
    return {
        "tactics": tactics,
        "sample_size": len(rows),
        "context_sample_size": context_sample,
        "predictability": predictability,
        "summary": f"{tactics['formation']} · {tactics['directness']} · {tactics['width']}",
        "context": wanted,
    }


def record_rival_preparation_outcome(
    state: dict[str, Any], *, manager_id: int | None, team_id: int, date_text: str,
    preparation: dict[str, Any], goals_for: int, goals_against: int,
    competition_context: dict[str, Any] | None = None,
) -> None:
    """Persist what an AI coach learned from actually facing the human manager.

    Learning is attached to the coach when possible, so a later reunion can
    carry football memory across clubs.  Only the public prepared plan and the
    result are retained; player ratings or hidden user state are never stored.
    """
    ensure_tactical_memory_state(state)
    key = f"manager:{int(manager_id)}" if manager_id is not None else f"team:{int(team_id)}"
    bucket = state["tactical_memory"]["rival_learning"].setdefault(key, [])
    score = 1.0 if int(goals_for) > int(goals_against) else .5 if int(goals_for) == int(goals_against) else 0.0
    prepared = preparation.get("prepared_tactics") or preparation.get("tactics") or {}
    row = {
        "date": str(date_text), "team_id": int(team_id), "manager_id": int(manager_id) if manager_id is not None else None,
        "score": score, "goals_for": int(goals_for), "goals_against": int(goals_against),
        "expected_opponent": dict(preparation.get("expected_opponent") or {}),
        "prepared_tactics": dict(prepared), "adjustments": list(preparation.get("adjustments") or []),
        "context": tactical_context_for_fixture(competition_context),
    }
    bucket.append(row)
    state["tactical_memory"]["rival_learning"][key] = bucket[-12:]


def rival_learning_for_preparation(
    state: dict[str, Any], *, manager_id: int | None, team_id: int,
    expected_opponent_tactics: FootballTactics9394 | dict[str, Any],
) -> dict[str, Any]:
    """Summarise prior head-to-head lessons that are still tactically relevant."""
    ensure_tactical_memory_state(state)
    key = f"manager:{int(manager_id)}" if manager_id is not None else f"team:{int(team_id)}"
    rows = list((state["tactical_memory"].get("rival_learning") or {}).get(key) or [])
    if isinstance(expected_opponent_tactics, FootballTactics9394):
        expected = asdict(expected_opponent_tactics)
    else:
        expected = dict(expected_opponent_tactics or {})
    formation = expected.get("formation")
    relevant = [row for row in rows if not formation or (row.get("expected_opponent") or {}).get("formation") == formation]
    if not relevant:
        return {"games": 0, "success_rate": None, "last_successful_tactics": None, "last_successful_adjustments": [], "failed_last_time": False}
    successes = [row for row in relevant if float(row.get("score") or 0) >= .5]
    last_success = next((row for row in reversed(relevant) if float(row.get("score") or 0) >= .5), None)
    last = relevant[-1]
    return {
        "games": len(relevant),
        "success_rate": round(sum(float(row.get("score") or 0) for row in relevant) / len(relevant), 3),
        "last_successful_tactics": dict((last_success or {}).get("prepared_tactics") or {}) or None,
        "last_successful_adjustments": list((last_success or {}).get("adjustments") or []),
        "failed_last_time": float(last.get("score") or 0) == 0.0,
        "last_date": last.get("date"),
        "successful_games": len(successes),
    }


def opponent_threat_profile(players: Iterable[dict[str, Any]], tactics: FootballTactics9394 | dict[str, Any]) -> dict[str, Any]:
    """Describe football threats using only observable player/tactical traits."""
    squad = sorted(list(players), key=_overall, reverse=True)[:16]
    if isinstance(tactics, dict):
        tactics = FootballTactics9394(**{**asdict(FootballTactics9394()), **tactics})
    if not squad:
        return {"pace": 50, "aerial": 50, "creativity": 50, "wide": 50, "set_piece": 50, "labels": []}

    def best_score(keys: tuple[str, ...], *, take: int = 4) -> int:
        scores = sorted((sum(_attr(p, key) for key in keys) / len(keys) for p in squad), reverse=True)[:take]
        return round(sum(scores) / len(scores)) if scores else 50

    wide_players = [p for p in squad if role_for_player(p).squad_slot in {"RM", "LM", "RW", "LW", "RB", "LB"}]
    wide_scores = sorted(((_attr(p, "crossing") + _attr(p, "dribbling") + _attr(p, "pace")) / 3 for p in wide_players), reverse=True)[:4]
    wide = round(sum(wide_scores) / len(wide_scores)) if wide_scores else 50
    if tactics.width == "wide":
        wide = min(100, wide + 7)

    profile = {
        "pace": best_score(("pace", "acceleration", "off_ball")),
        "aerial": best_score(("heading", "jumping", "strength")),
        "creativity": best_score(("vision", "short_pass", "technique")),
        "wide": wide,
        "set_piece": best_score(("free_kicks", "crossing", "heading"), take=3),
    }
    labels: list[str] = []
    for key, label in (
        ("pace", "amenaza al espacio"), ("aerial", "juego aéreo"),
        ("creativity", "creación entre líneas"), ("wide", "peligro por fuera"),
        ("set_piece", "balón parado"),
    ):
        if int(profile[key]) >= 72:
            labels.append(label)
    profile["labels"] = labels[:3]
    return profile


def _own_execution(players: list[dict[str, Any]]) -> dict[str, int]:
    if not players:
        return {"press": 60, "pass": 60, "pace": 60, "aerial": 60}
    top = sorted(players, key=_overall, reverse=True)[:14]
    avg = lambda *keys: round(sum(sum(_attr(p, k) for k in keys) / len(keys) for p in top) / len(top))
    return {
        "press": avg("stamina", "work_rate", "aggression"),
        "pass": avg("technique", "short_pass", "vision"),
        "pace": avg("pace", "acceleration"),
        "aerial": avg("heading", "jumping", "strength"),
    }


def prepare_tactics_for_opponent(
    base: FootballTactics9394,
    *,
    own_players: Iterable[dict[str, Any]],
    opponent_players: Iterable[dict[str, Any]],
    expected_opponent_tactics: FootballTactics9394 | dict[str, Any],
    manager: dict[str, Any] | None = None,
    observed_sample: int = 0,
    observed_predictability: int = 0,
    match_context: dict[str, Any] | None = None,
    learning: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare a restrained counter-plan without changing player ratings.

    Coaching quality governs how many observations a manager can turn into a
    coherent response.  A weak coach may spot the same threat but make fewer
    changes.  The output includes plain-language reasons for the match preview.
    """
    own = list(own_players)
    opposition = list(opponent_players)
    if isinstance(expected_opponent_tactics, dict):
        expected = FootballTactics9394(**{**asdict(FootballTactics9394()), **expected_opponent_tactics})
    else:
        expected = expected_opponent_tactics
    threat = opponent_threat_profile(opposition, expected)
    execution = _own_execution(own)
    quality = max(1, min(100, int((manager or {}).get("coaching_quality") or 60)))
    context = tactical_context_for_fixture(match_context)
    learning = dict(learning or {})
    # No history means only generic squad scouting.  Repeated public habits make
    # preparation more confident, but never perfect.
    confidence = max(28, min(92, round(quality * .58 + int(observed_predictability) * .32 + min(6, observed_sample) * 2.0)))
    adjustment_budget = 1 if quality < 62 else 2 if quality < 80 else 3
    phase = str(context.get("phase") or "generic")
    if phase in {"knockout", "second_leg_knockout", "final"} and quality >= 70:
        confidence = min(94, confidence + (5 if phase == "final" else 3))
        adjustment_budget = min(3, adjustment_budget + 1)
    if int(learning.get("games") or 0) > 0:
        confidence = min(95, confidence + min(6, int(learning.get("games") or 0) * 2))
        if learning.get("failed_last_time"):
            confidence = max(28, confidence - 2)
    plan = base
    adjustments: list[str] = []
    learning_note = ""
    phase_focus = {
        "league": "Prioriza el patrón repetible de liga y la gestión de noventa minutos.",
        "group": "Separa los hábitos de fase de grupos de los usados en eliminatorias.",
        "knockout": "Aumenta el peso de los emparejamientos y reduce soluciones frágiles.",
        "second_leg_knockout": "Prepara una vuelta de eliminatoria: concede menos valor a un plan único y protege escenarios de partido.",
        "final": "En una final la preparación es de máxima exigencia: detalles, balón parado y control de riesgos pesan más.",
        "friendly": "La prioridad es observar, no revelar ni sobrerreaccionar.",
        "generic": "Preparación general basada en información pública disponible.",
    }.get(phase, "Preparación general basada en información pública disponible.")

    def change(reason: str, **kwargs: Any) -> None:
        nonlocal plan
        if len(adjustments) >= adjustment_budget:
            return
        candidate = replace(plan, **kwargs)
        if candidate != plan:
            plan = candidate
            adjustments.append(reason)

    # Longitudinal learning: a coach may deliberately recover one solution that
    # already worked against the *same exposed opponent shape*.  This happens
    # before generic counters so it competes for the same finite preparation
    # budget and never becomes a free hidden bonus.
    learned_plan = learning.get("last_successful_tactics") or {}
    success_rate = learning.get("success_rate")
    if learned_plan and success_rate is not None and float(success_rate) >= .5:
        for key in ("defensive_line", "pressing", "marking", "directness", "width"):
            value = learned_plan.get(key)
            if value is not None and value != getattr(plan, key):
                change("Recupera una solución que ya funcionó en un enfrentamiento anterior", **{key: value})
                if adjustments:
                    learning_note = f"El técnico conserva memoria de {int(learning.get('games') or 0)} duelo(s) ante este patrón."
                break
    elif int(learning.get("games") or 0) > 0 and learning.get("failed_last_time"):
        learning_note = "El plan anterior no funcionó y el técnico evita repetirlo de forma automática."

    # 1) Pace behind the line: the most dangerous structural mismatch.
    if int(threat["pace"]) >= 74 and plan.defensive_line == "high":
        change("Baja la línea para negar metros a su velocidad", defensive_line="medium", offside_trap=False)
    elif int(threat["pace"]) >= 82 and plan.defensive_line == "medium" and quality >= 78:
        change("Protege la espalda ante su amenaza al espacio", defensive_line="low", offside_trap=False)

    # 2) Central creators: press if the squad can sustain it, otherwise track.
    if int(threat["creativity"]) >= 74 and expected.directness in {"short", "mixed"}:
        if execution["press"] >= 68:
            change("Sube la presión para incomodar a sus creadores", pressing="high")
        elif quality >= 72:
            change("Refuerza referencias sobre sus creadores", marking="man")

    # 3) Wide/aerial threat: do not pretend width itself defends; use contact
    # and a safer line, which the engine actually models defensively.
    if int(threat["wide"]) >= 74 and int(threat["aerial"]) >= 70:
        if plan.marking != "man" and quality >= 70:
            change("Endurece las marcas para defender centros y remates", marking="man")
        elif plan.defensive_line == "high":
            change("Evita defender los centros corriendo hacia tu portería", defensive_line="medium")

    # 4) How to escape the opponent's pressure is constrained by own quality.
    if expected.pressing == "high":
        if execution["pass"] >= 73 and plan.directness != "short":
            change("Confía en la calidad técnica para salir de su presión", directness="short")
        elif execution["pass"] < 66 and plan.directness != "direct":
            change("Evita pérdidas peligrosas saliendo más directo", directness="direct")

    # 5) A deep block can be stretched by a capable attacking coach, but this
    # never overrides all of the manager's source identity.
    if expected.defensive_line == "low" and int(threat["pace"]) < 76 and quality >= 78 and plan.width != "wide":
        change("Busca ensanchar un bloque que se espera bajo", width="wide")

    # In finals, a capable coach spends one of the scarce preparation slots on
    # dead-ball protection when the opponent gives him a concrete reason.
    if phase == "final" and quality >= 72 and int(threat["set_piece"]) >= 70 and plan.marking != "man":
        change("En una final prioriza referencias claras para defender el balón parado", marking="man")

    return {
        "tactics": plan,
        "prepared_tactics": asdict(plan),
        "base_tactics": base,
        "adjustments": adjustments,
        "threat_profile": threat,
        "confidence": confidence,
        "observed_sample": int(observed_sample),
        "observed_predictability": int(observed_predictability),
        "expected_opponent": asdict(expected),
        "summary": tactical_summary(plan),
        "context": context,
        "phase_focus": phase_focus,
        "preparation_intensity": "alta" if phase in {"final", "second_leg_knockout"} and quality >= 70 else "media" if phase in {"knockout", "group", "league"} else "baja",
        "learning": learning,
        "learning_note": learning_note,
    }


def contextual_ai_tactics(
    base: FootballTactics9394,
    *,
    minute: int,
    goals_for: int,
    goals_against: int,
    manager: dict[str, Any] | None = None,
) -> FootballTactics9394:
    """Score-state fallback used by callers outside the detailed engine."""
    if minute < 55:
        return base
    tendency = str((manager or {}).get("game_tendency") or "normal")
    quality = int((manager or {}).get("coaching_quality") or 60)
    score = goals_for - goals_against
    if score < 0 and minute >= (72 if quality < 60 else 62):
        return replace(base, mentality="attacking", tempo="high", pressing="high", defensive_line="high")
    if score > 0 and minute >= (78 if tendency == "attacking" else 68):
        return replace(base, mentality="defensive", tempo="slow", pressing="medium", defensive_line="low")
    return base


def tactical_summary(tactics: FootballTactics9394) -> str:
    bits = [tactics.formation]
    if tactics.pressing == "high": bits.append("presión alta")
    elif tactics.pressing == "low": bits.append("bloque bajo")
    if tactics.directness == "short": bits.append("pase corto")
    elif tactics.directness == "direct": bits.append("juego directo")
    if tactics.width == "wide": bits.append("amplitud")
    elif tactics.width == "narrow": bits.append("juego interior")
    if tactics.offside_trap: bits.append("fuera de juego")
    return " · ".join(bits)
