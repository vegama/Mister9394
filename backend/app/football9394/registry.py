from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .rules import (
    CompetitionRules9394, SPAIN_PRIMERA_1993_94, SPAIN_SEGUNDA_1993_94,
    ENGLAND_PREMIER_1993_94, GERMANY_BUNDESLIGA_1993_94, SCOTLAND_PREMIER_1993_94,
    ITALY_SERIE_A_1993_94, ITALY_SERIE_B_1993_94, FRANCE_DIVISION_1_1993_94, PORTUGAL_PRIMEIRA_1993_94,
    NETHERLANDS_EREDIVISIE_1993_94, NETHERLANDS_EERSTE_1993_94, SPAIN_SEGUNDA_B_1993_94, ARGENTINA_PRIMERA_1993_94, MEXICO_PRIMERA_1993_94, COLOMBIA_PRIMERA_A_1993, URUGUAY_PRIMERA_1993, BELGIUM_FIRST_DIVISION_1993_94, TURKEY_FIRST_DIVISION_1993_94, RUSSIA_SUPREME_LEAGUE_1993, GREECE_ALPHA_ETHNIKI_1993_94,
)


class UnresolvedHistoricalRulesError(LookupError):
    pass


def _key(value: str) -> str:
    return " ".join(value.casefold().strip().split())


@dataclass(slots=True)
class HistoricalCompetitionRegistry9394:
    """Registry that deliberately has no generic competition-rule fallback.

    MDB competitions can be discovered before their exact 1993-94 regulations
    have been researched.  They remain explicit audit items until registered;
    attempting to simulate one raises instead of inheriting modern/default
    scoring or promotion rules.
    """

    _rules_by_id: dict[str, CompetitionRules9394] = field(default_factory=dict)
    _aliases: dict[str, str] = field(default_factory=dict)
    _discovered_names: dict[str, str] = field(default_factory=dict)
    _rules_by_source: dict[tuple[str, int], str] = field(default_factory=dict)

    def register(self, rules: CompetitionRules9394, *, aliases: Iterable[str] = (), include_name_alias: bool = True) -> None:
        rules.validate()
        if rules.id in self._rules_by_id and self._rules_by_id[rules.id] != rules:
            raise ValueError(f"ruleset duplicado con contenido distinto: {rules.id}")
        self._rules_by_id[rules.id] = rules
        labels = (rules.id, *((rules.name,) if include_name_alias else ()), *aliases)
        for label in labels:
            normalized = _key(label)
            existing = self._aliases.get(normalized)
            if existing and existing != rules.id:
                raise ValueError(f"alias ambiguo {label!r}: {existing} / {rules.id}")
            self._aliases[normalized] = rules.id

    def discover(self, raw_name: str) -> None:
        normalized = _key(raw_name)
        if normalized:
            self._discovered_names.setdefault(normalized, raw_name.strip())

    def register_source(self, kind: str, source_id: int, rules: CompetitionRules9394) -> None:
        """Bind one exact MDB source row to a ruleset.

        Source bindings are deliberately separate from display-name aliases: the
        supplied database contains several competitions with identical names.
        """
        if rules.id not in self._rules_by_id:
            self.register(rules)
        key = (str(kind).strip().casefold(), int(source_id))
        existing = self._rules_by_source.get(key)
        if existing and existing != rules.id:
            raise ValueError(f"fuente {key} ya ligada a {existing}, no a {rules.id}")
        self._rules_by_source[key] = rules.id

    def resolve_source(self, kind: str, source_id: int) -> CompetitionRules9394:
        key = (str(kind).strip().casefold(), int(source_id))
        rules_id = self._rules_by_source.get(key)
        if rules_id is None:
            raise UnresolvedHistoricalRulesError(
                f"{key[0]}:{key[1]}: reglamento 1993-94 no ligado a esta fila MDB; no se resolverá por nombre"
            )
        return self._rules_by_id[rules_id]

    def resolve(self, competition: str) -> CompetitionRules9394:
        normalized = _key(competition)
        rules_id = self._aliases.get(normalized, competition if competition in self._rules_by_id else None)
        if rules_id is None or rules_id not in self._rules_by_id:
            label = self._discovered_names.get(normalized, competition)
            raise UnresolvedHistoricalRulesError(
                f"{label}: reglamento 1993-94 todavía no resuelto; no se aplicará un fallback genérico"
            )
        return self._rules_by_id[rules_id]

    @property
    def resolved(self) -> tuple[CompetitionRules9394, ...]:
        return tuple(self._rules_by_id.values())

    @property
    def unresolved_discovered(self) -> tuple[str, ...]:
        unresolved = []
        for normalized, raw_name in self._discovered_names.items():
            if normalized not in self._aliases:
                unresolved.append(raw_name)
        return tuple(sorted(unresolved, key=str.casefold))

    def coverage(self) -> dict[str, int]:
        discovered = len(self._discovered_names)
        unresolved = len(self.unresolved_discovered)
        return {
            "discovered": discovered,
            "resolved_discovered": max(0, discovered - unresolved),
            "unresolved": unresolved,
            "registered_rulesets": len(self._rules_by_id),
        }


def default_registry_9394() -> HistoricalCompetitionRegistry9394:
    registry = HistoricalCompetitionRegistry9394()
    registry.register(
        SPAIN_PRIMERA_1993_94,
        aliases=("Primera", "Liga 1ª", "Primera Division", "1ª División"),
    )
    registry.register(
        SPAIN_SEGUNDA_1993_94,
        aliases=("Segunda", "Liga 2ª", "Segunda Division", "2ª División"),
    )
    registry.register(ENGLAND_PREMIER_1993_94, aliases=("Premier League 1993-94",))
    registry.register(GERMANY_BUNDESLIGA_1993_94, aliases=("Bundesliga 1993-94",))
    registry.register(FRANCE_DIVISION_1_1993_94, aliases=("Division 1 France 1993-94",))
    registry.register(PORTUGAL_PRIMEIRA_1993_94, aliases=("Primeira Divisão 1993-94", "Primeira Liga 1993-94"))
    registry.register(NETHERLANDS_EREDIVISIE_1993_94, aliases=("Eredivisie 1993-94",))
    registry.register(SPAIN_SEGUNDA_B_1993_94, aliases=("Segunda B 1993-94",))
    registry.register(NETHERLANDS_EERSTE_1993_94, aliases=("Eerste Divisie 1993-94",))
    registry.register(ARGENTINA_PRIMERA_1993_94, aliases=("Primera Argentina 1993-94",))
    registry.register(MEXICO_PRIMERA_1993_94, aliases=("Primera México 1993-94", "Liga México 1993-94"), include_name_alias=False)
    registry.register(COLOMBIA_PRIMERA_A_1993, aliases=("Primera A Colombia 1993",), include_name_alias=False)
    registry.register(URUGUAY_PRIMERA_1993, aliases=("Primera Uruguay 1993",), include_name_alias=False)
    registry.register(ITALY_SERIE_A_1993_94, aliases=("Serie A 1993-94",))
    registry.register(ITALY_SERIE_B_1993_94, aliases=("Serie B 1993-94",))
    registry.register(SCOTLAND_PREMIER_1993_94, aliases=("Scottish Premier 1993-94", "Premier Division Scotland 1993-94"))
    registry.register(BELGIUM_FIRST_DIVISION_1993_94, aliases=("Belgian First Division 1993-94", "Pro League 1993-94"), include_name_alias=False)
    registry.register(TURKEY_FIRST_DIVISION_1993_94, aliases=("Turkish First Division 1993-94", "Süper Lig 1993-94"), include_name_alias=False)
    registry.register(RUSSIA_SUPREME_LEAGUE_1993, aliases=("Russian Supreme League 1993", "Russian Premier 1993"), include_name_alias=False)
    registry.register(GREECE_ALPHA_ETHNIKI_1993_94, aliases=("Greek Alpha Ethniki 1993-94", "Alpha Ethniki 1993-94"), include_name_alias=False)
    registry.register_source("league", 1, SPAIN_PRIMERA_1993_94)
    registry.register_source("league", 2, SPAIN_SEGUNDA_1993_94)
    registry.register_source("league", 5, ENGLAND_PREMIER_1993_94)
    registry.register_source("league", 13, GERMANY_BUNDESLIGA_1993_94)
    registry.register_source("league", 14, FRANCE_DIVISION_1_1993_94)
    registry.register_source("league", 32, PORTUGAL_PRIMEIRA_1993_94)
    registry.register_source("league", 31, NETHERLANDS_EREDIVISIE_1993_94)
    registry.register_source("league", 54, NETHERLANDS_EERSTE_1993_94)
    for source_id in (3, 10, 11, 9):
        registry.register_source("league", source_id, SPAIN_SEGUNDA_B_1993_94)
    registry.register_source("league", 16, ARGENTINA_PRIMERA_1993_94)
    registry.register_source("league", 40, MEXICO_PRIMERA_1993_94)
    registry.register_source("league", 128, COLOMBIA_PRIMERA_A_1993)
    registry.register_source("league", 49, URUGUAY_PRIMERA_1993)
    registry.register_source("league", 4, ITALY_SERIE_A_1993_94)
    registry.register_source("league", 102, ITALY_SERIE_B_1993_94)
    registry.register_source("league", 38, SCOTLAND_PREMIER_1993_94)
    registry.register_source("league", 930052, BELGIUM_FIRST_DIVISION_1993_94)
    registry.register_source("league", 930057, TURKEY_FIRST_DIVISION_1993_94)
    registry.register_source("league", 930015, RUSSIA_SUPREME_LEAGUE_1993)
    registry.register_source("league", 930047, GREECE_ALPHA_ETHNIKI_1993_94)
    return registry
