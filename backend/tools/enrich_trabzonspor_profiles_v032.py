from __future__ import annotations
from pathlib import Path
import json,sys
from typing import Any
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import role_ratings,ROLE_TO_BROAD,ROLE_TO_LABEL,comparable,stage_rows,profile_gap_stats
from tools.review_created_player_profiles import materialise_attributes
DATA=ROOT/'data'/'football9394';SNAP=DATA/'historical_snapshot.json';REG=DATA/'created_players_registry.json';QUEUE=DATA/'bdfutbol_photo_queue.json'
STAGES={'Belgium':DATA/'belgium_1993_94_roster_staging.json','Turkey':DATA/'turkey_1993_94_roster_staging.json','Russia':DATA/'russia_1993_roster_staging.json','Greece':DATA/'greece_1993_94_roster_staging.json'}
SOURCE='https://www.transfermarkt.com.tr/trabzonspor/kader/verein/449/saison_id/1993/plus/1'
P:dict[int,dict[str,Any]]={
9496375:dict(name='Ramazan Silin',dob='1965-05-01',nats=[84],role=0,pos='Goalkeeper'),
9495335:dict(name='Abdullah Ercan',dob='1971-12-08',nats=[84],height=182,foot=2,role=13,pos='Left Midfield'),
9496376:dict(name='Hamdi Aslan',dob='1967-09-06',nats=[84],role=5,pos='Sweeper'),
9496377:dict(name='Kemal Serdar',dob='1962-05-08',nats=[84],height=178,role=3,pos='Centre-Back'),
9495321:dict(name='Ogün Temizkanoğlu',dob='1969-10-06',nats=[84,4],role=3,pos='Centre-Back'),
9496378:dict(name='Orhan Çıkırıkçı',dob='1967-04-15',nats=[84],height=180,foot=2,role=13,pos='Left Midfield'),
9495333:dict(name='Ünal Karaman',dob='1966-06-29',nats=[84],role=8,pos='Attacking Midfield'),
9495344:dict(name='Tolunay Kafkas',dob='1968-03-31',nats=[84],height=188,foot=1,role=6,pos='Defensive Midfield'),
9495349:dict(name='Hami Mandıralı',dob='1968-07-20',nats=[84],height=178,foot=1,role=17,pos='Centre-Forward'),
9496380:dict(name='Shota Arveladze',dob='1973-02-22',nats=[104],height=181,foot=3,role=17,pos='Centre-Forward'),
9495328:dict(name='Cengiz Atila',dob='1966-07-27',nats=[84],height=192,role=3,pos='Centre-Back'),
9496381:dict(name='Viktor Gryshko',dob='1961-11-02',nats=[85],role=0,pos='Goalkeeper'),
9496382:dict(name='Soner Boz',dob='1968-01-12',nats=[84],role=9,pos='Right Midfield'),
9496383:dict(name='Lemi Çelik',dob='1966-03-09',nats=[84],role=6,pos='Defensive Midfield'),
9496384:dict(name='Orhan Kaynak',dob='1970-03-01',nats=[84],height=180,foot=1,role=17,pos='Centre-Forward'),
9496385:dict(name='Archil Arveladze',dob='1973-02-22',nats=[104],role=17,pos='Centre-Forward'),
9496386:dict(name='Nihat Tümkaya',dob='1971-03-24',nats=[84],height=190,foot=1,role=0,pos='Goalkeeper'),
9496387:dict(name='Osman Özköylü',dob='1971-08-26',nats=[84],height=188,foot=1,role=3,pos='Centre-Back'),
9497237:dict(name='Yuriy Shelepnytskyi',dob='1965-01-18',nats=[85],height=184,role=6,pos='Defensive Midfield'),
9497238:dict(name='Mehmet Alarçin',dob='1972-12-01',nats=[84],role=3,pos='Centre-Back'),
9497239:dict(name='Ender Traş',dob='1972-08-30',nats=[84],role=8,pos='Attacking Midfield'),
9497240:dict(name='Saffet Akyüz',dob='1970-03-11',nats=[84],height=182,foot=1,role=17,pos='Centre-Forward'),
9497241:dict(name='Ülken Durak',dob='1966-06-17',nats=[84,4],foot=2,role=2,pos='Left-Back'),
9497242:dict(name='Sergiy Gusev',dob='1967-07-01',nats=[85],height=180,foot=2,role=17,pos='Centre-Forward'),
9497243:dict(name='Süleyman Usta',dob='1973-08-03',nats=[84],role=3,pos='Centre-Back'),
}
COUNTRY={4:'Alemania',84:'Turquía',85:'Ucrania',104:'Georgia'}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split(n):
 a=n.split();return (None,n) if len(a)<2 else (' '.join(a[:-1]),a[-1])
def main():
 snap=load(SNAP);reg=load(REG);queue=load(QUEUE);stages={k:load(v) for k,v in STAGES.items()};before=profile_gap_stats(snap)
 by={int(x['source_id']):x for x in snap['players']};originals=[x for x in snap['players'] if not x.get('external_origin') and not x.get('creation_batch')];sr=stage_rows(stages);rb={int(x['source_id']):x for x in reg['players']};qb={int(x['source_id']):x for x in queue['players']};changes=[]
 for sid,patch in P.items():
  p=by[sid];b={'name':p.get('display_name'),'role':int(p.get('primary_role') or 0),'pos':p.get('historical_position_1993_94'),'birth':p.get('birth_date'),'country':p.get('international_country_id')};p['display_name']=patch['name'];f,s=split(patch['name']);p['first_name']=f;p['surname1']=s;p['birth_date']=patch['dob']+'T00:00:00';nats=patch['nats'];p['international_country_id']=nats[0];p['profile_nationality_country_ids']=nats
  if len(nats)>1:p['secondary_nationality_country_id']=nats[1]
  if patch.get('height') is not None:p['height_cm']=patch['height']
  if patch.get('foot') is not None:p['preferred_foot']=patch['foot']
  role=patch['role'];p['source_profile_position']=patch['pos'];p['profile_position_precision']='exact';p['historical_profile_source']='Transfermarkt detailed squad 1993-94 v0.32';p['historical_profile_source_url']=SOURCE;p['profile_review_required']=False;p['role_ratings']=role_ratings(role);p['primary_role']=role;p['broad_position']=ROLE_TO_BROAD[role];p['historical_position_1993_94']=ROLE_TO_LABEL[role];p['historical_position_source']='Transfermarkt detailed squad 1993-94 v0.32'
  if role!=b['role']:
   a,c=comparable(originals,ROLE_TO_BROAD[role],int(p.get('overall') or 70),sid);p['attributes']=materialise_attributes(int(p.get('overall') or 70),a,c);p['attribute_source']='fixed_source_comparable_role_correction_0.32';p['attribute_comparable_source_ids']=[int(a['source_id']),int(c['source_id'])]
  for row in sr.get(sid,[]):row.update({'resolved_display_name':p['display_name'],'resolved_primary_role':role,'resolved_exact_position':p['historical_position_1993_94'],'resolved_birth_date':p['birth_date'],'resolved_country_id':nats[0],'profile_source_url':SOURCE,'profile_source':'Transfermarkt detailed squad 1993-94 v0.32','source_profile_position':patch['pos'],'position_source':'season_specific_profile_v0.32'})
  for t in (rb.get(sid),qb.get(sid)):
   if t:t.update({'display_name':p['display_name'],'birth_date':patch['dob'],'country_id':nats[0],'country_name':COUNTRY[nats[0]],'broad_position':p['broad_position'],'historical_position_1993_94':p['historical_position_1993_94'],'profile_review_required':False,'individual_profile_source':'Transfermarkt detailed squad 1993-94 v0.32','individual_profile_source_url':SOURCE})
  changes.append({'source_id':sid,'before':b,'after':{'name':p['display_name'],'role':role,'pos':p['historical_position_1993_94'],'birth':p['birth_date'],'country':nats[0],'height':p.get('height_cm'),'foot':p.get('preferred_foot')},'source_position':patch['pos']})
 after=profile_gap_stats(snap);role_changes=sum(x['before']['role']!=x['after']['role'] for x in changes);dump(SNAP,snap);dump(REG,reg);dump(QUEUE,queue)
 for k,v in STAGES.items():dump(v,stages[k])
 ap=DATA/'historical_profiles_metadata_audit_v032.json';a=load(ap);a['profiles']['third_batch']='Trabzonspor 1993-94 detailed squad';a['profiles']['trabzonspor_curated']=len(changes);a['profiles']['trabzonspor_role_corrections']=role_changes;a['profiles']['trabzonspor_source']=SOURCE;a['profiles']['trabzonspor_changes']=changes;a['profiles']['curated_total_v032']=a['profiles'].get('curated_total_v032',a['profiles'].get('curated',0))+len(changes);a['profiles']['role_corrections_total_v032']=a['profiles'].get('role_corrections_total_v032',a['profiles'].get('role_corrections',0))+role_changes;a['profile_gaps_after']=after;dump(ap,a)
 gp=DATA/'historical_metadata_gaps_v032.json';g=load(gp);g['profile_gaps']=after;dump(gp,g)
 print(json.dumps({'status':'pass','trabzonspor_profiles':len(changes),'role_corrections':role_changes,'profile_gaps_after':after},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
