from __future__ import annotations

"""Incremental Copa del Rey and UEFA competitions for the persistent career.

Format/rules match the certified 1993-94 runtimes.  The MDB stage pools are
source-backed; exact date fidelity is still separated from format fidelity when
no trustworthy source calendar exists.
"""

from datetime import date
from random import Random
from typing import Any

from .career_special_world import _resolve_two_leg, _score
from .calendar_cycle import shift_reference_date
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, SimulationProfile9394
from .rules import CompetitionRules9394
from .schedule import generate_round_robin_cycles
from .standings import LeagueMatch9394, build_league_table
from .foreign_rules import competition_foreign_rule
from .domestic_cups import DOMESTIC_CUPS_9394, SYNTHETIC_DOMESTIC_CUPS_9394, domestic_cup_spec, cup_participant_ids_from_state

TOURNAMENT_CALENDAR_FIDELITY="historical_format_stage_cadence_dates_not_source_authoritative"

UEFA_CUP_STAGES=(
    ("Octavos",date(1993,11,3),date(1993,11,24),2,True),
    ("Cuartos",date(1994,3,2),date(1994,3,16),2,True),
    ("Semifinales",date(1994,3,30),date(1994,4,13),2,True),
    ("Final",date(1994,4,27),date(1994,5,11),2,True),
)
CWC_STAGES=(
    ("1/16",date(1993,10,13),date(1993,11,3),2,True),
    ("Octavos",date(1993,11,24),date(1993,12,8),2,True),
    ("Cuartos",date(1994,3,2),date(1994,3,16),2,True),
    ("Semifinales",date(1994,4,6),date(1994,4,20),2,True),
    ("Final",date(1994,5,4),None,1,False),
)
COPA_STAGES=(
    ("Primera ronda",date(1993,10,27),date(1993,11,10),None,"tier3"),
    ("Segunda ronda",date(1993,11,24),date(1993,12,8),None,"tier2"),
    ("Entrada Primera",date(1994,1,5),date(1994,1,19),32,"tier1"),
    ("Dieciseisavos",date(1994,2,2),date(1994,2,16),16,None),
    ("Octavos",date(1994,3,2),date(1994,3,16),8,None),
    ("Cuartos",date(1994,3,30),date(1994,4,13),4,None),
    ("Semifinales",date(1994,4,27),date(1994,5,11),2,None),
    ("Final",date(1994,6,18),None,1,None),
)


def ensure_tournament_state(state: dict[str,Any], universe) -> dict[str,Any]:
    block=state.setdefault("daily_tournaments",{})
    for source_id,name in ((1,"Copa de Europa"),(2,"Copa de la UEFA"),(3,"Copa del Rey"),(90,"Recopa de Europa")):
        if str(source_id) in block: continue
        if source_id==3:
            current=[]
        else:
            qualified=(state.get("continental_qualifiers") or {}).get(str(source_id))
            source_pool=qualified if qualified is not None else universe.payload.get("tournament_participants",{}).get(str(source_id),())
            current=[str(i) for i in source_pool]
        block[str(source_id)]={
            "source_id":source_id,"name":name,"stage_index":0,"stage":"pending","current_ids":current,"pending_ties":[],"byes":[],
            "results":[],"group_results":{"A":[],"B":[]} if source_id==1 else None,
            "champion_team_id":None,"runner_up_team_id":None,"completed":False,"events":[],"calendar_fidelity":TOURNAMENT_CALENDAR_FIDELITY,
        }
    for spec in SYNTHETIC_DOMESTIC_CUPS_9394:
        key=str(spec.source_id)
        if key in block: continue
        current=cup_participant_ids_from_state(state,universe,spec)
        block[key]={
            "source_id":spec.source_id,"name":spec.name,"country_id":spec.country_id,"league_ids":list(spec.league_ids),
            "format_style":spec.format_style,"stage_index":0,"stage":"pending","current_ids":current,"initial_ids":list(current),
            "pending_ties":[],"byes":[],"results":[],"group_results":{} if spec.format_style=="greece_groups_two_leg" else None,
            "champion_team_id":None,"runner_up_team_id":None,"completed":False,"events":[],
            "calendar_fidelity":"historical_format_adapted_to_playable_clubs_dates_not_source_authoritative",
            "historical_note":spec.historical_note,
        }
    return block


def _pair(ids: list[str]) -> list[tuple[str,str]]:
    if len(ids)%2: raise ValueError("bracket impar sin bye preparado")
    return [(ids[i],ids[i+1]) for i in range(0,len(ids),2)]


def _prepare_reduction(ids: list[str], target: int, *, seed: int) -> tuple[list[str],list[tuple[str,str]]]:
    eliminations=len(ids)-target
    if eliminations<0 or eliminations*2>len(ids): raise ValueError(f"reducción inválida {len(ids)}->{target}")
    pool=ids[:];Random(seed).shuffle(pool)
    playing=pool[:eliminations*2];byes=pool[eliminations*2:]
    return byes,_pair(playing)


def _played_leg(runtime,a:str,b:str,*,seed:int,source_id:int,neutral:bool=False) -> dict[str,Any]:
    controlled=str(int(runtime.state["team_id"]))
    tactics=dict(runtime.state.get("tactics") or {})
    if domestic_cup_spec(int(source_id)) is not None and hasattr(runtime,"_domestic_foreign_rule"):
        home_rule=runtime._domestic_foreign_rule(int(a));away_rule=runtime._domestic_foreign_rule(int(b))
    else:
        home_rule=competition_foreign_rule(runtime.universe,kind="tournament",source_id=int(source_id),team_id=int(a))
        away_rule=competition_foreign_rule(runtime.universe,kind="tournament",source_id=int(source_id),team_id=int(b))
    home=runtime._sheet(int(a), tactics if str(a)==controlled else None, foreign_rule=home_rule)
    away=runtime._sheet(int(b), tactics if str(b)==controlled else None, foreign_rule=away_rule)
    profile=ERA_BASELINE_1993_94
    if neutral:
        profile=SimulationProfile9394(id="era_1993_94_neutral",target_goals_per_match=profile.target_goals_per_match,
            goal_conversion_multiplier=profile.goal_conversion_multiplier,notable_attack_multiplier=profile.notable_attack_multiplier,
            foul_multiplier=profile.foul_multiplier,home_advantage_rating=0.0)
    validator=(runtime._substitution_validator_for_fixture({"fixture_type":"tournament","source_id":int(source_id),"competition_id":int(source_id)}) if hasattr(runtime,"_substitution_validator_for_fixture") else None)
    result=FootballMatchEngine9394(profile=profile).simulate(home,away,seed=seed,substitution_validator=validator)
    runtime._apply_match_player_state(result,home,away,seed)
    return {"home_team_id":a,"away_team_id":b,"home_goals":result.home.goals,"away_goals":result.away.goals,"bootstrap":False}


def _single(runtime,a:str,b:str,*,seed:int,bootstrap:bool,source_id:int,neutral:bool=False) -> dict[str,Any]:
    if bootstrap:
        return _score(runtime,a,b,seed=seed,bootstrap=True,no_draw=True,competition_kind="tournament",source_id=source_id)
    row=_played_leg(runtime,a,b,seed=seed,source_id=source_id,neutral=neutral)
    if row["home_goals"]!=row["away_goals"]:
        winner=a if row["home_goals"]>row["away_goals"] else b;decided="single_leg"
    else:
        if domestic_cup_spec(int(source_id)) is not None and hasattr(runtime,"_domestic_foreign_rule"):
            home_rule=runtime._domestic_foreign_rule(int(a));away_rule=runtime._domestic_foreign_rule(int(b))
        else:
            home_rule=competition_foreign_rule(runtime.universe,kind="tournament",source_id=int(source_id),team_id=int(a));away_rule=competition_foreign_rule(runtime.universe,kind="tournament",source_id=int(source_id),team_id=int(b))
        home=runtime._sheet(int(a),foreign_rule=home_rule);away=runtime._sheet(int(b),foreign_rule=away_rule)
        rng=Random(seed^0x909394);delta=(sum(p.overall for p in home.starters)-sum(p.overall for p in away.starters))/(11*120)
        winner=a if rng.random()<max(.3,min(.7,.5+delta)) else b;decided="extra_time_penalties"
    return {**row,"winner_team_id":winner,"decided_by":decided}


def _queue_controlled_match(runtime, *, source_id:int, stage:str, day:date, home_id:str, away_id:str,
                            seed:int, destination:str, tie_index:int|None=None, leg:int|None=None,
                            group:str|None=None, round_number:int|None=None, neutral:bool=False, single:bool=False) -> bool:
    """Stop the world processor before auto-playing the user's cup match."""
    if runtime.state.get("pending_world_match"):
        return True
    controlled=str(int(runtime.state["team_id"]))
    if controlled not in (str(home_id),str(away_id)):
        return False
    runtime.state["pending_world_match"]={
        "kind":"tournament","source_id":int(source_id),"stage":stage,"date":day.isoformat(),
        "home_team_id":str(home_id),"away_team_id":str(away_id),"seed":int(seed),
        "destination":destination,"tie_index":tie_index,"leg":leg,"group":group,"round":round_number,
        "neutral":bool(neutral),"single":bool(single),
    }
    return True


def play_pending_tournament_match(runtime) -> tuple[dict[str,Any],list[dict[str,Any]]]:
    pending=runtime.state.get("pending_world_match")
    if not pending or pending.get("kind")!="tournament":
        raise ValueError("no hay partido de copa/continental pendiente")
    sid=int(pending["source_id"]);s=runtime.state["daily_tournaments"][str(sid)]
    a,b=str(pending["home_team_id"]),str(pending["away_team_id"]);seed=int(pending["seed"])
    row=(_single(runtime,a,b,seed=seed,bootstrap=False,source_id=sid,neutral=bool(pending.get("neutral")))
         if pending.get("single") else _played_leg(runtime,a,b,seed=seed,source_id=sid,neutral=bool(pending.get("neutral"))))
    if pending.get("leg") is not None: row["leg"]=int(pending["leg"])
    dest=pending.get("destination")
    if dest=="ucl_group":
        row.update({"round":int(pending["round"]),"group":str(pending["group"])})
        s["group_results"][str(pending["group"])].append(row)
    elif dest=="tie":
        tie=s["pending_ties"][int(pending["tie_index"])]
        # Idempotence protects reload/retry after a successful save boundary.
        if not any(int(x.get("leg") or 0)==int(pending.get("leg") or 0) and str(x.get("home_team_id"))==a for x in tie["legs"]):
            tie["legs"].append(row)
    elif dest=="greek_group":
        group=str(pending["group"]);row.update({"round":int(pending["round"]),"group":group})
        if not any(int(x.get("round") or 0)==int(pending["round"]) and str(x.get("home_team_id"))==a for x in s["group_results"][group]):
            s["group_results"][group].append(row)
    else:
        raise ValueError(f"destino de partido pendiente no soportado: {dest}")
    row.update({"source_id":sid,"competition_name":s.get("name") or f"Torneo {sid}","stage":pending["stage"]})
    runtime.state["pending_world_match"]=None
    runtime._post_matchday_income(int(a),competition=f"tournament:{sid}",reference=pending["stage"])
    runtime._rebuild_rosters(sync_dynamics=False)
    followup=process_daily_tournaments(runtime,runtime.current_date,bootstrap=False)
    return row,followup


def commit_pending_tournament_result(runtime, result, home_sheet, away_sheet) -> tuple[dict[str,Any],list[dict[str,Any]]]:
    """Commit a controlled live-match result into the same cup state machine."""
    pending=runtime.state.get("pending_world_match")
    if not pending or pending.get("kind")!="tournament":
        raise ValueError("no hay partido de copa/continental pendiente")
    sid=int(pending["source_id"]);s=runtime.state["daily_tournaments"][str(sid)]
    a,b=str(pending["home_team_id"]),str(pending["away_team_id"]);seed=int(pending["seed"])
    runtime._apply_match_player_state(result,home_sheet,away_sheet,seed,competition=s.get("name") or f"Torneo {sid}")
    row={"home_team_id":a,"away_team_id":b,"home_goals":int(result.home.goals),"away_goals":int(result.away.goals),"bootstrap":False}
    if pending.get("single"):
        if row["home_goals"]!=row["away_goals"]:
            winner=a if row["home_goals"]>row["away_goals"] else b;decided="single_leg"
        else:
            rng=Random(seed^0x909394);delta=(sum(p.overall for p in home_sheet.starters)-sum(p.overall for p in away_sheet.starters))/(11*120)
            winner=a if rng.random()<max(.3,min(.7,.5+delta)) else b;decided="extra_time_penalties"
        row.update({"winner_team_id":winner,"decided_by":decided})
    if pending.get("leg") is not None: row["leg"]=int(pending["leg"])
    dest=pending.get("destination")
    if dest=="ucl_group":
        row.update({"round":int(pending["round"]),"group":str(pending["group"])})
        s["group_results"][str(pending["group"])].append(row)
    elif dest=="tie":
        tie=s["pending_ties"][int(pending["tie_index"])]
        if not any(int(x.get("leg") or 0)==int(pending.get("leg") or 0) and str(x.get("home_team_id"))==a for x in tie["legs"]):
            tie["legs"].append(row)
    elif dest=="greek_group":
        group=str(pending["group"]);row.update({"round":int(pending["round"]),"group":group})
        if not any(int(x.get("round") or 0)==int(pending["round"]) and str(x.get("home_team_id"))==a for x in s["group_results"][group]):
            s["group_results"][group].append(row)
    else:
        raise ValueError(f"destino de partido pendiente no soportado: {dest}")
    row.update({"source_id":sid,"competition_name":s.get("name") or f"Torneo {sid}","stage":pending["stage"]})
    runtime.state["pending_world_match"]=None
    runtime._post_matchday_income(int(a),competition=f"tournament:{sid}",reference=pending["stage"])
    runtime._rebuild_rosters(sync_dynamics=False)
    followup=process_daily_tournaments(runtime,runtime.current_date,bootstrap=False)
    return row,followup


def _ucl_groups(runtime, s) -> dict[str,list[str]]:
    groups=s.get("groups")
    if groups:
        return {key:[str(x) for x in value] for key,value in groups.items()}
    current=[str(x) for x in s.get("current_ids") or []]
    historical=["3","209","227","265","307","415","617","645"]
    if sorted(current)==sorted(historical):
        groups={"A":["3","227","617","645"],"B":["265","307","209","415"]}
    else:
        pool=current[:]
        Random(int(runtime.state["seed"])+int(str(runtime.state.get("season","1993-94"))[:4])*100+1).shuffle(pool)
        if len(pool)!=8:
            raise ValueError(f"Copa de Europa: se esperaban 8 clasificados y hay {len(pool)}")
        groups={"A":pool[:4],"B":pool[4:]}
    s["groups"]=groups
    return groups


def _process_ucl(runtime,s,day:date,bootstrap:bool) -> list[dict[str,Any]]:
    events=[];seed0=int(runtime.state["seed"])*100000+1000
    groups=_ucl_groups(runtime,s)
    start=shift_reference_date(runtime.state,date(1993,11,24))
    if s["stage"] in ("pending","groups"):
        s["stage"]="groups"
        due=min(6,max(0,((day-start).days//14)+1)) if day>=start else 0
        for rnd in range(1,due+1):
            for gi,g in enumerate(("A","B")):
                fixtures=generate_round_robin_cycles(groups[g],2)
                for idx,f in enumerate([x for x in fixtures if x.round_number==rnd]):
                    exists=any(int(r.get("round") or 0)==rnd and str(r["home_team_id"])==str(f.home_team_id) and str(r["away_team_id"])==str(f.away_team_id) for r in s["group_results"][g])
                    if exists: continue
                    seed=seed0+rnd*100+gi*10+idx
                    if not bootstrap and _queue_controlled_match(runtime,source_id=1,stage=f"Grupo {g} · Jornada {rnd}",day=day,
                        home_id=f.home_team_id,away_id=f.away_team_id,seed=seed,destination="ucl_group",group=g,round_number=rnd):
                        return events+[{"kind":"controlled_match_pending","source_id":1,"stage":f"Grupo {g}","round":rnd,"date":day.isoformat()}]
                    row=_score(runtime,f.home_team_id,f.away_team_id,seed=seed,bootstrap=bootstrap,competition_kind="tournament",source_id=1);row.update({"round":rnd,"group":g})
                    s["group_results"][g].append(row)
            if all(sum(1 for r in s["group_results"][g] if int(r.get("round") or 0)==rnd)==2 for g in ("A","B")):
                if not any(e.get("kind")=="competition_round" and e.get("round")==rnd and e.get("stage")=="groups" for e in s.get("events",[])+events):
                    events.append({"kind":"competition_round","source_id":1,"stage":"groups","round":rnd,"date":day.isoformat(),"bootstrap":bootstrap})
        if all(len(s["group_results"][g])>=12 for g in ("A","B")):
            tables={}
            for g in ("A","B"):
                rules=CompetitionRules9394(id=f"ucl_{g}",name="Copa de Europa · Grupo",country="UEFA",points_win=2,points_draw=1,points_loss=0,teams=4,rounds=6,tie_breakers=("overall_goal_difference","overall_goals_scored"))
                matches=[LeagueMatch9394(r["home_team_id"],r["away_team_id"],r["home_goals"],r["away_goals"]) for r in s["group_results"][g]]
                tables[g]=build_league_table(tuple(groups[g]),matches,rules)
            s["group_qualifiers"]=[tables["A"][0].team_id,tables["B"][1].team_id,tables["B"][0].team_id,tables["A"][1].team_id];s["stage"]="semifinals"
    if s["stage"]=="semifinals" and day>=shift_reference_date(runtime.state,date(1994,4,27)):
        q=s["group_qualifiers"]
        if not s["pending_ties"]:
            s["pending_ties"]=[{"team_a":a,"team_b":b,"legs":[]} for a,b in ((q[0],q[1]),(q[2],q[3]))]
        for idx,tie in enumerate(s["pending_ties"]):
            if tie["legs"]: continue
            a,b=tie["team_a"],tie["team_b"];seed=seed0+10000+idx
            if not bootstrap and _queue_controlled_match(runtime,source_id=1,stage="Semifinales",day=day,home_id=a,away_id=b,seed=seed,destination="tie",tie_index=idx,leg=1,single=True):
                return events+[{"kind":"controlled_match_pending","source_id":1,"stage":"Semifinales","date":day.isoformat()}]
            row=_single(runtime,a,b,seed=seed,bootstrap=bootstrap,source_id=1);row["leg"]=1;tie["legs"].append(row)
        if all(t.get("legs") for t in s["pending_ties"]):
            for tie in s["pending_ties"]: tie["winner_team_id"]=tie["legs"][0]["winner_team_id"]
            s["current_ids"]=[t["winner_team_id"] for t in s["pending_ties"]];s["results"].extend([t["legs"][0] for t in s["pending_ties"]]);s["pending_ties"]=[];s["stage"]="final"
            events.append({"kind":"competition_stage","source_id":1,"stage":"semifinals","date":day.isoformat(),"bootstrap":bootstrap})
    if s["stage"]=="final" and day>=shift_reference_date(runtime.state,date(1994,5,18)):
        if not s["pending_ties"]:
            a,b=s["current_ids"];s["pending_ties"]=[{"team_a":a,"team_b":b,"legs":[]}]
        tie=s["pending_ties"][0];a,b=tie["team_a"],tie["team_b"]
        if not tie["legs"]:
            seed=seed0+11000
            if not bootstrap and _queue_controlled_match(runtime,source_id=1,stage="Final",day=day,home_id=a,away_id=b,seed=seed,destination="tie",tie_index=0,leg=1,neutral=True,single=True):
                return events+[{"kind":"controlled_match_pending","source_id":1,"stage":"Final","date":day.isoformat()}]
            row=_single(runtime,a,b,seed=seed,bootstrap=bootstrap,source_id=1,neutral=True);row["leg"]=1;tie["legs"].append(row)
        row=tie["legs"][0];s["results"].append(row);s.update({"champion_team_id":row["winner_team_id"],"runner_up_team_id":b if row["winner_team_id"]==a else a,"completed":True,"stage":"completed","pending_ties":[]})
        events.append({"kind":"competition_completed","source_id":1,"champion_team_id":s["champion_team_id"],"date":day.isoformat(),"bootstrap":bootstrap})
    return events


def _process_standard_knockout(runtime,s,day:date,bootstrap:bool,stages,source_id:int) -> list[dict[str,Any]]:
    events=[];seed0=int(runtime.state["seed"])*100000+source_id*1000
    while not s["completed"] and s["stage_index"]<len(stages):
        name,leg1_ref,leg2_ref,legs,away_goals=stages[s["stage_index"]]
        leg1_date=shift_reference_date(runtime.state,leg1_ref)
        leg2_date=shift_reference_date(runtime.state,leg2_ref) if leg2_ref is not None else None
        if not s["pending_ties"]:
            if day<leg1_date: break
            pairs=_pair(list(s["current_ids"]));s["pending_ties"]=[{"team_a":a,"team_b":b,"legs":[]} for a,b in pairs];s["stage"]=name
        # First (or only) leg.
        for idx,tie in enumerate(s["pending_ties"]):
            if len(tie["legs"])>=1: continue
            a,b=tie["team_a"],tie["team_b"];seed=seed0+s["stage_index"]*1000+idx*10
            is_single=legs==1
            if not bootstrap and _queue_controlled_match(runtime,source_id=source_id,stage=name,day=day,home_id=a,away_id=b,
                seed=seed,destination="tie",tie_index=idx,leg=1,neutral=(source_id==90 and name=="Final"),single=is_single):
                return events+[{"kind":"controlled_match_pending","source_id":source_id,"stage":name,"date":day.isoformat()}]
            row=(_single(runtime,a,b,seed=seed,bootstrap=bootstrap,source_id=source_id,neutral=(source_id==90 and name=="Final"))
                 if is_single else _score(runtime,a,b,seed=seed,bootstrap=bootstrap,competition_kind="tournament",source_id=source_id))
            row["leg"]=1;tie["legs"].append(row)
        if legs==1:
            if not all(t["legs"] for t in s["pending_ties"]): break
            winners=[];losers=[]
            for tie in s["pending_ties"]:
                row=tie["legs"][0];winner=row["winner_team_id"];a,b=tie["team_a"],tie["team_b"]
                tie["winner_team_id"]=winner;tie["loser_team_id"]=b if winner==a else a;winners.append(winner);losers.append(tie["loser_team_id"])
            s["results"].extend([r for t in s["pending_ties"] for r in t["legs"]]);s["current_ids"]=winners;s["pending_ties"]=[];s["stage_index"]+=1
            events.append({"kind":"competition_stage","source_id":source_id,"stage":name,"date":day.isoformat(),"bootstrap":bootstrap})
            if len(winners)==1:
                s.update({"champion_team_id":winners[0],"runner_up_team_id":losers[0],"completed":True,"stage":"completed"});events.append({"kind":"competition_completed","source_id":source_id,"champion_team_id":winners[0],"date":day.isoformat(),"bootstrap":bootstrap})
            continue
        if day<leg2_date: break
        # Second leg.
        for idx,tie in enumerate(s["pending_ties"]):
            if len(tie["legs"])>=2: continue
            a,b=tie["team_a"],tie["team_b"];seed=seed0+s["stage_index"]*1000+idx*10+1
            if not bootstrap and _queue_controlled_match(runtime,source_id=source_id,stage=name,day=day,home_id=b,away_id=a,
                seed=seed,destination="tie",tie_index=idx,leg=2,single=False):
                return events+[{"kind":"controlled_match_pending","source_id":source_id,"stage":name,"date":day.isoformat()}]
            row=_score(runtime,b,a,seed=seed,bootstrap=bootstrap,competition_kind="tournament",source_id=source_id);row["leg"]=2;tie["legs"].append(row)
        if not all(len(t["legs"])>=2 for t in s["pending_ties"]): break
        winners=[];losers=[]
        for tie in s["pending_ties"]:
            winner,loser,resolved=_resolve_two_leg(tie["legs"],advantage=None,away_goals=away_goals);tie.update({"winner_team_id":winner,"loser_team_id":loser,"resolved_by":resolved});winners.append(winner);losers.append(loser)
        s["results"].extend([r for t in s["pending_ties"] for r in t["legs"]]);s["current_ids"]=winners;s["last_round_losers"]=losers;s["pending_ties"]=[];s["stage_index"]+=1
        events.append({"kind":"competition_stage","source_id":source_id,"stage":name,"date":day.isoformat(),"bootstrap":bootstrap})
        if len(winners)==1:
            s.update({"champion_team_id":winners[0],"runner_up_team_id":losers[0],"completed":True,"stage":"completed"});events.append({"kind":"competition_completed","source_id":source_id,"champion_team_id":winners[0],"date":day.isoformat(),"bootstrap":bootstrap})
        continue
    return events


def _copa_pools(runtime) -> dict[str,list[str]]:
    return {
        "tier1":[str(t["source_id"]) for t in runtime._teams_for_league(1) if not t.get("reserve_of")],
        "tier2":[str(t["source_id"]) for t in runtime._teams_for_league(2) if not t.get("reserve_of")],
        "tier3":[str(t["source_id"]) for lid in (3,9,10,11) for t in runtime._teams_for_league(lid) if not t.get("reserve_of")],
    }


def _process_copa(runtime,s,day:date,bootstrap:bool) -> list[dict[str,Any]]:
    pools=_copa_pools(runtime);events=[];seed0=int(runtime.state["seed"])*100000+3000
    while not s["completed"] and s["stage_index"]<len(COPA_STAGES):
        name,leg1_ref,leg2_ref,target,entry=COPA_STAGES[s["stage_index"]]
        leg1_date=shift_reference_date(runtime.state,leg1_ref)
        leg2_date=shift_reference_date(runtime.state,leg2_ref) if leg2_ref is not None else None
        if not s["pending_ties"]:
            if day<leg1_date: break
            current=list(s["current_ids"])
            if entry=="tier3" and not current: current=list(pools["tier3"])
            elif entry in ("tier2","tier1"): current.extend(pools[entry])
            if target is None: target=(len(current)+1)//2
            byes,pairs=_prepare_reduction(current,target,seed=seed0+s["stage_index"]*1000)
            s["byes"]=byes;s["pending_ties"]=[{"team_a":a,"team_b":b,"legs":[]} for a,b in pairs];s["stage"]=name
        if name=="Final":
            tie=s["pending_ties"][0];a,b=tie["team_a"],tie["team_b"]
            if not tie["legs"]:
                seed=seed0+9000
                if not bootstrap and _queue_controlled_match(runtime,source_id=3,stage=name,day=day,home_id=a,away_id=b,seed=seed,
                    destination="tie",tie_index=0,leg=1,neutral=True,single=True):
                    return events+[{"kind":"controlled_match_pending","source_id":3,"stage":name,"date":day.isoformat()}]
                row=_single(runtime,a,b,seed=seed,bootstrap=bootstrap,source_id=3,neutral=True);row["leg"]=1;tie["legs"].append(row)
            row=tie["legs"][0];s["results"].append(row);s.update({"current_ids":[row["winner_team_id"]],"champion_team_id":row["winner_team_id"],"runner_up_team_id":b if row["winner_team_id"]==a else a,"completed":True,"stage":"completed","pending_ties":[],"byes":[]})
            events.append({"kind":"competition_completed","source_id":3,"champion_team_id":s["champion_team_id"],"date":day.isoformat(),"bootstrap":bootstrap});continue
        # First legs.
        for idx,tie in enumerate(s["pending_ties"]):
            if len(tie["legs"])>=1: continue
            a,b=tie["team_a"],tie["team_b"];seed=seed0+s["stage_index"]*1000+idx*10
            if not bootstrap and _queue_controlled_match(runtime,source_id=3,stage=name,day=day,home_id=a,away_id=b,seed=seed,
                destination="tie",tie_index=idx,leg=1,single=False):
                return events+[{"kind":"controlled_match_pending","source_id":3,"stage":name,"date":day.isoformat()}]
            row=_score(runtime,a,b,seed=seed,bootstrap=bootstrap,competition_kind="tournament",source_id=3);row["leg"]=1;tie["legs"].append(row)
        if day<leg2_date: break
        # Second legs.
        for idx,tie in enumerate(s["pending_ties"]):
            if len(tie["legs"])>=2: continue
            a,b=tie["team_a"],tie["team_b"];seed=seed0+s["stage_index"]*1000+idx*10+1
            if not bootstrap and _queue_controlled_match(runtime,source_id=3,stage=name,day=day,home_id=b,away_id=a,seed=seed,
                destination="tie",tie_index=idx,leg=2,single=False):
                return events+[{"kind":"controlled_match_pending","source_id":3,"stage":name,"date":day.isoformat()}]
            row=_score(runtime,b,a,seed=seed,bootstrap=bootstrap,competition_kind="tournament",source_id=3);row["leg"]=2;tie["legs"].append(row)
        if not all(len(t["legs"])>=2 for t in s["pending_ties"]): break
        winners=[]
        for tie in s["pending_ties"]:
            winner,loser,resolved=_resolve_two_leg(tie["legs"],advantage=None,away_goals=True);tie.update({"winner_team_id":winner,"loser_team_id":loser,"resolved_by":resolved});winners.append(winner)
        s["results"].extend([r for t in s["pending_ties"] for r in t["legs"]]);s["current_ids"]=list(s["byes"])+winners;s["pending_ties"]=[];s["byes"]=[];s["stage_index"]+=1
        events.append({"kind":"competition_stage","source_id":3,"stage":name,"date":day.isoformat(),"bootstrap":bootstrap});continue
    return events



def _cup_round_dates(round_count: int) -> list[date]:
    templates={
        1:[date(1994,5,18)],
        2:[date(1994,4,20),date(1994,5,18)],
        3:[date(1994,3,16),date(1994,4,20),date(1994,5,18)],
        4:[date(1994,2,16),date(1994,3,16),date(1994,4,20),date(1994,5,18)],
        5:[date(1993,12,1),date(1994,2,16),date(1994,3,16),date(1994,4,20),date(1994,5,18)],
        6:[date(1993,11,3),date(1993,12,1),date(1994,2,16),date(1994,3,16),date(1994,4,20),date(1994,5,18)],
        7:[date(1993,10,6),date(1993,11,3),date(1993,12,1),date(1994,2,16),date(1994,3,16),date(1994,4,20),date(1994,5,18)],
        8:[date(1993,9,22),date(1993,10,6),date(1993,11,3),date(1993,12,1),date(1994,2,16),date(1994,3,16),date(1994,4,20),date(1994,5,18)],
    }
    if round_count not in templates:
        raise ValueError(f"copa doméstica: {round_count} rondas no soportadas")
    return templates[round_count]


def _round_name(target: int, stage_index: int) -> str:
    return {1:"Final",2:"Semifinales",4:"Cuartos",8:"Octavos",16:"Dieciseisavos",32:"1/32"}.get(int(target),f"Ronda {stage_index+1}")


def _domestic_knockout_plan(spec, participant_count: int, *, greek_knockout: bool=False) -> list[dict[str,Any]]:
    if participant_count < 2:
        return []
    sizes=[];n=int(participant_count)
    while n>1:
        target=(n+1)//2;sizes.append((n,target));n=target
    dates=_cup_round_dates(len(sizes))
    plan=[]
    for idx,((before,target),leg1) in enumerate(zip(sizes,dates,strict=True)):
        if greek_knockout:
            legs=1 if target==1 else 2
        elif spec.format_style=="italy_two_leg_late":
            legs=2 if before<=16 else 1
        elif spec.format_style=="turkey_two_leg_semis_final":
            legs=2 if before<=4 else 1
        elif spec.format_style=="belgium_two_leg_semis":
            legs=2 if before<=4 and target>1 else 1
        else:
            legs=1
        plan.append({
            "name":_round_name(target,idx),"leg1":leg1.isoformat(),"leg2":date.fromordinal(leg1.toordinal()+14).isoformat() if legs==2 else None,
            "legs":legs,"away_goals":bool(legs==2),"neutral":bool(legs==1 and target==1),
        })
    return plan


def _ensure_domestic_plan(runtime, s:dict[str,Any]) -> list[dict[str,Any]]:
    plan=s.get("round_plan")
    if plan:
        return plan
    spec=domestic_cup_spec(int(s["source_id"]))
    if spec is None:
        raise KeyError(f"copa doméstica {s['source_id']} no registrada")
    plan=_domestic_knockout_plan(spec,len(s.get("current_ids") or []))
    s["round_plan"]=plan
    return plan


def _process_domestic_knockout(runtime,s,day:date,bootstrap:bool) -> list[dict[str,Any]]:
    events=[];sid=int(s["source_id"]);spec=domestic_cup_spec(sid)
    if spec is None: return events
    plan=_ensure_domestic_plan(runtime,s);seed0=int(runtime.state["seed"])*100000+sid*17
    while not s["completed"] and s["stage_index"]<len(plan):
        stage=plan[s["stage_index"]];name=str(stage["name"])
        leg1_ref=date.fromisoformat(stage["leg1"]) if isinstance(stage.get("leg1"),str) else stage["leg1"]
        leg2_ref=date.fromisoformat(stage["leg2"]) if isinstance(stage.get("leg2"),str) else stage.get("leg2")
        leg1_date=shift_reference_date(runtime.state,leg1_ref)
        leg2_date=shift_reference_date(runtime.state,leg2_ref) if leg2_ref else None
        if not s["pending_ties"]:
            if day<leg1_date: break
            current=list(map(str,s.get("current_ids") or []))
            if len(current)==1:
                s.update({"champion_team_id":current[0],"completed":True,"stage":"completed"});break
            rng=Random(seed0+s["stage_index"]*1009);rng.shuffle(current)
            s["byes"]=current[-1:] if len(current)%2 else []
            playing=current[:-1] if len(current)%2 else current
            s["pending_ties"]=[{"team_a":a,"team_b":b,"legs":[]} for a,b in _pair(playing)]
            s["stage"]=name
        for tie_index,tie in enumerate(s["pending_ties"]):
            if tie["legs"]: continue
            a,b=str(tie["team_a"]),str(tie["team_b"]);seed=seed0+s["stage_index"]*1000+tie_index*10
            single=int(stage["legs"])==1
            if not bootstrap and _queue_controlled_match(runtime,source_id=sid,stage=name,day=day,home_id=a,away_id=b,seed=seed,destination="tie",tie_index=tie_index,leg=1,neutral=bool(stage.get("neutral")),single=single):
                return events+[{"kind":"controlled_match_pending","source_id":sid,"stage":name,"date":day.isoformat()}]
            row=(_single(runtime,a,b,seed=seed,bootstrap=bootstrap,source_id=sid,neutral=bool(stage.get("neutral"))) if single else _score(runtime,a,b,seed=seed,bootstrap=bootstrap,competition_kind="tournament",source_id=sid))
            row["leg"]=1;tie["legs"].append(row)
        if int(stage["legs"])==2:
            if day<leg2_date: break
            for tie_index,tie in enumerate(s["pending_ties"]):
                if len(tie["legs"])>=2: continue
                a,b=str(tie["team_a"]),str(tie["team_b"]);seed=seed0+s["stage_index"]*1000+tie_index*10+1
                if not bootstrap and _queue_controlled_match(runtime,source_id=sid,stage=name,day=day,home_id=b,away_id=a,seed=seed,destination="tie",tie_index=tie_index,leg=2,single=False):
                    return events+[{"kind":"controlled_match_pending","source_id":sid,"stage":name,"date":day.isoformat()}]
                row=_score(runtime,b,a,seed=seed,bootstrap=bootstrap,competition_kind="tournament",source_id=sid);row["leg"]=2;tie["legs"].append(row)
            if not all(len(t["legs"])>=2 for t in s["pending_ties"]): break
        elif not all(t["legs"] for t in s["pending_ties"]):
            break
        winners=list(map(str,s.get("byes") or []));losers=[]
        for tie in s["pending_ties"]:
            a,b=str(tie["team_a"]),str(tie["team_b"])
            if int(stage["legs"])==1:
                row=tie["legs"][0];winner=str(row["winner_team_id"]);loser=b if winner==a else a;resolved=str(row.get("decided_by") or "single_leg")
            else:
                winner,loser,resolved=_resolve_two_leg(tie["legs"],advantage=None,away_goals=bool(stage.get("away_goals")))
            tie.update({"winner_team_id":winner,"loser_team_id":loser,"resolved_by":resolved});winners.append(winner);losers.append(loser)
        s["results"].extend([row for tie in s["pending_ties"] for row in tie["legs"]]);s["current_ids"]=winners
        s["pending_ties"]=[];s["byes"]=[];s["stage_index"]+=1
        events.append({"kind":"competition_stage","source_id":sid,"stage":name,"date":day.isoformat(),"bootstrap":bootstrap})
        if len(winners)==1:
            runner=losers[-1] if losers else None
            s.update({"champion_team_id":winners[0],"runner_up_team_id":runner,"completed":True,"stage":"completed"})
            events.append({"kind":"competition_completed","source_id":sid,"champion_team_id":winners[0],"runner_up_team_id":runner,"date":day.isoformat(),"bootstrap":bootstrap})
        continue
    return events


def _greek_group_table(group_ids:list[str], rows:list[dict[str,Any]]) -> list[dict[str,Any]]:
    stats={str(t):{"team_id":str(t),"points":0,"gf":0,"ga":0,"wins":0} for t in group_ids}
    for row in rows:
        h,a=str(row["home_team_id"]),str(row["away_team_id"]);hg,ag=int(row["home_goals"]),int(row["away_goals"])
        stats[h]["gf"]+=hg;stats[h]["ga"]+=ag;stats[a]["gf"]+=ag;stats[a]["ga"]+=hg
        if hg>ag: stats[h]["points"]+=2;stats[h]["wins"]+=1
        elif ag>hg: stats[a]["points"]+=2;stats[a]["wins"]+=1
        else: stats[h]["points"]+=1;stats[a]["points"]+=1
    return sorted(stats.values(),key=lambda r:(-r["points"],-(r["gf"]-r["ga"]),-r["gf"],-r["wins"],int(r["team_id"])))


def _process_greek_cup(runtime,s,day:date,bootstrap:bool) -> list[dict[str,Any]]:
    sid=int(s["source_id"]);events=[];seed0=int(runtime.state["seed"])*100000+sid*17
    if s.get("stage") in {"pending","group_stage"} and not s.get("group_qualifiers"):
        if not s.get("groups"):
            pool=list(map(str,s.get("current_ids") or []));Random(seed0).shuffle(pool)
            group_count=max(1,min(6,len(pool)//3));groups={chr(65+i):[] for i in range(group_count)}
            for idx,tid in enumerate(pool): groups[chr(65+(idx%group_count))].append(tid)
            s["groups"]=groups;s["group_results"]={g:[] for g in groups};s["group_round"]=0;s["stage"]="group_stage"
        group_dates=[date(1993,10,6),date(1993,10,20),date(1993,11,3)]
        groups=s["groups"]
        for round_number,ref in enumerate(group_dates,start=1):
            if int(s.get("group_round") or 0)>=round_number: continue
            if day<shift_reference_date(runtime.state,ref): break
            for gi,(group,ids) in enumerate(sorted(groups.items())):
                fixtures=generate_round_robin_cycles(tuple(map(str,ids)),1)
                for fi,fixture in enumerate([f for f in fixtures if int(f.round_number)==round_number]):
                    already=any(int(r.get("round") or 0)==round_number and str(r.get("home_team_id"))==str(fixture.home_team_id) for r in s["group_results"][group])
                    if already: continue
                    a,b=str(fixture.home_team_id),str(fixture.away_team_id);seed=seed0+round_number*1000+gi*50+fi
                    if not bootstrap and _queue_controlled_match(runtime,source_id=sid,stage=f"Grupos {group} J{round_number}",day=day,home_id=a,away_id=b,seed=seed,destination="greek_group",group=group,round_number=round_number,single=False):
                        return events+[{"kind":"controlled_match_pending","source_id":sid,"stage":"Fase de grupos","date":day.isoformat()}]
                    row=_score(runtime,a,b,seed=seed,bootstrap=bootstrap,competition_kind="tournament",source_id=sid);row.update({"round":round_number,"group":group});s["group_results"][group].append(row)
            # All fixtures for this group round are now present.
            s["group_round"]=round_number
            events.append({"kind":"competition_stage","source_id":sid,"stage":f"grupos_j{round_number}","date":day.isoformat(),"bootstrap":bootstrap})
        if int(s.get("group_round") or 0)>=3:
            tables={g:_greek_group_table(list(map(str,ids)),s["group_results"][g]) for g,ids in groups.items()}
            winners=[table[0]["team_id"] for table in tables.values() if table]
            runners=[table[1] for table in tables.values() if len(table)>1]
            runners.sort(key=lambda r:(-r["points"],-(r["gf"]-r["ga"]),-r["gf"],int(r["team_id"])))
            qualifiers=(winners+[r["team_id"] for r in runners])[:8]
            # If the adapted pool produces fewer than eight, fill by next best
            # group positions rather than inventing a club.
            if len(qualifiers)<8:
                extras=[r["team_id"] for table in tables.values() for r in table[2:] if r["team_id"] not in qualifiers]
                qualifiers.extend(extras[:8-len(qualifiers)])
            s["group_qualifiers"]=qualifiers;s["current_ids"]=qualifiers;s["stage"]="knockout";s["stage_index"]=0
            spec=domestic_cup_spec(sid);s["round_plan"]=_domestic_knockout_plan(spec,len(qualifiers),greek_knockout=True)
    if s.get("group_qualifiers") and not s.get("completed"):
        events.extend(_process_domestic_knockout(runtime,s,day,bootstrap))
    return events

def process_daily_tournaments(runtime, day: date, *, bootstrap: bool=False) -> list[dict[str,Any]]:
    ensure_tournament_state(runtime.state,runtime.universe);events=[]
    for key,s in runtime.state["daily_tournaments"].items():
        sid=int(key)
        if sid==1: new=_process_ucl(runtime,s,day,bootstrap)
        elif sid==2: new=_process_standard_knockout(runtime,s,day,bootstrap,UEFA_CUP_STAGES,2)
        elif sid==90: new=_process_standard_knockout(runtime,s,day,bootstrap,CWC_STAGES,90)
        elif sid==3: new=_process_copa(runtime,s,day,bootstrap)
        elif domestic_cup_spec(sid) is not None:
            new=(_process_greek_cup(runtime,s,day,bootstrap) if str(s.get("format_style"))=="greece_groups_two_leg" else _process_domestic_knockout(runtime,s,day,bootstrap))
        else: new=[]
        s["events"].extend(new);events.extend(new)
        if not bootstrap and runtime.state.get("pending_world_match"):
            break
    # AI-only tournament progression does not change roster membership or
    # availability. Controlled cup matches are queued and committed through
    # the dedicated match path, which rebuilds after applying player state.
    return events


def tournament_snapshot(runtime) -> dict[str,Any]:
    ensure_tournament_state(runtime.state,runtime.universe)
    out={}
    for k,s in runtime.state["daily_tournaments"].items():
        count=len(s.get("results") or [])
        if s.get("group_results"):
            count += sum(len(rows) for rows in s["group_results"].values())
        out[k]={"source_id":int(k),"name":s["name"],"stage":s["stage"],"completed":bool(s["completed"]),"champion_team_id":s.get("champion_team_id"),"result_count":count,"event_count":len(s.get("events") or []),"calendar_fidelity":s["calendar_fidelity"]}
    return out
