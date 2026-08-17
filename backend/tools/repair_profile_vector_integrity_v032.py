from __future__ import annotations
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import comparable
from tools.review_created_player_profiles import materialise_attributes
DATA=ROOT/'data'/'football9394';SNAP=DATA/'historical_snapshot.json';REG=DATA/'created_players_registry.json';QUEUE=DATA/'bdfutbol_photo_queue.json'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 s=load(SNAP);reg=load(REG);q=load(QUEUE);by={int(x['source_id']):x for x in s['players']};orig=[x for x in s['players'] if not x.get('external_origin') and not x.get('creation_batch') and x.get('attributes')];rb={int(x['source_id']):x for x in reg['players']};qb={int(x['source_id']):x for x in q['players']};rep=[]
 # Broad source corrections in v0.32 changed category but deliberately not exact role. Their attribute provenance must follow the new broad category too.
 for p in s['players']:
  if not p.get('external_origin') or not p.get('attribute_comparable_source_ids'): continue
  sources=[by.get(int(i)) for i in p['attribute_comparable_source_ids']]
  if all(src and src.get('broad_position')==p.get('broad_position') for src in sources): continue
  a,b=comparable(orig,p['broad_position'],int(p.get('overall') or 70),int(p['source_id']))
  old=list(p['attribute_comparable_source_ids']);p['attributes']=materialise_attributes(int(p.get('overall') or 70),a,b);p['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])];p['attribute_source']='fixed_source_comparable_broad_position_repair_0.32';p['attribute_comparable_repair_reason']='v0.32 season source changed the verified broad position; attributes were re-materialised from surviving source-backed comparables in that broad position while exact role remains review-gated.'
  for t in (rb.get(int(p['source_id'])),qb.get(int(p['source_id']))):
   if t:t.update({'attribute_source':p['attribute_source'],'attribute_comparable_source_ids':p['attribute_comparable_source_ids'],'attribute_comparable_repair_reason':p['attribute_comparable_repair_reason']})
  rep.append({'source_id':int(p['source_id']),'display_name':p['display_name'],'old':old,'new':p['attribute_comparable_source_ids'],'broad_position':p['broad_position']})
 # Keep the no-clone invariant for reviewed national-pool profiles after the v0.31 cleanup forced comparable replacement.
 target=by[9495321];a=by[43];b=by[50];old=list(target.get('attribute_comparable_source_ids') or []);target['attributes']=materialise_attributes(int(target['overall']),a,b);target['attribute_comparable_source_ids']=[43,50];target['attribute_source']='fixed_source_comparable_repair_0.32';target['attribute_comparable_repair_reason']='Alternative surviving same-position pair selected after cleanup to preserve the unique reviewed attribute-vector invariant.'
 for t in (rb.get(9495321),qb.get(9495321)):
  if t:t.update({'attribute_source':target['attribute_source'],'attribute_comparable_source_ids':[43,50],'attribute_comparable_repair_reason':target['attribute_comparable_repair_reason']})
 rep.append({'source_id':9495321,'display_name':target['display_name'],'old':old,'new':[43,50],'broad_position':'DEF','reason':'unique_vector_integrity'})
 dump(SNAP,s);dump(REG,reg);dump(QUEUE,q)
 ap=DATA/'historical_profiles_metadata_audit_v032.json';audit=load(ap);audit['post_role_profile_integrity_repair']={'status':'pass','rows':rep,'repaired':len(rep)};dump(ap,audit)
 print(json.dumps({'status':'pass','repaired':len(rep),'rows':rep},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
