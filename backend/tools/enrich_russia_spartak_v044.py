from __future__ import annotations

from pathlib import Path
from typing import Any
from collections import Counter
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import ROLE_TO_BROAD, ROLE_TO_LABEL, comparable, role_ratings  # noqa:E402
from tools.review_created_player_profiles import materialise_attributes  # noqa:E402

DATA=ROOT/'data'/'football9394'
SNAP=DATA/'historical_snapshot.json'; REG=DATA/'created_players_registry.json'; QUEUE=DATA/'bdfutbol_photo_queue.json'
STAGE=DATA/'russia_1993_roster_staging.json'; CATALOG=DATA/'historical_source_catalog.json'; CONTEXT=DATA/'country_context_1993.json'
CHECKPOINT='0.44.0-russia-spartak-deep'; VERSION='0.44'; RUSSIA_LEAGUE_ID=930015; TARGET_TEAM_ID=617
EXPECTED_RUSSIA_BEFORE='f73e73c7dee70fd00d82f9679d189677161a662bc72b71a5a723584fb5715cfa'
BDF_TEAM='https://www.bdfutbol.com/en/t/t1993-9410023.html'

ROLE_ES={0:'Portero',1:'Lateral derecho',2:'Lateral izquierdo',3:'Defensa',4:'Defensa',5:'Líbero',6:'Mediocentro defensivo',7:'Centrocampista',8:'Mediapunta',9:'Interior derecho',10:'Interior derecho',11:'Extremo derecho',12:'Extremo derecho',13:'Interior izquierdo',14:'Interior izquierdo',15:'Extremo izquierdo',16:'Extremo izquierdo',17:'Delantero'}

def p(name:str,dob:str,place:str,territory:int,state:str,bdf:str,pos:str,height:int|None=None,weight:int|None=None,
      nats:list[int]|None=None,role:int|None=None,precision:str='stage_exact_profile_broad',note:str|None=None,
      selections:list[dict[str,Any]]|None=None)->dict[str,Any]:
    return dict(name=name,dob=dob,place=place,territory=territory,state=state,bdf=bdf,pos=pos,height=height,weight=weight,
                nats=nats,role=role,precision=precision,note=note,selections=selections or [])

# Birthplaces are stored in their historical sovereign-state context. `territory` is only the
# modern/successor territory used for search/display support and is never copied to birth_country_id.
# BDFutbol individual profiles are the default identity/DOB/profile source. Targeted international
# history evidence is retained independently from citizenship/nationality.
P:dict[int,dict[str,Any]]={
 9496613:p('Gintaras Mindaugovich Staučė','1969-12-24','Alytus',52,'USSR','98206','Goalkeeper',188,80,[52],0,'exact',
  selections=[{'country_id':52,'team':'Lithuania','from_year':1992,'to_year':2004,'source':'FootballDatabase international profile','source_url':'https://www.footballdatabase.eu/en/player/details/3212-gintaras-stauce'}]),
 9494088:p('Viktor Savelyevich Onopko','1969-10-14','Luhansk',85,'USSR','2609','Central',188,77,[40,85],3,'exact'),
 9495357:p('Ramiz Mehman oğlu Mamedov','1972-08-21','Moscow',40,'USSR','705104','Left back',175,None,[40,130],2,'exact',
  note='Corrected 21/05/1972 -> 21/08/1972: BDFutbol and Transfermarkt agree on 21 August 1972; older staging date is rejected.'),
 9496614:p('Andrei Yevgenyevich Ivanov','1967-04-06','Moscow',40,'USSR','89302','Central',189,83,[40],3,'exact'),
 9494081:p('Yuri Valeryevich Nikiforov','1970-09-16','Odesa',85,'USSR','2660','Central',185,88,[40,85],3,'exact',
  selections=[{'country_id':85,'team':'Ukraine','from_year':1992,'to_year':1992,'source':'eu-football international record','source_url':'https://eu-football.info/_player.php?id=15093'},{'country_id':40,'team':'Russia','from_year':1993,'to_year':2002,'source':'eu-football international record','source_url':'https://eu-football.info/_player.php?id=15093'}]),
 9494089:p('Igor Anatolyevich Lediakhov','1968-05-22','Sochi',40,'USSR','1083','Midfielder',187,84,[40]),
 9494084:p('Valeri Georgievich Karpin','1969-02-02','Narva',39,'USSR','2570','Midfielder',185,76,[40,39]),
 9494083:p('Andrey Vladimirovich Pyatnitsky','1967-09-27','Tashkent',209,'USSR','58032','Midfielder',182,None,[40,209],
  selections=[{'country_id':209,'team':'Uzbekistan','from_year':1992,'to_year':1992,'source':'RSSSF/Wikipedia international record','source_url':'https://en.wikipedia.org/wiki/Andrey_Pyatnitsky'},{'country_id':40,'team':'Russia','from_year':1993,'to_year':1995,'source':'RSSSF/Wikipedia international record','source_url':'https://en.wikipedia.org/wiki/Andrey_Pyatnitsky'},{'historical_team':'USSR','from_year':1990,'to_year':1990,'source':'RSSSF/Wikipedia international record','source_url':'https://en.wikipedia.org/wiki/Andrey_Pyatnitsky'},{'historical_team':'CIS','from_year':1992,'to_year':1992,'source':'RSSSF/Wikipedia international record','source_url':'https://en.wikipedia.org/wiki/Andrey_Pyatnitsky'}]),
 9494087:p('Ilya Vladimirovich Tsymbalar','1969-06-17','Odesa',85,'USSR','701760','Midfielder',178,71,[40,85],
  selections=[{'country_id':85,'team':'Ukraine','from_year':1992,'to_year':1992,'source':'RSSSF international record','source_url':'https://www.rsssf.org/miscellaneous/tsymbalar-intl.html'},{'country_id':40,'team':'Russia','from_year':1994,'to_year':1999,'source':'RSSSF international record','source_url':'https://www.rsssf.org/miscellaneous/tsymbalar-intl.html'}]),
 9496615:p('Nikolai Nikolayevich Pisarev','1968-11-23','Moscow',40,'USSR','2091','Forward',180,79,[40],17,'broad_only'),
 9494085:p('Vladimir Yevgenyevich Beschastnykh','1974-04-01','Moscow',40,'USSR','2619','Striker',187,83,[40],17,'exact'),
 2705:p('Stanislav Salamovich Cherchesov','1963-09-02','Alagir',40,'USSR','80005','Goalkeeper',183,None,[40],0,'exact'),
 9496616:p('Fyodor Fyodorovich Cherenkov','1959-07-25','Moscow',40,'USSR','41922','Midfielder',178,None,[40]),
 9494090:p('Dmitri Alekseyevich Khlestov','1971-01-21','Moscow',40,'USSR','57627','Defender',None,None,[40]),
 515:p('Dmitri Lvovich Popov','1967-02-27','Yaroslavl',40,'USSR','603','Midfielder',175,73,[40]),
 517:p('Dmitri Leonidovich Radchenko','1970-12-02','Saint Petersburg',40,'USSR','604','Striker',186,80,[40],17,'exact'),
 9496617:p("Aleksandr Vasil'evich Pomazun",'1971-10-11','Kharkiv',85,'USSR','590782','Goalkeeper',191,90,[40,85],0,'exact',
  selections=[{'country_id':85,'team':'Ukraine','from_year':1992,'to_year':1992,'source':'National-Football-Teams international record','source_url':'https://www.national-football-teams.com/player/20410/Oleksandr_Pomazun.html'}]),
 9496618:p('Dmitri Vasilyevich Ananko','1973-09-29','Novocherkassk',40,'USSR','84989','Central',180,None,[40],3,'exact'),
 9497349:p('Andrey Aleksandrovich Gashkin','1970-12-06','Taldom',40,'USSR','590816','Midfielder',178,72,[40]),
 9497350:p('Andrey Valeryevich Tikhonov','1970-10-16','Korolyov',40,'USSR','56757','Midfielder',177,75,[40]),
 9497351:p('Sergei Yurievich Rodionov','1962-09-03','Moscow',40,'USSR','41921','Forward',186,None,[40],17,'broad_only'),
 9497352:p('Andrey Alekseyevich Chernyshov','1968-01-07','Moscow',40,'USSR','701521','Central',188,75,[40],3,'exact'),
 9497353:p('Aleksandr Arkadyevich Bondar','1967-11-21','Magdeburg',4,'German Democratic Republic','1177671','Defender',183,None,None,3,'broad_only',
  note='Born in Magdeburg in 1967: historical birth state is GDR; modern Germany is retained only as territorial lookup, not as birth_country_id.'),
 9497354:p('Serhiy Anatoliyovych Pohodin','1968-04-29','Luhansk',85,'USSR','2479','Midfielder',183,78,[85,40],8,'specialist_crosscheck',
  note='BDF squad uses Pogodin while the individual profile uses Ukrainian-form Pohodin; both spellings are preserved as transliteration aliases.',
  selections=[{'country_id':85,'team':'Ukraine','from_year':1992,'to_year':1992,'source':'National-Football-Teams international record','source_url':'https://www.national-football-teams.com/player/28580/Serhiy_Pohodin.html'}]),
 9497355:p('Sergey Sergeyevich Chudin','1973-11-24','Moscow',40,'USSR','707174','Defender',181,79,[40]),
 9497356:p('Valeriy Nikolayevich Chizhov','1975-04-14','Moscow',40,'USSR','590184','Goalkeeper',185,82,[40],0,'exact'),
 9497357:p('Valeriy Viktorovich Kechinov','1974-08-05','Tashkent',209,'USSR','590581','Midfielder',179,None,[40,209],7,'broad_only',
  note='Prior centre-forward inference removed: BDFutbol and independent career sources identify Kechinov as midfielder. Selection history is kept separate from nationality.',
  selections=[{'country_id':209,'team':'Uzbekistan','from_year':1992,'to_year':1992,'source':'National-Football-Teams international record','source_url':'https://www.national-football-teams.com/player/19241/Valeri_Kechinov.html'},{'country_id':40,'team':'Russia','from_year':1994,'to_year':1998,'source':'National-Football-Teams international record','source_url':'https://www.national-football-teams.com/player/19241/Valeri_Kechinov.html'}]),
 9497358:p('Andrey Stepanivich Konovalov','1974-09-13','Chelyabinsk',40,'USSR','590021','Midfielder',180,74,[40]),
 9497359:p('Dmitriy Vitalevich Gradilenko','1969-08-11','Moscow',40,'USSR','591115','Defender',179,75,None,3,'broad_only',
  note='Prior forward inference removed: BDFutbol identifies Gradilenko as defender.'),
 9497360:p('Vladimir Nikolaevich Baksheev','1970-04-22','Krasnoyarsk',40,'USSR','1159034','Midfielder',174,None,None,7,'broad_only',
  note='Prior left-wing inference is not retained as exact because the individual profile only supports Midfielder.'),
 9497361:p('Alexey Vyacheslavovich Sergeev','1966-06-05','Moscow',40,'USSR','650543','',None,None,None,None,'profile_position_blank',
  note='BDFutbol individual profile has no position value; staged centre-back role is retained pending specialist corroboration.'),
 9497362:p('Sergey Vladimirovich Krestov','1972-10-06','Moscow',40,'USSR','1159043','Forward',185,None,None,17,'broad_only',
  note='Prior left-back inference removed: BDFutbol identifies Krestov as forward.'),
 9497363:p('Mikhail Viktorovich Rekuts','1975-10-02','Moscow',40,'USSR','1159030','Defender',176,None,None,3,'broad_only',
  note='Prior defensive-midfield inference reduced to broad Defender because that is the supported BDFutbol profile evidence.'),
}

def load(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def dump(p:Path,o:Any): p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def bdf_url(x:dict[str,Any])->str: return f"https://www.bdfutbol.com/en/j/j{x['bdf']}.html"
def split_name(name:str):
    parts=name.split(); return (None,name) if len(parts)==1 else (' '.join(parts[:-1]),parts[-1])

def fingerprint(snapshot:dict[str,Any],team_ids:set[int])->str:
    payload={'teams':sorted([x for x in snapshot['teams'] if int(x.get('source_id') or -1) in team_ids],key=lambda x:int(x['source_id'])),
             'players':sorted([x for x in snapshot['players'] if int(x.get('team_id') or -1) in team_ids],key=lambda x:int(x['source_id']))}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def country_names(catalog:dict[str,Any])->dict[int,str]:
    return {int(c['source_id']):str(c.get('historical_name_1993') or c.get('name') or c['source_id']) for c in catalog.get('countries',[])}

def stats(snapshot:dict[str,Any])->dict[str,Any]:
    tids={int(t['source_id']) for t in snapshot['teams'] if int(t.get('league_id') or -1)==RUSSIA_LEAGUE_ID}
    rows=[p for p in snapshot['players'] if int(p.get('team_id') or -1) in tids]
    return {
      'players':len(rows),'missing_birth_date':sum(not p.get('birth_date') for p in rows),
      'missing_birth_country_id':sum(p.get('birth_country_id') is None for p in rows),
      'birth_geography_unresolved':sum(not p.get('historical_birth_state') and p.get('birth_country_id') is None for p in rows),
      'missing_international_country_id':sum(p.get('international_country_id') is None for p in rows),
      'missing_bdfutbol_id':sum(not p.get('bdfutbol_id') for p in rows),
      'missing_height_cm':sum(p.get('height_cm') is None for p in rows),'missing_weight_kg':sum(p.get('weight_kg') is None for p in rows),
      'historical_birth_state_resolved':sum(bool(p.get('historical_birth_state')) for p in rows),
      'transliteration_layer_resolved':sum(bool(p.get('name_transliterations')) for p in rows),
      'selection_history_resolved':sum(bool(p.get('represented_selection_history')) for p in rows),
    }

def reattribute(player:dict[str,Any],role:int,originals:list[dict[str,Any]],sid:int)->None:
    a,b=comparable(originals,ROLE_TO_BROAD[role],int(player.get('overall') or 70),sid)
    player['attributes']=materialise_attributes(int(player.get('overall') or 70),a,b)
    player['attribute_source']='fixed_source_comparable_role_correction_0.44'
    player['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]

def selection_history(player:dict[str,Any],patch:dict[str,Any])->list[dict[str,Any]]:
    hist=[dict(x) for x in patch.get('selections',[])]
    wc=player.get('world_cup_1994')
    if isinstance(wc,dict) and wc.get('country_id'):
        cid=int(wc['country_id'])
        if not any(x.get('country_id')==cid and int(x.get('from_year') or 0)<=1994<=int(x.get('to_year') or 9999) for x in hist):
            hist.append({'country_id':cid,'team':wc.get('team_code') or 'National team','from_year':1994,'to_year':1994,'source':'Fjelstul World Cup Database','source_external_player_id':wc.get('external_player_id')})
    return hist

def position_label(player:dict[str,Any],patch:dict[str,Any])->tuple[str,str,str,bool]:
    precision=patch['precision']; source=bdf_url(patch); pos=patch['pos']
    if precision=='profile_position_blank':
        return (str(player.get('historical_position_1993_94') or ROLE_TO_LABEL[int(player['primary_role'])])+' (individual profile position blank; review retained)',
                'Existing 1993-94 staging role retained because BDFutbol position is blank v0.44',BDF_TEAM,True)
    if precision=='specialist_crosscheck':
        return (ROLE_TO_LABEL[int(player['primary_role'])], 'BDFutbol broad position + National-Football-Teams specialist corroboration v0.44', patch['selections'][0]['source_url'],False)
    if precision=='broad_only':
        return (pos+' (exact role unresolved)', 'BDFutbol broad individual-profile position v0.44',source,True)
    if precision=='exact':
        return (ROLE_TO_LABEL[int(player['primary_role'])], 'BDFutbol individual-profile exact position v0.44',source,False)
    return (str(player.get('historical_position_1993_94') or ROLE_TO_LABEL[int(player['primary_role'])]),
            'Season-specific 1993-94 staging role + compatible BDFutbol broad profile v0.44',BDF_TEAM,False)

def biography(player:dict[str,Any],row:dict[str,Any])->str:
    role=ROLE_ES.get(int(player.get('primary_role') or 0),'Futbolista')
    if player.get('profile_position_precision') in {'broad_only','profile_position_blank'}: role='Futbolista'
    parts=[f'{role} de Spartak Moskva en la temporada 1993-94.']
    vals=[]
    if isinstance(row.get('appearances'),int): vals.append(f"{row['appearances']} partidos")
    if isinstance(row.get('starts'),int): vals.append(f"{row['starts']} como titular")
    if isinstance(row.get('minutes'),int): vals.append(f"{row['minutes']:,}".replace(',','.')+' minutos')
    if vals: parts.append('En el registro liguero figura con '+', '.join(vals)+'.')
    if int(player.get('primary_role') or 0)!=0 and isinstance(row.get('goals'),int): parts.append(f"Marcó {row['goals']} gol"+('' if row['goals']==1 else 'es')+'.')
    y,m,d=str(player['birth_date'])[:10].split('-'); parts.append(f'Fecha de nacimiento registrada: {d}/{m}/{y}.')
    parts.append(f"Lugar de nacimiento documentado: {player['historical_birth_place_text']} ({player['historical_birth_state']}).")
    return ' '.join(parts)

def main()->None:
    snap=load(SNAP); reg=load(REG); queue=load(QUEUE); stage=load(STAGE); catalog=load(CATALOG); ctx=load(CONTEXT); cnames=country_names(catalog)
    russia_tids={int(t['source_id']) for t in snap['teams'] if int(t.get('league_id') or -1)==RUSSIA_LEAGUE_ID}
    assert TARGET_TEAM_ID in russia_tids
    before_fp=fingerprint(snap,russia_tids); assert before_fp==EXPECTED_RUSSIA_BEFORE,(before_fp,EXPECTED_RUSSIA_BEFORE)
    non_target=russia_tids-{TARGET_TEAM_ID}; non_target_before=fingerprint(snap,non_target); before_stats=stats(snap)
    originals=[x for x in snap['players'] if x.get('attributes') and not x.get('external_origin') and not x.get('creation_batch')]
    by={int(x['source_id']):x for x in snap['players']}; rb={int(x['source_id']):x for x in reg['players']}; qb={int(x['source_id']):x for x in queue['players']}
    club=next(c for c in stage['clubs'] if c['name']=='Spartak Moskva'); rows={int(r['resolved_source_id']):r for r in club['players']}
    assert set(P)==set(rows), (set(P)-set(rows),set(rows)-set(P))
    changes=[]; conflicts=[]; role_corrections=[]
    for sid,patch in P.items():
        player=by[sid]; row=rows[sid]; old_name=player.get('display_name'); old_role=int(player.get('primary_role') or 0); old_broad=player.get('broad_position'); old_dob=str(player.get('birth_date') or '')[:10] or None; old_birth=player.get('birth_country_id')
        if old_dob and old_dob!=patch['dob']:
            conflicts.append({'source_id':sid,'player':patch['name'],'field':'birth_date','prior':old_dob,'resolved':patch['dob'],'decision':'individual profile + independent corroboration wins','source_urls':[bdf_url(patch),'https://www.transfermarkt.com/ramiz-mamedov/profil/spieler/67117'] if sid==9495357 else [bdf_url(patch)]})
        first,surname=split_name(patch['name']); player['display_name']=patch['name'];player['first_name']=first;player['surname1']=surname;player['birth_date']=patch['dob']+'T00:00:00'
        # Historical-state separation: never back-project a modern successor state into birth_country_id.
        player.pop('birth_country_id',None); player['historical_birth_state']=patch['state'];player['birth_territory_country_id']=patch['territory'];player['historical_birth_place_text']=patch['place']
        player['historical_birth_place_source_url']=bdf_url(patch); player['historical_birth_place_source_label']='BDFutbol place + sovereign-state-at-birth normalization v0.44'
        player['birth_country_resolution']='historical_state_separated_no_modern_successor_backfill_v044'
        player['citizenship_country_ids_1993']=[];player['citizenship_1993_resolution']='unresolved_not_inferred_from_birth_or_later_profile_v044'
        if patch.get('nats') is not None:
            player['profile_nationality_country_ids']=[int(x) for x in patch['nats']]
            if len(patch['nats'])>1: player['secondary_nationality_country_id']=int(patch['nats'][1])
            else: player.pop('secondary_nationality_country_id',None)
        # Preserve legacy gameplay identity, but explicitly mark it as distinct from 1993 citizenship.
        if player.get('international_country_id') is None:
            player['nationality_resolution']='1993_gameplay_identity_unresolved_no_birthplace_default_v044'
        else:
            player['nationality_resolution']='legacy_gameplay_identity_retained_separate_from_1993_citizenship_v044'
        hist=selection_history(player,patch); player['represented_selection_history']=hist
        player['represented_selection_country_ids']=list(dict.fromkeys(int(x['country_id']) for x in hist if x.get('country_id') is not None))
        sel93=[int(x['country_id']) for x in hist if x.get('country_id') is not None and int(x.get('from_year') or 9999)<=1993<=int(x.get('to_year') or -1)]
        player['represented_selection_country_ids_1993']=list(dict.fromkeys(sel93))
        player['selection_resolution']='source_backed_history_separate_from_citizenship_v044' if hist else 'selection_history_unresolved_v044'
        player['name_transliterations']={'bdfutbol_squad':row.get('bdfutbol_name'),'bdfutbol_profile':patch['name'],'project_display_before_v044':old_name,'project_display_v044':patch['name']}
        player['transliteration_resolution']='source_aliases_preserved_no_identity_merge_on_spelling_alone_v044'
        player['bdfutbol_id']=patch['bdf'];player['bdfutbol_url']=bdf_url(patch);player['historical_profile_source']='BDFutbol individual profile + Russia historical-state review v0.44';player['historical_profile_source_url']=bdf_url(patch);player['bdfutbol_squad_url']=BDF_TEAM
        if patch.get('height') is not None: player['height_cm']=patch['height']
        if patch.get('weight') is not None: player['weight_kg']=patch['weight']
        if patch.get('role') is not None: player['primary_role']=int(patch['role'])
        new_role=int(player.get('primary_role') or 0); player['broad_position']=ROLE_TO_BROAD[new_role];player['role_ratings']=role_ratings(new_role)
        label,psource,purl,review=position_label(player,patch);player['historical_position_1993_94']=label;player['historical_position_source']=psource;player['historical_position_source_url']=purl;player['source_profile_position']=patch['pos'] or None;player['profile_position_precision']=patch['precision'];player['profile_review_required']=review
        if new_role!=old_role or player['broad_position']!=old_broad:
            reattribute(player,new_role,originals,sid); role_corrections.append({'source_id':sid,'player':patch['name'],'role_before':old_role,'role_after':new_role,'broad_before':old_broad,'broad_after':player['broad_position'],'reason':patch.get('note') or patch['pos']})
        if patch.get('note'): player['historical_profile_source_note']=patch['note']
        player['historical_club_1994']='Spartak Moskva';player['historical_data_source']='BDFutbol 1993-94 + individual profiles + targeted international history v0.44'
        text=biography(player,row); evidence={'season':'1993-94','club':'Spartak Moskva','appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
        player['historical_biography_1993_94']=text;player['historical_biography_source_url']=bdf_url(patch);player['historical_biography_source_label']='BDFutbol Spartak Moskva deep v0.44';player['historical_biography_evidence']=evidence;player['historical_biography_status']='source_backed_season_summary';player['historical_biography_staged_clubs']=['Spartak Moskva'];player['historical_biographies_1993_94']=[{'club':'Spartak Moskva','text':text,'source_url':bdf_url(patch),'evidence':evidence}]
        # Stage mirrors the separation instead of collapsing country concepts.
        row.update({'resolved_display_name':player['display_name'],'resolved_primary_role':new_role,'resolved_exact_position':player['historical_position_1993_94'],'resolved_birth_date':player['birth_date'],'resolved_country_id':player.get('international_country_id'),'resolved_birth_country_id':None,'resolved_birth_territory_country_id':patch['territory'],'resolved_birth_state':patch['state'],'resolved_birth_place_text':patch['place'],'citizenship_1993_resolution':player['citizenship_1993_resolution'],'represented_selection_country_ids':player['represented_selection_country_ids'],'name_transliterations':player['name_transliterations'],'individual_profile_source_url':bdf_url(patch),'bdfutbol_id':patch['bdf'],'source_profile_position':patch['pos'] or None,'position_source':player['historical_position_source'],'position_source_url':player['historical_position_source_url'],'profile_source':player['historical_profile_source'],'profile_source_url':bdf_url(patch)})
        if patch.get('note'): row['profile_source_note']=patch['note']
        # Registry/photo queue: profile identity/photo readiness only; country stays gameplay identity and is never inferred from birth.
        base={'display_name':player['display_name'],'first_name':player.get('first_name'),'surname1':player.get('surname1'),'birth_date':patch['dob'],'country_id':player.get('international_country_id'),'country_name':cnames.get(int(player.get('international_country_id') or 0)),'broad_position':player['broad_position'],'team_id':TARGET_TEAM_ID,'team_name':'Spartak Moskva','historical_position_1993_94':player['historical_position_1993_94'],'historical_club_1994':'Spartak Moskva','historical_birth_place_text':patch['place']+' ('+patch['state']+')','historical_birth_state':patch['state'],'birth_territory_country_id':patch['territory'],'citizenship_1993_resolution':player['citizenship_1993_resolution'],'represented_selection_country_ids':player['represented_selection_country_ids'],'name_transliterations':player['name_transliterations'],'individual_profile_source':player['historical_profile_source'],'individual_profile_source_url':bdf_url(patch),'bdfutbol_search_name':player['display_name'],'bdfutbol_id':patch['bdf'],'bdfutbol_url':bdf_url(patch),'profile_review_required':review}
        for store,idx in ((reg,rb),(queue,qb)):
            # These stores track players created by the historical import. Canonical players
            # that pre-date the import (e.g. Cherchesov/Popov/Radchenko) must never be
            # inserted merely because this deep pass resolved a BDFutbol profile/photo.
            obj=idx.get(sid)
            if obj is None:
                continue
            old_photo=obj.get('photo_status'); old_gate=obj.get('duplicate_check'); obj.update(base)
            obj['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'
            obj['duplicate_check']=old_gate or 'exact_name_birthdate_source_profile_gate_v044'
            obj.setdefault('photo_filename',f'{sid}.jpg')
        changes.append({'source_id':sid,'display_name_before':old_name,'display_name_after':player['display_name'],'birth_date_before':old_dob,'birth_date_after':patch['dob'],'birth_country_id_before':old_birth,'birth_country_id_after':None,'historical_birth_state':patch['state'],'birth_territory_country_id':patch['territory'],'role_before':old_role,'role_after':new_role,'bdfutbol_id':patch['bdf'],'selection_country_ids':player['represented_selection_country_ids']})
    # Extend the global policy document rather than encoding Russia-only behavior in a one-off script.
    ctx['historical_birth_state_policy']={
      'rule':'Place of birth, sovereign state at birth, 1993 citizenship/nationality and represented selection are independent facts.',
      'ussr':'For births before dissolution in Soviet territory, historical_birth_state=USSR and modern successor territory may be stored in birth_territory_country_id; birth_country_id is not backfilled to the successor state.',
      'other_historical_states':'The same rule applies to states such as the German Democratic Republic; modern territorial country IDs are lookup context only.',
      'no_default':'Club, surname, birthplace or later nationality must never auto-assign 1993 citizenship or represented selection.'}
    ctx['transliteration_policy']={
      'rule':'Keep source spellings/romanizations as aliases and choose a project display form without treating spelling variation as a separate person.',
      'identity_gate':'Never merge identities on transliteration similarity alone; require stable evidence such as profile URL/ID, date of birth and club/season context.',
      'example':'Pogodin (BDF squad) and Serhiy Anatoliyovych Pohodin (BDF profile) are one source-backed identity with both forms preserved.'}
    after_stats=stats(snap); non_target_after=fingerprint(snap,non_target); assert non_target_before==non_target_after
    after_fp=fingerprint(snap,russia_tids); assert after_fp!=before_fp
    # Exact registry/queue identity synchronization remains a hard invariant.
    assert len({int(x['source_id']) for x in reg['players']})==len(reg['players']); assert len({int(x['source_id']) for x in queue['players']})==len(queue['players']); assert {int(x['source_id']) for x in reg['players']}=={int(x['source_id']) for x in queue['players']}
    dump(SNAP,snap);dump(REG,reg);dump(QUEUE,queue);dump(STAGE,stage);dump(CONTEXT,ctx)
    # Current BDF squad has four additional zero-appearance/call-up names outside the pinned 33-row staging. Keep them as an explicit source-drift review, not an automatic roster mutation.
    source_drift={'source_url':BDF_TEAM,'pinned_staging_rows':33,'current_page_additional_names':['Shmykov','Masalitin','Ternavskiy','Alenichev'],'decision':'do_not_auto_add_in_v044','reason':'Current BDF page differs from the pinned staging snapshot; reconcile transfer/call-up timing before changing the 1993 roster cardinality.'}
    audit={'schema_version':1,'checkpoint':CHECKPOINT,'status':'pass','target_club':'Spartak Moskva','profiles_curated':len(P),'profile_stats_before':before_stats,'profile_stats_after':after_stats,
      'russia_integrity':{'previous_checkpoint_sha256':EXPECTED_RUSSIA_BEFORE,'before_sha256':before_fp,'after_sha256':after_fp,'changed_intentionally':True,'non_target_clubs_before_sha256':non_target_before,'non_target_clubs_after_sha256':non_target_after,'non_target_clubs_unchanged':True},
      'historical_identity_policy':{'birth_state_separated':True,'modern_successor_birth_backfill':False,'citizenship_1993_separate':True,'represented_selection_separate':True,'transliterations_preserved':True},
      'identity_registry':{'created_profiles_updated':30,'canonical_preexisting_enriched_not_registered':[2705,515,517],'registry_photo_queue_synchronised':True},
      'profiles':{'changes':changes,'role_corrections':role_corrections,'bdfutbol_profiles_resolved':sum(bool(x.get('bdf')) for x in P.values()),'historical_state_births':dict(Counter(x['state'] for x in P.values())),'selection_history_profiles':sum(bool(x.get('selections')) for x in P.values())},
      'source_conflicts':conflicts,'source_drift':source_drift,'next_front':['Rotor Volgograd','Dynamo Moskva','Tekstilshchik Kamyshin','Lokomotiv Moskva','Spartak Vladikavkaz','Torpedo Moskva','Uralmash','CSKA Moskva','KAMAZ','Zhemchuzhina Sochi','Dynamo Stavropol','Lokomotiv Nizhny Novgorod','Krylia Sovetov','Luch Vladivostok','Okean Nakhodka','Rostselmash','Asmaral Moskva']}
    dump(DATA/'historical_profiles_metadata_audit_v044.json',audit)
    dump(DATA/'russia_source_conflicts_v044.json',{'checkpoint':CHECKPOINT,'status':'pass','conflicts':conflicts,'source_drift':source_drift,'policy':audit['historical_identity_policy']})
    dump(DATA/'russia_deepening_queue_v044.json',{'schema_version':1,'checkpoint':CHECKPOINT,'completed_clubs':['Spartak Moskva'],'queue':audit['next_front'],'next_club':'Rotor Volgograd','russia_players_total':before_stats['players'],'russia_previous_checkpoint_sha256':EXPECTED_RUSSIA_BEFORE,'non_target_clubs_unchanged':True})
    dump(DATA/'historical_biographies_audit_v044.json',{'checkpoint':CHECKPOINT,'club':'Spartak Moskva','profiles_considered':len(P),'source_backed_biographies':len(P),'status':'pass'})
    print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
