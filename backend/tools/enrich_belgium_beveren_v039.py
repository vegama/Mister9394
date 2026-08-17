from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import ROLE_TO_BROAD, ROLE_TO_LABEL, comparable, profile_gap_stats, role_ratings  # noqa:E402
from tools.review_created_player_profiles import materialise_attributes  # noqa:E402

DATA=ROOT/'data'/'football9394'
SNAP=DATA/'historical_snapshot.json'; REG=DATA/'created_players_registry.json'; QUEUE=DATA/'bdfutbol_photo_queue.json'; STAGE=DATA/'belgium_1993_94_roster_staging.json'
BDF_TEAM='https://www.bdfutbol.com/en/t/t1993-9412039.html'
TM_TEAM='https://www.transfermarkt.com/ksk-beveren-2010-/kader/verein/1073/saison_id/1993/plus/0/galerie/0'
TEAM_ID=9352002
COUNTRY_NAME={3:'Países Bajos',17:'Bélgica',37:'Eslovenia',52:'Lituania',59:'Nigeria',88:'Zaire',91:'Guinea'}
ROLE_ES={0:'Portero',1:'Lateral derecho',2:'Lateral izquierdo',3:'Defensa central',4:'Defensa central',5:'Líbero',6:'Mediocentro defensivo',7:'Centrocampista',8:'Mediapunta',9:'Interior derecho',10:'Interior derecho',11:'Extremo derecho',12:'Extremo derecho',13:'Interior izquierdo',14:'Interior izquierdo',15:'Extremo izquierdo',16:'Extremo izquierdo',17:'Delantero centro'}

# BDF individual pages are the primary identity/DOB/birth/measurement source.
# Transfermarkt season data specializes roles when the identity is unambiguous.
# Two conflicts are deliberately retained for review: Victor Diagne's career-position mismatch,
# and the Juha/Jani Jussila identity/position conflation in modern squad databases.
def p(name:str,dob:str,nat:list[int],birth:int|None,place:str|None,role:int,pos:str,bdf:str,
      height:int|None=None,weight:int|None=None,precision:str='exact',note:str|None=None) -> dict[str,Any]:
    return dict(club='Beveren',name=name,dob=dob,nat=nat,birth_country=birth,place=place,role=role,pos=pos,bdf=bdf,
                height=height,weight=weight,precision=precision,note=note)

P:dict[int,dict[str,Any]]={
9496017:p('Geert de Vlieger','1971-10-16',[17],17,'Dendermonde',0,'Goalkeeper','90763',185,80),
9496022:p('Carl Massagie','1965-03-06',[17],17,None,3,'Centre-Back','68586',185,None,note='Transfermarkt corroborates centre-back and Belgian citizenship; BDFutbol supplies exact DOB and Belgian birth country.'),
9496011:p('Hans Belligh','1965-06-06',[17],17,None,2,'Left-Back','68905',174,None),
9494182:p('Chidi Nwanu','1967-01-01',[59],59,'Port Harcourt',3,'Centre-Back','99668',178,None),
9496021:p('Julien Lodders','1962-10-30',[17],17,None,3,'Defender','69335',precision='broad_only',note='Historical sources consistently say defender but do not safely resolve a 1993-94 side/centre subtype.'),
9496013:p('Jacky Boonen','1968-04-09',[17],17,'Dilsen',14,'Left Midfield','69127',173,None),
9496025:p('Dirk Thoelen','1968-05-15',[17],17,None,7,'Midfielder','66365',178,None,precision='broad_only'),
9496030:p('Hervé Van Overtvelt','1971-10-22',[17],17,None,7,'Midfielder','68861',precision='broad_only'),
9496029:p('Maurice van Ham','1966-04-25',[3],3,None,7,'Midfielder','63605',178,None,precision='broad_only'),
9496027:p('Marc Van Britsom','1966-01-19',[17],17,'Sint Pauwels',7,'Midfielder','302339',170,64,precision='broad_only'),
9496026:p('Sašo Udovič','1968-12-12',[37],37,'Ljubljana',17,'Centre-Forward','702027',180,85),
9496028:p('Pascal van Gheem','1968-02-28',[17],17,None,0,'Goalkeeper','69667'),
9496032:p('Dirk Volckerick','1968-06-26',[17],17,None,5,'Sweeper','69332',precision='source_conflict_review',note='Transfermarkt consistently classifies Volckerick as sweeper in adjacent Beveren seasons, while BDFutbol labels him midfielder. Sweeper is retained with explicit review instead of silently treating the conflict as exact.'),
9496024:p('Souleymane Oulare','1972-10-16',[91],91,'Conakry',17,'Centre-Forward','2524',182,80,note='BDFutbol lists 182 cm; Transfermarkt lists 180 cm. BDFutbol measurement is retained and the position/citizenship are cross-checked.'),
9496012:p('Marnik Bogaerts','1967-04-16',[17],17,None,17,'Forward','69336',175,None,precision='broad_only'),
9496015:p('Gary Colling','1970-02-15',[17],17,None,17,'Forward','69666',precision='broad_only'),
9496023:p('Peter Meeusen','1973-09-11',[17],17,None,1,'Right-Back','66439'),
9496020:p('Andy Janssens','1971-12-12',[17],17,None,7,'Midfielder','69331',180,None,precision='broad_only'),
9496018:p('Yves Essende-Liombi','1968-08-20',[88],88,'Kinshasa (Zaire)',17,'Centre-Forward','69543',note='BDFutbol uses modern DR Congo for the birthplace; Transfermarkt identifies him as a former Zaire international. The 1993-94 country field is frozen to Zaire.'),
9496031:p('Stefan van Rumst','1972-01-13',[17],17,None,17,'Forward','69668',precision='broad_only'),
9496016:p('Tomas Daumantas','1975-08-30',[52,17],52,'Plungė',8,'Attacking Midfield','69364',182,None,note='Lithuania is already an independent state in 1993; later Belgian citizenship is retained as secondary rather than back-projecting Belgium as primary.'),
9496019:p('Jurgen Heymans','1973-04-05',[17],17,None,7,'Midfielder','68656',177,None,precision='broad_only'),
9496014:p('Koen Caluwé','1975-04-23',[17],17,'Antwerp',2,'Left-Back','68874',179,74),
}


def load(path:Path): return json.loads(path.read_text(encoding='utf-8'))
def dump(path:Path,obj:Any): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split_name(name:str):
    parts=name.split(); return (None,name) if len(parts)==1 else (' '.join(parts[:-1]),parts[-1])
def url(patch:dict[str,Any])->str: return f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"

def reattribute(player:dict[str,Any],role:int,originals:list[dict[str,Any]],sid:int)->None:
    a,b=comparable(originals,ROLE_TO_BROAD[role],int(player.get('overall') or 70),sid)
    player['attributes']=materialise_attributes(int(player.get('overall') or 70),a,b)
    player['attribute_source']='fixed_source_comparable_role_correction_0.39'
    player['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]

def apply_profile(player:dict[str,Any],patch:dict[str,Any],originals:list[dict[str,Any]])->dict[str,Any]:
    sid=int(player['source_id']); old_role=int(player.get('primary_role') or 0); old_broad=player.get('broad_position'); old_nat=player.get('international_country_id')
    first,surname=split_name(patch['name']); player['display_name']=patch['name']; player['first_name']=first; player['surname1']=surname
    player['birth_date']=patch['dob']+'T00:00:00'
    if patch.get('birth_country') is not None: player['birth_country_id']=int(patch['birth_country'])
    player['international_country_id']=int(patch['nat'][0]); player['profile_nationality_country_ids']=[int(x) for x in patch['nat']]
    if len(patch['nat'])>1: player['secondary_nationality_country_id']=int(patch['nat'][1])
    else: player.pop('secondary_nationality_country_id',None)
    player['historical_birth_place_text']=patch.get('place'); player['historical_birth_place_source_url']=url(patch); player['historical_birth_place_source_label']='BDFutbol individual profile / historical-state policy v0.39'
    player['bdfutbol_id']=str(patch['bdf']); player['bdfutbol_url']=url(patch)
    if patch.get('height') is not None: player['height_cm']=int(patch['height'])
    if patch.get('weight') is not None: player['weight_kg']=int(patch['weight'])
    role=int(patch['role']); player['primary_role']=role; player['broad_position']=ROLE_TO_BROAD[role]; player['role_ratings']=role_ratings(role)
    precision=patch.get('precision','exact'); player['profile_position_precision']=precision; player['source_profile_position']=patch['pos']; player['profile_review_required']=precision!='exact'
    if precision=='broad_only':
        player['historical_position_1993_94']=patch['pos']+' (exact role unresolved)'; player['historical_position_source']='BDFutbol + Transfermarkt broad position only v0.39'
    elif precision=='source_conflict_review':
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]+' (source conflict: review retained)'; player['historical_position_source']='Season-specific historical evidence with conflicting modern profile v0.39'
    else:
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]; player['historical_position_source']='BDFutbol individual profile + Transfermarkt 1993-94 specialist role v0.39'
    player['historical_position_source_url']=TM_TEAM if role!=0 else url(patch)
    player['historical_profile_source']='BDFutbol individual profile + Transfermarkt 1993-94 season cross-check v0.39'
    player['historical_profile_source_url']=url(patch); player['historical_club_1994']='Beveren'; player['historical_data_source']='BDFutbol 1993-94 + specialist profile cross-check v0.39'; player['bdfutbol_squad_url']=BDF_TEAM
    if patch.get('note'): player['historical_profile_source_note']=patch['note']
    if role!=old_role or player['broad_position']!=old_broad: reattribute(player,role,originals,sid)
    return {'source_id':sid,'display_name':player['display_name'],'role_before':old_role,'role_after':role,'nat_before':old_nat,'nat_after':player.get('international_country_id'),'precision':precision}

def ensure_stage(stage:dict[str,Any],player:dict[str,Any],patch:dict[str,Any])->None:
    club=next(c for c in stage['clubs'] if c['name']=='Beveren')
    sid=int(player['source_id']); row=next((r for r in club['players'] if int(r.get('resolved_source_id') or -1)==sid),None)
    if row is None: raise RuntimeError(f'missing Beveren staging row {sid}')
    row.update({'resolved_display_name':player['display_name'],'resolved_primary_role':player['primary_role'],'resolved_exact_position':player['historical_position_1993_94'],
      'resolved_birth_date':player['birth_date'],'resolved_country_id':player.get('international_country_id'),'source_profile_position':patch['pos'],
      'profile_source':player['historical_profile_source'],'profile_source_url':player['historical_profile_source_url'],'position_source':player['historical_position_source'],
      'position_source_url':player['historical_position_source_url'],'resolved_birth_place_text':patch.get('place'),'individual_profile_source_url':player['historical_profile_source_url'],
      'bdfutbol_id':str(patch['bdf'])})
    if patch.get('note'): row['profile_source_note']=patch['note']

def sync_registry_queue(reg:dict[str,Any],queue:dict[str,Any],player:dict[str,Any],patch:dict[str,Any])->None:
    sid=int(player['source_id']); rb={int(x['source_id']):x for x in reg['players']}; qb={int(x['source_id']):x for x in queue['players']}
    base={'source_id':sid,'display_name':player['display_name'],'first_name':player.get('first_name'),'surname1':player.get('surname1'),'surname2':player.get('surname2'),
      'birth_date':str(player.get('birth_date') or '')[:10] or None,'country_id':player.get('international_country_id'),'country_name':COUNTRY_NAME.get(player.get('international_country_id')),
      'broad_position':player.get('broad_position'),'team_id':TEAM_ID,'team_name':'Beveren','origin':'historical_belgium_1993_94','source':'BDFutbol/Transfermarkt Beveren deep v0.39',
      'overall':player.get('overall'),'attribute_source':player.get('attribute_source'),'profile_review_required':bool(player.get('profile_review_required')),
      'historical_position_1993_94':player.get('historical_position_1993_94'),'historical_club_1994':'Beveren','historical_birth_place_text':patch.get('place'),
      'individual_profile_source':player.get('historical_profile_source'),'individual_profile_source_url':player.get('historical_profile_source_url'),
      'duplicate_check':'exact_name_birthdate_source_profile_gate_v039','matched_existing_id':None,'asset_filename':f'{sid}.jpg',
      'bdfutbol_id':str(patch['bdf']),'bdfutbol_url':url(patch),'bdfutbol_search_name':player['display_name']}
    if sid not in rb: reg['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=rb[sid].get('photo_status'); rb[sid].update(base); rb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'
    if sid not in qb: queue['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=qb[sid].get('photo_status'); qb[sid].update(base); qb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'

def biography(player:dict[str,Any],row:dict[str,Any])->str:
    role='Futbolista' if player.get('profile_position_precision')=='broad_only' else ROLE_ES.get(int(player.get('primary_role') or 0),'Futbolista')
    parts=[f'{role} de Beveren en la temporada 1993-94.']
    stats=[]
    for k,label in [('appearances','partidos'),('starts','como titular')]:
        if isinstance(row.get(k),int): stats.append(f"{row[k]} {label}")
    if isinstance(row.get('minutes'),int): stats.append(f"{row['minutes']:,}".replace(',','.')+' minutos')
    if stats: parts.append('En el registro liguero figura con '+', '.join(stats)+'.')
    if int(player.get('primary_role') or 0)!=0 and isinstance(row.get('goals'),int): parts.append(f"Marcó {row['goals']} gol"+('' if row['goals']==1 else 'es')+'.')
    d=str(player['birth_date'])[:10]; y,m,day=d.split('-'); parts.append(f'Fecha de nacimiento registrada: {day}/{m}/{y}.')
    if player.get('historical_birth_place_text'): parts.append('Lugar de nacimiento documentado: '+str(player['historical_birth_place_text'])+'.')
    return ' '.join(parts)

def main()->None:
    snap=load(SNAP); reg=load(REG); queue=load(QUEUE); stage=load(STAGE); before=profile_gap_stats(snap)
    originals=[x for x in snap['players'] if x.get('attributes') and not x.get('external_origin') and not x.get('creation_batch')]
    by={int(x['source_id']):x for x in snap['players']}; changes=[]
    missing=[sid for sid in P if sid not in by]
    if missing: raise RuntimeError(f'missing Beveren snapshot ids: {missing}')
    for sid,patch in P.items():
        changes.append(apply_profile(by[sid],patch,originals)); ensure_stage(stage,by[sid],patch); sync_registry_queue(reg,queue,by[sid],patch)
    club=next(c for c in stage['clubs'] if c['name']=='Beveren'); rows={int(r['resolved_source_id']):r for r in club['players'] if r.get('resolved_source_id') is not None}
    for sid in P:
        player=by[sid]; row=rows[sid]
        player['historical_club_spells_1993_94']=[{'club':'Beveren','team_id':TEAM_ID,'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}]
        player['historical_biography_1993_94']=biography(player,row); player['historical_biography_source_url']=row.get('profile_source_url'); player['historical_biography_source_label']='BDFutbol/Transfermarkt Beveren deep v0.39'; player['historical_biography_status']='source_backed_season_summary'
        player['historical_biography_evidence']={'season':'1993-94','club':'Beveren','appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
    after=profile_gap_stats(snap)
    reg_ids=[int(x['source_id']) for x in reg['players']]; q_ids=[int(x['source_id']) for x in queue['players']]
    if len(reg_ids)!=len(set(reg_ids)) or len(q_ids)!=len(set(q_ids)) or set(reg_ids)!=set(q_ids): raise RuntimeError('registry/queue identity integrity failure')
    if len(club['players'])!=23: raise RuntimeError(f'Beveren stage expected 23, got {len(club["players"])}')
    if after['Belgium']['missing_birth_date']>before['Belgium']['missing_birth_date']-22: raise RuntimeError('Beveren DOB reduction gate not met')
    conflict_names=['Dirk Volckerick']
    audit={'schema_version':1,'checkpoint':'0.39.0-belgium-beveren-deep','status':'pass','profile_gaps_before':before,'profile_gaps_after':after,
      'profiles':{'curated_existing':len(P),'role_corrections':sum(c['role_before']!=c['role_after'] for c in changes),'review_required':sum(bool(by[s].get('profile_review_required')) for s in P),'changes':changes},
      'source_conflicts':[{'name':'Dirk Volckerick','decision':'retain sweeper classification with review flag','note':by[9496032]['historical_profile_source_note']}],
      'historical_country_policy':{'Yves Essende-Liombi':'Zaire (country_id 88) is used for 1993-94; modern DR Congo is not back-projected.','Tomas Daumantas':'Lithuania (country_id 52) is valid as an independent state in 1993; later Belgian citizenship is secondary.'},
      'photo_queue':{'bdf_individual_profiles_linked':len(P),'policy':'Every Beveren staging identity is linked to its BDF individual profile and marked ready_for_download; no portrait URL is fabricated.'},
      'identity_integrity':{'registry_rows':len(reg_ids),'queue_rows':len(q_ids),'registry_queue_match':set(reg_ids)==set(q_ids),'unique_registry_ids':len(reg_ids)==len(set(reg_ids))},
      'source_policy':['Continue Belgium club-by-club before Russia.','BDFutbol individual profiles anchor identity, DOB, birthplace and measurements.','Transfermarkt season/adjacent-season data specializes roles only when identity is safe.','Historical country naming is frozen to the 1993-94 context.','Conflicting data is review-flagged rather than silently overwritten.','No basketball 75/25 rule is used.']}
    dump(SNAP,snap); dump(REG,reg); dump(QUEUE,queue); dump(STAGE,stage)
    dump(DATA/'historical_profiles_metadata_audit_v039.json',audit); dump(DATA/'historical_metadata_gaps_v039.json',{'checkpoint':audit['checkpoint'],'gaps':after}); dump(DATA/'historical_biographies_audit_v039.json',{'checkpoint':audit['checkpoint'],'profiles_considered':len(P),'status':'pass'}); dump(DATA/'belgium_source_conflicts_v039.json',{'checkpoint':audit['checkpoint'],'status':'pass','conflicts':audit['source_conflicts']})
    print(json.dumps({'checkpoint':audit['checkpoint'],'curated_existing':len(P),'beveren_stage_rows':len(club['players']),'belgium_gaps_before':before['Belgium'],'belgium_gaps_after':after['Belgium'],'role_corrections':audit['profiles']['role_corrections'],'review_required':audit['profiles']['review_required']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
