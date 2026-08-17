from __future__ import annotations
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'

def load(name): return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v032_all_reconstructed_league_venues_are_historical_source_backed():
    s=load('historical_snapshot.json')
    target={930015,930047,930052,930057}
    teams=[t for t in s['teams'] if t.get('league_id') in target]
    assert teams
    assert all(t.get('stadium_id') is not None for t in teams)
    assert not [t for t in teams if t.get('venue_source_status')=='unresolved_historical_1993_94']

def test_v032_belgium_and_turkey_stadium_names():
    s=load('historical_snapshot.json'); c=load('historical_source_catalog.json')
    stadiums={int(x['source_id']):x for x in c['stadiums']}; teams={int(t['source_id']):t for t in s['teams']}
    expected={
      9352001:'Stade du Pairay',9352002:'Freethielstadion',9352003:'Veltwijckpark',9352004:'Stedelijk Sportstadion',9352005:'Stade Vélodrome Oscar Flesch',9352006:'Stade Edmond Machtens',
      9357001:'Fenerbahçe Stadı',9357002:'Hüseyin Avni Aker Stadı',9357003:'19 Mayıs Stadı',9357004:'İsmetpaşa Stadyumu',9357005:'19 Mayıs Stadı',9357006:'Kamil Ocak Stadı',9357007:'Atatürk Stadı',9357008:'Atatürk Stadı',9357009:'19 Mayıs Stadı',9357010:'Atatürk Stadı',9357011:'Zeytinburnu Stadı',9357012:'Yenişehir Stadı',9357013:'Atatürk Stadı',9357014:'Yusuf Ziya Öniş Stadyumu'}
    for tid,name in expected.items():
        row=stadiums[int(teams[tid]['stadium_id'])]
        assert row['name']==name
        assert row['capacity'] is None and row['width_m'] is None and row['length_m'] is None
        assert row['physical_parameters_status']=='not_inferred_from_modern_values'

def test_v032_turkey_and_russia_referee_pools_are_complete_by_match_assignments():
    s=load('historical_snapshot.json'); c=load('historical_source_catalog.json')
    refs=c['referees']
    tur=[r for r in refs if r.get('league_id')==930057]
    rus=[r for r in refs if r.get('league_id')==930015]
    assert len(tur)==34 and sum(int(r.get('appearances') or 0) for r in tur)==240
    assert len(rus)==33 and sum(int(r.get('appearances') or 0) for r in rus)==306
    assert all(r.get('birth_country_id') is None for r in tur+rus)
    leagues={int(l['source_id']):l for l in s['leagues']}
    assert leagues[930057]['source_rule_hints']['referee_pool_size']==34
    assert leagues[930015]['source_rule_hints']['referee_pool_size']==33

def test_v032_fenerbahce_profile_corrections_are_materialised():
    s=load('historical_snapshot.json'); p={int(x['source_id']):x for x in s['players']}
    checks={
      9495343:('İlker Yağcıoğlu',1,'Right Back',84),9496365:('Tayfur Havutçu',6,'Defensive Midfielder',84),
      9495352:('Bülent Uygun',8,'Attacking Midfielder',84),9497233:('Hakan Tecimer',12,'Right Winger',84),
      9496367:('Brian Steen Nielsen',13,'Left Midfielder',33),9496364:('Uche Okechukwu',3,'Centre Back',59),
    }
    for sid,(name,role,pos,country) in checks.items():
        row=p[sid]; assert row['display_name']==name; assert row['primary_role']==role; assert row['historical_position_1993_94']==pos; assert row['international_country_id']==country
        assert row['historical_profile_source_url'].endswith('/saison_id/1993/plus/1')
    assert p[9497236]['display_name']=='Kerem Şenel' and p[9497236]['profile_review_required'] is True

def test_v032_samsunspor_profile_corrections_are_materialised():
    s=load('historical_snapshot.json'); p={int(x['source_id']):x for x in s['players']}
    checks={
      9496415:('Erol İlhan',0,'Goalkeeper',84),9496402:('Ercan Koloğlu',5,'Libero',84),
      9496405:('Daniel Timofte',8,'Attacking Midfielder',72),9496414:('Marius Cheregi',6,'Defensive Midfielder',72),
      9497250:('Ahmet Yıldırım',6,'Defensive Midfielder',84),9496411:('İsa Turan',2,'Left Back',84),
    }
    for sid,(name,role,pos,country) in checks.items():
        row=p[sid]; assert row['display_name']==name; assert row['primary_role']==role; assert row['historical_position_1993_94']==pos; assert row['international_country_id']==country
        assert 'samsunspor/kader/verein/152/saison_id/1993/plus/1' in row['historical_profile_source_url']
    assert p[9496404]['profile_review_required'] is True
    assert 'exact role unresolved' in p[9496404]['historical_position_1993_94']

def test_v032_registry_queue_and_gap_audit_are_consistent():
    reg=load('created_players_registry.json'); q=load('bdfutbol_photo_queue.json'); gaps=load('historical_metadata_gaps_v032.json'); audit=load('historical_profiles_metadata_audit_v032.json')
    assert {int(x['source_id']) for x in reg['players']}=={int(x['source_id']) for x in q['players']}
    assert gaps['unresolved_historical_venue_team_ids']==[]
    assert gaps['unresolved_historical_referee_pool_league_ids']==[]
    assert gaps['profile_gaps']['Turkey']['missing_birth_date']==227
    assert gaps['profile_gaps']['Turkey']['missing_international_country_id']==226
    assert gaps['profile_gaps']['Turkey']['missing_birth_country_id']==354
    assert audit['profiles']['curated_total_v032']==162
    assert audit['profiles']['role_corrections_total_v032']==96


def test_v032_trabzonspor_profile_corrections_are_materialised():
    s=load('historical_snapshot.json'); p={int(x['source_id']):x for x in s['players']}
    checks={
      9496376:('Hamdi Aslan',5,'Libero',84),9496378:('Orhan Çıkırıkçı',13,'Left Midfielder',84),
      9495333:('Ünal Karaman',8,'Attacking Midfielder',84),9496384:('Orhan Kaynak',17,'Centre Forward',84),
      9497237:('Yuriy Shelepnytskyi',6,'Defensive Midfielder',85),9497241:('Ülken Durak',2,'Left Back',84),
      9497242:('Sergiy Gusev',17,'Centre Forward',85),
    }
    for sid,(name,role,pos,country) in checks.items():
        row=p[sid]; assert row['display_name']==name; assert row['primary_role']==role; assert row['historical_position_1993_94']==pos; assert row['international_country_id']==country
        assert 'trabzonspor/kader/verein/449/saison_id/1993/plus/1' in row['historical_profile_source_url']


def test_v032_bdfutbol_portraits_and_birthplaces_are_materialised():
    from PIL import Image
    s=load('historical_snapshot.json'); reg=load('created_players_registry.json'); bio=load('historical_biographies_audit_v032.json')
    players={int(x['source_id']):x for x in s['players']}; registry={int(x['source_id']):x for x in reg['players']}
    expected={
      9495349:('Arsin (Trabzon)',84,'98308'),
      9496380:('Tbilisi',104,'4135'),
      9496385:('Tbilisi',104,'90266'),
      9495332:('Adapazarı (Sakarya)',84,'45597'),
      9495351:('Geyve (Sakarya)',84,'43562'),
      9496364:('Lagos',59,'55567'),
      9497231:('Nazilli',84,'45599'),
      9495352:('Sakarya',84,'51173'),
      9496365:('Hesse',4,'55596'),
      9496366:('Istanbul (Istanbul)',84,'45593'),
      9496374:('Bursa (Bursa)',84,'42307'),
      9496479:('Vejlby',33,'89072'),
      9496480:('Kristiansund',60,'91650'),
      9496437:('Zonguldak',84,'46413'),
      9496438:('Sakarya',84,'57628'),
      9496441:('Soweto',78,'55569'),
      9496444:('Lubumbashi',88,'702421'),
      9498004:('Kocaeli (Kocaeli)',84,'1175393'),
    }
    for sid,(place,birth_country,bdf_id) in expected.items():
        p=players[sid]; r=registry[sid]
        assert p['historical_birth_place_text']==place
        assert p['birth_country_id']==birth_country
        assert r['bdfutbol_id']==bdf_id
        assert r['photo_status']=='bundled_normalized_bdfutbol'
        asset=ROOT/'frontend'/'public'/'historical9394'/'players'/f'{sid}.jpg'
        with Image.open(asset) as im:
            assert im.size==(40,55) and im.mode=='RGB' and im.format=='JPEG'
    assert sum(x.get('photo_status')=='bundled_normalized_bdfutbol' for x in reg['players'])>=36
    assert bio['bundled_bdfutbol_portraits_total']==36


def test_v032_biographies_are_refreshed_after_profile_curation():
    s=load('historical_snapshot.json'); bio=load('historical_biographies_audit_v032.json')
    players={int(x['source_id']):x for x in s['players']}
    assert bio['active_reconstructed_players']==1813
    assert bio['biographies_written']==1813
    assert bio['biographies_with_season_stats']==1813
    assert bio['biographies_with_source_url']==1813
    assert 'Delantero centro de Trabzonspor' in players[9495349]['historical_biography_1993_94']
    assert 'Arsin (Trabzon)' in players[9495349]['historical_biography_1993_94']
    assert 'Lateral izquierdo de Fenerbahçe' in players[9496374]['historical_biography_1993_94']


def test_v032_bursaspor_genclerbirligi_kocaelispor_roster_recovery_and_roles():
    s=load('historical_snapshot.json'); p={int(x['source_id']):x for x in s['players']}
    # Source-visible opening-roster members recovered instead of being lost because they had zero/few league appearances.
    expected_new={
      9498000:('Vedat Emmez',9357007,0,'1975-10-03T00:00:00'),
      9498001:('Serkan Gültang',9357005,17,'1973-12-22T00:00:00'),
      9498002:('Sunay Kahraman',9357005,17,'1972-01-07T00:00:00'),
      9498003:('İsmail Ünal',9357004,0,'1966-01-01T00:00:00'),
      9498004:('Fevzi Açıkgöz',9357004,3,'1966-11-15T00:00:00'),
    }
    for sid,(name,team,role,dob) in expected_new.items():
        row=p[sid]; assert row['display_name']==name; assert row['team_id']==team; assert row['primary_role']==role; assert row['birth_date']==dob
        assert row['attribute_source'].startswith('fixed_source_comparable_role_')
        assert len(row['attribute_comparable_source_ids'])==2
    assert p[9498002]['profile_review_required'] is True
    assert p[9498004]['historical_secondary_positions_1993_94']==['Defensive Midfielder']
    # High-impact Kocaelispor corrections.
    checks={9496419:(5,'Libero'),9496432:(2,'Left Back'),9497262:(1,'Right Back'),9496429:(7,'Centre Midfielder'),9496424:(16,'Left Winger'),9496430:(17,'Centre Forward')}
    for sid,(role,pos) in checks.items():
        assert p[sid]['primary_role']==role and p[sid]['historical_position_1993_94']==pos


def test_v032_ace_khuse_conflicting_birth_year_is_explicitly_audited():
    s=load('historical_snapshot.json'); p={int(x['source_id']):x for x in s['players']}
    ace=p[9496447]
    assert ace['birth_date']=='1963-09-08T00:00:00'
    assert 'BDFutbol and National-Football-Teams' in ace['historical_profile_source_note']
    assert 'Transfermarkt' in ace['historical_profile_source_note']


def test_v032_all_active_reconstructed_players_have_biography_and_valid_comparables():
    s=load('historical_snapshot.json'); players={int(x['source_id']):x for x in s['players']}
    leagues={930015,930047,930052,930057}
    target_teams={int(t['source_id']) for t in s['teams'] if int(t.get('league_id') or -1) in leagues}
    active=[x for x in s['players'] if int(x.get('team_id') or 0) in target_teams]
    assert len(active)>=1813
    for row in active:
        assert row.get('historical_biography_1993_94')
        for cid in row.get('attribute_comparable_source_ids') or []:
            assert int(cid) in players
