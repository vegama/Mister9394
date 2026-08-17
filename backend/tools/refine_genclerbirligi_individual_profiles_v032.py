from __future__ import annotations
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'; SNAP=DATA/'historical_snapshot.json'; REG=DATA/'created_players_registry.json'; QUEUE=DATA/'bdfutbol_photo_queue.json'; STAGE=DATA/'turkey_1993_94_roster_staging.json'
PATCH={
 9496447:dict(name='Ace Khuse',dob='1963-09-08',birth_country=78,birth_place='Johannesburg',bdf='702561',profile='https://www.bdfutbol.com/en/j/j702561.html',full='Donald Themba Khuse',note='DOB 1963-09-08 follows BDFutbol and National-Football-Teams; Transfermarkt season/profile aggregator reports 1968 and is retained as a documented source conflict.'),
 9496437:dict(name='Ergün Penbe',dob='1972-05-17',birth_country=84,birth_place='Zonguldak',bdf='46413',profile='https://www.bdfutbol.com/en/j/j46413.html'),
 9496438:dict(name='Rahim Zafer',dob='1971-01-25',birth_country=84,birth_place='Sakarya',bdf='57628',profile='https://www.bdfutbol.com/en/j/j57628.html'),
 9496441:dict(name='John Leshiba Moshoeu',dob='1965-12-18',birth_country=78,birth_place='Soweto',bdf='55569',profile='https://www.bdfutbol.com/en/j/j55569.html'),
 9496444:dict(name="Andre Kona N'Gole",dob='1970-06-16',birth_country=88,birth_place='Lubumbashi',bdf='702421',profile='https://www.bdfutbol.com/en/j/j702421.html',height=181),
}
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 snap=load(SNAP);reg=load(REG);queue=load(QUEUE);stage=load(STAGE);by={int(x['source_id']):x for x in snap['players']};rb={int(x['source_id']):x for x in reg['players']};qb={int(x['source_id']):x for x in queue['players']}
 club=next(c for c in stage['clubs'] if c.get('name')=='Gençlerbirliği')
 for sid,a in PATCH.items():
  p=by[sid];p['display_name']=a['name'];p['birth_date']=a['dob']+'T00:00:00';p['birth_country_id']=a['birth_country'];p['historical_birth_place_text']=a['birth_place'];p['historical_birth_place_source_url']=a['profile'];p['bdfutbol_id']=a['bdf'];p['bdfutbol_url']=a['profile'];p['historical_profile_source_url']=a['profile'];p['historical_profile_source']='BDFutbol individual identity/profile + season role v0.32'
  if a.get('full'): p['historical_full_name']=a['full']
  if a.get('note'): p['historical_profile_source_note']=a['note'];p['birth_date_source_conflict']=True
  if a.get('height'): p['height_cm']=a['height']
  for r in club['players']:
   if int(r.get('resolved_source_id') or -1)==sid:
    r['resolved_display_name']=a['name'];r['resolved_birth_date']=a['dob']+'T00:00:00';r['individual_profile_source_url']=a['profile'];r['bdfutbol_id']=a['bdf']
  for t in (rb.get(sid),qb.get(sid)):
   if t:
    t.update({'display_name':a['name'],'birth_date':a['dob'],'bdfutbol_id':a['bdf'],'bdfutbol_url':a['profile'],'individual_profile_source':'BDFutbol individual profile v0.32','individual_profile_source_url':a['profile'],'historical_birth_place_text':a['birth_place']})
    if a.get('note'): t['profile_source_note']=a['note']
 dump(SNAP,snap);dump(REG,reg);dump(QUEUE,queue);dump(STAGE,stage)
 audit_path=DATA/'historical_profiles_metadata_audit_v032.json';audit=load(audit_path);audit['profiles']['genclerbirligi_individual_profile_refinements']=[{'source_id':sid,'display_name':a['name'],'profile_url':a['profile'],'birth_place':a['birth_place']} for sid,a in PATCH.items()];audit['profiles']['genclerbirligi_source_conflicts']=[{'source_id':9496447,'display_name':'Ace Khuse','field':'birth_date','chosen':'1963-09-08','conflicting_source_value':'1968-09-08','resolution':'BDFutbol + National-Football-Teams consensus over Transfermarkt aggregator'}];dump(audit_path,audit)
 print(json.dumps({'status':'pass','refined':len(PATCH),'ace_birth_date':by[9496447]['birth_date']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
