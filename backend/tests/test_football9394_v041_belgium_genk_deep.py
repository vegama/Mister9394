from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'data'/'football9394'
def load(name:str): return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v041_genk_gap_reduction_and_stage_integrity():
    a=load('historical_profiles_metadata_audit_v041.json'); b=a['profile_gaps_before']['Belgium']; z=a['profile_gaps_after']['Belgium']
    assert b['missing_birth_date']==183 and z['missing_birth_date']==160
    assert b['missing_international_country_id']==169 and z['missing_international_country_id']==148
    assert b['missing_birth_country_id']==194 and z['missing_birth_country_id']==176
    assert z['missing_height_cm']==250 and z['missing_weight_kg']==324
    assert a['profiles']['curated_existing']==23 and a['profiles']['role_corrections']==15
    stage=load('belgium_1993_94_roster_staging.json'); club=next(c for c in stage['clubs'] if c['name']=='Genk')
    assert len(club['players'])==23
    assert all(r.get('resolved_birth_date') for r in club['players'])
    assert all(r.get('bdfutbol_id') for r in club['players'])
    assert all(r.get('resolved_country_id') is not None for r in club['players'])

def test_v041_genk_roles_and_historical_state_policy():
    by={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    assert by[9496109]['primary_role']==0                    # Gaspercic
    assert by[9496118]['primary_role']==0                    # Thijs
    assert by[9496107]['primary_role']==0                    # Doumen
    assert by[9496111]['primary_role']==5                    # Katana sweeper
    assert by[9496114]['primary_role']==2                    # Oyen left-back
    assert by[9496121]['primary_role']==2                    # Vangronsveld left-back
    for sid in [9496102,9496108,9496119,9496115]:
        assert by[sid]['broad_position']=='MED' and by[sid]['profile_review_required'] is True
    for sid in [9496116,9496113]:
        assert by[sid]['broad_position']=='DEL' and by[sid]['profile_review_required'] is True
    # Modern successor-state labels are not back-projected onto Yugoslav birthplaces.
    for sid,place,nat in [
        (9496111,'Sarajevo (Yugoslavia)',20),
        (9496103,'Split (Yugoslavia)',31),
        (9496112,'Gradačac (Yugoslavia)',20),
    ]:
        assert by[sid]['historical_birth_place_text']==place
        assert by[sid]['international_country_id']==nat
        assert by[sid].get('birth_country_id') is None

def test_v041_genk_registry_queue_and_russia_policy_recorded():
    reg=load('created_players_registry.json'); q=load('bdfutbol_photo_queue.json')
    rb={int(x['source_id']):x for x in reg['players'] if not x.get('retired_alias_v113')}; qb={int(x['source_id']):x for x in q['players']}
    assert set(rb)==set(qb)
    ids=[9496109,9496122,9496111,9496106,9496102,9496117,9496105,9496120,9496100,9496110,9496104,9496107,9496114,9496101,9496103,9496108,9496118,9496119,9496116,9496121,9496112,9496113,9496115]
    for sid in ids:
        assert rb[sid]['duplicate_check']=='exact_name_birthdate_source_profile_gate_v041'
        assert rb[sid].get('bdfutbol_id') and rb[sid].get('bdfutbol_url')
        assert qb[sid]['photo_status'] in {'ready_for_download','bundled_normalized_bdfutbol'}
    policy=load('historical_profiles_metadata_audit_v041.json')['historical_country_policy']['future_Russia']
    assert 'Russia remains untouched' in policy and 'USSR must never be auto-mapped to Russia' in policy
