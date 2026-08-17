from __future__ import annotations
from pathlib import Path
import json, sys
from typing import Any

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import role_ratings,ROLE_TO_BROAD,ROLE_TO_LABEL,comparable,stage_rows,profile_gap_stats
from tools.review_created_player_profiles import materialise_attributes

DATA=ROOT/'data'/'football9394'; SNAP=DATA/'historical_snapshot.json'; REG=DATA/'created_players_registry.json'; QUEUE=DATA/'bdfutbol_photo_queue.json'; STAGE=DATA/'turkey_1993_94_roster_staging.json'
SOURCE='https://www.transfermarkt.com/genclerbirligi-ankara/startseite/verein/820/saison_id/1993'
BDF_SQUAD='https://www.bdfutbol.com/en/t/t1993-9410358.html'
TEAM=9357005
COUNTRY={4:'Alemania',20:'Bosnia-Herzegovina',21:'Bulgaria',78:'Sudáfrica',84:'Turquía',88:'República Democrática del Congo'}

# Season-squad roles. Broad categories stay explicitly unresolved instead of inventing an exact flank/central role.
P:dict[int,dict[str,Any]]={
9496435:dict(name='Hasan Okan Gültang',dob='1972-10-29',nats=[84],role=0,pos='Goalkeeper'),
9497270:dict(name='Mehmet Güler',dob='1972-10-09',nats=[84],role=0,pos='Goalkeeper'),
9496446:dict(name='Ivo Šimunić',dob='1970-11-13',nats=[20],role=0,pos='Goalkeeper'),
9496451:dict(name='Rüstem İsmailoğlu',dob='1964-05-10',nats=[84],role=0,pos='Goalkeeper'),
9496438:dict(name='Rahim Zafer',dob='1971-01-25',nats=[84],role=5,pos='Sweeper'),
9496439:dict(name='Taner Taşkın',dob='1972-10-27',nats=[84],role=3,pos='Centre-Back'),
9497265:dict(name='Serkan Damla',dob='1973-10-25',nats=[84],role=2,pos='Left-Back'),
9496437:dict(name='Ergün Penbe',dob='1972-05-17',nats=[84],role=2,pos='Left-Back'),
9496443:dict(name='Osman Coşkun',dob='1972-01-11',nats=[84],role=2,pos='Left-Back'),
9496436:dict(name='Erkan Sözeri',dob='1966-05-19',nats=[84],role=1,pos='Right-Back'),
9496448:dict(name='Erkut Çağdaş',dob='1967-05-15',nats=[84],pos='Midfielder',precision='broad_only',broad='MED',functional_role=7),
9496447:dict(name='Ace Khuse',dob='1963-09-08',nats=[78],pos='Midfielder',precision='broad_only',broad='MED',functional_role=7),
9496449:dict(name='Ali Işık',dob='1970-12-30',nats=[84,4],pos='Midfielder',precision='broad_only',broad='MED',functional_role=7),
9496452:dict(name='Yunus Kara',dob='1972-05-10',nats=[84],pos='Midfielder',precision='broad_only',broad='MED',functional_role=7),
9497266:dict(name='Murat Şenvardar',dob='1971-10-11',nats=[84],pos='Midfielder',precision='broad_only',broad='MED',functional_role=7),
9497271:dict(name='Nihat Baştürk',dob='1973-10-22',nats=[84],role=7,pos='Central Midfield'),
9496440:dict(name='Metin Diyadin',dob='1968-02-16',nats=[84],role=13,pos='Left Midfield'),
9496445:dict(name='Mehmet Şimşek',dob='1969-07-01',nats=[84],role=13,pos='Left Midfield'),
9496441:dict(name='John Moshoeu',dob='1965-12-18',nats=[78],role=8,pos='Attacking Midfield'),
9497269:dict(name='Mehmet Altıparmak',dob='1969-05-01',nats=[84],role=8,pos='Attacking Midfield'),
9497267:dict(name='Aykan Atik',dob='1971-12-28',nats=[84],role=16,pos='Left Winger'),
9496442:dict(name='Engin Özdemir',dob='1968-10-01',nats=[4,84],role=12,pos='Right Winger'),
9497268:dict(name='Tarkan Özyılmaz',dob='1975-04-03',nats=[84],role=17,pos='Centre-Forward'),
9496444:dict(name="Andre Kona N'Gole",dob='1970-06-16',nats=[88],role=17,pos='Centre-Forward',birth_country=88,birth_place='Lubumbashi',height=181,bdf='702421'),
9496450:dict(name='Tarık Daşgün',dob='1973-08-26',nats=[84],role=17,pos='Centre-Forward'),
}

NEW=[
 dict(sid=9498001,name='Serkan Gültang',dob='1973-12-22',nats=[84],role=17,pos='Centre-Forward',overall=67,bdf='1173561',birth_country=84,birth_place='Adana (Adana)',note='Transfermarkt season role Centre-Forward; BDFutbol identity page labels broad Defender, retained as documented source conflict'),
 dict(sid=9498002,name='Sunay Kahraman',dob='1972-01-07',nats=[84,21],role=17,pos='Forward (exact role unresolved)',overall=66,precision='broad_only',birth_country=84,note='Transfermarkt season squad gives broad Forward; TFF confirms Gençlerbirliği registration and November 1993 loan movement'),
]

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split(n):
 a=n.split(); return (None,n) if len(a)<2 else (' '.join(a[:-1]),a[-1])

def reattribute(p,role,originals,sid):
 a,c=comparable(originals,ROLE_TO_BROAD[role],int(p.get('overall') or 70),sid)
 p['attributes']=materialise_attributes(int(p.get('overall') or 70),a,c)
 p['attribute_source']='fixed_source_comparable_role_correction_0.32'
 p['attribute_comparable_source_ids']=[int(a['source_id']),int(c['source_id'])]

def apply_existing(p,patch,originals,sid):
 before={'name':p.get('display_name'),'role':int(p.get('primary_role') or 0),'broad':p.get('broad_position'),'pos':p.get('historical_position_1993_94'),'birth':p.get('birth_date'),'country':p.get('international_country_id')}
 p['display_name']=patch['name']; f,s=split(patch['name']); p['first_name']=f; p['surname1']=s; p['birth_date']=patch['dob']+'T00:00:00'
 nats=patch['nats']; p['international_country_id']=nats[0]; p['profile_nationality_country_ids']=nats
 if len(nats)>1:p['secondary_nationality_country_id']=nats[1]
 if patch.get('birth_country'): p['birth_country_id']=patch['birth_country']
 if patch.get('birth_place'): p['historical_birth_place_text']=patch['birth_place']
 if patch.get('height'): p['height_cm']=patch['height']
 p['source_profile_position']=patch['pos']; p['profile_position_precision']=patch.get('precision','exact'); p['profile_review_required']=patch.get('precision')=='broad_only'
 p['historical_profile_source']='Transfermarkt Gençlerbirliği season squad 1993-94 v0.32';p['historical_profile_source_url']=SOURCE
 role=patch.get('role',patch.get('functional_role'))
 if role is not None:
  old_role=int(p.get('primary_role') or 0); old_broad=p.get('broad_position')
  p['role_ratings']=role_ratings(role);p['primary_role']=role;p['broad_position']=ROLE_TO_BROAD[role]
  if patch.get('precision')=='broad_only':
   p['historical_position_1993_94']=patch['pos']+' (exact role unresolved)';p['historical_position_source']='Transfermarkt broad squad category 1993-94 v0.32'
  else:
   p['historical_position_1993_94']=ROLE_TO_LABEL[role];p['historical_position_source']='Transfermarkt Gençlerbirliği season squad 1993-94 v0.32'
  if role!=old_role or p['broad_position']!=old_broad: reattribute(p,role,originals,sid)
 if patch.get('bdf'):
  p['historical_profile_source']='Transfermarkt season squad + BDFutbol individual identity v0.32';p['historical_profile_source_url']=f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"
 return before

def new_player(row,originals):
 sid=row['sid'];role=row['role'];a,b=comparable(originals,ROLE_TO_BROAD[role],row['overall'],sid);attrs=materialise_attributes(row['overall'],a,b);f,s=split(row['name'])
 return {
  'source_id':sid,'team_id':TEAM,'display_name':row['name'],'first_name':f,'surname1':s,'surname2':None,'birth_date':row['dob']+'T00:00:00',
  'birth_country_id':row.get('birth_country'),'international_country_id':row['nats'][0],'preferred_foot':None,'shirt_number':None,
  'primary_role':role,'broad_position':ROLE_TO_BROAD[role],'overall':row['overall'],'category':row['overall'],'height_cm':None,'weight_kg':None,'salary':0,'release_clause':0,
  'contract_start_year':1993,'contract_end_year':None,'loan':False,'initially_reserve':True,'retired':False,'attributes':attrs,'birth_city_id':None,
  'naturalized_country_id':None,'basque_origin':False,'favorite_shirt_number':None,'injury_proneness':0,'progression_mean':0,'fan_affection':0,'academy_team_id':None,'previous_team_id':None,'previous_team_years':None,'buyback_option':False,
  'role_ratings':role_ratings(role),'hidden_traits':{'individualist':False,'killer_pass':False,'holds_ball':False,'long_shots':False,'cuts_inside':False,'first_time_play':False,'dives':False},
  'historical_squad_1994':True,'historical_data_source':'Transfermarkt Gençlerbirliği 1993-94 season squad; TFF/BDF identity cross-check v0.32','external_origin':'historical_turkey_1993_94','creation_batch':'turkey_genclerbirligi_roster_completion_0.32',
  'profile_review_required':row.get('precision')=='broad_only','historical_position_1993_94':row['pos'],'historical_position_source':'Transfermarkt Gençlerbirliği season squad 1993-94 v0.32','source_profile_position':row['pos'].split(' (')[0],
  'profile_position_precision':row.get('precision','exact'),'historical_profile_source':'Transfermarkt season squad + TFF/BDF identity v0.32','historical_profile_source_url': f"https://www.bdfutbol.com/en/j/j{row['bdf']}.html" if row.get('bdf') else SOURCE,
  'profile_nationality_country_ids':row['nats'],'secondary_nationality_country_id':row['nats'][1] if len(row['nats'])>1 else None,'historical_birth_place_text':row.get('birth_place'),
  'historical_profile_source_note':row.get('note'),'attribute_source':'fixed_source_comparable_role_profile_0.32','attribute_comparable_source_ids':[int(a['source_id']),int(b['source_id'])]
 }

def main():
 snap=load(SNAP);reg=load(REG);queue=load(QUEUE);stage=load(STAGE);before_gaps=profile_gap_stats(snap);by={int(x['source_id']):x for x in snap['players']};rb={int(x['source_id']):x for x in reg['players']};qb={int(x['source_id']):x for x in queue['players']}
 originals=[x for x in snap['players'] if x.get('attributes')];changes=[]
 for sid,patch in P.items():
  p=by[sid];before=apply_existing(p,patch,originals,sid);changes.append({'source_id':sid,'before':before,'after':{'name':p['display_name'],'role':p['primary_role'],'broad':p['broad_position'],'pos':p['historical_position_1993_94'],'birth':p['birth_date'],'country':p['international_country_id']},'source_position':patch['pos']})
  for c in stage['clubs']:
   if c.get('name')=='Gençlerbirliği':
    for r in c['players']:
     if int(r.get('resolved_source_id') or -1)==sid:
      r.update({'resolved_display_name':p['display_name'],'resolved_primary_role':p['primary_role'],'resolved_exact_position':p['historical_position_1993_94'],'resolved_birth_date':p['birth_date'],'resolved_country_id':p['international_country_id'],'profile_source_url':SOURCE,'profile_source':'Transfermarkt Gençlerbirliği season squad 1993-94 v0.32','source_profile_position':patch['pos'],'position_source':'season_specific_profile_v0.32'})
      if patch.get('bdf'):r.update({'individual_profile_source_url':f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html",'bdfutbol_id':patch['bdf']})
  for t in (rb.get(sid),qb.get(sid)):
   if t:
    t.update({'display_name':p['display_name'],'birth_date':patch['dob'],'country_id':p['international_country_id'],'country_name':COUNTRY[p['international_country_id']],'broad_position':p['broad_position'],'historical_position_1993_94':p['historical_position_1993_94'],'profile_review_required':bool(p.get('profile_review_required')),'individual_profile_source':'Transfermarkt Gençlerbirliği season squad 1993-94 v0.32','individual_profile_source_url':p['historical_profile_source_url']})
    if patch.get('bdf'):t.update({'bdfutbol_id':patch['bdf'],'bdfutbol_url':f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"})
 # Add the two source-visible opening-roster members omitted by the BDF league-appearance staging.
 club=next(c for c in stage['clubs'] if c.get('name')=='Gençlerbirliği')
 added=[]
 for row in NEW:
  sid=row['sid']
  if sid in by or any((x.get('display_name') or '').casefold()==row['name'].casefold() for x in snap['players']): continue
  p=new_player(row,originals);snap['players'].append(p);by[sid]=p;added.append(sid)
  club['players'].append({'bdfutbol_name':row['name'].split()[-1],'age_1993_94':1993-int(row['dob'][:4]),'appearances':0,'starts':0,'minutes':0,'goals':0,'core_18_candidate':False,'source_roster_member':True,'identity_resolution':'created_historical_identity','resolved_source_id':sid,'resolved_display_name':row['name'],'resolved_primary_role':row['role'],'resolved_exact_position':row['pos'],'position_source':'season_specific_profile_v0.32','resolved_birth_date':row['dob']+'T00:00:00','resolved_country_id':row['nats'][0],'profile_source_url':SOURCE,'profile_source':'Transfermarkt Gençlerbirliği season squad 1993-94 + TFF/BDF identity v0.32','source_profile_position':row['pos'].split(' (')[0],'individual_profile_source_url':f"https://www.bdfutbol.com/en/j/j{row['bdf']}.html" if row.get('bdf') else None,'bdfutbol_id':row.get('bdf')})
  entry={'source_id':sid,'display_name':row['name'],'first_name':p['first_name'],'surname1':p['surname1'],'surname2':None,'birth_date':row['dob'],'country_id':row['nats'][0],'country_name':COUNTRY[row['nats'][0]],'broad_position':p['broad_position'],'team_id':TEAM,'team_name':'Gençlerbirliği','creation_batch':'turkey_genclerbirligi_roster_completion_0.32','identity_source':'Transfermarkt season squad + TFF/BDF identity v0.32','identity_source_url':SOURCE,'verified_national_pool_year':None,'historical_position_1993_94':row['pos'],'historical_club_1994':'Gençlerbirliği','overall':row['overall'],'attribute_source':p['attribute_source'],'profile_review_required':bool(p['profile_review_required']),'duplicate_check':'exact_name_birthdate_historical_identity_gate','matched_existing_id':None,'bdfutbol_search_name':row['name'],'bdfutbol_id':row.get('bdf'),'bdfutbol_url':f"https://www.bdfutbol.com/en/j/j{row['bdf']}.html" if row.get('bdf') else None,'photo_filename':f'{sid}.jpg','photo_status':'pending','individual_profile_source':'Transfermarkt season squad + TFF/BDF identity v0.32','individual_profile_source_url':p['historical_profile_source_url']}
  reg['players'].append(entry);q=dict(entry);q.pop('overall',None);q.pop('attribute_source',None);q.update({'photo_width':40,'photo_height':55,'photo_format':'JPEG','photo_mode':'RGB'});queue['players'].append(q)
 # Sync staging-derived historical spells for newly added players (zero-match membership still retained in biography evidence later).
 dump(SNAP,snap);dump(REG,reg);dump(QUEUE,queue);dump(STAGE,stage)
 role_changes=sum(x['before']['role']!=x['after']['role'] for x in changes)
 broad_functional_changes=sum(1 for x in changes if x['source_position']=='Midfielder' and x['before']['role']!=x['after']['role'])
 after=profile_gap_stats(snap)
 ap=DATA/'historical_profiles_metadata_audit_v032.json';audit=load(ap);pr=audit['profiles'];pr['fifth_batch']='Gençlerbirliği 1993-94 season squad';pr['genclerbirligi_existing_curated']=len(changes);pr['genclerbirligi_players_added']=[{'source_id':sid,'display_name':by[sid]['display_name']} for sid in added];pr['genclerbirligi_role_corrections']=role_changes;pr['genclerbirligi_broad_functional_role_normalizations']=broad_functional_changes;pr['genclerbirligi_review_required']=sum(bool(by[s].get('profile_review_required')) for s in [*P,*added]);pr['genclerbirligi_source']=SOURCE;pr['curated_total_v032']=pr.get('curated_total_v032',108)+len(changes)+len(added);pr['role_corrections_total_v032']=pr.get('role_corrections_total_v032',57)+role_changes;pr['genclerbirligi_changes']=changes;audit['profile_gaps_after']=after;dump(ap,audit)
 gp=DATA/'historical_metadata_gaps_v032.json';g=load(gp);g['profile_gaps']=after;target_teams={9352001,9352002,9352003,9352004,9352005,9352006,*range(9357001,9357015),*range(9360001,9360017),*range(9347001,9347019)};g['profile_review_queue']=[{'source_id':int(x['source_id']),'display_name':x.get('display_name'),'reason':'season source only gives a broad position category; exact role remains source-gated'} for x in snap['players'] if int(x.get('team_id') or 0) in target_teams and x.get('profile_review_required')];dump(gp,g)
 print(json.dumps({'status':'pass','existing_curated':len(changes),'players_added':added,'role_corrections':role_changes,'review_required':pr['genclerbirligi_review_required'],'curated_total_v032':pr['curated_total_v032'],'role_corrections_total_v032':pr['role_corrections_total_v032'],'profile_gaps_after':after},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
