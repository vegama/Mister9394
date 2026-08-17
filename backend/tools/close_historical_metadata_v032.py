from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import (
    role_ratings, ROLE_TO_BROAD, ROLE_TO_LABEL, comparable, stage_rows, profile_gap_stats,
)
from tools.review_created_player_profiles import materialise_attributes

DATA = ROOT / 'data' / 'football9394'
SNAP = DATA / 'historical_snapshot.json'
CATALOG = DATA / 'historical_source_catalog.json'
REGISTRY = DATA / 'created_players_registry.json'
QUEUE = DATA / 'bdfutbol_photo_queue.json'
STAGES = {
    'Belgium': DATA / 'belgium_1993_94_roster_staging.json',
    'Turkey': DATA / 'turkey_1993_94_roster_staging.json',
    'Russia': DATA / 'russia_1993_roster_staging.json',
    'Greece': DATA / 'greece_1993_94_roster_staging.json',
}
LEAGUES = {'Russia': 930015, 'Greece': 930047, 'Belgium': 930052, 'Turkey': 930057}
PHOTO_DIR = ROOT / 'frontend' / 'public' / 'historical9394' / 'players'

BELGIUM_STADIUM_SOURCE = 'https://fr.wikipedia.org/wiki/Championnat_de_Belgique_de_football_1993-1994'
BELGIUM_STADIUMS = [
    (9352001, 'Stade du Pairay'),
    (9352002, 'Freethielstadion'),
    (9352003, 'Veltwijckpark'),
    (9352004, 'Stedelijk Sportstadion'),
    (9352005, 'Stade Vélodrome Oscar Flesch'),
    (9352006, 'Stade Edmond Machtens'),
]

TURKEY_STADIUM_SOURCE = 'https://de.wikipedia.org/wiki/Galatasaray_Istanbul/Saison_1993/94'
SARIYER_CROSSCHECK = 'https://macanilari.com/getir.php?cmd=esnek_arama&cmd_deger=0_-_0_-_0_-_Kar%C5%9F%C4%B1yaka_-_0_-_Sar%C4%B1yer_-_0_-_id_-_0_-_0_-_0_-_0_-_0_-_0_-_0_-_0_-_0_-_yok_-_0_-_0_-_yok_-_0_-_0_-_0_-_0_-_0_-_0_-_0_-_0_-_0&fid=199319941104'
ZEYTINBURNU_CROSSCHECK = 'https://www.soccerpunter.com/soccer-statistics/Turkey/S%C3%BCper-Lig-1993-1994/match/2434861_Zeytinburnu_Spor_Kulub%C3%BC_vs_Fenerbah%C3%A7e_Spor_Kul%C3%BCb%C3%BC'
TURKEY_STADIUMS = [
    (9357001, 'Fenerbahçe Stadı', TURKEY_STADIUM_SOURCE),
    (9357002, 'Hüseyin Avni Aker Stadı', TURKEY_STADIUM_SOURCE),
    (9357003, '19 Mayıs Stadı', TURKEY_STADIUM_SOURCE),
    (9357004, 'İsmetpaşa Stadyumu', TURKEY_STADIUM_SOURCE),
    (9357005, '19 Mayıs Stadı', TURKEY_STADIUM_SOURCE),
    (9357006, 'Kamil Ocak Stadı', TURKEY_STADIUM_SOURCE),
    (9357007, 'Atatürk Stadı', TURKEY_STADIUM_SOURCE),
    (9357008, 'Atatürk Stadı', TURKEY_STADIUM_SOURCE),
    (9357009, '19 Mayıs Stadı', TURKEY_STADIUM_SOURCE),
    (9357010, 'Atatürk Stadı', TURKEY_STADIUM_SOURCE),
    (9357011, 'Zeytinburnu Stadı', ZEYTINBURNU_CROSSCHECK),
    (9357012, 'Yenişehir Stadı', TURKEY_STADIUM_SOURCE),
    (9357013, 'Atatürk Stadı', TURKEY_STADIUM_SOURCE),
    (9357014, 'Yusuf Ziya Öniş Stadyumu', SARIYER_CROSSCHECK),
]

TURKEY_REF_SOURCE_1 = 'https://www.transfermarkt.com/super-lig/schiedsrichter/wettbewerb/TR1/saison_id/1993/plus//sort/rote_karten.desc'
TURKEY_REF_SOURCE_2 = TURKEY_REF_SOURCE_1 + '/page/2'
TURKEY_REFS = [
    ('Serdar Çakman',10,39,0,6,2),('Ahmet Çakar',9,52,2,5,7),('Vahap Beyaz',13,33,0,4,1),('Oğuz Sarvan',14,58,1,3,5),
    ('Hamza Işın',10,37,0,3,2),('Adnan Türkkan',3,7,0,3,4),('Mustafa Çulcu',9,39,0,2,4),('Metin Tokat',14,54,0,2,4),
    ('Hasan Ceylan',11,29,2,2,11),('Bülent Yavuz',15,58,1,2,6),('Engin Kurt',8,41,1,2,4),('Taner Yalçındağ',7,22,0,2,1),
    ('Sabri Çelik',13,40,1,2,3),('Alican Lakot',6,23,0,2,1),('İbrahim Aksoy',6,25,0,1,1),('Galip Bitigen',7,25,0,1,0),
    ('Ünsal Çimen',8,29,0,1,4),('Sadık Deda',5,17,0,1,5),('Ahmet İbanoğlu',5,19,0,1,4),('Erdoğan Kırıcı',3,11,0,1,2),
    ('Osman Avcı',7,16,0,1,2),('Serdar Çakır',10,37,0,1,2),('Mustafa Arslan',5,29,0,1,3),('Sefer Altuntaş',3,23,0,1,1),
    ('Hakan Ceylan',1,1,0,0,1),('Erman Toroğlu',4,11,0,0,1),('Abdurrahman Arıcı',5,9,0,0,2),('Nedim Göklü',5,18,0,0,3),
    ('Mekki Keskin',5,16,0,0,0),('Turgut Sığıç',7,29,0,0,4),('Necdet Erdilek',5,22,1,0,0),('Ergül Yücedağ',5,17,1,0,1),
    ('Yusuf Yaylı',1,5,0,0,0),('Ömer Alper',1,3,0,0,0),
]

RUSSIA_REF_SOURCE_1 = 'https://www.transfermarkt.com/premier-liga/schiedsrichter/wettbewerb/RU1/saison_id/1992/plus//sort/rote_karten.desc'
RUSSIA_REF_SOURCE_2 = RUSSIA_REF_SOURCE_1 + '/page/2'
RUSSIA_REFS = [
    ('Vyacheslav Sorokin',8,20,0,3,4),('Sergey Khusainov',16,23,1,2,5),('Aleksey Rumyantsev',9,16,0,2,5),('Yuriy Chebotarev',14,26,0,2,1),
    ('Aleksandr Kuzmenko',3,4,0,2,0),('Andrey Butenko',12,25,0,1,8),('Taras Bezubyak',16,37,0,1,2),('Nikolay Miloserdov',9,19,0,1,1),
    ('Viktor Yarygin',12,27,0,1,6),('Andrey Budogosskiy',9,14,1,1,5),('Aleksandr Kirillov',13,20,1,1,8),('Aleksey Markelov',15,33,0,1,5),
    ('Gennadi Kulichenkov',12,24,0,1,6),('Valentin Ivanov',5,6,0,0,3),('Nikolay Levnikov',14,30,0,0,5),('Viktor Filippov',14,21,0,0,3),
    ('Vladimir Ovchinnikov',14,32,1,0,5),('Sergey Anokhin',13,25,1,0,6),('Igor Siner',11,27,0,0,5),('Yuriy Savchenko',12,15,0,0,3),
    ('Yuriy Khlopotnov',7,4,0,0,0),('Anatoliy Malyarov',10,16,1,0,3),('Aleksandr Savkin',7,9,0,0,3),('Garyafi Zhafyarov',9,8,0,0,5),
    ('Nikolay Egorov',3,9,0,0,1),('Lom-Ali Ibragimov',13,17,0,0,7),('Viktor Gavrin',7,20,0,0,3),('Vladimir Gameev',1,1,0,0,1),
    ('Viktor Denisov',1,2,0,0,2),('Valentin Kupryashkin',5,3,0,0,2),('Vyacheslav Matushevskiy',3,6,0,0,0),('Aleksandr Lapin',3,6,0,0,1),
    ('Sergey Lapochkin Sr.',6,15,0,0,1),
]

FENER_SOURCE = 'https://www.transfermarkt.com/fenerbahce-sk/kader/verein/36/saison_id/1993/plus/1'
# Exact/season-specific details for the 25 identities already present in the verified staging.
# We do not create the three extra Transfermarkt rows that are absent from the staging gate in this pass.
FENER_PROFILES: dict[int, dict[str,Any]] = {
    9495315: dict(name='Engin İpekoğlu',dob='1961-06-07',nats=[84],height=184,role=0,pos='Goalkeeper'),
    9495343: dict(name='İlker Yağcıoğlu',dob='1966-03-10',nats=[84],height=178,foot=1,role=1,pos='Right-Back'),
    9496362: dict(name='Andreas Wagenhaus',dob='1964-10-29',nats=[4],role=3,pos='Centre-Back'),
    9495325: dict(name='Emre Aşık',dob='1973-12-13',nats=[84],height=183,foot=1,role=3,pos='Centre-Back'),
    9496364: dict(name='Uche Okechukwu',dob='1967-09-27',nats=[59,84],height=187,foot=1,role=3,pos='Centre-Back'),
    9495332: dict(name='Oğuz Çetin',dob='1963-02-15',nats=[84],height=183,foot=1,role=7,pos='Central Midfield'),
    9496365: dict(name='Tayfur Havutçu',dob='1970-04-23',nats=[84,4],role=6,pos='Defensive Midfield'),
    9496366: dict(name='Müjdat Yetkiner',dob='1961-11-16',nats=[84],height=175,foot=1,role=3,pos='Centre-Back'),
    9496367: dict(name='Brian Steen Nielsen',dob='1968-12-28',nats=[33],height=180,foot=2,role=13,pos='Left Midfield'),
    9495352: dict(name='Bülent Uygun',dob='1971-08-01',nats=[84],height=178,role=8,pos='Attacking Midfield'),
    9496368: dict(name='Mecnur Çolak',dob='1967-08-07',nats=[84,21],role=17,pos='Centre-Forward'),
    9496369: dict(name='Altay Dağdelen',dob='1970-01-20',nats=[84],role=0,pos='Goalkeeper'),
    9495351: dict(name='Aykut Kocaman',dob='1965-04-05',nats=[84],height=174,foot=3,role=17,pos='Centre-Forward'),
    9496370: dict(name='Kemalettin Şentürk',dob='1970-02-09',nats=[84],role=6,pos='Defensive Midfield'),
    9496371: dict(name='Nuri Kamburoğlu',dob='1967-05-24',nats=[84],height=179,role=3,pos='Centre-Back'),
    9496372: dict(name='Cengiz Alp',dob='1969-01-25',nats=[84],role=16,pos='Left Winger'),
    9496373: dict(name='Aygün Taşkıran',dob='1974-04-22',nats=[84],height=175,foot=2,role=16,pos='Left Winger'),
    9496374: dict(name='Semih Yuvakuran',dob='1963-09-01',nats=[84],foot=2,role=2,pos='Left-Back'),
    9497230: dict(name='Demir Hotic',nats=[20,4],height=179,role=17,pos='Centre-Forward'),
    9497231: dict(name='Rıdvan Dilmen',dob='1962-08-15',nats=[84],height=173,foot=1,role=8,pos='Attacking Midfield'),
    9497232: dict(name='Burhan Saatçioğlu',dob='1973-05-11',nats=[84],height=174,foot=1,role=5,pos='Sweeper'),
    9497233: dict(name='Hakan Tecimer',dob='1967-01-06',nats=[84],role=12,pos='Right Winger'),
    9497234: dict(name='Sadettin Demirtaş',dob='1968-12-20',nats=[84],role=17,pos='Centre-Forward'),
    9497235: dict(name='Volkan Alpacar',dob='1973-04-16',nats=[84],role=17,pos='Centre-Forward'),
    9497236: dict(name='Kerem Şenel',dob='1974-10-05',nats=[84],pos='Defender',precision='broad_only',broad='DEF'),
}

COUNTRY_NAMES={4:'Alemania',20:'Bosnia-Herzegovina',21:'Bulgaria',33:'Dinamarca',40:'Rusia',47:'Grecia',59:'Nigeria',84:'Turquía'}

def load(p:Path)->Any: return json.loads(p.read_text(encoding='utf-8'))
def dump(p:Path,o:Any)->None: p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def split_name(name:str)->tuple[str|None,str|None]:
    parts=name.split()
    return (None,name) if len(parts)<=1 else (' '.join(parts[:-1]),parts[-1])

def add_stadium_rows(snapshot:dict[str,Any], catalog:dict[str,Any], rows:list[tuple], country:str, source_label:str)->list[dict[str,Any]]:
    teams={int(t['source_id']):t for t in snapshot['teams']}
    prior={int(x.get('historical_team_id')):x for x in catalog['stadiums'] if x.get('historical_team_id') is not None}
    next_id=max(int(x['source_id']) for x in catalog['stadiums'])+1
    out=[]
    for item in rows:
        team_id,name=item[0],item[1]
        source_url=item[2] if len(item)>2 else BELGIUM_STADIUM_SOURCE
        row=prior.get(team_id)
        if row is None:
            row={'source_id':next_id,'name':name,'short_name':name,'without_article':False,'width_m':None,'length_m':None,
                 'capacity':None,'city_id':None,'stars':None,'grass_quality':None,'temporal_confidence':'season_specific_historical_source',
                 'historical_season':'1993-94','historical_team_id':team_id,'source_url':source_url,'source_label':source_label,
                 'physical_parameters_status':'not_inferred_from_modern_values'}
            catalog['stadiums'].append(row); prior[team_id]=row; next_id+=1
        else:
            row.update({'name':name,'short_name':name,'source_url':source_url,'source_label':source_label,'historical_season':'1993-94',
                        'temporal_confidence':'season_specific_historical_source','physical_parameters_status':'not_inferred_from_modern_values'})
        team=teams[team_id]
        team.update({'stadium_id':int(row['source_id']),'venue_source_status':'historical_source_backed_1993_94','venue_source_url':source_url,
                     'venue_source_label':source_label})
        out.append({'team_id':team_id,'team_name':team['name'],'stadium_id':int(row['source_id']),'stadium_name':name,'source_url':source_url})
    catalog['counts']['stadiums']=len(catalog['stadiums'])
    return out

def add_ref_pool(snapshot:dict[str,Any],catalog:dict[str,Any],league_id:int,country_id:int,association:str,season:str,rows:list[tuple],source1:str,source2:str,expected_matches:int)->dict[str,Any]:
    refs=catalog['referees']; existing={(int(r.get('league_id') or -1),(r.get('display_name') or '').casefold()) for r in refs}
    next_id=max(int(r['source_id']) for r in refs)+1
    added=0
    for i,(name,apps,y,sy,red,pens) in enumerate(rows):
        key=(league_id,name.casefold())
        if key in existing: continue
        first,surname=split_name(name)
        url=source1 if i<25 else source2
        refs.append({'source_id':next_id,'display_name':name,'first_name':first,'surname1':surname,'surname2':None,'birth_city_id':None,
                     'birth_country_id':None,'nationality_country_id':country_id,'birth_date':None,'backup_birth_date':None,'birth_date_conflict':False,
                     'yellow_tendency':round(y/apps,3) if apps else None,'red_tendency':round((sy+red)/apps,3) if apps else None,'quality':None,
                     'association':association,'profession':None,'league_id':league_id,'historical_season':season,'appearances':apps,'yellow_count':y,
                     'second_yellow_count':sy,'red_count':red,'penalties_awarded':pens,'temporal_confidence':'season_specific_historical_source',
                     'source_url':url,'source_label':f'Transfermarkt {association} {season} referees'})
        next_id+=1; added+=1; existing.add(key)
    appearances=sum(x[1] for x in rows)
    if appearances != expected_matches: raise RuntimeError(f'{association} referee appearance total {appearances} != {expected_matches}')
    league=next(l for l in snapshot['leagues'] if int(l['source_id'])==league_id)
    league.setdefault('source_rule_hints',{}).update({'referee_pool_status':f'historical_source_backed_complete_{season.replace("-","_")}',
        'referee_pool_source':source1,'referee_pool_secondary_page':source2,'referee_pool_size':len(rows),'referee_pool_match_assignments':appearances,
        'referee_pool_completeness_note':f'Appearance counts sum to all {expected_matches} league matches; no unnamed referee is required.'})
    catalog['counts']['referees']=len(refs)
    return {'added':added,'pool_size':len(rows),'appearance_assignments':appearances,'expected_matches':expected_matches,'source_pages':[source1,source2]}

def apply_fener_profiles(snapshot:dict[str,Any],stages:dict[str,dict[str,Any]],registry:dict[str,Any],queue:dict[str,Any])->list[dict[str,Any]]:
    players=snapshot['players']; by={int(p['source_id']):p for p in players}
    originals=[p for p in players if not p.get('external_origin') and not p.get('creation_batch')]
    srows=stage_rows(stages)
    regby={int(r['source_id']):r for r in registry.get('players',[]) if r.get('source_id') is not None}
    qby={int(r['source_id']):r for r in queue.get('players',[]) if r.get('source_id') is not None}
    out=[]
    for sid,patch in FENER_PROFILES.items():
        p=by[sid]
        before={'name':p.get('display_name'),'role':p.get('primary_role'),'pos':p.get('historical_position_1993_94'),'birth':p.get('birth_date'),'country':p.get('international_country_id')}
        p['display_name']=patch['name']
        first,surname=split_name(patch['name']); p['first_name']=first; p['surname1']=surname
        if patch.get('dob'): p['birth_date']=patch['dob']+'T00:00:00'
        nats=[int(x) for x in patch.get('nats',[])]
        if nats:
            p['international_country_id']=nats[0]; p['profile_nationality_country_ids']=nats
            if len(nats)>1: p['secondary_nationality_country_id']=nats[1]
        if patch.get('height') is not None:p['height_cm']=int(patch['height'])
        if patch.get('foot') is not None:p['preferred_foot']=int(patch['foot'])
        p['source_profile_position']=patch['pos']; p['profile_position_precision']=patch.get('precision','exact')
        p['historical_profile_source']='Transfermarkt detailed squad 1993-94 v0.32'; p['historical_profile_source_url']=FENER_SOURCE
        p['profile_review_required']=patch.get('precision')=='broad_only'
        role=patch.get('role')
        if role is not None:
            role=int(role); p['role_ratings']=role_ratings(role); p['primary_role']=role; p['broad_position']=ROLE_TO_BROAD[role]
            p['historical_position_1993_94']=ROLE_TO_LABEL[role]; p['historical_position_source']='Transfermarkt detailed squad 1993-94 v0.32'
            if role != int(before['role'] or 0):
                a,b=comparable(originals,ROLE_TO_BROAD[role],int(p.get('overall') or 70),sid)
                p['attributes']=materialise_attributes(int(p.get('overall') or 70),a,b)
                p['attribute_source']='fixed_source_comparable_role_correction_0.32'; p['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]
        elif patch.get('broad'):
            p['broad_position']=patch['broad']; p['historical_position_1993_94']='Defender (exact role unresolved)'
            p['historical_position_source']='Transfermarkt broad squad category 1993-94 v0.32'
        for row in srows.get(sid,[]):
            row['resolved_display_name']=p['display_name']; row['resolved_primary_role']=int(p.get('primary_role') or 0)
            row['resolved_exact_position']=p.get('historical_position_1993_94'); row['resolved_birth_date']=p.get('birth_date')
            row['resolved_country_id']=p.get('international_country_id') or p.get('birth_country_id'); row['profile_source_url']=FENER_SOURCE
            row['profile_source']='Transfermarkt detailed squad 1993-94 v0.32'; row['source_profile_position']=patch['pos']
            row['position_source']='season_specific_profile_v0.32'
        for target in (regby.get(sid),qby.get(sid)):
            if target is None: continue
            target.update({'display_name':p['display_name'],'birth_date':(p.get('birth_date') or '')[:10] or None,'country_id':p.get('international_country_id') or p.get('birth_country_id'),
                           'country_name':COUNTRY_NAMES.get(int(p.get('international_country_id') or p.get('birth_country_id') or 0),target.get('country_name')),
                           'broad_position':p.get('broad_position'),'historical_position_1993_94':p.get('historical_position_1993_94'),
                           'profile_review_required':bool(p.get('profile_review_required')),'individual_profile_source':'Transfermarkt detailed squad 1993-94 v0.32',
                           'individual_profile_source_url':FENER_SOURCE})
        out.append({'source_id':sid,'before':before,'after':{'name':p['display_name'],'role':p.get('primary_role'),'pos':p.get('historical_position_1993_94'),'birth':p.get('birth_date'),'country':p.get('international_country_id'),'height':p.get('height_cm'),'foot':p.get('preferred_foot')},'source_position':patch['pos']})
    return out

def main()->None:
    snapshot=load(SNAP); catalog=load(CATALOG); registry=load(REGISTRY); queue=load(QUEUE); stages={k:load(v) for k,v in STAGES.items()}
    before=profile_gap_stats(snapshot)
    bel=add_stadium_rows(snapshot,catalog,BELGIUM_STADIUMS,'Belgium','Belgium Division 1 1993-94 participant stadium table')
    tur=add_stadium_rows(snapshot,catalog,TURKEY_STADIUMS,'Turkey','Turkey 1. Lig 1993-94 match-venue reconstruction')
    tr=add_ref_pool(snapshot,catalog,930057,84,'Turkey','1993-94',TURKEY_REFS,TURKEY_REF_SOURCE_1,TURKEY_REF_SOURCE_2,240)
    ru=add_ref_pool(snapshot,catalog,930015,40,'Russia','1993',RUSSIA_REFS,RUSSIA_REF_SOURCE_1,RUSSIA_REF_SOURCE_2,306)
    prof=apply_fener_profiles(snapshot,stages,registry,queue)
    after=profile_gap_stats(snapshot)
    unresolved_venues=[int(t['source_id']) for t in snapshot['teams'] if isinstance(t.get('league_id'),int) and t.get('venue_source_status')=='unresolved_historical_1993_94']
    unresolved_refs=[lid for lid in LEAGUES.values() if not any(r.get('league_id')==lid for r in catalog['referees'])]
    if unresolved_venues: raise RuntimeError(f'unresolved historical venues remain: {unresolved_venues}')
    if unresolved_refs: raise RuntimeError(f'unresolved referee leagues remain: {unresolved_refs}')
    if len({int(r['source_id']) for r in registry['players']}) != len(registry['players']): raise RuntimeError('duplicate registry ids')
    if {int(r['source_id']) for r in registry['players']} != {int(r['source_id']) for r in queue['players']}: raise RuntimeError('registry/queue mismatch')
    role_changes=sum(int(x['before']['role'] or 0)!=int(x['after']['role'] or 0) for x in prof if x['after']['pos']!='Defender (exact role unresolved)')
    audit={'schema_version':1,'checkpoint':'0.32.0-historical-metadata-closure-and-fener-profiles','status':'pass',
           'stadiums':{'belgium_closed':len(bel),'turkey_closed':len(tur),'unresolved_count':0,'rows':bel+tur,'physical_parameters_policy':'No modern capacity or pitch dimensions are back-filled without a season-specific historical source.'},
           'referees':{'Turkey':tr,'Russia':ru,'unresolved_referee_pool_league_ids':[],'Greece_status':'historical source-backed subset 11/45 retained; no unnamed officials invented.'},
           'profiles':{'batch':'Fenerbahçe 1993-94 detailed squad','curated':len(prof),'role_corrections':role_changes,'review_required':sum(x['after']['pos']=='Defender (exact role unresolved)' for x in prof),'source':FENER_SOURCE,'changes':prof},
           'profile_gaps_before':before,'profile_gaps_after':after}
    gaps={'schema_version':1,'checkpoint':'0.32.0-historical-metadata-closure-and-fener-profiles','status':'pass','profile_gaps':after,
          'unresolved_historical_venue_team_ids':[],'unresolved_historical_referee_pool_league_ids':[],
          'partially_resolved_referee_pools':{'930047':'RSSSF publishes 11 named leaders out of 45 referees; encoded as an explicit historical subset.'},
          'profile_review_queue':[{'source_id':sid,'display_name':FENER_PROFILES[sid]['name'],'reason':'season source only says Defender; exact defensive role remains source-gated'} for sid in FENER_PROFILES if FENER_PROFILES[sid].get('precision')=='broad_only'],
          'policy':'Known player-profile gaps remain explicit and source-gated; venue/referee structural gaps for the four newly reconstructed leagues are now closed except Greece referee-name completeness.'}
    dump(SNAP,snapshot); dump(CATALOG,catalog); dump(REGISTRY,registry); dump(QUEUE,queue)
    for country,path in STAGES.items(): dump(path,stages[country])
    dump(DATA/'historical_profiles_metadata_audit_v032.json',audit); dump(DATA/'historical_metadata_gaps_v032.json',gaps)
    print(json.dumps({'status':'pass','stadiums_closed':len(bel)+len(tur),'turkey_referees':tr,'russia_referees':ru,'fener_profiles':len(prof),'role_corrections':role_changes,'unresolved_venues':0,'unresolved_referee_leagues':[],'profile_gaps_after':after},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
