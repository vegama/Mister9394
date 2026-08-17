from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib,json,re,sys,unicodedata
from typing import Any

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'backend'))
from tools.review_created_player_profiles import ATTRS, materialise_attributes
DATA=ROOT/'data/football9394'; SNAP=DATA/'historical_snapshot.json'; STAGE=DATA/'turkey_1993_94_roster_staging.json'; FOUNDATION=DATA/'bel_tur_rus_1993_94_league_foundations.json'; REGISTRY=DATA/'created_players_registry.json'; AUDIT=DATA/'turkey_1993_94_roster_gate_audit.json'
LEAGUE_ID=930057; TURKEY_ID=84; OTHER_TURKEY_ID=9400084; BATCH='turkey_league_rosters_0.26'
TEAM_IDS={'Galatasaray':645,'Fenerbahçe':9357001,'Trabzonspor':9357002,'Beşiktaş':644,'Samsunspor':9357003,'Kocaelispor':9357004,'Gençlerbirliği':9357005,'Gaziantepspor':9357006,'Bursaspor':9357007,'Altay':9357008,'Ankaragücü':9357009,'Kayserispor':9357010,'Zeytinburnuspor':9357011,'Karabükspor':9357012,'Karşıyaka':9357013,'Sarıyer':9357014}
EXISTING={
('galatasaray','hayrettin'):9495316,('galatasaray','bulent'):9495319,('galatasaray','hamzaoglu'):9495337,('galatasaray','suat'):9495336,('galatasaray','tugay'):9495331,('galatasaray','tepekule'):9495327,('galatasaray','sukur'):9495348,('galatasaray','erdem'):9495354,('galatasaray','tutuneker'):9495342,
('fenerbahce','ipekoglu'):9495315,('fenerbahce','yagcioglu'):9495343,('fenerbahce','asik'):9495325,('fenerbahce','oguz'):9495332,('fenerbahce','uygun'):9495352,('fenerbahce','kocaman'):9495351,
('trabzonspor','ercan'):9495335,('trabzonspor','ogun'):9495321,('trabzonspor','cikirkci'):9495346,('trabzonspor','karaman'):9495333,('trabzonspor','kafkas'):9495344,('trabzonspor','mandirali'):9495349,('trabzonspor','atila'):9495328,
('besiktas','cetin'):9495320,('besiktas','topcu'):9495330,('besiktas','guncar'):9495322,('besiktas','keskin'):9495323,('besiktas','calimbay'):9495338,('besiktas','ozdilek'):9495334,('besiktas','ucar'):9495347,('besiktas','yalcin'):9495345,
('samsunspor','saglam'):9495350,('kocaelispor','sancakli'):9495353,('bursaspor','balkanli'):9495326,('altay','goymen'):9495318,('ankaragucu','guller'):9495324}
ROLE_TO_BROAD={0:'POR',1:'DEF',2:'DEF',3:'DEF',4:'DEF',5:'DEF',6:'MED',7:'MED',8:'MED',9:'MED',10:'MED',11:'DEL',12:'DEL',13:'MED',14:'MED',15:'DEL',16:'DEL',17:'DEL'}
ROLE_TO_LABEL={0:'Goalkeeper',1:'Right Back',2:'Left Back',3:'Centre Back',4:'Centre Back',5:'Libero',6:'Defensive Midfielder',7:'Centre Midfielder',8:'Attacking Midfielder',9:'Right Midfielder',10:'Right Inside',11:'Right Attacking Midfielder',12:'Right Winger',13:'Left Midfielder',14:'Left Inside',15:'Left Attacking Midfielder',16:'Left Winger',17:'Centre Forward'}
HIST={'goalkeeper':0,'right back':1,'left back':2,'centre back':3,'center back':3,'central defender':3,'defender':3,'libero':5,'sweeper':5,'defensive midfielder':6,'centre midfielder':7,'center midfielder':7,'central midfielder':7,'midfielder':7,'attacking midfielder':8,'right midfielder':9,'right winger':12,'left midfielder':13,'left winger':16,'centre forward':17,'center forward':17,'forward':17,'secondary striker':17}
XI=(0,1,3,4,2,9,7,7,13,17,17); BASE={1:77,2:76,3:75,4:75,5:71,6:72,7:71,8:70,9:70,10:69,11:69,12:68,13:67,14:66,15:66,16:66}
CLUB_ALIAS={'galatasaray sk':'Galatasaray','galatasaray':'Galatasaray','fenerbahce sk':'Fenerbahçe','fenerbahce':'Fenerbahçe','trabzonspor':'Trabzonspor','besiktas jk':'Beşiktaş','besiktas':'Beşiktaş','samsunspor':'Samsunspor','kocaelispor':'Kocaelispor','genclerbirligi':'Gençlerbirliği','gaziantepspor':'Gaziantepspor','bursaspor':'Bursaspor','altay izmir':'Altay','altay':'Altay','ankaragucu':'Ankaragücü','kayserispor':'Kayserispor','zeytinburnuspor':'Zeytinburnuspor','karabukspor':'Karabükspor','karsiyaka':'Karşıyaka','sariyer':'Sarıyer'}


def norm(v:Any)->str:
 s=unicodedata.normalize('NFKD',str(v or '').replace('ı','i').replace('İ','I')); s=''.join(c for c in s if not unicodedata.combining(c)); return re.sub(r'\s+',' ',re.sub(r'[^a-zA-Z0-9]+',' ',s).strip().lower())

def split_name(s:str):
 p=s.split(); return ((' '.join(p[:-1]) or None),p[-1] if p else None)

def ratings(role:int):
 o={str(i):0 for i in range(18)};o[str(role)]=100
 adj={0:{},1:{3:60,9:55},2:{4:60,13:55},3:{4:75,5:60,6:45},4:{3:75,5:60,6:45},5:{3:75,4:75,6:60},6:{7:75,3:50,4:50},7:{6:70,8:65,9:45,13:45},8:{7:65,11:55,15:55,17:45},9:{12:75,7:55,8:50,1:45},10:{9:80,12:65,7:55},11:{12:80,9:65,8:65,17:50},12:{9:75,11:65,17:50},13:{16:75,7:55,8:50,2:45},14:{13:80,16:65,7:55},15:{16:80,13:65,8:65,17:50},16:{13:75,15:65,17:50},17:{11:45,15:45,12:35,16:35,8:30}}
 for k,v in adj[role].items():o[str(k)]=v
 return o

def overall(pos,row):
 b=BASE[pos];starts=int(row.get('starts') or 0);apps=int(row.get('appearances') or 0);goals=int(row.get('goals') or 0)
 b+=2 if starts>=24 else 1 if starts>=15 else -2 if apps<8 else -1 if apps<15 else 0
 if goals>=15:b+=2
 elif goals>=7:b+=1
 return max(60,min(81,b))

def attrs_for(originals,player,ov,serial):
 pool=[p for p in originals if p.get('broad_position')==player['broad_position'] and p.get('attributes') and abs(int(p.get('overall') or 0)-ov)<=5]
 if len(pool)<2:pool=[p for p in originals if p.get('broad_position')==player['broad_position'] and p.get('attributes')]
 pool.sort(key=lambda p:(abs(int(p.get('overall') or 0)-ov),int(p.get('source_id') or 0)));lim=min(len(pool),24)
 if lim<2:raise RuntimeError('No comparable profiles')
 a=pool[(serial*7)%lim];b=pool[(serial*13+5)%lim]
 if a['source_id']==b['source_id']:b=pool[(pool.index(a)+1)%lim]
 at=materialise_attributes(ov,a,b);d=hashlib.sha256(f"{player['display_name']}:{serial}".encode()).digest()
 for i,k in enumerate(('consistency','work_rate','anticipation','technique')):at[k]=max(20,min(99,int(at[k])+(-1,0,1)[d[i]%3]))
 return at,[int(a['source_id']),int(b['source_id'])]

def role_for(row,idx,serial,p=None):
 if p:
  h=HIST.get(norm(p.get('historical_position_1993_94')))
  if h is not None:return h,'existing_historical_position'
  try:
   h=int(p.get('primary_role'));assert 0<=h<=17;return h,'existing_specialist_role'
  except:pass
 if int(row.get('goals') or 0)<0:return 0,'bdfutbol_goalkeeper_stat'
 if idx<11:return XI[idx],'bdfutbol_lineup_order_inference'
 g=int(row.get('goals') or 0);a=int(row.get('appearances') or 0)
 if g>=max(5,int(a*.25)):return 17,'bdfutbol_goal_output_inference'
 cycle=(3,4,1,2,7,6,9,13,8,17,12,16);return cycle[(idx-11+serial)%len(cycle)],'squad_balance_inference'

def make_team(old,name,tid,pos):
 x=dict(old or {});init=''.join(w[0] for w in name.replace('-',' ').split()[:3]).upper()
 x.update({'source_id':tid,'name':name,'long_name':name,'short_name':name,'initials':x.get('initials') or init,'league_id':LEAGUE_ID,'league_position':pos,'manager_id':None,'members':int(x.get('members') or 0),'budget':int(x.get('budget') or {1:70000000,2:68000000,3:50000000,4:60000000}.get(pos,16000000)),'debt':x.get('debt'),'reserve_of':None,'reserve_step':0,'academy_level':int(x.get('academy_level') or 1),'squad_building_style':int(x.get('squad_building_style') or 2),'sporting_director_level':int(x.get('sporting_director_level') or 0),'women_flag':False,'activation_reason':'historical_turkey_1993_94_roster_gate','familiar_name':name,'very_short_name':name,'president':x.get('president'),'secondary_stadium_id':x.get('secondary_stadium_id'),'training_ground':x.get('training_ground'),'youth_residence':x.get('youth_residence'),'main_rival_id':x.get('main_rival_id'),'regional_rival_id':x.get('regional_rival_id'),'honours':x.get('honours') or {},'academy_style':int(x.get('academy_style') or 2),'special_academy_pattern_id':None,'initial_points_sanction':None,'fifa_registration_ban_until':None,'country_id':TURKEY_ID,'historical_season':'1993-94','historical_position':pos,'historical_identity_source':'BDFutbol 1993-94 squad; roster gate v0.26'})
 return x

def main():
 snap=json.load(open(SNAP,encoding='utf8'));stage=json.load(open(STAGE,encoding='utf8'));foundation=json.load(open(FOUNDATION,encoding='utf8'));registry=json.load(open(REGISTRY,encoding='utf8'))
 players=snap['players'];byid={int(p['source_id']):p for p in players};oldteams={int(t['source_id']):t for t in snap['teams']}; originals=[p for p in players if not p.get('external_origin') and not p.get('creation_batch')]
 regby={int(r['source_id']):r for r in registry['players'] if r.get('source_id') is not None};history_name_candidates={};history_by_signature={}
 for hp in players:
  if not hp.get('bdfutbol_name_1993_94'):continue
  hkey=(int(hp.get('team_id') or 0),norm(hp.get('bdfutbol_name_1993_94')));history_name_candidates.setdefault(hkey,[]).append(int(hp['source_id']))
  spells=hp.get('historical_club_spells_1993_94') or []
  if spells:
   sp=spells[0];sig=hkey+(int(hp.get('historical_age_1993_94') or -1),int(sp.get('appearances') or 0),int(sp.get('starts') or 0),int(sp.get('minutes') or 0),int(sp.get('goals') or 0));history_by_signature[sig]=int(hp['source_id'])
 nextid=max(byid)+1;used={tuple(int((p.get('attributes') or {}).get(k,-1)) for k in ATTRS) for p in players if p.get('attributes')}
 safe=set(EXISTING.values());mixed=0
 for p in players:
  if int(p.get('team_id') or 0) in {644,645} and int(p['source_id']) not in safe:
   mixed+=not bool(p.get('retired'));p['retired']=True;p['historical_exclusion_reason']='mixed_era_mdb_not_verified_turkey_1993_94'
 created=reused=0;roles=Counter();resolved=set();ident=[]
 for ci,c in enumerate(stage['clubs']):
  name=c['name'];tid=TEAM_IDS[name];pos=int(c['historical_position'])
  for idx,row in enumerate(c['players']):
   verified_eid=EXISTING.get((norm(name),norm(row['bdfutbol_name'])));staged_eid=int(row.get('resolved_source_id') or 0) or None;hkey=(tid,norm(row['bdfutbol_name']));hsig=hkey+(int(row.get('age_1993_94') or -1),int(row.get('appearances') or 0),int(row.get('starts') or 0),int(row.get('minutes') or 0),int(row.get('goals') or 0));historical_eid=history_by_signature.get(hsig);candidates=history_name_candidates.get(hkey,[]);historical_eid=historical_eid or (candidates[0] if len(candidates)==1 else None)
   if verified_eid and staged_eid and staged_eid!=verified_eid and staged_eid in byid:
    dup=byid[staged_eid];dup['retired']=True;dup['historical_exclusion_reason']='duplicate_identity_reconciled_v0.30';dup['merged_into_source_id']=verified_eid
   eid=verified_eid or (staged_eid if staged_eid in byid else None) or (historical_eid if historical_eid in byid else None);p=byid.get(eid) if eid else None;role,rs=role_for(row,idx,ci*31+idx,p);roles[rs]+=1;broad=ROLE_TO_BROAD[role]
   if p is None:
    sid=nextid;nextid+=1;display=row.get('identity_hint') if norm(row.get('identity_hint')) in {'shota arveladze','archil arveladze'} else str(row['bdfutbol_name']);first,surname=split_name(display);ov=overall(pos,row)
    p={'source_id':sid,'team_id':tid,'display_name':display,'first_name':first,'surname1':surname,'surname2':None,'birth_date':None,'birth_country_id':None,'international_country_id':None,'preferred_foot':None,'shirt_number':None,'primary_role':role,'broad_position':broad,'overall':ov,'category':ov,'height_cm':None,'weight_kg':None,'salary':0,'release_clause':0,'contract_start_year':1993,'contract_end_year':None,'loan':False,'initially_reserve':int(row.get('starts') or 0)<8,'retired':False,'attributes':{},'role_ratings':ratings(role),'hidden_traits':{'individualist':False,'killer_pass':False,'holds_ball':False,'long_shots':False,'cuts_inside':False,'first_time_play':False,'dives':False},'external_origin':'historical_turkey_1993_94','creation_batch':BATCH,'profile_review_required':False}
    at,comps=attrs_for(originals,p,ov,ci*31+idx);vec=tuple(at[k] for k in ATTRS);bump=0
    while vec in used:
     k=ATTRS[(ci+idx+bump)%len(ATTRS)];at[k]=min(99,at[k]+1);vec=tuple(at[k] for k in ATTRS);bump+=1
    used.add(vec);p['attributes']=at;p['attribute_source']='fixed_source_comparable_turkey_1993_94';p['attribute_comparable_source_ids']=comps;players.append(p);byid[sid]=p;created+=1
   else:
    sid=eid;reused+=1;p['retired']=False;p.pop('historical_exclusion_reason',None);p['primary_role']=role;p['broad_position']=broad;p['role_ratings']=ratings(role)
   resolved.add(sid);p.update({'team_id':tid,'historical_club_1994':name,'historical_position_1993_94':ROLE_TO_LABEL[role],'historical_position_source':rs,'bdfutbol_name_1993_94':row['bdfutbol_name'],'historical_age_1993_94':int(row.get('age_1993_94') or -1),'historical_club_spells_1993_94':[{'club':name,'team_id':tid,'appearances':int(row.get('appearances') or 0),'starts':int(row.get('starts') or 0),'minutes':int(row.get('minutes') or 0),'goals':int(row.get('goals') or 0)}],'historical_data_source':'BDFutbol 1993-94 squad; identity/position audit v0.26','bdfutbol_squad_url':c['bdfutbol_squad_url'],'profile_review_required':False})
   row.update({'identity_resolution':'reused_verified_national_depth' if verified_eid else ('reused_staged_identity' if eid else 'created_historical_identity'),'resolved_source_id':sid,'resolved_display_name':p['display_name'],'resolved_primary_role':role,'resolved_exact_position':ROLE_TO_LABEL[role],'position_source':rs})
   r=regby.get(sid)
   if not (p.get('external_origin') or p.get('creation_batch')):
    if r is not None:registry['players'].remove(r);regby.pop(sid,None)
    r=None
   elif r is None:r={'source_id':sid};registry['players'].append(r);regby[sid]=r
   if r is not None:r.update({'display_name':p['display_name'],'first_name':p.get('first_name'),'surname1':p.get('surname1'),'surname2':p.get('surname2'),'birth_date':p.get('birth_date'),'country_id':p.get('international_country_id') or p.get('birth_country_id'),'country_name':'Turquía' if (p.get('international_country_id') or p.get('birth_country_id'))==84 else None,'broad_position':broad,'team_id':tid,'team_name':name,'creation_batch':p.get('creation_batch'),'identity_source':p['historical_data_source'],'identity_source_url':c['bdfutbol_squad_url'],'verified_national_pool_year':1994,'historical_position_1993_94':p['historical_position_1993_94'],'historical_club_1994':name,'overall':p.get('overall'),'attribute_source':p.get('attribute_source'),'profile_review_required':False,'duplicate_check':'turkey_1993_94_explicit_identity_gate','matched_existing_id':sid if verified_eid else None,'bdfutbol_search_name':p['display_name'],'bdfutbol_id':str(p.get('bdfutbol_id') or ''),'bdfutbol_url':p.get('bdfutbol_url',''),'photo_filename':f'{sid}.jpg','photo_status':'ready_for_download' if p.get('bdfutbol_id') else 'pending_identity_profile'})
   ident.append({'club':name,'bdfutbol_name':row['bdfutbol_name'],'identity_hint':row.get('identity_hint'),'source_id':sid,'display_name':p['display_name'],'role':role,'position':ROLE_TO_LABEL[role],'position_source':rs})
 extras=[]
 for p in players:
  sid=int(p.get('source_id') or 0)
  if sid in resolved or int(p.get('international_country_id') or 0)!=84:continue
  if p.get('creation_batch') not in {'bel_tur_rus_national_depth_0.24','world_cup_1994'}:continue
  club=CLUB_ALIAS.get(norm(p.get('historical_club_1994')))
  if not club:continue
  p['team_id']=TEAM_IDS[club];p['retired']=False;p.pop('historical_exclusion_reason',None);r=regby.get(sid)
  if r:r.update({'team_id':TEAM_IDS[club],'team_name':club,'historical_club_1994':club})
  extras.append({'source_id':sid,'display_name':p['display_name'],'club':club})
 idx={int(t['source_id']):i for i,t in enumerate(snap['teams'])}
 for c in stage['clubs']:
  tid=TEAM_IDS[c['name']];t=make_team(oldteams.get(tid),c['name'],tid,int(c['historical_position']))
  if tid in idx:snap['teams'][idx[tid]]=t
  else:snap['teams'].append(t)
 snap['leagues']=[l for l in snap['leagues'] if int(l.get('source_id') or 0) not in {57,LEAGUE_ID}];snap['leagues'].append({'source_id':LEAGUE_ID,'country_id':84,'country':'Turquía','name':'1. Lig','short_name':'1. Lig','level':1,'team_count':16,'turns':2,'yellow_card_cycle':3,'max_foreigners_starting':None,'max_foreigners_squad':None,'prefer_nationals':False,'source_start':'1993-08-01T00:00:00','source_end':'1994-05-31T00:00:00','source_edition':'1993-94','admitted':True,'signable':True,'source_rule_hints':{'historical_runtime_id':True,'points_win':3,'direct_relegation_places':[14,15,16],'modern_mdb_source_id_blocked':57,'foreign_rule_status':'separate_from_roster_activation'}});snap['leagues'].sort(key=lambda l:int(l.get('source_id') or 0))
 tur=next(l for l in foundation['leagues'] if l['key']=='tur_1993_94');tur['activation_status']='active_historical_roster_gate_passed';tur['activated_runtime_league_id']=LEAGUE_ID
 for c in tur['clubs']:c['team_id']=TEAM_IDS[c['name']];c['roster_status']='complete_historical_1993_94'
 counts={};rc={}
 for name,tid in TEAM_IDS.items():
  rows=[p for p in players if int(p.get('team_id') or 0)==tid and not p.get('retired')];counts[name]=len(rows);rc[name]=dict(Counter(ROLE_TO_LABEL.get(int(p.get('primary_role') or 0),'?') for p in rows))
  if len(rows)<18:raise RuntimeError(f'{name}: {len(rows)}')
 stranded=[p for p in players if int(p.get('team_id') or 0)==OTHER_TURKEY_ID and not p.get('retired') and CLUB_ALIAS.get(norm(p.get('historical_club_1994')))]
 if stranded:raise RuntimeError('Stranded: '+','.join(p['display_name'] for p in stranded))
 audit={'schema_version':1,'season':'1993-94','league_id':LEAGUE_ID,'status':'pass_turkey_1993_94_active','staged_rows':sum(len(c['players']) for c in stage['clubs']),'unique_staged_identities':len({int(r['resolved_source_id']) for c in stage['clubs'] for r in c['players']}),'clubs':16,'minimum_required':18,'source_roster_target':'all rows on pinned BDFutbol season squad pages','minimum_active_roster':min(counts.values()),'roster_counts':counts,'role_counts':rc,'reused_existing_players':reused,'created_players':created,'extra_verified_pool_players_reassigned':len(extras),'extra_reassigned':extras,'mixed_era_memberships_excluded':mixed,'position_provenance':dict(roles),'otros_turquia_stranded_recognised_club':len(stranded),'modern_mdb_league_id_57_active':False,'identities':ident,'duplicate_policy':'explicit reuse only; no fuzzy surname merging','rating_policy':'fixed source-comparable attributes on the game scale; no football 75/25 rule'}
 if audit['staged_rows']!=audit['unique_staged_identities']:raise RuntimeError('Turkey source-roster identity cardinality failed')
 audit['source_roster_exhaustive']=True; audit['minimum_is_floor_not_target']=True
 for path,obj in ((SNAP,snap),(STAGE,stage),(FOUNDATION,foundation),(REGISTRY,registry),(AUDIT,audit)):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({k:audit[k] for k in ('status','staged_rows','unique_staged_identities','minimum_active_roster','reused_existing_players','created_players','extra_verified_pool_players_reassigned','mixed_era_memberships_excluded','position_provenance')},ensure_ascii=False,indent=2));print(json.dumps(counts,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
