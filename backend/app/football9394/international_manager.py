from __future__ import annotations

"""P9 · user international career layer on top of the persistent club world."""

from datetime import date
from random import Random
from typing import Any

from .national_teams import national_team_catalog, select_national_squad


def ensure_international_manager_state(state: dict[str, Any]) -> None:
    state.setdefault("international_manager", {
        "country_id": None, "country_name": None, "reputation": 50.0,
        "offers": [], "selected_player_ids": [], "history": [], "started_on": None,
    })
    state.setdefault("international_tournaments", [])


def generate_national_job_offers(state: dict[str, Any], universe: Any, *, day: date, manager_reputation: float, seed: int) -> list[dict[str, Any]]:
    ensure_international_manager_state(state)
    current=(state["international_manager"] or {}).get("country_id")
    catalog=national_team_catalog(universe)
    rng=Random(int(seed)^day.toordinal()^0x1994)
    rows=[]
    for item in catalog:
        if current and int(item.country_id)==int(current): continue
        prestige=max(35.0,min(95.0,float(item.average_top_22)))
        gap=abs(prestige-float(manager_reputation))
        if prestige>float(manager_reputation)+18: continue
        score=100-gap*1.4+rng.random()*5
        rows.append((score,item))
    rows.sort(key=lambda pair:(-pair[0],pair[1].name))
    offers=[{"id":f"nt-job:{day.isoformat()}:{row.country_id}","date":day.isoformat(),"country_id":int(row.country_id),"country_name":row.name,"squad_level":row.average_top_22,"status":"open","reason":f"La federación busca un técnico de reputación {round(float(manager_reputation),1)} para un bloque de nivel {row.average_top_22}."} for _,row in rows[:3]]
    state["international_manager"]["offers"]=offers
    return offers


def accept_national_job(state: dict[str, Any], universe: Any, offer_id: str, *, day: date, development: dict[str,dict[str,Any]]|None=None) -> dict[str, Any]:
    ensure_international_manager_state(state)
    job=state["international_manager"]
    offer=next((row for row in job.get("offers") or [] if str(row.get("id"))==str(offer_id) and row.get("status")=="open"),None)
    if offer is None: raise KeyError("oferta de selección no disponible")
    for row in job.get("offers") or []: row["status"]="accepted" if row is offer else "expired"
    cid=int(offer["country_id"])
    squad=select_national_squad(universe,cid,development=development)
    job.update({"country_id":cid,"country_name":offer["country_name"],"started_on":day.isoformat(),"selected_player_ids":[int(p["id"]) for p in squad],"offers":[]})
    event={"kind":"national_job_started","date":day.isoformat(),"country_id":cid,"country_name":offer["country_name"]}
    job.setdefault("history",[]).append(event)
    return event


def resign_national_job(state: dict[str, Any], *, day: date) -> dict[str, Any]:
    ensure_international_manager_state(state);job=state["international_manager"]
    if not job.get("country_id"): raise ValueError("no diriges ninguna selección")
    event={"kind":"national_job_resigned","date":day.isoformat(),"country_id":int(job["country_id"]),"country_name":job.get("country_name")}
    job.setdefault("history",[]).append(event);job.update({"country_id":None,"country_name":None,"started_on":None,"selected_player_ids":[]})
    return event


def set_national_selection(state: dict[str, Any], universe: Any, player_ids: list[int], *, development: dict[str,dict[str,Any]]|None=None) -> list[int]:
    ensure_international_manager_state(state);job=state["international_manager"]
    cid=job.get("country_id")
    if not cid: raise ValueError("no diriges ninguna selección")
    eligible_rows=select_national_squad(universe,int(cid),development=development,size=60)
    allowed={int(p["id"]) for p in eligible_rows}
    ids=[int(pid) for pid in player_ids]
    if len(ids)!=22 or len(set(ids))!=22: raise ValueError("la convocatoria debe tener exactamente 22 jugadores distintos")
    if any(pid not in allowed for pid in ids): raise ValueError("hay jugadores no elegibles para esta selección")
    # Require the same broad balance used by automatic squads.
    broad={"POR":0,"DEF":0,"MED":0,"DEL":0}
    selected={int(p["id"]):p for p in eligible_rows}
    for pid in ids:
        key=str((selected.get(pid) or {}).get("broad_position") or "MED").upper()
        if key not in broad: key="MED"
        broad[key]+=1
    if broad["POR"]<2 or broad["DEF"]<5 or broad["MED"]<5 or broad["DEL"]<3: raise ValueError("la convocatoria necesita al menos 2 POR, 5 DEF, 5 MED y 3 DEL")
    job["selected_player_ids"]=ids
    return ids


def update_international_reputation(state: dict[str, Any], *, country_id: int, goals_for: int, goals_against: int, tournament: bool=False, stage: str|None=None) -> float:
    ensure_international_manager_state(state);job=state["international_manager"]
    if int(job.get("country_id") or 0)!=int(country_id): return float(job.get("reputation") or 50)
    delta=1.6 if goals_for>goals_against else .25 if goals_for==goals_against else -1.0
    if tournament: delta*=1.7
    if stage in {"quarterfinal","semifinal","final"}: delta+=.8
    job["reputation"]=round(max(1.0,min(100.0,float(job.get("reputation") or 50)+delta)),2)
    return float(job["reputation"])


def international_manager_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    ensure_international_manager_state(state)
    snap=dict(state["international_manager"])
    snap["job_offers"]=list(snap.get("offers") or [])
    snap["selection"]=list(snap.get("selected_player_ids") or [])
    return snap


def ensure_international_player_stats(state: dict[str, Any]) -> None:
    state.setdefault("international_player_stats", {})


def record_international_player_match(
    state: dict[str, Any], *, result: Any, home_sheet: Any, away_sheet: Any,
    date_text: str, competition: str, tournament: bool = False, stage: str | None = None,
) -> None:
    """Persist real caps/contributions for the eternal historical cast."""
    ensure_international_player_stats(state)
    store=state["international_player_stats"]
    events=list(result.events)
    for sheet in (home_sheet,away_sheet):
        team_id=str(sheet.team_id)
        country_id=int(team_id.split(":",1)[1]) if team_id.startswith("NT:") else None
        starters={str(p.id) for p in sheet.starters}
        appeared=set(starters)
        # Substitution events store the incoming player as player_id.
        appeared.update(str(e.player_id) for e in events if str(e.team_id)==team_id and e.kind in {"substitution","injury_substitution"} and e.player_id)
        goals={};assists={}
        for e in events:
            if str(e.team_id)!=team_id or not e.player_id: continue
            pid=str(e.player_id)
            if e.kind=="goal": goals[pid]=goals.get(pid,0)+1
            elif e.kind=="assist": assists[pid]=assists.get(pid,0)+1
        for pid in appeared:
            row=store.setdefault(pid,{"caps":0,"starts":0,"goals":0,"assists":0,"tournament_caps":0,"tournament_goals":0,"countries":{},"history":[]})
            row["caps"]+=1;row["starts"]+=1 if pid in starters else 0;row["goals"]+=goals.get(pid,0);row["assists"]+=assists.get(pid,0)
            if tournament:
                row["tournament_caps"]+=1;row["tournament_goals"]+=goals.get(pid,0)
            if country_id is not None:
                row["countries"][str(country_id)]=int(row["countries"].get(str(country_id),0))+1
            opponent=away_sheet.team_name if sheet is home_sheet else home_sheet.team_name
            gf=int(result.home.goals if sheet is home_sheet else result.away.goals);ga=int(result.away.goals if sheet is home_sheet else result.home.goals)
            row["history"].append({"date":date_text,"competition":competition,"stage":stage,"opponent":opponent,"result":f"{gf}-{ga}","started":pid in starters,"goals":goals.get(pid,0),"assists":assists.get(pid,0)})
            row["history"]=row["history"][-80:]
