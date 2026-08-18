from __future__ import annotations

"""Causal newspaper/hemeroteca for Míster 93/94.

No filler headlines are generated. Every item has a source event key so reloads
and repeated snapshots cannot duplicate the story.
"""

from typing import Any, Callable


def ensure_news_state(state: dict[str, Any]) -> None:
    state.setdefault("news_feed", [])
    state.setdefault("news_seen_keys", [])
    state.setdefault("news_seen_causes", [])
    if "news_serial" not in state:
        serial=0
        for item in state.get("news_feed") or []:
            raw=str(item.get("id") or "")
            if raw.startswith("news-"):
                try: serial=max(serial,int(raw.split("-",1)[1]))
                except ValueError: pass
        state["news_serial"]=serial


def _key(event: dict[str, Any]) -> str:
    material = (
        event.get("kind"), event.get("date"), event.get("source_id"), event.get("stage"),
        event.get("player_id"), event.get("from_team_id"), event.get("to_team_id"),
        event.get("champion_team_id"), event.get("home_team_id"), event.get("away_team_id"),
        event.get("home_goals"), event.get("away_goals"), event.get("from_season"), event.get("to_season"),
        event.get("team_id"), event.get("from_manager_id"), event.get("to_manager_id"),
        event.get("record"), event.get("value"), event.get("opponent_id"),
    )
    return "|".join("" if x is None else str(x) for x in material)


def publish(state: dict[str, Any], *, key: str, date: str, category: str, importance: int,
            headline: str, detail: str = "", entity: dict[str, Any] | None = None, cause: str = "") -> dict[str, Any] | None:
    ensure_news_state(state)
    if key in set(state.get("news_seen_keys") or []):
        return None
    if cause and cause in set(state.get("news_seen_causes") or []):
        return None
    state["news_serial"] = int(state.get("news_serial") or 0) + 1
    item = {
        "id": f"news-{state['news_serial']}", "date": date, "category": category,
        "importance": int(max(1,min(5,importance))), "headline": headline, "detail": detail,
        "entity": entity or {}, "source_key": key, "cause": cause or None,
    }
    state["news_feed"].append(item)
    state["news_feed"] = state["news_feed"][-800:]
    state["news_seen_keys"].append(key)
    state["news_seen_keys"] = state["news_seen_keys"][-1200:]
    if cause:
        state["news_seen_causes"].append(cause)
        state["news_seen_causes"] = state["news_seen_causes"][-1200:]
    return item


def ingest_events(state: dict[str, Any], events: list[dict[str, Any]], *,
                  team_name: Callable[[int], str], player_name: Callable[[int], str]) -> list[dict[str, Any]]:
    created=[]
    for event in events:
        kind=str(event.get("kind") or "")
        date=str(event.get("date") or state.get("current_date") or "")
        key=f"event:{_key(event)}"
        item=None
        if kind in {"ai_transfer","user_transfer","user_sale"}:
            pid=int(event.get("player_id") or 0); a=int(event.get("from_team_id") or 0); b=int(event.get("to_team_id") or 0)
            item=publish(state,key=key,date=date,category="Mercado",importance=3,
                headline=f"{player_name(pid)} cambia de club",
                detail=f"{team_name(a)} y {team_name(b)} cierran el movimiento por {int(event.get('fee') or 0):,} ptas.".replace(",","."),
                entity={"player_id":pid,"team_id":b})
        elif kind=="contract_expired":
            pid=int(event.get("player_id") or 0); a=int(event.get("from_team_id") or 0)
            item=publish(state,key=key,date=date,category="Contratos",importance=2,
                headline=f"{player_name(pid)} queda libre",detail=f"Finaliza su contrato con {team_name(a)}.",entity={"player_id":pid})
        elif kind=="competition_completed":
            champion=int(event.get("champion_team_id") or 0); name=str(event.get("competition_name") or f"Competición {event.get('source_id')}")
            cause=f"competition-title:{state.get('season')}:{event.get('competition_kind') or 'competition'}:{event.get('source_id')}:{champion}"
            item=publish(state,key=key,date=date,category="Competiciones",importance=5,
                headline=f"{team_name(champion)} conquista {name}",detail="El título queda registrado en el palmarés de esta partida.",entity={"team_id":champion,"competition_id":event.get("source_id"),"competition_kind":event.get("competition_kind") or "league"},cause=cause)
        elif kind=="season_rollover":
            item=publish(state,key=key,date=date,category="Temporada",importance=5,
                headline=f"Comienza la temporada {event.get('to_season')}",
                detail=f"La {event.get('from_season')} queda archivada con sus campeones, ascensos, descensos y plazas europeas.")
        elif kind=="international_friendly":
            item=publish(state,key=key,date=date,category="Selecciones",importance=2,
                headline=f"{event.get('home_name')} {event.get('home_goals')}-{event.get('away_goals')} {event.get('away_name')}",detail="Amistoso generado dentro de la carrera.")
        elif kind=="incoming_transfer_offer":
            pid=int(event.get("player_id") or 0); buyer=int(event.get("buyer_team_id") or 0)
            item=publish(state,key=key,date=date,category="Mercado",importance=2,
                headline=f"{team_name(buyer)} pregunta por {player_name(pid)}",detail="Hay una oferta que requiere decisión del mánager.",entity={"player_id":pid,"team_id":buyer})
        elif kind=="scouting_report_ready":
            pid=int(event.get("player_id") or 0)
            item=publish(state,key=key,date=date,category="Scouting",importance=2,
                headline=f"Informe listo: {player_name(pid)}",
                detail=f"{event.get('responsible') or 'El cuerpo técnico'} completa el seguimiento con {int(event.get('confidence') or 0)}% de confianza.",
                entity={"player_id":pid})
        elif kind=="training_injury":
            pid=int(event.get("player_id") or 0); days=int(event.get("expected_days") or 0)
            item=publish(state,key=key,date=date,category="Área médica",importance=3 if days>=14 else 2,
                headline=f"{player_name(pid)} se lesiona en el entrenamiento",
                detail=f"{event.get('injury') or 'Problemas físicos'} durante {event.get('session') or 'la sesión'}; la primera estimación es de {days} días.",
                entity={"player_id":pid})
        elif kind=="manager_change":
            tid=int(event.get("team_id") or 0)
            old=str(event.get("from_manager_name") or "el anterior entrenador")
            new=str(event.get("to_manager_name") or "un nuevo entrenador")
            item=publish(state,key=key,date=date,category="Entrenadores",importance=4,
                headline=f"{team_name(tid)} cambia de entrenador",
                detail=f"{old} deja el cargo y {new} toma el equipo. El cambio afectará al sistema y a las prioridades de plantilla.",
                entity={"team_id":tid,"manager_id":event.get("to_manager_id")})
        elif kind=="financial_restructuring":
            tid=int(event.get("team_id") or 0); amount=int(event.get("amount") or 0)
            item=publish(state,key=key,date=date,category="Economía",importance=4,
                headline=f"{team_name(tid)} reestructura su deuda",
                detail=f"El club necesita {amount:,} ptas. de financiación para sostener su operativa. La presión económica tendrá consecuencias deportivas.".replace(",","."),
                entity={"team_id":tid})
        elif kind=="board_sale_pressure":
            tid=int(event.get("team_id") or 0); remaining=int(event.get("remaining") or event.get("required_income") or 0)
            item=publish(state,key=key,date=date,category="Club",importance=4,
                headline=f"El consejo de {team_name(tid)} pide una venta",
                detail=f"La situación financiera obliga a generar {remaining:,} ptas. antes de ampliar el gasto.".replace(",","."),
                entity={"team_id":tid})
        elif kind=="board_sale_pressure_resolved":
            tid=int(event.get("team_id") or 0)
            item=publish(state,key=key,date=date,category="Club",importance=3,
                headline=f"{team_name(tid)} cubre la exigencia de ingresos",
                detail="La venta realizada cierra la presión extraordinaria del consejo y devuelve margen al proyecto.",entity={"team_id":tid})
        elif kind=="career_record":
            record=str(event.get("record") or "")
            if record=="biggest_win":
                item=publish(state,key=key,date=date,category="Tu etapa",importance=4,
                    headline="Nueva mayor victoria de tu etapa",
                    detail=f"{event.get('result')} ante {event.get('opponent_name')}. {event.get('competition')} ya tiene una nueva referencia para tu carrera.",
                    entity={"team_id":state.get("team_id"),"opponent_id":event.get("opponent_id")})
            elif record in {"longest_win_streak","longest_unbeaten_streak"}:
                value=int(event.get("value") or 0); label=str(event.get("label") or "racha")
                item=publish(state,key=key,date=date,category="Tu etapa",importance=4 if value>=10 else 3,
                    headline=f"{value} {label}",
                    detail="La racha entra entre los hitos de tu etapa y seguirá viva hasta que el campo diga lo contrario.",
                    entity={"team_id":state.get("team_id")})
        if item: created.append(item)
    return created


def publish_managed_match(state: dict[str, Any], *, date: str, competition: str,
                          home_name: str, away_name: str, home_goals: int, away_goals: int,
                          controlled_team_id: int, home_team_id: int, away_team_id: int) -> dict[str, Any] | None:
    mine = home_goals if controlled_team_id == home_team_id else away_goals
    theirs = away_goals if controlled_team_id == home_team_id else home_goals
    importance = 4 if abs(home_goals-away_goals)>=3 else 3
    category = "Partidos"
    key=f"managed:{date}:{competition}:{home_team_id}:{away_team_id}:{home_goals}:{away_goals}"
    return publish(state,key=key,date=date,category=category,importance=importance,
        headline=f"{home_name} {home_goals}-{away_goals} {away_name}",
        detail=("Victoria importante para tu equipo." if mine>theirs else "Empate para tu equipo." if mine==theirs else "Derrota que tendrá consecuencias en la clasificación."),
        entity={"team_id":controlled_team_id})
