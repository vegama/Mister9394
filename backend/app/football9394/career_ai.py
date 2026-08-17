from __future__ import annotations

"""Deterministic club AI for transfers and renewals in the persistent career.

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
from .player_identity import tactical_fit
from .coaching import tactics_from_source_manager
from .position_roles import (
    role_for_player, squad_role_audit, SQUAD_ROLE_MINIMUM_9394, position_penalty,
    MINIMUM_SENIOR_SQUAD_SIZE_9394, TARGET_SENIOR_SQUAD_SIZE_9394,
)


def _overall(player: dict[str, Any], development: dict[str, dict[str, Any]]) -> int:
    return int(development.get(str(int(player["source_id"])), {}).get("overall") or player.get("overall") or player.get("category") or 60)


def _club_average(players: list[dict[str, Any]], development: dict[str, dict[str, Any]]) -> float:
    vals=sorted((_overall(p,development) for p in players), reverse=True)[:16]
    return (sum(vals)/len(vals)) if vals else 0.0




def _position_group(player: dict[str, Any]) -> str:
    slot=role_for_player(player).squad_slot
    if slot == "GK": return "GK"
    if slot in {"RB","LB","CB"}: return "DEF"
    if slot == "ST": return "ATT"
    return "MID"


def squad_audit(players: list[dict[str, Any]], development: dict[str, dict[str, Any]]) -> dict[str, Any]:
    specialist=squad_role_audit(players)
    strengths: dict[str,list[int]]={}
    for player in players:
        slot=role_for_player(player).squad_slot
        strengths.setdefault(slot,[]).append(_overall(player,development))
    needs=[]
    for raw in specialist["needs"]:
        slot=str(raw["slot"]);vals=strengths.get(slot,[])
        needs.append({**raw,"average":round(sum(vals)/len(vals),1) if vals else 0.0})
    needs.sort(key=lambda row:(-int(row["shortage"]),float(row["average"]),str(row["slot"])))
    broad={"GK":0,"DEF":0,"MID":0,"ATT":0}
    for player in players: broad[_position_group(player)]+=1
    role_coverage_ok=all(int(row["shortage"])==0 for row in needs)
    squad_size=len(players)
    depth_shortage=max(0,MINIMUM_SENIOR_SQUAD_SIZE_9394-squad_size)
    return {
        "squad_size":squad_size,"minimum_squad_size":MINIMUM_SENIOR_SQUAD_SIZE_9394,
        "target_squad_size":TARGET_SENIOR_SQUAD_SIZE_9394,"depth_shortage":depth_shortage,
        "counts":specialist["counts"],"broad_counts":broad,
        "needs":needs,"primary_need":next((row["slot"] for row in needs if int(row["shortage"]) > 0),("DEPTH" if depth_shortage > 0 else None)),
        "role_coverage_ok":role_coverage_ok,"squad_size_ok":depth_shortage==0,
        "coverage_ok":role_coverage_ok and depth_shortage==0,
    }

def renew_ai_contracts(
    *,
    current_date: date,
    controlled_team_id: int,
    players_by_team: dict[int, list[dict[str, Any]]],
    development: dict[str, dict[str, Any]],
    contract_overrides: dict[str, dict[str, Any]],
    seed: int,
    max_renewals: int = 48,
    eligible_team_ids: list[int] | None = None,
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
    team_ids = sorted(set(int(tid) for tid in eligible_team_ids)) if eligible_team_ids is not None else sorted(players_by_team)
    for team_id in team_ids:
        if len(actions) >= max(0, int(max_renewals)):
            break
        if team_id in (0, controlled_team_id):
            continue
        players=players_by_team[team_id]
        if not players:
            continue
        average=_club_average(players,development)
        expiring=[];stable=[]
        for player in players:
            pid=str(int(player["source_id"])); overall=_overall(player,development)
            contract=effective_contract(player,overall=overall,override=contract_overrides.get(pid))
            if int(contract.get("end_year") or 0) == season_end_year:
                expiring.append((overall,player,contract))
            else:
                stable.append(player)
        # Essential roles outrank rating.  Otherwise two low-rated goalkeepers
        # (or all full-backs/strikers covering one job) can expire together and
        # leave a club impossible to repair under its nationality rules.  Each
        # monthly pulse renews one, then the next pulse recalculates the remaining
        # shortage against the already-protected roster.
        stable_audit=squad_role_audit(stable)
        shortages={str(row["slot"]):int(row["shortage"]) for row in stable_audit.get("needs") or [] if int(row["shortage"])>0}
        depth_shortage=max(0,MINIMUM_SENIOR_SQUAD_SIZE_9394-len(stable))
        candidates=[]
        for overall,player,contract in expiring:
            protected_role=sum(shortage for slot,shortage in shortages.items() if position_penalty(player,slot)<=9)
            protected_depth=1 if depth_shortage>0 else 0
            protected=protected_role+protected_depth
            natural_gk=(role_for_player(player).squad_slot=="GK")
            if protected<=0 and overall + 5 < average and rng.random() < .72:
                continue
            candidates.append((protected,1 if natural_gk else 0,overall,player,contract))
        candidates.sort(key=lambda row:(-row[0],-row[1],-row[2],int(row[3]["source_id"])))
        # One negotiation per club and monthly pulse. This keeps the market
        # legible instead of renewing hundreds of contracts on the same day.
        for _,_,overall,player,old in candidates[:1]:
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
    seller_team_ids: list[int] | None = None,
    seller_release_exempt_ids: set[int] | None = None,
    development: dict[str, dict[str, Any]],
    club_finances: dict[str, dict[str, Any]],
    player_team_overrides: dict[str, int],
    contract_overrides: dict[str, dict[str, Any]],
    seed: int,
    max_deals: int = 6,
    signing_allowed=None,
    attraction_score=None,
    foreign_limit_getter=None,
    foreign_predicate=None,
    coach_profile_getter=None,
) -> list[dict[str, Any]]:
    """Execute a deterministic, specialist-position aware AI market pulse.

    Buyers recruit for a concrete shortage.  Sellers are allowed to negotiate
    only players whose departure leaves a playable, positionally covered squad.
    Explicit market-container sellers are exempt from that squad floor: they do
    not compete and exist only to hold real players from non-playable clubs.
    Candidate pools are indexed once by specialist slot so a busy football world
    remains cheap enough to advance between fixtures.
    """
    if max_deals <= 0:
        return []
    rng=Random(seed ^ (current_date.year*100+current_date.month) ^ 0xA19394)
    candidates_buyers=[]
    for tid in eligible_team_ids:
        if tid==controlled_team_id:
            continue
        players=players_by_team.get(tid,[])
        if not players:
            continue
        avg=_club_average(players,development)
        audit=squad_audit(players,development)
        primary=audit["primary_need"]
        shortage=sum(int(row["shortage"]) for row in audit["needs"])
        depth_shortage=max(0,MINIMUM_SENIOR_SQUAD_SIZE_9394-len(players))
        target_gap=max(0,TARGET_SENIOR_SQUAD_SIZE_9394-len(players))
        # A club below the squad-size floor is always a buyer even when versatile
        # players technically cover every specialist role.  If no specialist job
        # is missing, normal depth is the recruitment need.
        primary=primary or "DEPTH"
        need=shortage*2 + depth_shortage*3 + target_gap + max(0,round((70-avg)/4))
        if need<=0:
            continue
        candidates_buyers.append((need+rng.random(),tid,avg,primary))
    candidates_buyers.sort(reverse=True)

    seller_ids=list(dict.fromkeys(int(tid) for tid in (seller_team_ids if seller_team_ids is not None else eligible_team_ids)))
    exempt_sellers={int(tid) for tid in (seller_release_exempt_ids or set())}
    seller_audits={tid:squad_role_audit(players_by_team.get(tid,[])) for tid in set(seller_ids)|set(eligible_team_ids)}
    pool_by_slot:dict[str,list[tuple[int,dict[str,Any]]]]={}
    for seller in seller_ids:
        if seller==controlled_team_id:
            continue
        if seller not in exempt_sellers and len(players_by_team.get(seller,[]))<=MINIMUM_SENIOR_SQUAD_SIZE_9394:
            continue
        for player in players_by_team.get(seller,[]):
            pool_by_slot.setdefault(role_for_player(player).squad_slot,[]).append((seller,player))
    for rows in pool_by_slot.values():
        rows.sort(key=lambda sp:(-_overall(sp[1],development),int(sp[1]["source_id"])))

    def seller_can_release(seller:int, player:dict[str,Any]) -> bool:
        rows=players_by_team.get(seller,[])
        if seller in exempt_sellers:
            return True
        if len(rows)<=MINIMUM_SENIOR_SQUAD_SIZE_9394:
            return False
        natural=role_for_player(player).squad_slot
        if natural=="GK" and sum(1 for p in rows if role_for_player(p).squad_slot=="GK")<=1:
            return False
        audit=seller_audits.get(seller) or squad_role_audit(rows)
        for need in audit.get("needs") or []:
            slot=str(need["slot"]); minimum=int(need["minimum"]); count=int(need["count"])
            if position_penalty(player,slot)<=9 and count<=minimum:
                return False
        # A sale must not make the seller unable to field a regulation XI under
        # its domestic foreign-player limit.  This is separate from positional
        # coverage: a squad can own 20 players and still be legally unusable if
        # too few are domestic/equivalent.
        if foreign_limit_getter is not None and foreign_predicate is not None:
            limit=foreign_limit_getter(seller)
            if limit is not None and not foreign_predicate(seller,player):
                remaining=[p for p in rows if int(p.get("source_id") or 0)!=int(player.get("source_id") or -1)]
                domestic_outfield=sum(1 for p in remaining if not foreign_predicate(seller,p) and role_for_player(p).squad_slot!="GK")
                domestic_keeper=sum(1 for p in remaining if not foreign_predicate(seller,p) and role_for_player(p).squad_slot=="GK")
                usable_domestic=domestic_outfield + (1 if domestic_keeper else 0)
                if usable_domestic < max(0,11-int(limit)):
                    return False
        return True

    actions=[];used_players=set()
    for _,buyer,avg,primary_need in candidates_buyers:
        if len(actions)>=max_deals:
            break
        finance=club_finances.get(str(buyer)) or {}
        cash=int(finance.get("cash") or 0)
        if cash<=0:
            continue
        pool=[]
        source_pool=(
            [(seller,player) for rows in pool_by_slot.values() for seller,player in rows]
            if str(primary_need)=="DEPTH" else pool_by_slot.get(str(primary_need),[])
        )
        for seller,player in source_pool:
            if seller==buyer or seller==controlled_team_id:
                continue
            pid=int(player["source_id"])
            if pid in used_players:
                continue
            overall=_overall(player,development)
            if overall < max(55,round(avg-4)) or overall > round(avg+10):
                continue
            value=estimated_transfer_value(player,overall=overall)
            # Period-scale valuations are intentionally much steeper at the
            # top end.  Let ambitious clubs commit more of their available
            # transfer cash without allowing the AI to spend money it lacks.
            if value > cash*0.78:
                continue
            if not seller_can_release(seller,player):
                continue
            if signing_allowed is not None and not signing_allowed(buyer, player):
                continue
            prestige=float(attraction_score(buyer, seller, player) if attraction_score is not None else 0.0)
            fit_bonus = 0.0
            if coach_profile_getter is not None:
                coach = coach_profile_getter(int(buyer))
                if coach:
                    plan = tactics_from_source_manager(coach)
                    fit_bonus = (float(tactical_fit(player, plan)["score"]) - 60.0) / 10.0
            pool.append((abs(overall-(avg+2))+rng.random()*1.25-prestige-fit_bonus,-overall,pid,seller,player,value))
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
        years=3+(1 if rng.random()<.45 else 0)
        contract_overrides[str(pid)]={
            "start":str(current_date.year),"end":str(current_date.year+years),"end_year":current_date.year+years,
            "salary":salary,"salary_display":f"{salary:,} ptas.".replace(",","."),"loan":False,
            "career_inferred":True,"signed_by_ai":True,
        }
        # Keep this pulse internally coherent: a later deal sees the moved player
        # at his new club and the seller's updated specialist coverage.
        players_by_team[seller]=[p for p in players_by_team.get(seller,[]) if int(p["source_id"])!=pid]
        players_by_team.setdefault(buyer,[]).append(player)
        seller_audits[seller]=squad_role_audit(players_by_team[seller])
        seller_audits[buyer]=squad_role_audit(players_by_team[buyer])
        used_players.add(pid)
        actions.append({"kind":"ai_transfer","date":current_date.isoformat(),"player_id":pid,"from_team_id":seller,"to_team_id":buyer,"fee":fee,"salary":salary,"contract_years":years,"need":primary_need,"coach_fit":round(float(tactical_fit(player,tactics_from_source_manager(coach_profile_getter(int(buyer))))["score"]),1) if coach_profile_getter is not None and coach_profile_getter(int(buyer)) else None})
    return actions

def ensure_ai_squad_coverage(
    *, current_date: date, controlled_team_id: int, eligible_team_ids: list[int],
    players_by_team: dict[int,list[dict[str,Any]]], development: dict[str,dict[str,Any]],
    club_finances: dict[str,dict[str,Any]], player_team_overrides: dict[str,int],
    contract_overrides: dict[str,dict[str,Any]], seed: int, max_signings: int = 120,
    signing_allowed=None, foreign_limit_getter=None, foreign_predicate=None, target_squad_size_getter=None,
    emergency_source_team_ids: list[int] | None = None,
) -> list[dict[str,Any]]:
    """Emergency summer recruitment so AI clubs remain structurally playable.

    Free agents are preferred.  When the free-agent pool is exhausted, callers may
    also expose non-playable market containers (for example Otros-País) as an
    emergency source of *real* historical players.  No synthetic footballer is
    created to satisfy the operational squad floor.  Financial discipline still
    matters for ordinary depth, but a distressed club may always reach eighteen.
    """
    if current_date.month not in (7,8):
        return []
    source_ids=[0]+[int(tid) for tid in (emergency_source_team_ids or []) if int(tid)!=0]
    source_ids=list(dict.fromkeys(source_ids))
    candidates=[(source_id,p) for source_id in source_ids for p in players_by_team.get(source_id,[])]
    active_sources={int(tid) for tid in eligible_team_ids}
    used:set[int]=set();actions=[];rng=Random(seed ^ current_date.year ^ 0xC0A49394)
    def source_rank(source_id:int)->int:
        if source_id==0:return 0
        if source_id not in active_sources:return 1
        return 2
    # Index once. Prefer genuine free agents, then non-playable historical pools,
    # and use surplus players from active clubs only as a last-resort hard-floor repair.
    ranked_all=sorted(candidates,key=lambda sp:(source_rank(sp[0]),-_overall(sp[1],development),int(sp[1]["source_id"])))
    ranked_by_slot:dict[str,list[tuple[int,dict[str,Any]]]]={}
    for slot in SQUAD_ROLE_MINIMUM_9394:
        ranked_by_slot[slot]=sorted(
            (sp for sp in candidates if position_penalty(sp[1],slot)<=9),
            key=lambda sp:(source_rank(sp[0]),-(_overall(sp[1],development)-position_penalty(sp[1],slot)*1.4),position_penalty(sp[1],slot),int(sp[1]["source_id"])),
        )

    def source_can_release(source_id:int, player:dict[str,Any]) -> bool:
        if source_id==0 or source_id not in active_sources:
            return True
        if source_id==controlled_team_id:
            return False
        rows=players_by_team.get(source_id,[])
        pid=int(player.get("source_id") or 0)
        if not any(int(p.get("source_id") or 0)==pid for p in rows):
            return False
        if len(rows)<=MINIMUM_SENIOR_SQUAD_SIZE_9394:
            return False
        natural=role_for_player(player).squad_slot
        if natural=="GK" and sum(1 for p in rows if role_for_player(p).squad_slot=="GK")<=1:
            return False
        audit=squad_role_audit(rows)
        for need in audit.get("needs") or []:
            slot=str(need["slot"]);minimum=int(need["minimum"]);count=int(need["count"])
            if position_penalty(player,slot)<=9 and count<=minimum:
                return False
        if foreign_limit_getter is not None and foreign_predicate is not None:
            limit=foreign_limit_getter(source_id)
            if limit is not None and not foreign_predicate(source_id,player):
                remaining=[p for p in rows if int(p.get("source_id") or 0)!=pid]
                domestic_outfield=sum(1 for p in remaining if not foreign_predicate(source_id,p) and role_for_player(p).squad_slot!="GK")
                domestic_keeper=sum(1 for p in remaining if not foreign_predicate(source_id,p) and role_for_player(p).squad_slot=="GK")
                if domestic_outfield+(1 if domestic_keeper else 0)<max(0,11-int(limit)):
                    return False
        return True

    def eligible_candidate(tid:int, slot:str|None=None, predicate=None, *, allow_active_sources:bool=False):
        for source_id,player in (ranked_by_slot.get(slot,[]) if slot else ranked_all):
            pid=int(player["source_id"])
            if pid in used:
                continue
            if source_id in active_sources and not allow_active_sources:
                continue
            if source_id==tid or not source_can_release(source_id,player):
                continue
            if predicate is not None and not predicate(player):
                continue
            if signing_allowed is not None and not signing_allowed(tid,player):
                continue
            return source_id,player
        return None

    def sign(tid:int, players:list[dict[str,Any]], source_id:int, candidate:dict[str,Any], need:str, *, distress:bool) -> None:
        pid=int(candidate["source_id"]);overall=_overall(candidate,development)
        salary=inferred_annual_salary(candidate,overall=overall)
        player_team_overrides[str(pid)]=tid;used.add(pid)
        if source_id!=0:
            players_by_team[source_id]=[p for p in players_by_team.get(source_id,[]) if int(p.get("source_id") or 0)!=pid]
        players.append(candidate)
        years=2 if distress else 3+(1 if rng.random()<.35 else 0)
        contract_overrides[str(pid)]={
            "start":str(current_date.year),"end":str(current_date.year+years),"end_year":current_date.year+years,
            "salary":salary,"salary_display":f"{salary:,} ptas.".replace(",","."),"loan":False,
            "career_inferred":True,"signed_by_ai":True,"emergency_depth":True,"financial_distress":bool(distress),
        }
        actions.append({
            "kind":"ai_free_agent_signing" if source_id==0 else "ai_market_pool_signing","date":current_date.isoformat(),"player_id":pid,"from_team_id":source_id,"to_team_id":tid,
            "fee":0,"salary":salary,"contract_years":years,"need":need,"financial_distress":bool(distress),
        })

    for tid in sorted(eligible_team_ids):
        if tid==controlled_team_id or len(actions)>=max_signings:
            continue
        players=players_by_team.setdefault(tid,[])
        minimum_squad_size = MINIMUM_SENIOR_SQUAD_SIZE_9394
        target_squad_size = int(target_squad_size_getter(tid) if target_squad_size_getter is not None else TARGET_SENIOR_SQUAD_SIZE_9394)
        target_squad_size = max(minimum_squad_size, min(25, target_squad_size))
        audit=squad_audit(players,development)
        finance=club_finances.get(str(tid)) or {}
        cash=int(finance.get("cash") or 0)

        # Positional floor first.  Compatible source roles may cover nearby jobs.
        for need in audit["needs"]:
            shortage=int(need["shortage"])
            for _ in range(shortage):
                if len(actions)>=max_signings:
                    break
                slot=str(need["slot"])
                picked=eligible_candidate(tid,slot,allow_active_sources=(len(players)<minimum_squad_size or not any(role_for_player(p).squad_slot=="GK" for p in players)))
                if picked is None:
                    break
                source_id,candidate=picked
                salary=inferred_annual_salary(candidate,overall=_overall(candidate,development))
                has_keeper=any(role_for_player(p).squad_slot=="GK" for p in players)
                hard_emergency=len(players)<minimum_squad_size or not has_keeper
                if not hard_emergency and cash < salary//4:
                    break
                sign(tid,players,source_id,candidate,slot,distress=(cash < salary//4))

        # A role audit can be technically covered by versatile players while the
        # actual roster is still too small.  The senior-squad floor is a
        # separate concept from the 11 players required to start a match.
        while len(players)<minimum_squad_size and len(actions)<max_signings:
            has_keeper=any(role_for_player(p).squad_slot=="GK" for p in players)
            picked=eligible_candidate(tid,"GK" if not has_keeper else None,allow_active_sources=True)
            if picked is None:
                break
            source_id,candidate=picked
            sign(tid,players,source_id,candidate,"GK" if not has_keeper else "DEPTH",distress=(cash<=0))

        # Match-day legality is also a squad-building need.  If a competition
        # permits at most N foreign starters, the club needs at least 11-N
        # domestic/equivalent senior players available.  Repair that floor in
        # summer with free agents before the calendar can expose an impossible XI.
        if foreign_limit_getter is not None and foreign_predicate is not None:
            limit=foreign_limit_getter(tid)
            if limit is not None:
                minimum_domestic=max(0,11-int(limit))
                def usable_domestic_count() -> int:
                    outfield=sum(1 for p in players if not foreign_predicate(tid,p) and role_for_player(p).squad_slot!="GK")
                    keepers=sum(1 for p in players if not foreign_predicate(tid,p) and role_for_player(p).squad_slot=="GK")
                    return outfield + (1 if keepers else 0)
                while usable_domestic_count() < minimum_domestic and len(actions)<max_signings:
                    # Extra domestic goalkeepers do not help an XI once one keeper
                    # slot is covered, so prefer an outfield national/equivalent.
                    picked=eligible_candidate(
                        tid,None,
                        predicate=lambda p, team_id=tid: (not foreign_predicate(team_id,p)) and role_for_player(p).squad_slot!="GK",
                        allow_active_sources=True,
                    )
                    if picked is None:
                        picked=eligible_candidate(tid,None,predicate=lambda p, team_id=tid: not foreign_predicate(team_id,p),allow_active_sources=True)
                    if picked is None:
                        break
                    source_id,candidate=picked
                    sign(tid,players,source_id,candidate,"DOMESTIC_QUOTA",distress=(cash<=0))

    # Second pass: only after every club has had the chance to satisfy hard
    # positional, numeric and domestic-quota floors may healthy clubs consume
    # remaining free agents for normal depth.  Doing this inside the first pass
    # let alphabetically early rich clubs exhaust the pool before later clubs
    # could even reach eighteen.
    for tid in sorted(eligible_team_ids):
        if tid==controlled_team_id or len(actions)>=max_signings:
            continue
        players=players_by_team.setdefault(tid,[])
        minimum_squad_size=MINIMUM_SENIOR_SQUAD_SIZE_9394
        if len(players)<minimum_squad_size:
            continue
        target_squad_size=int(target_squad_size_getter(tid) if target_squad_size_getter is not None else TARGET_SENIOR_SQUAD_SIZE_9394)
        target_squad_size=max(minimum_squad_size,min(25,target_squad_size))
        finance=club_finances.get(str(tid)) or {}
        cash=int(finance.get("cash") or 0)
        while len(players)<target_squad_size and len(actions)<max_signings:
            picked=eligible_candidate(tid,None)
            if picked is None:
                break
            source_id,candidate=picked
            salary=inferred_annual_salary(candidate,overall=_overall(candidate,development))
            # Require roughly three months of wage headroom for non-emergency
            # depth; negative/fragile clubs stop at the operational floor.
            if cash < salary//4:
                break
            sign(tid,players,source_id,candidate,"DEPTH",distress=False)
            cash -= max(1,salary//12)
    return actions

