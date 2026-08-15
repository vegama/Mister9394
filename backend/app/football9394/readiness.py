from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .registry import HistoricalCompetitionRegistry9394, UnresolvedHistoricalRulesError


@dataclass(frozen=True, slots=True)
class CompetitionReadiness9394:
    name: str
    resolved: bool
    ruleset_id: str | None


@dataclass(frozen=True, slots=True)
class UniverseReadiness9394:
    competitions: tuple[CompetitionReadiness9394, ...]

    @property
    def unresolved(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.competitions if not item.resolved)

    @property
    def ready(self) -> bool:
        return not self.unresolved

    def require_ready(self) -> None:
        if not self.ready:
            preview = ", ".join(self.unresolved[:8])
            suffix = "…" if len(self.unresolved) > 8 else ""
            raise UnresolvedHistoricalRulesError(
                f"universo 1993-94 incompleto: {len(self.unresolved)} competiciones sin reglamento ({preview}{suffix})"
            )


def audit_competition_readiness(
    names: Iterable[str], registry: HistoricalCompetitionRegistry9394
) -> UniverseReadiness9394:
    rows: list[CompetitionReadiness9394] = []
    seen: set[str] = set()
    for raw in names:
        name = " ".join(str(raw).strip().split())
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())
        registry.discover(name)
        try:
            rules = registry.resolve(name)
        except UnresolvedHistoricalRulesError:
            rows.append(CompetitionReadiness9394(name, False, None))
        else:
            rows.append(CompetitionReadiness9394(name, True, rules.id))
    return UniverseReadiness9394(tuple(rows))
