from __future__ import annotations

from pathlib import Path
from typing import Any
from collections import Counter
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import ROLE_TO_BROAD, ROLE_TO_LABEL, comparable, profile_gap_stats, role_ratings  # noqa:E402
from tools.review_created_player_profiles import materialise_attributes  # noqa:E402

DATA = ROOT/'data'/'football9394'
SNAP = DATA/'historical_snapshot.json'
REG = DATA/'created_players_registry.json'
QUEUE = DATA/'bdfutbol_photo_queue.json'
STAGE = DATA/'belgium_1993_94_roster_staging.json'
CATALOG = DATA/'historical_source_catalog.json'

CHECKPOINT='0.42.0-belgium-waregem-lommel-deep'
VERSION='0.42'
CLUBS={
    'Waregem': {
        'team_id':466,
        'bdf_team':'https://www.bdfutbol.com/en/t/t1993-9410295.html',
        'tm_team':'https://www.transfermarkt.com/ksv-waregem/startseite/verein/2456/saison_id/1993',
        'expected_rows':27,
        'expected_dob_closed':23,
        'expected_nat_closed':20,
    },
    'Lommel': {
        'team_id':9352004,
        'bdf_team':'https://www.bdfutbol.com/en/t/t1993-9411701.html',
        'tm_team':'https://www.transfermarkt.com/kfc-lommel-sk/startseite/verein/718/saison_id/1993',
        'expected_rows':22,
        'expected_dob_closed':21,
        'expected_nat_closed':21,
    },
}

ROLE_ES={0:'Portero',1:'Lateral derecho',2:'Lateral izquierdo',3:'Defensa central',4:'Defensa central',5:'Líbero',6:'Mediocentro defensivo',7:'Centrocampista',8:'Mediapunta',9:'Interior derecho',10:'Interior derecho',11:'Extremo derecho',12:'Extremo derecho',13:'Interior izquierdo',14:'Interior izquierdo',15:'Extremo izquierdo',16:'Extremo izquierdo',17:'Delantero centro'}


def p(club:str,name:str,dob:str,nat:list[int],birth:int|None,place:str|None,role:int,pos:str,bdf:str,
      height:int|None=None,weight:int|None=None,precision:str='exact',position_source:str='bdf',
      note:str|None=None) -> dict[str,Any]:
    return dict(club=club,name=name,dob=dob,nat=nat,birth_country=birth,place=place,role=role,pos=pos,bdf=bdf,
                height=height,weight=weight,precision=precision,position_source=position_source,note=note)

# Identity, DOB, birthplace and measurements: BDFutbol individual profiles.
# Specialist role: only where BDF itself is specialist or Transfermarkt supplies a safe corroboration.
# Broad-only BDF labels are deliberately kept broad instead of preserving an unsupported squad-balance inference.
# Historical-state policy is explicit: Zaire is the 1993 international identity; Sabitov's 1968 Moscow birthplace is USSR, not Russia.
P:dict[int,dict[str,Any]]={
    # Waregem (27 real season rows; the incoming 23/20 figure is DOB/nationality gaps, not squad size).
    9496342:p('Waregem','Marc Huysmans','1961-04-05',[17],17,'Overpelt',0,'Goalkeeper','69497'),
    9496336:p('Waregem','Benny de Kneef','1965-06-12',[17],17,'Gent',3,'Defender','69691',precision='broad_only'),
    9496340:p('Waregem','Yvan Desloover','1963-07-29',[17],17,None,3,'Defender','69166',188,84,precision='broad_only'),
    9496341:p('Waregem','Rudy Ducoulombier','1964-08-27',[17],17,None,3,'Central','68593',187,None,note='BDFutbol position label Central is treated as centre-back in the project vocabulary.'),
    9496339:p('Waregem','Nick Descamps','1966-03-24',[17],17,None,7,'Midfielder','68602',precision='broad_only',note='BDFutbol identifies Descamps as midfielder; the previous left-back squad-balance inference is removed.'),
    9496338:p('Waregem','Frank Dekenne','1960-07-07',[17],17,'Waregem',7,'Midfielder','69356',precision='broad_only'),
    9496346:p('Waregem','Patrick Stalmans','1959-10-31',[17],17,None,7,'Midfielder','69693',precision='broad_only'),
    9496349:p('Waregem','Jude Vandelannoite','1973-02-14',[17],17,'Waregem',7,'Midfielder','68655',178,80,precision='broad_only'),
    9496343:p('Waregem','Hendrie Krüzen','1964-11-24',[3],3,'Almelo',15,'Left Winger','79841',184,None,position_source='tm',note='BDFutbol gives Forward; Transfermarkt 1993-94 club data specializes Krüzen as left winger.'),
    9495157:p('Waregem','Aurelio Vidmar','1967-02-03',[15],15,'Adelaide',17,'Centre-Forward','298',182,73,position_source='tm'),
    9496325:p('Waregem','Laurent Ballenghien','1969-12-15',[17],17,None,17,'Forward','69671',precision='broad_only'),
    9496350:p('Waregem','Franck Vandendriessche','1971-04-07',[17],17,'Waregem',0,'Goalkeeper','65813',185,78),
    9496332:p('Waregem','Marino Blancke','1970-09-14',[17],17,None,7,'Midfielder','69358',precision='broad_only',note='BDFutbol identifies Blancke as midfielder; the previous right-back inference is removed.'),
    9496333:p('Waregem','David Bossuyt','1975-01-23',[17],17,None,7,'Midfielder','69351',183,81,precision='broad_only'),
    9496337:p('Waregem','Sébastien De Meersman','1970-12-30',[17],17,None,15,'Left Winger','69310',position_source='tm',note='BDFutbol gives Forward; Transfermarkt specializes De Meersman as left winger.'),
    9496330:p('Waregem','Raymond Atteveld','1966-09-08',[3],3,'Amsterdam',3,'Centre-Back','79621',precision='source_conflict_review',position_source='tm',note='BDFutbol profile says Midfielder while Transfermarkt 1993-94 Waregem data lists Centre-Back. Season-specific role is retained as centre-back and the conflict stays review-flagged.'),
    9494227:p('Waregem','Nacer Abdellah','1966-03-03',[56],56,'Sidi Slimane',3,'Defender','7025',178,70,precision='broad_only'),
    9496351:p('Waregem','Dirk Vanderbeken','1965-12-30',[17],17,None,7,'Midfielder','69352',164,63,precision='broad_only',note='BDFutbol identifies Vanderbeken as midfielder; the previous right-back inference is removed.'),
    9496335:p('Waregem','Hans Christiaens','1964-01-12',[17],17,'Zele',17,'Centre-Forward','69692',position_source='tm'),
    9496331:p('Waregem','Henri Mbala Balenga Mukuka','1966-12-17',[88],88,'DR Congo',17,'Forward','69509',precision='broad_only',note='BDFutbol uses modern DR Congo. The 1993 football/nationality identity is frozen to Zaire through country id 88.'),
    9496329:p('Waregem','Flórián Urbán','1968-07-29',[93],93,'Budapest',6,'Defensive Midfield','68620',182,82,position_source='tm'),
    9496348:p('Waregem','Chris van Geem','1971-07-07',[17],17,'Gent',3,'Defender','85993',181,None,precision='broad_only'),
    9496345:p('Waregem','Ravil Rufailovich Sabitov','1968-03-08',[40],None,'Moscow (USSR)',2,'Left back','69694',179,74,note='BDFutbol uses the modern Russia birthplace label. Moscow in 1968 was USSR; Russia is stored separately as the 1993 citizenship/football identity, never back-projected into birth_country_id.'),
    9496344:p('Waregem','Patrick Pascal Onya','1974-12-24',[59],59,'Bauchi',17,'Forward','66327',precision='broad_only',note='BDFutbol identifies Onya as forward; the previous centre-back inference is removed.'),
    9496334:p('Waregem','Fangio Buyse','1974-09-27',[17],17,'Deinze',7,'Midfielder','69354',186,74,precision='broad_only'),
    9496347:p('Waregem','Eddy Syx','1974-10-15',[17],17,None,3,'Defender','69353',177,71,precision='broad_only',note='BDFutbol identifies Syx as defender; the previous right-midfield inference is removed.'),
    9496324:p('Waregem','Jean-Marie Abeels','1962-11-18',[17],17,None,7,'Midfielder','69296',precision='broad_only'),

    # Lommel (22 real season rows; incoming 21/21 is DOB/nationality gaps).
    9496212:p('Lommel','Jacky Mathijssen','1963-07-20',[17],17,'Dilsen-Stokkem',0,'Goalkeeper','64767'),
    9496213:p('Lommel','Jean-Claude Mukanya Kabeya','1968-05-01',[88],88,'DR Congo',3,'Centre-Back','62913',187,None,position_source='tm',note='BDFutbol gives Defender; adjacent-season Transfermarkt data specializes Mukanya as centre-back. Country id 88 is presented as Zaire in the 1993 context.'),
    9496207:p('Lommel','Robert Gijbels','1962-02-19',[17],17,None,2,'Left back','69674'),
    9496219:p('Lommel','Ronny van Geneugden','1968-08-17',[17],17,'Hasselt',7,'Midfielder','63498',183,None,precision='broad_only',note='BDFutbol identifies Van Geneugden as midfielder; the previous centre-back inference is removed.'),
    9496220:p('Lommel','Harm van Veldhoven','1962-09-28',[3],3,'Luyksgestel',7,'Midfielder','79162',180,None,precision='broad_only',note='BDFutbol identifies Van Veldhoven as midfielder; the previous left-back inference is removed.'),
    9496221:p('Lommel','Vital Vanaken','1962-03-09',[17],17,None,7,'Midfielder','69146',186,78,precision='broad_only'),
    9496222:p('Lommel','Tom Vandervee','1970-09-19',[17],17,'Lommel',7,'Midfielder','68464',175,None,precision='broad_only'),
    9496204:p('Lommel','Gert Cannaerts','1963-07-05',[17],17,None,7,'Midfielder','68641',187,None,precision='broad_only'),
    9496223:p('Lommel','Ronny Vangompel','1968-07-09',[17],17,None,7,'Midfielder','69495',precision='broad_only'),
    9496216:p('Lommel','Mathieu Peeters','1965-04-10',[17],17,'Bree',17,'Forward','69143',187,80,precision='broad_only'),
    6792:p('Lommel','Frank Berghuis','1967-05-02',[3],3,'Nunspeet',15,'Left Winger','41864',182,None,position_source='tm',note='BDFutbol gives Forward; Transfermarkt identifies Berghuis as a left winger. Existing source-backed 77 kg is preserved because BDFutbol does not provide a replacement weight here.'),
    9496215:p('Lommel','Bart Peeters','1974-03-04',[17],17,None,0,'Goalkeeper','68582',note='Identity correction: BDFutbol explicitly identifies Bart Peeters as goalkeeper; the previous right-back inference is invalid.'),
    9496203:p('Lommel',"John Buana N'Galula",'1968-06-23',[88],88,'Kinshasa (DR Congo)',3,'Centre-Back','69493',position_source='tm',note='BDFutbol gives Defender; external career sources confirm a Zaire international and Transfermarkt specializes centre-back. Country id 88 is Zaire for the 1993 context.'),
    9496217:p('Lommel','Daniël Scavone','1972-09-03',[17],17,'Lommel',3,'Centre-Back','66244',position_source='tm',note='BDFutbol uses Central; Transfermarkt independently confirms centre-back (with left-back secondary). The previous right-midfield inference is removed.'),
    9496209:p('Lommel','Marc Hendrikx','1974-07-02',[17],17,'Hamont',13,'Left Midfield','700230',184,None,position_source='tm',note='BDFutbol lists right back / left back / midfielder. Transfermarkt repeatedly identifies Hendrikx as left midfield; the previous forward inference is removed.'),
    9496208:p('Lommel','Wilhelmus Edwin Gorter','1963-07-06',[3],3,'Den Haag',7,'Midfielder','54401',178,None,precision='broad_only',note='BDFutbol identifies Gorter as midfielder; the previous forward inference is removed.'),
    9496211:p('Lommel','Frank Machiels','1970-06-16',[17],17,'Mol',3,'Centre-Back','66174',185,None,position_source='tm',note='BDFutbol uses Central; Transfermarkt independently confirms centre-back.'),
    9496214:p('Lommel',"Nela Petrus N'Ganzadi Kimonekene",'1968-08-27',[88],88,'DR Congo',17,'Forward','69494',precision='broad_only',note='BDFutbol labels the country Congo; FootballDatabase/Transfermarkt identify DR Congo. For 1993 the corresponding football identity is Zaire (country id 88).'),
    9496205:p('Lommel','Dimitri De Condé','1975-01-07',[17],17,'Hasselt',7,'Midfielder','701452',177,71,precision='broad_only',note='BDFutbol identifies De Condé as midfielder; the previous forward inference is removed.'),
    9496210:p('Lommel','Bonide Isumgampala','1968-04-08',[116],116,None,7,'Midfielder','69675',precision='broad_only',note='BDFutbol identifies Burundi nationality/birth country and a broad midfielder role; the unsupported defensive-midfield specialization is removed.'),
    9496218:p('Lommel','Maarten Schops','1976-04-03',[17],17,'Leuven',7,'Midfielder','85877',180,None,precision='broad_only',note='BDFutbol identifies Schops as midfielder; the previous right-back inference is removed.'),
    9496206:p('Lommel','Bart Gijbels','1972-02-10',[17],17,None,17,'Forward','69676',precision='broad_only',note='BDFutbol identifies Bart Gijbels as forward; the previous left-back inference is removed.'),
}


def load(path:Path): return json.loads(path.read_text(encoding='utf-8'))
def dump(path:Path,obj:Any): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split_name(name:str):
    parts=name.split(); return (None,name) if len(parts)==1 else (' '.join(parts[:-1]),parts[-1])
def profile_url(patch:dict[str,Any])->str: return f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"

def country_names(catalog:dict[str,Any])->dict[int,str]:
    out={}
    for c in catalog.get('countries',[]):
        sid=int(c['source_id'])
        out[sid]=str(c.get('historical_name_1993') or c.get('name') or sid)
    return out


def reattribute(player:dict[str,Any],role:int,originals:list[dict[str,Any]],sid:int)->None:
    a,b=comparable(originals,ROLE_TO_BROAD[role],int(player.get('overall') or 70),sid)
    player['attributes']=materialise_attributes(int(player.get('overall') or 70),a,b)
    player['attribute_source']='fixed_source_comparable_role_correction_0.42'
    player['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]


def position_source_text(patch:dict[str,Any])->tuple[str,str]:
    bdf=profile_url(patch); club=CLUBS[patch['club']]
    precision=patch.get('precision','exact'); src=patch.get('position_source','bdf')
    if precision=='source_conflict_review':
        return ('Season-specific/individual historical evidence with explicit source conflict v0.42', club['tm_team'] if src=='tm' else bdf)
    if precision=='broad_only':
        return ('BDFutbol broad position; exact specialist role unresolved v0.42', bdf)
    if src=='tm':
        return ('BDFutbol individual profile + Transfermarkt specialist corroboration v0.42', club['tm_team'])
    return ('BDFutbol individual profile exact position v0.42', bdf)


def apply_profile(player:dict[str,Any],patch:dict[str,Any],originals:list[dict[str,Any]])->dict[str,Any]:
    sid=int(player['source_id']); old_role=int(player.get('primary_role') or 0); old_broad=player.get('broad_position'); old_nat=player.get('international_country_id')
    prior_club=player.get('historical_club_1994')
    prior_profile_source=player.get('historical_profile_source')
    prior_precision=player.get('profile_position_precision')
    preserve_prior_deep=(
        prior_precision=='exact'
        and bool(prior_profile_source)
        and prior_club not in {None,patch['club']}
        and patch.get('precision','exact')=='broad_only'
        and old_broad==ROLE_TO_BROAD[int(patch['role'])]
    )
    prior_position={k:player.get(k) for k in ['primary_role','broad_position','role_ratings','profile_position_precision','source_profile_position','profile_review_required','historical_position_1993_94','historical_position_source','historical_position_source_url','historical_profile_source','historical_profile_source_url','historical_profile_source_note','historical_club_1994']}
    first,surname=split_name(patch['name']); player['display_name']=patch['name']; player['first_name']=first; player['surname1']=surname
    player['birth_date']=patch['dob']+'T00:00:00'
    if patch.get('birth_country') is not None: player['birth_country_id']=int(patch['birth_country'])
    else: player.pop('birth_country_id',None)
    player['international_country_id']=int(patch['nat'][0]); player['profile_nationality_country_ids']=[int(x) for x in patch['nat']]
    if len(patch['nat'])>1: player['secondary_nationality_country_id']=int(patch['nat'][1])
    else: player.pop('secondary_nationality_country_id',None)
    player['historical_birth_place_text']=patch.get('place'); player['historical_birth_place_source_url']=profile_url(patch); player['historical_birth_place_source_label']='BDFutbol individual profile / historical-state policy v0.42'
    player['bdfutbol_id']=str(patch['bdf']); player['bdfutbol_url']=profile_url(patch)
    if patch.get('height') is not None: player['height_cm']=int(patch['height'])
    if patch.get('weight') is not None: player['weight_kg']=int(patch['weight'])
    role=int(patch['role']); player['primary_role']=role; player['broad_position']=ROLE_TO_BROAD[role]; player['role_ratings']=role_ratings(role)
    precision=patch.get('precision','exact'); player['profile_position_precision']=precision; player['source_profile_position']=patch['pos']; player['profile_review_required']=precision!='exact'
    if precision=='broad_only': player['historical_position_1993_94']=patch['pos']+' (exact role unresolved)'
    elif precision=='source_conflict_review': player['historical_position_1993_94']=ROLE_TO_LABEL[role]+' (source conflict: review retained)'
    else: player['historical_position_1993_94']=ROLE_TO_LABEL[role]
    ptext,purl=position_source_text(patch); player['historical_position_source']=ptext; player['historical_position_source_url']=purl
    club=CLUBS[patch['club']]
    player['historical_profile_source']='BDFutbol individual profile + targeted specialist cross-check v0.42'
    player['historical_profile_source_url']=profile_url(patch); player['historical_club_1994']=patch['club']; player['historical_data_source']='BDFutbol 1993-94 + targeted specialist cross-check v0.42'; player['bdfutbol_squad_url']=club['bdf_team']
    if patch.get('note'): player['historical_profile_source_note']=patch['note']
    if preserve_prior_deep:
        # A player can appear for multiple Belgian clubs in 1993-94. A broad label from the
        # current-club page must not erase a specialist role already source-backed earlier.
        for key,value in prior_position.items():
            if value is None:
                player.pop(key,None)
            else:
                player[key]=value
        role=int(player['primary_role']); precision=str(player.get('profile_position_precision') or 'exact')
    elif role!=old_role or player['broad_position']!=old_broad:
        reattribute(player,role,originals,sid)
    clubs=list(player.get('historical_clubs_1993_94') or [])
    for cname in [prior_club,patch['club']]:
        if cname and cname not in clubs: clubs.append(cname)
    player['historical_clubs_1993_94']=clubs
    return {'source_id':sid,'club':patch['club'],'display_name':player['display_name'],'role_before':old_role,'role_after':role,'nat_before':old_nat,'nat_after':player.get('international_country_id'),'precision':precision,'preserved_prior_deep_profile':preserve_prior_deep}


def ensure_stage(stage:dict[str,Any],player:dict[str,Any],patch:dict[str,Any])->None:
    club=next(c for c in stage['clubs'] if c['name']==patch['club'])
    sid=int(player['source_id']); row=next((r for r in club['players'] if int(r.get('resolved_source_id') or -1)==sid),None)
    if row is None: raise RuntimeError(f"missing {patch['club']} staging row {sid}")
    row.update({'resolved_display_name':player['display_name'],'resolved_primary_role':player['primary_role'],'resolved_exact_position':player['historical_position_1993_94'],
      'resolved_birth_date':player['birth_date'],'resolved_country_id':player.get('international_country_id'),'source_profile_position':patch['pos'],
      'profile_source':player['historical_profile_source'],'profile_source_url':player['historical_profile_source_url'],'position_source':player['historical_position_source'],
      'position_source_url':player['historical_position_source_url'],'resolved_birth_place_text':patch.get('place'),'individual_profile_source_url':player['historical_profile_source_url'],
      'bdfutbol_id':str(patch['bdf'])})
    if patch.get('note'): row['profile_source_note']=patch['note']


def sync_registry_queue(reg:dict[str,Any],queue:dict[str,Any],player:dict[str,Any],patch:dict[str,Any],cnames:dict[int,str],preserve_gate:bool=False)->None:
    sid=int(player['source_id']); rb={int(x['source_id']):x for x in reg['players']}; qb={int(x['source_id']):x for x in queue['players']}; club=CLUBS[patch['club']]
    base={'source_id':sid,'display_name':player['display_name'],'first_name':player.get('first_name'),'surname1':player.get('surname1'),'surname2':player.get('surname2'),
      'birth_date':str(player.get('birth_date') or '')[:10] or None,'country_id':player.get('international_country_id'),'country_name':cnames.get(int(player.get('international_country_id') or 0)),
      'broad_position':player.get('broad_position'),'team_id':club['team_id'],'team_name':patch['club'],'origin':'historical_belgium_1993_94','source':f"BDFutbol/Transfermarkt {patch['club']} deep v0.42",
      'overall':player.get('overall'),'attribute_source':player.get('attribute_source'),'profile_review_required':bool(player.get('profile_review_required')),
      'historical_position_1993_94':player.get('historical_position_1993_94'),'historical_club_1994':patch['club'],'historical_birth_place_text':patch.get('place'),
      'individual_profile_source':player.get('historical_profile_source'),'individual_profile_source_url':player.get('historical_profile_source_url'),
      'duplicate_check':'exact_name_birthdate_source_profile_gate_v042','matched_existing_id':None,'asset_filename':f'{sid}.jpg',
      'bdfutbol_id':str(patch['bdf']),'bdfutbol_url':profile_url(patch),'bdfutbol_search_name':player['display_name']}
    if sid not in rb: reg['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=rb[sid].get('photo_status'); old_gate=rb[sid].get('duplicate_check'); rb[sid].update(base); rb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'
        if preserve_gate and old_gate: rb[sid]['duplicate_check']=old_gate
    if sid not in qb: queue['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=qb[sid].get('photo_status'); old_gate=qb[sid].get('duplicate_check'); qb[sid].update(base); qb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'
        if preserve_gate and old_gate: qb[sid]['duplicate_check']=old_gate


def biography(player:dict[str,Any],row:dict[str,Any],club:str)->str:
    role='Futbolista' if player.get('profile_position_precision')=='broad_only' else ROLE_ES.get(int(player.get('primary_role') or 0),'Futbolista')
    parts=[f'{role} de {club} en la temporada 1993-94.']; stats=[]
    for k,label in [('appearances','partidos'),('starts','como titular')]:
        if isinstance(row.get(k),int): stats.append(f"{row[k]} {label}")
    if isinstance(row.get('minutes'),int): stats.append(f"{row['minutes']:,}".replace(',','.')+' minutos')
    if stats: parts.append('En el registro liguero figura con '+', '.join(stats)+'.')
    if int(player.get('primary_role') or 0)!=0 and isinstance(row.get('goals'),int): parts.append(f"Marcó {row['goals']} gol"+('' if row['goals']==1 else 'es')+'.')
    d=str(player['birth_date'])[:10]; y,m,day=d.split('-'); parts.append(f'Fecha de nacimiento registrada: {day}/{m}/{y}.')
    if player.get('historical_birth_place_text'): parts.append('Lugar de nacimiento documentado: '+str(player['historical_birth_place_text'])+'.')
    return ' '.join(parts)


def main()->None:
    snap=load(SNAP); reg=load(REG); queue=load(QUEUE); stage=load(STAGE); catalog=load(CATALOG); cnames=country_names(catalog); before=profile_gap_stats(snap)
    originals=[x for x in snap['players'] if x.get('attributes') and not x.get('external_origin') and not x.get('creation_batch')]
    by={int(x['source_id']):x for x in snap['players']}; changes=[]; missing=[sid for sid in P if sid not in by]
    if missing: raise RuntimeError(f'missing Belgium snapshot ids: {missing}')
    for sid,patch in P.items():
        change=apply_profile(by[sid],patch,originals); changes.append(change); ensure_stage(stage,by[sid],patch); sync_registry_queue(reg,queue,by[sid],patch,cnames,bool(change.get('preserved_prior_deep_profile')))
    # Build source-backed season summaries from the canonical BDF staging rows.
    for clubname,meta in CLUBS.items():
        club=next(c for c in stage['clubs'] if c['name']==clubname)
        rows={int(r['resolved_source_id']):r for r in club['players'] if r.get('resolved_source_id') is not None}
        for sid,patch in P.items():
            if patch['club']!=clubname: continue
            player=by[sid]; row=rows[sid]
            spell={'club':clubname,'team_id':meta['team_id'],'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
            spells=[x for x in list(player.get('historical_club_spells_1993_94') or []) if x.get('club')!=clubname]
            spells.append(spell); player['historical_club_spells_1993_94']=spells
            current_text=biography(player,row,clubname)
            bios=list(player.get('historical_biographies_1993_94') or [])
            if not bios and player.get('historical_biography_1993_94') and player.get('historical_biography_evidence'):
                ev=player.get('historical_biography_evidence') or {}; prior_club=ev.get('club')
                if prior_club and prior_club!=clubname:
                    bios.append({'club':prior_club,'text':player['historical_biography_1993_94'],'source_url':player.get('historical_biography_source_url'),'evidence':ev})
            bios=[x for x in bios if x.get('club')!=clubname]
            current_ev={'season':'1993-94','club':clubname,'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
            bios.append({'club':clubname,'text':current_text,'source_url':row.get('profile_source_url'),'evidence':current_ev})
            player['historical_biographies_1993_94']=bios
            player['historical_biography_1993_94']=' '.join(x['text'] for x in bios)
            player['historical_biography_source_url']=row.get('profile_source_url'); player['historical_biography_source_label']=('Multiple source-backed club spells 1993-94' if len(bios)>1 else f'BDFutbol/Transfermarkt {clubname} deep v0.42'); player['historical_biography_status']='source_backed_season_summary'
            player['historical_biography_evidence']=({'season':'1993-94','clubs':[x['evidence'] for x in bios]} if len(bios)>1 else current_ev)
    after=profile_gap_stats(snap)
    reg_ids=[int(x['source_id']) for x in reg['players']]; q_ids=[int(x['source_id']) for x in queue['players']]
    if len(reg_ids)!=len(set(reg_ids)) or len(q_ids)!=len(set(q_ids)) or set(reg_ids)!=set(q_ids): raise RuntimeError('registry/queue identity integrity failure')
    for clubname,meta in CLUBS.items():
        club=next(c for c in stage['clubs'] if c['name']==clubname)
        if len(club['players'])!=meta['expected_rows']: raise RuntimeError(f'{clubname} stage expected {meta["expected_rows"]}, got {len(club["players"])}')
        if not all(r.get('resolved_birth_date') for r in club['players']): raise RuntimeError(f'{clubname} still has staging DOB gaps')
        if not all(r.get('resolved_country_id') is not None for r in club['players']): raise RuntimeError(f'{clubname} still has staging nationality gaps')
        if not all(r.get('bdfutbol_id') for r in club['players']): raise RuntimeError(f'{clubname} still has unlinked BDF identities')
    dob_expected=sum(x['expected_dob_closed'] for x in CLUBS.values()); nat_expected=sum(x['expected_nat_closed'] for x in CLUBS.values())
    if after['Belgium']['missing_birth_date'] != before['Belgium']['missing_birth_date']-dob_expected: raise RuntimeError('Waregem/Lommel DOB reduction gate not met')
    if after['Belgium']['missing_international_country_id'] != before['Belgium']['missing_international_country_id']-nat_expected: raise RuntimeError('Waregem/Lommel nationality reduction gate not met')
    conflicts=[{'source_id':c['source_id'],'display_name':c['display_name'],'club':c['club']} for c in changes if c['precision']=='source_conflict_review']
    audit={'schema_version':1,'checkpoint':CHECKPOINT,'status':'pass','profile_gaps_before':before,'profile_gaps_after':after,
      'profiles':{'curated_existing':len(P),'by_club':dict(Counter(x['club'] for x in P.values())),'role_corrections':sum(c['role_before']!=c['role_after'] for c in changes),'review_required':sum(bool(by[s].get('profile_review_required')) for s in P),'preserved_prior_deep_profiles':[c['source_id'] for c in changes if c.get('preserved_prior_deep_profile')],'changes':changes},
      'gap_closure':{'Waregem':{'incoming_missing_birth_date':23,'incoming_missing_nationality':20,'remaining_missing_birth_date':0,'remaining_missing_nationality':0,'season_rows':27},'Lommel':{'incoming_missing_birth_date':21,'incoming_missing_nationality':21,'remaining_missing_birth_date':0,'remaining_missing_nationality':0,'season_rows':22}},
      'source_conflicts':conflicts,
      'historical_country_policy':{
        'Zaire_1993':'Country source id 88 is the DR Congo state identity in the catalog but is rendered by historical_name_1993 as Zaire. Lommel/Waregem Congolese identities use Zaire for 1993 football context; modern DR Congo evidence remains source text, not a 1993 label.',
        'Sabitov_USSR':'Ravil Sabitov was born in Moscow in 1968. historical_birth_place_text is Moscow (USSR), birth_country_id is intentionally absent, and Russia country id 40 is stored only as 1993 citizenship/football identity.',
        'future_Russia':'Russia league remains untouched. The Russia pass must separate historical birthplace state, 1993 citizenship/nationality, represented selection and transliterations; USSR must never be auto-mapped to Russia.'},
      'photo_queue':{'bdf_individual_profiles_linked':len(P),'policy':'Every Waregem and Lommel season identity is linked to its BDF individual profile and marked ready_for_download unless an already bundled normalized portrait exists; no portrait URL is fabricated.'},
      'identity_integrity':{'registry_rows':len(reg_ids),'queue_rows':len(q_ids),'registry_queue_match':set(reg_ids)==set(q_ids),'unique_registry_ids':len(reg_ids)==len(set(reg_ids))},
      'source_policy':['Continue Belgium club-by-club before Russia.','BDFutbol individual profiles anchor identity, DOB, birthplace and measurements.','Broad BDF positions are never silently converted into unsupported specialist roles.','Transfermarkt is used only for safe specialist corroboration or explicitly review-flagged conflicts.','Historical country naming is separated from modern source labels.','No basketball 75/25 rule is used.'],
      'next_front':['RFC Liège','Cercle Brugge','Oostende','KV Mechelen','Gent','Lierse']}
    dump(SNAP,snap); dump(REG,reg); dump(QUEUE,queue); dump(STAGE,stage)
    dump(DATA/'historical_profiles_metadata_audit_v042.json',audit)
    dump(DATA/'historical_metadata_gaps_v042.json',{'checkpoint':CHECKPOINT,'gaps':after})
    dump(DATA/'historical_biographies_audit_v042.json',{'checkpoint':CHECKPOINT,'profiles_considered':len(P),'by_club':audit['profiles']['by_club'],'status':'pass'})
    dump(DATA/'belgium_source_conflicts_v042.json',{'checkpoint':CHECKPOINT,'status':'pass','conflicts':conflicts,'historical_country_policy':audit['historical_country_policy']})
    print(json.dumps({'checkpoint':CHECKPOINT,'curated_existing':len(P),'by_club':audit['profiles']['by_club'],'belgium_gaps_before':before['Belgium'],'belgium_gaps_after':after['Belgium'],'role_corrections':audit['profiles']['role_corrections'],'review_required':audit['profiles']['review_required'],'next_front':audit['next_front']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
