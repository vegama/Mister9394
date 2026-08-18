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

from .career_economy import annual_wage_commitment, effective_contract, inferred_annual_salary, receive_transfer_funds, spend_transfer_funds, transfer_spending_power, wage_budget_headroom
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
    club_finances: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Resolve AI retention plans in fair, batched contract cycles.

    Specialist coverage is protected first, then enough useful expiring players
    are retained to approach the 22-man target.  Oversized squads may shrink
    naturally.  Plans are applied round-robin so a global cap can never let a
    low/source-order club consume every negotiation before later clubs get one.
    """
    if current_date.month < 1 or current_date.month > 6:
        return []
    rng=Random(seed ^ (current_date.year*100+current_date.month) ^ 0x9394C0)
    season_end_year=current_date.year
    team_ids = sorted(set(int(tid) for tid in eligible_team_ids)) if eligible_team_ids is not None else sorted(players_by_team)
    limit=max(0,int(max_renewals))
    if limit<=0:
        return []

    plans:dict[int,list[tuple[int,dict[str,Any],dict[str,Any]]]]={}
    for team_id in team_ids:
        if team_id in (0, controlled_team_id):
            continue
        players=players_by_team.get(team_id,[])
        if not players:
            continue
        average=_club_average(players,development)
        expiring=[]; stable=[]
        for player in players:
            pid=str(int(player["source_id"])); overall=_overall(player,development)
            contract=effective_contract(player,overall=overall,override=contract_overrides.get(pid))
            if int(contract.get("end_year") or 0)==season_end_year:
                expiring.append((overall,player,contract))
            else:
                stable.append(player)
        if not expiring:
            continue
        stable_audit=squad_role_audit(stable)
        shortages={str(row["slot"]):int(row["shortage"]) for row in stable_audit.get("needs") or [] if int(row["shortage"])>0}
        target_gap=max(0,TARGET_SENIOR_SQUAD_SIZE_9394-len(stable))
        ranked=[]
        for overall,player,contract in expiring:
            compatible=[slot for slot,shortage in shortages.items() if shortage>0 and position_penalty(player,slot)<=9]
            protected=sum(shortages[slot] for slot in compatible)
            natural_gk=role_for_player(player).squad_slot=="GK"
            ranked.append((protected,1 if natural_gk else 0,overall,player,contract,compatible))
        ranked.sort(key=lambda row:(-row[0],-row[1],-row[2],int(row[3]["source_id"])))
        chosen=[]
        for _,_,overall,player,old,compatible in ranked:
            role_needed=any(shortages.get(slot,0)>0 for slot in compatible)
            depth_needed=len(chosen)<target_gap
            core_player=overall>=average+4 and len(stable)+len(chosen)<TARGET_SENIOR_SQUAD_SIZE_9394+2
            if not (role_needed or depth_needed or core_player):
                continue
            chosen.append((overall,player,old))
            for slot in compatible:
                if shortages.get(slot,0)>0:
                    shortages[slot]-=1
        if chosen:
            plans[int(team_id)]=chosen

    # One action per club per round preserves fairness under deliberately small
    # caps while still allowing the normal annual cycle to retain several men.
    actions=[]; round_index=0
    ordered=sorted(plans)
    while len(actions)<limit:
        progressed=False
        for team_id in ordered:
            rows=plans[team_id]
            if round_index>=len(rows):
                continue
            overall,player,old=rows[round_index]; progressed=True
            pid=str(int(player["source_id"])); average=_club_average(players_by_team.get(team_id,[]),development)
            years=2+(1 if overall>=average+3 else 0)
            salary=round(max(int(old.get("salary") or 0),inferred_annual_salary(player,overall=overall))*(1.04+max(0,overall-average)/100))
            if club_finances is not None:
                finance=club_finances.get(str(team_id)) or {}
                room=wage_budget_headroom(
                    finance,players=players_by_team.get(team_id,[]),development=development,
                    contract_overrides=contract_overrides,exclude_player_id=int(pid),
                )
                # Core/coverage renewals may consume the whole envelope, but an AI
                # club does not sign an unaffordable raise and create hidden wage debt.
                if salary>room:
                    continue
            contract_overrides[pid]={
                **old,"start":str(current_date.year),"end":str(current_date.year+years),"end_year":current_date.year+years,
                "salary":salary,"salary_display":f"{salary:,} ptas.".replace(",","."),"career_inferred":True,"renewed_by_ai":True,
            }
            actions.append({"kind":"ai_renewal","team_id":team_id,"player_id":int(pid),"years":years,"salary":salary,"date":current_date.isoformat()})
            if len(actions)>=limit:
                break
        if not progressed:
            break
        round_index+=1
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
    buyer_plans: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Execute one deterministic, position-aware market pulse.

    V1.0-G keeps the market behaviour but avoids re-scanning the complete world
    for every buyer. Candidates are bucketed once by specialist slot and rating;
    a club therefore inspects only the plausible quality band for its need.
    Replacement buyers created by a sale are queued inside the same pulse, so a
    second full-world transfer pass is unnecessary during long careers.
    """
    if max_deals <= 0:
        return []
    rng=Random(seed ^ (current_date.year*100+current_date.month) ^ 0xA19394)
    candidates_buyers=[]
    queued_buyers:set[int]=set()
    buyer_average:dict[int,float]={}
    for tid in eligible_team_ids:
        if tid==controlled_team_id:
            continue
        players=players_by_team.get(tid,[])
        if not players:
            continue
        avg=_club_average(players,development); buyer_average[int(tid)]=avg
        plan=(buyer_plans or {}).get(str(int(tid))) if buyer_plans is not None else None
        if plan:
            primary=str(plan.get("primary_need") or "DEPTH")
            shortage=sum(int(row.get("shortage") or 0) for row in plan.get("needs") or [])
            depth_shortage=max(0,MINIMUM_SENIOR_SQUAD_SIZE_9394-len(players))
            target_gap=max(0,TARGET_SENIOR_SQUAD_SIZE_9394-len(players))
            need=max(1,round(float(plan.get("urgency") or 0)/18.0))+shortage+depth_shortage*2+target_gap
        else:
            audit=squad_audit(players,development)
            primary=audit["primary_need"] or "DEPTH"
            shortage=sum(int(row["shortage"]) for row in audit["needs"])
            depth_shortage=max(0,MINIMUM_SENIOR_SQUAD_SIZE_9394-len(players))
            target_gap=max(0,TARGET_SENIOR_SQUAD_SIZE_9394-len(players))
            need=shortage*2 + depth_shortage*3 + target_gap + max(0,round((70-avg)/4))
        if need<=0:
            continue
        candidates_buyers.append((need+rng.random(),int(tid),avg,str(primary),None))
        queued_buyers.add(int(tid))
    candidates_buyers.sort(reverse=True)

    seller_ids=list(dict.fromkeys(int(tid) for tid in (seller_team_ids if seller_team_ids is not None else eligible_team_ids)))
    exempt_sellers={int(tid) for tid in (seller_release_exempt_ids or set())}

    # Release safety is a property of the seller's current squad, not of the
    # prospective buyer.  Older code recomputed the same role/foreign-player
    # checks for every buyer/candidate pair; in a 20-30 year career that became
    # the dominant summer cost.  Cache the result once per seller and invalidate
    # only the two squads touched by an actual deal.
    penalty_cache:dict[tuple[int,str],int]={}
    foreign_cache:dict[tuple[int,int],bool]={}

    def cached_penalty(player:dict[str,Any],slot:str)->int:
        pid=int(player.get("source_id") or 0); key=(pid,str(slot))
        value=penalty_cache.get(key)
        if value is None:
            value=int(position_penalty(player,slot)); penalty_cache[key]=value
        return value

    def cached_foreign(team_id:int,player:dict[str,Any])->bool:
        if foreign_predicate is None:
            return False
        pid=int(player.get("source_id") or 0); key=(int(team_id),pid)
        if key not in foreign_cache:
            foreign_cache[key]=bool(foreign_predicate(int(team_id),player))
        return foreign_cache[key]

    releaseable_by_seller:dict[int,set[int]]={}
    def rebuild_releaseable(seller:int)->set[int]:
        rows=players_by_team.get(int(seller),[])
        if seller in exempt_sellers:
            safe={int(p.get("source_id") or 0) for p in rows}
            releaseable_by_seller[int(seller)]=safe
            return safe
        if len(rows)<=MINIMUM_SENIOR_SQUAD_SIZE_9394:
            releaseable_by_seller[int(seller)]=set(); return set()
        audit=squad_role_audit(rows)
        guarded=[(str(need["slot"]),int(need["minimum"]),int(need["count"])) for need in audit.get("needs") or []]
        natural_gks=sum(1 for p in rows if role_for_player(p).squad_slot=="GK")
        limit=foreign_limit_getter(int(seller)) if foreign_limit_getter is not None else None
        domestic_outfield=0; domestic_keeper=0
        if limit is not None and foreign_predicate is not None:
            for p in rows:
                if cached_foreign(int(seller),p):
                    continue
                if role_for_player(p).squad_slot=="GK": domestic_keeper+=1
                else: domestic_outfield+=1
        required_domestic=max(0,11-int(limit)) if limit is not None else 0
        safe=set()
        for player in rows:
            pid=int(player.get("source_id") or 0); natural=role_for_player(player).squad_slot
            if natural=="GK" and natural_gks<=1:
                continue
            if any(count<=minimum and cached_penalty(player,slot)<=9 for slot,minimum,count in guarded):
                continue
            if limit is not None and foreign_predicate is not None and not cached_foreign(int(seller),player):
                outfield_left=domestic_outfield-(0 if natural=="GK" else 1)
                keeper_left=domestic_keeper-(1 if natural=="GK" else 0)
                usable=max(0,outfield_left)+(1 if keeper_left>0 else 0)
                if usable<required_domestic:
                    continue
            safe.add(pid)
        releaseable_by_seller[int(seller)]=safe
        return safe

    # Releaseability is intentionally lazy.  A pulse may inspect only a few
    # dozen plausible sellers; auditing every one of the 400+ clubs up front was
    # pure summer overhead and dominated long-career soak time.

    # Rating buckets are tiny (the playable scale is bounded), so a buyer only
    # sees footballers inside avg-4..avg+10 instead of thousands of irrelevant
    # rows. DEPTH uses the same buckets without requiring a particular slot.
    pool_by_slot_rating:dict[str,dict[int,list[tuple[int,dict[str,Any]]]]]={}
    pool_by_rating:dict[int,list[tuple[int,dict[str,Any]]]]={}
    for seller in seller_ids:
        if seller==controlled_team_id:
            continue
        if seller not in exempt_sellers and len(players_by_team.get(seller,[]))<=MINIMUM_SENIOR_SQUAD_SIZE_9394:
            continue
        for player in players_by_team.get(seller,[]):
            overall=_overall(player,development)
            pair=(seller,player)
            pool_by_rating.setdefault(overall,[]).append(pair)
            slot=role_for_player(player).squad_slot
            pool_by_slot_rating.setdefault(slot,{}).setdefault(overall,[]).append(pair)
    for bucket in pool_by_rating.values():
        bucket.sort(key=lambda sp:int(sp[1]["source_id"]))
    for ratings in pool_by_slot_rating.values():
        for bucket in ratings.values():
            bucket.sort(key=lambda sp:int(sp[1]["source_id"]))

    def seller_can_release(seller:int, player:dict[str,Any]) -> bool:
        seller=int(seller);pid=int(player.get("source_id") or 0)
        if seller not in releaseable_by_seller:
            rebuild_releaseable(seller)
        return pid in releaseable_by_seller.get(seller,set())

    actions=[]; used_players=set(); sold_in_pulse:dict[int,int]={}; index=0
    while index < len(candidates_buyers) and len(actions) < max_deals:
        _,buyer,avg,primary_need,replacement_for=candidates_buyers[index]; index+=1
        finance=club_finances.get(str(buyer)) or {}; cash=transfer_spending_power(finance)
        if cash<=0:
            continue
        lo=max(55,round(avg-4)); hi=round(avg+10)
        ratings=pool_by_rating if primary_need=="DEPTH" else pool_by_slot_rating.get(str(primary_need),{})
        source_pool=[]
        for rating in range(lo,hi+1):
            source_pool.extend(ratings.get(rating,()))
        if not source_pool:
            continue
        coach=coach_profile_getter(int(buyer)) if coach_profile_getter is not None else None
        coach_plan=tactics_from_source_manager(coach) if coach else None
        # First rank by cheap sporting/financial plausibility.  Registration,
        # seller-cover and tactical-fit checks are substantially more expensive
        # and only matter for the best handful of candidates a club would
        # realistically discuss with its staff.
        shortlist=[]
        for seller,player in source_pool:
            if seller==buyer or seller==controlled_team_id:
                continue
            pid=int(player["source_id"])
            if pid in used_players:
                continue
            overall=_overall(player,development)
            value=estimated_transfer_value(player,overall=overall)
            if value > cash*0.78:
                continue
            expected_salary=round(inferred_annual_salary(player,overall=overall)*1.12)
            if expected_salary>wage_budget_headroom(
                finance,players=players_by_team.get(buyer,[]),development=development,contract_overrides=contract_overrides
            ):
                continue
            prestige=float(attraction_score(buyer, seller, player) if attraction_score is not None else 0.0)
            shortlist.append((abs(overall-(avg+2))+rng.random()*1.25-prestige,-overall,pid,seller,player,value))
        if not shortlist:
            continue
        shortlist.sort(key=lambda x:(x[0],x[1],x[2]))
        pool=[]
        for cheap_score,neg_overall,pid,seller,player,value in shortlist[:96]:
            if not seller_can_release(seller,player):
                continue
            if signing_allowed is not None and not signing_allowed(buyer,player):
                continue
            fit_score=float(tactical_fit(player,coach_plan)["score"]) if coach_plan is not None else 60.0
            fit_bonus=(fit_score-60.0)/10.0
            pool.append((cheap_score-fit_bonus,neg_overall,pid,seller,player,value,fit_score))
        if not pool:
            continue
        pool.sort(key=lambda x:(x[0],x[1],x[2]))
        _,_,pid,seller,player,value,fit_score=pool[0]
        fee=max(250_000,round(value*(0.90+rng.random()*0.16)))
        if fee>cash:
            continue
        buyer_fin=club_finances[str(buyer)]; seller_fin=club_finances[str(seller)]
        spend_transfer_funds(buyer_fin,fee,recorded_fee=fee)
        receive_transfer_funds(seller_fin,fee)
        player_team_overrides[str(pid)]=buyer
        overall=_overall(player,development)
        salary=round(inferred_annual_salary(player,overall=overall)*(1.02+rng.random()*.10))
        years=3+(1 if rng.random()<.45 else 0)
        contract_overrides[str(pid)]={
            "start":str(current_date.year),"end":str(current_date.year+years),"end_year":current_date.year+years,
            "salary":salary,"salary_display":f"{salary:,} ptas.".replace(",","."),"loan":False,
            "career_inferred":True,"signed_by_ai":True,
        }
        players_by_team[seller]=[p for p in players_by_team.get(seller,[]) if int(p["source_id"])!=pid]
        players_by_team.setdefault(buyer,[]).append(player)
        rebuild_releaseable(int(seller)); rebuild_releaseable(int(buyer))
        used_players.add(pid)
        deal={"kind":"ai_transfer","date":current_date.isoformat(),"player_id":pid,"from_team_id":seller,"to_team_id":buyer,"fee":fee,"salary":salary,"contract_years":years,"need":primary_need,"coach_fit":round(fit_score,1) if coach_plan is not None else None}
        if replacement_for is not None:
            deal["replacement_chain_for_player_id"]=int(replacement_for)
        actions.append(deal); sold_in_pulse[int(seller)]=pid

        # A sale may create the next recruitment need. Queue the seller once as
        # a replacement buyer rather than launching a second global market pass.
        if seller not in (controlled_team_id,0) and seller in eligible_team_ids and seller not in queued_buyers and len(actions)<max_deals:
            rows=players_by_team.get(seller,[])
            if rows:
                new_avg=_club_average(rows,development); buyer_average[seller]=new_avg
                audit=squad_audit(rows,development); need_slot=str(audit.get("primary_need") or role_for_player(player).squad_slot or "DEPTH")
                candidates_buyers.append((999.0-rng.random(),seller,new_avg,need_slot,pid));queued_buyers.add(seller)
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
    active_sources={int(tid) for tid in eligible_team_ids}
    used:set[int]=set();actions=[];rng=Random(seed ^ current_date.year ^ 0xC0A49394)

    # Audit clubs *before* building a global candidate index.  Mature careers
    # usually need only a handful of positional repairs; indexing every player
    # against every role each July made the cost grow with the database rather
    # than with the actual amount of summer work.
    team_meta:dict[int,dict[str,Any]]={}
    required_slots:set[str]=set()
    any_repair=False
    for tid in sorted(active_sources):
        if tid==controlled_team_id:
            continue
        players=players_by_team.setdefault(tid,[])
        minimum_squad_size=MINIMUM_SENIOR_SQUAD_SIZE_9394
        target_squad_size=int(target_squad_size_getter(tid) if target_squad_size_getter is not None else TARGET_SENIOR_SQUAD_SIZE_9394)
        target_squad_size=max(minimum_squad_size,min(25,target_squad_size))
        audit=squad_audit(players,development)
        domestic_shortage=0
        if foreign_limit_getter is not None and foreign_predicate is not None:
            limit=foreign_limit_getter(tid)
            if limit is not None:
                minimum_domestic=max(0,11-int(limit))
                domestic_outfield=sum(1 for p in players if not foreign_predicate(tid,p) and role_for_player(p).squad_slot!="GK")
                domestic_keeper=any(not foreign_predicate(tid,p) and role_for_player(p).squad_slot=="GK" for p in players)
                domestic_shortage=max(0,minimum_domestic-(domestic_outfield+(1 if domestic_keeper else 0)))
        needs=[row for row in audit["needs"] if int(row.get("shortage") or 0)>0]
        for row in needs:
            required_slots.add(str(row["slot"]))
        if not any(role_for_player(p).squad_slot=="GK" for p in players):
            required_slots.add("GK")
        needs_hard=bool(needs or len(players)<minimum_squad_size or domestic_shortage>0)
        needs_depth=len(players)<target_squad_size
        any_repair=any_repair or needs_hard or needs_depth
        team_meta[tid]={
            "audit":audit,"minimum":minimum_squad_size,"target":target_squad_size,
            "domestic_shortage":domestic_shortage,"needs_hard":needs_hard,"needs_depth":needs_depth,
        }

    if not any_repair:
        return []

    source_ids=[0]+[int(tid) for tid in (emergency_source_team_ids or []) if int(tid)!=0]
    source_ids=list(dict.fromkeys(source_ids))
    candidates=[(source_id,p) for source_id in source_ids for p in players_by_team.get(source_id,[])]
    def source_rank(source_id:int)->int:
        if source_id==0:return 0
        if source_id not in active_sources:return 1
        return 2
    # Index once. Prefer genuine free agents, then non-playable historical pools,
    # and use surplus players from active clubs only as a last-resort hard-floor repair.
    ranked_all=sorted(candidates,key=lambda sp:(source_rank(sp[0]),-_overall(sp[1],development),int(sp[1]["source_id"])))
    ranked_by_slot:dict[str,list[tuple[int,dict[str,Any]]]]={}
    affordable_by_slot:dict[str,list[tuple[int,dict[str,Any]]]]={}
    for slot in required_slots:
        scored=[]
        for sp in candidates:
            penalty=position_penalty(sp[1],slot)
            if penalty<=9:
                scored.append((sp,penalty))
        scored.sort(key=lambda item:(source_rank(item[0][0]),-(_overall(item[0][1],development)-item[1]*1.4),item[1],int(item[0][1]["source_id"])))
        ranked_by_slot[slot]=[sp for sp,_penalty in scored]
        affordable=sorted(scored,key=lambda item:(source_rank(item[0][0]),inferred_annual_salary(item[0][1],overall=_overall(item[0][1],development)),item[1],-_overall(item[0][1],development),int(item[0][1]["source_id"])))
        affordable_by_slot[slot]=[sp for sp,_penalty in affordable]
    affordable_all=sorted(
        candidates,
        key=lambda sp:(source_rank(sp[0]),inferred_annual_salary(sp[1],overall=_overall(sp[1],development)),-_overall(sp[1],development),int(sp[1]["source_id"])),
    )

    release_cache:dict[int,dict[str,Any]]={}
    def release_profile(source_id:int) -> dict[str,Any]:
        cached=release_cache.get(source_id)
        if cached is not None:
            return cached
        rows=players_by_team.get(source_id,[])
        profile={
            "pids":{int(p.get("source_id") or 0) for p in rows},
            "size":len(rows),
            "keepers":sum(1 for p in rows if role_for_player(p).squad_slot=="GK"),
            "audit":squad_role_audit(rows),
        }
        if foreign_limit_getter is not None and foreign_predicate is not None:
            limit=foreign_limit_getter(source_id)
            if limit is not None:
                profile["domestic_minimum"]=max(0,11-int(limit))
                profile["domestic_outfield"]={int(p.get("source_id") or 0) for p in rows if not foreign_predicate(source_id,p) and role_for_player(p).squad_slot!="GK"}
                profile["domestic_keepers"]={int(p.get("source_id") or 0) for p in rows if not foreign_predicate(source_id,p) and role_for_player(p).squad_slot=="GK"}
        release_cache[source_id]=profile
        return profile

    def source_can_release(source_id:int, player:dict[str,Any]) -> bool:
        if source_id==0 or source_id not in active_sources:
            return True
        if source_id==controlled_team_id:
            return False
        profile=release_profile(source_id)
        pid=int(player.get("source_id") or 0)
        if pid not in profile["pids"]:
            return False
        if int(profile["size"])<=MINIMUM_SENIOR_SQUAD_SIZE_9394:
            return False
        natural=role_for_player(player).squad_slot
        if natural=="GK" and int(profile["keepers"])<=1:
            return False
        for need in profile["audit"].get("needs") or []:
            slot=str(need["slot"]);minimum=int(need["minimum"]);count=int(need["count"])
            if position_penalty(player,slot)<=9 and count<=minimum:
                return False
        minimum_domestic=profile.get("domestic_minimum")
        if minimum_domestic is not None and pid in (profile.get("domestic_outfield") or set()) | (profile.get("domestic_keepers") or set()):
            outfield=set(profile.get("domestic_outfield") or set()); keepers=set(profile.get("domestic_keepers") or set())
            outfield.discard(pid); keepers.discard(pid)
            if len(outfield)+(1 if keepers else 0)<int(minimum_domestic):
                return False
        return True

    def eligible_candidate(tid:int, slot:str|None=None, predicate=None, *, allow_active_sources:bool=False, prefer_affordable:bool=False):
        if prefer_affordable:
            pool=affordable_by_slot.get(slot,[]) if slot else affordable_all
        else:
            pool=ranked_by_slot.get(slot,[]) if slot else ranked_all
        for source_id,player in pool:
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
            release_cache.pop(source_id,None)
        players.append(candidate)
        years=2 if distress else 3+(1 if rng.random()<.35 else 0)
        contract_overrides[str(pid)]={
            "start":str(current_date.year),"end":str(current_date.year+years),"end_year":current_date.year+years,
            "salary":salary,"salary_display":f"{salary:,} ptas.".replace(",","."),"loan":False,
            "career_inferred":True,"signed_by_ai":True,"emergency_depth":True,"financial_distress":bool(distress),
        }
        finance=club_finances.get(str(tid))
        if finance is not None:
            committed=annual_wage_commitment(players,development=development,contract_overrides=contract_overrides)
            finance["wage_budget_annual"]=max(int(finance.get("wage_budget_annual") or 0),committed)
        actions.append({
            "kind":"ai_free_agent_signing" if source_id==0 else "ai_market_pool_signing","date":current_date.isoformat(),"player_id":pid,"from_team_id":source_id,"to_team_id":tid,
            "fee":0,"salary":salary,"contract_years":years,"need":need,"financial_distress":bool(distress),
        })

    for tid in sorted(eligible_team_ids):
        if tid==controlled_team_id or len(actions)>=max_signings:
            continue
        players=players_by_team.setdefault(tid,[])
        meta=team_meta.get(tid) or {}
        minimum_squad_size=int(meta.get("minimum") or MINIMUM_SENIOR_SQUAD_SIZE_9394)
        target_squad_size=int(meta.get("target") or TARGET_SENIOR_SQUAD_SIZE_9394)
        audit=meta.get("audit") or squad_audit(players,development)
        finance=club_finances.get(str(tid)) or {}
        cash=int(finance.get("cash") or 0)

        # Positional floor first.  Compatible source roles may cover nearby jobs.
        for need in audit["needs"]:
            shortage=int(need["shortage"])
            for _ in range(shortage):
                if len(actions)>=max_signings:
                    break
                slot=str(need["slot"])
                has_keeper=any(role_for_player(p).squad_slot=="GK" for p in players)
                # Rows in audit["needs"] are minimum positional coverage, not
                # aspirational depth.  Repair them even under financial stress,
                # but use the cheapest suitable player rather than a star.
                hard_emergency=True
                picked=eligible_candidate(
                    tid,slot,allow_active_sources=True,prefer_affordable=True
                )
                if picked is None:
                    break
                source_id,candidate=picked
                salary=inferred_annual_salary(candidate,overall=_overall(candidate,development))
                wage_room=wage_budget_headroom(finance,players=players,development=development,contract_overrides=contract_overrides)
                if not hard_emergency and (cash < salary//4 or salary>wage_room):
                    break
                sign(tid,players,source_id,candidate,slot,distress=(cash < salary//4))

        # A role audit can be technically covered by versatile players while the
        # actual roster is still too small.  The senior-squad floor is a
        # separate concept from the 11 players required to start a match.
        while len(players)<minimum_squad_size and len(actions)<max_signings:
            has_keeper=any(role_for_player(p).squad_slot=="GK" for p in players)
            picked=eligible_candidate(tid,"GK" if not has_keeper else None,allow_active_sources=True,prefer_affordable=True)
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
                        allow_active_sources=True,prefer_affordable=True,
                    )
                    if picked is None:
                        picked=eligible_candidate(tid,None,predicate=lambda p, team_id=tid: not foreign_predicate(team_id,p),allow_active_sources=True,prefer_affordable=True)
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
            # Require both short-term cash and annual wage-budget headroom for
            # non-emergency depth; the hard 18-player floor remains protected.
            wage_room=wage_budget_headroom(finance,players=players,development=development,contract_overrides=contract_overrides)
            if cash < salary//4 or salary>wage_room:
                break
            sign(tid,players,source_id,candidate,"DEPTH",distress=False)
            cash -= max(1,salary//12)
    return actions

