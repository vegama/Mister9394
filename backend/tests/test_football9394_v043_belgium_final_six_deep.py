from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'


def load(name:str):
    return json.loads((DATA/name).read_text(encoding='utf-8'))


def test_v043_final_six_close_belgium_birth_dates_and_stage_queue():
    a=load('historical_profiles_metadata_audit_v043.json')
    b=a['profile_gaps_before']['Belgium']; z=a['profile_gaps_after']['Belgium']
    assert b['missing_birth_date']==116 and z['missing_birth_date']==0
    assert b['missing_international_country_id']==107 and z['missing_international_country_id']==1
    assert b['missing_birth_country_id']==137 and z['missing_birth_country_id']==32
    assert b['missing_height_cm']==224 and z['missing_height_cm']==150
    assert b['missing_weight_kg']==310 and z['missing_weight_kg']==268
    assert a['profiles']['curated_existing']==136
    assert a['profiles']['by_club']=={
        'RFC Liège':24,'Cercle Brugge':24,'Oostende':19,
        'KV Mechelen':24,'Gent':25,'Lierse':20,
    }
    stage=load('belgium_1993_94_roster_staging.json')
    for name, expected in a['profiles']['by_club'].items():
        club=next(c for c in stage['clubs'] if c['name']==name)
        assert len(club['players'])==expected
        assert all(r.get('resolved_birth_date') for r in club['players'])
        assert all(r.get('resolved_country_id') is not None for r in club['players'])
        assert all(r.get('bdfutbol_id') for r in club['players'])
    queue=load('belgium_deepening_queue_v043.json')
    assert queue['queue']==[]
    assert queue['belgium_queue_complete'] is True
    assert queue['russia_status']=='unlocked_next_but_untouched_in_v043'


def test_v043_key_position_corrections_and_historical_countries():
    by={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    expected_roles={
        9496270:1,  # Eric Deflandre - right back
        9496279:2,  # Philippe Lenglois - left back
        9496284:17, # Christian Theissen - forward
        9496271:7,  # Jean-François Demonceau - midfielder
        9496046:1,  # Bert Lamaire - right back
        9494021:2,  # Tibor Selymes - left back
        9496042:3,  # Stéphane Demol - central
        9496049:3,  # Thierry Siquet - central
        9496258:1,  # Johnny Nierynck - right back
        9496200:2,  # Nico Van Kerckhoven - left back
        9496188:3,  # Steve Goossen - central
        9496185:1,  # David Brocken - right back
    }
    for sid,role in expected_roles.items(): assert by[sid]['primary_role']==role

    # Zaire remains the 1993 state/football identity despite modern DR Congo source geography.
    for sid in [9496277,9496247]:
        assert by[sid]['international_country_id']==88
        assert by[sid]['birth_country_id']==88
    # Independent post-Yugoslav states are not collapsed into Serbia/Yugoslavia.
    assert by[9495160]['international_country_id']==20  # Bosnia-Herzegovina
    assert by[9496134]['international_country_id']==20  # Bosnia-Herzegovina
    assert by[9496130]['international_country_id']==31  # Croatia
    assert by[9496166]['international_country_id']==31  # Croatia
    # Dual nationalities explicitly present in source evidence are retained.
    assert by[9496267]['profile_nationality_country_ids']==[62,10]  # Brazil + Portugal
    assert by[9494220]['profile_nationality_country_ids']==[17,31]  # Belgium + Croatia


def test_v043_shared_profiles_registry_photo_queue_and_single_intentional_nat_gap():
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    audit=load('historical_profiles_metadata_audit_v043.json')
    assert set(audit['profiles']['preserved_prior_deep_profiles'])=={9496329,9496327,9496328}
    assert snap[9496329]['primary_role']==6  # Urbán remains source-backed DM
    assert snap[9496327]['primary_role']==13 # Pister remains source-backed left midfield
    assert snap[9496328]['primary_role']==8  # Schepens remains source-backed attacking midfield
    assert {x['club'] for x in snap[9496329]['historical_club_spells_1993_94']}=={'Waregem','KV Mechelen'}
    assert {x['club'] for x in snap[9496327]['historical_club_spells_1993_94']}=={'Standard Liège','Gent'}
    assert {x['club'] for x in snap[9496328]['historical_club_spells_1993_94']}=={'Standard Liège','Gent'}

    reg=load('created_players_registry.json'); q=load('bdfutbol_photo_queue.json')
    rb={int(x['source_id']):x for x in reg['players']}; qb={int(x['source_id']):x for x in q['players']}
    assert set(rb)==set(qb)
    assert len(rb)==len(reg['players']) and len(qb)==len(q['players'])
    for sid in [int(x['source_id']) for x in audit['profiles']['changes']]:
        assert rb[sid].get('bdfutbol_id') and rb[sid].get('bdfutbol_url')
        assert qb[sid]['photo_status'] in {'ready_for_download','bundled_normalized_bdfutbol'}
    assert qb[9496277]['country_name']=='Zaire'
    assert qb[9496247]['country_name']=='Zaire'

    # The only remaining Belgian-league nationality gap is a previously documented, intentional Mauritius catalogue gap.
    belgian_team_ids={int(t['source_id']) for t in load('historical_snapshot.json')['teams'] if t.get('league_id')==930052}
    missing=[p for p in snap.values() if p.get('team_id') in belgian_team_ids and p.get('international_country_id') is None]
    assert [(int(p['source_id']),p['display_name']) for p in missing]==[(9496307,'Willy Vincent')]
    assert 'Mauritian international identity is source-backed' in missing[0]['historical_profile_source_note']


def test_v043_russia_remains_frozen_and_next_front_is_russia():
    audit=load('historical_profiles_metadata_audit_v043.json')
    queue=load('belgium_deepening_queue_v043.json')
    assert audit['russia_touched'] is False
    assert audit['russia_integrity']['unchanged'] is True
    assert audit['russia_integrity']['before_sha256']==audit['russia_integrity']['after_sha256']
    assert audit['next_front']==['Russia']
    assert queue['russia_status']=='unlocked_next_but_untouched_in_v043'
    policy=audit['historical_country_policy']['future_Russia']
    assert 'Russia league remains untouched in v0.43' in policy
    assert 'USSR must never be auto-mapped to Russia' in policy
