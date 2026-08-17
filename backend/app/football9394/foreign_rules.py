from __future__ import annotations

"""Competition-specific foreign-player eligibility for the 1993-94 world.

The supplied MDB exposes ``Ex11`` and ``ExPlantilla`` on both ``Liga`` and
``Torneo``.  Those source values are normalised into the runtime snapshot and
are the primary rules used here.  The historical British/Irish home-nations
labour area is treated as domestic for English/Scottish *domestic* competition;
continental competitions use association nationality instead.

``ExPlantilla == 0`` is interpreted as no separate squad cap because the source
uses that value for the European cups while still setting ``Ex11 == 3``.
"""

from dataclasses import dataclass
from typing import Any, Iterable


BRITISH_IRISH_DOMESTIC_GROUP = frozenset({6, 43, 44, 45, 46})  # England, Scotland, N. Ireland, Wales, Ireland


@dataclass(frozen=True, slots=True)
class ForeignPlayerRule9394:
    competition_kind: str
    source_id: int
    name: str
    home_country_id: int | None
    max_starting: int | None
    max_squad: int | None
    continental: bool = False
    source: str = "basedatos.mdb Ex11/ExPlantilla"

    def as_dict(self) -> dict[str, Any]:
        return {
            "competition_kind": self.competition_kind,
            "source_id": self.source_id,
            "name": self.name,
            "home_country_id": self.home_country_id,
            "max_starting": self.max_starting,
            "max_squad": self.max_squad,
            "continental": self.continental,
            "source": self.source,
        }


def player_nationality_id(player: dict[str, Any]) -> int | None:
    raw = player.get("international_country_id") or player.get("nationality_id") or player.get("birth_country_id")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def is_foreign_player(player: dict[str, Any], *, home_country_id: int | None, continental: bool = False) -> bool:
    nationality = player_nationality_id(player)
    if nationality is None or home_country_id is None:
        return False
    home = int(home_country_id)
    if not continental and home in {6, 43} and nationality in BRITISH_IRISH_DOMESTIC_GROUP:
        return False
    return nationality != home


def competition_foreign_rule(universe: Any, *, kind: str, source_id: int, team_id: int | None = None) -> ForeignPlayerRule9394:
    source_id = int(source_id)
    kind = str(kind)
    if kind == "league":
        comp = universe.leagues_by_id.get(source_id) or {}
        home_country = comp.get("country_id")
        # The 1993 APSL was cross-border.  The MDB competition is attached to
        # the USA, but Montréal, Toronto and Vancouver are Canadian clubs.
        # The source does not expose a separate club-country field, so infer the
        # club association from the dominant USA/Canada nationality in its
        # original historical squad.  This keeps the league's Ex11/ExPlantilla
        # quota meaningful for both sides of the border.
        if source_id == 120 and team_id is not None:
            rows=list(getattr(universe, "players_by_team", {}).get(int(team_id), ()))
            counts={22:0,38:0}
            for player in rows:
                nat=player_nationality_id(player)
                if nat in counts: counts[nat]+=1
            if counts[22] > counts[38]:
                home_country=22
            elif counts[38] > counts[22]:
                home_country=38
        starting_limit=_positive_or_none(comp.get("max_foreigners_starting"))
        squad_limit=_positive_or_none(comp.get("max_foreigners_squad"))
        source_note="basedatos.mdb Ex11/ExPlantilla"
        if source_id == 120:
            # Historical 1993 APSL game-day rules required a strong domestic
            # presence in an 18-player roster.  Our 1993 match contract names
            # 16 players (XI + five), so seven foreign players is the closest
            # non-fictional cap that preserves the documented era rule without
            # applying the stale generic 3/6 values stored on this MDB row.
            # The association itself is resolved per US/Canadian club above.
            starting_limit=7
            squad_limit=7
            source_note="APSL 1993 historical domestic-roster rule; adapted to the game's 16-player match squad"
        return ForeignPlayerRule9394(
            "league", source_id, str(comp.get("name") or f"Liga {source_id}"),
            int(home_country) if home_country else None,
            starting_limit, squad_limit,
            continental=False, source=source_note,
        )
    comp = universe.tournaments_by_id.get(source_id) or {}
    country = comp.get("country_id")
    continent = comp.get("continent_id")
    home_country = int(country) if country not in (None, 0, "0") else None
    if home_country is None and team_id is not None:
        team = universe.team(int(team_id)) or {}
        league_id = (team.get("league") or {}).get("source_id") or team.get("league_id")
        league = universe.leagues_by_id.get(int(league_id)) if league_id is not None else None
        if league and league.get("country_id"):
            home_country = int(league["country_id"])
    return ForeignPlayerRule9394(
        "tournament", source_id, str(comp.get("name") or f"Torneo {source_id}"),
        home_country,
        _positive_or_none(comp.get("max_foreigners_starting")),
        _positive_or_none(comp.get("max_foreigners_squad")),
        continental=bool(continent),
    )


def _positive_or_none(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 and number < 500 else None


def foreign_count(players: Iterable[dict[str, Any]], rule: ForeignPlayerRule9394) -> int:
    return sum(1 for player in players if is_foreign_player(player, home_country_id=rule.home_country_id, continental=rule.continental))


def validate_matchday_foreigners(starters: Iterable[dict[str, Any]], bench: Iterable[dict[str, Any]], rule: ForeignPlayerRule9394) -> list[str]:
    starters = list(starters); bench = list(bench)
    issues: list[str] = []
    starting = foreign_count(starters, rule)
    squad = foreign_count([*starters, *bench], rule)
    if rule.max_starting is not None and starting > rule.max_starting:
        issues.append(f"{rule.name}: máximo {rule.max_starting} extranjeros en el once; hay {starting}.")
    # ExPlantilla is used as the named match-squad limit here, not as a global
    # employment ban.  Existing historical club rosters are grandfathered and
    # transfer eligibility separately prevents worsening an over-limit squad.
    if rule.max_squad is not None and squad > rule.max_squad:
        issues.append(f"{rule.name}: máximo {rule.max_squad} extranjeros en la convocatoria; hay {squad}.")
    return issues


def can_register_foreign_signing(current_squad: Iterable[dict[str, Any]], incoming: dict[str, Any], rule: ForeignPlayerRule9394) -> tuple[bool, str]:
    if not is_foreign_player(incoming, home_country_id=rule.home_country_id, continental=False):
        return True, "nacional/equiparado"
    if rule.max_squad is None:
        return True, "sin tope de plantilla en la fuente"
    current = foreign_count(current_squad, ForeignPlayerRule9394(
        rule.competition_kind, rule.source_id, rule.name, rule.home_country_id,
        rule.max_starting, rule.max_squad, continental=False, source=rule.source,
    ))
    if current >= rule.max_squad:
        return False, f"límite de extranjeros de plantilla ({rule.max_squad}) alcanzado"
    return True, "plaza de extranjero disponible"
