from __future__ import annotations
from pathlib import Path
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'

def load(name): return json.loads((DATA/name).read_text(encoding='utf-8'))

def curated_ids():
    stage=load('turkey_1993_94_roster_staging.json')
    names={'Zeytinburnuspor','Karabükspor','Karşıyaka','Sarıyer'}
    out={}
    for club in stage['clubs']:
        if club.get('name') in names:
            out[club['name']]=[int(r['resolved_source_id']) for r in club['players']]
    return out


def test_v035_four_turkish_clubs_are_deepened_with_full_staged_rosters():
    groups=curated_ids()
    assert set(groups)=={'Zeytinburnuspor','Karabükspor','Karşıyaka','Sarıyer'}
    assert {k:len(v) for k,v in groups.items()}=={'Zeytinburnuspor':26,'Karabükspor':27,'Karşıyaka':25,'Sarıyer':24}
    ids=sum(groups.values(),[])
    assert len(ids)==102 and len(set(ids))==102
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    for sid in ids:
        p=snap[sid]
        assert p.get('international_country_id') is not None
        assert p.get('bdfutbol_id')
        assert p.get('historical_birth_place_source_url')
        assert p.get('historical_position_1993_94')
        assert p.get('historical_biography_1993_94')


def test_v035_turkey_identity_gaps_collapse_without_inventing_partial_dates():
    audit=load('historical_profiles_metadata_audit_v035.json')
    before=audit['profile_gaps_before']['Turkey']; after=audit['profile_gaps_after']['Turkey']
    assert before['missing_birth_date']==124 and after['missing_birth_date']==23
    assert before['missing_international_country_id']==121 and after['missing_international_country_id']==19
    assert before['missing_birth_country_id']==259 and after['missing_birth_country_id']==165
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    ece=snap[9496557]
    assert ece['birth_date'] is None and ece['historical_birth_year_only']==1964
    assert 'no se inventa día ni mes' in ece['historical_biography_1993_94']


def test_v035_historical_states_dual_nationalities_and_aliases_are_preserved():
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    ibra=snap[9496541]
    assert ibra['display_name']=='Miralem Ibrahimović' and ibra['international_country_id']==20
    assert ibra.get('birth_country_id') is None and '(Yugoslavia)' in ibra['historical_birth_place_text']
    cvikl=snap[9496556]
    assert cvikl['international_country_id']==37 and cvikl.get('birth_country_id') is None
    ziya=snap[9496585]
    assert ziya['display_name']=='Ziya Yıldız' and ziya['profile_nationality_country_ids']==[20,84]
    assert ziya.get('birth_country_id') is None and '(Yugoslavia)' in ziya['historical_birth_place_text']
    gol=snap[9497337]
    assert gol['profile_nationality_country_ids']==[20,75] and gol.get('birth_country_id') is None
    yar=snap[9496597]
    assert yar['birth_date']=='1962-08-17T00:00:00' and yar['profile_nationality_country_ids']==[85,132]
    assert yar.get('birth_country_id') is None and '(USSR)' in yar['historical_birth_place_text']
    metin=snap[9496595]
    assert metin['display_name']=='Metin Mert' and metin['profile_nationality_country_ids']==[84,4]
    sinan=snap[9496610]
    assert sinan['display_name']=='Sinan Engin'
    salihi=snap[9497345]
    assert salihi['international_country_id']==8 and salihi.get('birth_country_id') is None


def test_v035_exact_roles_are_source_backed_and_broad_positions_remain_unresolved():
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    exact={9496561:(2,'Left Back'),9496597:(3,'Centre Back'),9496541:(0,'Goalkeeper'),9496593:(0,'Goalkeeper'),9496611:(0,'Goalkeeper')}
    for sid,(role,pos) in exact.items():
        p=snap[sid]
        assert p['primary_role']==role and p['historical_position_1993_94']==pos
        assert p['profile_position_precision']=='exact' and p['profile_review_required'] is False
    broad=[9496542,9496547,9496560,9496571,9496585,9496591,9496608,9497345]
    for sid in broad:
        p=snap[sid]
        assert p['profile_position_precision']=='broad_only' and p['profile_review_required'] is True
        assert 'exact role unresolved' in p['historical_position_1993_94']
    assert snap[9496560]['historical_biography_1993_94'].startswith('Defensa de Karabükspor')
    assert not snap[9496560]['historical_biography_1993_94'].startswith('Defensa central')


def test_v035_twenty_new_bdf_portraits_are_normalized_and_synced():
    audit=load('historical_profiles_metadata_audit_v035.json')
    photo_audit=load('bdfutbol_photo_normalization_v035_zeytin_karabuk_karsiyaka_sariyer.json')
    assert audit['photos']['new_normalized_bdfutbol_portraits']==20
    assert audit['photos']['total_bundled_normalized_bdfutbol']==89
    assert len(photo_audit['portraits'])==20
    reg=load('created_players_registry.json')['players']; queue=load('bdfutbol_photo_queue.json')['players']
    r={int(x['source_id']):x for x in reg if not x.get('retired_alias_v113')}; q={int(x['source_id']):x for x in queue}
    assert len(r)==len(q)>=2080 and set(r)==set(q)
    for row in photo_audit['portraits']:
        sid=int(row['source_id']); asset=ROOT/row['asset']
        assert r[sid]['photo_status']==q[sid]['photo_status']=='bundled_normalized_bdfutbol'
        assert r[sid]['photo_filename']==q[sid]['photo_filename']==f'{sid}.jpg'
        with Image.open(asset) as im:
            assert im.size==(40,55) and im.mode=='RGB' and im.format=='JPEG'


def test_v035_audit_counts_and_role_corrections_are_consistent():
    audit=load('historical_profiles_metadata_audit_v035.json')
    assert audit['status']=='pass'
    assert audit['profiles']['curated_this_batch']==102
    assert audit['profiles']['by_club']=={'Zeytinburnuspor':26,'Karabükspor':27,'Karşıyaka':25,'Sarıyer':24}
    assert audit['profiles']['exact_specialist_roles']==14
    assert audit['profiles']['broad_only_exact_role_unresolved']==88
    assert audit['profiles']['year_only_birth_records']==1
    assert audit['profiles']['role_corrections_this_batch']==69
    assert audit['biographies']=={'profiles_considered':102,'biographies_changed':102,'missing_stage_rows':0}
    # Historical v0.35 audit counts are preserved as provenance; current v1.1.3
    # identity integrity is asserted against the active registry/queue instead.
    reg=load('created_players_registry.json')['players']; queue=load('bdfutbol_photo_queue.json')['players']
    active=[x for x in reg if not x.get('retired_alias_v113')]
    assert len(active)==len(queue)>=2080
    assert {int(x['source_id']) for x in active}=={int(x['source_id']) for x in queue}
    snap={int(p['source_id']):p for p in load('historical_snapshot.json')['players']}
    for c in audit['profiles']['changes']:
        if not c['role_changed']:
            continue
        p=snap[int(c['source_id'])]
        assert p['attribute_source']=='fixed_source_comparable_role_correction_0.35'
        assert len(p['attribute_comparable_source_ids'])==2
        for cid in p['attribute_comparable_source_ids']:
            assert int(cid) in snap and snap[int(cid)]['broad_position']==p['broad_position']
