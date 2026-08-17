from __future__ import annotations

"""P4 dressing-room depth without dialogue minigames.

The squad reacts to football facts: captaincy, leadership, competition for
places, important injuries/departures and mentoring. The neutral player rating
is never rewritten here; effects land on morale, satisfaction, relationship and
slow evidence-driven development.
"""

from datetime import date
from typing import Any, Iterable

from .career_memory import adjust_player_manager_relationship, relationship_api
from .player_identity import age_on
from .position_roles import role_for_player
from .squad_dynamics import dynamics_api


def ensure_dressing_room_state(state: dict[str, Any]) -> None:
    state.setdefault("dressing_room", {})
    room = state["dressing_room"]
    room.setdefault("captain_id", None)
    room.setdefault("leadership_group", [])
    room.setdefault("mentorships", {})
    room.setdefault("events", [])
    room.setdefault("competition_history", [])
    room.setdefault("role_promises", {})
    room.setdefault("promise_archive", [])


def _dev(state: dict[str, Any], pid: int) -> dict[str, Any]:
    return state.setdefault("player_development", {}).setdefault(str(int(pid)), {})


def _overall(state: dict[str, Any], player: dict[str, Any]) -> int:
    return int(_dev(state, int(player["source_id"])).get("overall") or player.get("overall") or player.get("category") or 60)


def _leadership_score(state: dict[str, Any], player: dict[str, Any]) -> float:
    pid = int(player["source_id"])
    attrs = player.get("attributes") or {}
    leadership = int(attrs.get("leadership") or 60)
    consistency = int(attrs.get("consistency") or 60)
    affection = int(player.get("fan_affection") or 0)
    dyn = dynamics_api(state, pid)
    trust = int(relationship_api(state, pid).get("trust") or 55)
    morale = int(_dev(state, pid).get("morale") or 70)
    return round(leadership * .38 + consistency * .15 + _overall(state, player) * .17 + affection * 2.1 + trust * .09 + morale * .08, 2)


def sync_dressing_room(state: dict[str, Any], *, players: Iterable[dict[str, Any]], game_date: date) -> dict[str, Any]:
    ensure_dressing_room_state(state)
    rows = list(players)
    room = state["dressing_room"]
    if not rows:
        room["captain_id"] = None
        room["leadership_group"] = []
        room["mentorships"] = {}
        return room

    ranked = sorted(rows, key=lambda p: (-_leadership_score(state, p), -_overall(state, p), int(p["source_id"])))
    ids = {int(p["source_id"]) for p in rows}
    captain = room.get("captain_id")
    if not isinstance(captain, int) or captain not in ids:
        captain = int(ranked[0]["source_id"])
        room["captain_id"] = captain
    room["leadership_group"] = [int(p["source_id"]) for p in ranked[: min(5, len(ranked))]]

    # Mentoring only uses the historical cast. In frozen-age careers a young
    # player remains the same chronological age, but can still mature as a
    # footballer through experience and guidance.
    leaders = [p for p in ranked[:5] if int(p["source_id"]) != captain or len(ranked) > 1]
    candidates = sorted(rows, key=lambda p: ((age_on(p, date(1993, 10, 23)) or 30), _overall(state, p)))
    mentorships: dict[str, int] = {}
    used: set[int] = set()
    for prospect in candidates:
        age = age_on(prospect, date(1993, 10, 23))
        if age is None or age > 23:
            continue
        pslot = role_for_player(prospect).squad_slot
        mentor = next((m for m in leaders if int(m["source_id"]) not in used and (age_on(m, date(1993,10,23)) or 0) >= 26 and role_for_player(m).squad_slot == pslot), None)
        if mentor is None:
            mentor = next((m for m in leaders if int(m["source_id"]) not in used and (age_on(m, date(1993,10,23)) or 0) >= 27), None)
        if mentor:
            mentorships[str(int(prospect["source_id"]))] = int(mentor["source_id"])
            used.add(int(mentor["source_id"]))
    room["mentorships"] = mentorships
    return room


def set_captain(state: dict[str, Any], *, player_id: int, players: Iterable[dict[str, Any]], date_text: str) -> dict[str, Any]:
    ensure_dressing_room_state(state)
    ids = {int(p["source_id"]) for p in players}
    pid = int(player_id)
    if pid not in ids:
        raise ValueError("el capitán debe pertenecer a la plantilla")
    previous = state["dressing_room"].get("captain_id")
    state["dressing_room"]["captain_id"] = pid
    if isinstance(previous, int) and previous != pid:
        adjust_player_manager_relationship(state, player_id=previous, date_text=date_text, delta=-3, reason="pierde la capitanía")
    adjust_player_manager_relationship(state, player_id=pid, date_text=date_text, delta=4, reason="confianza como capitán")
    _event(state, {"kind":"captain_change","date":date_text,"player_id":pid,"previous_player_id":previous})
    return {"captain_id": pid, "previous_player_id": previous}



ROLE_PROMISE_START_SHARE = {
    "Figura": 0.78,
    "Titular": 0.62,
    "Rotación": 0.34,
    "Promesa": 0.24,
    "Fondo de plantilla": 0.14,
}


def set_role_promise(state: dict[str, Any], *, player_id: int, role: str, players: Iterable[dict[str, Any]], date_text: str) -> dict[str, Any]:
    """Agree a football role and let subsequent match selection judge it.

    A role promise never edits player ability.  It is deliberately a commitment
    about usage, so the only evidence is what the manager actually does in
    official matches.
    """
    ensure_dressing_room_state(state)
    pid = int(player_id)
    ids = {int(p["source_id"]) for p in players}
    if pid not in ids:
        raise ValueError("el jugador debe pertenecer a tu plantilla")
    role = str(role or "").strip()
    if role not in ROLE_PROMISE_START_SHARE:
        raise ValueError("rol acordado no válido")
    current = (state["dressing_room"].get("role_promises") or {}).get(str(pid))
    if current and current.get("status") in {"active", "on_track", "at_risk"}:
        archived = {**current, "status": "superseded", "closed_on": date_text}
        state["dressing_room"]["promise_archive"].append(archived)
    promise = {
        "player_id": pid, "role": role, "date": date_text,
        "window_matches": 8, "team_matches": 0, "starts": 0,
        "expected_start_share": ROLE_PROMISE_START_SHARE[role],
        "status": "active", "last_eval_matches": 0,
    }
    state["dressing_room"]["role_promises"][str(pid)] = promise
    adjust_player_manager_relationship(state, player_id=pid, date_text=date_text, delta=1, reason=f"acuerda rol: {role}")
    _event(state, {"kind": "role_promise", "date": date_text, "player_id": pid, "role": role})
    return dict(promise)


def role_promise_api(state: dict[str, Any], player_id: int) -> dict[str, Any] | None:
    ensure_dressing_room_state(state)
    row = (state["dressing_room"].get("role_promises") or {}).get(str(int(player_id)))
    if not row:
        return None
    matches = int(row.get("team_matches") or 0)
    starts = int(row.get("starts") or 0)
    share = round(starts / matches, 3) if matches else 0.0
    return {**row, "actual_start_share": share, "remaining_matches": max(0, int(row.get("window_matches") or 8) - matches)}


def _update_role_promises(state: dict[str, Any], *, starter_ids: set[int], date_text: str) -> None:
    ensure_dressing_room_state(state)
    room = state["dressing_room"]
    promises = room.get("role_promises") or {}
    for key, row in list(promises.items()):
        if row.get("status") not in {"active", "on_track", "at_risk"}:
            continue
        pid = int(row.get("player_id") or key)
        row["team_matches"] = int(row.get("team_matches") or 0) + 1
        if pid in starter_ids:
            row["starts"] = int(row.get("starts") or 0) + 1
        matches = int(row["team_matches"]); starts = int(row.get("starts") or 0)
        expected = float(row.get("expected_start_share") or 0.0)
        share = starts / matches if matches else 0.0
        # The promise window is eight official matches. Mid-window feedback is
        # deliberately mild: the player notices risk, but only the final
        # outcome creates a major relationship consequence.
        if matches in {4, 6} and int(row.get("last_eval_matches") or 0) < matches:
            if share + 0.20 < expected:
                row["status"] = "at_risk"
                adjust_player_manager_relationship(state, player_id=pid, date_text=date_text, delta=-2, reason=f"rol {row['role']} en riesgo")
                dyn = state.setdefault("player_dynamics", {}).setdefault(str(pid), {})
                dyn["satisfaction"] = max(0, min(100, int(dyn.get("satisfaction") or 70) - 3))
            else:
                row["status"] = "on_track"
            row["last_eval_matches"] = matches
        if matches >= int(row.get("window_matches") or 8):
            kept = share + 0.08 >= expected
            row["status"] = "kept" if kept else "broken"
            row["closed_on"] = date_text
            row["actual_start_share"] = round(share, 3)
            adjust_player_manager_relationship(state, player_id=pid, date_text=date_text, delta=4 if kept else -7, reason=(f"cumple rol {row['role']}" if kept else f"incumple rol {row['role']}"))
            dyn = state.setdefault("player_dynamics", {}).setdefault(str(pid), {})
            dyn["satisfaction"] = max(0, min(100, int(dyn.get("satisfaction") or 70) + (4 if kept else -8)))
            if not kept and int(dyn.get("satisfaction") or 70) <= 42:
                dyn["wants_move"] = True
            room["promise_archive"].append(dict(row))
            _event(state, {"kind": "role_promise_resolved", "date": date_text, "player_id": pid, "role": row["role"], "status": row["status"], "actual_start_share": round(share, 3)})
    room["promise_archive"] = room["promise_archive"][-120:]



def close_role_promises_on_manager_exit(state: dict[str, Any], *, date_text: str, voluntary: bool = False) -> list[dict[str, Any]]:
    """Close unresolved commitments when the manager leaves the club.

    A dismissal is not treated as the manager breaking his word. A voluntary
    departure is remembered as an interrupted promise and therefore carries a
    modest trust cost that can matter in a future reencounter.
    """
    ensure_dressing_room_state(state)
    room = state["dressing_room"]
    closed=[]
    for row in (room.get("role_promises") or {}).values():
        if row.get("status") not in {"active", "on_track", "at_risk"}:
            continue
        pid=int(row.get("player_id") or 0)
        row["status"] = "interrupted" if voluntary else "closed_by_dismissal"
        row["closed_on"] = date_text
        if voluntary and pid:
            adjust_player_manager_relationship(state, player_id=pid, date_text=date_text, delta=-4, reason=f"abandona el club con rol {row.get('role')} pendiente")
        room["promise_archive"].append(dict(row)); closed.append(dict(row))
        _event(state,{"kind":"role_promise_interrupted","date":date_text,"player_id":pid,"role":row.get("role"),"voluntary":bool(voluntary)})
    room["promise_archive"] = room["promise_archive"][-120:]
    return closed

def _event(state: dict[str, Any], row: dict[str, Any]) -> None:
    ensure_dressing_room_state(state)
    state["dressing_room"]["events"].append(row)
    state["dressing_room"]["events"] = state["dressing_room"]["events"][-120:]


def _slot_competitions(state: dict[str, Any], players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for p in players:
        buckets.setdefault(role_for_player(p).squad_slot, []).append(p)
    out=[]
    for slot, rows in buckets.items():
        ranked=sorted(rows,key=lambda p:(-(_overall(state,p)+int(_dev(state,int(p['source_id'])).get('form') or 70)*.08),int(p['source_id'])))
        if len(ranked)<2: continue
        a,b=ranked[0],ranked[1]
        gap=abs(_overall(state,a)-_overall(state,b))
        form_gap=abs(int(_dev(state,int(a['source_id'])).get('form') or 70)-int(_dev(state,int(b['source_id'])).get('form') or 70))
        if gap<=6 or form_gap>=10:
            out.append({"slot":slot,"incumbent_id":int(a['source_id']),"challenger_id":int(b['source_id']),"overall_gap":gap,"form_gap":form_gap,"heat":max(1,min(100,72-gap*8+min(24,form_gap)))})
    return sorted(out,key=lambda r:-int(r['heat']))


def update_after_match(state: dict[str, Any], *, players: Iterable[dict[str, Any]], starter_ids: Iterable[int|str], won: bool, drew: bool, date_text: str) -> None:
    rows=list(players); room=sync_dressing_room(state,players=rows,game_date=date.fromisoformat(date_text))
    starters={int(x) for x in starter_ids if str(x).isdigit()}
    _update_role_promises(state, starter_ids=starters, date_text=date_text)
    leaders=[int(x) for x in room.get('leadership_group') or []]
    captain=int(room.get('captain_id') or 0)
    captain_trust=int(relationship_api(state,captain).get('trust') or 55) if captain else 55
    # Strong aligned leadership dampens adversity; fractured leadership spreads it.
    group_delta=0
    if not won and not drew:
        group_delta = 1 if captain_trust>=72 else -1 if captain_trust<=38 else 0
    elif won and captain_trust>=70:
        group_delta=1
    if group_delta:
        for p in rows:
            pid=int(p['source_id']); dyn=state.setdefault('player_dynamics',{}).setdefault(str(pid),{})
            dyn['satisfaction']=max(0,min(100,int(dyn.get('satisfaction') or 70)+group_delta))
    # Mentoring creates a very small permanent evidence pulse when both are in
    # the match environment; enough to matter over years, never enough to farm.
    for protege, mentor in (room.get('mentorships') or {}).items():
        if int(mentor) in starters or int(protege) in starters:
            d=_dev(state,int(protege)); d['development_points']=round(float(d.get('development_points') or 0.0)+0.025,4)
            d['morale']=min(100,int(d.get('morale') or 70)+1)
    competitions=_slot_competitions(state,rows)
    room['competition_history'].append({'date':date_text,'rows':competitions[:8]})
    room['competition_history']=room['competition_history'][-20:]


def register_important_departure(state: dict[str, Any], *, player_id: int, players_before: Iterable[dict[str, Any]], date_text: str) -> None:
    rows=list(players_before); room=sync_dressing_room(state,players=rows,game_date=date.fromisoformat(date_text))
    pid=int(player_id)
    promise=(room.get('role_promises') or {}).get(str(pid))
    if promise and promise.get('status') in {'active','on_track','at_risk'}:
        promise['status']='broken';promise['closed_on']=date_text;promise['reason']='sale_during_commitment'
        adjust_player_manager_relationship(state,player_id=pid,date_text=date_text,delta=-7,reason=f"venta con rol {promise.get('role')} pendiente")
        room['promise_archive'].append(dict(promise))
        _event(state,{'kind':'role_promise_resolved','date':date_text,'player_id':pid,'role':promise.get('role'),'status':'broken','reason':'sale'})
    influence=int((state.get('player_dynamics') or {}).get(str(pid),{}).get('influence') or 0)
    if influence < 65 and pid not in set(room.get('leadership_group') or []):
        return
    captain=int(room.get('captain_id') or 0); stability=int(relationship_api(state,captain).get('trust') or 55) if captain else 55
    delta=-1 if stability>=70 else -3
    for p in rows:
        other=int(p['source_id'])
        if other==pid: continue
        d=_dev(state,other); d['morale']=max(0,min(100,int(d.get('morale') or 70)+delta))
        dyn=state.setdefault('player_dynamics',{}).setdefault(str(other),{}); dyn['satisfaction']=max(0,min(100,int(dyn.get('satisfaction') or 70)+delta))
    _event(state,{'kind':'important_departure','date':date_text,'player_id':pid,'squad_delta':delta,'captain_stability':stability})


def register_important_injury(state: dict[str, Any], *, player_id: int, days: int, players: Iterable[dict[str, Any]], date_text: str) -> None:
    if int(days)<14: return
    rows=list(players); sync_dressing_room(state,players=rows,game_date=date.fromisoformat(date_text))
    influence=int((state.get('player_dynamics') or {}).get(str(int(player_id)),{}).get('influence') or 0)
    if influence<70: return
    for p in rows:
        pid=int(p['source_id'])
        if pid==int(player_id): continue
        d=_dev(state,pid); d['morale']=max(0,int(d.get('morale') or 70)-1)
    _event(state,{'kind':'important_injury','date':date_text,'player_id':int(player_id),'days':int(days)})



def register_return_from_injury(state: dict[str, Any], *, player_id: int, players: Iterable[dict[str, Any]], date_text: str) -> dict[str, Any] | None:
    """Record a meaningful return without granting the player his place back.

    A long absence changes the social context: a leader can lift the group on
    return while the player who occupied the same slot now faces renewed
    competition. Selection remains entirely the manager's decision.
    """
    rows=list(players); pid=int(player_id)
    player=next((p for p in rows if int(p.get('source_id') or 0)==pid),None)
    if player is None: return None
    dev=_dev(state,pid); history=list(dev.get('injury_history') or [])
    last=history[-1] if history else {}
    days=int(last.get('days') or last.get('expected_days') or 0)
    if days < 14: return None
    room=sync_dressing_room(state,players=rows,game_date=date.fromisoformat(date_text))
    dyn=state.setdefault('player_dynamics',{}).setdefault(str(pid),{})
    dev['morale']=min(100,int(dev.get('morale') or 70)+2)
    dyn['satisfaction']=min(100,int(dyn.get('satisfaction') or 70)+1)
    slot=role_for_player(player).squad_slot
    competitors=[]
    for other in rows:
        oid=int(other.get('source_id') or 0)
        if oid==pid or role_for_player(other).squad_slot!=slot: continue
        odyn=state.setdefault('player_dynamics',{}).setdefault(str(oid),{})
        # Competition is tension, not punishment: only highly established
        # incumbents notice a small pressure pulse.
        if int(odyn.get('influence') or 0)>=55:
            odyn['satisfaction']=max(0,int(odyn.get('satisfaction') or 70)-1)
        competitors.append(oid)
    leadership=pid in set(room.get('leadership_group') or [])
    if leadership:
        for other in rows:
            oid=int(other.get('source_id') or 0)
            if oid==pid: continue
            d=_dev(state,oid); d['morale']=min(100,int(d.get('morale') or 70)+1)
    event={'kind':'important_return','date':date_text,'player_id':pid,'days_out':days,'slot':slot,'leadership_return':leadership,'competition_ids':competitors[:5]}
    _event(state,event)
    return event

def reencounters_for_opponent(state: dict[str, Any], *, opponent_players: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rels=state.get('manager_player_relationships') or {}; out=[]
    for p in opponent_players:
        pid=int(p['source_id']); row=rels.get(str(pid)) or {}
        history=list(row.get('history') or [])
        if not history: continue
        out.append({'player_id':pid,'name':p.get('display_name'),'trust':int(row.get('trust') or 55),'label':relationship_api(state,pid).get('label'),'history_count':len(history),'last_change':row.get('last_change')})
    return sorted(out,key=lambda r:(-int(r['history_count']),-abs(int(r['trust'])-55)))[:5]


def dressing_room_snapshot(state: dict[str, Any], *, players: Iterable[dict[str, Any]], game_date: date) -> dict[str, Any]:
    rows=list(players); room=sync_dressing_room(state,players=rows,game_date=game_date)
    by_id={int(p['source_id']):p for p in rows}
    leaders=[]
    for pid in room.get('leadership_group') or []:
        p=by_id.get(int(pid));
        if p: leaders.append({'player_id':int(pid),'name':p.get('display_name'),'score':_leadership_score(state,p),'captain':int(pid)==int(room.get('captain_id') or 0),'relationship':relationship_api(state,int(pid)).get('label')})
    mentorships=[]
    for protege,mentor in (room.get('mentorships') or {}).items():
        pp,mp=by_id.get(int(protege)),by_id.get(int(mentor))
        if pp and mp: mentorships.append({'protege_id':int(protege),'protege_name':pp.get('display_name'),'mentor_id':int(mentor),'mentor_name':mp.get('display_name')})
    active_promises=[]
    for key,row in (room.get('role_promises') or {}).items():
        if row.get('status') in {'active','on_track','at_risk'}:
            player=by_id.get(int(row.get('player_id') or key))
            if player:
                active_promises.append({**role_promise_api(state,int(player['source_id'])),'player_name':player.get('display_name')})
    return {'captain_id':room.get('captain_id'),'leaders':leaders,'competitions':_slot_competitions(state,rows),'mentorships':mentorships,'role_promises':active_promises,'recent_promises':list(room.get('promise_archive') or [])[-8:],'recent_events':list(room.get('events') or [])[-12:]}
