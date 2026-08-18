from __future__ import annotations

"""V1.0-G · season-transition health, summer briefing and save compaction.

The career can run for decades, but the player should experience each July as a
small number of comprehensible decisions.  This module keeps the two concerns
connected: it measures whether the football world remains operational and
produces the compact briefing shown to the human manager.
"""

import json
from typing import Any

from .career_ai import squad_audit
from .career_economy import effective_contract
from .position_roles import MINIMUM_SENIOR_SQUAD_SIZE_9394

FULL_HISTORY_SEASONS = 12
TRANSITION_HISTORY_LIMIT = 40
AI_CONTRACT_LOG_LIMIT = 3000
AI_TRANSFER_LOG_LIMIT = 4000
OPERATIONAL_LOG_LIMITS = {
    "economy_ledger": 720,
    "contract_history": 720,
    "transfer_history": 720,
    "international_history": 800,
    "processed_months": 420,
}


def ensure_longitudinal_health_state(state: dict[str, Any]) -> None:
    state.setdefault("longitudinal_health", [])
    state.setdefault("summer_briefing", None)
    state.setdefault("longitudinal_compaction", {"runs": 0, "last_season": None})

    # Pre-G saves kept only the latest 20 manager recaps even though the
    # canonical season archive remained complete.  Recover those summaries on
    # load so a 30-season career never appears to have "forgotten" its first
    # decade merely because an old UI retention limit was reached.
    archives=list(state.get("season_archive") or [])
    recaps=list(state.get("season_recaps") or [])
    if archives:
        by_season={str(row.get("season") or ""):dict(row) for row in recaps if row.get("season")}
        repaired=[]
        for archive in archives[-60:]:
            season=str(archive.get("season") or "")
            row=by_season.get(season)
            if row is None:
                managed=dict(archive.get("managed_club") or {})
                if managed:
                    managed.setdefault("season",season)
                    managed["recovered_from_archive"]=True
                    row=managed
            if row is not None:
                repaired.append(row)
        archive_seasons={str(row.get("season") or "") for row in archives[-60:]}
        repaired.extend(row for row in recaps if str(row.get("season") or "") not in archive_seasons)
        if len(repaired)>len(recaps) or any(str(a.get("season") or "")!=str(b.get("season") or "") for a,b in zip(repaired,recaps)):
            state["season_recaps"]=repaired[-60:]


def _slim_honour(row: dict[str, Any]) -> dict[str, Any]:
    keys=("season","competition_kind","source_id","competition_name","team_id","team_name","champion_manager")
    return {key: row.get(key) for key in keys if row.get(key) is not None}


def _slim_movement(row: dict[str, Any]) -> dict[str, Any]:
    keys=("team_id","team_name","reason","from_league_id","to_league_id")
    return {key: row.get(key) for key in keys if row.get(key) is not None}


def _slim_recap(row: dict[str, Any] | None) -> dict[str, Any]:
    row=dict(row or {})
    board=dict(row.get("board") or {})
    keys=(
        "season","team_id","team_name","league_id","league_name","position","points","played",
        "wins","draws","losses","goals_for","goals_against","qualified_for","headline",
        "top_scorer","player_of_season",
    )
    slim={key: row.get(key) for key in keys if row.get(key) is not None}
    if board:
        slim["board"]={key: board.get(key) for key in ("score","label","risk") if board.get(key) is not None}
    slim["titles"]=[_slim_honour(x) for x in row.get("titles") or []]
    slim["history_compacted"]=True
    return slim


def compact_long_career_state(state: dict[str, Any], *, season: str) -> dict[str, Any]:
    """Bound operational growth while preserving canonical long-term history.

    Recent seasons stay rich. Older seasons keep the facts needed by History,
    honours and manager trajectory, but no longer duplicate complete league
    tables and award payloads that already exist in the canonical honours ledger.
    """
    ensure_longitudinal_health_state(state)
    changed={"archives":0,"recaps":0,"dossiers":0,"logs":0}

    archives=state.get("season_archive") or []
    cutoff=max(0,len(archives)-FULL_HISTORY_SEASONS)
    for index in range(cutoff):
        row=archives[index]
        if row.get("history_compacted"):
            continue
        row["league_table_summaries"]={
            str(lid): {
                "team_count": len(table or []),
                "champion": dict((table or [{}])[0]) if table else None,
                "bottom": [dict(x) for x in (table or [])[-3:]],
            }
            for lid,table in (row.get("league_tables") or {}).items()
        }
        row["league_tables"]={}
        row["honours"]=[_slim_honour(x) for x in row.get("honours") or []]
        row["movements"]=[_slim_movement(x) for x in row.get("movements") or []]
        row["managed_club"]=_slim_recap(row.get("managed_club"))
        row["history_compacted"]=True
        changed["archives"]+=1

    recaps=state.get("season_recaps") or []
    cutoff=max(0,len(recaps)-FULL_HISTORY_SEASONS)
    for index in range(cutoff):
        row=recaps[index]
        if row.get("history_compacted"):
            continue
        compacted=_slim_recap(row)
        # Keep the season's health verdict so History can still explain whether
        # that summer was clean decades later without retaining the full UI
        # briefing and duplicated champion/award payloads.
        health=dict(row.get("world_health") or {})
        if health:
            compacted["world_health"]={key:health.get(key) for key in ("date","season","status","active_clubs","squad_min","squad_median","squad_max","coverage_failures","negative_cash_ratio","save_megabytes","transition_ms") if health.get(key) is not None}
        recaps[index]=compacted
        changed["recaps"]+=1

    dossiers=state.get("season_dossiers") or []
    cutoff=max(0,len(dossiers)-FULL_HISTORY_SEASONS)
    for index in range(cutoff):
        row=dossiers[index]
        if row.get("history_compacted"):
            continue
        row["league_tables"]={}
        row["league_awards"]={}
        row["champions"]=[_slim_honour(x) for x in row.get("champions") or []]
        row["movements"]=[_slim_movement(x) for x in row.get("movements") or []]
        row["managed_recap"]=_slim_recap(row.get("managed_recap"))
        row["history_compacted"]=True
        changed["dossiers"]+=1

    before=len(state.get("ai_contract_history") or [])
    state["ai_contract_history"]=(state.get("ai_contract_history") or [])[-AI_CONTRACT_LOG_LIMIT:]
    changed["logs"]+=max(0,before-len(state["ai_contract_history"]))
    before=len(state.get("ai_transfer_history") or [])
    state["ai_transfer_history"]=(state.get("ai_transfer_history") or [])[-AI_TRANSFER_LOG_LIMIT:]
    changed["logs"]+=max(0,before-len(state["ai_transfer_history"]))
    for key,limit in OPERATIONAL_LOG_LIMITS.items():
        before=len(state.get(key) or [])
        state[key]=(state.get(key) or [])[-limit:]
        changed["logs"]+=max(0,before-len(state[key]))

    root=state["longitudinal_compaction"]
    root["runs"]=int(root.get("runs") or 0)+1
    root["last_season"]=str(season)
    root["last_changes"]=changed
    return changed


def _state_size_bytes(state: dict[str, Any]) -> int:
    return len(json.dumps(state, ensure_ascii=False, separators=(",",":"), default=str).encode("utf-8"))


def _contract_risk(runtime: Any, team_id: int, next_year: int) -> tuple[int,list[str]]:
    rows=runtime._career_players_by_team.get(int(team_id),[])
    count=0; names=[]
    for player in rows:
        pid=str(int(player["source_id"]))
        overall=int(runtime.state.get("player_development",{}).get(pid,{}).get("overall") or player.get("overall") or player.get("category") or 60)
        contract=effective_contract(player,overall=overall,override=runtime.state.get("contract_overrides",{}).get(pid))
        if int(contract.get("end_year") or 9999)<=int(next_year):
            count+=1
            if len(names)<4:
                names.append(str(player.get("display_name") or player.get("surname1") or f"Jugador {pid}"))
    return count,names


def build_summer_briefing(runtime: Any, *, from_season: str, to_season: str, date_text: str) -> dict[str, Any]:
    team_id=int(runtime.state["team_id"])
    squad=runtime._career_players_by_team.get(team_id,[])
    audit=squad_audit(squad,runtime.state.get("player_development") or {})
    contract_count,contract_names=_contract_risk(runtime,team_id,runtime.current_date.year+1)
    economy=runtime.economy_snapshot()
    health=dict(economy.get("health") or {})
    preseason=runtime.preseason_snapshot()
    priorities=[]
    if len(squad)<MINIMUM_SENIOR_SQUAD_SIZE_9394 or not audit.get("coverage_ok"):
        priorities.append({"priority":"high","kind":"squad","label":"Completar la plantilla","detail":f"Plantilla: {len(squad)} jugadores. Necesidad principal: {audit.get('primary_need') or 'profundidad'}.","action":"squad"})
    if contract_count:
        priorities.append({"priority":"high" if contract_count>=5 else "medium","kind":"contracts","label":f"Revisar {contract_count} contratos","detail":", ".join(contract_names)+(f" y {contract_count-len(contract_names)} más" if contract_count>len(contract_names) else ""),"action":"squad"})
    if str(health.get("label") or "") in {"Vigilancia","Crisis"}:
        priorities.append({"priority":"high" if health.get("label")=="Crisis" else "medium","kind":"economy","label":"Revisar la economía","detail":f"Salud financiera: {health.get('label')} ({health.get('score','—')}/100).","action":"economy"})
    if not priorities:
        priorities.append({"priority":"low","kind":"planning","label":"Planificar el verano","detail":"La estructura del club está sana; puedes centrarte en mejorar la plantilla y preparar la temporada.","action":"market"})

    checklist=[
        {"key":"season","label":"Temporada archivada","status":"done","detail":f"{from_season} queda cerrada y {to_season} ya está activa.","action":"history"},
        {"key":"squad","label":"Plantilla","status":"attention" if not audit.get("coverage_ok") or len(squad)<MINIMUM_SENIOR_SQUAD_SIZE_9394 else "ready","detail":f"{len(squad)} jugadores · {audit.get('primary_need') or 'cobertura suficiente'}","action":"squad"},
        {"key":"contracts","label":"Contratos","status":"attention" if contract_count else "ready","detail":f"{contract_count} vencen antes de julio de {runtime.current_date.year+1}" if contract_count else "Sin vencimientos inmediatos","action":"squad"},
        {"key":"economy","label":"Economía","status":"attention" if str(health.get('label')) in {'Vigilancia','Crisis'} else "ready","detail":f"{health.get('label','—')} · {int(economy.get('transfer_room') or 0):,} ptas. de margen".replace(",","."),"action":"economy"},
        {"key":"market","label":"Mercado","status":"active","detail":str(runtime.transfer_period_snapshot().get("label") or "Mercado de verano"),"action":"market"},
        {"key":"preseason","label":"Pretemporada","status":"ready" if preseason.get("friendlies") else "attention","detail":f"{len(preseason.get('friendlies') or [])} amistosos · liga desde {preseason.get('first_league_match')}","action":"calendar"},
    ]
    return {
        "date":date_text,"from_season":from_season,"season":to_season,"team_id":team_id,
        "headline":f"{to_season}: el nuevo proyecto ya está en marcha",
        "summary":"El verano está preparado. Atiende sólo los puntos que requieren una decisión; el resto del mundo continúa en segundo plano.",
        "checklist":checklist,"priorities":priorities[:4],"action_required":sum(1 for x in priorities if x["priority"] in {"high","medium"}),
    }


def build_world_health(runtime: Any, *, from_season: str, to_season: str, date_text: str, transition_ms: int | None = None) -> dict[str, Any]:
    state=runtime.state;ensure_longitudinal_health_state(state)
    active=[int(tid) for tid in runtime._active_club_ids()]
    squad_sizes=[]; coverage_failures=[]
    for tid in active:
        rows=runtime._career_players_by_team.get(tid,[])
        squad_sizes.append(len(rows))
        if tid==int(state["team_id"]):
            audit=squad_audit(rows,state.get("player_development") or {})
            if not audit.get("coverage_ok") or len(rows)<MINIMUM_SENIOR_SQUAD_SIZE_9394:
                coverage_failures.append(tid)
    oversized=sum(1 for size in squad_sizes if int(size)>25)
    latest_audit=(state.get("ai_squad_audits") or [])[-1] if state.get("ai_squad_audits") else {}
    ai_fail=max(0,int(latest_audit.get("club_count") or 0)-int(latest_audit.get("coverage_ok") or 0))
    coverage_failure_count=ai_fail+len(coverage_failures)

    finances=[state.get("club_finances",{}).get(str(tid),{}) for tid in active]
    negative=sum(1 for row in finances if int(row.get("cash") or 0)<0)
    max_cash=max((int(row.get("cash") or 0) for row in finances),default=0)
    max_debt=max((int(row.get("debt") or 0) for row in finances),default=0)
    save_bytes=_state_size_bytes(state)
    previous=(state.get("longitudinal_health") or [])[-1] if state.get("longitudinal_health") else None
    growth=save_bytes-int(previous.get("save_bytes") or save_bytes) if previous else None

    issues=[]
    if coverage_failure_count:
        issues.append({"severity":"critical","code":"squad_coverage","detail":f"{coverage_failure_count} clubes quedan por debajo de la cobertura operativa."})
    if active and oversized/len(active)>=.10:
        issues.append({"severity":"warning","code":"oversized_squads","detail":f"{oversized}/{len(active)} clubes superan 25 jugadores; el verano debe seguir normalizando plantillas."})
    if active and negative/len(active)>=.20:
        issues.append({"severity":"critical","code":"financial_collapse","detail":f"{negative}/{len(active)} clubes tienen caja negativa."})
    elif active and negative/len(active)>=.10:
        issues.append({"severity":"warning","code":"financial_pressure","detail":f"{negative}/{len(active)} clubes tienen caja negativa."})
    if max_cash>=2_500_000_000:
        issues.append({"severity":"warning","code":"cash_runaway","detail":f"Caja máxima fuera de escala: {max_cash:,} ptas.".replace(",",".")})
    if growth is not None and growth>2_500_000:
        issues.append({"severity":"warning","code":"save_growth","detail":f"El save creció {growth/1_000_000:.1f} MB en una temporada."})
    if transition_ms is not None and transition_ms>12_000:
        issues.append({"severity":"warning","code":"summer_latency","detail":f"La transición de verano consumió {transition_ms/1000:.1f} s."})
    status="critical" if any(x["severity"]=="critical" for x in issues) else "warning" if issues else "healthy"
    return {
        "date":date_text,"from_season":from_season,"season":to_season,"status":status,"issues":issues,
        "active_clubs":len(active),"squad_min":min(squad_sizes) if squad_sizes else 0,"squad_median":sorted(squad_sizes)[len(squad_sizes)//2] if squad_sizes else 0,"squad_max":max(squad_sizes) if squad_sizes else 0,"oversized_squads":oversized,
        "coverage_failures":coverage_failure_count,"negative_cash_clubs":negative,"negative_cash_ratio":round(negative/max(1,len(active)),4),"max_cash":max_cash,"max_debt":max_debt,
        "save_bytes":save_bytes,"save_megabytes":round(save_bytes/1_000_000,2),"growth_bytes":growth,"transition_ms":transition_ms,
        "history":{"seasons":len(state.get("season_archive") or []),"dossiers":len(state.get("season_dossiers") or []),"honours":len(state.get("honours") or []),"news":len(state.get("news_feed") or []),"world_events":len(state.get("world_events") or [])},
    }


def finalize_summer_transition(runtime: Any, *, from_season: str, date_text: str, transition_ms: int | None = None) -> dict[str, Any]:
    state=runtime.state;to_season=str(state.get("season") or "")
    compact_long_career_state(state,season=to_season)
    briefing=build_summer_briefing(runtime,from_season=from_season,to_season=to_season,date_text=date_text)
    health=build_world_health(runtime,from_season=from_season,to_season=to_season,date_text=date_text,transition_ms=transition_ms)
    state["summer_briefing"]=briefing
    state["longitudinal_health"].append(health);state["longitudinal_health"]=state["longitudinal_health"][-TRANSITION_HISTORY_LIMIT:]
    log=state.get("season_transition_log") or []
    if log and str(log[-1].get("to_season") or "")==to_season:
        log[-1]["health"]=health
        log[-1]["summer_briefing"]={"action_required":briefing["action_required"],"priority_count":len(briefing["priorities"])}
    recaps=state.get("season_recaps") or []
    if recaps and str(recaps[-1].get("season") or "")==str(from_season):
        recaps[-1]["next_season_briefing"]=briefing
        recaps[-1]["world_health"]=health
    return {"briefing":briefing,"health":health}
