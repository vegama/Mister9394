from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'data'/'football9394'
def load(name:str): return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v040_molenbeek_gap_reduction_and_stage_integrity():
    a=load('historical_profiles_metadata_audit_v040.json'); b=a['profile_gaps_before']['Belgium']; z=a['profile_gaps_after']['Belgium']
    assert b['missing_birth_date']==207 and z['missing_birth_date']==183
    assert b['missing_international_country_id']==191 and z['missing_international_country_id']==169
    assert b['missing_birth_country_id']==216 and z['missing_birth_country_id']==194
    assert z['missing_height_cm']==262 and z['missing_weight_kg']==330
    assert a['profiles']['curated_existing']==25 and a['profiles']['role_corrections']==18
    stage=load('belgium_1993_94_roster_staging.json'); club=next(c for c in stage['clubs'] if c['name']=='Molenbeek')
    assert len(club['players'])==25 and all(r.get('resolved_birth_date') for r in club['players']) and all(r.get('bdfutbol_id') for r in club['players'])
    names=[r['resolved_display_name'] for r in club['players']]
    assert 'Steve Laeremans' in names and 'Michael Laeremans' in names

def test_v040_molenbeek_roles_identities_and_source_conflicts():
    by={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    expected={9496240:0,9496233:1,9496241:2,9496237:1,9496244:9,9496225:6,9496230:7,9496245:17,9496246:8,9496242:8,9496229:0,9496235:5,9496232:9,9496238:7,9496227:17,9496224:17}
    for sid,r in expected.items(): assert by[sid]['primary_role']==r
    assert by[9496245]['international_country_id']==78 and by[9496245]['birth_country_id']==78
    assert by[9496245]['historical_birth_place_text']=='Cape Town'
    assert 'rio de janeiro' in by[9496245]['historical_profile_source_note'].lower()
    assert by[9496242]['profile_nationality_country_ids']==[62,17]
    assert by[9496242]['international_country_id']==62 and by[9496242]['secondary_nationality_country_id']==17
    assert by[9496238]['profile_review_required'] is True and by[9496238]['broad_position']=='MED'
    assert by[9496227]['broad_position']=='DEL' and by[9496224]['broad_position']=='DEL'

def test_v040_registry_queue_photo_links_and_identity_gate():
    reg=load('created_players_registry.json'); q=load('bdfutbol_photo_queue.json'); rb={int(x['source_id']):x for x in reg['players'] if not x.get('retired_alias_v113')}; qb={int(x['source_id']):x for x in q['players']}
    assert set(rb)==set(qb)
    ids=[9496240,9496233,9496241,9496237,9496244,9496225,9496243,9496230,9496245,9496246,9496242,9496229,9496235,9496326,9496228,9496239,9496232,9496231,9496238,9496234,9494180,9496227,9496226,9496224,9496236]
    for sid in ids:
        assert rb[sid]['duplicate_check']=='exact_name_birthdate_source_profile_gate_v040'
        assert rb[sid].get('bdfutbol_id') and rb[sid].get('bdfutbol_url')
