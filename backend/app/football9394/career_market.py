from __future__ import annotations

"""Compact but real transfer/contract economy for the playable 93/94 career."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any


# Career market-value anchors in 1993-94 pesetas.  The source club ``budget``
# field is useful for hierarchy but is not a complete annual accounts figure,
# so transfer values must not be compressed to that field alone.  The curve is
# deliberately steep at elite level: ordinary squad players remain affordable
# while genuine world stars occupy the hundreds-of-millions/billion-peseta
# scale expected by a period football manager.  These are gameplay estimates,
# not claims about each player's historical transfer fee.
_TRANSFER_VALUE_ANCHORS: tuple[tuple[int, int], ...] = (
    (40, 250_000), (45, 500_000), (50, 1_200_000), (55, 2_500_000),
    (60, 5_000_000), (65, 10_000_000), (70, 20_000_000), (75, 38_000_000),
    (80, 85_000_000), (85, 180_000_000), (89, 450_000_000), (90, 600_000_000),
    (95, 1_200_000_000), (100, 2_000_000_000),
)


def _interpolate_money(rating: int, anchors: tuple[tuple[int, int], ...], *, floor: int) -> int:
    rating = max(1, min(100, int(rating)))
    if rating <= anchors[0][0]:
        return int(floor)
    for (r0, v0), (r1, v1) in zip(anchors, anchors[1:]):
        if rating <= r1:
            ratio = (rating - r0) / max(1, r1 - r0)
            value = v0 + (v1 - v0) * ratio
            return max(int(floor), int(round(value / 50_000.0) * 50_000))
    return int(anchors[-1][1])


@lru_cache(maxsize=128)
def _transfer_value_for_rating(rating: int) -> int:
    # Transfer value depends only on the effective rating. Market screens and
    # AI windows ask this question thousands of times per pulse, while there
    # are only 100 possible ratings. Cache the curve, not player-specific data.
    return _interpolate_money(int(rating), _TRANSFER_VALUE_ANCHORS, floor=250_000)


def estimated_transfer_value(player: dict[str, Any], *, overall: int | None = None) -> int:
    rating = int(overall or player.get("overall") or player.get("category") or 60)
    return _transfer_value_for_rating(rating)


def initial_finances(team: dict[str, Any]) -> dict[str, Any]:
    # Compatibility shim for older callers.  H1 moved the canonical financial
    # baseline to career_economy so treasury and transfer budget cannot diverge.
    from .career_economy import initial_club_finances
    return initial_club_finances(team)


def matchday_income(team: dict[str, Any]) -> int:
    members = max(0, int(team.get("members") or 0))
    # ``Socios`` in the historical source is not a literal turnstile count and
    # spans wildly different national conventions.  A linear multiplier made
    # the clubs with the largest source values print money forever.  Square-root
    # scaling preserves the advantage of a huge support without letting it grow
    # twenty times faster than a normal top-flight club.
    return max(100_000, min(2_500_000, round((members ** 0.5) * 5_000)))


def negotiate_transfer(
    *, player: dict[str, Any], current_overall: int, buyer_cash: int,
    fee_offer: int, salary_offer: int, contract_years: int,
) -> dict[str, Any]:
    value = estimated_transfer_value(player, overall=current_overall)
    minimum = round(value * (0.88 if player.get("contract", {}).get("end") else 0.72))
    accepted = fee_offer >= minimum and fee_offer <= buyer_cash and contract_years >= 1 and salary_offer >= 0
    if accepted:
        return {"accepted": True, "fee": int(fee_offer), "salary": int(salary_offer), "contract_years": int(contract_years), "estimated_value": value, "minimum": minimum}
    counter = min(max(minimum, fee_offer), max(minimum, value))
    reason = "presupuesto_insuficiente" if fee_offer > buyer_cash else "oferta_insuficiente" if fee_offer < minimum else "contrato_invalido"
    return {"accepted": False, "counter_fee": int(counter), "estimated_value": value, "minimum": minimum, "reason": reason}
