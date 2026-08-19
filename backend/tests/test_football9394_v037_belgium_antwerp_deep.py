from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'

def load(name:str): return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v037_antwerp_source_union_and_gaps():
    audit=load('historical_profiles_metadata_audit_v037.json')
    before=audit['profile_gaps_before']['Belgium']; after=audit['profile_gaps_after']['Belgium']
    assert before['active_players']==413
    assert after['active_players']==414
    assert after['missing_birth_date']==253
    assert after['missing_international_country_id']==233
    assert after['missing_birth_country_id']==258
    assert after['missing_height_cm']==302
    assert after['missing_weight_kg']==353
    assert audit['profiles']['curated_existing']==24
    assert audit['profiles']['new_historical_identities']==1
    assert audit['source_roster_union']['royal_antwerp_stage_rows_after']==25
    assert audit['source_roster_union']['source_visible_without_bdf_league_row']==[9498014]

def test_v037_antwerp_profiles_and_role_repairs():
    snap=load('historical_snapshot.json'); by={int(p['source_id']):p for p in snap['players']}
    assert by[9496303]['display_name']=='Rudy Taeymans'
    assert by[9496303]['birth_date'].startswith('1967-02-08') and by[9496303]['primary_role']==2
    assert by[9496287]['primary_role']==5
    assert by[9496293]['primary_role']==1
    assert by[9496301]['primary_role']==2
    assert by[9496288]['birth_date'].startswith('1964-06-23') and by[9496288]['primary_role']==17
    assert by[9496306]['birth_date'].startswith('1961-11-21')
    assert by[9496298]['international_country_id']==88 and by[9496298].get('birth_country_id') is None
    assert by[9496295]['birth_date'].startswith('1967-08-12') and by[9496295]['primary_role']==1
    assert by[9496299]['international_country_id']==56 and by[9496299]['primary_role']==8
    assert by[9496286]['primary_role']==17 and by[9496286]['height_cm']==185
    assert by[9496292]['international_country_id']==75 and by[9496292].get('birth_country_id') is None
    assert by[9496290]['primary_role']==2 and by[9496290]['profile_review_required'] is True

def test_v037_stojanovic_added_without_fake_league_stats_and_muzsnay_held_out():
    snap=load('historical_snapshot.json'); stage=load('belgium_1993_94_roster_staging.json'); by={int(p['source_id']):p for p in snap['players']}
    st=by[9498014]
    assert st['display_name']=='Stevan Stojanović'
    assert st['birth_date'].startswith('1964-10-29')
    assert st['international_country_id']==75 and st['primary_role']==0
    club=next(c for c in stage['clubs'] if c['name']=='Royal Antwerp')
    row=next(r for r in club['players'] if int(r.get('resolved_source_id') or -1)==9498014)
    assert row['source_roster_member'] is True and row['league_row_absent'] is True
    assert row['appearances']==row['starts']==row['minutes']==row['goals']==0
    assert 'no se inventan partidos ni minutos' in st['historical_biography_1993_94']
    assert not any((p.get('display_name') or '').casefold()=='zsolt muzsnay' for p in snap['players'] if p.get('team_id')==1032)
    conflicts=load('belgium_source_conflicts_v037.json')['conflicts']
    assert any(x['name']=='Zsolt Muzsnay' and x['decision']=='not_added' for x in conflicts)

def test_v037_mauritius_is_explicit_gap_not_invented_country_id():
    snap=load('historical_snapshot.json'); by={int(p['source_id']):p for p in snap['players']}
    vincent=by[9496307]
    assert vincent['birth_date'].startswith('1966-11-18')
    assert vincent.get('international_country_id') is None
    assert vincent.get('historical_nationality_text')=='Mauritius'
    assert vincent.get('historical_nationality_id_status')=='unresolved_country_id_catalogue'
    assert vincent['height_cm']==170 and vincent['weight_kg']==62

def test_v037_bdf_profile_links_and_registry_queue_integrity():
    reg=load('created_players_registry.json'); queue=load('bdfutbol_photo_queue.json')
    rb={int(x['source_id']):x for x in reg['players'] if not x.get('retired_alias_v113')}; qb={int(x['source_id']):x for x in queue['players']}
    assert set(rb)==set(qb)
    for sid in [9496302,9494210,9496303,9496287,9496291,9496293,9496301,9496297,9496300,9495304,9496289,9496304,9496288,9496306,9496298,9496295,9496299,9496286,9496307,9496294,9496292,9496296,9496305,9496290]:
        assert rb[sid].get('bdfutbol_id')
        assert rb[sid].get('photo_status') in {'ready_for_download','bundled_normalized_bdfutbol','bundled'} or str(rb[sid].get('photo_status')).startswith('bundled')
    assert rb[9498014]['display_name']=='Stevan Stojanović'
