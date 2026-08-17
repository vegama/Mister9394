from __future__ import annotations

"""Incremental national-team friendlies for the persistent 1993-94 world.

The MDB gives us national eligibility but not a complete historical fixture
list.  Therefore these are explicitly generated *career friendlies*, never
presented as real 1993-94 results.  They exist so selections are living actors:
players are called up from their current career form and can gain/lose form or
suffer injuries while away.
"""

from datetime import date
from typing import Any

from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, FootballTactics9394, Footballer9394, TeamSheet9394
from .national_teams import eligible_national_players, national_team_catalog, select_national_squad
from .snapshot_runtime import FootballUniverseSnapshot9394


def generated_international_windows_9394(season_start_year: int = 1993) -> tuple[date, ...]:
    delta = int(season_start_year) - 1993
    return (
        date(1993 + delta,11,17),
        date(1994 + delta,2,16),
        date(1994 + delta,3,23),
        date(1994 + delta,4,20),
        date(1994 + delta,5,25),
    )


def _attr(api: dict[str, Any], key: str, fallback: int) -> int:
    try:
        return max(1,min(100,int((api.get("attributes") or {}).get(key) or fallback)))
    except (TypeError,ValueError):
        return fallback


def _slot(api:dict[str,Any]) -> str:
    return str((api.get("specialist_role") or {}).get("squad_slot") or "CM").upper()

def _broad(api:dict[str,Any]) -> str:
    slot=_slot(api)
    if slot=="GK": return "POR"
    if slot in {"RB","LB","CB"}: return "DEF"
    if slot in {"ST","RW","LW"}: return "DEL"
    return "MED"

def _footballer(api: dict[str, Any]) -> Footballer9394:
    slot=_slot(api)
    mapped="GK" if slot=="GK" else "DF" if slot in {"RB","LB","CB"} else "ST" if slot in {"ST","RW","LW"} else "MF"
    overall=max(1,min(100,int(api.get("overall") or 60)))
    return Footballer9394(
        id=str(api["id"]), name=str(api.get("display_name") or api["id"]), position=mapped, overall=overall,
        pace=_attr(api,"pace",overall), stamina=_attr(api,"stamina",overall), technique=_attr(api,"technique",overall),
        short_pass=_attr(api,"short_pass",overall), long_pass=_attr(api,"long_pass",overall), creativity=_attr(api,"vision",overall),
        finishing=_attr(api,"finishing",overall), heading=_attr(api,"heading",overall), tackling=_attr(api,"tackling",overall),
        marking=_attr(api,"marking",overall), positioning=_attr(api,"positioning",overall), discipline=_attr(api,"discipline",72),
        leadership=_attr(api,"leadership",70), goalkeeping=_attr(api,"goalkeeping",overall if mapped=="GK" else 8),
    )


def build_national_sheet(
    universe: FootballUniverseSnapshot9394,
    country_id: int,
    *,
    development: dict[str,dict[str,Any]] | None = None,
    selected_player_ids: list[int] | None = None,
) -> TeamSheet9394:
    if selected_player_ids:
        wanted=[int(pid) for pid in selected_player_ids]
        eligible={int(p["source_id"]):p for p in eligible_national_players(universe,country_id,development=development)}
        squad=[]
        for pid in wanted:
            source=eligible.get(pid)
            if source is None:
                continue
            api=universe.player_api(source)
            if development:
                state=development.get(str(pid),{})
                api["overall"]=state.get("overall",api.get("overall"))
                api["form"]=state.get("form");api["morale"]=state.get("morale");api["condition"]=state.get("condition")
                if int(state.get("injury_days") or 0)>0: api["status"]=f"Lesionado · {state['injury_days']} d"
            squad.append(api)
        if len(squad)<11:
            raise ValueError("la convocatoria guardada ya no permite formar un once internacional")
    else:
        squad=select_national_squad(universe,country_id,development=development)
    by={"POR":[],"DEF":[],"MED":[],"DEL":[]}
    for row in squad:
        by.setdefault(_broad(row),[]).append(row)
    chosen=(by["POR"][:1]+by["DEF"][:4]+by["MED"][:4]+by["DEL"][:2])
    chosen_ids={int(p["id"]) for p in chosen}
    if len(chosen)<11:
        chosen.extend(p for p in squad if int(p["id"]) not in chosen_ids)
        chosen=chosen[:11]
    # 1993-94 Laws contract in this game names at most five substitutes.
    bench=[p for p in squad if p not in chosen][:5]
    catalog={row.country_id:row.name for row in national_team_catalog(universe)}
    return TeamSheet9394(
        team_id=f"NT:{country_id}", team_name=catalog.get(country_id,str(country_id)),
        starters=tuple(_footballer(p) for p in chosen), bench=tuple(_footballer(p) for p in bench),
        tactics=FootballTactics9394(formation="4-4-2"),
    )


def generated_pairings(universe: FootballUniverseSnapshot9394, *, window_index: int) -> list[tuple[int,int]]:
    catalog=national_team_catalog(universe)
    ids=[row.country_id for row in catalog]
    if len(ids)%2: ids=ids[:-1]
    if len(ids)<2: return []
    # Rotate the list between windows so the same countries do not repeatedly
    # meet.  Ranking stays source/form backed; only the friendly pairing is generated.
    shift=(window_index*3)%len(ids)
    ids=ids[shift:]+ids[:shift]
    return [(ids[i],ids[i+1]) for i in range(0,len(ids)-1,2)]


def simulate_generated_friendlies(
    universe: FootballUniverseSnapshot9394,
    *,
    development: dict[str,dict[str,Any]] | None,
    window_index: int,
    seed: int,
    selections: dict[int,list[int]] | None = None,
) -> list[dict[str,Any]]:
    engine=FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)
    outputs=[]
    for index,(home_id,away_id) in enumerate(generated_pairings(universe,window_index=window_index)):
        home=build_national_sheet(universe,home_id,development=development,selected_player_ids=(selections or {}).get(int(home_id)))
        away=build_national_sheet(universe,away_id,development=development,selected_player_ids=(selections or {}).get(int(away_id)))
        result=engine.simulate(home,away,seed=seed+window_index*1000+index)
        outputs.append({
            "kind":"international_friendly","generated_fixture":True,"historical_result":False,
            "home_country_id":home_id,"away_country_id":away_id,"home_name":home.team_name,"away_name":away.team_name,
            "home_goals":result.home.goals,"away_goals":result.away.goals,"result":result,"home_sheet":home,"away_sheet":away,
        })
    return outputs
