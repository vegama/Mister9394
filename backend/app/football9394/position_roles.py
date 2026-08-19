from __future__ import annotations

"""Historical player specialisation for the supplied 1993 database.

The source MDB contains a ``Rol`` table with eighteen exact football roles.
Historically imported players retain ``primary_role`` as that source id; this
module turns it into a user-facing specialist position and a smaller set of
squad-building slots.  We never infer a modern role when the source already
contains one.
"""

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class PositionRole9394:
    source_id: int
    code: str
    name: str
    squad_slot: str
    side: str = "C"


# Exact labels from basedatos.mdb -> Rol.
ROLES_9394: dict[int, PositionRole9394] = {
    0: PositionRole9394(0, "POR", "Portero", "GK"),
    1: PositionRole9394(1, "LD", "Lateral derecho", "RB", "R"),
    2: PositionRole9394(2, "LI", "Lateral izquierdo", "LB", "L"),
    3: PositionRole9394(3, "DFC-D", "Central derecho", "CB", "R"),
    4: PositionRole9394(4, "DFC-I", "Central izquierdo", "CB", "L"),
    5: PositionRole9394(5, "LIB", "Líbero", "CB"),
    6: PositionRole9394(6, "MCD", "Organizador defensivo", "DM"),
    7: PositionRole9394(7, "MC", "Medio centro organizador", "CM"),
    8: PositionRole9394(8, "MP", "Mediapunta por el centro", "AM"),
    9: PositionRole9394(9, "MD", "Centrocampista derecho", "RM", "R"),
    10: PositionRole9394(10, "ID", "Interior derecho", "RM", "R"),
    11: PositionRole9394(11, "MPD", "Mediapunta derecho", "RW", "R"),
    12: PositionRole9394(12, "ED", "Extremo derecho", "RW", "R"),
    13: PositionRole9394(13, "MI", "Centrocampista izquierdo", "LM", "L"),
    14: PositionRole9394(14, "II", "Interior izquierdo", "LM", "L"),
    15: PositionRole9394(15, "MPI", "Mediapunta izquierdo", "LW", "L"),
    16: PositionRole9394(16, "EI", "Extremo izquierdo", "LW", "L"),
    17: PositionRole9394(17, "DC", "Delantero centro", "ST"),
}


# Match formation slots.  Slots express actual jobs, not only DEF/MED/DEL.
FORMATION_SLOTS_9394: dict[str, tuple[str, ...]] = {
    "4-4-2": ("GK", "RB", "CB", "CB", "LB", "RM", "CM", "CM", "LM", "ST", "ST"),
    "4-3-3": ("GK", "RB", "CB", "CB", "LB", "DM", "CM", "CM", "RW", "ST", "LW"),
    "4-2-3-1": ("GK", "RB", "CB", "CB", "LB", "DM", "DM", "RW", "AM", "LW", "ST"),
    "4-5-1": ("GK", "RB", "CB", "CB", "LB", "DM", "RM", "CM", "AM", "LM", "ST"),
    "4-4-1-1": ("GK", "RB", "CB", "CB", "LB", "RM", "CM", "CM", "LM", "AM", "ST"),
    "4-3-1-2": ("GK", "RB", "CB", "CB", "LB", "DM", "CM", "CM", "AM", "ST", "ST"),
    "4-2-4": ("GK", "RB", "CB", "CB", "LB", "CM", "CM", "RW", "ST", "ST", "LW"),
    "3-5-2": ("GK", "CB", "CB", "CB", "RM", "DM", "CM", "CM", "LM", "ST", "ST"),
    "3-4-3": ("GK", "CB", "CB", "CB", "RM", "CM", "CM", "LM", "RW", "ST", "LW"),
    "3-4-1-2": ("GK", "CB", "CB", "CB", "RM", "CM", "CM", "LM", "AM", "ST", "ST"),
    "5-3-2": ("GK", "RB", "CB", "CB", "CB", "LB", "DM", "CM", "CM", "ST", "ST"),
    "5-4-1": ("GK", "RB", "CB", "CB", "CB", "LB", "RM", "CM", "CM", "LM", "ST"),
    "5-2-3": ("GK", "RB", "CB", "CB", "CB", "LB", "CM", "CM", "RW", "ST", "LW"),
}


# Minimum squad coverage used by the transfer AI.  It is intentionally a
# coverage floor rather than a prescribed tactic: clubs may still specialise.
# Squad-size policy is deliberately separate from the eleven players needed
# to start a match.  Eighteen is the operational floor for a senior squad;
# twenty-two is the normal depth target used by recruitment AI when finances
# allow it.  Match legality still requires an XI and is handled elsewhere.
MINIMUM_SENIOR_SQUAD_SIZE_9394 = 18
TARGET_SENIOR_SQUAD_SIZE_9394 = 22


SQUAD_ROLE_MINIMUM_9394: dict[str, int] = {
    # A squad is not required to own every possible historical role.  The
    # source DB distinguishes eighteen specialisms, but a 4-4-2 club does not
    # need a mediapunta *and* two extremos just to be structurally healthy.
    # These are core jobs; compatible specialist roles count as cover below.
    "GK": 2,
    "RB": 1,
    "LB": 1,
    "CB": 3,
    "CM": 4,
    "RM": 2,
    "LM": 2,
    "ST": 3,
}


# Source role ratings (Jugador.Rol1..Rol18) describe actual polyvalence on a
# 1..100 scale.  The primary source role is treated as natural even in the
# handful of rows where the legacy editor left its matching RolN at zero.
SLOT_SOURCE_ROLES_9394: dict[str, tuple[int, ...]] = {
    "GK": (0,), "RB": (1,), "LB": (2,), "CB": (3, 4, 5), "DM": (6,),
    "CM": (7, 6), "AM": (8,), "RM": (9, 10, 11, 12),
    "LM": (13, 14, 15, 16), "RW": (12, 11, 10, 9),
    "LW": (16, 15, 14, 13), "ST": (17, 8),
}


def source_role_aptitude(player: dict[str, Any], slot: str) -> int:
    role_ids = SLOT_SOURCE_ROLES_9394.get(str(slot).upper(), ())
    ratings = player.get("role_ratings") or {}
    values: list[int] = []
    for role_id in role_ids:
        raw = ratings.get(str(role_id), ratings.get(role_id, 0)) if isinstance(ratings, dict) else 0
        try:
            values.append(int(raw or 0))
        except (TypeError, ValueError):
            pass
    primary = role_for_player(player).source_id
    if primary in role_ids:
        values.append(100)
    return max(values, default=0)


# Penalty in rating points when a player is asked to perform another job.
# The source role remains visible; this only models match-day fit.
_COMPATIBILITY_PENALTY: dict[str, dict[str, int]] = {
    "GK": {"GK": 0},
    "RB": {"RB": 0, "CB": 7, "RM": 8, "RW": 14, "LB": 18},
    "LB": {"LB": 0, "CB": 7, "LM": 8, "LW": 14, "RB": 18},
    "CB": {"CB": 0, "RB": 8, "LB": 8, "DM": 9},
    "DM": {"DM": 0, "CM": 5, "CB": 8, "AM": 13},
    "CM": {"CM": 0, "DM": 5, "AM": 6, "RM": 8, "LM": 8},
    "AM": {"AM": 0, "CM": 6, "RW": 7, "LW": 7, "ST": 10},
    "RM": {"RM": 0, "RW": 4, "CM": 8, "RB": 9, "LM": 16},
    "LM": {"LM": 0, "LW": 4, "CM": 8, "LB": 9, "RM": 16},
    "RW": {"RW": 0, "RM": 4, "AM": 7, "ST": 9, "LW": 17},
    "LW": {"LW": 0, "LM": 4, "AM": 7, "ST": 9, "RW": 17},
    "ST": {"ST": 0, "AM": 10, "RW": 9, "LW": 9},
}


def role_for_player(player: dict[str, Any]) -> PositionRole9394:
    raw = player.get("primary_role")
    try:
        source_id = int(raw)
    except (TypeError, ValueError):
        source_id = -1
    if source_id in ROLES_9394:
        return ROLES_9394[source_id]
    broad = str(player.get("broad_position") or "MED").upper()
    fallback = {"POR": 0, "DEF": 3, "MED": 7, "DEL": 17}.get(broad, 7)
    return ROLES_9394[fallback]


def role_api(player: dict[str, Any]) -> dict[str, Any]:
    role = role_for_player(player)
    return {
        "source_id": role.source_id,
        "code": role.code,
        "name": role.name,
        "squad_slot": role.squad_slot,
        "side": role.side,
    }


def position_penalty(player: dict[str, Any], slot: str) -> int:
    # Goalkeeper is a hard specialist role. Some legacy MDB rows carry a stray
    # Rol1 affinity even for outfield players; that must never outrank an actual
    # goalkeeper when one exists in the squad. Emergency outfield goalkeepers
    # are handled explicitly by the caller, not via residual role affinity.
    natural = role_for_player(player).squad_slot
    if str(slot).upper() == "GK" and natural != "GK":
        return 45
    # Prefer the source's explicit polyvalence ratings for outfield jobs. This
    # prevents a player with a documented secondary role from being approximated
    # by our generic compatibility matrix.
    aptitude = source_role_aptitude(player, slot)
    if aptitude > 0:
        return max(0, round((100 - min(100, aptitude)) * 0.20))
    return int(_COMPATIBILITY_PENALTY.get(natural, {}).get(str(slot).upper(), 24 if natural != "GK" and slot != "GK" else 45))


def position_fit(player: dict[str, Any], slot: str) -> dict[str, Any]:
    penalty = position_penalty(player, slot)
    if penalty == 0:
        label = "Natural"
    elif penalty <= 5:
        label = "Muy compatible"
    elif penalty <= 9:
        label = "Compatible"
    elif penalty <= 14:
        label = "Adaptado"
    else:
        label = "Fuera de posición"
    return {"slot": slot, "penalty": penalty, "label": label, "natural_role": role_api(player)}


def _overall(player: dict[str, Any]) -> int:
    return int(player.get("_selection_overall") or player.get("overall") or player.get("category") or 60)


def assign_players_to_formation(
    players: Iterable[dict[str, Any]],
    formation: str,
    *,
    penalty_cache: dict[tuple[int, str], int] | None = None,
) -> list[dict[str, Any]]:
    """Greedily assign a supplied XI/squad to specialist formation slots.

    The algorithm is deterministic and deliberately cheap enough to run for AI
    clubs.  Scarce jobs (GK/full-backs) are filled before generic central jobs.
    Each output row contains the original player, assigned slot and fit cost.
    """
    available = list(players)
    slots = list(FORMATION_SLOTS_9394.get(formation, FORMATION_SLOTS_9394["4-4-2"]))
    priority = {"GK": 0, "RB": 1, "LB": 1, "RW": 2, "LW": 2, "RM": 2, "LM": 2, "ST": 3, "CB": 4, "DM": 4, "AM": 5, "CM": 6}
    ordered_slots = sorted(enumerate(slots), key=lambda item: (priority.get(item[1], 9), item[0]))
    picked: dict[int, dict[str, Any]] = {}
    used: set[int] = set()
    for index, slot in ordered_slots:
        candidates = []
        for order, player in enumerate(available):
            pid = int(player.get("source_id") or player.get("id") or order + 1)
            if pid in used:
                continue
            cache_key = (pid, str(slot))
            if penalty_cache is not None and cache_key in penalty_cache:
                penalty = penalty_cache[cache_key]
            else:
                penalty = position_penalty(player, slot)
                if penalty_cache is not None:
                    penalty_cache[cache_key] = penalty
            # Position dominates a small rating advantage; a superstar can still
            # cover a nearby job, but a striker will not beat a real goalkeeper.
            overall = _overall(player)
            score = overall - penalty * 1.55
            candidates.append((score, -penalty, overall, -order, pid, player))
        if not candidates:
            break
        candidates.sort(reverse=True, key=lambda row: row[:5])
        _, neg_penalty, _, _, pid, player = candidates[0]
        used.add(pid)
        penalty = -int(neg_penalty)
        label = "Natural" if penalty == 0 else "Muy compatible" if penalty <= 5 else "Compatible" if penalty <= 9 else "Adaptado" if penalty <= 14 else "Fuera de posición"
        picked[index] = {
            "player": player, "player_id": pid, "slot": slot, "penalty": penalty,
            "label": label, "natural_role": role_api(player),
        }
    return [picked[i] for i in range(len(slots)) if i in picked]



def assign_players_to_formation_with_foreign_limit(
    players: Iterable[dict[str, Any]],
    formation: str,
    *,
    foreign_predicate,
    max_foreign: int,
    allow_emergency_outfield_goalkeeper: bool = False,
) -> list[dict[str, Any]]:
    """Build the best legal specialist XI under a foreign-player limit.

    A local greedy swap can fail even when a legal XI exists: if the initial
    specialist assignment consumes all useful domestic outfielders, the only
    unused domestic players may be reserve goalkeepers.  This routine solves
    the *whole* XI at once instead.  With eleven formation slots, a bit-mask
    dynamic programme is small (2**11 states) and still cheap enough for the
    world AI.

    Position remains more important than a small overall-rating advantage.
    Natural goalkeepers are never used as outfield quota fillers.  An outfield
    emergency goalkeeper is considered only when the squad has no natural
    goalkeeper and the caller explicitly allows it.
    """
    available = list(players)
    slots = list(FORMATION_SLOTS_9394.get(formation, FORMATION_SLOTS_9394["4-4-2"]))
    if not slots:
        return []
    max_foreign = max(0, int(max_foreign))
    has_natural_goalkeeper = any(role_for_player(player).squad_slot == "GK" for player in available)

    # Fast path: most historical squads already produce a legal XI when picked
    # purely by football fit.  Running the quota DP for every club in the world
    # made a global matchday audit unnecessarily expensive.  Only invoke the
    # combinatorial rebuild when the best normal XI actually exceeds the quota.
    unconstrained = assign_players_to_formation(available, formation)
    if len(unconstrained) == len(slots):
        foreign_count = sum(1 for item in unconstrained if foreign_predicate(item["player"]))
        emergency_keeper_ok = has_natural_goalkeeper or allow_emergency_outfield_goalkeeper
        if foreign_count <= max_foreign and emergency_keeper_ok:
            return unconstrained

    # Quota-aware minimum-cost matching.  A previous bit-mask DP was exact but
    # became the dominant cost of long careers when J.League/other quota-heavy
    # competitions rebuilt many legal XIs.  The quota is a network capacity:
    # domestic players connect directly to the source; foreign players share a
    # gate with capacity ``max_foreign``.  Player->slot edges encode positional
    # fit and rating, so eleven shortest augmenting paths produce a legal XI in
    # a few thousand operations instead of millions of tuple copies.
    import heapq

    source = 0
    foreign_gate = 1
    player_base = 2
    slot_base = player_base + len(available)
    sink = slot_base + len(slots)
    node_count = sink + 1
    graph: list[list[list[int]]] = [[] for _ in range(node_count)]

    def add_edge(u: int, v: int, capacity: int, cost: int) -> None:
        forward = [v, len(graph[v]), capacity, cost]
        reverse = [u, len(graph[u]), 0, -cost]
        graph[u].append(forward)
        graph[v].append(reverse)

    add_edge(source, foreign_gate, min(max_foreign, len(slots)), 0)
    for player_index, player in enumerate(available):
        pnode = player_base + player_index
        foreign = bool(foreign_predicate(player))
        add_edge(foreign_gate if foreign else source, pnode, 1, 0)
        natural = role_for_player(player).squad_slot
        for slot_index, slot in enumerate(slots):
            if slot == "GK":
                if natural != "GK" and (has_natural_goalkeeper or not allow_emergency_outfield_goalkeeper):
                    continue
            elif natural == "GK":
                # Reserve goalkeepers cannot become quota-filling outfielders.
                continue
            penalty = position_penalty(player, slot)
            utility = _overall(player) * 100 - penalty * 155
            # Keep costs non-negative on initial forward edges; the tiny suffix
            # gives deterministic ties without changing football priorities.
            cost = (12000 - utility) * 1000 + player_index * 20 + slot_index
            add_edge(pnode, slot_base + slot_index, 1, cost)
    for slot_index in range(len(slots)):
        add_edge(slot_base + slot_index, sink, 1, 0)

    flow = 0
    potential = [0] * node_count
    inf = 10**30
    while flow < len(slots):
        dist = [inf] * node_count
        parent: list[tuple[int, int] | None] = [None] * node_count
        dist[source] = 0
        queue: list[tuple[int, int]] = [(0, source)]
        while queue:
            current, u = heapq.heappop(queue)
            if current != dist[u]:
                continue
            for edge_index, edge in enumerate(graph[u]):
                v, _, capacity, cost = edge
                if capacity <= 0:
                    continue
                reduced = cost + potential[u] - potential[v]
                candidate = current + reduced
                if candidate < dist[v]:
                    dist[v] = candidate
                    parent[v] = (u, edge_index)
                    heapq.heappush(queue, (candidate, v))
        if dist[sink] == inf:
            return []
        for node, value in enumerate(dist):
            if value < inf:
                potential[node] += value
        v = sink
        while v != source:
            prev = parent[v]
            if prev is None:
                return []
            u, edge_index = prev
            edge = graph[u][edge_index]
            edge[2] -= 1
            reverse_index = edge[1]
            graph[v][reverse_index][2] += 1
            v = u
        flow += 1

    by_slot: dict[int, dict[str, Any]] = {}
    for player_index, player in enumerate(available):
        pnode = player_base + player_index
        for edge in graph[pnode]:
            v, reverse_index, capacity, _ = edge
            if not (slot_base <= v < slot_base + len(slots)):
                continue
            # A used player->slot edge has zero residual forward capacity and one
            # unit on its reverse edge.
            if capacity != 0 or graph[v][reverse_index][2] <= 0:
                continue
            slot_index = v - slot_base
            slot = slots[slot_index]
            pid = int(player.get("source_id") or player.get("id") or player_index + 1)
            by_slot[slot_index] = {
                "player": player, "player_id": pid, **position_fit(player, slot),
            }
            break
    return [by_slot[i] for i in range(len(slots)) if i in by_slot]

def squad_role_audit(
    players: Iterable[dict[str, Any]],
    *,
    penalty_cache: dict[tuple[int, str], int] | None = None,
) -> dict[str, Any]:
    """Audit specialist squad coverage without demanding every role in the DB.

    Natural roles remain authoritative and visible, but a historically plausible
    compatible specialist can provide depth for a job (for example an interior
    can cover the right-midfield lane).  This avoids forcing every AI club into
    the same modern template while still producing concrete needs such as LB/ST.

    The market AI calls this for hundreds of clubs in the same summer pulse.
    Walk the squad once and evaluate the eight core jobs with the already parsed
    source role instead of calling ``position_penalty`` (and therefore
    ``role_for_player`` + ``source_role_aptitude``) once per player/job pair.
    The exact penalties are still populated in ``penalty_cache`` so every later
    recruitment/release check sees byte-for-byte the same compatibility model.
    """
    rows = list(players)
    core_slots = tuple(SQUAD_ROLE_MINIMUM_9394)
    natural_counts: dict[str, int] = {}
    counts: dict[str, int] = {slot: 0 for slot in core_slots}

    for order, player in enumerate(rows):
        role = role_for_player(player)
        natural = role.squad_slot
        primary = role.source_id
        natural_counts[natural] = natural_counts.get(natural, 0) + 1
        ratings = player.get("role_ratings") or {}
        ratings_dict = ratings if isinstance(ratings, dict) else {}
        pid = int(player.get("source_id") or player.get("id") or order + 1)

        for slot in core_slots:
            key = (pid, slot)
            if penalty_cache is not None and key in penalty_cache:
                penalty = penalty_cache[key]
            else:
                if slot == "GK" and natural != "GK":
                    penalty = 45
                else:
                    role_ids = SLOT_SOURCE_ROLES_9394.get(slot, ())
                    aptitude = 100 if primary in role_ids else 0
                    if aptitude < 100 and ratings_dict:
                        for role_id in role_ids:
                            raw = ratings_dict.get(str(role_id), ratings_dict.get(role_id, 0))
                            try:
                                value = int(raw or 0)
                            except (TypeError, ValueError):
                                continue
                            if value > aptitude:
                                aptitude = value
                    if aptitude > 0:
                        penalty = max(0, round((100 - min(100, aptitude)) * 0.20))
                    else:
                        penalty = int(_COMPATIBILITY_PENALTY.get(natural, {}).get(slot, 24 if natural != "GK" and slot != "GK" else 45))
                if penalty_cache is not None:
                    penalty_cache[key] = penalty
            if penalty <= 9:
                counts[slot] += 1

    needs = [
        {
            "slot": slot, "count": counts[slot], "natural_count": int(natural_counts.get(slot, 0)),
            "minimum": minimum, "shortage": max(0, minimum - counts[slot]),
        }
        for slot, minimum in SQUAD_ROLE_MINIMUM_9394.items()
    ]
    needs.sort(key=lambda row: (-row["shortage"], row["count"], row["slot"]))
    return {
        "counts": counts, "natural_counts": natural_counts, "needs": needs,
        "coverage_ok": all(row["shortage"] == 0 for row in needs),
        "primary_need": next((row["slot"] for row in needs if row["shortage"] > 0), None),
    }
