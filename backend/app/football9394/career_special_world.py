from __future__ import annotations

"""Incremental APSL, J.League and Brasileirão state inside a persistent career.

The format is historical; the exact fixture dates are currently a deterministic
career cadence because the mixed-era MDB does not provide a trustworthy 1993
calendar for these competitions.  That distinction is persisted and surfaced.
"""

from datetime import date, timedelta
from random import Random
from typing import Any

from .brazil_runtime import BRAZIL_1993_GROUPS, HISTORICAL_REPAIR_CLUBS, _group_rules, _synthetic_sheet
from .calendar_cycle import shift_reference_date
from .knockout import KnockoutLeg9394, KnockoutRoundRules9394, resolve_knockout_tie
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394
from .schedule import generate_round_robin_cycles
from .special_league_runtime import DecidedMatch9394, _resolve_no_draw, _special_table
from .standings import LeagueMatch9394, build_league_table
from .team_builder import build_snapshot_team_sheet_with_repair

SPECIAL_CALENDAR_FIDELITY = "historical_format_runtime_cadence_dates_not_source_authoritative"


def _iso(d: date) -> str: return d.isoformat()


def ensure_special_competitions(state: dict[str, Any]) -> dict[str, Any]:
    block=state.setdefault("special_competitions",{})
    block.setdefault("47",{
        "kind":"brazil_serie_a_1993","source_id":47,"name":"Série A","stage":"first_phase","completed_round":0,
        "first_results":{"A":[],"B":[],"C":[],"D":[]},"intermediate":[],"second_results":{"E":[],"F":[]},"final_legs":[],
        "champion_team_id":None,"runner_up_team_id":None,"completed":False,"events":[],"calendar_fidelity":SPECIAL_CALENDAR_FIDELITY,
    })
    block.setdefault("111",{
        "kind":"jleague_1993","source_id":111,"name":"J. League","stage":"suntory","completed_round":0,
        "suntory_results":[],"nicos_results":[],"suntory_winner":None,"suntory_runner_up":None,"nicos_winner":None,"nicos_runner_up":None,
        "championship_teams":[],"championship_legs":[],"champion_team_id":None,"runner_up_team_id":None,"completed":False,"events":[],
        "calendar_fidelity":SPECIAL_CALENDAR_FIDELITY,
    })
    block.setdefault("120",{
        "kind":"apsl_1993","source_id":120,"name":"APSL","stage":"regular","completed_round":0,"regular_results":[],
        "semifinals":[],"final":None,"champion_team_id":None,"runner_up_team_id":None,"completed":False,"events":[],
        "calendar_fidelity":SPECIAL_CALENDAR_FIDELITY,
    })
    return block


def _strength(runtime, team_id: str) -> float:
    if str(team_id) in HISTORICAL_REPAIR_CLUBS:
        return 62.0
    try:
        rows=runtime._career_players_by_team.get(int(team_id),[])
    except (TypeError,ValueError):
        rows=[]
    vals=sorted((int(runtime.state["player_development"].get(str(p["source_id"]),{}).get("overall") or p.get("overall") or p.get("category") or 60) for p in rows),reverse=True)[:11]
    return (sum(vals)/len(vals)) if vals else 60.0


def _fast_score(runtime, home_id: str, away_id: str, *, seed: int, no_draw: bool=False, golden_goal: bool=False) -> dict[str,Any]:
    rng=Random(seed)
    edge=(_strength(runtime,home_id)-_strength(runtime,away_id))/18.0 + .16
    hg=max(0,round(rng.random()*2.35 + max(-.45,min(.8,edge))))
    ag=max(0,round(rng.random()*2.05 - max(-.5,min(.5,edge/2))))
    winner=None; decided="regulation"
    if no_draw:
        if hg==ag:
            p_home=max(.30,min(.70,.5+(_strength(runtime,home_id)-_strength(runtime,away_id))/120))
            winner=home_id if rng.random()<p_home else away_id
            decided="extra_time" if rng.random() < (.46 if golden_goal else .38) else "shootout"
        else:
            winner=home_id if hg>ag else away_id
    return {"home_team_id":home_id,"away_team_id":away_id,"home_goals":hg,"away_goals":ag,"winner_team_id":winner,"decided_by":decided,"bootstrap":True}


def _full_score(runtime, home_id: str, away_id: str, *, seed: int, no_draw: bool=False, golden_goal: bool=False) -> dict[str,Any]:
    if home_id in HISTORICAL_REPAIR_CLUBS:
        home=_synthetic_sheet(home_id,HISTORICAL_REPAIR_CLUBS[home_id])
    else:
        home,_=build_snapshot_team_sheet_with_repair(runtime._career_universe,int(home_id))
        home=type(home)(home.team_id,home.team_name,tuple(runtime._apply_development_to_footballer(p) for p in home.starters),tuple(runtime._apply_development_to_footballer(p) for p in home.bench),home.tactics)
    if away_id in HISTORICAL_REPAIR_CLUBS:
        away=_synthetic_sheet(away_id,HISTORICAL_REPAIR_CLUBS[away_id])
    else:
        away,_=build_snapshot_team_sheet_with_repair(runtime._career_universe,int(away_id))
        away=type(away)(away.team_id,away.team_name,tuple(runtime._apply_development_to_footballer(p) for p in away.starters),tuple(runtime._apply_development_to_footballer(p) for p in away.bench),away.tactics)
    engine=FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)
    result=engine.simulate(home,away,seed=seed)
    runtime._apply_match_player_state(result,home,away,seed)
    row={"home_team_id":home_id,"away_team_id":away_id,"home_goals":result.home.goals,"away_goals":result.away.goals,"bootstrap":False}
    if no_draw:
        decided=_resolve_no_draw(result,home,away,seed=seed,golden_goal=golden_goal)
        row.update({"winner_team_id":decided.winner_team_id,"decided_by":decided.decided_by})
    return row


def _score(runtime, home_id: str, away_id: str, *, seed: int, bootstrap: bool, no_draw: bool=False, golden_goal: bool=False) -> dict[str,Any]:
    return (_fast_score(runtime,home_id,away_id,seed=seed,no_draw=no_draw,golden_goal=golden_goal) if bootstrap
            else _full_score(runtime,home_id,away_id,seed=seed,no_draw=no_draw,golden_goal=golden_goal))


def _league_group_table(ids: list[str] | tuple[str,...], rows: list[dict[str,Any]], rules) -> tuple:
    matches=[LeagueMatch9394(str(r["home_team_id"]),str(r["away_team_id"]),int(r["home_goals"]),int(r["away_goals"])) for r in rows]
    return build_league_table(tuple(map(str,ids)),matches,rules)


def _decided_rows(rows: list[dict[str,Any]]) -> tuple[DecidedMatch9394,...]:
    out=[]
    for r in rows:
        winner=str(r["winner_team_id"]); home=str(r["home_team_id"]); away=str(r["away_team_id"])
        out.append(DecidedMatch9394(home,away,int(r["home_goals"]),int(r["away_goals"]),winner,away if winner==home else home,str(r.get("decided_by") or "regulation")))
    return tuple(out)


def _brazil_first_tables(state: dict[str,Any]) -> dict[str,tuple]:
    return {g:_league_group_table(BRAZIL_1993_GROUPS[g],state["first_results"][g],_group_rules(g,8,14)) for g in "ABCD"}


def _campaign_key(row) -> tuple[int,int,int,int]:
    return (row.points,row.wins,row.goal_difference,row.goals_for)


def _resolve_two_leg(rows: list[dict[str,Any]], *, advantage: str | None=None, away_goals: bool=False) -> tuple[str,str,str]:
    a=str(rows[0]["home_team_id"]); b=str(rows[0]["away_team_id"])
    leg1=KnockoutLeg9394(a,b,int(rows[0]["home_goals"]),int(rows[0]["away_goals"]))
    leg2=KnockoutLeg9394(b,a,int(rows[1]["home_goals"]),int(rows[1]["away_goals"]))
    resolution=resolve_knockout_tie(leg1,KnockoutRoundRules9394("Eliminatoria",2,away_goals=away_goals,extra_time=True,penalties=True),leg2)
    if resolution.winner_team_id:
        return resolution.winner_team_id,resolution.loser_team_id,resolution.resolved_by or "aggregate"
    if advantage:
        return advantage,b if advantage==a else a,"better_campaign_draw_advantage"
    # deterministic fallback for a declared extra-time/penalty decider.  It is
    # not an extra hidden league rule; the round explicitly permits the decider.
    seed=sum(ord(ch) for ch in a+b)+sum(int(r["home_goals"])+int(r["away_goals"]) for r in rows)
    winner=a if Random(seed).random()<.5 else b
    return winner,b if winner==a else a,resolution.pending_decider or "extra_time_penalties"


def _process_brazil(runtime, day: date, *, bootstrap: bool) -> list[dict[str,Any]]:
    s=runtime.state["special_competitions"]["47"]
    if s["completed"]: return []
    events=[]; seed0=int(runtime.state["seed"])*100000+470000
    first_start=shift_reference_date(runtime.state,date(1993,9,5))
    if s["stage"]=="first_phase":
        due=min(14,max(0,((day-first_start).days//7)+1)) if day>=first_start else 0
        fixtures={g:generate_round_robin_cycles(BRAZIL_1993_GROUPS[g],2) for g in "ABCD"}
        while s["completed_round"]<due:
            rnd=s["completed_round"]+1
            for gi,g in enumerate("ABCD"):
                for idx,f in enumerate([x for x in fixtures[g] if x.round_number==rnd]):
                    row=_score(runtime,f.home_team_id,f.away_team_id,seed=seed0+rnd*100+gi*10+idx,bootstrap=bootstrap)
                    row["round"]=rnd; row["group"]=g; s["first_results"][g].append(row)
            s["completed_round"]=rnd
            events.append({"kind":"competition_round","source_id":47,"stage":"first_phase","round":rnd,"date":_iso(day),"bootstrap":bootstrap})
        if s["completed_round"]>=14:
            s["stage"]="intermediate_leg1"; s["completed_round"]=0
    if s["stage"].startswith("intermediate"):
        tables=_brazil_first_tables(s)
        c1,c2=tables["C"][0].team_id,tables["C"][1].team_id; d1,d2=tables["D"][0].team_id,tables["D"][1].team_id
        pairs=((c1,d2),(c2,d1))
        leg1_date=first_start+timedelta(days=14*7+7); leg2_date=leg1_date+timedelta(days=7)
        if s["stage"]=="intermediate_leg1" and day>=leg1_date:
            s["intermediate"]=[]
            for idx,(a,b) in enumerate(pairs):
                row=_score(runtime,a,b,seed=seed0+20000+idx,bootstrap=bootstrap); row["leg"]=1
                s["intermediate"].append({"team_a":a,"team_b":b,"legs":[row]})
            s["stage"]="intermediate_leg2"; events.append({"kind":"competition_stage","source_id":47,"stage":"intermediate_leg1","date":_iso(day),"bootstrap":bootstrap})
        if s["stage"]=="intermediate_leg2" and day>=leg2_date:
            for idx,tie in enumerate(s["intermediate"]):
                a,b=tie["team_a"],tie["team_b"]
                row=_score(runtime,b,a,seed=seed0+20100+idx,bootstrap=bootstrap); row["leg"]=2; tie["legs"].append(row)
                first_rows={r.team_id:r for table in tables.values() for r in table}
                advantage=a if _campaign_key(first_rows[a])>_campaign_key(first_rows[b]) else b
                winner,loser,resolved=_resolve_two_leg(tie["legs"],advantage=advantage)
                tie.update({"winner_team_id":winner,"loser_team_id":loser,"resolved_by":resolved})
            a1,a2,a3=[r.team_id for r in tables["A"][:3]]; b1,b2,b3=[r.team_id for r in tables["B"][:3]]
            w1,w2=s["intermediate"][0]["winner_team_id"],s["intermediate"][1]["winner_team_id"]
            s["second_groups"]={"E":[a1,a3,b2,w1],"F":[b1,b3,a2,w2]}; s["stage"]="second_phase"; s["completed_round"]=0
            events.append({"kind":"competition_stage","source_id":47,"stage":"intermediate_complete","date":_iso(day),"bootstrap":bootstrap})
    if s["stage"]=="second_phase":
        start=first_start+timedelta(days=14*7+21)
        due=min(6,max(0,((day-start).days//4)+1)) if day>=start else 0
        fixtures={g:generate_round_robin_cycles(tuple(s["second_groups"][g]),2) for g in "EF"}
        while s["completed_round"]<due:
            rnd=s["completed_round"]+1
            for gi,g in enumerate("EF"):
                for idx,f in enumerate([x for x in fixtures[g] if x.round_number==rnd]):
                    row=_score(runtime,f.home_team_id,f.away_team_id,seed=seed0+30000+rnd*100+gi*10+idx,bootstrap=bootstrap); row["round"]=rnd; row["group"]=g
                    s["second_results"][g].append(row)
            s["completed_round"]=rnd; events.append({"kind":"competition_round","source_id":47,"stage":"second_phase","round":rnd,"date":_iso(day),"bootstrap":bootstrap})
        if s["completed_round"]>=6:
            s["stage"]="final_leg1"; s["completed_round"]=0
    if s["stage"].startswith("final"):
        first_tables=_brazil_first_tables(s)
        second_tables={g:_league_group_table(s["second_groups"][g],s["second_results"][g],_group_rules(g,4,6)) for g in "EF"}
        a,b=second_tables["E"][0].team_id,second_tables["F"][0].team_id
        final1=first_start+timedelta(days=14*7+21+6*4+7); final2=final1+timedelta(days=7)
        if s["stage"]=="final_leg1" and day>=final1:
            s["final_legs"]=[{**_score(runtime,a,b,seed=seed0+40000,bootstrap=bootstrap),"leg":1}];s["stage"]="final_leg2"
            events.append({"kind":"competition_stage","source_id":47,"stage":"final_leg1","date":_iso(day),"bootstrap":bootstrap})
        if s["stage"]=="final_leg2" and day>=final2:
            s["final_legs"].append({**_score(runtime,b,a,seed=seed0+40001,bootstrap=bootstrap),"leg":2})
            first_rows={r.team_id:r for table in first_tables.values() for r in table}; second_rows={r.team_id:r for table in second_tables.values() for r in table}
            def combined(t):
                x,y=first_rows[t],second_rows[t]; return (x.points+y.points,x.wins+y.wins,x.goal_difference+y.goal_difference,x.goals_for+y.goals_for)
            advantage=a if combined(a)>combined(b) else b
            winner,loser,resolved=_resolve_two_leg(s["final_legs"],advantage=advantage)
            s.update({"champion_team_id":winner,"runner_up_team_id":loser,"final_resolved_by":resolved,"completed":True,"stage":"completed"})
            events.append({"kind":"competition_completed","source_id":47,"champion_team_id":winner,"date":_iso(day),"bootstrap":bootstrap})
    s["events"].extend(events); return events


def _process_jleague(runtime, day: date, *, bootstrap: bool) -> list[dict[str,Any]]:
    s=runtime.state["special_competitions"]["111"]
    if s["completed"]: return []
    teams=[str(t["source_id"]) for t in runtime._teams_for_league(111)]; fixtures=generate_round_robin_cycles(tuple(teams),2)
    seed0=int(runtime.state["seed"])*100000+111000; events=[]
    stage_dates={"suntory":shift_reference_date(runtime.state,date(1993,5,15)),"nicos":shift_reference_date(runtime.state,date(1993,9,18))}
    for stage in ("suntory","nicos"):
        if s["stage"]!=stage: continue
        start=stage_dates[stage]; due=min(18,max(0,((day-start).days//7)+1)) if day>=start else 0
        rows=s[f"{stage}_results"]
        while s["completed_round"]<due:
            rnd=s["completed_round"]+1
            for idx,f in enumerate([x for x in fixtures if x.round_number==rnd]):
                row=_score(runtime,f.home_team_id,f.away_team_id,seed=seed0+(0 if stage=="suntory" else 20000)+rnd*100+idx,bootstrap=bootstrap,no_draw=True,golden_goal=True);row["round"]=rnd
                rows.append(row)
            s["completed_round"]=rnd;events.append({"kind":"competition_round","source_id":111,"stage":stage,"round":rnd,"date":_iso(day),"bootstrap":bootstrap})
        if s["completed_round"]>=18:
            table=_special_table(teams,_decided_rows(rows),apsl=False)
            s[f"{stage}_winner"]=table[0].team_id;s[f"{stage}_runner_up"]=table[1].team_id
            if stage=="suntory": s["stage"]="nicos";s["completed_round"]=0
            else: s["stage"]="championship_setup";s["completed_round"]=0
    if s["stage"]=="championship_setup" and day>=shift_reference_date(runtime.state,date(1994,1,22)):
        first,second=s["suntory_winner"],s["nicos_winner"]
        if first==second:
            a,b=s["suntory_runner_up"],s["nicos_runner_up"]
            deciding=_score(runtime,a,b,seed=seed0+50000,bootstrap=bootstrap,no_draw=True,golden_goal=True)
            second=deciding["winner_team_id"]
            s["contender_playoff"]=deciding
        s["championship_teams"]=[first,second];s["stage"]="championship_leg1"
        events.append({"kind":"competition_stage","source_id":111,"stage":"championship_setup","date":_iso(day),"bootstrap":bootstrap})
    if s["stage"]=="championship_leg1" and day>=shift_reference_date(runtime.state,date(1994,1,29)):
        a,b=s["championship_teams"];s["championship_legs"]=[{**_score(runtime,a,b,seed=seed0+51000,bootstrap=bootstrap),"leg":1}];s["stage"]="championship_leg2"
        events.append({"kind":"competition_stage","source_id":111,"stage":"championship_leg1","date":_iso(day),"bootstrap":bootstrap})
    if s["stage"]=="championship_leg2" and day>=shift_reference_date(runtime.state,date(1994,2,5)):
        a,b=s["championship_teams"];s["championship_legs"].append({**_score(runtime,b,a,seed=seed0+51001,bootstrap=bootstrap),"leg":2})
        winner,loser,resolved=_resolve_two_leg(s["championship_legs"],advantage=None)
        s.update({"champion_team_id":winner,"runner_up_team_id":loser,"championship_resolved_by":resolved,"completed":True,"stage":"completed"})
        events.append({"kind":"competition_completed","source_id":111,"champion_team_id":winner,"date":_iso(day),"bootstrap":bootstrap})
    s["events"].extend(events);return events


def _process_apsl(runtime, day: date, *, bootstrap: bool) -> list[dict[str,Any]]:
    s=runtime.state["special_competitions"]["120"]
    if s["completed"]: return []
    teams=[str(t["source_id"]) for t in runtime._teams_for_league(120)];fixtures=generate_round_robin_cycles(tuple(teams),4)
    start=shift_reference_date(runtime.state,date(1993,5,1));due=min(28,max(0,((day-start).days//5)+1)) if day>=start else 0;seed0=int(runtime.state["seed"])*100000+120000;events=[]
    if s["stage"]=="regular":
        while s["completed_round"]<due:
            rnd=s["completed_round"]+1
            for idx,f in enumerate([x for x in fixtures if x.round_number==rnd]):
                row=_score(runtime,f.home_team_id,f.away_team_id,seed=seed0+rnd*100+idx,bootstrap=bootstrap,no_draw=True,golden_goal=False);row["round"]=rnd;s["regular_results"].append(row)
            s["completed_round"]=rnd;events.append({"kind":"competition_round","source_id":120,"stage":"regular","round":rnd,"date":_iso(day),"bootstrap":bootstrap})
        if s["completed_round"]>=28: s["stage"]="semifinals"
    if s["stage"]=="semifinals" and day>=start+timedelta(days=28*5+5):
        table=_special_table(teams,_decided_rows(s["regular_results"]),apsl=True);pairs=((table[0].team_id,table[3].team_id),(table[1].team_id,table[2].team_id));s["semifinals"]=[]
        for idx,(a,b) in enumerate(pairs):
            row=_score(runtime,a,b,seed=seed0+40000+idx,bootstrap=bootstrap,no_draw=True);s["semifinals"].append(row)
        s["stage"]="final";events.append({"kind":"competition_stage","source_id":120,"stage":"semifinals","date":_iso(day),"bootstrap":bootstrap})
    if s["stage"]=="final" and day>=start+timedelta(days=28*5+12):
        a,b=s["semifinals"][0]["winner_team_id"],s["semifinals"][1]["winner_team_id"];row=_score(runtime,a,b,seed=seed0+41000,bootstrap=bootstrap,no_draw=True)
        s.update({"final":row,"champion_team_id":row["winner_team_id"],"runner_up_team_id":b if row["winner_team_id"]==a else a,"completed":True,"stage":"completed"})
        events.append({"kind":"competition_completed","source_id":120,"champion_team_id":s["champion_team_id"],"date":_iso(day),"bootstrap":bootstrap})
    s["events"].extend(events);return events


def process_special_competitions(runtime, day: date, *, bootstrap: bool=False) -> list[dict[str,Any]]:
    ensure_special_competitions(runtime.state)
    events=[]
    events.extend(_process_apsl(runtime,day,bootstrap=bootstrap))
    events.extend(_process_jleague(runtime,day,bootstrap=bootstrap))
    events.extend(_process_brazil(runtime,day,bootstrap=bootstrap))
    if not bootstrap:
        runtime._rebuild_rosters()
    return events


def special_competition_snapshot(runtime) -> dict[str,Any]:
    ensure_special_competitions(runtime.state)
    out={}
    for key,s in runtime.state["special_competitions"].items():
        out[key]={
            "source_id":int(key),"name":s["name"],"stage":s["stage"],"completed_round":int(s.get("completed_round") or 0),
            "completed":bool(s.get("completed")),"champion_team_id":s.get("champion_team_id"),"event_count":len(s.get("events") or []),
            "calendar_fidelity":s.get("calendar_fidelity"),
        }
    return out
