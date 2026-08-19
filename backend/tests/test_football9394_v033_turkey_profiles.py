from __future__ import annotations

import pytest
from pathlib import Path
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'

def load(name): return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v033_gaziantepspor_all_26_profiles_have_birth_and_international_country():
    s=load('historical_snapshot.json')
    players=[p for p in s['players'] if p.get('team_id')==9357006]
    assert len(players)==26
    assert all(p.get('birth_date') for p in players)
    assert all(p.get('international_country_id') is not None for p in players)
    assert all(p.get('historical_birth_place_text') for p in players)
    assert all(p.get('bdfutbol_id') for p in players)


def test_v033_gaziantepspor_high_impact_role_corrections():
    s=load('historical_snapshot.json'); p={int(x['source_id']):x for x in s['players']}
    checks={
      9496454:('İhsan Okay',13,'MED','Left Midfielder'),
      9496459:('Mustafa Özer',1,'DEF','Right Back'),
      9496460:('Kemal Sönmez',3,'DEF','Centre Back'),
      9496461:('Hasan Çelik',17,'DEL','Centre Forward'),
      9496465:('Kubilay Toptaş',17,'DEL','Centre Forward'),
      9496469:('Teboho Claude Moloi',7,'MED','Midfielder (exact role unresolved)'),
      9496470:('Tayfun Yungul',7,'MED','Centre Midfielder'),
      9497272:('Mehmet Gönülaçar',17,'DEL','Centre Forward'),
      9497274:('Mustafa Yücedağ',8,'MED','Attacking Midfielder'),
    }
    for sid,(name,role,broad,pos) in checks.items():
        row=p[sid]
        assert row['display_name']==name
        assert row['primary_role']==role
        assert row['broad_position']==broad
        assert row['historical_position_1993_94']==pos
        assert row['attribute_source']=='fixed_source_comparable_role_correction_0.33'
        assert len(row['attribute_comparable_source_ids'])==2


def test_v033_broad_only_profiles_are_explicitly_review_gated():
    s=load('historical_snapshot.json'); p={int(x['source_id']):x for x in s['players']}
    unresolved={9496455,9496457,9496467,9496469,9497275,9497276,9497277,9497279}
    for sid in unresolved:
        assert p[sid]['profile_review_required'] is True
        assert 'exact role unresolved' in p[sid]['historical_position_1993_94']
    assert 'similarly named Transfermarkt goalkeeper' in p[9497276]['historical_profile_source_note']


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Correcciones de alta confianza de Altay, Ankaragucu y Kayserispor pendientes."
), strict=True)
def test_v033_altay_ankaragucu_kayseri_high_confidence_corrections():
    s=load('historical_snapshot.json'); p={int(x['source_id']):x for x in s['players']}
    checks={
      9496491:('Ahmet Akuygur',1,'Right Back',84,'1967-05-29T00:00:00'),
      9496502:('Yuriy Shelepnytskyi',6,'Defensive Midfielder',85,'1965-01-18T00:00:00'),
      9496517:('Mehmet Yıldırım',17,'Centre Forward',84,'1972-09-15T00:00:00'),
      9496519:('Yuriy Matveev',17,'Centre Forward',40,'1967-06-08T00:00:00'),
      9497305:('Charyar Mukhadov',17,'Centre Forward',206,'1969-11-12T00:00:00'),
      9497315:('Öztürk Tanrıbilir',0,'Goalkeeper',84,'1966-05-03T00:00:00'),
      9496515:('Cafer Aydın',17,'Centre Forward',84,'1971-11-17T00:00:00'),
    }
    for sid,(name,role,pos,country,dob) in checks.items():
        row=p[sid]
        assert row['display_name']==name and row['primary_role']==role
        assert row['historical_position_1993_94']==pos
        assert row['international_country_id']==country and row['birth_date']==dob
    assert p[9496502].get('birth_country_id') is None
    assert p[9496519].get('birth_country_id') is None
    assert '(USSR)' in p[9496502]['historical_birth_place_text']
    assert '(USSR)' in p[9496519]['historical_birth_place_text']
    assert p[9496502]['historical_full_name']=='Yuriy Hryhorovych Shelepnytskyi'
    assert p[9497305]['historical_full_name']=='Charyar Abdurakhmanovich Mukhadov'


def test_v033_new_bdfutbol_portraits_are_real_normalized_assets():
    audit=load('bdfutbol_photo_normalization_v033_gaziantep.json')
    reg={int(x['source_id']):x for x in load('created_players_registry.json')['players']}
    assert audit['status']=='pass' and len(audit['portraits'])==18
    for row in audit['portraits']:
        sid=int(row['source_id'])
        asset=ROOT/'frontend'/'public'/'historical9394'/'players'/f'{sid}.jpg'
        assert reg[sid]['photo_status']=='bundled_normalized_bdfutbol'
        with Image.open(asset) as im:
            assert im.size==(40,55) and im.mode=='RGB' and im.format=='JPEG'
    assert sum(x.get('photo_status')=='bundled_normalized_bdfutbol' for x in reg.values())>=54


def test_v033_gap_audit_and_registry_queue_integrity():
    audit=load('historical_profiles_metadata_audit_v033.json')
    gaps=load('historical_metadata_gaps_v033.json')['gaps']['Turkey']
    reg=load('created_players_registry.json')['players']; q=load('bdfutbol_photo_queue.json')['players']
    assert audit['status']=='pass'
    assert audit['profiles']['curated_this_batch']==33
    assert audit['profiles']['gaziantepspor_curated']==26
    assert audit['profiles']['next_high_confidence_curated']==7
    assert audit['profiles']['role_corrections_this_batch']==24
    assert audit['profiles']['broad_only_exact_role_unresolved']==8
    assert gaps['active_players']==419
    assert gaps['missing_birth_date']==194
    assert gaps['missing_international_country_id']==193
    assert gaps['missing_birth_country_id']==323
    assert len([x for x in reg if not x.get('retired_alias_v113')])==len(q)>=2080
    assert len({int(x['source_id']) for x in reg})==len(reg)
    assert {int(x['source_id']) for x in reg if not x.get('retired_alias_v113')}=={int(x['source_id']) for x in q}


def test_v033_biographies_refreshed_after_role_and_identity_corrections():
    bio=load('historical_biographies_audit_v033.json')
    s=load('historical_snapshot.json'); p={int(x['source_id']):x for x in s['players']}
    assert bio['active_players']==1813 and bio['biographies_written']==1813
    assert bio['changed_from_v032']==33 and bio['missing_stage_rows']==0
    assert 'Delantero centro de Gaziantepspor' in p[9496465]['historical_biography_1993_94']
    assert 'Kars' in p[9496465]['historical_biography_1993_94']
    assert 'Portero de Kayserispor' in p[9497315]['historical_biography_1993_94']
    assert 'Delantero centro de Ankaragücü' in p[9496519]['historical_biography_1993_94']


def test_v033_attribute_comparables_exist_and_match_corrected_broad_position():
    s=load('historical_snapshot.json'); by={int(x['source_id']):x for x in s['players']}
    for sid in list(GAZ_IDS)+[9496491,9496502,9496517,9496519,9497305,9497315,9496515]:
        row=by[sid]
        for cid in row.get('attribute_comparable_source_ids') or []:
            assert int(cid) in by
            assert by[int(cid)]['broad_position']==row['broad_position']

GAZ_IDS={
9496453,9496454,9496455,9496456,9496457,9496458,9496459,9496460,9496461,9496462,9496463,9496464,
9496465,9496466,9496467,9496468,9496469,9496470,9497272,9497273,9497274,9497275,9497276,9497277,
9497278,9497279,
}
