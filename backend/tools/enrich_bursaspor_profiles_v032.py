from __future__ import annotations
from pathlib import Path
import json,sys
from typing import Any
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import role_ratings,ROLE_TO_BROAD,ROLE_TO_LABEL,comparable,stage_rows,profile_gap_stats
from tools.review_created_player_profiles import materialise_attributes
DATA=ROOT/'data'/'football9394';SNAP=DATA/'historical_snapshot.json';REG=DATA/'created_players_registry.json';QUEUE=DATA/'bdfutbol_photo_queue.json'
STAGES={'Belgium':DATA/'belgium_1993_94_roster_staging.json','Turkey':DATA/'turkey_1993_94_roster_staging.json','Russia':DATA/'russia_1993_roster_staging.json','Greece':DATA/'greece_1993_94_roster_staging.json'}
SOURCE='https://www.transfermarkt.com.tr/bursaspor/startseite/verein/20/saison_id/1993'
LINEUP_SOURCE='https://www.transfermarkt.com.tr/bursaspor_genclerbirligi-sk/aufstellung/spielbericht/952297'
# 30 identities already active in the reconstructed Bursaspor roster. Vedat Emmez is source-visible but not yet in staging;
# this pass intentionally enriches existing identities without silently creating a 31st player.
P:dict[int,dict[str,Any]]={
9496471:dict(name='Ivko Ganchev',dob='1965-07-21',nats=[21,84],role=0,pos='Goalkeeper'),
9496487:dict(name='Abdullah Kılıç',dob='1972-08-08',nats=[84],role=0,pos='Goalkeeper'),
9496482:dict(name='Nevzat Dinçbudak',dob='1965-10-26',nats=[84],role=0,pos='Goalkeeper'),
9496473:dict(name='Feti Okuroğlu',dob='1971-08-05',nats=[84],role=5,pos='Sweeper',secondary=[(6,'Defensive Midfielder')]),
9497290:dict(name='Fatih Çayla',dob='1975-09-13',nats=[84],pos='Defender',precision='broad_only',broad='DEF'),
9495326:dict(name='Sedat Balkanlı',dob='1965-01-15',nats=[84],role=3,pos='Centre-Back'),
9497281:dict(name='Mesut Ünal',dob='1973-04-03',nats=[84],role=3,pos='Centre-Back'),
9496485:dict(name='Yalçın Gündüz',dob='1966-02-04',nats=[84],role=3,pos='Centre-Back'),
9496472:dict(name='Turhan Şen',dob='1966-03-09',nats=[84,21],role=3,pos='Centre-Back',secondary=[(6,'Defensive Midfielder')]),
9496474:dict(name='Adnan Örnek',dob='1965-10-17',nats=[84],role=3,pos='Centre-Back',secondary=[(2,'Left-Back')]),
9497288:dict(name='Cihan Bastık',dob='1974-10-11',nats=[84],role=3,pos='Centre-Back'),
9497280:dict(name='Şaban Yıldırım',dob='1970-01-25',nats=[84],role=2,pos='Left-Back'),
9496476:dict(name='Ümit Şengül',dob='1968-09-06',nats=[84],role=2,pos='Left-Back'),
9496486:dict(name='Ahmet Suphi Evke',dob='1965-02-06',nats=[84],role=1,pos='Right-Back',secondary=[(9,'Right Midfielder')]),
9496483:dict(name='Ersel Uzğur',dob='1967-01-01',nats=[84],role=1,pos='Right-Back'),
9496488:dict(name='Turhan Sofuoğlu',dob='1965-08-19',nats=[84],role=6,pos='Defensive Midfield'),
9497289:dict(name='İlker Özdemir',dob='1975-02-16',nats=[84],pos='Midfielder',precision='broad_only',broad='MED'),
9497282:dict(name='Serkan Arslan',dob='1974-08-02',nats=[84],pos='Midfielder',precision='broad_only',broad='MED'),
9497284:dict(name='Zafer Baştan',dob='1975-11-03',nats=[84],role=7,pos='Central Midfield'),
9497286:dict(name='Engin Şentürk',dob='1973-12-24',nats=[84],role=13,pos='Left Midfield'),
9496477:dict(name='Tunahan Akdoğan',dob='1967-10-19',nats=[84],role=13,pos='Left Midfield'),
9496481:dict(name='Ali Nail Durmuş',dob='1970-11-20',nats=[84],role=8,pos='Attacking Midfield'),
9497283:dict(name='Ali Rıza Yılmaz',dob='1968-01-02',nats=[84,4],role=8,pos='Attacking Midfield'),
9496478:dict(name='Volkan Velioğlu',dob='1972-05-31',nats=[84],role=8,pos='Attacking Midfield'),
9496479:dict(name='Frank Pingel',dob='1964-05-09',nats=[33],role=17,pos='Centre-Forward'),
9496480:dict(name='Gøran Sørloth',dob='1962-07-16',nats=[60],role=17,pos='Centre-Forward'),
9496475:dict(name='Vedat Vatansever',dob='1969-09-20',nats=[84],role=17,pos='Centre-Forward'),
9497287:dict(name='Muhammet Dilaver',dob='1965-12-31',nats=[84],role=17,pos='Centre-Forward'),
9497285:dict(name='Egemen Bayhan',dob='1977-12-17',nats=[84],role=17,pos='Centre-Forward'),
9497291:dict(name='Ramazan Gürbüz',dob='1977-05-05',nats=[84],pos='Forward',precision='broad_only',broad='DEL'),
}
COUNTRY={4:'Alemania',21:'Bulgaria',33:'Dinamarca',60:'Noruega',84:'Turquía'}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split(n):
 a=n.split();return (None,n) if len(a)<2 else (' '.join(a[:-1]),a[-1])

def main():
 snap=load(SNAP);reg=load(REG);queue=load(QUEUE);stages={k:load(v) for k,v in STAGES.items()};before=profile_gap_stats(snap)
 by={int(x['source_id']):x for x in snap['players']};originals=[x for x in snap['players'] if not x.get('external_origin') and not x.get('creation_batch')];sr=stage_rows(stages);rb={int(x['source_id']):x for x in reg['players']};qb={int(x['source_id']):x for x in queue['players']};changes=[]
 for sid,patch in P.items():
  p=by[sid];b={'name':p.get('display_name'),'role':int(p.get('primary_role') or 0),'pos':p.get('historical_position_1993_94'),'birth':p.get('birth_date'),'country':p.get('international_country_id')}
  p['display_name']=patch['name'];f,s=split(patch['name']);p['first_name']=f;p['surname1']=s;p['birth_date']=patch['dob']+'T00:00:00';nats=patch['nats'];p['international_country_id']=nats[0];p['profile_nationality_country_ids']=nats
  if len(nats)>1:p['secondary_nationality_country_id']=nats[1]
  p['source_profile_position']=patch['pos'];p['profile_position_precision']=patch.get('precision','exact');p['historical_profile_source']='Transfermarkt Bursaspor season squad 1993-94 v0.32';p['historical_profile_source_url']=SOURCE;p['profile_review_required']=patch.get('precision')=='broad_only'
  role=patch.get('role')
  if role is not None:
   rr=role_ratings(role)
   if patch.get('secondary'):
    for secondary_role,label in patch['secondary']:
     rr[str(secondary_role)]=max(rr.get(str(secondary_role),0),65)
    p['historical_secondary_positions_1993_94']=[label for _,label in patch['secondary']];p['historical_secondary_position_source']=LINEUP_SOURCE
   p['role_ratings']=rr;p['primary_role']=role;p['broad_position']=ROLE_TO_BROAD[role];p['historical_position_1993_94']=ROLE_TO_LABEL[role];p['historical_position_source']='Transfermarkt Bursaspor season squad 1993-94 v0.32'
   if role!=b['role']:
    a,c=comparable(originals,ROLE_TO_BROAD[role],int(p.get('overall') or 70),sid);p['attributes']=materialise_attributes(int(p.get('overall') or 70),a,c);p['attribute_source']='fixed_source_comparable_role_correction_0.32';p['attribute_comparable_source_ids']=[int(a['source_id']),int(c['source_id'])]
  else:
   p['broad_position']=patch['broad'];p['historical_position_1993_94']=patch['pos']+' (exact role unresolved)';p['historical_position_source']='Transfermarkt broad squad category 1993-94 v0.32'
  for row in sr.get(sid,[]):
   row.update({'resolved_display_name':p['display_name'],'resolved_primary_role':int(p.get('primary_role') or 0),'resolved_exact_position':p.get('historical_position_1993_94'),'resolved_birth_date':p.get('birth_date'),'resolved_country_id':nats[0],'profile_source_url':SOURCE,'profile_source':'Transfermarkt Bursaspor season squad 1993-94 v0.32','source_profile_position':patch['pos'],'position_source':'season_specific_profile_v0.32'})
  for t in (rb.get(sid),qb.get(sid)):
   if t:t.update({'display_name':p['display_name'],'birth_date':patch['dob'],'country_id':nats[0],'country_name':COUNTRY[nats[0]],'broad_position':p.get('broad_position'),'historical_position_1993_94':p.get('historical_position_1993_94'),'profile_review_required':bool(p.get('profile_review_required')),'individual_profile_source':'Transfermarkt Bursaspor season squad 1993-94 v0.32','individual_profile_source_url':SOURCE})
  changes.append({'source_id':sid,'before':b,'after':{'name':p['display_name'],'role':int(p.get('primary_role') or 0),'pos':p.get('historical_position_1993_94'),'birth':p.get('birth_date'),'country':p.get('international_country_id')},'source_position':patch['pos'],'secondary_positions':p.get('historical_secondary_positions_1993_94',[])})
 after=profile_gap_stats(snap);role_changes=sum(x['before']['role']!=x['after']['role'] for x in changes if 'exact role unresolved' not in x['after']['pos'])
 dump(SNAP,snap);dump(REG,reg);dump(QUEUE,queue)
 for k,v in STAGES.items():dump(v,stages[k])
 ap=DATA/'historical_profiles_metadata_audit_v032.json';a=load(ap);pr=a['profiles'];pr['fourth_batch']='Bursaspor 1993-94 season squad';pr['bursaspor_curated']=len(changes);pr['bursaspor_role_corrections']=role_changes;pr['bursaspor_review_required']=sum(bool(by[s]['profile_review_required']) for s in P);pr['bursaspor_source']=SOURCE;pr['bursaspor_lineup_crosscheck_source']=LINEUP_SOURCE;pr['bursaspor_changes']=changes;pr['bursaspor_source_visible_not_in_active_staging']=['Vedat Emmez'];pr['curated_total_v032']=pr.get('curated_total_v032',0)+len(changes);pr['role_corrections_total_v032']=pr.get('role_corrections_total_v032',0)+role_changes;a['profile_gaps_after']=after;dump(ap,a)
 gp=DATA/'historical_metadata_gaps_v032.json';g=load(gp);g['profile_gaps']=after
 # rebuild only review queue from actual current target players to avoid duplicate accumulation across incremental scripts
 target_teams={9352001,9352002,9352003,9352004,9352005,9352006,*range(9357001,9357015),*range(9360001,9360017),*range(9347001,9347019)}
 g['profile_review_queue']=[{'source_id':int(x['source_id']),'display_name':x.get('display_name'),'reason':'season source only gives a broad position category; exact role remains source-gated'} for x in snap['players'] if int(x.get('team_id') or 0) in target_teams and x.get('profile_review_required')]
 g['known_source_roster_differences']=g.get('known_source_roster_differences',[])+[{'team_id':9357007,'team':'Bursaspor','source_player':'Vedat Emmez','status':'source-visible_not_in_active_staging','source':SOURCE}]
 dump(gp,g)
 print(json.dumps({'status':'pass','bursaspor_profiles':len(changes),'role_corrections':role_changes,'review_required':sum(bool(by[s]['profile_review_required']) for s in P),'curated_total_v032':pr['curated_total_v032'],'role_corrections_total_v032':pr['role_corrections_total_v032'],'profile_gaps_after':after},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
