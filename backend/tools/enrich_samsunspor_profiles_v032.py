from __future__ import annotations
from pathlib import Path
import json, sys
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import role_ratings,ROLE_TO_BROAD,ROLE_TO_LABEL,comparable,stage_rows,profile_gap_stats
from tools.review_created_player_profiles import materialise_attributes

DATA=ROOT/'data'/'football9394'; SNAP=DATA/'historical_snapshot.json'; REG=DATA/'created_players_registry.json'; QUEUE=DATA/'bdfutbol_photo_queue.json'
STAGES={
 'Belgium':DATA/'belgium_1993_94_roster_staging.json','Turkey':DATA/'turkey_1993_94_roster_staging.json',
 'Russia':DATA/'russia_1993_roster_staging.json','Greece':DATA/'greece_1993_94_roster_staging.json'}
SOURCE='https://www.transfermarkt.com.tr/samsunspor/kader/verein/152/saison_id/1993/plus/1'
# Roles use the project's canonical 0..17 mapping. Broad-only source categories stay review-gated.
P:dict[int,dict[str,Any]]={
9496400:dict(name='Murat Ayhan Aydın',dob='1966-04-04',nats=[84],role=0,pos='Goalkeeper'),
9496401:dict(name='İmdat Arslan',dob='1969-10-10',nats=[84],height=168,foot=1,role=1,pos='Right-Back'),
9496402:dict(name='Ercan Koloğlu',dob='1968-02-11',nats=[84],height=183,role=5,pos='Sweeper'),
9496403:dict(name='Kasım Çıkla',dob='1967-02-26',nats=[84],role=3,pos='Centre-Back'),
9496404:dict(name='Fevzi Korkmaz',dob='1969-05-16',nats=[84],pos='Defender',precision='broad_only',broad='DEF'),
9496405:dict(name='Daniel Timofte',dob='1967-10-01',nats=[72],role=8,pos='Attacking Midfield'),
9496406:dict(name='Osman Akyol',dob='1969-09-01',nats=[84],pos='Midfielder',precision='broad_only',broad='MED'),
9496407:dict(name='Müjdat Gürsu',dob='1971-09-13',nats=[84],role=8,pos='Attacking Midfield'),
9495350:dict(name='Ertuğrul Sağlam',dob='1969-11-19',nats=[84],height=184,foot=1,role=17,pos='Centre-Forward'),
9496408:dict(name='Bünyamin Kubat',dob='1969-11-24',nats=[84],role=17,pos='Centre-Forward'),
9496409:dict(name='Faruk Korkmaz',dob='1969-09-14',nats=[84],role=17,pos='Centre-Forward'),
9496410:dict(name='Abdullah Aslan',dob='1970-03-01',nats=[84],role=0,pos='Goalkeeper'),
9496411:dict(name='İsa Turan',dob='1969-08-06',nats=[84],foot=2,role=2,pos='Left-Back'),
9496412:dict(name='Vural Korkmaz',dob='1972-04-04',nats=[84],foot=1,role=9,pos='Right Midfield'),
9496413:dict(name='Constantin Luca',dob='1969-05-26',nats=[72],role=17,pos='Centre-Forward'),
9496414:dict(name='Marius Cheregi',dob='1967-10-04',nats=[72],height=184,role=6,pos='Defensive Midfield'),
9496415:dict(name='Erol İlhan',dob='1968-07-15',nats=[84],role=0,pos='Goalkeeper'),
9496416:dict(name='Serkan Aykut',dob='1975-02-24',nats=[84],height=174,foot=3,role=17,pos='Centre-Forward'),
9497249:dict(name='Silvian Dobre',dob='1967-12-04',nats=[72],role=17,pos='Centre-Forward'),
9497250:dict(name='Ahmet Yıldırım',dob='1974-02-25',nats=[84],height=186,foot=2,role=6,pos='Defensive Midfield'),
9497251:dict(name='Recep Tüzün',dob='1969-06-01',nats=[84],pos='Defender',precision='broad_only',broad='DEF'),
9497252:dict(name='Ovidiu Hanganu',dob='1970-05-12',nats=[72],role=17,pos='Centre-Forward'),
9497253:dict(name='Yaşar Işık',dob='1969-05-13',nats=[84],role=3,pos='Centre-Back'),
9497254:dict(name='Gökay Akpınar',dob='1968-04-10',nats=[84],pos='Midfielder',precision='broad_only',broad='MED'),
9497255:dict(name='Mevlüt Kahraman',dob='1973-09-01',nats=[84],pos='Midfielder',precision='broad_only',broad='MED'),
9497256:dict(name='Serdar Şahin',dob='1974-02-10',nats=[84],role=17,pos='Centre-Forward'),
9497257:dict(name='İsmail Demirci',dob='1968-11-27',nats=[84],role=17,pos='Centre-Forward'),
}
COUNTRY={72:'Rumanía',84:'Turquía'}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split(n):
 a=n.split();return (None,n) if len(a)<2 else (' '.join(a[:-1]),a[-1])

def main():
 snap=load(SNAP);reg=load(REG);queue=load(QUEUE);stages={k:load(v) for k,v in STAGES.items()}
 before=profile_gap_stats(snap); by={int(x['source_id']):x for x in snap['players']}; originals=[x for x in snap['players'] if not x.get('external_origin') and not x.get('creation_batch')]
 sr=stage_rows(stages);rb={int(x['source_id']):x for x in reg['players']};qb={int(x['source_id']):x for x in queue['players']}
 changes=[]
 for sid,patch in P.items():
  p=by[sid]; b={'name':p.get('display_name'),'role':int(p.get('primary_role') or 0),'pos':p.get('historical_position_1993_94'),'birth':p.get('birth_date'),'country':p.get('international_country_id')}
  p['display_name']=patch['name'];f,s=split(patch['name']);p['first_name']=f;p['surname1']=s;p['birth_date']=patch['dob']+'T00:00:00'
  nats=patch['nats'];p['international_country_id']=nats[0];p['profile_nationality_country_ids']=nats
  if patch.get('height') is not None:p['height_cm']=patch['height']
  if patch.get('foot') is not None:p['preferred_foot']=patch['foot']
  p['source_profile_position']=patch['pos'];p['profile_position_precision']=patch.get('precision','exact');p['historical_profile_source']='Transfermarkt detailed squad 1993-94 v0.32';p['historical_profile_source_url']=SOURCE;p['profile_review_required']=patch.get('precision')=='broad_only'
  role=patch.get('role')
  if role is not None:
   p['role_ratings']=role_ratings(role);p['primary_role']=role;p['broad_position']=ROLE_TO_BROAD[role];p['historical_position_1993_94']=ROLE_TO_LABEL[role];p['historical_position_source']='Transfermarkt detailed squad 1993-94 v0.32'
   if role!=b['role']:
    a,c=comparable(originals,ROLE_TO_BROAD[role],int(p.get('overall') or 70),sid);p['attributes']=materialise_attributes(int(p.get('overall') or 70),a,c);p['attribute_source']='fixed_source_comparable_role_correction_0.32';p['attribute_comparable_source_ids']=[int(a['source_id']),int(c['source_id'])]
  else:
   p['broad_position']=patch['broad'];p['historical_position_1993_94']=patch['pos']+' (exact role unresolved)';p['historical_position_source']='Transfermarkt broad squad category 1993-94 v0.32'
  for row in sr.get(sid,[]):
   row.update({'resolved_display_name':p['display_name'],'resolved_primary_role':int(p.get('primary_role') or 0),'resolved_exact_position':p.get('historical_position_1993_94'),'resolved_birth_date':p.get('birth_date'),'resolved_country_id':p.get('international_country_id'),'profile_source_url':SOURCE,'profile_source':'Transfermarkt detailed squad 1993-94 v0.32','source_profile_position':patch['pos'],'position_source':'season_specific_profile_v0.32'})
  for t in (rb.get(sid),qb.get(sid)):
   if t:t.update({'display_name':p['display_name'],'birth_date':patch['dob'],'country_id':nats[0],'country_name':COUNTRY[nats[0]],'broad_position':p.get('broad_position'),'historical_position_1993_94':p.get('historical_position_1993_94'),'profile_review_required':bool(p.get('profile_review_required')),'individual_profile_source':'Transfermarkt detailed squad 1993-94 v0.32','individual_profile_source_url':SOURCE})
  changes.append({'source_id':sid,'before':b,'after':{'name':p['display_name'],'role':int(p.get('primary_role') or 0),'pos':p.get('historical_position_1993_94'),'birth':p.get('birth_date'),'country':p.get('international_country_id'),'height':p.get('height_cm'),'foot':p.get('preferred_foot')},'source_position':patch['pos']})
 after=profile_gap_stats(snap); role_changes=sum(x['before']['role']!=x['after']['role'] for x in changes if 'exact role unresolved' not in x['after']['pos'])
 dump(SNAP,snap);dump(REG,reg);dump(QUEUE,queue)
 for k,v in STAGES.items():dump(v,stages[k])
 auditp=DATA/'historical_profiles_metadata_audit_v032.json';audit=load(auditp)
 audit['profiles']['second_batch']='Samsunspor 1993-94 detailed squad';audit['profiles']['samsunspor_curated']=len(changes);audit['profiles']['samsunspor_role_corrections']=role_changes;audit['profiles']['samsunspor_review_required']=sum(bool(by[s]['profile_review_required']) for s in P);audit['profiles']['samsunspor_source']=SOURCE;audit['profiles']['samsunspor_changes']=changes;audit['profiles']['curated_total_v032']=audit['profiles'].get('curated',0)+len(changes);audit['profiles']['role_corrections_total_v032']=audit['profiles'].get('role_corrections',0)+role_changes;audit['profile_gaps_after']=after;dump(auditp,audit)
 gapsp=DATA/'historical_metadata_gaps_v032.json';g=load(gapsp);g['profile_gaps']=after;g['profile_review_queue'] += [{'source_id':sid,'display_name':P[sid]['name'],'reason':'season source only gives broad '+P[sid]['pos']+' category; exact role remains source-gated'} for sid in P if P[sid].get('precision')=='broad_only'];dump(gapsp,g)
 print(json.dumps({'status':'pass','samsunspor_profiles':len(changes),'role_corrections':role_changes,'review_required':sum(bool(by[s]['profile_review_required']) for s in P),'profile_gaps_after':after},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
