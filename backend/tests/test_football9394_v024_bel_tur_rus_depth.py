from __future__ import annotations

import pytest

import json
from pathlib import Path

from backend.app.football9394.national_teams import national_team_catalog
from backend.app.football9394.rules import (
    BELGIUM_FIRST_DIVISION_1993_94,
    TURKEY_FIRST_DIVISION_1993_94,
    RUSSIA_SUPREME_LEAGUE_1993,
    GREECE_ALPHA_ETHNIKI_1993_94,
)
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.registry import default_registry_9394, UnresolvedHistoricalRulesError

ROOT=Path(__file__).resolve().parents[2]
SNAP=ROOT/'data/football9394/historical_snapshot.json'
REG=ROOT/'data/football9394/created_players_registry.json'
MDB_AUDIT=ROOT/'docs/v024_full_mdb_bel_tur_rus_reconciliation.json'


def _players():
    return json.loads(SNAP.read_text(encoding='utf-8'))['players']


def test_depth_pools_are_around_forty_and_balanced():
    players=_players()
    for cid,minimum in ((17,38),(84,40),(40,38)):
        rows=[p for p in players if int(p.get('international_country_id') or 0)==cid and not p.get('retired')]
        assert len(rows)>=minimum
        pos={key:sum(1 for p in rows if p.get('broad_position')==key) for key in ('POR','DEF','MED','DEL')}
        assert pos['POR']>=3
        assert pos['DEF']>=8
        assert pos['MED']>=8
        assert pos['DEL']>=5


def test_new_batch_was_checked_against_full_mdb_and_has_no_hidden_exact_match():
    report=json.loads(MDB_AUDIT.read_text(encoding='utf-8'))
    assert report['source_players']==37312
    assert report['new_batch']==61
    assert report['exact_hidden_existing']==0
    assert report['name_collisions']==0
    assert report['missing']==61


def test_new_batch_profiles_are_fixed_and_individual_not_provisional():
    rows=[p for p in _players() if p.get('creation_batch')=='bel_tur_rus_national_depth_0.24']
    assert len(rows)==55
    vectors=[]
    pending={int(p['source_id']) for p in rows if p.get('profile_review_required')}
    assert {9495331,9495336,9495337,9495342} <= pending
    for p in rows:
        assert str(p.get('attribute_source') or '').startswith('fixed_source_comparable_')
        assert p.get('historical_club_1994')
        assert p.get('historical_position_1993_94')
        vectors.append(tuple(sorted((p.get('attributes') or {}).items())))
    assert len(set(vectors))==len(rows)


def test_photo_registry_keeps_historical_club_and_position_for_new_players():
    payload=json.loads(REG.read_text(encoding='utf-8'))
    rows=[r for r in payload['players'] if r.get('creation_batch')=='bel_tur_rus_national_depth_0.24']
    assert len(rows)==55
    assert all(r.get('historical_club_1994') for r in rows)
    assert all(r.get('historical_position_1993_94') for r in rows)
    assert all(r.get('photo_status') in {'pending','pending_identity_profile','ready_for_download','bundled_normalized_bdfutbol'} for r in rows)


def test_catalog_exposes_depth_readiness():
    catalog={r.country_id:r for r in national_team_catalog(default_runtime_snapshot())}
    for cid in (17,84,40):
        assert catalog[cid].depth_ready_40 is True
        assert catalog[cid].depth_gap_to_40==0


def test_belgium_turkey_russia_historical_rules():
    bel=BELGIUM_FIRST_DIVISION_1993_94
    tur=TURKEY_FIRST_DIVISION_1993_94
    rus=RUSSIA_SUPREME_LEAGUE_1993
    assert (bel.teams,bel.rounds,bel.points_win,bel.direct_relegation_places)==(18,34,2,(17,18))
    assert (tur.teams,tur.rounds,tur.points_win,tur.direct_relegation_places)==(16,30,2,(14,15,16))
    assert (rus.teams,rus.rounds,rus.points_win,rus.direct_relegation_places)==(18,34,2,(15,16,17,18))


def test_league_foundation_activates_belgium_turkey_and_russia_after_roster_gates():
    foundation=json.loads((ROOT/'data/football9394/bel_tur_rus_1993_94_league_foundations.json').read_text(encoding='utf-8'))
    expected={'Bélgica':18,'Turquía':16,'Rusia':18}
    all_urls=[]
    for league in foundation['leagues']:
        assert len(league['clubs'])==expected[league['country']]
        assert league['source_mdb_row_is_historical'] is False
        assert league['source_mdb_row_blocked_from_runtime_binding'] is True
        assert int(league['historical_runtime_league_id'])>=930000
        assert league['activation_status']=='active_historical_roster_gate_passed'
        assert int(league['activated_runtime_league_id'])==({'Bélgica':930052,'Turquía':930057,'Rusia':930015}[league['country']])
        expected_status='complete_historical_1993' if league['country']=='Rusia' else 'complete_historical_1993_94'
        assert all(club['roster_status']==expected_status for club in league['clubs'])
        assert all(int(club['team_id'])>0 for club in league['clubs'])
        all_urls.extend(club['bdfutbol_squad_url'] for club in league['clubs'])
    assert len(all_urls)==52
    assert len(set(all_urls))==52
    snapshot=default_runtime_snapshot()
    ids={int(row.get('source_id') or 0) for row in snapshot.payload['leagues']}
    assert {930015,930052,930057}.issubset(ids)
    assert not ids.intersection({15,52,57})


def test_belgium_roster_gate_is_complete_unique_and_playable():
    audit=json.loads((ROOT/'data/football9394/belgium_1993_94_roster_gate_audit.json').read_text(encoding='utf-8'))
    assert audit['status']=='pass_belgium_1993_94_active'
    assert audit['staged_rows']==413
    assert audit['unique_identities']==406
    assert audit['same_season_transfer_duplicate_rows']==7
    assert audit['clubs']==18
    assert audit['minimum_active_roster']>=18
    assert min(audit['roster_counts'].values())>=18
    identities=audit['identities']
    assert len(identities)==406
    assert len({int(row['source_id']) for row in identities})==406
    assert all(0<=int(row['role'])<=17 for row in identities)
    assert all(row['position'] and row['position_source'] for row in identities)
    players=_players()
    by_team={}
    for p in players:
        if not p.get('retired'):
            by_team.setdefault(int(p.get('team_id') or 0),[]).append(p)
    foundation=json.loads((ROOT/'data/football9394/bel_tur_rus_1993_94_league_foundations.json').read_text(encoding='utf-8'))
    bel=next(row for row in foundation['leagues'] if row['country']=='Bélgica')
    for club in bel['clubs']:
        rows=by_team.get(int(club['team_id']),[])
        assert len(rows)>=18
        assert all(0<=int(p['primary_role'])<=17 for p in rows)
        assert all(p.get('historical_position_1993_94') for p in rows)
        assert all(p.get('historical_position_source') for p in rows)
    registry=default_registry_9394()
    assert registry.resolve_source('league',930052) is BELGIUM_FIRST_DIVISION_1993_94



def test_turkey_roster_gate_is_complete_unique_and_playable():
    audit=json.loads((ROOT/'data/football9394/turkey_1993_94_roster_gate_audit.json').read_text(encoding='utf-8'))
    assert audit['status']=='pass_turkey_1993_94_active'
    assert audit['staged_rows']==414
    assert audit['unique_staged_identities']==414
    assert audit['clubs']==16
    assert audit['minimum_active_roster']>=18
    assert audit['minimum_is_floor_not_target'] is True
    assert audit['source_roster_target'].startswith('all rows')
    assert audit['otros_turquia_stranded_recognised_club']==0
    ids=[int(row['source_id']) for row in audit['identities']]
    assert len(ids)==len(set(ids))==414
    assert audit['reused_existing_players']>0
    players=_players()
    active=[p for p in players if not p.get('retired')]
    for name in ('Hakan Şükür','Bülent Korkmaz','Tugay Kerimoğlu','Sergen Yalçın','Hami Mandıralı','Aykut Kocaman'):
        assert sum(1 for p in active if p.get('display_name')==name)==1
    registry=default_registry_9394()
    assert registry.resolve_source('league',930057) is TURKEY_FIRST_DIVISION_1993_94


def test_russia_roster_gate_is_complete_unique_and_playable():
    audit=json.loads((ROOT/'data/football9394/russia_1993_roster_gate_audit.json').read_text(encoding='utf-8'))
    assert audit['status']=='pass_russia_1993_active'
    assert audit['staged_rows']==492
    assert audit['unique_staged_identities']==492
    assert audit['clubs']==18
    assert audit['minimum_active_roster']>=18
    assert audit['minimum_is_floor_not_target'] is True
    assert audit['source_roster_target'].startswith('all rows')
    assert audit['otros_russia_stranded_recognised_club']==0
    ids=[int(row['source_id']) for row in audit['identities']]
    assert len(ids)==len(set(ids))==492
    assert audit['reused_existing_players']>=16
    assert audit['modern_mdb_league_id_15_active'] is False
    players=_players()
    active=[p for p in players if not p.get('retired')]
    # Identity uniqueness is keyed by stable source IDs; later deep passes may expand
    # display names with patronymics/transliterations without creating another person.
    for sid in (9494088,9495357,9494084,9494087,9494085,9494086,9495358,9495355):
        assert sum(1 for p in active if int(p.get('source_id') or 0)==sid)==1
    registry=default_registry_9394()
    assert registry.resolve_source('league',930015) is RUSSIA_SUPREME_LEAGUE_1993



@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. La puerta de plantilla de Grecia no esta completa ni es unica todavia."
), strict=True)
def test_greece_roster_gate_is_complete_unique_and_playable():
    audit=json.loads((ROOT/'data/football9394/greece_1993_94_roster_gate_audit.json').read_text(encoding='utf-8'))
    assert audit['status']=='pass_greece_1993_94_active'
    assert audit['staged_rows']==496
    assert audit['unique_staged_identities']==496
    assert audit['clubs']==18
    assert audit['minimum_active_roster']>=22
    assert audit['minimum_is_floor_not_target'] is True
    assert audit['source_roster_target'].startswith('all rows')
    assert audit['reused_existing_players']==496
    assert audit['verified_greece_pool_stranded_in_otros']==0
    ids=[int(row['source_id']) for row in audit['identities']]
    assert len(ids)==len(set(ids))==496
    players=_players()
    active=[p for p in players if not p.get('retired')]
    for name in ('Stelios Manolas','Dimitris Saravakos','Nikos Machlas','Tasos Mitropoulos','Vasilis Dimitriadis','Alexis Alexandris'):
        assert sum(1 for p in active if p.get('display_name')==name)==1
    greek_team_ids=set(range(9347001,9347019))
    core=[p for p in active if int(p.get('team_id') or 0) in greek_team_ids]
    # The source roster has 496 rows, but six are verified same-season club
    # spells of players already present elsewhere in the league. Runtime keeps
    # one person per canonical identity and preserves both spells in metadata.
    staging=json.loads((ROOT/'data/football9394/greece_1993_94_roster_staging.json').read_text(encoding='utf-8'))
    canonical_ids={int(r['resolved_source_id']) for c in staging['clubs'] for r in c['players']}
    assert len(canonical_ids)==490
    assert len(core)==len(canonical_ids)
    assert all(p.get('historical_position_1993_94') for p in core)
    assert all(p.get('historical_position_source') for p in core)
    assert all(p.get('attributes') for p in core)
    registry=default_registry_9394()
    assert registry.resolve_source('league',930047) is GREECE_ALPHA_ETHNIKI_1993_94


def test_greece_historical_rules_and_runtime_binding():
    gre=GREECE_ALPHA_ETHNIKI_1993_94
    assert (gre.teams,gre.rounds,gre.points_win,gre.direct_relegation_places)==(18,34,2,(16,17,18))
    snapshot=default_runtime_snapshot()
    ids={int(row.get('source_id') or 0) for row in snapshot.payload['leagues']}
    assert 930047 in ids
    league=next(row for row in snapshot.payload['leagues'] if int(row.get('source_id') or 0)==930047)
    assert league['source_edition']=='1993-94'
    assert league['team_count']==18


def test_greece_has_no_fictional_gate_fillers_and_keeps_source_provenance():
    stage=json.loads((ROOT/'data/football9394/greece_1993_94_roster_staging.json').read_text(encoding='utf-8'))
    assert len(stage['clubs'])==18
    assert all(len(c['players'])>=18 for c in stage['clubs'])
    assert sum(len(c['players']) for c in stage['clubs'])==496
    assert all(p.get('rsssf_name') and p.get('source_url') for c in stage['clubs'] for p in c['players'])
    created=[p for p in _players() if p.get('creation_batch')=='greece_league_rosters_0.28']
    assert len(created)==474
    assert all(p.get('attribute_source') in {
        'fixed_source_comparable_greece_1993_94',
        'fixed_source_comparable_role_correction_0.29',
        'fixed_source_comparable_role_correction_0.31',
    } for p in created)
    corrected=[p for p in created if p.get('attribute_source')=='fixed_source_comparable_role_correction_0.29']
    assert [(int(p['source_id']),p['display_name']) for p in corrected]==[(9496943,'Krzysztof Warzycha')]
    assert all(p.get('external_origin')=='historical_greece_1993_94' for p in created)
    pending={int(p['source_id']) for p in created if p.get('profile_review_required')}
    assert pending=={9497518,9497522}

def test_reconstructed_players_keep_source_backed_age_without_fake_birth_date():
    from backend.app.football9394.player_identity import age_on
    rows=[p for p in _players() if p.get('creation_batch') in {'turkey_league_rosters_0.26','russia_league_rosters_0.27'}]
    assert rows
    samples=[p for p in rows if not p.get('birth_date') and p.get('historical_age_1993_94') is not None]
    assert samples
    assert all(age_on(p)==int(p['historical_age_1993_94']) for p in samples[:50])

def test_belgium_transfer_rows_share_one_identity_without_duplicates():
    stage=json.loads((ROOT/'data/football9394/belgium_1993_94_roster_staging.json').read_text(encoding='utf-8'))
    transfer_names={'Nwanu','Schepens','Pister','Urbán','Abeels','Ballenghien','Ernès'}
    by_name={}
    for club in stage['clubs']:
        for row in club['players']:
            if row['bdfutbol_name'] in transfer_names:
                by_name.setdefault(row['bdfutbol_name'],set()).add(int(row['resolved_source_id']))
    assert set(by_name)==transfer_names
    assert all(len(ids)==1 for ids in by_name.values())


def test_belgium_bundled_portraits_are_native_40x55_jpeg():
    from PIL import Image
    audit=json.loads((ROOT/'data/football9394/belgium_1993_94_roster_gate_audit.json').read_text(encoding='utf-8'))
    assert audit['portraits_bundled_normalized']>=2
    root=ROOT/'frontend/public/historical9394/players'
    for sid in (9494216,9495172):
        path=root/f'{sid}.jpg'
        assert path.exists()
        with Image.open(path) as im:
            assert im.size==(40,55)
            assert im.mode=='RGB'


def test_modern_mdb_league_ids_are_not_bound_to_historical_rules():
    registry=default_registry_9394()
    for source_id in (15,52,57):
        try:
            registry.resolve_source('league',source_id)
        except UnresolvedHistoricalRulesError:
            pass
        else:
            raise AssertionError(f'modern MDB league source {source_id} must not resolve to 1993-94 rules')
    guard=json.loads((ROOT/'docs/v024_bel_tur_rus_mdb_league_row_guard.json').read_text(encoding='utf-8'))
    assert guard['status']=='pass_modern_source_rows_blocked'
    assert {row['source_edition'] for row in guard['rows']}=={'2017'}
    assert all(row['runtime_binding_allowed'] is False for row in guard['rows'])


def test_outfield_residual_goalkeeper_affinity_never_beats_real_goalkeeper():
    from backend.app.football9394.position_roles import assign_players_to_formation, role_for_player
    snapshot=default_runtime_snapshot()
    sevilla_b=list(snapshot.players_by_team[47])
    assignment=assign_players_to_formation(sevilla_b,'4-4-2')
    goalkeeper=next(row['player'] for row in assignment if row['slot']=='GK')
    assert role_for_player(goalkeeper).squad_slot=='GK'
