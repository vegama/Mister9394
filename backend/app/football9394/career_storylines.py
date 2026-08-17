from __future__ import annotations

"""Emergent, fact-backed story arcs for Míster 93/94.

A storyline is not flavour text.  It exists only while a real condition exists
in the save: a streak, title/relegation pressure, an unhappy star, an active
transfer saga, a hot rivalry or a recent coach change.  The layer gives the
player continuity between matches without adding chores.
"""

from typing import Any


def ensure_storyline_state(state: dict[str, Any]) -> None:
    state.setdefault("storylines", [])


def _upsert(state: dict[str, Any], *, key: str, date_text: str, kind: str, title: str, summary: str,
            intensity: int, entities: dict[str, Any] | None = None, priority: str = "normal") -> dict[str, Any]:
    ensure_storyline_state(state)
    rows = state["storylines"]
    current = next((row for row in rows if row.get("key") == key and row.get("status") == "active"), None)
    if current is None:
        current = {
            "id": f"story:{key}:{date_text}", "key": key, "kind": kind, "status": "active",
            "started_on": date_text, "milestones": [],
        }
        rows.append(current)
    current.update({
        "updated_on": date_text, "title": title, "summary": summary,
        "intensity": max(1, min(100, int(intensity))), "priority": priority,
        "entities": entities or {},
    })
    return current


def _resolve_absent(state: dict[str, Any], active_keys: set[str], date_text: str, kinds: set[str]) -> None:
    for row in state.get("storylines") or []:
        if row.get("status") != "active" or row.get("kind") not in kinds:
            continue
        if row.get("key") not in active_keys:
            row["status"] = "resolved"
            row["resolved_on"] = date_text


def refresh_storylines(
    state: dict[str, Any], *, date_text: str, controlled_team_id: int,
    standings: list[dict[str, Any]], recent_form: list[str], squad: list[dict[str, Any]],
    negotiations: list[dict[str, Any]], next_match: dict[str, Any] | None,
    rivalry: dict[str, Any] | None, team_name: str, opponent_name: str | None = None,
    manager_name_lookup=None, player_name_lookup=None,
) -> list[dict[str, Any]]:
    ensure_storyline_state(state)
    active: set[str] = set()
    own = next((r for r in standings if int(r.get("team_id") or 0) == int(controlled_team_id)), None) or {}
    played = int(own.get("played") or 0)
    count = len(standings)
    position = int(own.get("position") or 0)

    if played >= 5 and count:
        if position <= 3:
            key = "table:title"
            active.add(key)
            _upsert(state, key=key, date_text=date_text, kind="table_pressure", title="La pelea de arriba ya es real",
                    summary=f"{team_name} marcha {position}º después de {played} partidos. Cada jornada empieza a pesar.",
                    intensity=68 + (4-position)*7, entities={"team_id": controlled_team_id}, priority="high" if position == 1 else "normal")
        if count >= 8 and position >= max(1, count-3):
            key = "table:survival"
            active.add(key)
            _upsert(state, key=key, date_text=date_text, kind="table_pressure", title="La permanencia entra en cada decisión",
                    summary=f"{team_name} ocupa la {position}ª posición. Rotaciones, lesiones y puntos directos ya tienen coste inmediato.",
                    intensity=74, entities={"team_id": controlled_team_id}, priority="high")

    form = list(recent_form or [])[-5:]
    if len(form) >= 3:
        if all(x == "V" for x in form[-3:]):
            key = "form:wins"; active.add(key)
            _upsert(state, key=key, date_text=date_text, kind="streak", title="El equipo ha encontrado una ola",
                    summary=f"Tres victorias consecutivas han cambiado la energía alrededor de {team_name}.", intensity=62,
                    entities={"team_id": controlled_team_id})
        elif all(x == "D" for x in form[-3:]):
            key = "form:losses"; active.add(key)
            _upsert(state, key=key, date_text=date_text, kind="streak", title="Tres derrotas ya forman una crisis",
                    summary="La siguiente alineación y el próximo resultado tendrán más peso del habitual.", intensity=82,
                    entities={"team_id": controlled_team_id}, priority="high")
        elif "D" not in form[-4:] and len(form) >= 4:
            key = "form:unbeaten"; active.add(key)
            _upsert(state, key=key, date_text=date_text, kind="streak", title="Una racha que empieza a construir confianza",
                    summary=f"{team_name} enlaza cuatro partidos sin perder.", intensity=56, entities={"team_id": controlled_team_id})

    ranked = sorted(squad, key=lambda p: -int(p.get("overall") or 0))
    for player in ranked[:6]:
        dyn = player.get("squad_dynamics") or player.get("profile", {}).get("squad_dynamics") or {}
        if bool(dyn.get("wants_move")) or int(dyn.get("satisfaction") or 70) < 38:
            pid = int(player.get("id") or player.get("source_id") or 0)
            name = player.get("display_name") or player.get("name") or (player_name_lookup(pid) if player_name_lookup else str(pid))
            key = f"player:unhappy:{pid}"; active.add(key)
            _upsert(state, key=key, date_text=date_text, kind="player_tension", title=f"{name} ya no es un problema silencioso",
                    summary=f"Una pieza importante está descontenta ({int(dyn.get('satisfaction') or 0)}/100) y su futuro empieza a afectar al vestuario.",
                    intensity=84 if dyn.get("wants_move") else 70, entities={"player_id": pid, "team_id": controlled_team_id}, priority="high")
            break

    for row in negotiations:
        if row.get("status") not in {"waiting", "countered"}:
            continue
        pid = int(row.get("player_id") or 0)
        name = player_name_lookup(pid) if player_name_lookup else f"Jugador {pid}"
        key = f"transfer:{pid}"; active.add(key)
        round_no = int(row.get("round") or 1)
        _upsert(state, key=key, date_text=date_text, kind="transfer_saga", title=f"La operación {name} sigue abierta",
                summary=f"La negociación entra en su ronda {round_no}. Esperar puede cambiar precio, competencia y alternativas.",
                intensity=min(88, 48 + round_no*12), entities={"player_id": pid}, priority="high" if row.get("status") == "countered" else "normal")

    if next_match and rivalry and int(rivalry.get("heat") or 0) >= 45:
        other = int(next_match.get("away_team_id") if int(next_match.get("home_team_id") or 0) == int(controlled_team_id) else next_match.get("home_team_id") or 0)
        key = f"rivalry:{min(other,controlled_team_id)}:{max(other,controlled_team_id)}"; active.add(key)
        label = opponent_name or str(other)
        _upsert(state, key=key, date_text=date_text, kind="rivalry", title=f"No es una jornada cualquiera: llega {label}",
                summary=f"La rivalidad está en {int(rivalry.get('heat') or 0)}/100 y arrastra {int(rivalry.get('meetings') or 0)} enfrentamientos registrados en esta carrera.",
                intensity=int(rivalry.get("heat") or 50), entities={"team_id": controlled_team_id, "opponent_id": other}, priority="high")

    latest_change = next((row for row in reversed(state.get("manager_history") or []) if row.get("date") <= date_text), None)
    if latest_change and latest_change.get("date") == date_text:
        tid = int(latest_change.get("team_id") or 0)
        mid = int(latest_change.get("to_manager_id") or 0)
        name = manager_name_lookup(mid) if manager_name_lookup else f"Entrenador {mid}"
        key = f"manager-change:{tid}:{date_text}"; active.add(key)
        _upsert(state, key=key, date_text=date_text, kind="manager_change", title=f"{name} abre una nueva etapa",
                summary="Un cambio de entrenador alterará sistema, jerarquías y prioridades de mercado del club desde este momento.",
                intensity=66, entities={"team_id": tid, "manager_id": mid})

    _resolve_absent(state, active, date_text, {"table_pressure", "streak", "player_tension", "transfer_saga", "rivalry", "manager_change"})
    state["storylines"] = (state.get("storylines") or [])[-160:]
    return storyline_snapshot(state)


def storyline_snapshot(state: dict[str, Any], *, limit: int = 10) -> list[dict[str, Any]]:
    rows = [dict(row) for row in state.get("storylines") or [] if row.get("status") == "active"]
    rows.sort(key=lambda r: (0 if r.get("priority") == "high" else 1, -int(r.get("intensity") or 0), str(r.get("started_on") or "")))
    return rows[:max(1, int(limit))]
