from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'
TARGET=['Rotor Volgograd','Dynamo Moskva','Tekstilshchik Kamyshin','Lokomotiv Moskva','Spartak Vladikavkaz','Torpedo Moskva']
PRE_V045='e07f35db04e5979433ed1bfc3a9e2704758a636abe8f116903eb12d7c9473111'

def load(name:str): return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v045_batch_closes_six_clubs_in_one_pass():
    a=load('historical_profiles_metadata_audit_v045.json')
    assert a['status']=='pass'
    assert a['target_clubs']==TARGET
    assert a['staging_rows_processed']==159
    assert a['individual_bdfutbol_profiles_resolved']==159
    assert a['unique_player_identities_after_merge']==158
    assert a['detailed_birth_profile_subset']==24
    assert a['russia_integrity']['before_sha256']==PRE_V045
    assert a['russia_integrity']['protected_other_clubs_unchanged'] is True
    assert a['russia_integrity']['russia_player_objects_before']==492
    assert a['russia_integrity']['russia_player_objects_after']==491

    stage=load('russia_1993_roster_staging.json')
    clubs={c['name']:c for c in stage['clubs']}
    expected={'Rotor Volgograd':23,'Dynamo Moskva':29,'Tekstilshchik Kamyshin':27,'Lokomotiv Moskva':29,'Spartak Vladikavkaz':22,'Torpedo Moskva':29}
    for name,n in expected.items():
        rows=clubs[name]['players']
        assert len(rows)==n
        assert all(r.get('bdfutbol_id') for r in rows)
        assert all(r.get('individual_profile_source_url') for r in rows)
        assert all(r.get('profile_identity_status')=='bdfutbol_individual_profile_resolved_v045' for r in rows)


def test_v045_proven_cross_club_duplicate_is_merged_not_name_guessed():
    snap=load('historical_snapshot.json')
    by={int(x['source_id']):x for x in snap['players']}
    assert 9496652 not in by
    ch=by[9497352]
    assert ch['bdfutbol_id']=='701521'
    assert ch['duplicate_resolution']=='cross_club_same_individual_profile_merged_v045'
    assert {x['club'] for x in ch['historical_club_spells_1993_94']} >= {'Spartak Moskva','Dynamo Moskva'}
    assert any(x.get('merged_source_id')==9496652 for x in ch['identity_merge_history'])

    stage=load('russia_1993_roster_staging.json')
    dyn=next(c for c in stage['clubs'] if c['name']=='Dynamo Moskva')
    row=next(r for r in dyn['players'] if r['bdfutbol_name']=='Chernyshov')
    assert row['resolved_source_id']==9497352
    assert row['duplicate_source_id_retired']==9496652
    assert row['identity_resolution']=='merged_to_existing_cross_club_identity_v045'


def test_v045_homonyms_remain_distinct_when_profile_ids_are_distinct():
    stage=load('russia_1993_roster_staging.json')
    kam=next(c for c in stage['clubs'] if c['name']=='Tekstilshchik Kamyshin')
    morozov=[r for r in kam['players'] if r['bdfutbol_name']=='Morozov']
    assert len(morozov)==2
    assert {int(x['resolved_source_id']) for x in morozov}=={9496654,9496656}
    assert {x['bdfutbol_id'] for x in morozov}=={'591050','591054'}


def test_v045_ussr_birth_state_stays_separate_from_successor_territory_and_citizenship():
    snap=load('historical_snapshot.json')
    by={int(x['source_id']):x for x in snap['players']}
    for sid,territory in [(9496619,202),(9496620,85),(9496629,132),(9496631,18),(9494086,104)]:
        p=by[sid]
        assert p.get('birth_country_id') is None
        assert p['historical_birth_state']=='USSR'
        assert p['birth_territory_country_id']==territory
        assert p['citizenship_country_ids_1993']==[]
        assert 'not_inferred' in p['citizenship_1993_resolution']
    assert by[9496619]['historical_birth_place_text']=='Dushanbe'
    assert by[9496620]['historical_birth_place_text']=='Luhansk'
    assert by[9494086]['historical_birth_place_text']=='Velospiri'


def test_v045_registry_photo_queue_and_profile_ids_are_unique():
    reg=load('created_players_registry.json')['players']; q=load('bdfutbol_photo_queue.json')['players']
    rb={int(x['source_id']):x for x in reg}; qb={int(x['source_id']):x for x in q}
    assert len(rb)==len(reg); assert len(qb)==len(q); assert set(rb)==set(qb)
    assert 9496652 not in rb and 9496652 not in qb

    stage=load('russia_1993_roster_staging.json')
    bids={}
    for c in stage['clubs']:
        if c['name'] not in TARGET: continue
        for r in c['players']:
            bid=r['bdfutbol_id']; sid=int(r['resolved_source_id'])
            assert bid not in bids or bids[bid]==sid
            bids[bid]=sid
            if sid in qb:
                assert qb[sid]['photo_status'] in {'ready_for_download','bundled_normalized_bdfutbol'}


def test_v045_queue_advances_to_uralmash():
    q=load('russia_deepening_queue_v045.json')
    assert q['completed_clubs']==['Spartak Moskva']+TARGET
    assert q['next_club']=='Uralmash'
    assert q['queue'][0]=='Uralmash'
    assert q['staging_rows_completed_this_pass']==159
    assert q['unique_identities_completed_this_pass']==158
