from __future__ import annotations
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import role_ratings,comparable,profile_gap_stats
from tools.review_created_player_profiles import materialise_attributes
DATA=ROOT/'data'/'football9394';SNAP=DATA/'historical_snapshot.json';REG=DATA/'created_players_registry.json';QUEUE=DATA/'bdfutbol_photo_queue.json';STAGE=DATA/'turkey_1993_94_roster_staging.json'
SID=9498000;TEAM=9357007;BATCH='turkey_bursaspor_roster_completion_0.32';TM='https://www.transfermarkt.com.tr/bursaspor/startseite/verein/20/saison_id/1993';BDF='https://www.bdfutbol.com/j/j700700.html?p=stats'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 snap=load(SNAP);reg=load(REG);queue=load(QUEUE);stage=load(STAGE)
 existing=next((p for p in snap['players'] if int(p['source_id'])==SID),None)
 if existing:
  print(json.dumps({'status':'already_present','source_id':SID},indent=2)); return
 if any((p.get('display_name') or '').casefold()=='vedat emmez'.casefold() for p in snap['players']): raise RuntimeError('Vedat Emmez already exists under another source id')
 originals=[p for p in snap['players'] if p.get('attributes')]
 a,b=comparable(originals,'POR',66,SID)
 attrs=materialise_attributes(66,a,b)
 p={
  'source_id':SID,'team_id':TEAM,'display_name':'Vedat Emmez','first_name':'Vedat','surname1':'Emmez','surname2':None,
  'birth_date':'1975-10-03T00:00:00','birth_country_id':84,'international_country_id':84,'preferred_foot':None,'shirt_number':None,
  'primary_role':0,'broad_position':'POR','overall':66,'category':66,'height_cm':None,'weight_kg':None,'salary':0,'release_clause':0,
  'contract_start_year':1993,'contract_end_year':None,'loan':False,'initially_reserve':True,'retired':False,'attributes':attrs,
  'birth_city_id':None,'naturalized_country_id':None,'basque_origin':False,'favorite_shirt_number':None,'injury_proneness':0,'progression_mean':0,
  'fan_affection':0,'academy_team_id':None,'previous_team_id':None,'previous_team_years':None,'buyback_option':False,
  'role_ratings':role_ratings(0),'hidden_traits':{'individualist':False,'killer_pass':False,'holds_ball':False,'long_shots':False,'cuts_inside':False,'first_time_play':False,'dives':False},
  'historical_squad_1994':True,'historical_data_source':'Transfermarkt Bursaspor 1993-94 squad + BDFutbol individual identity v0.32',
  'external_origin':'historical_turkey_1993_94','creation_batch':BATCH,'profile_review_required':False,
  'historical_position_1993_94':'Goalkeeper','historical_position_source':'Transfermarkt Bursaspor season squad 1993-94 v0.32',
  'source_profile_position':'Goalkeeper','profile_position_precision':'exact','historical_profile_source':'BDFutbol individual profile + Transfermarkt season squad v0.32',
  'historical_profile_source_url':BDF,'profile_nationality_country_ids':[84],'historical_birth_place_text':'Bursa (Bursa)',
  'attribute_source':'fixed_source_comparable_role_profile_0.32','attribute_comparable_source_ids':[int(a['source_id']),int(b['source_id'])]
 }
 snap['players'].append(p)
 # Append to Bursaspor staging as source-visible squad member without league minutes in the 93/94 BDF table.
 club=next(c for c in stage['clubs'] if c.get('name')=='Bursaspor')
 club['players'].append({'bdfutbol_name':'Emmez','age_1993_94':18,'appearances':0,'starts':0,'minutes':0,'goals':0,'core_18_candidate':False,'source_roster_member':True,
  'identity_resolution':'created_historical_identity','resolved_source_id':SID,'resolved_display_name':'Vedat Emmez','resolved_primary_role':0,'resolved_exact_position':'Goalkeeper',
  'position_source':'season_specific_profile_v0.32','resolved_birth_date':'1975-10-03T00:00:00','resolved_country_id':84,'profile_source_url':TM,
  'profile_source':'Transfermarkt Bursaspor season squad 1993-94 v0.32; BDFutbol individual identity','source_profile_position':'Goalkeeper','individual_profile_source_url':BDF,'bdfutbol_id':'700700'})
 entry={'source_id':SID,'display_name':'Vedat Emmez','first_name':'Vedat','surname1':'Emmez','surname2':None,'birth_date':'1975-10-03','country_id':84,'country_name':'Turquía','broad_position':'POR','team_id':TEAM,'team_name':'Bursaspor','creation_batch':BATCH,
  'identity_source':'Transfermarkt Bursaspor 1993-94 squad + BDFutbol individual identity v0.32','identity_source_url':TM,'verified_national_pool_year':None,'historical_position_1993_94':'Goalkeeper','historical_club_1994':'Bursaspor','overall':66,
  'attribute_source':p['attribute_source'],'profile_review_required':False,'duplicate_check':'exact_name_birthdate_bdfutbol_identity_gate','matched_existing_id':None,'bdfutbol_search_name':'Vedat Emmez','bdfutbol_id':'700700','bdfutbol_url':BDF,'photo_filename':f'{SID}.jpg','photo_status':'pending','individual_profile_source':'BDFutbol individual profile + Transfermarkt season squad v0.32','individual_profile_source_url':BDF}
 reg['players'].append(entry)
 q=dict(entry);q.pop('overall',None);q.pop('attribute_source',None);q.update({'photo_width':40,'photo_height':55,'photo_format':'JPEG','photo_mode':'RGB'})
 queue['players'].append(q)
 dump(SNAP,snap);dump(REG,reg);dump(QUEUE,queue);dump(STAGE,stage)
 # Remove previous "missing source roster player" marker now that it is resolved.
 gp=DATA/'historical_metadata_gaps_v032.json';g=load(gp);g['known_source_roster_differences']=[x for x in g.get('known_source_roster_differences',[]) if not (x.get('team_id')==TEAM and x.get('source_player')=='Vedat Emmez')];g['profile_gaps']=profile_gap_stats(snap);dump(gp,g)
 ap=DATA/'historical_profiles_metadata_audit_v032.json';audit=load(ap);audit['profiles']['bursaspor_source_visible_player_added']={'source_id':SID,'display_name':'Vedat Emmez','overall':66,'position':'Goalkeeper','source':TM,'identity_source':BDF};audit['profiles']['curated_total_v032']=audit['profiles'].get('curated_total_v032',107)+1;audit['profile_gaps_after']=profile_gap_stats(snap);dump(ap,audit)
 print(json.dumps({'status':'pass','source_id':SID,'display_name':'Vedat Emmez','overall':66,'comparables':[a['source_id'],b['source_id']],'profile_gaps_after':profile_gap_stats(snap)},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
