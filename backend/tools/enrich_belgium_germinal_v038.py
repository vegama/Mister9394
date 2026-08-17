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
BDF_TEAM='https://www.bdfutbol.com/en/t/t1993-9411039.html'
TM_TEAM='https://www.transfermarkt.com/beerschot-ac/startseite/verein/566/saison_id/1993'
TEAM_ID=9352003
COUNTRY_NAME={3:'Países Bajos',6:'Inglaterra',17:'Bélgica',41:'Finlandia',56:'Marruecos',72:'Rumanía',74:'Senegal',88:'Zaire',93:'Hungría'}
ROLE_ES={0:'Portero',1:'Lateral derecho',2:'Lateral izquierdo',3:'Defensa central',4:'Defensa central',5:'Líbero',6:'Mediocentro defensivo',7:'Centrocampista',8:'Mediapunta',9:'Interior derecho',10:'Interior derecho',11:'Extremo derecho',12:'Extremo derecho',13:'Interior izquierdo',14:'Interior izquierdo',15:'Extremo izquierdo',16:'Extremo izquierdo',17:'Delantero centro'}

# BDF individual pages are the primary identity/DOB/birth/measurement source.
# Transfermarkt season data specializes roles when the identity is unambiguous.
# Two conflicts are deliberately retained for review: Victor Diagne's career-position mismatch,
# and the Juha/Jani Jussila identity/position conflation in modern squad databases.
def p(name:str,dob:str,nat:list[int],birth:int|None,place:str|None,role:int,pos:str,bdf:str,
      height:int|None=None,weight:int|None=None,precision:str='exact',note:str|None=None) -> dict[str,Any]:
    return dict(club='Germinal Ekeren',name=name,dob=dob,nat=nat,birth_country=birth,place=place,role=role,pos=pos,bdf=bdf,
                height=height,weight=weight,precision=precision,note=note)

P:dict[int,dict[str,Any]]={
9496163:p('Philippe vande Walle','1961-12-22',[17],17,'Gozée',0,'Goalkeeper','42165'),
9496165:p('Michaël Verstraeten','1967-08-12',[17],17,'Mechelen',3,'Centre-Back','57020',192,None),
9496149:p('Didier Dheedene','1972-01-22',[17],17,'Antwerp',2,'Left-Back','90565',183,84),
9496162:p('Mark Talbut','1962-07-23',[6,17],6,'Burnley',3,'Centre-Back','69487',note='Transfermarkt records English and Belgian citizenship; England is retained as primary.'),
9496146:p('Frank Bosmans','1967-10-14',[17],17,None,3,'Defender','69355',precision='broad_only',note='Both BDFutbol and Transfermarkt are broad Defender; no centre-back subtype is asserted as exact.'),
9496153:p('Rudy Janssens','1963-08-05',[17],17,'Geel',7,'Central Midfield','66366',180,77),
9496161:p('Simon Tahamata','1956-05-26',[3,17],3,'Vught',16,'Left Winger','42783',note='Transfermarkt records Netherlands and Belgium citizenship; Netherlands is primary.'),
9495310:p('Gunther Hofmans','1967-01-03',[17],17,'Berchem',8,'Attacking Midfield','68472',180,70),
9496147:p('Pascal Bovri','1964-10-04',[17],17,'Halle',6,'Defensive Midfield','68860',178,82),
9496324:p('Jean-Marie Abeels','1962-11-18',[17],17,None,8,'Attacking Midfield','69296'),
9496152:p('Gábor Halmai','1972-01-07',[93],93,'Székesfehérvár',6,'Defensive Midfield','69295',187,75),
9496144:p('Matthew Andrews','1970-03-30',[6],6,None,0,'Goalkeeper','68601'),
9496145:p('Geert Berrevoets','1971-05-28',[17],17,None,7,'Midfielder','69486',precision='broad_only'),
9496156:p('Ervin Kovács','1967-01-24',[93],93,'Bercel',6,'Defensive Midfield','68471',182,79),
9496159:p("Ngoy N'Sumbu",'1972-12-30',[88],88,'Kinshasa (Zaire)',8,'Attacking Midfield','701430',173,None,note='1993-94 historical state is Zaire; modern DR Congo is not back-projected. BDF/National-Football-Teams support 30/12/1972; a conflicting Transfermarkt profile shows 30/10.'),
9496160:p('Frédéric Pierre','1974-02-23',[17],17,'Namur',17,'Centre-Forward','66180',178,76),
9496148:p('Romulus Buia','1970-06-15',[72],72,'Baia Mare',8,'Attacking Midfield','69672',173,70),
9496150:p('Victor Diagne','1971-07-07',[74],74,None,17,'Forward','69673',precision='source_conflict_review',note='BDFutbol and a season-specific 1993-94 squad source classify him as forward; Transfermarkt current profile lists central midfield. Season classification is retained with review flag.'),
9496164:p('Patrick Versavel','1961-07-01',[17],17,'Diest',7,'Midfielder','59801',188,None,precision='broad_only'),
9496154:p('Juha Jussila','1975-08-21',[41],41,None,7,'Midfielder','69669',175,71,precision='source_conflict_review',note='BDFutbol and Finnish historical player-abroad records identify Juha Jussila as a midfielder with five 1993-94 league appearances. Transfermarkt 93/94 appears to list Jani Jussila as a defender; no cross-identity overwrite is applied.'),
9496151:p('Patrick Ghislain','1965-08-29',[17],17,None,2,'Left-Back','69488'),
9496157:p("Karim M'Ghoghi",'1971-04-17',[56,17],17,'La Louvière',7,'Central Midfield','87597',182,None,note='BDFutbol records Morocco and Belgium nationality; Belgium is the documented birth country.'),
9496155:p('Salif Keïta','1975-10-19',[74],74,'Dakar',17,'Centre-Forward','701431',176,74),
9496158:p('Kurt Moons','1972-06-16',[17],17,None,7,'Midfielder','69670',precision='broad_only'),
9496325:p('Laurent Ballenghien','1969-12-15',[17],17,None,17,'Forward','69671'),
}


def load(path:Path): return json.loads(path.read_text(encoding='utf-8'))
def dump(path:Path,obj:Any): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split_name(name:str):
    parts=name.split(); return (None,name) if len(parts)==1 else (' '.join(parts[:-1]),parts[-1])
def url(patch:dict[str,Any])->str: return f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"

def reattribute(player:dict[str,Any],role:int,originals:list[dict[str,Any]],sid:int)->None:
    a,b=comparable(originals,ROLE_TO_BROAD[role],int(player.get('overall') or 70),sid)
    player['attributes']=materialise_attributes(int(player.get('overall') or 70),a,b)
    player['attribute_source']='fixed_source_comparable_role_correction_0.38'
    player['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]

def apply_profile(player:dict[str,Any],patch:dict[str,Any],originals:list[dict[str,Any]])->dict[str,Any]:
    sid=int(player['source_id']); old_role=int(player.get('primary_role') or 0); old_broad=player.get('broad_position'); old_nat=player.get('international_country_id')
    first,surname=split_name(patch['name']); player['display_name']=patch['name']; player['first_name']=first; player['surname1']=surname
    player['birth_date']=patch['dob']+'T00:00:00'
    if patch.get('birth_country') is not None: player['birth_country_id']=int(patch['birth_country'])
    player['international_country_id']=int(patch['nat'][0]); player['profile_nationality_country_ids']=[int(x) for x in patch['nat']]
    if len(patch['nat'])>1: player['secondary_nationality_country_id']=int(patch['nat'][1])
    else: player.pop('secondary_nationality_country_id',None)
    player['historical_birth_place_text']=patch.get('place'); player['historical_birth_place_source_url']=url(patch); player['historical_birth_place_source_label']='BDFutbol individual profile / historical-state policy v0.38'
    player['bdfutbol_id']=str(patch['bdf']); player['bdfutbol_url']=url(patch)
    if patch.get('height') is not None: player['height_cm']=int(patch['height'])
    if patch.get('weight') is not None: player['weight_kg']=int(patch['weight'])
    role=int(patch['role']); player['primary_role']=role; player['broad_position']=ROLE_TO_BROAD[role]; player['role_ratings']=role_ratings(role)
    precision=patch.get('precision','exact'); player['profile_position_precision']=precision; player['source_profile_position']=patch['pos']; player['profile_review_required']=precision!='exact'
    if precision=='broad_only':
        player['historical_position_1993_94']=patch['pos']+' (exact role unresolved)'; player['historical_position_source']='BDFutbol + Transfermarkt broad position only v0.38'
    elif precision=='source_conflict_review':
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]+' (source conflict: review retained)'; player['historical_position_source']='Season-specific historical evidence with conflicting modern profile v0.38'
    else:
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]; player['historical_position_source']='BDFutbol individual profile + Transfermarkt 1993-94 specialist role v0.38'
    player['historical_position_source_url']=TM_TEAM if role!=0 else url(patch)
    player['historical_profile_source']='BDFutbol individual profile + Transfermarkt 1993-94 season cross-check v0.38'
    player['historical_profile_source_url']=url(patch); player['historical_club_1994']='Germinal Ekeren'; player['historical_data_source']='BDFutbol 1993-94 + specialist profile cross-check v0.38'; player['bdfutbol_squad_url']=BDF_TEAM
    if patch.get('note'): player['historical_profile_source_note']=patch['note']
    if role!=old_role or player['broad_position']!=old_broad: reattribute(player,role,originals,sid)
    return {'source_id':sid,'display_name':player['display_name'],'role_before':old_role,'role_after':role,'nat_before':old_nat,'nat_after':player.get('international_country_id'),'precision':precision}

def ensure_stage(stage:dict[str,Any],player:dict[str,Any],patch:dict[str,Any])->None:
    club=next(c for c in stage['clubs'] if c['name']=='Germinal Ekeren')
    sid=int(player['source_id']); row=next((r for r in club['players'] if int(r.get('resolved_source_id') or -1)==sid),None)
    if row is None: raise RuntimeError(f'missing Germinal staging row {sid}')
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
      'broad_position':player.get('broad_position'),'team_id':TEAM_ID,'team_name':'Germinal Ekeren','origin':'historical_belgium_1993_94','source':'BDFutbol/Transfermarkt Germinal deep v0.38',
      'overall':player.get('overall'),'attribute_source':player.get('attribute_source'),'profile_review_required':bool(player.get('profile_review_required')),
      'historical_position_1993_94':player.get('historical_position_1993_94'),'historical_club_1994':'Germinal Ekeren','historical_birth_place_text':patch.get('place'),
      'individual_profile_source':player.get('historical_profile_source'),'individual_profile_source_url':player.get('historical_profile_source_url'),
      'duplicate_check':'exact_name_birthdate_source_profile_gate_v038','matched_existing_id':None,'asset_filename':f'{sid}.jpg',
      'bdfutbol_id':str(patch['bdf']),'bdfutbol_url':url(patch),'bdfutbol_search_name':player['display_name']}
    if sid not in rb: reg['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=rb[sid].get('photo_status'); rb[sid].update(base); rb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'
    if sid not in qb: queue['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=qb[sid].get('photo_status'); qb[sid].update(base); qb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'

def biography(player:dict[str,Any],row:dict[str,Any])->str:
    role='Futbolista' if player.get('profile_position_precision')=='broad_only' else ROLE_ES.get(int(player.get('primary_role') or 0),'Futbolista')
    parts=[f'{role} de Germinal Ekeren en la temporada 1993-94.']
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
    if missing: raise RuntimeError(f'missing Germinal snapshot ids: {missing}')
    for sid,patch in P.items():
        changes.append(apply_profile(by[sid],patch,originals)); ensure_stage(stage,by[sid],patch); sync_registry_queue(reg,queue,by[sid],patch)
    club=next(c for c in stage['clubs'] if c['name']=='Germinal Ekeren'); rows={int(r['resolved_source_id']):r for r in club['players'] if r.get('resolved_source_id') is not None}
    for sid in P:
        player=by[sid]; row=rows[sid]
        player['historical_club_spells_1993_94']=[{'club':'Germinal Ekeren','team_id':TEAM_ID,'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}]
        player['historical_biography_1993_94']=biography(player,row); player['historical_biography_source_url']=row.get('profile_source_url'); player['historical_biography_source_label']='BDFutbol/Transfermarkt Germinal deep v0.38'; player['historical_biography_status']='source_backed_season_summary'
        player['historical_biography_evidence']={'season':'1993-94','club':'Germinal Ekeren','appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
    after=profile_gap_stats(snap)
    reg_ids=[int(x['source_id']) for x in reg['players']]; q_ids=[int(x['source_id']) for x in queue['players']]
    if len(reg_ids)!=len(set(reg_ids)) or len(q_ids)!=len(set(q_ids)) or set(reg_ids)!=set(q_ids): raise RuntimeError('registry/queue identity integrity failure')
    if len(club['players'])!=25: raise RuntimeError(f'Germinal stage expected 25, got {len(club["players"])}')
    if after['Belgium']['missing_birth_date']>before['Belgium']['missing_birth_date']-24: raise RuntimeError('Germinal DOB reduction gate not met')
    conflict_names=['Victor Diagne','Juha Jussila']
    audit={'schema_version':1,'checkpoint':'0.38.0-belgium-germinal-deep','status':'pass','profile_gaps_before':before,'profile_gaps_after':after,
      'profiles':{'curated_existing':len(P),'role_corrections':sum(c['role_before']!=c['role_after'] for c in changes),'review_required':sum(bool(by[s].get('profile_review_required')) for s in P),'changes':changes},
      'source_conflicts':[{'name':n,'decision':'retain season-safe interpretation with review flag','note':by[s]['historical_profile_source_note']} for s,n in [(9496150,'Victor Diagne'),(9496154,'Juha Jussila')]],
      'historical_country_policy':{'Ngoy N\'Sumbu':'Zaire (country_id 88) is used for 1993-94; modern DR Congo is not back-projected.'},
      'photo_queue':{'bdf_individual_profiles_linked':len(P),'policy':'Every Germinal staging identity is linked to its BDF individual profile and marked ready_for_download; no portrait URL is fabricated.'},
      'identity_integrity':{'registry_rows':len(reg_ids),'queue_rows':len(q_ids),'registry_queue_match':set(reg_ids)==set(q_ids),'unique_registry_ids':len(reg_ids)==len(set(reg_ids))},
      'source_policy':['Continue Belgium club-by-club before Russia.','BDFutbol individual profiles anchor identity, DOB, birthplace and measurements.','Transfermarkt season data specializes roles only when identity is safe.','Historical country naming is frozen to the 1993-94 context.','Conflicting modern data is review-flagged rather than silently overwriting season evidence.','No basketball 75/25 rule is used.']}
    dump(SNAP,snap); dump(REG,reg); dump(QUEUE,queue); dump(STAGE,stage)
    dump(DATA/'historical_profiles_metadata_audit_v038.json',audit); dump(DATA/'historical_metadata_gaps_v038.json',{'checkpoint':audit['checkpoint'],'gaps':after}); dump(DATA/'historical_biographies_audit_v038.json',{'checkpoint':audit['checkpoint'],'profiles_considered':len(P),'status':'pass'}); dump(DATA/'belgium_source_conflicts_v038.json',{'checkpoint':audit['checkpoint'],'status':'pass','conflicts':audit['source_conflicts']})
    print(json.dumps({'checkpoint':audit['checkpoint'],'curated_existing':len(P),'germinal_stage_rows':len(club['players']),'belgium_gaps_before':before['Belgium'],'belgium_gaps_after':after['Belgium'],'role_corrections':audit['profiles']['role_corrections'],'review_required':audit['profiles']['review_required']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
