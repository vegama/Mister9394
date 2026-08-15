from __future__ import annotations

"""Inclusion policy for competitions present in the supplied 1993-94 MDB.

Product rule: a source competition is never removed from the game merely
because its promotion/relegation pyramid is incomplete in the MDB.  Presence,
historical simulation readiness and inter-competition movement are separate
concepts:

* every source row is included in the runtime catalogue;
* a competition may be simulated only after its own 1993-94 format is certified;
* promotion/relegation links are enabled only when both ends are trustworthy;
* missing links are surfaced as data gaps rather than replaced by modern rules.
"""

from dataclasses import dataclass
from typing import Iterable

from .source_rules import SourceRuleAuditEntry9394


@dataclass(frozen=True, slots=True)
class PyramidState9394:
    country: str
    league_levels: tuple[int, ...]
    league_source_ids: tuple[int, ...]
    has_pyramid: bool
    all_leagues_ready: bool
    active: bool
    reason: str


@dataclass(frozen=True, slots=True)
class CompetitionActivation9394:
    kind: str
    source_id: int
    name: str
    country: str | None
    simulation_ready: bool
    pyramid_eligible: bool
    active: bool
    reason: str

    @property
    def source_key(self) -> str:
        return f"{self.kind}:{self.source_id}"


def _country_pyramids(
    competitions: Iterable[dict], audits: Iterable[SourceRuleAuditEntry9394]
) -> dict[str, PyramidState9394]:
    audit_by_key = {entry.ref.key: entry for entry in audits}
    rows_by_country: dict[str, list[dict]] = {}
    for row in competitions:
        if row.get("kind") != "league" or not row.get("country"):
            continue
        rows_by_country.setdefault(str(row["country"]), []).append(row)

    result: dict[str, PyramidState9394] = {}
    for country, rows in rows_by_country.items():
        levels = tuple(sorted({int(row["level"]) for row in rows if row.get("level") is not None}))
        source_ids = tuple(sorted(int(row["source_id"]) for row in rows))
        has_pyramid = len(levels) >= 2
        audit_rows = [audit_by_key.get(("league", int(row["source_id"]))) for row in rows]
        all_ready = bool(rows) and all(entry is not None and entry.simulation_ready for entry in audit_rows)
        if has_pyramid and all_ready:
            reason = "movement_graph_ready"
        elif has_pyramid:
            reason = "movement_graph_partial"
        else:
            reason = "standalone_competition_no_source_link"
        # `active` here means that the country's movement graph is usable, not
        # that its competitions are visible. Every competition is included below.
        result[country] = PyramidState9394(
            country=country,
            league_levels=levels,
            league_source_ids=source_ids,
            has_pyramid=has_pyramid,
            all_leagues_ready=all_ready,
            active=has_pyramid and all_ready,
            reason=reason,
        )
    return result


def audit_competition_activation(
    competitions: list[dict], audits: list[SourceRuleAuditEntry9394]
) -> tuple[list[CompetitionActivation9394], dict[str, PyramidState9394]]:
    """Return catalogue inclusion for every MDB competition.

    `active=True` means "admitted by the original MDB for a playable career".
    Historical rows with ADMITIDA=False remain in the source catalogue and can
    still feed player/club data, but they are not silently promoted into the
    playable universe. `simulation_ready` is a second, independent gate.
    """
    pyramids = _country_pyramids(competitions, audits)
    rows_by_key = {(row["kind"], int(row["source_id"])): row for row in competitions}
    result: list[CompetitionActivation9394] = []

    for audit in audits:
        row = rows_by_key[audit.ref.key]
        country = row.get("country") or audit.ref.country
        pyramid = pyramids.get(str(country)) if country else None
        pyramid_eligible = bool(audit.ref.kind == "league" and pyramid and pyramid.has_pyramid)
        admitted = bool(row.get("admitted", True))
        if not admitted:
            reason = "source_not_admitted"
        elif audit.simulation_ready:
            if pyramid_eligible and pyramid and pyramid.active:
                reason = "included_simulation_ready_with_movement_graph"
            elif audit.ref.kind == "tournament":
                reason = "included_simulation_ready_tournament"
            else:
                reason = "included_simulation_ready_standalone"
        else:
            reason = "included_pending_historical_runtime"

        result.append(CompetitionActivation9394(
            kind=audit.ref.kind,
            source_id=audit.ref.source_id,
            name=audit.ref.name,
            country=country,
            simulation_ready=audit.simulation_ready,
            pyramid_eligible=pyramid_eligible,
            active=admitted,
            reason=reason,
        ))

    return result, pyramids
