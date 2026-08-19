from __future__ import annotations

"""Derived domestic cups for the playable 1993-94 career world.

The original MDB snapshot only carries Copa del Rey as a selectable domestic
cup.  The career nevertheless contains enough clubs to run the principal cup
for every represented European association.  These rows are deliberately
*derived career competitions*: they never claim to be rows imported from the
MDB, and their brackets are resized to the clubs that actually exist in the
save.
"""

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class DomesticCupSpec9394:
    source_id: int
    name: str
    short_name: str
    country: str
    country_id: int
    league_ids: tuple[int, ...]
    format_style: str
    historical_note: str
    source_note: str

    def competition_row(self) -> dict[str, Any]:
        return {
            "kind": "tournament",
            "source_id": self.source_id,
            "name": self.name,
            "short_name": self.short_name,
            "country": self.country,
            "country_id": self.country_id,
            "continent_id": None,
            "entrants": None,
            "admitted": True,
            "derived": True,
            "derived_from_playable_clubs": True,
            "format_style": self.format_style,
            "historical_note": self.historical_note,
            "source_note": self.source_note,
        }


# Spain remains source tournament 3 and keeps its dedicated staged runtime.
# Synthetic ids use 940000 + historical country id so saves can resolve them
# deterministically without colliding with imported MDB ids.
DOMESTIC_CUPS_9394: tuple[DomesticCupSpec9394, ...] = (
    DomesticCupSpec9394(3, "Copa del Rey", "Copa del Rey", "España", 11, (1, 2, 3, 9, 10, 11), "spain_staged_two_leg", "Entradas escalonadas por categoría, eliminatorias a doble partido y final única.", "MDB + formato histórico 1993-94"),
    DomesticCupSpec9394(940001, "Coupe de France", "Coupe de France", "Francia", 1, (14,), "single_leg", "Eliminación directa a partido único; cuadro reducido a los clubes franceses representados.", "formato histórico 1993-94; participantes adaptados al mundo jugable"),
    DomesticCupSpec9394(940003, "KNVB Beker", "KNVB Beker", "Países Bajos", 3, (31, 54), "single_leg", "Eliminación directa a partido único con los clubes neerlandeses disponibles.", "formato histórico 1993-94; participantes adaptados al mundo jugable"),
    DomesticCupSpec9394(940004, "DFB-Pokal", "DFB-Pokal", "Alemania", 4, (13,), "single_leg", "Eliminación directa a partido único, redimensionada a los clubes representados.", "formato histórico 1993-94; participantes adaptados al mundo jugable"),
    DomesticCupSpec9394(940005, "Coppa Italia", "Coppa Italia", "Italia", 5, (4, 102), "italy_two_leg_late", "Rondas iniciales comprimidas; desde octavos, eliminatorias a doble partido incluida la final.", "formato histórico 1993-94; participantes adaptados al mundo jugable"),
    DomesticCupSpec9394(940006, "FA Cup", "FA Cup", "Inglaterra", 6, (5,), "single_leg_replay_compressed", "Eliminación directa; los replays históricos se resuelven en prórroga/penaltis para no inflar el calendario.", "formato histórico 1993-94 con replay comprimido"),
    DomesticCupSpec9394(940010, "Taça de Portugal", "Taça de Portugal", "Portugal", 10, (32,), "single_leg_replay_compressed", "Eliminación directa; un eventual replay se comprime a prórroga/penaltis.", "formato histórico 1993-94 con replay comprimido"),
    DomesticCupSpec9394(940017, "Beker van België", "Copa de Bélgica", "Bélgica", 17, (930052,), "belgium_two_leg_semis", "Partido único salvo semifinales a doble partido; final única.", "formato histórico 1993-94; participantes adaptados al mundo jugable"),
    DomesticCupSpec9394(940040, "Kubok Rossii", "Copa de Rusia", "Rusia", 40, (930015,), "single_leg", "Eliminación directa a partido único.", "formato histórico 1993-94; participantes adaptados al mundo jugable"),
    DomesticCupSpec9394(940043, "Scottish Cup", "Scottish Cup", "Escocia", 43, (38,), "single_leg", "Eliminación directa a partido único con final neutral.", "formato histórico 1993-94; participantes adaptados al mundo jugable"),
    DomesticCupSpec9394(940047, "Kypello Elladas", "Copa de Grecia", "Grecia", 47, (930047,), "greece_groups_two_leg", "Fase inicial de grupos comprimida a los clubes disponibles; cuartos y semifinales a doble partido, final única.", "formato histórico 1993-94; fase de grupos redimensionada"),
    DomesticCupSpec9394(940084, "Türkiye Kupası", "Copa de Turquía", "Turquía", 84, (930057,), "turkey_two_leg_semis_final", "Rondas iniciales a partido único; semifinales y final a doble partido.", "formato histórico 1993-94; participantes adaptados al mundo jugable"),
)

DOMESTIC_CUP_BY_ID = {spec.source_id: spec for spec in DOMESTIC_CUPS_9394}
SYNTHETIC_DOMESTIC_CUPS_9394 = tuple(spec for spec in DOMESTIC_CUPS_9394 if spec.source_id != 3)


def domestic_cup_spec(source_id: int) -> DomesticCupSpec9394 | None:
    return DOMESTIC_CUP_BY_ID.get(int(source_id))


def domestic_cup_competition_rows() -> list[dict[str, Any]]:
    return [spec.competition_row() for spec in SYNTHETIC_DOMESTIC_CUPS_9394]


def cup_participant_ids(runtime: Any, spec: DomesticCupSpec9394) -> list[str]:
    """Return only real clubs that are members of represented leagues now.

    This deliberately reads career memberships, not the frozen 1993 league on
    the team row, so promotion/relegation never leaves a cup stuck in 1993.
    Reserve/filial sides and transfer-only containers are excluded.
    """
    ids: list[str] = []
    seen: set[int] = set()
    for league_id in spec.league_ids:
        for team in runtime._teams_for_league(int(league_id)):
            tid = int(team["source_id"])
            if tid in seen or team.get("reserve_of") or team.get("market_container"):
                continue
            seen.add(tid)
            ids.append(str(tid))
    return ids



def cup_participant_ids_from_state(state: dict[str, Any], universe: Any, spec: DomesticCupSpec9394) -> list[str]:
    memberships=state.get("league_memberships") or {}
    ids: list[str]=[]; seen: set[int]=set()
    for league_id in spec.league_ids:
        raw_ids=memberships.get(str(int(league_id)))
        if raw_ids is None:
            raw_ids=[int(t["source_id"]) for t in universe.teams(league_id=int(league_id))]
        for raw in raw_ids:
            tid=int(raw); team=universe.team(tid) or {}
            if tid in seen or team.get("reserve_of") or team.get("market_container"):
                continue
            seen.add(tid); ids.append(str(tid))
    return ids

def team_current_league_id(universe: Any, team_id: int, memberships: dict[str, Iterable[int]] | None = None) -> int | None:
    if memberships:
        for league_id, ids in memberships.items():
            if int(team_id) in {int(x) for x in ids}:
                return int(league_id)
    team = universe.team(int(team_id)) or {}
    league = team.get("league") or {}
    raw = league.get("source_id") or team.get("league_id")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None

# The imported 1993-94 Cup Winners' Cup pool contains one national cup
# representative for each of these playable associations plus Parma as the
# reigning 1992-93 CWC holder.  Keeping the mapping explicit lets rollover
# replace only the national berth while preserving the rest of Europe's
# historical baseline participants.
CWC_BASELINE_REPRESENTATIVE_BY_COUNTRY_9394: dict[int, int] = {
    11: 5,      # Real Madrid - Spain
    6: 79,      # Arsenal - England
    4: 217,     # Leverkusen - Germany
    1: 232,     # PSG - France
    5: 280,     # Torino - Italy
    3: 285,     # Ajax - Netherlands
    10: 303,    # Benfica - Portugal
    47: 406,    # Panathinaikos - Greece (legacy league id in source pool)
    17: 409,    # Standard Liège - Belgium
    43: 492,    # Aberdeen - Scotland
    84: 644,    # Beşiktaş - Turkey
    40: 1087,   # Torpedo Moskva - Russia
}
CWC_BASELINE_DEFENDING_CHAMPION_9394 = 753  # Parma, 1992-93 title holder
