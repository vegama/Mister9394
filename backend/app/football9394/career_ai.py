from __future__ import annotations

"""Deterministic club AI for transfers and renewals in the frozen-age career.

The first target is a believable moving world, not a Football Manager-sized
negotiation model.  AI clubs protect squad depth, renew useful expiring players
and make a small number of affordable transfers each month.  Every action is
persisted in the career state and therefore never re-rolled on reload.
"""

from datetime import date
from random import Random
from typing import Any

from .career_economy import effective_contract, inferred_annual_salary
from .career_market import estimated_transfer_value


def _overall(player: dict[str, Any], development: dict[str, dict[str, Any]]) -> int:
    return int(development.get(str(int(player["source_id"])), {}).get("overall") or player.get("overall") or player.get("category") or 60)


def _club_average(players: list[dict[str, Any]], development: dict[str, dict[str, Any]]) -> float:
    vals=sorted((_overall(p,development) for p in players), reverse=True)[:16]
    return (sum(vals)/len(vals)) if vals else 0.0


def renew_ai_contracts(
    *,
    current_date: date,
    controlled_team_id: int,
    players_by_team: dict[int, list[dict[str, Any]]],
    development: dict[str, dict[str, Any]],
    contract_overrides: dict[str, dict[str, Any]],
    seed: int,
    max_renewals: int = 48,
) -> list[dict[str, Any]]:
    """Renew a limited number of AI contracts that expire at season end.

    We only act from January onwards, keeping contract chatter out of the first
    autumn months.  Lower-rated fringe players may be deliberately left to run
    down; actual release is handled at June rollover.
    """
    if current_date.month < 1 or current_date.month > 6:
        return []
    if current_date.month < 1:
        return []
    rng=Random(seed ^ (current_date.year*100+current_date.month) ^ 0x9394C0)
    actions=[]
    season_end_year=current_date.year if current_date.month <= 6 else current_date.year+1
    for team_id in sorted(players_by_team):
        if len(actions) >= max(0, int(max_renewals)):
            break
        if team_id in (0, controlled_team_id):
            continue
        players=players_by_team[team_id]
        if not players:
            continue
        average=_club_average(players,development)
        candidates=[]
        for player in players:
            pid=str(int(player["source_id"]))
            overall=_overall(player,development)
            contract=effective_contract(player,overall=overall,override=contract_overrides.get(pid))
            if int(contract.get("end_year") or 0) != season_end_year:
                continue
            if overall + 5 < average and rng.random() < .72:
                continue
            candidates.append((overall,player,contract))
        candidates.sort(key=lambda row:(-row[0],int(row[1]["source_id"])))
        # One negotiation per club and monthly pulse. This keeps the market
        # legible instead of renewing hundreds of contracts on the same day.
        for overall,player,old in candidates[:1]:
            if len(actions) >= max(0, int(max_renewals)):
                break
            pid=str(int(player["source_id"]))
            years=2 + (1 if overall >= average+3 else 0)
            salary=round(max(int(old.get("salary") or 0), inferred_annual_salary(player,overall=overall)) * (1.04 + max(0,overall-average)/100))
            contract_overrides[pid]={
                **old,"start":str(current_date.year),"end":str(current_date.year+years),"end_year":current_date.year+years,
                "salary":salary,"salary_display":f"{salary:,} ptas.".replace(",","."),
                "career_inferred":True,"renewed_by_ai":True,
            }
            actions.append({"kind":"ai_renewal","team_id":team_id,"player_id":int(pid),"years":years,"salary":salary,"date":current_date.isoformat()})
    return actions


def run_ai_transfer_window(
    *,
    current_date: date,
    controlled_team_id: int,
    eligible_team_ids: list[int],
    players_by_team: dict[int, list[dict[str, Any]]],
    development: dict[str, dict[str, Any]],
    club_finances: dict[str, dict[str, Any]],
    player_team_overrides: dict[str, int],
    contract_overrides: dict[str, dict[str, Any]],
    seed: int,
    max_deals: int = 6,
) -> list[dict[str, Any]]:
    """Execute a small deterministic AI market pulse.

    The 1993-94 career deliberately does *not* impose modern transfer windows.
    This is a simplified pre-Bosman continuous market: clubs may trade throughout
    the season, while July/August get a larger activity allowance from the caller.
    Sellers still keep at least 16 players so AI trading cannot hollow squads out.
    """
    rng=Random(seed ^ (current_date.year*100+current_date.month) ^ 0xA19394)
    candidates_buyers=[]
    for tid in eligible_team_ids:
        if tid==controlled_team_id:
            continue
        players=players_by_team.get(tid,[])
        if len(players)<11:
            continue
        avg=_club_average(players,development)
        need=max(0,22-len(players)) + max(0,round((70-avg)/4))
        candidates_buyers.append((need+rng.random(),tid,avg))
    candidates_buyers.sort(reverse=True)
    actions=[]
    used_players=set()
    for _,buyer,avg in candidates_buyers:
        if len(actions)>=max_deals:
            break
        finance=club_finances.get(str(buyer)) or {}
        cash=int(finance.get("cash") or 0)
        if cash<=0:
            continue
        pool=[]
        for seller in eligible_team_ids:
            if seller in (buyer,controlled_team_id) or len(players_by_team.get(seller,[]))<=16:
                continue
            for player in players_by_team.get(seller,[]):
                pid=int(player["source_id"])
                if pid in used_players:
                    continue
                overall=_overall(player,development)
                if overall < max(55,round(avg-4)) or overall > round(avg+10):
                    continue
                value=estimated_transfer_value(player,overall=overall)
                if value > cash*0.42:
                    continue
                pool.append((abs(overall-(avg+2))+rng.random()*2,-overall,pid,seller,player,value))
        if not pool:
            continue
        pool.sort(key=lambda x:(x[0],x[1],x[2]))
        _,_,pid,seller,player,value=pool[0]
        fee=max(250_000,round(value*(0.90+rng.random()*0.16)))
        if fee>cash:
            continue
        buyer_fin=club_finances[str(buyer)]; seller_fin=club_finances[str(seller)]
        buyer_fin["cash"]-=fee; buyer_fin["transfer_spend"]=int(buyer_fin.get("transfer_spend") or 0)+fee
        seller_fin["cash"]+=fee; seller_fin["transfer_income"]=int(seller_fin.get("transfer_income") or 0)+fee
        player_team_overrides[str(pid)]=buyer
        overall=_overall(player,development)
        salary=round(inferred_annual_salary(player,overall=overall)*(1.02+rng.random()*.10))
        years=2+(1 if rng.random()<.55 else 0)
        contract_overrides[str(pid)]={
            "start":str(current_date.year),"end":str(current_date.year+years),"end_year":current_date.year+years,
            "salary":salary,"salary_display":f"{salary:,} ptas.".replace(",","."),"loan":False,
            "career_inferred":True,"signed_by_ai":True,
        }
        used_players.add(pid)
        actions.append({"kind":"ai_transfer","date":current_date.isoformat(),"player_id":pid,"from_team_id":seller,"to_team_id":buyer,"fee":fee,"salary":salary,"contract_years":years})
    return actions
