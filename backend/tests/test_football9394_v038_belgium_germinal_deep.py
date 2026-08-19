from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'

def load(name:str): return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v038_germinal_gap_reduction_and_stage_integrity():
    audit=load('historical_profiles_metadata_audit_v038.json')
    before=audit['profile_gaps_before']['Belgium']; after=audit['profile_gaps_after']['Belgium']
    assert before['missing_birth_date']==253 and after['missing_birth_date']==229
    assert before['missing_international_country_id']==233 and after['missing_international_country_id']==213
    assert before['missing_birth_country_id']==258 and after['missing_birth_country_id']==238
    assert before['missing_height_cm']==302 and after['missing_height_cm']==288
    assert before['missing_weight_kg']==353 and after['missing_weight_kg']==343
    assert audit['profiles']['curated_existing']==25
    stage=load('belgium_1993_94_roster_staging.json')
    club=next(c for c in stage['clubs'] if c['name']=='Germinal Ekeren')
    assert len(club['players'])==25
    assert all(r.get('resolved_birth_date') for r in club['players'])
    assert all(r.get('bdfutbol_id') for r in club['players'])

def test_v038_germinal_specialist_role_repairs():
    snap=load('historical_snapshot.json'); by={int(p['source_id']):p for p in snap['players']}
    expected={9496163:0,9496165:3,9496149:2,9496162:3,9496153:7,9496161:16,9495310:8,9496147:6,9496324:8,9496152:6,9496144:0,9496156:6,9496159:8,9496160:17,9496148:8,9496151:2,9496157:7,9496155:17,9496325:17}
    for sid,role in expected.items(): assert by[sid]['primary_role']==role
    assert by[9496149]['height_cm']==183 and by[9496149]['weight_kg']==84
    assert by[9496152]['height_cm']==187 and by[9496152]['weight_kg']==75
    assert by[9496159]['height_cm']==173

def test_v038_historical_countries_and_dual_nationalities():
    snap=load('historical_snapshot.json'); by={int(p['source_id']):p for p in snap['players']}
    assert by[9496159]['international_country_id']==88 and by[9496159]['birth_country_id']==88
    assert by[9496159]['historical_birth_place_text']=='Kinshasa (Zaire)'
    assert by[9496162]['profile_nationality_country_ids']==[6,17]
    assert by[9496161]['profile_nationality_country_ids']==[3,17]
    assert by[9496157]['profile_nationality_country_ids']==[56,17]
    assert by[9496150]['international_country_id']==74 and by[9496155]['international_country_id']==74

def test_v038_jussila_and_diagne_conflicts_are_not_silently_overwritten():
    snap=load('historical_snapshot.json'); by={int(p['source_id']):p for p in snap['players']}
    j=by[9496154]; d=by[9496150]
    assert j['display_name']=='Juha Jussila' and j['primary_role']==7 and j['profile_review_required'] is True
    assert 'Jani Jussila' in j['historical_profile_source_note']
    assert d['primary_role']==17 and d['profile_review_required'] is True
    assert 'central midfield' in d['historical_profile_source_note'].lower()
    conflicts=load('belgium_source_conflicts_v038.json')['conflicts']
    assert {x['name'] for x in conflicts}=={'Victor Diagne','Juha Jussila'}

def test_v038_registry_queue_and_photo_profiles():
    reg=load('created_players_registry.json'); queue=load('bdfutbol_photo_queue.json')
    rb={int(x['source_id']):x for x in reg['players'] if not x.get('retired_alias_v113')}; qb={int(x['source_id']):x for x in queue['players']}
    assert set(rb)==set(qb)
    for sid in [9496163,9496165,9496149,9496162,9496146,9496153,9496161,9495310,9496147,9496324,9496152,9496144,9496145,9496156,9496159,9496160,9496148,9496150,9496164,9496154,9496151,9496157,9496155,9496158,9496325]:
        assert rb[sid]['duplicate_check']=='exact_name_birthdate_source_profile_gate_v038'
        assert rb[sid].get('bdfutbol_id')
        assert rb[sid].get('photo_status') in {'ready_for_download','bundled_normalized_bdfutbol','bundled'} or str(rb[sid].get('photo_status')).startswith('bundled')
