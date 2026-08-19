from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'data'/'football9394'
def load(name:str): return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v039_beveren_gap_reduction_and_stage_integrity():
    a=load('historical_profiles_metadata_audit_v039.json'); b=a['profile_gaps_before']['Belgium']; z=a['profile_gaps_after']['Belgium']
    assert b['missing_birth_date']==229 and z['missing_birth_date']==207
    assert b['missing_international_country_id']==213 and z['missing_international_country_id']==191
    assert b['missing_birth_country_id']==238 and z['missing_birth_country_id']==216
    assert z['missing_height_cm']==274 and z['missing_weight_kg']==338
    assert a['profiles']['curated_existing']==23
    stage=load('belgium_1993_94_roster_staging.json'); club=next(c for c in stage['clubs'] if c['name']=='Beveren')
    assert len(club['players'])==23 and all(r.get('resolved_birth_date') for r in club['players']) and all(r.get('bdfutbol_id') for r in club['players'])

def test_v039_beveren_roles_and_historical_states():
    by={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    expected={9496017:0,9496022:3,9496011:2,9494182:3,9496013:14,9496026:17,9496028:0,9496032:5,9496024:17,9496023:1,9496018:17,9496016:8,9496014:2}
    for sid,r in expected.items(): assert by[sid]['primary_role']==r
    assert by[9496018]['international_country_id']==88 and by[9496018]['birth_country_id']==88
    assert by[9496018]['historical_birth_place_text']=='Kinshasa (Zaire)'
    assert by[9496016]['profile_nationality_country_ids']==[52,17]
    assert by[9496032]['profile_review_required'] is True and 'sweeper' in by[9496032]['historical_profile_source_note'].lower()

def test_v039_registry_queue_photo_links():
    reg=load('created_players_registry.json'); q=load('bdfutbol_photo_queue.json'); rb={int(x['source_id']):x for x in reg['players'] if not x.get('retired_alias_v113')}; qb={int(x['source_id']):x for x in q['players']}
    assert set(rb)==set(qb)
    ids=[9496017,9496022,9496011,9494182,9496021,9496013,9496025,9496030,9496029,9496027,9496026,9496028,9496032,9496024,9496012,9496015,9496023,9496020,9496018,9496031,9496016,9496019,9496014]
    for sid in ids:
        assert rb[sid]['duplicate_check']=='exact_name_birthdate_source_profile_gate_v039'
        assert rb[sid].get('bdfutbol_id') and rb[sid].get('bdfutbol_url')
