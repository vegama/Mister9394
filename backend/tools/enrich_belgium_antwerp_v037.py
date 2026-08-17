from __future__ import annotations

from collections import Counter
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
BDF_TEAM='https://www.bdfutbol.com/en/t/t1993-9410010.html'
TM_TEAM='https://www.transfermarkt.com/royal-antwerpen-fc/startseite/verein/1096/saison_id/1993'
WF_TEAM='https://www.worldfootball.net/teams/te1590/royal-antwerp-fc/vs1993-1994/squad/'
TEAM_ID=1032
COUNTRY_NAME={4:'Alemania',15:'Australia',17:'Bélgica',20:'Bosnia-Herzegovina',56:'Marruecos',63:'Italia',75:'República Federal de Yugoslavia',88:'Zaire',93:'Hungría'}
ROLE_ES={0:'Portero',1:'Lateral derecho',2:'Lateral izquierdo',3:'Defensa central',4:'Defensa central',5:'Líbero',6:'Mediocentro defensivo',7:'Centrocampista',8:'Mediapunta',9:'Interior derecho',10:'Interior derecho',11:'Extremo derecho',12:'Extremo derecho',13:'Interior izquierdo',14:'Interior izquierdo',15:'Extremo izquierdo',16:'Extremo izquierdo',17:'Delantero centro'}

# Source policy: BDF individual profiles for identity/DOB/birthplace/measurements where available;
# Transfermarkt's 1993-94 season squad for specialist roles; international-history sources to avoid
# projecting modern successor states backwards. Mauritius remains textual because the current game
# country-id catalogue has no verified Mauritius mapping; no arbitrary numeric country id is invented.
def p(name:str,dob:str,nat:list[int]|None,birth:int|None,place:str|None,role:int,pos:str,bdf:str|None,
      height:int|None=None,weight:int|None=None,precision:str='exact',note:str|None=None) -> dict[str,Any]:
    return dict(club='Royal Antwerp',name=name,dob=dob,nat=nat,birth_country=birth,place=place,role=role,pos=pos,bdf=bdf,
                height=height,weight=weight,precision=precision,note=note)

P:dict[int,dict[str,Any]]={
9496302:p('Ratko Svilar','1950-05-06',[75,17],None,'Crvenka (Yugoslavia)',0,'Goalkeeper','69517',183,None,note='Born in SFR Yugoslavia; 1993 sporting context is retained as FR Yugoslavia, with Belgian secondary citizenship.'),
9494210:p('Rudi Smidts','1963-08-12',[17],17,'Deurne',2,'Left-Back','66440',178,72),
9496303:p('Rudy Taeymans','1967-02-08',[17],17,'Merksem',2,'Left-Back','68932',180,74),
9496287:p('Nico Broeckaert','1960-11-23',[17],17,'Zottegem',5,'Sweeper','69315',186,82,note='BDFutbol career profile is broad central defender; the 1993-94 season squad identifies him as sweeper.'),
9496291:p('Geert Emmerechts','1968-05-05',[17],17,'Vilvoorde',3,'Centre-Back','68926'),
9496293:p('Wim Kiekens','1968-02-26',[17],17,'Aalst',1,'Right-Back','77573',note='BDFutbol is broad defender; the 1993-94 season squad specializes him at right-back.'),
9496301:p('Didier Segers','1965-02-21',[17],17,'Berchem-Sainte-Agathe',2,'Left-Back','66238',176,None),
9496297:p('Hans-Peter Lehnhoff','1963-07-12',[4],4,'Mariadorf',9,'Right Midfield','91122',178,75),
9496300:p('Krist Porte','1968-09-07',[17],17,'Gent',9,'Right Midfield','68469',180,78,note='BDFutbol is broad midfielder; Transfermarkt 93/94 supplies Right Midfield.'),
9495304:p('Francis Severeyns','1968-01-08',[17],17,'Westmalle',17,'Centre-Forward','81760',178,66),
9496289:p('Nico Claesen','1962-10-01',[17],17,'Leut',17,'Centre-Forward','91895',171,None),
9496304:p('Yves Van der Straeten','1971-01-18',[17],17,'Berlare',0,'Goalkeeper','89144',186,83),
9496288:p('Miloš Bursać','1964-06-23',[75],None,'Belgrade (Yugoslavia)',17,'Centre-Forward','2036',184,76,note='BDFutbol and eu-football support 23/06/1964; a conflicting Transfermarkt DOB is not used. Born in SFR Yugoslavia, so no modern Serbia birth_country_id is back-projected.'),
9496306:p('Ronny Van Rethy','1961-11-21',[17],17,'Mol',7,'Central Midfield','69317',183,77,note='BDFutbol, Belgian archive material and BeSoccer support 21/11/1961; some modern databases show 12/11/1961.'),
9496298:p('Victor Lembi Kubu','1970-05-10',[88],None,'Kinshasa',7,'Central Midfield','68929',178,75,note='1993 historical country context uses Zaire; modern DR Congo is not back-projected into birth_country_id.'),
9496295:p('George Kulcsár','1967-08-12',[15,93],93,'Budapest',1,'Right-Back','69099',183,79,note='National-Football-Teams and Transfermarkt support 12/08/1967, Australian international identity and right-back; one secondary source gives a conflicting December date.'),
9496299:p('Nourrédine Moukrim','1966-02-16',[56,17],56,'Khemisset',8,'Attacking Midfield','69515',note='Moroccan primary identity with Belgian secondary citizenship.'),
9496286:p('John Aloisi','1976-02-05',[15,63],15,'Adelaide',17,'Centre-Forward','1297',185,79),
9496307:p('Willy Vincent','1966-11-18',None,None,'Mauritius',17,'Striker','69101',170,62,note='Mauritian international identity is source-backed, but the current game country-id catalogue has no verified Mauritius id; kept explicitly unresolved instead of inventing one.'),
9496294:p('Kálmán Kovács','1965-09-11',[93],93,'Budapest',17,'Centre-Forward','54163',174,None),
9496292:p('Dragan Jakovljević','1962-02-23',[75],None,'Konjic (Yugoslavia)',17,'Centre-Forward','65490',190,88,note='Former Yugoslavia international (8 caps); birthplace remains textual rather than rewriting the birth state to modern Bosnia-Herzegovina.'),
9496296:p('Carlo Lavigne','1972-08-19',[17],17,'Sint-Truiden',7,'Midfielder','69313',183,82,precision='broad_only'),
9496305:p('Peter Van Hout','1974-09-19',[17],17,None,7,'Midfielder','69516',precision='broad_only'),
9496290:p('Garry de Graef','1974-10-21',[17],17,'Aarschot',2,'Left-Back','85677',171,69,precision='source_conflict_review',note='Transfermarkt 93/94 places him at left-back while BDFutbol career profile labels him midfielder; left-back is used for the season role but remains explicitly review-required.'),
}

NEW_ID=9498014
NEW=p('Stevan Stojanović','1964-10-29',[75],None,'Kosovska Mitrovica (Yugoslavia)',0,'Goalkeeper',None,187,84,
      note='Transfermarkt and WorldFootball independently list him in the Royal Antwerp 1993-94 squad; BDFutbol league lineup has no row, so no league appearances/minutes are invented.')

ROLE_SOURCE_CONFLICT={'Garry de Graef'}


def load(path:Path): return json.loads(path.read_text(encoding='utf-8'))
def dump(path:Path,obj:Any): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split_name(name:str):
    parts=name.split(); return (None,name) if len(parts)==1 else (' '.join(parts[:-1]),parts[-1])
def url(patch:dict[str,Any])->str:
    return f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html" if patch.get('bdf') else TM_TEAM

def reattribute(player:dict[str,Any],role:int,originals:list[dict[str,Any]],sid:int)->None:
    a,b=comparable(originals,ROLE_TO_BROAD[role],int(player.get('overall') or 70),sid)
    player['attributes']=materialise_attributes(int(player.get('overall') or 70),a,b)
    player['attribute_source']='fixed_source_comparable_role_correction_0.37'
    player['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]

def create_player(originals:list[dict[str,Any]])->dict[str,Any]:
    patch=NEW; role=0; overall=75; first,surname=split_name(patch['name'])
    a,b=comparable(originals,ROLE_TO_BROAD[role],overall,NEW_ID)
    return {'source_id':NEW_ID,'team_id':TEAM_ID,'display_name':patch['name'],'first_name':first,'surname1':surname,'surname2':None,
      'birth_date':patch['dob']+'T00:00:00','birth_country_id':None,'international_country_id':75,'preferred_foot':None,'shirt_number':None,
      'primary_role':role,'broad_position':ROLE_TO_BROAD[role],'overall':overall,'category':overall,'height_cm':187,'weight_kg':84,
      'salary':0,'release_clause':0,'contract_start_year':1993,'contract_end_year':None,'loan':False,'initially_reserve':True,'retired':False,
      'attributes':materialise_attributes(overall,a,b),'birth_city_id':None,'naturalized_country_id':None,'basque_origin':False,'favorite_shirt_number':None,
      'injury_proneness':0,'progression_mean':0,'fan_affection':0,'academy_team_id':None,'previous_team_id':None,'previous_team_years':None,'buyback_option':False,
      'role_ratings':role_ratings(role),'hidden_traits':{'individualist':False,'killer_pass':False,'holds_ball':False,'long_shots':False,'cuts_inside':False,'first_time_play':False,'dives':False},
      'historical_squad_1994':True,'external_origin':'historical_belgium_1993_94','creation_batch':'belgium_antwerp_deep_0.37',
      'attribute_source':'fixed_source_comparable_role_profile_0.37','attribute_comparable_source_ids':[int(a['source_id']),int(b['source_id'])]}

def apply_profile(player:dict[str,Any],patch:dict[str,Any],originals:list[dict[str,Any]])->dict[str,Any]:
    sid=int(player['source_id']); old_role=int(player.get('primary_role') or 0); old_broad=player.get('broad_position'); old_nat=player.get('international_country_id')
    first,surname=split_name(patch['name']); player['display_name']=patch['name']; player['first_name']=first; player['surname1']=surname
    player['birth_date']=patch['dob']+'T00:00:00'
    # Only set a numeric birth-country when it is historically defensible. None means intentionally unresolved.
    if patch.get('birth_country') is not None: player['birth_country_id']=int(patch['birth_country'])
    elif patch.get('place') and ('Yugoslavia' in str(patch['place']) or patch['name'] in {'Victor Lembi Kubu','Willy Vincent'}): player.pop('birth_country_id',None)
    if patch.get('nat'):
        player['international_country_id']=int(patch['nat'][0]); player['profile_nationality_country_ids']=[int(x) for x in patch['nat']]
        if len(patch['nat'])>1: player['secondary_nationality_country_id']=int(patch['nat'][1])
        else: player.pop('secondary_nationality_country_id',None)
    else:
        player.pop('international_country_id',None); player['profile_nationality_country_ids']=[]; player.pop('secondary_nationality_country_id',None)
        player['historical_nationality_text']='Mauritius'; player['historical_nationality_id_status']='unresolved_country_id_catalogue'
    player['historical_birth_place_text']=patch.get('place'); player['historical_birth_place_source_url']=url(patch); player['historical_birth_place_source_label']='BDFutbol individual profile / historical-state policy v0.37'
    if patch.get('bdf'):
        player['bdfutbol_id']=str(patch['bdf']); player['bdfutbol_url']=url(patch)
    if patch.get('height') is not None: player['height_cm']=int(patch['height'])
    if patch.get('weight') is not None: player['weight_kg']=int(patch['weight'])
    role=int(patch['role']); player['primary_role']=role; player['broad_position']=ROLE_TO_BROAD[role]; player['role_ratings']=role_ratings(role)
    precision=patch.get('precision','exact'); player['profile_position_precision']=precision; player['source_profile_position']=patch['pos']
    player['profile_review_required']=precision!='exact'
    if precision=='broad_only':
        player['historical_position_1993_94']=patch['pos']+' (exact role unresolved)'; player['historical_position_source']='BDFutbol broad profile / Transfermarkt no safer specialist resolution v0.37'
    elif precision=='source_conflict_review':
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]+' (source conflict: review retained)'; player['historical_position_source']='Transfermarkt 1993-94 specialist role vs BDFutbol career-profile conflict v0.37'
    else:
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]; player['historical_position_source']='BDFutbol individual profile + Transfermarkt 1993-94 specialist role v0.37'
    player['historical_position_source_url']=TM_TEAM if role not in {0} else url(patch)
    player['historical_profile_source']='BDFutbol individual profile + Transfermarkt 1993-94 season cross-check v0.37' if patch.get('bdf') else 'Transfermarkt + WorldFootball 1993-94 squad cross-check v0.37'
    player['historical_profile_source_url']=url(patch); player['historical_club_1994']='Royal Antwerp'; player['historical_data_source']='BDFutbol 1993-94 + specialist profile cross-check v0.37'; player['bdfutbol_squad_url']=BDF_TEAM
    if patch.get('note'): player['historical_profile_source_note']=patch['note']
    if role!=old_role or player['broad_position']!=old_broad: reattribute(player,role,originals,sid)
    return {'source_id':sid,'display_name':player['display_name'],'role_before':old_role,'role_after':role,'nat_before':old_nat,'nat_after':player.get('international_country_id'),'precision':precision}

def ensure_stage(stage:dict[str,Any],player:dict[str,Any],patch:dict[str,Any],new:bool=False)->None:
    club=next(c for c in stage['clubs'] if c['name']=='Royal Antwerp')
    sid=int(player['source_id'])
    row=next((r for r in club['players'] if int(r.get('resolved_source_id') or -1)==sid),None)
    if row is None:
        if not new: raise RuntimeError(f'missing Antwerp staging row {sid}')
        row={'bdfutbol_name':'Stojanović','age_1993_94':29,'appearances':0,'starts':0,'minutes':0,'goals':0,'core_18_candidate':False,
             'source_roster_member':True,'league_row_absent':True,'identity_resolution':'created_historical_identity_from_corroborated_season_roster','resolved_source_id':sid,'opening_club_1993_94':'Royal Antwerp'}
        club['players'].append(row)
    row.update({'resolved_display_name':player['display_name'],'resolved_primary_role':player['primary_role'],'resolved_exact_position':player['historical_position_1993_94'],
      'resolved_birth_date':player['birth_date'],'resolved_country_id':player.get('international_country_id'),'source_profile_position':patch['pos'],
      'profile_source':player['historical_profile_source'],'profile_source_url':player['historical_profile_source_url'],'position_source':player['historical_position_source'],
      'position_source_url':player['historical_position_source_url'],'resolved_birth_place_text':patch.get('place'),'individual_profile_source_url':player['historical_profile_source_url']})
    if patch.get('bdf'): row['bdfutbol_id']=str(patch['bdf'])
    if patch.get('note'): row['profile_source_note']=patch['note']
    if not patch.get('nat'): row['nationality_resolution']='source_backed_text_only_country_id_unresolved'; row['historical_nationality_text']='Mauritius'

def sync_registry_queue(reg:dict[str,Any],queue:dict[str,Any],player:dict[str,Any],patch:dict[str,Any])->None:
    sid=int(player['source_id']); rb={int(x['source_id']):x for x in reg['players']}; qb={int(x['source_id']):x for x in queue['players']}
    base={'source_id':sid,'display_name':player['display_name'],'first_name':player.get('first_name'),'surname1':player.get('surname1'),'surname2':player.get('surname2'),
      'birth_date':str(player.get('birth_date') or '')[:10] or None,'country_id':player.get('international_country_id'),'country_name':COUNTRY_NAME.get(player.get('international_country_id')),
      'broad_position':player.get('broad_position'),'team_id':TEAM_ID,'team_name':'Royal Antwerp','origin':'historical_belgium_1993_94','source':'BDFutbol/Transfermarkt Antwerp deep v0.37',
      'overall':player.get('overall'),'attribute_source':player.get('attribute_source'),'profile_review_required':bool(player.get('profile_review_required')),
      'historical_position_1993_94':player.get('historical_position_1993_94'),'historical_club_1994':'Royal Antwerp','historical_birth_place_text':patch.get('place'),
      'individual_profile_source':player.get('historical_profile_source'),'individual_profile_source_url':player.get('historical_profile_source_url'),
      'duplicate_check':'exact_name_birthdate_source_profile_gate_v037','matched_existing_id':None,'asset_filename':f'{sid}.jpg'}
    if patch.get('bdf'):
        base.update({'bdfutbol_id':str(patch['bdf']),'bdfutbol_url':url(patch),'bdfutbol_search_name':player['display_name']})
    if not patch.get('nat'): base.update({'historical_nationality_text':'Mauritius','country_id_status':'unresolved_verified_catalogue_mapping'})
    if sid not in rb: reg['players'].append(dict(base,photo_status='ready_for_download' if patch.get('bdf') else 'pending'))
    else:
        old_photo=rb[sid].get('photo_status'); rb[sid].update(base); rb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else ('ready_for_download' if patch.get('bdf') else old_photo or 'pending')
    if sid not in qb: queue['players'].append(dict(base,photo_status='ready_for_download' if patch.get('bdf') else 'pending'))
    else:
        old_photo=qb[sid].get('photo_status'); qb[sid].update(base); qb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else ('ready_for_download' if patch.get('bdf') else old_photo or 'pending')

def biography(player:dict[str,Any],row:dict[str,Any])->str:
    role='Futbolista' if player.get('profile_position_precision')=='broad_only' else ROLE_ES.get(int(player.get('primary_role') or 0),'Futbolista')
    parts=[f'{role} de Royal Antwerp en la temporada 1993-94.']
    if row.get('league_row_absent'):
        parts.append('Está corroborado como miembro de la plantilla de temporada, pero no aparece en la tabla liguera BDFutbol utilizada; no se inventan partidos ni minutos.')
    else:
        stats=[]
        for k,label in [('appearances','partidos'),('starts','como titular')]:
            if isinstance(row.get(k),int): stats.append(f"{row[k]} {label}")
        if isinstance(row.get('minutes'),int): stats.append(f"{row['minutes']:,}".replace(',','.')+' minutos')
        if stats: parts.append('En el registro liguero figura con '+', '.join(stats)+'.')
        if int(player.get('primary_role') or 0)!=0 and isinstance(row.get('goals'),int): parts.append(f"Marcó {row['goals']} gol"+('' if row['goals']==1 else 'es')+'.')
    d=str(player['birth_date'])[:10]; y,m,day=d.split('-'); parts.append(f'Fecha de nacimiento registrada: {day}/{m}/{y}.')
    if player.get('historical_birth_place_text'): parts.append('Lugar de nacimiento documentado: '+str(player['historical_birth_place_text'])+'.')
    if player.get('historical_nationality_text'): parts.append('Nacionalidad histórica documentada: '+str(player['historical_nationality_text'])+' (id interno pendiente de mapeo verificado).')
    return ' '.join(parts)

def main()->None:
    snap=load(SNAP); reg=load(REG); queue=load(QUEUE); stage=load(STAGE); before=profile_gap_stats(snap)
    originals=[x for x in snap['players'] if x.get('attributes') and not x.get('external_origin') and not x.get('creation_batch')]
    by={int(x['source_id']):x for x in snap['players']}
    # Duplicate gate for the source-only Stojanović identity.
    collisions=[x for x in snap['players'] if (x.get('display_name') or '').casefold()==NEW['name'].casefold() and str(x.get('birth_date') or '')[:10]==NEW['dob']]
    if collisions and NEW_ID not in {int(x['source_id']) for x in collisions}: raise RuntimeError(f'Stojanovic duplicate collision: {[x["source_id"] for x in collisions]}')
    if NEW_ID not in by:
        np=create_player(originals); snap['players'].append(np); by[NEW_ID]=np
    changes=[]
    for sid,patch in {**P,NEW_ID:NEW}.items():
        changes.append(apply_profile(by[sid],patch,originals)); ensure_stage(stage,by[sid],patch,new=(sid==NEW_ID)); sync_registry_queue(reg,queue,by[sid],patch)
    # Regenerate Antwerp biographies and spell evidence.
    club=next(c for c in stage['clubs'] if c['name']=='Royal Antwerp'); rows={int(r['resolved_source_id']):r for r in club['players'] if r.get('resolved_source_id') is not None}
    for sid in list(P)+[NEW_ID]:
        player=by[sid]; row=rows[sid]
        player['historical_club_spells_1993_94']=[{'club':'Royal Antwerp','team_id':TEAM_ID,'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals'),'source_roster_member':bool(row.get('source_roster_member')),'league_row_absent':bool(row.get('league_row_absent'))}]
        player['historical_biography_1993_94']=biography(player,row); player['historical_biography_source_url']=row.get('profile_source_url'); player['historical_biography_source_label']='BDFutbol/Transfermarkt/WorldFootball Antwerp deep v0.37'; player['historical_biography_status']='source_backed_season_summary'
        player['historical_biography_evidence']={'season':'1993-94','club':'Royal Antwerp','appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals'),'source_roster_member':bool(row.get('source_roster_member')),'league_row_absent':bool(row.get('league_row_absent'))}
    after=profile_gap_stats(snap)
    reg_ids=[int(x['source_id']) for x in reg['players']]; q_ids=[int(x['source_id']) for x in queue['players']]
    if len(reg_ids)!=len(set(reg_ids)) or len(q_ids)!=len(set(q_ids)) or set(reg_ids)!=set(q_ids): raise RuntimeError('registry/queue identity integrity failure')
    # Antwerp should have all 24 BDF rows plus one independently corroborated source-roster-only goalkeeper.
    if len(club['players'])!=25: raise RuntimeError(f'Antwerp stage expected 25, got {len(club["players"])}')
    if after['Belgium']['missing_birth_date']>before['Belgium']['missing_birth_date']-22: raise RuntimeError('DOB reduction gate not met')
    unresolved_conflicts=[{'name':'Zsolt Muzsnay','decision':'not_added','reason':'Transfermarkt 93/94 displays him in Antwerp squad, but multiple career histories place his Antwerp spell earlier and/or at Videoton in 1992-93; held out pending stronger season-specific corroboration.'}]
    audit={'schema_version':1,'checkpoint':'0.37.0-belgium-antwerp-deep','status':'pass','profile_gaps_before':before,'profile_gaps_after':after,
      'profiles':{'curated_existing':len(P),'new_historical_identities':1,'role_corrections':sum(c['role_before']!=c['role_after'] for c in changes),'review_required':sum(bool(by[s].get('profile_review_required')) for s in list(P)+[NEW_ID]),'changes':changes},
      'source_roster_union':{'royal_antwerp_stage_rows_after':len(club['players']),'source_visible_without_bdf_league_row':[NEW_ID],'source_only_identity':'Stevan Stojanović','league_stats_policy':'No league appearances/minutes invented for source-roster-only identities.'},
      'unresolved_source_conflicts':unresolved_conflicts,
      'nationality_policy':{'unresolved_country_id':['Willy Vincent / Mauritius'],'note':'Source-backed historical nationality is retained textually where the internal country catalogue has no verified mapping; arbitrary ids are prohibited.'},
      'photo_queue':{'bdf_individual_profiles_linked':sum(bool(x.get('bdf')) for x in P.values()),'new_source_only_without_bdf_profile':1,'policy':'Identified BDF individual profiles are marked ready_for_download; no portrait URL is fabricated.'},
      'identity_integrity':{'registry_rows':len(reg_ids),'queue_rows':len(q_ids),'registry_queue_match':set(reg_ids)==set(q_ids),'unique_registry_ids':len(reg_ids)==len(set(reg_ids))},
      'source_policy':['Continue Belgium club-by-club before Russia.','BDFutbol individual profile is preferred for biographical facts when present.','Transfermarkt season squad specializes broad positions, with source conflicts explicitly review-required.','Former Yugoslavia birth states are not rewritten as modern successor states.','Conflicting roster membership is held unresolved instead of being silently added.','No basketball 75/25 rule is used.']}
    dump(SNAP,snap); dump(REG,reg); dump(QUEUE,queue); dump(STAGE,stage)
    dump(DATA/'historical_profiles_metadata_audit_v037.json',audit); dump(DATA/'historical_metadata_gaps_v037.json',{'checkpoint':audit['checkpoint'],'gaps':after}); dump(DATA/'historical_biographies_audit_v037.json',{'checkpoint':audit['checkpoint'],'profiles_considered':len(P)+1,'status':'pass'}); dump(DATA/'belgium_source_conflicts_v037.json',{'checkpoint':audit['checkpoint'],'status':'pass','conflicts':unresolved_conflicts})
    print(json.dumps({'checkpoint':audit['checkpoint'],'curated_existing':len(P),'new_identities':1,'antwerp_stage_rows':len(club['players']),'belgium_gaps_before':before['Belgium'],'belgium_gaps_after':after['Belgium'],'role_corrections':audit['profiles']['role_corrections'],'review_required':audit['profiles']['review_required']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
