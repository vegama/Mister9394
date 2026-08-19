from __future__ import annotations

import pytest

from copy import deepcopy
from datetime import date
import json
from pathlib import Path

from backend.app.football9394.career_ai import run_ai_transfer_window
from backend.app.football9394.career_economy import initial_club_finances
from backend.app.football9394.foreign_rules import can_register_foreign_signing, competition_foreign_rule, is_foreign_player
from backend.app.football9394.international_tournaments import simulate_world_championship_24
from backend.app.football9394.national_teams import (
    historical_world_cup_1994_squad,
    national_team_catalog,
    world_cup_1994_country_ids,
    world_cup_1994_player_ids,
)
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot


def test_usa94_has_24_complete_unique_22_player_squads():
    universe=default_runtime_snapshot()
    countries=world_cup_1994_country_ids()
    assert len(countries)==24
    all_ids=[]
    for country_id in countries:
        ids=world_cup_1994_player_ids(universe,country_id)
        assert len(ids)==22
        assert len(set(ids))==22
        all_ids.extend(ids)
        squad=historical_world_cup_1994_squad(universe,country_id)
        assert len(squad)==22
        assert all(player["historical_squad_1994"] for player in squad)
    assert len(all_ids)==528
    assert len(set(all_ids))==528


def test_all_24_usa94_countries_are_visible_functional_national_teams():
    universe=default_runtime_snapshot()
    catalog={row.country_id:row for row in national_team_catalog(universe)}
    for country_id in world_cup_1994_country_ids():
        assert country_id in catalog
        row=catalog[country_id]
        assert row.eligible_players>=22
        assert row.qualified_1994 is True
        assert row.world_cup_1994_squad_complete is True
        assert row.world_cup_1994_group in set("ABCDEF")
        assert row.historical_head_coach


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Tres contenedores 'Otros-' quedaron vacios (Paises Bajos, Grecia, Turquia) al pasar sus jugadores a clubes reales, y Popov sigue sin reconciliarse al Racing."
), strict=True)
def test_market_containers_hold_nonplayable_club_players_but_never_join_a_league():
    universe=default_runtime_snapshot()
    containers=[team for team in universe.payload["teams"] if team.get("market_container")]
    assert containers
    admitted={int(row["source_id"]) for row in universe.payload["leagues"] if row.get("admitted",True)}
    assert all(int(team.get("league_id") or 0) not in admitted for team in containers)
    assert all(team.get("playable") is False and team.get("can_buy_players") is False and team.get("players_transferable") is True for team in containers)
    assert all(universe.players_by_team.get(int(team["source_id"])) for team in containers)


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Tres contenedores 'Otros-' quedaron vacios (Paises Bajos, Grecia, Turquia) al pasar sus jugadores a clubes reales, y Popov sigue sin reconciliarse al Racing."
), strict=True)
def test_verified_playable_club_assignments_are_not_sent_to_otros():
    universe=default_runtime_snapshot()
    expected={
        9494053:734,  # Hugo Pérez: true USA94 addition
        9494079:793,  # Thomas N'Kono: true USA94 addition
        4842:303,     # Yuran: reconciled to existing Benfica player
        515:17,       # Popov: reconciled to existing Racing player
        2114:253,     # Phelan: existing Manchester City player
        1912:249,     # McGrath: existing Aston Villa player
        2117:253,     # Kernaghan: existing Manchester City player
        1951:323,     # Babb: existing Coventry player
        2051:80,      # Cascarino: existing Chelsea player
        1707:79,      # McGoldrick: existing Arsenal player
        1828:337,     # Sheridan: existing Sheffield Wednesday player
        2238:336,     # Kelly: existing Sheffield United player
    }
    for player_id,team_id in expected.items():
        player=universe.players_by_id[player_id]
        assert player.get("world_cup_1994")
        assert int(player["team_id"])==team_id
        assert player.get("market_container_origin") is None
    # Only true additions need the external club-assignment provenance field;
    # reconciled legacy identities intentionally keep their existing club row.
    assert universe.players_by_id[9494053].get("club_assignment_source")=="1994 FIFA World Cup squad club listing"
    assert universe.players_by_id[9494079].get("club_assignment_source")=="1994 FIFA World Cup squad club listing"


def test_otros_player_is_a_normal_foreigner_for_spanish_registration():
    universe=default_runtime_snapshot()
    incoming=next(p for p in universe.payload["players"] if p.get("market_container_origin")=="Nigeria")
    rule=competition_foreign_rule(universe,kind="league",source_id=1,team_id=3)
    assert rule.home_country_id==11
    assert is_foreign_player(incoming,home_country_id=rule.home_country_id,continental=False)
    assert rule.max_squad is not None
    current=[{"nationality_id":59} for _ in range(rule.max_squad)]
    allowed,reason=can_register_foreign_signing(current,incoming,rule)
    assert allowed is False
    assert "límite de extranjeros" in reason


def test_ai_can_buy_from_otros_but_otros_are_not_buyers():
    universe=default_runtime_snapshot()
    active_leagues={int(x["source_id"]) for x in universe.payload["leagues"] if x.get("admitted",True)}
    active=[int(t["source_id"]) for t in universe.payload["teams"] if int(t.get("league_id") or 0) in active_leagues]
    containers=[int(t["source_id"]) for t in universe.payload["teams"] if t.get("market_container")]
    players_by_team={tid:list(rows) for tid,rows in universe.players_by_team.items()}
    finances={str(int(t["source_id"])):initial_club_finances(t,players=universe.players_by_team.get(int(t["source_id"]),[])) for t in universe.payload["teams"]}
    for tid in active: finances[str(tid)]["cash"]=1_000_000_000
    actions=run_ai_transfer_window(
        current_date=date(1993,7,1),controlled_team_id=-1,eligible_team_ids=active,
        players_by_team=players_by_team,seller_team_ids=containers,seller_release_exempt_ids=set(containers),
        development={},club_finances=finances,player_team_overrides={},contract_overrides={},seed=9394,max_deals=8,
        signing_allowed=lambda buyer,player: True,
    )
    assert actions
    assert all(int(row["from_team_id"]) in containers for row in actions)
    assert all(int(row["to_team_id"]) in active for row in actions)
    assert all(int(row["to_team_id"]) not in containers for row in actions)
    assert all(int(row.get("fee") or 0) > 0 for row in actions)
    assert all(int(row.get("salary") or 0) > 0 for row in actions)


def test_world_championship_1994_uses_real_24_and_exact_historical_squad_pool():
    universe=default_runtime_snapshot()
    tournament=simulate_world_championship_24(universe,year=1994,development=None,seed=1994)
    assert tournament["participants"]==world_cup_1994_country_ids()
    assert tournament["historical_1994_participants"] is True
    assert tournament["historical_1994_squads"] is True
    assert len(tournament["matches"])==51
    assert {row["group"] for row in tournament["matches"] if row["stage"]=="group"}==set("ABCDEF")


def test_enrichment_report_matches_runtime_and_source_counts_stay_provenance_only():
    universe=default_runtime_snapshot()
    report=universe.payload["world_cup_1994_enrichment"]
    assert report["players"]==528
    assert report["source_existing_players"]+report["added_players"]==528
    assert report["added_players"]==267
    assert report["market_container_players"]==265
    assert report["playable_club_assignments"]==2
    # Do not rewrite source provenance just because derived international records
    # were added at runtime.
    assert universe.counts["historical_players"]==10528
    assert len(universe.players_by_id)==len(universe.payload["players"])
    assert len(universe.players_by_id)>10528+report["added_players"]+int(universe.payload["national_pool_1993_94_enrichment"]["created"])


def test_functional_catalog_requires_22_and_real_positional_balance():
    universe=default_runtime_snapshot()
    catalog=national_team_catalog(universe)
    assert len(catalog)>=50
    assert any(row.country_id==15 for row in catalog)  # Australia is functional after Branko Milosevic restoration.
    for row in catalog:
        players=[p for p in universe.payload["players"] if not p.get("retired") and int(p.get("international_country_id") or p.get("birth_country_id") or 0)==row.country_id]
        counts={pos:0 for pos in ("POR","DEF","MED","DEL")}
        for player in players:
            pos=str(player.get("broad_position") or "MED").upper()
            if pos in counts:
                counts[pos]+=1
        assert len(players)>=22
        assert counts["POR"]>=2
        assert counts["DEF"]>=5
        assert counts["MED"]>=5
        assert counts["DEL"]>=3


def test_explicit_saved_national_selection_is_rendered_exactly():
    from backend.app.football9394.national_teams import national_team_snapshot
    universe=default_runtime_snapshot()
    country_id=11  # Spain: large enough pool to distinguish saved 22 from auto-selection.
    eligible=[p for p in universe.payload["players"] if not p.get("retired") and int(p.get("international_country_id") or p.get("birth_country_id") or 0)==country_id]
    eligible=sorted(eligible,key=lambda p:int(p["source_id"]))
    chosen=[int(p["source_id"]) for p in eligible[-22:]]
    snapshot=national_team_snapshot(universe,country_id,selected_player_ids=chosen)
    assert [int(p["id"]) for p in snapshot["squad"]]==chosen
    assert len(snapshot["world_cup_1994"]["squad"])==22
