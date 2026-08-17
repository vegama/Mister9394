from __future__ import annotations
from collections import Counter
from pathlib import Path
import json,sys
from typing import Any
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from tools.review_created_player_profiles import materialise_attributes
DATA=ROOT/'data/football9394'; SNAP=DATA/'historical_snapshot.json'; REG=DATA/'created_players_registry.json'
STAGES={'Turkey':DATA/'turkey_1993_94_roster_staging.json','Russia':DATA/'russia_1993_roster_staging.json','Greece':DATA/'greece_1993_94_roster_staging.json'}
AUDITS={'Turkey':DATA/'turkey_1993_94_roster_gate_audit.json','Russia':DATA/'russia_1993_roster_gate_audit.json','Greece':DATA/'greece_1993_94_roster_gate_audit.json'}
ROLE_TO_BROAD={0:'POR',1:'DEF',2:'DEF',3:'DEF',4:'DEF',5:'DEF',6:'MED',7:'MED',8:'MED',9:'MED',10:'MED',11:'DEL',12:'DEL',13:'MED',14:'MED',15:'DEL',16:'DEL',17:'DEL'}
ROLE_TO_LABEL={0:'Goalkeeper',1:'Right Back',2:'Left Back',3:'Centre Back',4:'Centre Back',5:'Libero',6:'Defensive Midfielder',7:'Centre Midfielder',8:'Attacking Midfielder',9:'Right Midfielder',10:'Right Inside',11:'Right Attacking Midfielder',12:'Right Winger',13:'Left Midfielder',14:'Left Inside',15:'Left Attacking Midfielder',16:'Left Winger',17:'Centre Forward'}
COUNTRY={4:'Alemania',40:'Rusia',47:'Grecia',63:'Argentina',78:'Sudáfrica',84:'Turquía',104:'Georgia',132:'Kazajistán',202:'Tayikistán'}
# Sources are pinned BDFutbol individual-profile pages; every row exposes an image.
PATCH={
9495349:dict(country='Turkey',display_name='Hami Mandıralı',first_name='Hami',surname1='Mandıralı',birth_date='1968-07-20',birth_country_id=84,international_country_id=84,height_cm=178,weight_kg=75,bdfutbol_id='98308',profile_position='Forward',role=17),
9495338:dict(country='Turkey',display_name='Rıza Çalımbay',first_name='Rıza',surname1='Çalımbay',birth_date='1963-02-02',birth_country_id=84,international_country_id=84,height_cm=165,bdfutbol_id='42289',profile_position='Midfielder'),
9496380:dict(country='Turkey',display_name='Shota Arveladze',first_name='Shota',surname1='Arveladze',birth_date='1973-02-22',birth_country_id=104,international_country_id=104,height_cm=181,weight_kg=73,bdfutbol_id='4135',profile_position='Forward',role=17),
9496385:dict(country='Turkey',display_name='Archil Arveladze',first_name='Archil',surname1='Arveladze',birth_date='1973-02-22',birth_country_id=104,international_country_id=104,height_cm=178,weight_kg=73,bdfutbol_id='90266',profile_position='Forward',role=17),
9496390:dict(country='Turkey',display_name='Fani Tommy Madida',first_name='Fani Tommy',surname1='Madida',birth_date='1966-12-07',birth_country_id=78,international_country_id=78,bdfutbol_id='702745',profile_position='Midfielder'),
9496391:dict(country='Turkey',display_name='Oktay Derelioğlu',first_name='Oktay',surname1='Derelioğlu',birth_date='1975-12-17',birth_country_id=84,international_country_id=84,height_cm=182,weight_kg=71,bdfutbol_id='2101',profile_position='Forward',role=17),
9496392:dict(country='Turkey',display_name='Osvaldo Darío Nartallo',first_name='Osvaldo Darío',surname1='Nartallo',birth_date='1972-09-07',birth_country_id=63,international_country_id=63,bdfutbol_id='702756',profile_position='Forward',role=17),
9496627:dict(country='Russia',display_name='Oleg Aleksandrovich Veretennikov',first_name='Oleg Aleksandrovich',surname1='Veretennikov',birth_date='1970-01-05',birth_country_id=40,international_country_id=40,height_cm=185,weight_kg=80,bdfutbol_id='66381',profile_position='Forward',role=17),
9496629:dict(country='Russia',display_name='Vladimir Viktorovich Niederhaus',first_name='Vladimir Viktorovich',surname1='Niederhaus',birth_date='1967-08-13',birth_country_id=132,international_country_id=132,height_cm=175,bdfutbol_id='1159061',profile_position='Forward',role=17),
503:dict(country='Russia',display_name='Rashid Mamatkulovich Rakhimov',first_name='Rashid Mamatkulovich',surname1='Rakhimov',birth_date='1965-03-18',birth_country_id=202,international_country_id=40,secondary_nationality_country_id=202,height_cm=182,weight_kg=78,bdfutbol_id='2861',profile_position='Midfielder'),
9494086:dict(country='Russia',display_name='Omari Mikhailovich Tetradze',first_name='Omari Mikhailovich',surname1='Tetradze',birth_date='1969-10-13',birth_country_id=104,international_country_id=40,secondary_nationality_country_id=104,height_cm=190,bdfutbol_id='99702',profile_position='Defender'),
9496942:dict(country='Greece',display_name='Giorgos Donis',first_name='Giorgos',surname1='Donis',birth_date='1969-10-29',birth_country_id=4,international_country_id=47,secondary_nationality_country_id=4,height_cm=180,weight_kg=76,bdfutbol_id='99153',profile_position='Midfielder'),
}
MERGED={9496361:9495343,9496363:9495325,9496379:9495349,9496389:9495338,9496395:9495345,9496426:9495353,9496484:9495326,9497392:503}

def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def role_ratings(role:int):
 o={str(i):0 for i in range(18)};o[str(role)]=100
 adj={
  0:{},1:{3:60,9:55},2:{4:60,13:55},3:{4:75,5:60,6:45},4:{3:75,5:60,6:45},5:{3:75,4:75,6:60},
  6:{7:75,3:50,4:50},7:{6:70,8:65,9:45,13:45},8:{7:65,11:55,15:55,17:45},9:{12:75,7:55,8:50,1:45},
  10:{9:80,12:65,7:55},11:{12:80,9:65,8:65,17:50},12:{9:75,11:65,17:50},13:{16:75,7:55,8:50,2:45},
  14:{13:80,16:65,7:55},15:{16:80,13:65,8:65,17:50},16:{13:75,15:65,17:50},17:{11:45,15:45,12:35,16:35,8:30},
 }
 for k,v in adj[role].items():o[str(k)]=v
 return o

def comparable(originals,broad,ov,sid):
 pool=[p for p in originals if p.get('broad_position')==broad and p.get('attributes')]
 pool.sort(key=lambda p:(abs(int(p.get('overall') or 0)-ov),int(p.get('source_id') or 0)));pool=pool[:32]
 if len(pool)<2:raise RuntimeError('not enough comparables')
 a=pool[(sid*7)%len(pool)];b=pool[(sid*13+5)%len(pool)]
 if a['source_id']==b['source_id']:b=pool[(pool.index(a)+1)%len(pool)]
 return a,b

def main():
 snap=json.load(open(SNAP,encoding='utf8'));registry=json.load(open(REG,encoding='utf8'));stages={k:json.load(open(v,encoding='utf8')) for k,v in STAGES.items()};audits={k:json.load(open(v,encoding='utf8')) for k,v in AUDITS.items()}
 players=snap['players'];by={int(p['source_id']):p for p in players};originals=[p for p in players if not p.get('external_origin') and not p.get('creation_batch')]
 # Purge registry rows belonging to identities explicitly merged into a verified existing player.
 registry['players']=[r for r in registry['players'] if int(r.get('source_id') or -1) not in MERGED]
 regby={int(r['source_id']):r for r in registry['players'] if r.get('source_id') is not None}
 changes=[]
 for sid,pa in PATCH.items():
  p=by.get(sid)
  if not p:raise RuntimeError(f'missing profile {sid}')
  before=int(p.get('primary_role') or 0);before_broad=p.get('broad_position')
  for k in ['display_name','first_name','surname1','birth_country_id','international_country_id','height_cm','weight_kg']:
   if k in pa:p[k]=pa[k]
  p['birth_date']=pa['birth_date']+'T00:00:00'
  if pa.get('secondary_nationality_country_id'):p['secondary_nationality_country_id']=pa['secondary_nationality_country_id']
  if 'role' in pa:
   role=int(pa['role']);p['role_ratings']=role_ratings(role)
   if role!=before:
    broad=ROLE_TO_BROAD[role];p['primary_role']=role;p['broad_position']=broad;p['historical_position_1993_94']=ROLE_TO_LABEL[role];p['historical_position_source']='BDFutbol individual profile v0.30'
    a,b=comparable(originals,broad,int(p.get('overall') or 70),sid);p['attributes']=materialise_attributes(int(p.get('overall') or 70),a,b);p['attribute_source']='fixed_source_comparable_role_correction_0.30';p['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]
  p['bdfutbol_id']=pa['bdfutbol_id'];p['bdfutbol_url']=f"https://www.bdfutbol.com/en/j/j{pa['bdfutbol_id']}.html";p['historical_profile_source']='BDFutbol individual player profile v0.30';p['historical_profile_source_url']=p['bdfutbol_url'];p['source_profile_position']=pa['profile_position'];p['profile_review_required']=False
  # Update any registry row (base-MDB identities intentionally have none).
  r=regby.get(sid)
  if r:
   r.update({'display_name':p['display_name'],'first_name':p.get('first_name'),'surname1':p.get('surname1'),'birth_date':pa['birth_date'],'country_id':p.get('international_country_id') or p.get('birth_country_id'),'country_name':COUNTRY.get(int(p.get('international_country_id') or p.get('birth_country_id') or 0)),'broad_position':p.get('broad_position'),'historical_position_1993_94':p.get('historical_position_1993_94'),'bdfutbol_search_name':p['display_name'],'bdfutbol_id':pa['bdfutbol_id'],'bdfutbol_url':p['bdfutbol_url'],'photo_status':'ready_for_download','profile_review_required':False,'individual_profile_source':'BDFutbol individual player profile v0.30'})
  # Keep staging and roster-gate audit identity rows synchronized.
  country=pa['country']
  for club in stages[country].get('clubs',[]):
   for row in club.get('players',[]):
    if int(row.get('resolved_source_id') or -1)==sid:
     row.update({'resolved_display_name':p['display_name'],'resolved_primary_role':int(p.get('primary_role') or 0),'resolved_exact_position':p.get('historical_position_1993_94'),'resolved_birth_date':p.get('birth_date'),'resolved_country_id':p.get('international_country_id') or p.get('birth_country_id'),'individual_profile_source_url':p['bdfutbol_url'],'bdfutbol_id':pa['bdfutbol_id']})
     if 'role' in pa and int(pa['role'])!=before:row['position_source']='bdfutbol_individual_profile_v0.30'
  for row in audits[country].get('identities',[]):
   if int(row.get('source_id') or -1)==sid:
    row.update({'display_name':p['display_name'],'role':int(p.get('primary_role') or 0),'position':p.get('historical_position_1993_94'),'individual_profile_source_url':p['bdfutbol_url'],'country_id':p.get('international_country_id') or p.get('birth_country_id')})
    if 'role' in pa and int(pa['role'])!=before:row['position_source']='bdfutbol_individual_profile_v0.30'
  changes.append({'source_id':sid,'display_name':p['display_name'],'country':country,'bdfutbol_id':pa['bdfutbol_id'],'birth_country_id':p.get('birth_country_id'),'international_country_id':p.get('international_country_id'),'role_before':before,'role_after':int(p.get('primary_role') or 0),'portrait_ready':True})
 # Record merged IDs in stage/audits if any stale references survived.
 for old,new in MERGED.items():
  target=by.get(new)
  if not target:continue
  for country,st in stages.items():
   for club in st.get('clubs',[]):
    for row in club.get('players',[]):
     if int(row.get('resolved_source_id') or -1)==old:
      row['resolved_source_id']=new;row['resolved_display_name']=target['display_name'];row['identity_resolution']='reused_verified_existing_identity_v0.30'
  for country,a in audits.items():
   for row in a.get('identities',[]):
    if int(row.get('source_id') or -1)==old:
     row['source_id']=new;row['display_name']=target['display_name'];row['duplicate_reconciliation']='v0.30 verified identity merge'
 # 1993 country policy audit.
 ctx=json.load(open(DATA/'country_context_1993.json',encoding='utf8'))
 country_audit={'schema_version':1,'reference_year':1993,'status':'pass','policy':ctx['policy'],'profiles_normalized':[{k:c[k] for k in ['source_id','display_name','birth_country_id','international_country_id']} for c in changes if c['birth_country_id'] not in {40,47,84}], 'created_country_ids':[], 'reused_existing_1993_country_ids':[4,63,78,104,132,202], 'note':'Georgia, Kazakhstan, South Africa and Tajikistan already had canonical source IDs, so they were normalized/reused rather than duplicated. Modern-only state identities remain blocked by country_context_1993.json.'}
 # Clean merged retired player records from snapshot entirely when they were created by historical enrichment.
 players[:]=[p for p in players if int(p.get('source_id') or -1) not in MERGED]
 for country,a in audits.items():
  rel=[c for c in changes if c['country']==country];a['individual_profile_enrichment_0_30']={'profiles_curated':len(rel),'portrait_profiles_ready_for_download':len(rel),'role_corrections':sum(c['role_before']!=c['role_after'] for c in rel),'duplicate_identities_merged_total':sum(1 for old,new in MERGED.items() if country=='Turkey' and old!=9497392 or country=='Russia' and old==9497392)}
  a['position_provenance']=dict(Counter(str(r.get('position_source') or 'unknown') for r in a.get('identities',[])))
 audit={'schema_version':1,'checkpoint':'0.30.0-full-rosters-1993-countries-profiles','status':'pass','profiles_curated':len(changes),'portrait_profiles_ready_for_download':len(changes),'role_corrections':sum(c['role_before']!=c['role_after'] for c in changes),'duplicates_merged':MERGED,'changes':changes,'country_context_file':'country_context_1993.json'}
 dump(SNAP,snap);dump(REG,registry)
 for k,pth in STAGES.items():dump(pth,stages[k])
 for k,pth in AUDITS.items():dump(pth,audits[k])
 dump(DATA/'turkey_russia_greece_individual_profile_audit_v030.json',audit);dump(DATA/'country_normalization_1993_audit.json',country_audit)
 print(json.dumps(audit,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
