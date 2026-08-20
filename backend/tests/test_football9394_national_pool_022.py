from __future__ import annotations

import pytest

import json
from pathlib import Path

from backend.app.football9394.snapshot_runtime import default_runtime_snapshot


def test_six_new_players_are_real_batch_records_under_nonplayable_otros_containers():
    universe = default_runtime_snapshot()
    ids = {9495000, 9495001, 9495002, 9495003, 9495004, 9495005}
    players = [universe.players_by_id[player_id] for player_id in ids]
    assert len(players) == 6
    for player in players:
        assert player["external_origin"] == "national_pool_1993_94"
        assert player["creation_batch"] == "near_functional_national_teams_0.22"
        team = universe.teams_by_id[int(player["team_id"])]
        assert team["market_container"] is True
        assert team["playable"] is False
        assert team["can_buy_players"] is False
        assert team["players_transferable"] is True
        assert team.get("league_id") is None


def test_duplicate_audit_has_zero_collisions_against_original_database():
    root = Path(__file__).resolve().parents[2]
    audit = json.loads((root / "data/football9394/created_players_duplicate_audit.json").read_text(encoding="utf-8"))
    assert audit["created_players_checked"] >= 367
    assert audit["existing_players_compared"] >= 10528
    assert audit["strong_or_ambiguous_collisions"] == []
    assert audit["generated_exact_duplicates"] == []


# Estuvo en el backlog de contenido: uno de los cinco pools se quedaba en 21
# jugadores verificados. Las convocatorias de torneo lo han completado, así que
# vuelve a exigirse de verdad.
def test_five_expanded_1993_pools_have_22_verified_players_each():
    universe = default_runtime_snapshot()
    for country_id in (14, 15, 23, 41, 42):
        verified = [
            p for p in universe.payload["players"]
            if int(p.get("international_country_id") or p.get("birth_country_id") or 0) == country_id
            and p.get("verified_national_pool_1993_94")
        ]
        assert len(verified) == 22
        counts = {pos: 0 for pos in ("POR", "DEF", "MED", "DEL")}
        for player in verified:
            counts[str(player.get("broad_position") or "MED").upper()] += 1
        assert counts["POR"] >= 2
        assert counts["DEF"] >= 5
        assert counts["MED"] >= 5
        assert counts["DEL"] >= 3
