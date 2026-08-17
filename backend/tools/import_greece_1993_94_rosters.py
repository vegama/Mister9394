from __future__ import annotations
from collections import Counter
from datetime import date, datetime
from pathlib import Path
import hashlib, json, re, sys, unicodedata
from typing import Any

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'backend'))
from tools.review_created_player_profiles import ATTRS, materialise_attributes

DATA=ROOT/'data/football9394'
SNAP=DATA/'historical_snapshot.json'
STAGE=DATA/'greece_1993_94_roster_staging.json'
FOUNDATION=DATA/'greece_1993_94_league_foundation.json'
REGISTRY=DATA/'created_players_registry.json'
AUDIT=DATA/'greece_1993_94_roster_gate_audit.json'
CATALOG=DATA/'historical_source_catalog.json'
LEAGUE_ID=930047; GREECE_ID=47; OTHER_GREECE_ID=9400047; BATCH='greece_league_rosters_0.28'
SOURCE='https://www.rsssf.org/tablesg/grk94.html'

TEAM_IDS={
'AEK Athinon':9347001,'Panathinaikos':9347002,'Olympiakos Pireas':9347003,'Aris Thessalonikis':9347004,
'PAOK Thessalonikis':9347005,'Iraklis Thessalonikis':9347006,'OFI Irakliou':9347007,'Skoda Xanthi':9347008,
'Panionios':9347009,'AE Larisa':9347010,'Levadiakos':9347011,'Athinaikos':9347012,
'Apollon Athinas':9347013,'Edessaikos':9347014,'Doxa Dramas':9347015,'Panachaiki':9347016,
'Apollon Kalamarias':9347017,'Naousa':9347018,
}

# Explicit reconciliation only. Variants are source spellings from RSSSF; no surname-only fuzzy merging.
EXISTING={
('aek athinon','ilias atmatzidis'):9494176,('aek athinon','vaios karajiannis'):9494169,
('aek athinon','stelios manolas'):9494160,('aek athinon','tasos mitropoulos'):9494166,
('aek athinon','alekos alexandris'):9494177,('aek athinon','vassilis dimitriadis'):9494170,
('panathinaikos','stratos apostolakis'):9494158,('panathinaikos','thanasis kolitsidakis'):9494159,
('panathinaikos','jiannis kalitzakis'):9494161,('panathinaikos','spyros maragkos'):9494168,
('panathinaikos','mikos niomblias'):9494164,('panathinaikos','dimitris saravakos'):9494163,
('olympiakos pireas','koulis karantaidis'):9494174,('olympiakos pireas','minas chatzidis'):9494173,
('olympiakos pireas','jiotis tsalouchidis'):9494162,('olympiakos pireas','nikos tsiantakis'):9494167,
('aris thessalonikis','christos karkamanis'):9494171,('aris thessalonikis','savvas kofidis'):9494175,
('paok thessalonikis','alexis alexiou'):9494178,
('ofi irakliou','alexis alexoudis'):9494172,('ofi irakliou','nikos machlas'):9494165,
('apollon athinas','antonis minou'):9494157,
}

EXACT_ROLE_BY_EXISTING={
9494176:0,9494169:1,9494160:3,9494166:7,9494177:17,9494170:17,
9494158:1,9494159:3,9494161:3,9494168:7,9494164:7,9494163:8,
9494174:2,9494173:13,9494162:7,9494167:13,9494171:0,9494175:6,
9494178:3,9494172:17,9494165:17,9494157:0,
}
# Cross-source identity corrections verified against BDFutbol and independent references.
DOB_OVERRIDES={9494159:'1966-11-21',9494175:'1961-02-05'}
ROLE_OVERRIDE={
('aek athinon','vassilis tsartas'):8,('aek athinon','michalis kasapis'):2,
('panathinaikos','jiorgos georgiadis charal'):9,('panathinaikos','jiorgos donis'):12,
('olympiakos pireas','vassilis karapialis'):8,('olympiakos pireas','daniel lima batista'):8,
('paok thessalonikis','theodoros zagorakis'):7,('panachaiki','grigoris georgatos'):13,
('skoda xanthi','zisis vryzas'):17,
}
ROLE_TO_BROAD={0:'POR',1:'DEF',2:'DEF',3:'DEF',4:'DEF',5:'DEF',6:'MED',7:'MED',8:'MED',9:'MED',10:'MED',11:'DEL',12:'DEL',13:'MED',14:'MED',15:'DEL',16:'DEL',17:'DEL'}
ROLE_TO_LABEL={0:'Goalkeeper',1:'Right Back',2:'Left Back',3:'Centre Back',4:'Centre Back',5:'Libero',6:'Defensive Midfielder',7:'Centre Midfielder',8:'Attacking Midfielder',9:'Right Midfielder',10:'Right Inside',11:'Right Attacking Midfielder',12:'Right Winger',13:'Left Midfielder',14:'Left Inside',15:'Left Attacking Midfielder',16:'Left Winger',17:'Centre Forward'}
BASE={1:75,2:75,3:75,4:72,5:72,6:71,7:70,8:69,9:68,10:67,11:66,12:66,13:65,14:65,15:64,16:63,17:62,18:61}

def norm(v:Any)->str:
    s=unicodedata.normalize('NFKD',str(v or ''));s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',re.sub(r'[^a-zA-Z0-9]+',' ',s).strip().lower())

def split_name(s:str):
    p=s.split();return ((' '.join(p[:-1]) or None),p[-1] if p else None)

def ratings(role:int):
    o={str(i):0 for i in range(18)};o[str(role)]=100
    adj={0:{},1:{3:60,9:55},2:{4:60,13:55},3:{4:75,5:60,6:45},4:{3:75,5:60,6:45},5:{3:75,4:75,6:60},6:{7:75,3:50,4:50},7:{6:70,8:65,9:45,13:45},8:{7:65,11:55,15:55,17:45},9:{12:75,7:55,8:50,1:45},10:{9:80,12:65,7:55},11:{12:80,9:65,8:65,17:50},12:{9:75,11:65,17:50},13:{16:75,7:55,8:50,2:45},14:{13:80,16:65,7:55},15:{16:80,13:65,8:65,17:50},16:{13:75,15:65,17:50},17:{11:45,15:45,12:35,16:35,8:30}}
    for k,v in adj[role].items():o[str(k)]=v
    return o

def age_on_1993_08_22(birth_date):
    if not birth_date:return None
    try:d=datetime.fromisoformat(str(birth_date).replace('Z','+00:00')).date()
    except Exception:return None
    at=date(1993,8,22);return at.year-d.year-((at.month,at.day)<(d.month,d.day))

def overall(pos:int,row:dict,role:int)->int:
    b=BASE[pos];apps=int(row.get('appearances') or 0);goals=int(row.get('goals') or 0)
    b += 2 if apps>=28 else 1 if apps>=20 else 0 if apps>=12 else -1 if apps>=6 else -2
    if role!=0:
        b += 4 if goals>=20 else 3 if goals>=12 else 2 if goals>=8 else 1 if goals>=5 else 0
    return max(58,min(81,b))

def attrs_for(originals,player,target,serial):
    pool=[p for p in originals if p.get('broad_position')==player['broad_position'] and p.get('attributes') and abs(int(p.get('overall') or 0)-target)<=5]
    if len(pool)<2:pool=[p for p in originals if p.get('broad_position')==player['broad_position'] and p.get('attributes')]
    pool.sort(key=lambda p:(abs(int(p.get('overall') or 0)-target),int(p.get('source_id') or 0)));lim=min(len(pool),28)
    if lim<2:raise RuntimeError('No comparable profiles')
    a=pool[(serial*7)%lim];b=pool[(serial*13+5)%lim]
    if a['source_id']==b['source_id']:b=pool[(pool.index(a)+1)%lim]
    at=materialise_attributes(target,a,b);d=hashlib.sha256(f"gre:{player['display_name']}:{serial}".encode()).digest()
    for i,k in enumerate(('consistency','work_rate','anticipation','technique')):at[k]=max(20,min(99,int(at[k])+(-1,0,1)[d[i]%3]))
    return at,[int(a['source_id']),int(b['source_id'])]

def make_team(name,tid,pos):
    init=''.join(w[0] for w in re.findall(r'[A-Za-z]+',name)[:3]).upper() or name[:3].upper()
    budget={1:52000000,2:50000000,3:52000000,4:28000000,5:30000000,6:24000000}.get(pos,max(7000000,22000000-(pos-7)*1100000))
    return {'source_id':tid,'name':name,'long_name':name,'short_name':name,'initials':init,'league_id':LEAGUE_ID,'league_position':pos,'stadium_id':None,'manager_id':None,'members':0,'budget':budget,'debt':None,'reserve_of':None,'reserve_step':0,'academy_level':1,'squad_building_style':2,'sporting_director_level':0,'women_flag':False,'activation_reason':'historical_greece_1993_94_roster_gate','familiar_name':name,'very_short_name':name,'president':None,'secondary_stadium_id':None,'training_ground':None,'youth_residence':None,'main_rival_id':None,'regional_rival_id':None,'honours':{},'academy_style':2,'special_academy_pattern_id':None,'initial_points_sanction':None,'fifa_registration_ban_until':None,'country_id':GREECE_ID,'historical_season':'1993-94','historical_position':pos,'historical_identity_source':'RSSSF Greece 1993/94 roster section; gate v0.28'}

def main():
    snap=json.load(open(SNAP,encoding='utf8'));stage=json.load(open(STAGE,encoding='utf8'));registry=json.load(open(REGISTRY,encoding='utf8'));catalog=json.load(open(CATALOG,encoding='utf8'))
    countries={int(c['source_id']):c['name'] for c in catalog['countries']}
    players=snap['players'];byid={int(p['source_id']):p for p in players};originals=[p for p in players if not p.get('external_origin') and not p.get('creation_batch')]
    regby={int(r['source_id']):r for r in registry['players'] if r.get('source_id') is not None};nextid=max(byid)+1
    used={tuple(int((p.get('attributes') or {}).get(k,-1)) for k in ATTRS) for p in players if p.get('attributes')}
    created=reused=reprofiled=0;resolved=set();idents=[];role_sources=Counter();dob_conflicts=[];foreign=0
    for ci,c in enumerate(stage['clubs']):
        name=c['name'];tid=TEAM_IDS[name];pos=int(c['historical_position'])
        for ri,row in enumerate(c['players']):
            key=(norm(name),norm(row['rsssf_name']));eid=EXISTING.get(key);p=byid.get(eid) if eid else None
            if eid and not p:raise RuntimeError(f'Missing explicit Greek existing id {eid}')
            if eid:
                role=EXACT_ROLE_BY_EXISTING[eid];role_source='verified_existing_historical_specialist_role'
            else:
                role=ROLE_OVERRIDE.get(key,int(row['suggested_primary_role']));role_source='source_section_specialist_inference' if key not in ROLE_OVERRIDE else 'verified_role_override'
            broad=ROLE_TO_BROAD[role];target=overall(pos,row,role)
            if p is None:
                sid=nextid;nextid+=1;first,surname=split_name(row['rsssf_name']);cid=int(row.get('country_id') or GREECE_ID)
                p={'source_id':sid,'team_id':tid,'display_name':row['rsssf_name'],'first_name':first,'surname1':surname,'surname2':None,'birth_date':row.get('birth_date'),'birth_country_id':cid,'international_country_id':cid,'preferred_foot':None,'shirt_number':None,'primary_role':role,'broad_position':broad,'overall':target,'category':target,'height_cm':None,'weight_kg':None,'salary':0,'release_clause':0,'contract_start_year':1993,'contract_end_year':None,'loan':False,'initially_reserve':int(row.get('appearances') or 0)<8,'retired':False,'attributes':{},'role_ratings':ratings(role),'hidden_traits':{'individualist':False,'killer_pass':False,'holds_ball':False,'long_shots':False,'cuts_inside':False,'first_time_play':False,'dives':False},'external_origin':'historical_greece_1993_94','creation_batch':BATCH,'profile_review_required':False,'nationality_resolution':'rsssf_roster_nationality_note_or_greek_default'}
                # Daniel Batista was Brazilian-born but represented Greece; model him as naturalized Greek, not as a foreign international.
                if norm(row['rsssf_name'])=='daniel lima batista':
                    p['birth_country_id']=62;p['international_country_id']=47;p['naturalized_country_id']=47;p['nationality_resolution']='historical_naturalized_greece'
                at,comps=attrs_for(originals,p,target,ci*31+ri);vec=tuple(at[k] for k in ATTRS);bump=0
                while vec in used:
                    k=ATTRS[(ci+ri+bump)%len(ATTRS)];at[k]=min(99,at[k]+1);vec=tuple(at[k] for k in ATTRS);bump+=1
                used.add(vec);p['attributes']=at;p['attribute_source']='fixed_source_comparable_greece_1993_94';p['attribute_comparable_source_ids']=comps
                players.append(p);byid[sid]=p;created+=1
            else:
                sid=eid;reused+=1;p['retired']=False;p.pop('historical_exclusion_reason',None)
                if sid in DOB_OVERRIDES:
                    p['birth_date']=DOB_OVERRIDES[sid]
                    p['birth_date_source']='cross_source_bdfutbol_verified_v0.28'
                # Preserve the verified identity/DOB/nationality, while recording source conflicts and allowing a season-performance recalibration upward.
                if row.get('birth_date') and p.get('birth_date') and str(row['birth_date'])[:10]!=str(p['birth_date'])[:10]:
                    dob_conflicts.append({'source_id':sid,'display_name':p['display_name'],'rsssf_birth_date':row['birth_date'],'kept_verified_birth_date':p['birth_date'],'resolution':'cross_source_verified_identity'})
                old=int(p.get('overall') or 0)
                if target>old:
                    p['overall']=target;p['category']=target
                    p['primary_role']=role;p['broad_position']=broad;p['role_ratings']=ratings(role)
                    at,comps=attrs_for(originals,p,target,ci*31+ri);p['attributes']=at;p['attribute_source']='fixed_source_comparable_greece_1993_94_recalibrated';p['attribute_comparable_source_ids']=comps;reprofiled+=1
                else:
                    p['primary_role']=role;p['broad_position']=broad;p['role_ratings']=ratings(role)
            resolved.add(sid);role_sources[role_source]+=1
            hist_age=age_on_1993_08_22(p.get('birth_date'))
            p.update({'team_id':tid,'historical_club_1994':name,'historical_position_1993_94':ROLE_TO_LABEL[role],'historical_position_source':role_source,'rsssf_name_1993_94':row['rsssf_name'],'historical_age_1993_94':hist_age if hist_age is not None else row.get('historical_age_1993_94'),'historical_club_spells_1993_94':[{'club':name,'team_id':tid,'appearances':int(row.get('appearances') or 0),'goals':int(row.get('goals') or 0)}],'historical_data_source':'RSSSF Greece 1993/94 roster section; identity/position audit v0.28','historical_source_url':SOURCE,'profile_review_required':False})
            if int(p.get('international_country_id') or p.get('birth_country_id') or 47)!=47:foreign+=1
            row.update({'identity_resolution':'reused_verified_greece_pool' if eid else 'created_historical_identity','resolved_source_id':sid,'resolved_display_name':p['display_name'],'resolved_primary_role':role,'resolved_exact_position':ROLE_TO_LABEL[role],'position_source':role_source,'resolved_birth_date':p.get('birth_date'),'resolved_country_id':p.get('international_country_id') or p.get('birth_country_id')})
            r=regby.get(sid)
            if not (p.get('external_origin') or p.get('creation_batch')):
                if r is not None:
                    registry['players'].remove(r);regby.pop(sid,None)
                r=None
            elif r is None:
                r={'source_id':sid};registry['players'].append(r);regby[sid]=r
            cid=int(p.get('international_country_id') or p.get('birth_country_id') or 47)
            if r is not None:r.update({'display_name':p['display_name'],'first_name':p.get('first_name'),'surname1':p.get('surname1'),'surname2':p.get('surname2'),'birth_date':p.get('birth_date'),'country_id':cid,'country_name':countries.get(cid),'broad_position':broad,'team_id':tid,'team_name':name,'creation_batch':p.get('creation_batch'),'identity_source':p['historical_data_source'],'identity_source_url':SOURCE,'verified_national_pool_year':1994 if cid==47 else None,'historical_position_1993_94':p['historical_position_1993_94'],'historical_club_1994':name,'overall':p.get('overall'),'attribute_source':p.get('attribute_source'),'profile_review_required':False,'duplicate_check':'greece_1993_94_explicit_identity_gate','matched_existing_id':sid if eid else None,'bdfutbol_search_name':p['display_name'],'bdfutbol_id':str(p.get('bdfutbol_id') or ''),'bdfutbol_url':p.get('bdfutbol_url',''),'photo_filename':f'{sid}.jpg','photo_status':'ready_for_download' if p.get('bdfutbol_id') else 'pending_identity_profile'})
            idents.append({'club':name,'rsssf_name':row['rsssf_name'],'source_id':sid,'display_name':p['display_name'],'role':role,'position':ROLE_TO_LABEL[role],'position_source':role_source,'appearances':row['appearances'],'goals':row['goals'],'country_id':cid})
    # The 22 verified Greece-pool players are all selected in the 18x18 core. They must no longer remain in Otros-Grecia.
    stranded=[p for p in players if int(p.get('team_id') or 0)==OTHER_GREECE_ID and not p.get('retired') and int(p.get('source_id') or 0) in set(EXISTING.values())]
    if stranded:raise RuntimeError('Verified Greek pool players stranded in Otros-Grecia: '+','.join(p['display_name'] for p in stranded))
    team_index={int(t['source_id']):i for i,t in enumerate(snap['teams'])}
    for c in stage['clubs']:
        tid=TEAM_IDS[c['name']];team=make_team(c['name'],tid,int(c['historical_position']))
        if tid in team_index:snap['teams'][team_index[tid]]=team
        else:snap['teams'].append(team)
    snap['leagues']=[l for l in snap['leagues'] if int(l.get('source_id') or 0)!=LEAGUE_ID]
    snap['leagues'].append({'source_id':LEAGUE_ID,'country_id':47,'country':'Grecia','name':'Alpha Ethniki','short_name':'Alpha Ethniki','level':1,'team_count':18,'turns':2,'yellow_card_cycle':3,'max_foreigners_starting':None,'max_foreigners_squad':None,'prefer_nationals':True,'source_start':'1993-08-22T00:00:00','source_end':'1994-04-24T00:00:00','source_edition':'1993-94','admitted':True,'signable':True,'source_rule_hints':{'historical_runtime_id':True,'points_win':3,'direct_relegation_places':[16,17,18],'foreign_rule_status':'candidate 3 strongly corroborated; exact Greek 1993-94 domestic numeric clause not recovered, so no guessed limit encoded','foreign_rule_evidence_file':'greece_1993_94_foreign_rule_evidence.json','foreign_domestic_equivalent_country_ids':[25],'foreign_domestic_equivalence_status':'Cypriots source-supported as non-foreign and encoded for domestic Greek competitions','roster_source':'RSSSF Greece 1993/94'}})
    snap['leagues'].sort(key=lambda l:int(l.get('source_id') or 0))
    foundation={'schema_version':1,'purpose':'Activate the complete 1993-94 Greek Alpha Ethniki only after an 18-real-player-per-club gate.','policy':{'fictional_fillers':False,'minimum_real_players_per_club':18,'identity_reconciliation':'explicit verified reuse only; no surname-only merge','specialist_positions':'verified where available; otherwise inferred inside the RSSSF broad roster section and marked as inference','ratings':'fixed source-comparable materialised attributes; season performance anchor; no football 75/25 rule'},'league':{'key':'gre_1993_94','name':'Alpha Ethniki','country':'Grecia','source_league_id':None,'historical_runtime_league_id':LEAGUE_ID,'historical_season':'1993-94','teams':18,'rounds':34,'points_win':3,'direct_relegation_places':[16,17,18],'activation_status':'active_historical_roster_gate_passed','roster_gate_minimum_players_per_club':18,'source_url':SOURCE,'clubs':[]}}
    counts={};role_counts={}
    for c in stage['clubs']:
        name=c['name'];tid=TEAM_IDS[name];rows=[p for p in players if int(p.get('team_id') or 0)==tid and not p.get('retired')]
        counts[name]=len(rows);role_counts[name]=dict(Counter(ROLE_TO_LABEL[int(p.get('primary_role') or 0)] for p in rows))
        if len(rows)<18:raise RuntimeError(f'{name}: only {len(rows)} active')
        foundation['league']['clubs'].append({'historical_position':int(c['historical_position']),'name':name,'rsssf_roster_url':SOURCE,'roster_status':'complete_historical_1993_94','team_id':tid})
    audit={'schema_version':1,'season':'1993-94','league_id':LEAGUE_ID,'status':'pass_greece_1993_94_active','staged_rows':sum(len(c['players']) for c in stage['clubs']),'unique_staged_identities':len({int(r['resolved_source_id']) for c in stage['clubs'] for r in c['players']}),'clubs':18,'minimum_required':18,'minimum_active_roster':min(counts.values()),'roster_counts':counts,'role_counts':role_counts,'reused_existing_players':reused,'created_players':created,'reprofiled_existing_players':reprofiled,'verified_greece_pool_stranded_in_otros':len(stranded),'foreign_players_in_core':foreign,'dob_source_conflicts_kept_verified_identity':dob_conflicts,'position_provenance':dict(role_sources),'identities':idents,'duplicate_policy':'explicit verified reuse of the 22 pre-existing Greece 1994 pool identities; no fuzzy surname merging','rating_policy':'fixed source-comparable materialised attributes on the original game scale, anchored by 1993-94 appearances/goals and club level; no football 75/25 rule','source_url':SOURCE,'rule_evidence':{'points_win':3,'teams':18,'rounds':34,'relegated_positions':[16,17,18],'foreigners':{'evidence_file':'greece_1993_94_foreign_rule_evidence.json','candidate_limit':3,'primary_domestic_numerical_clause_recovered':False,'runtime_encoded':False}}}
    if audit['staged_rows']!=324 or audit['unique_staged_identities']!=324:raise RuntimeError('Greece cardinality failed')
    if reused!=22:raise RuntimeError(f'Expected 22 verified Greek pool reuses, got {reused}')
    for path,obj in ((SNAP,snap),(STAGE,stage),(FOUNDATION,foundation),(REGISTRY,registry),(AUDIT,audit)):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:audit[k] for k in ('status','staged_rows','unique_staged_identities','minimum_active_roster','reused_existing_players','created_players','reprofiled_existing_players','foreign_players_in_core','position_provenance')},ensure_ascii=False,indent=2))
    print(json.dumps(counts,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
