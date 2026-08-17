from __future__ import annotations
from pathlib import Path
import json, sys
from typing import Any

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import role_ratings,ROLE_TO_BROAD,ROLE_TO_LABEL,comparable,profile_gap_stats
from tools.review_created_player_profiles import materialise_attributes

DATA=ROOT/'data'/'football9394'; SNAP=DATA/'historical_snapshot.json'; REG=DATA/'created_players_registry.json'; QUEUE=DATA/'bdfutbol_photo_queue.json'; STAGE=DATA/'turkey_1993_94_roster_staging.json'
SOURCE='https://www.transfermarkt.com.tr/kocaelispor/startseite/verein/120/saison_id/1993'
ISMAIL_TFF='https://www.tff.org/Default.aspx?kisiId=21749&pageId=526'
FEVZI_TFF='https://www.tff.org/Default.aspx?kisiId=23276&pageId=526'
FEVZI_TM='https://www.transfermarkt.com.tr/fevzi-acikgoz/profil/spieler/601055'
FEVZI_BDF='https://www.bdfutbol.com/en/j/j1175393.html'
TEAM=9357004
COUNTRY={4:'Alemania',20:'Bosnia-Herzegovina',21:'Bulgaria',54:'Macedonia',75:'República Federal de Yugoslavia',84:'Turquía'}

P:dict[int,dict[str,Any]]={
9496417:dict(name='Fahrudin Omerović',dob='1961-08-20',nats=[20,84],role=0,pos='Goalkeeper'),
9496428:dict(name='Alper Boğuşlu',dob='1962-07-05',nats=[84],role=0,pos='Goalkeeper'),
9496419:dict(name='Stevica Kuzmanovski',dob='1962-11-16',nats=[54,21],role=5,pos='Sweeper'),
9496434:dict(name='Sefer Yılmaz',dob='1969-01-22',nats=[84],role=3,pos='Defender',precision='broad_only'),
9496418:dict(name='Misko Mirkovic',dob='1966-08-07',nats=[75,84],role=3,pos='Centre-Back'),
9496420:dict(name='Osman Çakır',dob='1967-06-16',nats=[84],role=3,pos='Centre-Back'),
9497259:dict(name='Murat Doğansoy',dob='1967-12-26',nats=[84],role=3,pos='Centre-Back'),
9497264:dict(name='Olcay Danacı',dob='1966-09-12',nats=[84],role=3,pos='Centre-Back'),
9496432:dict(name='Yalçın Kıldıran',dob='1969-04-30',nats=[84],role=2,pos='Left-Back'),
9497262:dict(name='Şeyhmus Suna',dob='1965-04-05',nats=[84],role=1,pos='Right-Back'),
9496433:dict(name='İlhami Arslan',dob='1975-01-01',nats=[84],role=1,pos='Right-Back'),
9496421:dict(name='Erol Usta',dob='1965-09-01',nats=[84],role=1,pos='Right-Back'),
9497261:dict(name='Hasan Şişman',dob='1974-01-02',nats=[84],role=7,pos='Midfielder',precision='broad_only'),
9496431:dict(name='Zeki Önatlı',dob='1968-10-30',nats=[84],role=7,pos='Central Midfield'),
9496423:dict(name='Turan Uzun',dob='1969-07-31',nats=[84],role=7,pos='Central Midfield'),
9496429:dict(name='Melih Gürbüztürk',dob='1966-10-15',nats=[84],role=7,pos='Central Midfield'),
9496425:dict(name='Ümit Birol',dob='1963-01-26',nats=[84],role=9,pos='Right Midfield'),
9496427:dict(name='Halil İbrahim Kara',dob='1972-09-26',nats=[84],role=13,pos='Left Midfield'),
9496422:dict(name='Tuncay Akgün',dob='1968-11-01',nats=[84,4],role=8,pos='Attacking Midfield'),
9496424:dict(name='Arif Bacacı',dob='1968-03-28',nats=[84],role=16,pos='Left Winger'),
9497263:dict(name='Yaşar Altıntaş',dob='1957-10-03',nats=[84],role=16,pos='Left Winger'),
9495353:dict(name='Saffet Sancaklı',dob='1966-02-27',nats=[84],role=17,pos='Centre-Forward'),
9496430:dict(name='Faruk Yiğit',dob='1968-04-15',nats=[84],role=17,pos='Centre-Forward'),
9497258:dict(name='Ergun Kula',dob='1968-01-31',nats=[84],role=17,pos='Centre-Forward'),
9497260:dict(name='Bayram Oral',dob='1974-06-09',nats=[84],role=17,pos='Centre-Forward'),
}
NEW=[
 dict(sid=9498003,name='İsmail Ünal',dob='1966-01-01',nats=[84],role=0,pos='Goalkeeper',overall=66,birth_country=84,birth_place='Adana',individual_source=ISMAIL_TFF,note='TFF records Kocaelispor contract from 2 July 1993 and domestic-transfer licence on 23 August 1993.'),
 dict(sid=9498004,name='Fevzi Açıkgöz',dob='1966-11-15',nats=[84],role=3,pos='Centre-Back',overall=68,birth_country=84,birth_place='Kocaeli',bdf='1175393',individual_source=FEVZI_TM,note='Opening-season Kocaelispor squad member; TFF career history records Eskişehirspor from 11 November 1993. Transfermarkt gives Centre-Back with Defensive Midfield secondary; BDFutbol gives broad Midfielder. Conflict retained explicitly.',secondary=[(6,'Defensive Midfielder')]),
]

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split(n):
 a=n.split(); return (None,n) if len(a)<2 else (' '.join(a[:-1]),a[-1])

def reattribute(p,role,originals,sid,kind='correction'):
 a,b=comparable(originals,ROLE_TO_BROAD[role],int(p.get('overall') or 70),sid)
 p['attributes']=materialise_attributes(int(p.get('overall') or 70),a,b)
 p['attribute_source']=f'fixed_source_comparable_role_{kind}_0.32'
 p['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]

def apply_existing(p,patch,originals,sid):
 before={'name':p.get('display_name'),'role':int(p.get('primary_role') or 0),'broad':p.get('broad_position'),'pos':p.get('historical_position_1993_94'),'birth':p.get('birth_date'),'country':p.get('international_country_id')}
 p['display_name']=patch['name']; f,s=split(patch['name']); p['first_name']=f;p['surname1']=s;p['birth_date']=patch['dob']+'T00:00:00'
 nats=patch['nats'];p['international_country_id']=nats[0];p['profile_nationality_country_ids']=nats
 if len(nats)>1:p['secondary_nationality_country_id']=nats[1]
 p['source_profile_position']=patch['pos'];p['profile_position_precision']=patch.get('precision','exact');p['profile_review_required']=patch.get('precision')=='broad_only'
 p['historical_profile_source']='Transfermarkt Kocaelispor season squad 1993-94 v0.32';p['historical_profile_source_url']=SOURCE
 role=patch['role']; old_role=int(p.get('primary_role') or 0);old_broad=p.get('broad_position')
 p['role_ratings']=role_ratings(role);p['primary_role']=role;p['broad_position']=ROLE_TO_BROAD[role]
 if patch.get('precision')=='broad_only':
  p['historical_position_1993_94']=patch['pos']+' (exact role unresolved)';p['historical_position_source']='Transfermarkt broad squad category 1993-94 v0.32'
 else:
  p['historical_position_1993_94']=ROLE_TO_LABEL[role];p['historical_position_source']='Transfermarkt Kocaelispor season squad 1993-94 v0.32'
 if role!=old_role or p['broad_position']!=old_broad: reattribute(p,role,originals,sid)
 return before

def new_player(row,originals):
 sid=row['sid'];role=row['role'];a,b=comparable(originals,ROLE_TO_BROAD[role],row['overall'],sid);attrs=materialise_attributes(row['overall'],a,b);f,s=split(row['name'])
 role_rates=role_ratings(role)
 for rr,_ in row.get('secondary',[]): role_rates[str(rr)]=max(role_rates.get(str(rr),0),65)
 return {
  'source_id':sid,'team_id':TEAM,'display_name':row['name'],'first_name':f,'surname1':s,'surname2':None,'birth_date':row['dob']+'T00:00:00','birth_country_id':row.get('birth_country'),'international_country_id':row['nats'][0],
  'preferred_foot':None,'shirt_number':None,'primary_role':role,'broad_position':ROLE_TO_BROAD[role],'overall':row['overall'],'category':row['overall'],'height_cm':None,'weight_kg':None,'salary':0,'release_clause':0,'contract_start_year':1993,'contract_end_year':None,'loan':False,'initially_reserve':True,'retired':False,'attributes':attrs,'birth_city_id':None,'naturalized_country_id':None,'basque_origin':False,'favorite_shirt_number':None,'injury_proneness':0,'progression_mean':0,'fan_affection':0,'academy_team_id':None,'previous_team_id':None,'previous_team_years':None,'buyback_option':False,'role_ratings':role_rates,
  'hidden_traits':{'individualist':False,'killer_pass':False,'holds_ball':False,'long_shots':False,'cuts_inside':False,'first_time_play':False,'dives':False},
  'historical_squad_1994':True,'historical_data_source':'Transfermarkt Kocaelispor 1993-94 season squad; TFF/BDF individual cross-check v0.32','external_origin':'historical_turkey_1993_94','creation_batch':'turkey_kocaelispor_roster_completion_0.32','profile_review_required':False,'historical_position_1993_94':ROLE_TO_LABEL[role],'historical_position_source':'Transfermarkt Kocaelispor season squad 1993-94 v0.32','source_profile_position':row['pos'],'profile_position_precision':'exact','historical_profile_source':'Transfermarkt season squad + TFF/BDF identity v0.32','historical_profile_source_url':row['individual_source'],'profile_nationality_country_ids':row['nats'],'historical_birth_place_text':row.get('birth_place'),'historical_profile_source_note':row.get('note'),'historical_secondary_positions_1993_94':[x[1] for x in row.get('secondary',[])],
  'attribute_source':'fixed_source_comparable_role_profile_0.32','attribute_comparable_source_ids':[int(a['source_id']),int(b['source_id'])]
 }

def main():
 snap=load(SNAP);reg=load(REG);queue=load(QUEUE);stage=load(STAGE);by={int(x['source_id']):x for x in snap['players']};rb={int(x['source_id']):x for x in reg['players']};qb={int(x['source_id']):x for x in queue['players']};originals=[x for x in snap['players'] if x.get('attributes')];changes=[]
 club=next(c for c in stage['clubs'] if c.get('name')=='Kocaelispor')
 for sid,patch in P.items():
  p=by[sid];before=apply_existing(p,patch,originals,sid);changes.append({'source_id':sid,'before':before,'after':{'name':p['display_name'],'role':p['primary_role'],'broad':p['broad_position'],'pos':p['historical_position_1993_94'],'birth':p['birth_date'],'country':p['international_country_id']},'source_position':patch['pos']})
  for r in club['players']:
   if int(r.get('resolved_source_id') or -1)==sid:r.update({'resolved_display_name':p['display_name'],'resolved_primary_role':p['primary_role'],'resolved_exact_position':p['historical_position_1993_94'],'resolved_birth_date':p['birth_date'],'resolved_country_id':p['international_country_id'],'profile_source_url':SOURCE,'profile_source':'Transfermarkt Kocaelispor season squad 1993-94 v0.32','source_profile_position':patch['pos'],'position_source':'season_specific_profile_v0.32'})
  for t in (rb.get(sid),qb.get(sid)):
   if t:t.update({'display_name':p['display_name'],'birth_date':patch['dob'],'country_id':p['international_country_id'],'country_name':COUNTRY[p['international_country_id']],'broad_position':p['broad_position'],'historical_position_1993_94':p['historical_position_1993_94'],'profile_review_required':bool(p.get('profile_review_required')),'individual_profile_source':'Transfermarkt Kocaelispor season squad 1993-94 v0.32','individual_profile_source_url':SOURCE})
 added=[]
 for row in NEW:
  sid=row['sid']
  if sid in by or any((x.get('display_name') or '').casefold()==row['name'].casefold() for x in snap['players']): continue
  p=new_player(row,originals);snap['players'].append(p);by[sid]=p;added.append(sid)
  club['players'].append({'bdfutbol_name':row['name'].split()[-1],'age_1993_94':1993-int(row['dob'][:4]),'appearances':0,'starts':0,'minutes':0,'goals':0,'core_18_candidate':False,'source_roster_member':True,'identity_resolution':'created_historical_identity','resolved_source_id':sid,'resolved_display_name':row['name'],'resolved_primary_role':row['role'],'resolved_exact_position':ROLE_TO_LABEL[row['role']],'position_source':'season_specific_profile_v0.32','resolved_birth_date':row['dob']+'T00:00:00','resolved_country_id':row['nats'][0],'profile_source_url':SOURCE,'profile_source':'Transfermarkt Kocaelispor season squad 1993-94 + TFF/BDF identity v0.32','source_profile_position':row['pos'],'individual_profile_source_url':row['individual_source'],'bdfutbol_id':row.get('bdf'),'historical_transfer_note_1993_94':row.get('note')})
  entry={'source_id':sid,'display_name':row['name'],'first_name':p['first_name'],'surname1':p['surname1'],'surname2':None,'birth_date':row['dob'],'country_id':row['nats'][0],'country_name':COUNTRY[row['nats'][0]],'broad_position':p['broad_position'],'team_id':TEAM,'team_name':'Kocaelispor','creation_batch':'turkey_kocaelispor_roster_completion_0.32','identity_source':'Transfermarkt season squad + TFF/BDF identity v0.32','identity_source_url':row['individual_source'],'verified_national_pool_year':None,'historical_position_1993_94':p['historical_position_1993_94'],'historical_club_1994':'Kocaelispor','overall':row['overall'],'attribute_source':p['attribute_source'],'profile_review_required':False,'duplicate_check':'exact_name_birthdate_historical_identity_gate','matched_existing_id':None,'bdfutbol_search_name':row['name'],'bdfutbol_id':row.get('bdf'),'bdfutbol_url':FEVZI_BDF if row.get('bdf') else None,'photo_filename':f'{sid}.jpg','photo_status':'pending','individual_profile_source':'TFF/Transfermarkt/BDF historical identity v0.32','individual_profile_source_url':row['individual_source']}
  reg['players'].append(entry);q=dict(entry);q.pop('overall',None);q.pop('attribute_source',None);q.update({'photo_width':40,'photo_height':55,'photo_format':'JPEG','photo_mode':'RGB'});queue['players'].append(q)
 dump(SNAP,snap);dump(REG,reg);dump(QUEUE,queue);dump(STAGE,stage)
 role_changes=sum(x['before']['role']!=x['after']['role'] for x in changes);after=profile_gap_stats(snap)
 ap=DATA/'historical_profiles_metadata_audit_v032.json';audit=load(ap);pr=audit['profiles'];pr['sixth_batch']='Kocaelispor 1993-94 season squad';pr['kocaelispor_existing_curated']=len(changes);pr['kocaelispor_players_added']=[{'source_id':sid,'display_name':by[sid]['display_name']} for sid in added];pr['kocaelispor_role_corrections']=role_changes;pr['kocaelispor_review_required']=sum(bool(by[s].get('profile_review_required')) for s in [*P,*added]);pr['kocaelispor_source']=SOURCE;pr['kocaelispor_identity_crosschecks']={'Ismail_Unal':ISMAIL_TFF,'Fevzi_Acikgoz_TFF':FEVZI_TFF,'Fevzi_Acikgoz_Transfermarkt':FEVZI_TM,'Fevzi_Acikgoz_BDFutbol':FEVZI_BDF};pr['curated_total_v032']=pr.get('curated_total_v032',135)+len(changes)+len(added);pr['role_corrections_total_v032']=pr.get('role_corrections_total_v032',77)+role_changes;pr['kocaelispor_changes']=changes;audit['profile_gaps_after']=after;dump(ap,audit)
 gp=DATA/'historical_metadata_gaps_v032.json';g=load(gp);g['profile_gaps']=after;target_teams={9352001,9352002,9352003,9352004,9352005,9352006,*range(9357001,9357015),*range(9360001,9360017),*range(9347001,9347019)};g['profile_review_queue']=[{'source_id':int(x['source_id']),'display_name':x.get('display_name'),'reason':'season source only gives a broad position category; exact role remains source-gated'} for x in snap['players'] if int(x.get('team_id') or 0) in target_teams and x.get('profile_review_required')];dump(gp,g)
 print(json.dumps({'status':'pass','existing_curated':len(changes),'players_added':added,'role_corrections':role_changes,'review_required':pr['kocaelispor_review_required'],'curated_total_v032':pr['curated_total_v032'],'role_corrections_total_v032':pr['role_corrections_total_v032'],'profile_gaps_after':after},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
