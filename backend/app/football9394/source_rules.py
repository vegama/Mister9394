from __future__ import annotations

"""Source-scoped rule readiness for the supplied 1993-94 MDB.

Competition names are not identities.  The database contains several leagues
called "Primera División", so historical rules are keyed by (kind, source_id).
This layer deliberately distinguishes "researched" from "simulation ready".
"""

from dataclasses import asdict, dataclass
from typing import Literal

RuleStatus = Literal[
    "certified_simple",
    "certified_complex",
    "structure_verified",
    "historical_conflict",
    "unresolved",
]


@dataclass(frozen=True, slots=True)
class CompetitionSourceRef9394:
    kind: Literal["league", "tournament"]
    source_id: int
    name: str
    country: str | None = None

    @property
    def key(self) -> tuple[str, int]:
        return (self.kind, self.source_id)


@dataclass(frozen=True, slots=True)
class SourceRuleAuditEntry9394:
    ref: CompetitionSourceRef9394
    status: RuleStatus
    simulation_ready: bool
    ruleset_id: str | None = None
    format_id: str | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["source_key"] = f"{self.ref.kind}:{self.ref.source_id}"
        return payload


# This is intentionally explicit.  A new source competition is unresolved until
# somebody adds an audited entry; there is no name-based inheritance.
_SOURCE_RULE_AUDIT: dict[tuple[str, int], SourceRuleAuditEntry9394] = {}


def _add(
    kind: Literal["league", "tournament"], source_id: int, name: str, country: str | None,
    status: RuleStatus, *, ready: bool = False, ruleset: str | None = None,
    format_id: str | None = None, notes: tuple[str, ...] = (),
) -> None:
    ref = CompetitionSourceRef9394(kind, source_id, name, country)
    _SOURCE_RULE_AUDIT[ref.key] = SourceRuleAuditEntry9394(
        ref=ref, status=status, simulation_ready=ready, ruleset_id=ruleset,
        format_id=format_id, notes=notes,
    )


# Fully wired simple Spanish tiers.
_add("league", 1, "Primera División", "España", "certified_simple", ready=True, ruleset="esp_primera_1993_94")
_add("league", 2, "Segunda División", "España", "certified_simple", ready=True, ruleset="esp_segunda_1993_94")
_add("league", 5, "Premier League", "Inglaterra", "certified_simple", ready=True, ruleset="eng_premier_1993_94")
_add("league", 13, "1.Bundesliga", "Alemania", "certified_simple", ready=True, ruleset="ger_bundesliga_1993_94")
_add("league", 38, "Scottish Premier Division", "Escocia", "certified_simple", ready=True, ruleset="sco_premier_1993_94",
     notes=("12 clubes, cuatro enfrentamientos por pareja y tres descensos por reestructuración; la MDB declara erróneamente tres vueltas.",))
_add("league", 14, "Division 1", "Francia", "certified_simple", ready=True, ruleset="fra_division_1_1993_94",
     notes=("20 clubes, 2 puntos por victoria, desempate por diferencia de goles/goles marcados y tres descensos deportivos.",))
_add("league", 32, "Primeira Liga", "Portugal", "certified_simple", ready=True, ruleset="por_primeira_1993_94",
     notes=("18 clubes, 34 jornadas, 2 puntos por victoria y tres descensos.",))

# Non-standard formats already encoded as graph specs.
_add("league", 120, "APSL", "Estados Unidos", "certified_complex", ready=True, format_id="usa_apsl_1993")
_add("league", 111, "J. League", "Japón", "certified_complex", ready=True, format_id="jpn_jleague_1993")
_add("league", 47, "Série A", "Brasil", "certified_complex", ready=True, format_id="bra_serie_a_1993",
     notes=("La fila MDB simplifica el torneo a 20 clubes; el runtime histórico usa 32, recupera Fortaleza de otra fila de la propia MDB y audita dos clubes ausentes como reparación de fuente.",))
_add("league", 40, "Primera División", "México", "certified_complex", ready=True, ruleset="mex_primera_1993_94", format_id="mex_primera_1993_94",
     notes=("20 clubes, cuatro grupos de clasificación sobre una liga completa, reclasificación, liguilla a doble partido y descenso por cociente trianual ejecutables.",))
_add("league", 128, "Primera A", "Colombia", "certified_complex", ready=True, ruleset="col_primera_a_1993", format_id="col_primera_a_1993",
     notes=("16 clubes; Apertura por grupos, Finalización, reclasificación, bonificaciones, cuadrangulares y un descenso ejecutables. Dos clubes requieren reparación temporal de plantilla por huecos de la MDB.",))

# Explicit source conflict: this competition did not take place as an ordinary
# Série B in 1993, so the MDB row must never be simulated as a 20-team league.
_add("league", 105, "Serie B", "Brasil", "historical_conflict", ready=False,
     notes=("La fila histórica de la MDB contradice el calendario real de 1993 y queda bloqueada hasta modelar los clasificatorios de 1994.",))

_add("league", 4, "Serie A", "Italia", "certified_complex", ready=True, ruleset="ita_serie_a_1993_94", format_id="ita_serie_a_b_pyramid_1993_94",
     notes=("18 clubes, 2 puntos por victoria, classifica avulsa y spareggi decisivos; cuatro descensos conectados a Serie B. Las plazas continentales quedan fuera del runtime mientras los torneos europeos no estén activados.",))
_add("league", 102, "Serie B", "Italia", "certified_complex", ready=True, ruleset="ita_serie_b_1993_94", format_id="ita_serie_a_b_pyramid_1993_94",
     notes=("Puntuación, cuatro ascensos/descensos y spareggi decisivos de ascenso/descenso integrados en el cierre de temporada.",))

# Uruguay is playable as the 13-club championship present in the MDB. The
# source does not include its second level, so the historical relegation/repechage
# transition is intentionally left unlinked while the competition itself remains.
_add("league", 49, "Primera División", "Uruguay", "certified_simple", ready=True, ruleset="uru_primera_1993",
     notes=("13 clubes, 24 partidos por club y dos puntos por victoria; la transición con Segunda queda sin enlazar porque esa división no está en la MDB.",))

# Historical Belgian league reconstructed from the 1993-94 roster gate.  The modern
# MDB row 52 stays deliberately unbound; 930052 is the frozen historical runtime.
_add("league", 930052, "Eerste Klasse / Division 1", "Bélgica", "certified_simple", ready=True,
     ruleset="bel_first_division_1993_94",
     notes=("18 clubes, 34 jornadas y dos puntos por victoria; roster gate histórico 1993-94 superado.",))

# Historical Turkish 1993-94 league reconstructed from BDFutbol rosters. The
# stale MDB source row 57 remains deliberately unbound.
_add("league", 930057, "1. Lig", "Turquía", "certified_simple", ready=True,
     ruleset="tur_first_division_1993_94",
     notes=("16 clubes, 30 jornadas y tres puntos por victoria; roster gate histórico 1993-94 superado.",))

# Historical Russian 1993 league reconstructed from BDFutbol rosters. The stale
# MDB source row 15 remains deliberately unbound.
_add("league", 930015, "Supreme League", "Rusia", "certified_simple", ready=True,
     ruleset="rus_supreme_league_1993",
     notes=("18 clubes, 34 jornadas y dos puntos por victoria; roster gate histórico 1993 superado.",))

# Dutch 1993-94 pyramid: both source leagues are certified together because
# their movement is decided by one shared nacompetitie runtime.
_add("league", 31, "Eredivisie", "Países Bajos", "certified_complex", ready=True, ruleset="ned_eredivisie_1993_94", format_id="ned_nacompetitie_1993_94",
     notes=("18 clubes; 18.º desciende y 16.º/17.º juegan nacompetitie.",))
_add("league", 54, "Eerste Divisie", "Países Bajos", "certified_complex", ready=True, ruleset="ned_eerste_1993_94", format_id="ned_nacompetitie_1993_94",
     notes=("Campeón directo; seis plazas de nacompetitie mediante cuatro periodos y clasificación general.",))

_add("league", 16, "Campeonato de Primera División", "Argentina", "certified_complex", ready=True,
     ruleset="arg_primera_1993_94", format_id="arg_apertura_clausura_1993_94",
     notes=("Apertura y Clausura de 19 fechas con campeones propios; descenso por promedio trianual.",))

# Segunda B is one coupled four-group system: regular groups, four promotion
# mini-leagues and the neutral survival playoff among the four 16th placed clubs.
for source_id, name in ((3,"Segunda División B G I"),(10,"Segunda División B G II"),(11,"Segunda División B G III"),(9,"Segunda División B G IV")):
    _add("league", source_id, name, "España", "certified_complex", ready=True,
         ruleset="esp_segunda_b_1993_94", format_id="esp_segundab_pyramid_1993_94",
         notes=("20 clubes, 38 jornadas; top-4 a liguilla, 17.º-20.º descenso y 16.º a promoción de permanencia.",))

# Cups are always present when the MDB contains them.  Where the source stores
# a mid-competition participant pool, the runtime resumes from that historical
# stage instead of inventing qualifying clubs that are absent from the data.
_add("tournament", 88, "Ascenso a Segunda", "España", "certified_complex", ready=True,
     format_id="esp_segundab_pyramid_1993_94",
     notes=("Cuatro liguillas de cuatro con un ascenso por grupo; alimentada por los cuatro grupos de Segunda B.",))
_add("tournament", 1, "Copa de Europa", None, "certified_complex", ready=True,
     format_id="uefa_ec_group_stage_1993_94",
     notes=("La MDB aporta los ocho clubes de la fase de grupos; se disputan dos grupos de cuatro, semifinales a partido único y final neutral.",))
_add("tournament", 2, "Copa de la UEFA", None, "certified_complex", ready=True,
     format_id="uefa_cup_from_r16_1993_94",
     notes=("La MDB aporta los dieciséis clubes de octavos; el runtime continúa con eliminatorias a doble partido y final también a doble partido.",))
_add("tournament", 90, "Recopa de Europa", None, "certified_complex", ready=True,
     format_id="uefa_cwc_from_r32_1993_94",
     notes=("La MDB aporta 32 clubes desde primera ronda; eliminatorias a doble partido y final neutral a partido único.",))
_add("tournament", 3, "Copa de S.M. El Rey", "España", "certified_complex", ready=True,
     format_id="esp_copa_del_rey_source_pool_1993_94",
     notes=("La MDB no contiene Tercera: se incluyen todos los clubes españoles elegibles disponibles, se excluyen filiales y se conserva el sistema histórico de eliminatorias; las plazas inferiores ausentes quedan auditadas como huecos de fuente.",))


def source_rule_audit(ref: CompetitionSourceRef9394) -> SourceRuleAuditEntry9394:
    existing = _SOURCE_RULE_AUDIT.get(ref.key)
    if existing is not None:
        # Return source metadata from the actual snapshot while preserving the
        # audited rule state.  This avoids stale display names in the registry.
        return SourceRuleAuditEntry9394(
            ref=ref, status=existing.status, simulation_ready=existing.simulation_ready,
            ruleset_id=existing.ruleset_id, format_id=existing.format_id, notes=existing.notes,
        )
    return SourceRuleAuditEntry9394(ref=ref, status="unresolved", simulation_ready=False)


def audit_snapshot_competitions(competitions: list[dict]) -> list[SourceRuleAuditEntry9394]:
    result: list[SourceRuleAuditEntry9394] = []
    for row in competitions:
        ref = CompetitionSourceRef9394(
            kind=row["kind"], source_id=int(row["source_id"]), name=str(row["name"]), country=row.get("country")
        )
        result.append(source_rule_audit(ref))
    return result
