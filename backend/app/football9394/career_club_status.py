from __future__ import annotations

"""Dynamic club stature for the persistent 1993-94 career.

A club starts from its historical snapshot context but its stature is not a
permanent label.  Results, trophies, European qualification, squad quality and
financial health move the score gradually from season to season.  This score is
consumed by board expectations and recruitment so a long save can genuinely
change the football hierarchy without one freak season turning a modest club
into a superpower overnight.
"""

from typing import Any, Callable


def _tier(score: float) -> str:
    if score >= 92: return "GIGANTE"
    if score >= 82: return "GRANDE"
    if score >= 70: return "FUERTE"
    if score >= 52: return "MEDIO"
    if score >= 38: return "MODESTO"
    return "PEQUEÑO"


def _percentile(value: float, values: list[float]) -> float:
    if not values: return .5
    below=sum(1 for x in values if x < value)
    equal=sum(1 for x in values if x == value)
    return (below + max(0,equal-1)*.5) / max(1,len(values)-1)


def initialise_club_status(*, state: dict[str,Any], active_team_ids: list[int], team_getter: Callable[[int],dict[str,Any]|None], strength_getter: Callable[[int],float]) -> None:
    store=state.setdefault("club_status",{})
    strengths={tid:float(strength_getter(tid)) for tid in active_team_ids}
    members={tid:float((team_getter(tid) or {}).get("members") or 0) for tid in active_team_ids}
    budgets={tid:float((team_getter(tid) or {}).get("budget") or 0) for tid in active_team_ids}
    svals=list(strengths.values()); mvals=list(members.values()); bvals=list(budgets.values())
    for tid in active_team_ids:
        key=str(int(tid))
        if key in store: continue
        team=team_getter(tid) or {}
        league=team.get("league") or {}
        level=int(league.get("level") or team.get("league_level") or 1)
        previous=int(team.get("league_position") or 99)
        strength_p=_percentile(strengths[tid],svals)
        fan_p=_percentile(members[tid],mvals)
        budget_p=_percentile(budgets[tid],bvals)
        historical=max(0.0,min(1.0,(22-previous)/21)) if previous < 90 else .35
        division=max(.20,1.0-(max(1,level)-1)*.18)
        score=25 + 31*strength_p + 18*fan_p + 14*budget_p + 7*historical + 5*division
        score=max(20.0,min(95.0,score))
        store[key]={"score":round(score,1),"tier":_tier(score),"trend":0.0,"history":[],"initial_score":round(score,1)}


def club_status(state: dict[str,Any], team_id:int) -> dict[str,Any]:
    row=dict((state.get("club_status") or {}).get(str(int(team_id))) or {"score":50.0,"tier":"MEDIO","trend":0.0,"history":[]})
    row.setdefault("score",50.0);row.setdefault("tier",_tier(float(row["score"])));row.setdefault("trend",0.0);row.setdefault("history",[])
    return row


def update_after_season(*, state:dict[str,Any], season:str, tables:dict[int,list[dict[str,Any]]], honours:list[dict[str,Any]], qualifiers:dict[str,list[int]], team_league_getter:Callable[[int],int|None], league_level_getter:Callable[[int],int]|None=None, finances:dict[str,dict[str,Any]], squad_strength_getter:Callable[[int],float]) -> list[dict[str,Any]]:
    """Move stature gradually while keeping football hierarchy relative.

    Club stature is allowed to change substantially over a long career, but
    prestige is not money that can be printed by the whole football world.
    Seasonal movement is therefore calculated in two passes: first from each
    club's sporting/economic season, then centred around the active population.
    Established giants also have diminishing upside (and tiny clubs diminishing
    downside), which avoids a decade ending with dozens of clubs pinned at the
    98-point ceiling while still allowing sustained success to create a new
    major club.
    """
    european={int(tid) for ids in qualifiers.values() for tid in ids}
    # Success is contextual: a lower-division title is important, but it cannot
    # create the same worldwide stature as winning a strong top flight.  Derive
    # league prestige from the historical stature of its current membership and
    # damp it further by division level.
    league_prestige:dict[int,float]={}
    for lid,table in tables.items():
        initial=[float((state.get("club_status") or {}).get(str(int(r.get("team_id") or 0)),{}).get("initial_score") or 50.0) for r in table]
        avg=sum(initial)/len(initial) if initial else 50.0
        prestige=max(.35,min(1.0,.45+(avg-45.0)*.018))
        level=int(league_level_getter(int(lid)) if league_level_getter is not None else 1)
        prestige*= {1:1.0,2:.58,3:.34}.get(level,.28)
        league_prestige[int(lid)]=max(.20,min(1.0,prestige))
    title_weight:dict[int,float]={}
    for h in honours:
        tid=int(h.get("team_id") or 0);kind=str(h.get("competition_kind") or "")
        weight=league_prestige.get(int(h.get("source_id") or 0),.65) if kind=="league" else .75
        title_weight[tid]=max(title_weight.get(tid,0.0),weight)
    planned:list[dict[str,Any]]=[]
    for key,row in (state.get("club_status") or {}).items():
        tid=int(key);old=float(row.get("score") or 50.0);delta=0.0
        lid=team_league_getter(tid);table=tables.get(int(lid)) if lid is not None else None
        if table:
            found=next((r for r in table if int(r.get("team_id") or 0)==tid),None)
            if found:
                n=max(2,len(table));pos=int(found.get("position") or n)
                percentile=(n-pos)/(n-1)
                context=league_prestige.get(int(lid),.65)
                delta += (percentile-.5)*2.35*context
                if pos==1: delta+=.55*context
                if pos>=n-2: delta-=.65*max(.55,context)
        if tid in title_weight: delta+=1.15*title_weight[tid]
        if tid in european: delta+=.40
        fin=finances.get(str(tid)) or {}
        cash=float(fin.get("cash") or 0);debt=float(fin.get("debt") or 0)
        if debt>0 and cash < debt*.12: delta-=.65
        if cash > max(5_000_000,debt*.65): delta+=.20
        quality=float(squad_strength_getter(tid))
        if quality>=78: delta+=.22
        elif quality<62: delta-=.28
        initial=float(row.get("initial_score") or old)
        # Historical stature remains a source of inertia, not a permanent caste.
        delta += (initial-old)*0.050
        delta=max(-2.8,min(2.8,delta))
        planned.append({"tid":tid,"row":row,"old":old,"raw_delta":delta})

    # Prestige is relative. Remove the global seasonal drift so a good decade
    # creates winners *and* losers instead of inflating every tier at once.
    mean_delta=(sum(float(item["raw_delta"]) for item in planned)/len(planned)) if len(planned)>1 else 0.0
    changes=[]
    for item in planned:
        tid=int(item["tid"]);row=item["row"];old=float(item["old"])
        delta=float(item["raw_delta"])-mean_delta
        if delta>0:
            # Above 82, every extra reputation point is increasingly difficult.
            # A decade of elite results can still turn a strong club into a
            # giant, but established giants do not all pile up at 98.
            headroom=max(0.0,98.0-old)
            delta*=max(.22,min(1.0,headroom/16.0))
        elif delta<0 and old<38:
            # Symmetric floor resistance keeps a bad spell from erasing a club.
            footroom=max(0.0,old-15.0)
            delta*=max(.30,min(1.0,footroom/23.0))
        delta=max(-2.8,min(2.8,delta))
        new=max(15.0,min(98.0,old+delta))
        history=list(row.get("history") or [])
        history.append({"season":season,"score_before":round(old,1),"score_after":round(new,1),"change":round(new-old,1),"tier_before":_tier(old),"tier_after":_tier(new)})
        row.update({"score":round(new,1),"tier":_tier(new),"trend":round(new-old,1),"history":history[-20:]})
        changes.append({"team_id":tid,"score_before":round(old,1),"score_after":round(new,1),"change":round(new-old,1),"tier_before":_tier(old),"tier_after":_tier(new)})
    return changes


def attraction_modifier(state:dict[str,Any], *, from_team_id:int, to_team_id:int) -> float:
    """Salary multiplier required for a move based on club stature.

    Downward moves require a premium; upward moves can be attractive at a small
    discount.  Kept deliberately bounded so money/football quality still matter.
    """
    origin=float(club_status(state,from_team_id).get("score") or 50) if from_team_id else 42.0
    target=float(club_status(state,to_team_id).get("score") or 50)
    diff=target-origin
    return max(.88,min(1.22,1.0-diff*.005))
