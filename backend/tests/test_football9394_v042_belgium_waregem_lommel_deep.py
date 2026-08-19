from __future__ import annotations

import pytest
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'

def load(name:str):
    return json.loads((DATA/name).read_text(encoding='utf-8'))


def test_v042_waregem_lommel_gap_closure_and_stage_integrity():
    a=load('historical_profiles_metadata_audit_v042.json')
    b=a['profile_gaps_before']['Belgium']; z=a['profile_gaps_after']['Belgium']
    assert b['missing_birth_date']==160 and z['missing_birth_date']==116
    assert b['missing_international_country_id']==148 and z['missing_international_country_id']==107
    assert b['missing_birth_country_id']==176 and z['missing_birth_country_id']==137
    assert b['missing_height_cm']==250 and z['missing_height_cm']==224
    assert b['missing_weight_kg']==324 and z['missing_weight_kg']==310
    assert a['profiles']['curated_existing']==49
    assert a['profiles']['by_club']=={'Waregem':27,'Lommel':22}
    assert a['gap_closure']['Waregem']['remaining_missing_birth_date']==0
    assert a['gap_closure']['Waregem']['remaining_missing_nationality']==0
    assert a['gap_closure']['Lommel']['remaining_missing_birth_date']==0
    assert a['gap_closure']['Lommel']['remaining_missing_nationality']==0

    stage=load('belgium_1993_94_roster_staging.json')
    for name, expected in [('Waregem',27),('Lommel',22)]:
        club=next(c for c in stage['clubs'] if c['name']==name)
        assert len(club['players'])==expected
        assert all(r.get('resolved_birth_date') for r in club['players'])
        assert all(r.get('bdfutbol_id') for r in club['players'])
        assert all(r.get('resolved_country_id') is not None for r in club['players'])


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Correcciones de rol y estado historico de Waregem y Lommel pendientes."
), strict=True)
def test_v042_key_role_corrections_and_historical_state_policy():
    by={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    # High-value corrections from individual/specialist historical sources.
    assert by[9496215]['primary_role']==0       # Bart Peeters, goalkeeper
    assert by[9496217]['primary_role']==3       # Daniël Scavone, centre-back
    assert by[9496211]['primary_role']==3       # Frank Machiels, centre-back
    assert by[6792]['primary_role']==15         # Frank Berghuis, left winger
    assert by[9496209]['primary_role']==13      # Marc Hendrikx, left midfield
    assert by[9496672]['primary_role']==2       # Ravil Sabitov, left-back
    assert by[9496343]['primary_role']==15      # Hendrie Krüzen, left winger
    assert by[9496329]['primary_role']==6       # Flórián Urbán, defensive midfield

    # USSR != Russia: birthplace-state is not back-projected from later nationality.
    sab=by[9496672]
    assert sab['historical_birth_place_text']=='Moscow (USSR)'
    assert sab['international_country_id']==40
    assert sab.get('birth_country_id') is None

    # 1993 Congolese football identity is Zaire (catalog source id 88).
    for sid in [9496331,9496213,9496203,9496214]:
        assert by[sid]['international_country_id']==88


def test_v042_registry_photo_queue_identity_gate_and_future_russia_policy():
    reg=load('created_players_registry.json'); q=load('bdfutbol_photo_queue.json')
    rb={int(x['source_id']):x for x in reg['players'] if not x.get('retired_alias_v113')}; qb={int(x['source_id']):x for x in q['players']}
    assert set(rb)==set(qb)
    assert len(rb)==len(qb)==len(q['players'])

    audit=load('historical_profiles_metadata_audit_v042.json')
    ids=[int(x['source_id']) for x in audit['profiles']['changes']]
    assert len(ids)==49 and len(set(ids))==49
    shared_prior={9496324,9496325}
    for historical_sid in ids:
        sid=9496672 if historical_sid==9496345 else historical_sid
        if historical_sid == 9496345:
            expected_gate='individual_profile_id_identity_gate_v045'
        else:
            expected_gate='exact_name_birthdate_source_profile_gate_v038' if sid in shared_prior else 'exact_name_birthdate_source_profile_gate_v042'
        assert rb[sid]['duplicate_check']==expected_gate
        assert rb[sid].get('bdfutbol_id') and rb[sid].get('bdfutbol_url')
        assert qb[sid]['photo_status'] in {'ready_for_download','bundled_normalized_bdfutbol'}

    # Shared same-season identities retain the stronger prior specialist profile and both club spells.
    snap={int(x['source_id']):x for x in load('historical_snapshot.json')['players']}
    assert snap[9496324]['primary_role']==8
    assert {x['club'] for x in snap[9496324]['historical_club_spells_1993_94']}=={'Germinal Ekeren','Waregem'}
    assert {x['club'] for x in snap[9496325]['historical_club_spells_1993_94']}=={'Germinal Ekeren','Waregem'}

    # Queue renders historical country label rather than silently modernising it.
    for sid in [9496331,9496213,9496203,9496214]:
        assert qb[sid]['country_name']=='Zaire'

    policy=audit['historical_country_policy']['future_Russia']
    assert 'Russia league remains untouched' in policy
    assert 'USSR must never be auto-mapped to Russia' in policy
    assert audit['next_front']==['RFC Liège','Cercle Brugge','Oostende','KV Mechelen','Gent','Lierse']
