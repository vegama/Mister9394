from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.source_catalog_runtime import default_source_catalog

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/football9394'

def load(name:str):
    return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v031_roster_hygiene_removes_only_legacy_id_collision_rows():
    audit=load('historical_profiles_metadata_audit_v031.json')
    assert audit['roster_hygiene']['removed_assignments']==142
    assert audit['roster_hygiene']['by_country']=={'Belgium':60,'Turkey':47,'Russia':35}
    snap=load('historical_snapshot.json')
    active=[p for p in snap['players'] if not p.get('retired')]
    for lid in (930052,930057,930015,930047):
        teams=[t for t in snap['teams'] if t.get('league_id')==lid]
        counts=[sum(int(p.get('team_id') or 0)==int(t['source_id']) for p in active) for t in teams]
        assert teams and min(counts)>=18
    assert not [p for p in snap['players'] if p.get('display_name') in {'Cedric Bakenga','Fedor Smolov','Magomed Ozdoev'} and p.get('team_id') in {415,645,617}]


def test_v031_source_backed_profile_corrections_are_materialised():
    p={int(x['source_id']):x for x in load('historical_snapshot.json')['players']}
    assert p[9495305]['birth_date']=='1971-10-15T00:00:00'
    assert (int(p[9495172]['primary_role']),p[9495172]['historical_position_1993_94'])==(1,'Right Back')
    assert (int(p[9496077]['primary_role']),p[9496077]['historical_position_1993_94'])==(6,'Defensive Midfielder')
    assert (int(p[9496080]['primary_role']),p[9496080]['historical_position_1993_94'])==(7,'Centre Midfielder')
    assert (int(p[9494084]['primary_role']),p[9494084]['historical_position_1993_94'])==(9,'Right Midfielder')
    assert (int(p[9497350]['primary_role']),p[9497350]['historical_position_1993_94'])==(8,'Attacking Midfielder')
    assert (int(p[9495327]['primary_role']),p[9495327]['historical_position_1993_94'])==(7,'Centre Midfielder')
    assert p[9495348]['height_cm']==188 and p[9495348]['weight_kg']==77
    for sid in (9495172,9496077,9496080,9494084,9497350,9495327):
        assert p[sid]['attribute_source']=='fixed_source_comparable_role_correction_0.31'
        assert len(p[sid]['attribute_comparable_source_ids'])==2


def test_v031_greece_all_clubs_have_season_specific_historical_venues_without_modern_fabrication():
    universe=default_runtime_snapshot();catalog=default_source_catalog()
    teams=[t for t in universe.payload['teams'] if t.get('league_id')==930047]
    assert len(teams)==18
    assert all(t.get('venue_source_status')=='historical_source_backed_1993_94' for t in teams)
    rows=[catalog.stadium(t['stadium_id']) for t in teams]
    assert all(r and r['historical_season']=='1993-94' for r in rows)
    assert {r['name'] for r in rows} >= {'Nikos Goumas Stadium','Karaiskakis Stadium','Xanthi Ground','Alcazar Stadium'}
    assert all(r.get('capacity') is None and r.get('width_m') is None and r.get('length_m') is None for r in rows)



def test_v031_russia_reconstructed_clubs_have_1993_venues_crosschecked_against_match_records():
    universe=default_runtime_snapshot();catalog=default_source_catalog()
    teams=[t for t in universe.payload['teams'] if t.get('league_id')==930015 and int(t['source_id'])>=9315001]
    assert len(teams)==16
    assert all(t.get('venue_source_status')=='historical_source_backed_1993' for t in teams)
    rows=[catalog.stadium(t['stadium_id']) for t in teams]
    assert all(r and r['historical_season']=='1993' for r in rows)
    names={int(r['historical_team_id']):r['name'] for r in rows}
    assert names[9315006]=='Central Stadium'
    assert names[9315013]=='Luch Stadium'
    assert names[9315015]=='Rostselmash Stadium'
    assert all(r.get('capacity') is None and r.get('width_m') is None and r.get('length_m') is None for r in rows)


def test_v031_all_1808_active_reconstructed_players_have_source_backed_historical_biographies():
    snap=load('historical_snapshot.json')
    tids={int(t['source_id']) for t in snap['teams'] if t.get('league_id') in {930015,930047,930052,930057}}
    players=[p for p in snap['players'] if not p.get('retired') and p.get('team_id') in tids]
    assert len(players)>=1790
    assert all(p.get('historical_biography_status')=='source_backed_season_summary' for p in players)
    assert all(p.get('historical_biography_1993_94') for p in players)
    assert all(p.get('historical_biography_source_url') for p in players)
    audit=load('historical_biographies_audit_v031.json')
    assert audit['biographies_written']==1808
    assert audit['biographies_with_season_stats']==1808


def test_v031_belgian_referee_pool_is_complete_and_greek_pool_is_explicit_subset():
    catalog=default_source_catalog();snapshot=load('historical_snapshot.json')
    bel=catalog.referees_for_league(930052);gre=catalog.referees_for_league(930047)
    assert len(bel)==25
    assert len(gre)==11
    assert {r['display_name'] for r in bel}>={'Frans Van Den Wyngaert','Michel Piraux','Guy Goethals'}
    assert {r['display_name'] for r in gre}>={'Sotiris Mbazas','Kostas Karapatas','Dimitris Iliadis'}
    assert all(r.get('birth_country_id') is None and r.get('nationality_country_id')==17 for r in bel)
    assert all(r.get('birth_country_id') is None and r.get('nationality_country_id')==47 for r in gre)
    b=next(l for l in snapshot['leagues'] if l['source_id']==930052)['source_rule_hints']
    g=next(l for l in snapshot['leagues'] if l['source_id']==930047)['source_rule_hints']
    assert b['referee_pool_status']=='historical_source_backed_complete_1993_94'
    assert b['referee_pool_size']==25
    assert g['referee_pool_status']=='historical_source_backed_subset_1993_94'
    assert (g['referee_pool_encoded'],g['referee_pool_reported_total'])==(11,45)


def test_v031_sixteen_new_bdf_portraits_are_bundled_native_assets():
    reg={int(r['source_id']):r for r in load('created_players_registry.json')['players']}
    queue={int(r['source_id']):r for r in load('bdfutbol_photo_queue.json')['players']}
    ids={9495316,9495319,9495337,9495336,9495331,9495327,9495348,9495354,9495342,9494093,9496352,9496353,9496354,9496355,9496357,9496358}
    for sid in ids:
        assert reg[sid]['photo_status']=='bundled_normalized_bdfutbol'
        assert queue[sid]['photo_status']=='bundled_normalized_bdfutbol'
        path=ROOT/'frontend/public/historical9394/players'/f'{sid}.jpg'
        assert path.exists()
        with Image.open(path) as im:
            assert im.size==(40,55) and im.mode=='RGB'
