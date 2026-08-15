from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LawsOfGame9394:
    """Core Laws of the Game that the football simulator must obey.

    These are not competition-format rules.  They are the global match laws
    for the 1993-94 season and are kept in one immutable object so the engine
    cannot accidentally inherit modern defaults.
    """

    players_per_team: int = 11
    minimum_players_recommended: int = 7
    normal_half_minutes: int = 45
    halftime_max_minutes: int = 5
    max_named_substitutes: int = 5
    max_used_substitutes: int = 2
    substituted_player_may_return: bool = False
    backpass_to_goalkeeper_hands_allowed: bool = False
    goalkeeper_max_steps_in_control: int = 4
    offside_requires_two_opponents: bool = True
    direct_goal_from_throw_in_allowed: bool = False


# IFAB, Laws of the Game 1993-94.  Among other details, Law III limits an
# official competition to at most two used substitutes chosen from at most
# five named substitutes; Law VII specifies two 45-minute halves and a
# half-time interval not exceeding five minutes (unless the referee consents);
# Law XII contains the deliberate-backpass restriction and the four-step rule.
LAWS_1993_94 = LawsOfGame9394()
