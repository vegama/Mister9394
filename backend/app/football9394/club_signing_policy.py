from __future__ import annotations

"""Club-specific recruitment policies documented by the historical source.

The supplied MDB explicitly marks Basque-origin players (``Jugador.OrigenVasco``)
and Athletic Club's entire 1993-94 squad carries that marker.  That source flag
lets the career enforce Athletic's sporting policy without trying to infer
ethnicity from surnames or modern geography.
"""

from typing import Any

ATHLETIC_CLUB_SOURCE_ID = 6


def club_specific_signing_eligibility(team_id: int, player: dict[str, Any]) -> tuple[bool, str]:
    team_id = int(team_id)
    if team_id != ATHLETIC_CLUB_SOURCE_ID:
        return True, "sin política específica de club"
    if bool(player.get("basque_origin")):
        return True, "elegible para la política de Athletic Club por origen vasco de la fuente"
    if bool(player.get("generated")) and int(player.get("academy_team_id") or 0) == ATHLETIC_CLUB_SOURCE_ID:
        return True, "elegible por haberse formado en la cantera del Athletic Club durante la carrera"
    return False, "Athletic Club sólo incorpora jugadores con origen vasco/elegibilidad de fuente o formados en su cantera durante la carrera"
