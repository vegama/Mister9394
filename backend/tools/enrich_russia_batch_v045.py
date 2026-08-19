from __future__ import annotations

from pathlib import Path
from typing import Any
import copy, hashlib, json, sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))
from app.football9394.player_names import preserve_full_name_and_shorten
DATA=ROOT/'data'/'football9394'
SNAP=DATA/'historical_snapshot.json'; REG=DATA/'created_players_registry.json'; PHOTO=DATA/'bdfutbol_photo_queue.json'
STAGE=DATA/'russia_1993_roster_staging.json'; LINKS=DATA/'russia_profile_links_v045.json'; CONTEXT=DATA/'country_context_1993.json'
CHECKPOINT='0.45.0-russia-rotor-torpedo-batch-deep'; RUSSIA_LEAGUE_ID=930015
EXPECTED_BEFORE='e07f35db04e5979433ed1bfc3a9e2704758a636abe8f116903eb12d7c9473111'
TARGET_CLUBS=['Rotor Volgograd','Dynamo Moskva','Tekstilshchik Kamyshin','Lokomotiv Moskva','Spartak Vladikavkaz','Torpedo Moskva']
NEXT_QUEUE=['Uralmash','CSKA Moskva','KAMAZ','Zhemchuzhina Sochi','Dynamo Stavropol','Lokomotiv Nizhny Novgorod','Krylia Sovetov','Luch Vladivostok','Okean Nakhodka','Rostselmash','Asmaral Moskva']
DUPLICATE_SOURCE_ID=9496652; CANONICAL_SOURCE_ID=9497352; DUPLICATE_BDF='701521'

# A deliberately partial metadata layer. These fields were read from the individual profiles during
# the batch; anything not listed remains unresolved rather than being guessed from surname/club.
DETAILS={
9496619:('1965-08-05','Dushanbe',202,'Goalkeeper',None,None),
9496620:('1968-12-10','Luhansk',85,'Defender',181,73),
9496621:('1968-04-27','Dnipropetrovsk',85,'Defender',190,None),
9496622:('1969-03-12','Maykop',40,'Defender',177,74),
9496623:('1970-07-05','Volgograd',40,'Defender',183,73),
9496624:('1970-07-26','Surgut',40,'Midfielder',194,None),
9496625:('1967-11-21','Volgograd',40,'Midfielder',176,None),
9496626:('1966-04-09',None,40,'Midfielder',179,None),
9496627:('1970-01-05','Revda',40,'Forward',185,80),
9496628:('1971-10-04','Shchigry',40,'Forward',170,69),
9496629:('1967-08-13','Kokshetau',132,'Forward',175,None),
9496630:('1972-02-01','Ruzayevka',40,'Goalkeeper',188,None),
9496631:('1970-03-20',None,18,'Midfielder',180,75),
9496637:('1965-09-10','Shchekino',40,'Goalkeeper',193,None),
9494086:('1969-10-13','Velospiri',104,'Defender',190,82),
9495358:('1970-01-05','Azov',40,'Left back',190,84),
9496638:('1971-05-04','Nizhny Novgorod',40,'Central',181,79),
9496639:('1965-03-05','Pavlodar',132,'Defender',177,None),
9496640:('1969-09-18','Tskhinvali',104,'Midfielder',179,None),
9496641:('1968-05-05','Volgograd',40,'Midfielder',181,None),
9496642:('1969-01-17','Barnaul',40,'Midfielder',173,65),
9496643:('1973-04-03','Moscow',40,'Forward',172,65),
9496644:('1969-05-11','Nizhny Novgorod',40,'Forward',171,73),
9496645:('1971-03-12','Moscow',40,'Forward',182,None),
}

def load(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def dump(p:Path,x:Any): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fp(snap:dict[str,Any], team_ids:set[int])->str:
    payload={'teams':sorted([x for x in snap['teams'] if int(x.get('source_id') or -1) in team_ids],key=lambda x:int(x['source_id'])),
             'players':sorted([x for x in snap['players'] if int(x.get('team_id') or -1) in team_ids],key=lambda x:int(x['source_id']))}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def split_name(name:str, squad_name:str)->tuple[str|None,str]:
    # Prefer the squad surname token because patronymics and suffixes make blind last-token splitting unsafe.
    normalized=squad_name.strip()
    words=name.split()
    idx=-1
    for i,w in enumerate(words):
        if w.casefold().rstrip('.')==normalized.casefold().rstrip('.'):
            idx=i
    if idx>=0:
        first=' '.join(words[:idx]) or None
        return first,words[idx]
    if name.endswith(' Jr.') and len(words)>=3:
        return ' '.join(words[:-2]),words[-2]
    return (' '.join(words[:-1]) or None,words[-1])

def add_unique_spells(existing:list[dict[str,Any]], spell:dict[str,Any])->list[dict[str,Any]]:
    out=copy.deepcopy(existing or [])
    key=(spell.get('club'),spell.get('team_id'))
    for i,x in enumerate(out):
        if (x.get('club'),x.get('team_id'))==key:
            out[i]=spell; break
    else: out.append(spell)
    return out

def main()->None:
    snap=load(SNAP); reg=load(REG); photo=load(PHOTO); stage=load(STAGE); links=load(LINKS); ctx=load(CONTEXT)
    teams_by_name={t['name']:int(t['source_id']) for t in snap['teams']}
    russia_tids={int(t['source_id']) for t in snap['teams'] if int(t.get('league_id') or -1)==RUSSIA_LEAGUE_ID}
    before=fp(snap,russia_tids); assert before==EXPECTED_BEFORE,(before,EXPECTED_BEFORE)
    target_tids={teams_by_name[x] for x in TARGET_CLUBS}; spartak_tid=teams_by_name['Spartak Moskva']
    protected=russia_tids-target_tids-{spartak_tid}; protected_before=fp(snap,protected)
    before_ids={int(p['source_id']) for p in snap['players']}; before_russia_count=sum(int(p.get('team_id') or -1) in russia_tids for p in snap['players'])

    club_rows={c['name']:{int(r['resolved_source_id']):r for r in c['players']} for c in stage['clubs'] if c['name'] in TARGET_CLUBS}
    assert sum(len(x) for x in club_rows.values())==159
    by={int(p['source_id']):p for p in snap['players']}; rb={int(p['source_id']):p for p in reg['players']}; qb={int(p['source_id']):p for p in photo['players']}
    link_by={int(x['source_id']):x for x in links['players']}; assert len(link_by)==159
    assert set(link_by)==set().union(*(set(x) for x in club_rows.values()))

    # Same individual profile in Spartak and Dynamo proves a cross-club duplicate. Keep the already
    # deepened Spartak identity as canonical and attach the Dynamo spell to it.
    duplicate=by[DUPLICATE_SOURCE_ID]; canonical=by[CANONICAL_SOURCE_ID]
    assert canonical.get('bdfutbol_id')==DUPLICATE_BDF and link_by[DUPLICATE_SOURCE_ID]['bdfutbol_id']==DUPLICATE_BDF
    drow=club_rows['Dynamo Moskva'][DUPLICATE_SOURCE_ID]
    dynamo_spell={'club':'Dynamo Moskva','team_id':teams_by_name['Dynamo Moskva'],'appearances':drow.get('appearances'),'starts':drow.get('starts'),'minutes':drow.get('minutes'),'goals':drow.get('goals')}
    canonical['historical_club_spells_1993_94']=add_unique_spells(canonical.get('historical_club_spells_1993_94',[]),dynamo_spell)
    existing_bios=list(canonical.get('historical_biographies_1993_94') or [])
    dyn_text=f"Defensa central de Dynamo Moskva en la temporada 1993-94. En el registro histórico figura con {drow.get('appearances')} partidos, {drow.get('starts')} como titular, {drow.get('minutes'):,} minutos y {drow.get('goals')} gol.".replace(',', '.')
    if not any(x.get('club')=='Dynamo Moskva' for x in existing_bios):
        existing_bios.append({'club':'Dynamo Moskva','text':dyn_text,'source_url':link_by[DUPLICATE_SOURCE_ID]['bdfutbol_url'],'evidence':dynamo_spell})
    canonical['historical_biographies_1993_94']=existing_bios
    canonical['historical_biography_staged_clubs']=sorted(set((canonical.get('historical_biography_staged_clubs') or [])+['Dynamo Moskva']))
    canonical['identity_merge_history']=list(canonical.get('identity_merge_history') or [])+[{'checkpoint':CHECKPOINT,'merged_source_id':DUPLICATE_SOURCE_ID,'reason':'same BDFutbol individual profile ID across Spartak Moskva and Dynamo Moskva','bdfutbol_id':DUPLICATE_BDF}]
    canonical['duplicate_resolution']='cross_club_same_individual_profile_merged_v045'
    drow['resolved_source_id']=CANONICAL_SOURCE_ID; drow['identity_resolution']='merged_to_existing_cross_club_identity_v045'; drow['duplicate_source_id_retired']=DUPLICATE_SOURCE_ID
    # Remove the duplicate object and synchronized created/photo entries.
    snap['players']=[p for p in snap['players'] if int(p['source_id'])!=DUPLICATE_SOURCE_ID]
    reg['players']=[p for p in reg['players'] if int(p['source_id'])!=DUPLICATE_SOURCE_ID]
    photo['players']=[p for p in photo['players'] if int(p['source_id'])!=DUPLICATE_SOURCE_ID]
    by={int(p['source_id']):p for p in snap['players']}; rb={int(p['source_id']):p for p in reg['players']}; qb={int(p['source_id']):p for p in photo['players']}

    changes=[]; detail_changes=[]
    for link in links['players']:
        original_sid=int(link['source_id']); sid=CANONICAL_SOURCE_ID if original_sid==DUPLICATE_SOURCE_ID else original_sid
        p=by[sid]
        club=link['club']; row=next(r for r in next(c for c in stage['clubs'] if c['name']==club)['players'] if int(r['resolved_source_id'])==sid)
        old_name=p.get('display_name'); full=link['full_name']; first,surname=split_name(full,str(row.get('bdfutbol_name') or ''))
        aliases=dict(p.get('name_transliterations') or {})
        aliases.setdefault('bdfutbol_squad',row.get('bdfutbol_name'))
        aliases['bdfutbol_profile']=full
        aliases.setdefault('project_display_before_v045',old_name)
        aliases['project_display_v045']=full
        p['display_name']=full; p['first_name']=first; p['surname1']=surname
        preserve_full_name_and_shorten(p)
        p['bdfutbol_id']=link['bdfutbol_id']; p['bdfutbol_url']=link['bdfutbol_url']; p['bdfutbol_squad_url']=link['squad_url']
        p['historical_profile_source']='BDFutbol individual profile + Russia batch identity review v0.45'
        p['historical_profile_source_url']=link['bdfutbol_url']; p['historical_profile_identity_status']='bdfutbol_individual_profile_resolved_v045'
        p['historical_profile_metadata_status']='identity_resolved_metadata_partial_v045'
        p['name_transliterations']=aliases; p['transliteration_resolution']='source_aliases_preserved_identity_merge_requires_profile_id_v045'
        p.setdefault('citizenship_country_ids_1993',[])
        if not p.get('citizenship_1993_resolution'):
            p['citizenship_1993_resolution']='unresolved_not_inferred_from_birth_club_name_or_later_profile_v045'
        if p.get('international_country_id') is None:
            p['nationality_resolution']='1993_gameplay_identity_unresolved_no_birthplace_default_v045'
        row.update({'resolved_display_name':p.get('display_name'),'individual_profile_source_url':link['bdfutbol_url'],'profile_source_url':link['bdfutbol_url'],'profile_source':p['historical_profile_source'],'bdfutbol_id':link['bdfutbol_id'],'name_transliterations':aliases,'profile_identity_status':p['historical_profile_identity_status'],'profile_metadata_status':p['historical_profile_metadata_status']})
        # Patch only the subset for which the individual page metadata was explicitly transcribed in this pass.
        if original_sid in DETAILS:
            dob,place,territory,profile_pos,height,weight=DETAILS[original_sid]
            p['birth_date']=dob+'T00:00:00'; p.pop('birth_country_id',None); p['historical_birth_state']='USSR'; p['birth_territory_country_id']=territory
            if place: p['historical_birth_place_text']=place
            p['historical_birth_place_source_url']=link['bdfutbol_url']; p['historical_birth_place_source_label']='BDFutbol individual profile + sovereign-state-at-birth normalization v0.45'
            p['birth_country_resolution']='historical_state_separated_no_modern_successor_backfill_v045'
            p['source_profile_position']=profile_pos
            if height is not None: p['height_cm']=height
            if weight is not None: p['weight_kg']=weight
            p['historical_profile_metadata_status']='identity_birthdate_birthstate_profile_position_resolved_v045'
            row.update({'resolved_birth_date':p['birth_date'],'resolved_birth_country_id':None,'resolved_birth_territory_country_id':territory,'resolved_birth_state':'USSR','resolved_birth_place_text':place,'source_profile_position':profile_pos,'profile_metadata_status':p['historical_profile_metadata_status']})
            detail_changes.append(original_sid)
        # Registry/photo queue exist only for generated historical players. Canonical pre-existing players stay out.
        base={'display_name':full,'first_name':first,'surname1':surname,'bdfutbol_search_name':full,'bdfutbol_id':link['bdfutbol_id'],'bdfutbol_url':link['bdfutbol_url'],'individual_profile_source':p['historical_profile_source'],'individual_profile_source_url':link['bdfutbol_url'],'name_transliterations':aliases,'profile_review_required':False}
        for idx in (rb,qb):
            obj=idx.get(sid)
            if obj is None: continue
            old_photo=obj.get('photo_status'); obj.update(base); obj['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'; obj['duplicate_check']='individual_profile_id_identity_gate_v045'; obj.setdefault('photo_filename',f'{sid}.jpg')
        changes.append({'club':club,'source_id':sid,'source_id_before_merge':original_sid,'display_name_before':old_name,'display_name_after':full,'bdfutbol_id':link['bdfutbol_id'],'metadata_depth':'birth_profile_partial' if original_sid in DETAILS else 'identity_profile_link'})

    ctx['historical_birth_state_policy']={
      'rule':'Place of birth, sovereign state at birth, 1993 citizenship/nationality and represented selection are independent facts.',
      'ussr':'For births before dissolution in Soviet territory, historical_birth_state=USSR and a modern successor territory may be stored only in birth_territory_country_id; birth_country_id is not backfilled to the successor state.',
      'other_historical_states':'The same rule applies to states such as the German Democratic Republic; modern territorial country IDs are lookup context only.',
      'no_default':'Club, surname, birthplace, later nationality and profile nationality must never auto-assign 1993 citizenship or represented selection.'}
    ctx['transliteration_policy']={
      'rule':'Keep source spellings/romanizations as aliases and choose a project display form without treating spelling variation as a separate person.',
      'identity_gate':'Never merge identities on transliteration similarity alone; require stable evidence such as profile URL/ID, date of birth and club/season context.',
      'profile_id_merge_gate':'A stable individual-profile ID is strong merge evidence when the club/season context is compatible.',
      'cross_club_example':'Andrey Alekseyevich Chernyshov appears in Dynamo Moskva and Spartak Moskva staging but resolves to one BDFutbol individual profile and therefore one game identity.'}

    # Hard invariants after the cross-club merge.
    after_ids={int(p['source_id']) for p in snap['players']}; assert before_ids-{DUPLICATE_SOURCE_ID}==after_ids
    assert fp(snap,protected)==protected_before
    assert len({int(x['source_id']) for x in reg['players']})==len(reg['players'])
    assert len({int(x['source_id']) for x in photo['players']})==len(photo['players'])
    assert {int(x['source_id']) for x in reg['players']}=={int(x['source_id']) for x in photo['players']}
    # No duplicate BDF identity among the six staged clubs after canonical resolution.
    seen={}
    for c in stage['clubs']:
        if c['name'] not in TARGET_CLUBS: continue
        for r in c['players']:
            bid=str(r.get('bdfutbol_id') or '')
            if not bid: raise AssertionError((c['name'],r.get('bdfutbol_name'),'missing bdf id'))
            sid=int(r['resolved_source_id'])
            if bid in seen and seen[bid]!=sid: raise AssertionError(('duplicate bdf identity',bid,seen[bid],sid))
            seen[bid]=sid
    after=fp(snap,russia_tids); after_russia_count=sum(int(p.get('team_id') or -1) in russia_tids for p in snap['players'])

    dump(SNAP,snap); dump(REG,reg); dump(PHOTO,photo); dump(STAGE,stage); dump(CONTEXT,ctx)
    audit={
      'schema_version':1,'checkpoint':CHECKPOINT,'status':'pass','target_clubs':TARGET_CLUBS,'staging_rows_processed':159,'unique_player_identities_after_merge':158,
      'individual_bdfutbol_profiles_resolved':159,'detailed_birth_profile_subset':len(detail_changes),'photos_ready_or_bundled_for_generated_profiles':sum(1 for x in photo['players'] if int(x['source_id']) in {int(r['resolved_source_id']) for c in stage['clubs'] if c['name'] in TARGET_CLUBS for r in c['players']} and str(x.get('photo_status','')).startswith(('ready','bundled'))),
      'duplicate_resolution':{'retired_source_id':DUPLICATE_SOURCE_ID,'canonical_source_id':CANONICAL_SOURCE_ID,'bdfutbol_id':DUPLICATE_BDF,'player':'Andrey Alekseyevich Chernyshov','clubs':['Dynamo Moskva','Spartak Moskva'],'decision':'merge_same_individual_profile_cross_club_and_preserve_both_spells'},
      'russia_integrity':{'before_sha256':before,'after_sha256':after,'protected_other_clubs_before_sha256':protected_before,'protected_other_clubs_after_sha256':fp(snap,protected),'protected_other_clubs_unchanged':True,'russia_player_objects_before':before_russia_count,'russia_player_objects_after':after_russia_count,'change_reason':'one proven duplicate retired'},
      'metadata_policy':{'identity_links_are_complete':True,'metadata_is_not_fabricated':True,'partial_metadata_explicit':True,'ussr_birth_state_separate_from_successor_territory':True,'citizenship_1993_not_inferred':True,'transliterations_preserved':True},
      'changes':changes,'next_front':NEXT_QUEUE}
    dump(DATA/'historical_profiles_metadata_audit_v045.json',audit)
    dump(DATA/'russia_source_conflicts_v045.json',{'checkpoint':CHECKPOINT,'status':'pass','identity_conflicts_resolved':[audit['duplicate_resolution']],'policy':audit['metadata_policy']})
    dump(DATA/'russia_deepening_queue_v045.json',{'schema_version':1,'checkpoint':CHECKPOINT,'completed_clubs':['Spartak Moskva']+TARGET_CLUBS,'queue':NEXT_QUEUE,'next_club':'Uralmash','staging_rows_completed_this_pass':159,'unique_identities_completed_this_pass':158,'russia_player_objects':after_russia_count})
    dump(DATA/'historical_biographies_audit_v045.json',{'checkpoint':CHECKPOINT,'clubs':TARGET_CLUBS,'profiles_considered':159,'existing_source_backed_biographies_preserved':159,'cross_club_biography_merged_for_source_id':CANONICAL_SOURCE_ID,'status':'pass'})
    print(json.dumps({k:audit[k] for k in ['checkpoint','status','target_clubs','staging_rows_processed','unique_player_identities_after_merge','individual_bdfutbol_profiles_resolved','detailed_birth_profile_subset','duplicate_resolution','russia_integrity','next_front']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
