from __future__ import annotations

"""Frozen 24-team 1994-style world championship used every four years.

1994 itself uses the real 24 qualified countries and the exact 22-player squad
mapped in the bundled USA 1994 data.  Results remain generated alternate
history.  Future editions preserve the 24-team/1994 laws format but qualify the
strongest living selections from the evolving career world.
"""

from datetime import date
from random import Random
from typing import Any

from .career_international import build_national_sheet
from .match_engine import FootballMatchEngine9394, ERA_BASELINE_1993_94
from .national_teams import national_team_catalog, world_cup_1994_country_ids, world_cup_1994_player_ids


def is_world_championship_summer(year: int) -> bool:
    return int(year)>=1994 and (int(year)-1994)%4==0


def _play(engine, universe, development, home_id, away_id, seed, selections, *, stage: str, match_recorder=None):
    home=build_national_sheet(universe,home_id,development=development,selected_player_ids=(selections or {}).get(int(home_id)))
    away=build_national_sheet(universe,away_id,development=development,selected_player_ids=(selections or {}).get(int(away_id)))
    result=engine.simulate(home,away,seed=seed)
    winner=None;shootout=False
    if result.home.goals>result.away.goals: winner=home_id
    elif result.away.goals>result.home.goals: winner=away_id
    else:
        shootout=True;winner=home_id if Random(seed^0x24).random()<.5 else away_id
    if match_recorder is not None:
        match_recorder(result,home,away,stage)
    return {"home_country_id":home_id,"away_country_id":away_id,"home_name":home.team_name,"away_name":away.team_name,"home_goals":result.home.goals,"away_goals":result.away.goals,"winner_country_id":winner,"shootout":shootout}


def simulate_world_championship_24(universe: Any, *, year: int, development: dict[str,dict[str,Any]]|None, seed: int, selections: dict[int,list[int]]|None=None, match_recorder=None) -> dict[str,Any]:
    catalog=national_team_catalog(universe)
    names={int(row.country_id):row.name for row in catalog}
    user_selections={int(cid):[int(pid) for pid in ids] for cid,ids in (selections or {}).items()}
    historical_1994=int(year)==1994
    if historical_1994:
        ids=world_cup_1994_country_ids()
        if len(ids)!=24:
            raise ValueError("los datos USA 1994 no contienen exactamente 24 selecciones")
        missing=[cid for cid in ids if len(world_cup_1994_player_ids(universe,cid))!=22]
        if missing:
            raise ValueError(f"convocatorias USA 1994 incompletas: {missing}")
        effective_selections={cid:world_cup_1994_player_ids(universe,cid) for cid in ids}
        # A human manager is allowed to rewrite his own 22 before the tournament;
        # every unmanaged country keeps the exact historical squad.
        effective_selections.update(user_selections)
    else:
        ids=[int(row.country_id) for row in catalog[:24]]
        if len(ids)<24:
            raise ValueError("no hay 24 selecciones elegibles para el campeonato mundial")
        effective_selections=user_selections
    groups=[ids[i:i+4] for i in range(0,24,4)];engine=FootballMatchEngine9394(profile=ERA_BASELINE_1993_94);matches=[];qualified=[]
    third_rows=[]
    for gi,group in enumerate(groups):
        table={cid:{"country_id":cid,"points":0,"gf":0,"ga":0} for cid in group};idx=0
        for i in range(4):
            for j in range(i+1,4):
                h,a=group[i],group[j];row=_play(engine,universe,development,h,a,seed+gi*100+idx,effective_selections,stage="group",match_recorder=match_recorder);idx+=1;row.update({"stage":"group","group":chr(ord('A')+gi)});matches.append(row)
                hg,ag=int(row["home_goals"]),int(row["away_goals"]);table[h]["gf"]+=hg;table[h]["ga"]+=ag;table[a]["gf"]+=ag;table[a]["ga"]+=hg
                if hg>ag: table[h]["points"]+=2
                elif ag>hg: table[a]["points"]+=2
                else: table[h]["points"]+=1;table[a]["points"]+=1
        ordered=sorted(table.values(),key=lambda r:(-r["points"],-(r["gf"]-r["ga"]),-r["gf"],r["country_id"]))
        qualified.extend([ordered[0]["country_id"],ordered[1]["country_id"]]);third_rows.append(ordered[2])
    third_rows.sort(key=lambda r:(-r["points"],-(r["gf"]-r["ga"]),-r["gf"],r["country_id"]));qualified.extend(r["country_id"] for r in third_rows[:4])
    current=qualified[:16];stage_names=["round16","quarterfinal","semifinal","final"]
    stage_seed=seed+5000
    for stage in stage_names:
        next_round=[]
        for i in range(0,len(current),2):
            row=_play(engine,universe,development,current[i],current[i+1],stage_seed+i,effective_selections,stage=stage,match_recorder=match_recorder);row["stage"]=stage;matches.append(row);next_round.append(int(row["winner_country_id"]))
        current=next_round;stage_seed+=500
    champion=current[0]
    return {
        "kind":"world_championship","year":int(year),"format":"24_team_1994_frozen",
        "generated_alternate_history":True,"historical_results_claimed":False,
        "historical_1994_participants":historical_1994,"historical_1994_squads":historical_1994,
        "participants":ids,"matches":matches,"champion_country_id":champion,
        "champion_name":names.get(champion,str(champion)),"played_on":date(year,6,17).isoformat(),
    }
