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
 s=load(SNAP);reg=load(REG);q=load(QUEUE);ids={int(x['source_id']) for x in s['players']};by={int(x['source_id']):x for x in s['players']};orig=[x for x in s['players'] if not x.get('external_origin') and not x.get('creation_batch') and x.get('attributes')]
 rb={int(x['source_id']):x for x in reg['players']};qb={int(x['source_id']):x for x in q['players']};rep=[]
 for p in s['players']:
  if not p.get('external_origin'):continue
  cids=p.get('attribute_comparable_source_ids')
  broken=False;old=[]
  if cids:
   old=[int(x) for x in cids];broken=any(x not in ids for x in old)
  else:
   r=p.get('profile_review_0_23') or {};old=[int(r[k]['source_id']) for k in ('primary_comparable','secondary_comparable') if r.get(k) and r[k].get('source_id') is not None];broken=any(x not in ids for x in old)
  if not broken:continue
  broad=p.get('broad_position');ov=int(p.get('overall') or 70);sid=int(p['source_id']);a,b=comparable(orig,broad,ov,sid)
  p['attributes']=materialise_attributes(ov,a,b);p['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])];p['attribute_source']='fixed_source_comparable_repair_0.32';p['attribute_comparable_repair_reason']='v0.31 roster-ID collision cleanup removed one or more legacy comparable identities; regenerated from surviving source-backed same-position comparables.'
  for t in (rb.get(sid),qb.get(sid)):
   if t:t.update({'attribute_source':p['attribute_source'],'attribute_comparable_source_ids':p['attribute_comparable_source_ids'],'attribute_comparable_repair_reason':p['attribute_comparable_repair_reason']})
  rep.append({'source_id':sid,'display_name':p.get('display_name'),'broad_position':broad,'old_comparable_source_ids':old,'new_comparable_source_ids':p['attribute_comparable_source_ids']})
 dump(SNAP,s);dump(REG,reg);dump(QUEUE,q)
 ap=DATA/'historical_profiles_metadata_audit_v032.json';a=load(ap);a['comparable_integrity_repair']={'status':'pass','repaired_players':len(rep),'rows':rep,'policy':'A removed legacy identity may not remain as provenance for generated attributes; affected profiles are re-materialised from two surviving non-created comparables of the same broad position.'};dump(ap,a)
 print(json.dumps({'status':'pass','repaired_players':len(rep),'rows':rep},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
