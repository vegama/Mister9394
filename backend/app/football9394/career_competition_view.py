from __future__ import annotations

"""User-facing competition navigator for the persistent career."""

from typing import Any

from .brazil_runtime import HISTORICAL_REPAIR_CLUBS
from .foreign_rules import competition_foreign_rule


def _team_name(runtime, team_id: int | str) -> str:
    raw=str(team_id or "")
    if raw in HISTORICAL_REPAIR_CLUBS: return HISTORICAL_REPAIR_CLUBS[raw]
    try: tid=int(raw)
    except (TypeError,ValueError): return raw or "—"
    row=runtime._team_api(tid) or runtime.universe.team(tid) or {}
    return str(row.get("name") or row.get("long_name") or tid)


def _result(runtime, row: dict[str, Any]) -> dict[str, Any]:
    home=row.get("home_team_id") or 0;away=row.get("away_team_id") or 0
    return {**row,"home_team":_team_name(runtime,home),"away_team":_team_name(runtime,away)}


def competition_directory(runtime) -> list[dict[str, Any]]:
    rows=[]
    for comp in runtime.universe.career_competitions():
        kind=str(comp.get("kind")); sid=int(comp["source_id"])
        if kind=="league":
            special=(runtime.state.get("special_competitions") or {}).get(str(sid))
            world=(runtime.state.get("world_leagues") or {}).get(str(sid))
            if sid==int(runtime.state.get("league_id") or 0):
                progress={"stage":f"Jornada {runtime.state.get('completed_matchday',0)}","completed":False,"result_count":len(runtime.state.get("results") or [])}
            elif special:
                progress={"stage":special.get("stage"),"completed":bool(special.get("completed")),"result_count":sum(len(v) for k,v in special.items() if k.endswith("results") and isinstance(v,list))}
            else:
                progress={"stage":f"Jornada {int((world or {}).get('completed_round') or 0)}","completed":False,"result_count":len((world or {}).get("results") or [])}
        else:
            tournament=(runtime.state.get("daily_tournaments") or {}).get(str(sid))
            progress={"stage":(tournament or {}).get("stage") or "Pendiente","completed":bool((tournament or {}).get("completed")),"result_count":len((tournament or {}).get("results") or []) + sum(len(x) for x in (((tournament or {}).get("group_results") or {}).values()))}
        champion=next((h for h in reversed(runtime.state.get("honours") or []) if h.get("competition_kind")==kind and int(h.get("source_id") or -1)==sid),None)
        rows.append({
            "kind":kind,"source_id":sid,"name":comp.get("name"),"country":comp.get("country"),"level":comp.get("level"),
            "team_count":comp.get("team_count") or comp.get("entrants"),"progress":progress,
            "last_champion":({"season":champion.get("season"),"team_id":champion.get("team_id"),"team_name":champion.get("team_name")} if champion else None),
        })
    rows.sort(key=lambda row:(0 if row["kind"]=="league" else 1,str(row.get("country") or "ZZZ"),int(row.get("level") or 99),str(row.get("name") or "")))
    return rows


def competition_detail(runtime, kind: str, source_id: int) -> dict[str, Any]:
    source_id=int(source_id); kind=str(kind)
    comp=next((c for c in runtime.universe.career_competitions() if str(c.get("kind"))==kind and int(c.get("source_id") or -1)==source_id),None)
    if comp is None: raise KeyError(f"competición {kind}:{source_id} no encontrada")
    honours=[h for h in runtime.state.get("honours") or [] if h.get("competition_kind")==kind and int(h.get("source_id") or -1)==source_id]
    foreign_rule=competition_foreign_rule(runtime.universe,kind=kind,source_id=source_id,team_id=int(runtime.state.get("team_id") or 0))
    base={"kind":kind,"source_id":source_id,"name":comp.get("name"),"country":comp.get("country"),"season":runtime.state.get("season"),"honours":honours[-20:],
        "rules":{"foreigners":foreign_rule.as_dict(),"points_for_win":(2 if kind=="league" else None)}}
    if kind=="league":
        special=(runtime.state.get("special_competitions") or {}).get(str(source_id))
        if special:
            result_lists=[]
            for key,value in special.items():
                if key.endswith("results") and isinstance(value,list): result_lists.extend(value)
                elif isinstance(value,dict) and key.endswith("results"):
                    for inner in value.values(): result_lists.extend(inner or [])
            for key in ("intermediate","final_legs","championship_legs","semifinals"):
                if isinstance(special.get(key),list): result_lists.extend(special.get(key) or [])
            if isinstance(special.get("final"),dict): result_lists.append(special["final"])
            participants=[int(t["source_id"]) for t in runtime._teams_for_league(source_id)]
            return {**base,"format":"special","stage":special.get("stage"),"completed":bool(special.get("completed")),
                "champion_team_id":special.get("champion_team_id"),"champion_team":_team_name(runtime,special.get("champion_team_id")) if special.get("champion_team_id") else None,
                "participants":[{"team_id":tid,"team_name":_team_name(runtime,tid)} for tid in participants],"standings":[],"results":[_result(runtime,r) for r in result_lists[-80:]],"calendar":[]}
        standings=runtime.league_standings(source_id)
        schedule=runtime._league_schedule(source_id)
        results=runtime._league_result_rows(source_id)
        by_pair={(int(r["home_team_id"]),int(r["away_team_id"]),int(r.get("round") or r.get("matchday") or 0)):r for r in results}
        calendar=[]
        for fx in schedule:
            found=by_pair.get((int(fx["home_team_id"]),int(fx["away_team_id"]),int(fx.get("round") or fx.get("matchday") or 0)))
            calendar.append({**_result(runtime,fx),"played":found is not None,"home_goals":found.get("home_goals") if found else None,"away_goals":found.get("away_goals") if found else None})
        progress=(runtime.state.get("world_leagues") or {}).get(str(source_id)) or {}
        completed_round=int(runtime.state.get("completed_matchday") or 0) if source_id==int(runtime.state.get("league_id") or 0) else int(progress.get("completed_round") or 0)
        return {**base,"format":"league","stage":f"Jornada {completed_round}","completed":completed_round>=max((int(x.get('round') or x.get('matchday') or 0) for x in schedule),default=0),
            "standings":standings,"results":[_result(runtime,r) for r in results[-80:]],"calendar":calendar,
            "participants":[{"team_id":int(t["source_id"]),"team_name":t.get("name")} for t in runtime._teams_for_league(source_id)]}
    tournament=(runtime.state.get("daily_tournaments") or {}).get(str(source_id))
    if tournament is None:
        return {**base,"format":"tournament","stage":"No iniciada","completed":False,"participants":[],"results":[],"ties":[],"standings":[],"calendar":[]}
    results=list(tournament.get("results") or [])
    for rows in (tournament.get("group_results") or {}).values(): results.extend(rows or [])
    ties=[]
    for tie in tournament.get("pending_ties") or []:
        ties.append({**tie,"team_a_name":_team_name(runtime,tie.get("team_a")),"team_b_name":_team_name(runtime,tie.get("team_b")),"legs":[_result(runtime,r) for r in tie.get("legs") or []]})
    ids=set(int(x) for x in tournament.get("current_ids") or [] if str(x).isdigit())
    for r in results: ids.update([int(r.get("home_team_id") or 0),int(r.get("away_team_id") or 0)])
    ids.discard(0)
    return {**base,"format":"tournament","stage":tournament.get("stage"),"completed":bool(tournament.get("completed")),
        "champion_team_id":tournament.get("champion_team_id"),"champion_team":_team_name(runtime,tournament.get("champion_team_id")) if tournament.get("champion_team_id") else None,
        "runner_up_team_id":tournament.get("runner_up_team_id"),"participants":[{"team_id":tid,"team_name":_team_name(runtime,tid)} for tid in sorted(ids)],
        "results":[_result(runtime,r) for r in results[-100:]],"ties":ties,"standings":[],"calendar":[]}
