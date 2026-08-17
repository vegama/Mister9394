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
BDF_TEAM='https://www.bdfutbol.com/en/t/t1993-9410201.html'
TM_TEAM='https://www.transfermarkt.com/krc-genk/kader/verein/1184/saison_id/1993/plus/0/galerie/0'
TEAM_ID=462
COUNTRY_NAME={3:'Países Bajos',17:'Bélgica',20:'Bosnia-Herzegovina',31:'Croacia',42:'Ghana',55:'Malta',59:'Nigeria',62:'Brasil'}
ROLE_ES={0:'Portero',1:'Lateral derecho',2:'Lateral izquierdo',3:'Defensa central',4:'Defensa central',5:'Líbero',6:'Mediocentro defensivo',7:'Centrocampista',8:'Mediapunta',9:'Interior derecho',10:'Interior derecho',11:'Extremo derecho',12:'Extremo derecho',13:'Interior izquierdo',14:'Interior izquierdo',15:'Extremo izquierdo',16:'Extremo izquierdo',17:'Delantero centro'}

# BDF individual pages are the primary identity/DOB/birth/measurement source.
# BDF broad positions are not silently converted into specialist roles.
# Transfermarkt is used only for safe specialist corroboration (Suad Katana as sweeper).
# Former-Yugoslavia birthplaces retain the historical birth-state text and do not receive
# a modern successor-state birth_country_id. Citizenship/football identity remains separate.
def p(name:str,dob:str,nat:list[int],birth:int|None,place:str|None,role:int,pos:str,bdf:str,
      height:int|None=None,weight:int|None=None,precision:str='exact',note:str|None=None) -> dict[str,Any]:
    return dict(club='Genk',name=name,dob=dob,nat=nat,birth_country=birth,place=place,role=role,pos=pos,bdf=bdf,
                height=height,weight=weight,precision=precision,note=note)

P:dict[int,dict[str,Any]]={
9496109:p('Ronald Louis Gaspercic','1969-05-09',[17],17,'Genk',0,'Goalkeeper','2390',186,79),
9496122:p('Dirk Verwimp','1963-05-04',[17],17,None,3,'Defender','69103',precision='broad_only'),
9496111:p('Suad Katana','1969-04-06',[20],None,'Sarajevo (Yugoslavia)',5,'Sweeper','99920',178,None,note='BDFutbol uses the modern Bosnia-Herzegovina birth-country label. The 1969 birthplace is retained as Yugoslavia; Bosnia-Herzegovina is stored as the 1993 football/citizenship identity. Transfermarkt season data specializes the role as sweeper.'),
9496106:p('Michael Delcampe','1972-02-08',[17],17,None,3,'Defender','69702',precision='broad_only'),
9496102:p('Luc Beyens','1959-03-27',[17],17,'Lommel',7,'Midfielder','42174',precision='broad_only',note='BDFutbol identifies Beyens as midfielder; the previous left-back inference is removed.'),
9496117:p('Marc Schaessens','1968-09-14',[17],17,'Hoboken',7,'Midfielder','65988',176,72,precision='broad_only'),
9496105:p('Gert Claessens','1972-02-21',[17],17,'Tongeren',7,'Midfielder','958',187,79,precision='broad_only'),
9496120:p('Jürgen Van Deurzen','1974-01-26',[17],17,None,7,'Midfielder','69700',170,None,precision='broad_only'),
9496100:p('Arisvaldo Pereira','1970-11-28',[62],62,None,7,'Midfielder','69695',precision='broad_only'),
9496110:p('Patrick Goots','1966-04-10',[17],17,'Mol',17,'Forward','66131',183,86,precision='broad_only'),
9496104:p('Carmel Busuttil','1964-02-29',[55],55,'Rabat',17,'Forward','69696',precision='broad_only'),
9496107:p('Gert Doumen','1971-06-24',[17],17,'Bree',0,'Goalkeeper','701432',184,77),
9496114:p('Davy Oyen','1975-07-17',[17],17,'Zutendaal',2,'Left-Back','43843',182,81),
9496101:p('Norbert Beuls','1957-01-13',[17],17,'Kleine-Spouwen',3,'Defender','69703',precision='broad_only'),
9496103:p('Frane Bućan','1965-08-25',[31],None,'Split (Yugoslavia)',7,'Midfielder','63263',precision='broad_only',note='BDFutbol labels the modern birth country Croatia. Because the player was born in 1965, the birth state is retained textually as Yugoslavia; Croatian 1993 identity is stored separately.'),
9496108:p('Kurt Dreesen','1973-06-24',[17],17,None,7,'Midfielder','69701',precision='broad_only',note='BDFutbol identifies Dreesen as midfielder; the previous centre-forward inference is removed.'),
9496118:p('Stijn Thijs','1974-04-20',[17],17,None,0,'Goalkeeper','69704'),
9496119:p('Peter van der Ven','1961-01-08',[3],3,'Hunsel',7,'Midfielder','49396',185,None,precision='broad_only',note='BDFutbol identifies Van der Ven as midfielder; the previous winger inference is removed.'),
9496116:p('Emmanuel Sarpong','1971-11-05',[42],42,None,17,'Forward','69697',178,None,precision='broad_only',note='BDFutbol identifies Sarpong as forward; the previous attacking-midfield inference is removed.'),
9496121:p('Marc Vangronsveld','1972-03-29',[17],17,'Maasmechelen',2,'Left-Back','701433',180,None,note='BDFutbol explicitly identifies Vangronsveld as left back; the previous right-back inference is corrected.'),
9496112:p('Ismet Mulavdić','1968-10-19',[20],None,'Gradačac (Yugoslavia)',7,'Midfielder','69699',precision='broad_only',note='BDFutbol uses the modern Bosnia-Herzegovina birth-country label. The 1968 birthplace remains Yugoslavia; Bosnia-Herzegovina is stored separately as the 1993 identity.'),
9496113:p('Sunny Nwachukwu','1976-01-15',[59],59,'Maiduguri',17,'Forward','68639',169,None,precision='broad_only',note='BDFutbol identifies Nwachukwu as forward; the previous attacking-midfield inference is removed.'),
9496115:p('Frank Reumers','1973-09-22',[17],17,None,7,'Midfielder','69698',precision='broad_only',note='BDFutbol identifies Reumers as midfielder; the previous left-wing inference is removed.'),
}


def load(path:Path): return json.loads(path.read_text(encoding='utf-8'))
def dump(path:Path,obj:Any): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split_name(name:str):
    parts=name.split(); return (None,name) if len(parts)==1 else (' '.join(parts[:-1]),parts[-1])
def url(patch:dict[str,Any])->str: return f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"

def reattribute(player:dict[str,Any],role:int,originals:list[dict[str,Any]],sid:int)->None:
    a,b=comparable(originals,ROLE_TO_BROAD[role],int(player.get('overall') or 70),sid)
    player['attributes']=materialise_attributes(int(player.get('overall') or 70),a,b)
    player['attribute_source']='fixed_source_comparable_role_correction_0.41'
    player['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]

def apply_profile(player:dict[str,Any],patch:dict[str,Any],originals:list[dict[str,Any]])->dict[str,Any]:
    sid=int(player['source_id']); old_role=int(player.get('primary_role') or 0); old_broad=player.get('broad_position'); old_nat=player.get('international_country_id')
    first,surname=split_name(patch['name']); player['display_name']=patch['name']; player['first_name']=first; player['surname1']=surname
    player['birth_date']=patch['dob']+'T00:00:00'
    if patch.get('birth_country') is not None: player['birth_country_id']=int(patch['birth_country'])
    else: player.pop('birth_country_id',None)
    player['international_country_id']=int(patch['nat'][0]); player['profile_nationality_country_ids']=[int(x) for x in patch['nat']]
    if len(patch['nat'])>1: player['secondary_nationality_country_id']=int(patch['nat'][1])
    else: player.pop('secondary_nationality_country_id',None)
    player['historical_birth_place_text']=patch.get('place'); player['historical_birth_place_source_url']=url(patch); player['historical_birth_place_source_label']='BDFutbol individual profile / historical-state policy v0.41'
    player['bdfutbol_id']=str(patch['bdf']); player['bdfutbol_url']=url(patch)
    if patch.get('height') is not None: player['height_cm']=int(patch['height'])
    if patch.get('weight') is not None: player['weight_kg']=int(patch['weight'])
    role=int(patch['role']); player['primary_role']=role; player['broad_position']=ROLE_TO_BROAD[role]; player['role_ratings']=role_ratings(role)
    precision=patch.get('precision','exact'); player['profile_position_precision']=precision; player['source_profile_position']=patch['pos']; player['profile_review_required']=precision!='exact'
    if precision=='broad_only':
        player['historical_position_1993_94']=patch['pos']+' (exact role unresolved)'; player['historical_position_source']='BDFutbol + Transfermarkt broad position only v0.41'
    elif precision=='source_conflict_review':
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]+' (source conflict: review retained)'; player['historical_position_source']='Season-specific historical evidence with conflicting modern profile v0.41'
    else:
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]; player['historical_position_source']='BDFutbol individual profile + Transfermarkt 1993-94 specialist role v0.41'
    player['historical_position_source_url']=TM_TEAM if role!=0 else url(patch)
    player['historical_profile_source']='BDFutbol individual profile + Transfermarkt 1993-94 season cross-check v0.41'
    player['historical_profile_source_url']=url(patch); player['historical_club_1994']='Genk'; player['historical_data_source']='BDFutbol 1993-94 + specialist profile cross-check v0.41'; player['bdfutbol_squad_url']=BDF_TEAM
    if patch.get('note'): player['historical_profile_source_note']=patch['note']
    if role!=old_role or player['broad_position']!=old_broad: reattribute(player,role,originals,sid)
    return {'source_id':sid,'display_name':player['display_name'],'role_before':old_role,'role_after':role,'nat_before':old_nat,'nat_after':player.get('international_country_id'),'precision':precision}

def ensure_stage(stage:dict[str,Any],player:dict[str,Any],patch:dict[str,Any])->None:
    club=next(c for c in stage['clubs'] if c['name']=='Genk')
    sid=int(player['source_id']); row=next((r for r in club['players'] if int(r.get('resolved_source_id') or -1)==sid),None)
    if row is None: raise RuntimeError(f'missing Genk staging row {sid}')
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
      'broad_position':player.get('broad_position'),'team_id':TEAM_ID,'team_name':'Genk','origin':'historical_belgium_1993_94','source':'BDFutbol/Transfermarkt Genk deep v0.41',
      'overall':player.get('overall'),'attribute_source':player.get('attribute_source'),'profile_review_required':bool(player.get('profile_review_required')),
      'historical_position_1993_94':player.get('historical_position_1993_94'),'historical_club_1994':'Genk','historical_birth_place_text':patch.get('place'),
      'individual_profile_source':player.get('historical_profile_source'),'individual_profile_source_url':player.get('historical_profile_source_url'),
      'duplicate_check':'exact_name_birthdate_source_profile_gate_v041','matched_existing_id':None,'asset_filename':f'{sid}.jpg',
      'bdfutbol_id':str(patch['bdf']),'bdfutbol_url':url(patch),'bdfutbol_search_name':player['display_name']}
    if sid not in rb: reg['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=rb[sid].get('photo_status'); rb[sid].update(base); rb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'
    if sid not in qb: queue['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=qb[sid].get('photo_status'); qb[sid].update(base); qb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'

def biography(player:dict[str,Any],row:dict[str,Any])->str:
    role='Futbolista' if player.get('profile_position_precision')=='broad_only' else ROLE_ES.get(int(player.get('primary_role') or 0),'Futbolista')
    parts=[f'{role} de Genk en la temporada 1993-94.']
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
    if missing: raise RuntimeError(f'missing Genk snapshot ids: {missing}')
    for sid,patch in P.items():
        changes.append(apply_profile(by[sid],patch,originals)); ensure_stage(stage,by[sid],patch); sync_registry_queue(reg,queue,by[sid],patch)
    club=next(c for c in stage['clubs'] if c['name']=='Genk'); rows={int(r['resolved_source_id']):r for r in club['players'] if r.get('resolved_source_id') is not None}
    for sid in P:
        player=by[sid]; row=rows[sid]
        player['historical_club_spells_1993_94']=[{'club':'Genk','team_id':TEAM_ID,'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}]
        player['historical_biography_1993_94']=biography(player,row); player['historical_biography_source_url']=row.get('profile_source_url'); player['historical_biography_source_label']='BDFutbol/Transfermarkt Genk deep v0.41'; player['historical_biography_status']='source_backed_season_summary'
        player['historical_biography_evidence']={'season':'1993-94','club':'Genk','appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
    after=profile_gap_stats(snap)
    reg_ids=[int(x['source_id']) for x in reg['players']]; q_ids=[int(x['source_id']) for x in queue['players']]
    if len(reg_ids)!=len(set(reg_ids)) or len(q_ids)!=len(set(q_ids)) or set(reg_ids)!=set(q_ids): raise RuntimeError('registry/queue identity integrity failure')
    if len(club['players'])!=23: raise RuntimeError(f'Genk stage expected 23, got {len(club["players"])}')
    if after['Belgium']['missing_birth_date']>before['Belgium']['missing_birth_date']-23: raise RuntimeError('Genk DOB reduction gate not met')
    audit={'schema_version':1,'checkpoint':'0.41.0-belgium-genk-deep','status':'pass','profile_gaps_before':before,'profile_gaps_after':after,
      'profiles':{'curated_existing':len(P),'role_corrections':sum(c['role_before']!=c['role_after'] for c in changes),'review_required':sum(bool(by[s].get('profile_review_required')) for s in P),'changes':changes},
      'source_conflicts':[],
      'historical_country_policy':{
        'former_Yugoslavia':'Katana, Bućan and Mulavdić retain Yugoslavia in historical_birth_place_text and no modern successor-state birth_country_id; 1993 nationality/citizenship identity is stored separately.',
        'future_Russia':'Russia remains untouched. The next Russia pass must separate historical birthplace state, 1993 citizenship/nationality, represented selection and transliterations; USSR must never be auto-mapped to Russia.'},
      'photo_queue':{'bdf_individual_profiles_linked':len(P),'policy':'Every Genk staging identity is linked to its BDF individual profile and marked ready_for_download; no portrait URL is fabricated.'},
      'identity_integrity':{'registry_rows':len(reg_ids),'queue_rows':len(q_ids),'registry_queue_match':set(reg_ids)==set(q_ids),'unique_registry_ids':len(reg_ids)==len(set(reg_ids))},
      'source_policy':['Continue Belgium club-by-club before Russia.','BDFutbol individual profiles anchor identity, DOB, birthplace and measurements.','Transfermarkt season/adjacent-season data specializes roles only when identity is safe.','Historical country naming is frozen to the 1993-94 context.','Conflicting data is review-flagged rather than silently overwritten.','No basketball 75/25 rule is used.']}
    dump(SNAP,snap); dump(REG,reg); dump(QUEUE,queue); dump(STAGE,stage)
    dump(DATA/'historical_profiles_metadata_audit_v041.json',audit); dump(DATA/'historical_metadata_gaps_v041.json',{'checkpoint':audit['checkpoint'],'gaps':after}); dump(DATA/'historical_biographies_audit_v041.json',{'checkpoint':audit['checkpoint'],'profiles_considered':len(P),'status':'pass'}); dump(DATA/'belgium_source_conflicts_v041.json',{'checkpoint':audit['checkpoint'],'status':'pass','conflicts':audit['source_conflicts'],'historical_country_policy':audit['historical_country_policy']})
    print(json.dumps({'checkpoint':audit['checkpoint'],'curated_existing':len(P),'genk_stage_rows':len(club['players']),'belgium_gaps_before':before['Belgium'],'belgium_gaps_after':after['Belgium'],'role_corrections':audit['profiles']['role_corrections'],'review_required':audit['profiles']['review_required']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
