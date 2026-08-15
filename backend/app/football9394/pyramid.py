from __future__ import annotations

from collections.abc import Iterable, Sequence


def compute_relegations(
    ranked_team_ids: Sequence[str],
    sporting_relegation_slots: int,
    forced_relegation_ids: Iterable[str] = (),
) -> tuple[str, ...]:
    """Resolve relegation when forced reserve-team drops consume a slot.

    `ranked_team_ids` must be ordered best -> worst.  A forced relegation is
    applied first and counts inside the division's normal relegation quota.
    Therefore every forced reserve team above the sporting drop zone saves one
    additional club that otherwise would have gone down on classification.

    If a forced team was already inside the sporting drop zone it does not
    consume a *second* slot.  The function never returns duplicates.
    """

    if sporting_relegation_slots < 0:
        raise ValueError("sporting_relegation_slots no puede ser negativo")
    ranking = list(dict.fromkeys(str(team_id) for team_id in ranked_team_ids))
    ranking_set = set(ranking)
    forced = [str(team_id) for team_id in forced_relegation_ids if str(team_id) in ranking_set]
    forced = list(dict.fromkeys(forced))

    # Forced relegations occupy quota before sporting classification.  If the
    # number of forced drops equals/exceeds the quota, nobody else drops for
    # sporting reasons in this division.
    sporting_needed = max(0, sporting_relegation_slots - len(forced))
    sporting: list[str] = []
    for team_id in reversed(ranking):
        if team_id in forced:
            continue
        sporting.append(team_id)
        if len(sporting) >= sporting_needed:
            break

    # Stable presentation: keep forced clubs at their ranking position, then
    # append the sporting drop-zone order from highest to lowest place.
    result_set = set(forced) | set(sporting)
    return tuple(team_id for team_id in ranking if team_id in result_set)


def select_eligible_promotions(
    ranked_team_ids: Sequence[str],
    promotion_slots: int,
    ineligible_team_ids: Iterable[str] = (),
) -> tuple[str, ...]:
    """Select promotion places while skipping ineligible reserve teams."""

    if promotion_slots < 0:
        raise ValueError("promotion_slots no puede ser negativo")
    ineligible = {str(team_id) for team_id in ineligible_team_ids}
    selected: list[str] = []
    for raw_team_id in ranked_team_ids:
        team_id = str(raw_team_id)
        if team_id in ineligible or team_id in selected:
            continue
        selected.append(team_id)
        if len(selected) >= promotion_slots:
            break
    return tuple(selected)


def reserve_forced_drop_required(*, parent_target_division: str, reserve_current_division: str) -> bool:
    """A reserve side must drop if its parent is entering its division."""

    return bool(parent_target_division and reserve_current_division and parent_target_division == reserve_current_division)
