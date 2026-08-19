from __future__ import annotations

import pytest
from pathlib import Path
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'

def load(name): return json.loads((DATA/name).read_text(encoding='utf-8'))

def curated_ids():
    stage=load('turkey_1993_94_roster_staging.json')
    names={'Altay','Ankaragücü','Kayserispor'}
    out={}
    for club in stage['clubs']:
        if club.get('name') in names:
            ids=[int(r['resolved_source_id']) for r in club['players']]
            out[club['name']]=ids
    return out


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de profundidad de clubes turcos incompleto: faltan efectivos, estados historicos explicitos y retratos normalizados."
), strict=True)
def test_v034_three_turkish_clubs_are_deepened_27_each():
    groups=curated_ids()
    assert set(groups)=={'Altay','Ankaragücü','Kayserispor'}
    assert {k:len(v) for k,v in groups.items()}=={'Altay':27,'Ankaragücü':27,'Kayserispor':27}
    # 81 staged club-spells, but Cafer Aydin is one person appearing for both
    # Kayserispor and Ankaragucu during 1993-94.
    assert len(sum(groups.values(),[]))==81
    assert len(set(sum(groups.values(),[])))==80
    assert 9496515 in groups['Kayserispor'] and 9496515 in groups['Ankaragücü']
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    for sid in sum(groups.values(),[]):
        p=snap[sid]
        assert p.get('international_country_id') is not None
        assert p.get('bdfutbol_id')
        assert p.get('historical_birth_place_source_url')
        assert p.get('historical_position_1993_94')
        assert p.get('historical_biography_1993_94')


def test_v034_birth_date_and_nationality_gaps_drop_without_invented_partial_dates():
    audit=load('historical_profiles_metadata_audit_v034.json')
    before=audit['profile_gaps_before']['Turkey']; after=audit['profile_gaps_after']['Turkey']
    assert before['missing_birth_date']==194 and after['missing_birth_date']==124
    assert before['missing_international_country_id']==193 and after['missing_international_country_id']==121
    assert before['missing_birth_country_id']==323 and after['missing_birth_country_id']==259
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    assert snap[9497300]['birth_date'] is None and snap[9497300]['historical_birth_year_only']==1975
    assert snap[9497306]['birth_date'] is None and snap[9497306]['historical_birth_year_only']==1973
    assert 'no se inventa día ni mes' in snap[9497300]['historical_biography_1993_94']
    assert 'no se inventa día ni mes' in snap[9497306]['historical_biography_1993_94']


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de profundidad de clubes turcos incompleto: faltan efectivos, estados historicos explicitos y retratos normalizados."
), strict=True)
def test_v034_known_date_conflicts_and_dissolved_states_are_explicit():
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    gusev=snap[9496498]
    assert gusev['display_name']=='Sergei Gusev'
    assert gusev['historical_full_name']=='Sergei Yevgenovich Gusev'
    assert gusev['birth_date']=='1967-07-01T00:00:00'
    assert gusev['international_country_id']==85 and gusev.get('birth_country_id') is None
    assert 'BDFutbol records 07/07/1967' in gusev['historical_profile_source_note']
    tanri=snap[9497315]
    assert tanri['birth_date']=='1966-05-03T00:00:00' and tanri['international_country_id']==84
    muk=snap[9497305]
    assert muk['international_country_id']==206 and muk.get('birth_country_id') is None
    assert '(USSR)' in muk['historical_birth_place_text']
    shabani=snap[9496538]
    assert shabani['international_country_id']==54 and shabani.get('birth_country_id') is None
    assert '(Yugoslavia)' in shabani['historical_birth_place_text']


def test_v034_exact_roles_only_when_cross_checked_and_broad_roles_stay_uncertain():
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    exact={
        9496489:(3,'Centre Back'),
        9496493:(13,'Left Midfielder'),
        9496494:(1,'Right Back'),
        9496498:(17,'Centre Forward'),
        9496510:(1,'Right Back'),
        9497302:(5,'Libero'),
        9496538:(17,'Centre Forward'),
    }
    for sid,(role,pos) in exact.items():
        p=snap[sid]
        assert p['primary_role']==role and p['historical_position_1993_94']==pos
        assert p['profile_position_precision']=='exact' and p['profile_review_required'] is False
    broad=[9496490,9496495,9496500,9495324,9496507,9496524,9496540]
    for sid in broad:
        p=snap[sid]
        assert p['profile_position_precision']=='broad_only' and p['profile_review_required'] is True
        assert 'exact role unresolved' in p['historical_position_1993_94']
    assert snap[9496490]['historical_biography_1993_94'].startswith('Defensa de Altay')
    assert not snap[9496490]['historical_biography_1993_94'].startswith('Defensa central')


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de profundidad de clubes turcos incompleto: faltan efectivos, estados historicos explicitos y retratos normalizados."
), strict=True)
def test_v034_15_new_bdf_portraits_are_normalized_and_registry_synced():
    audit=load('historical_profiles_metadata_audit_v034.json')
    photo_audit=load('bdfutbol_photo_normalization_v034_altay_ank_kay.json')
    assert audit['photos']['new_normalized_bdfutbol_portraits']==15
    assert audit['photos']['total_bundled_normalized_bdfutbol']==69
    assert len(photo_audit['portraits'])==15
    reg=load('created_players_registry.json')['players']; queue=load('bdfutbol_photo_queue.json')['players']
    r={int(x['source_id']):x for x in reg if not x.get('retired_alias_v113')}; q={int(x['source_id']):x for x in queue}
    assert len(r)==len(q)>=2080 and set(r)==set(q)
    for row in photo_audit['portraits']:
        historical_sid=int(row['source_id'])
        sid=9496515 if historical_sid==9497314 else historical_sid
        asset=ROOT/row['asset']
        assert r[sid]['photo_status']==q[sid]['photo_status']=='bundled_normalized_bdfutbol'
        assert r[sid]['photo_filename']==q[sid]['photo_filename']==f'{sid}.jpg'
        with Image.open(asset) as im:
            assert im.size==(40,55) and im.mode=='RGB' and im.format=='JPEG'


def test_v034_audit_counts_and_attribute_comparables_are_consistent():
    audit=load('historical_profiles_metadata_audit_v034.json')
    assert audit['status']=='pass'
    assert audit['profiles']['curated_this_batch']==81
    assert audit['profiles']['by_club']=={'Altay':27,'Ankaragücü':27,'Kayserispor':27}
    assert audit['profiles']['exact_specialist_roles']==31
    assert audit['profiles']['broad_only_exact_role_unresolved']==50
    assert audit['profiles']['year_only_birth_records']==2
    assert audit['profiles']['role_corrections_this_batch']==48
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    for c in audit['profiles']['changes']:
        if not c['role_changed']:
            continue
        p=snap[int(c['source_id'])]
        assert p['attribute_source']=='fixed_source_comparable_role_correction_0.34'
        assert len(p['attribute_comparable_source_ids'])==2
        for cid in p['attribute_comparable_source_ids']:
            assert int(cid) in snap and snap[int(cid)]['broad_position']==p['broad_position']
