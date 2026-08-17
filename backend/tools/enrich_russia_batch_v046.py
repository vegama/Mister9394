from __future__ import annotations

from pathlib import Path
from typing import Any
import copy, hashlib, json

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'
SNAP=DATA/'historical_snapshot.json'; REG=DATA/'created_players_registry.json'; PHOTO=DATA/'bdfutbol_photo_queue.json'
STAGE=DATA/'russia_1993_roster_staging.json'; LINKS=DATA/'russia_profile_links_v046.json'; CONTEXT=DATA/'country_context_1993.json'
CHECKPOINT='0.46.0-russia-uralmash-asmaral-batch-deep'; RUSSIA_LEAGUE_ID=930015
EXPECTED_BEFORE='731ae8da21ba76f6b73182adcec485f53bce47989481a81552774d358d3d39b1'
TARGET_CLUBS=['Uralmash','CSKA Moskva','KAMAZ','Zhemchuzhina Sochi','Dynamo Stavropol','Lokomotiv Nizhny Novgorod','Krylia Sovetov','Luch Vladivostok','Okean Nakhodka','Rostselmash','Asmaral Moskva']
NEXT_QUEUE=[]

def load(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def dump(p:Path,x:Any): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fp(snap:dict[str,Any], team_ids:set[int])->str:
    payload={'teams':sorted([x for x in snap['teams'] if int(x.get('source_id') or -1) in team_ids],key=lambda x:int(x['source_id'])),
             'players':sorted([x for x in snap['players'] if int(x.get('team_id') or -1) in team_ids],key=lambda x:int(x['source_id']))}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def split_name(name:str, squad_name:str)->tuple[str|None,str]:
    normalized=squad_name.strip(); words=name.split(); idx=-1
    for i,w in enumerate(words):
        if w.casefold().rstrip('.')==normalized.casefold().rstrip('.'): idx=i
    if idx>=0: return (' '.join(words[:idx]) or None),words[idx]
    if name.endswith(' Jr.') and len(words)>=3: return ' '.join(words[:-2]),words[-2]
    return (' '.join(words[:-1]) or None,words[-1])

def add_unique_spell(existing:list[dict[str,Any]]|None, spell:dict[str,Any])->list[dict[str,Any]]:
    out=copy.deepcopy(existing or []); key=(spell.get('club'),spell.get('team_id'))
    for i,x in enumerate(out):
        if (x.get('club'),x.get('team_id'))==key: out[i]=spell; break
    else: out.append(spell)
    return out

def main()->None:
    snap=load(SNAP); reg=load(REG); photo=load(PHOTO); stage=load(STAGE); links=load(LINKS); ctx=load(CONTEXT)
    teams_by_name={t['name']:int(t['source_id']) for t in snap['teams']}
    russia_tids={int(t['source_id']) for t in snap['teams'] if int(t.get('league_id') or -1)==RUSSIA_LEAGUE_ID}
    before=fp(snap,russia_tids); assert before==EXPECTED_BEFORE,(before,EXPECTED_BEFORE)
    target_tids={teams_by_name[x] for x in TARGET_CLUBS}
    rows_by_original={}
    for c in stage['clubs']:
        if c['name'] not in TARGET_CLUBS: continue
        for r in c['players']:
            rows_by_original[int(r['resolved_source_id'])]=(c['name'],r)
    assert len(rows_by_original)==300
    assert len(links['players'])==300
    link_by_original={int(x['source_id']):x for x in links['players']}
    assert set(link_by_original)==set(rows_by_original)

    by={int(p['source_id']):p for p in snap['players']}
    rb={int(p['source_id']):p for p in reg['players']}; qb={int(p['source_id']):p for p in photo['players']}
    target_source_ids=set(link_by_original)

    # Stable individual profile IDs are the identity gate. Existing already-deepened identities win;
    # otherwise the first row in the explicit batch order becomes canonical. Name similarity alone never merges.
    existing_by_bid:dict[str,list[int]]={}
    for p in snap['players']:
        sid=int(p['source_id']); bid=str(p.get('bdfutbol_id') or '')
        if bid and sid not in target_source_ids: existing_by_bid.setdefault(bid,[]).append(sid)
    grouped:dict[str,list[int]]={}
    for link in links['players']: grouped.setdefault(str(link['bdfutbol_id']),[]).append(int(link['source_id']))

    canonical_for:dict[int,int]={}; merge_groups=[]
    for bid,sids in grouped.items():
        existing=existing_by_bid.get(bid,[])
        assert len(existing)<=1,('ambiguous pre-existing BDF identity',bid,existing)
        canonical=existing[0] if existing else sids[0]
        for sid in sids: canonical_for[sid]=canonical
        retired=[sid for sid in sids if sid!=canonical]
        if retired:
            merge_groups.append({'bdfutbol_id':bid,'canonical_source_id':canonical,'retired_source_ids':retired,'target_source_ids':sids,'preexisting_canonical':bool(existing)})

    retired={sid for g in merge_groups for sid in g['retired_source_ids']}
    canonical_touched={g['canonical_source_id'] for g in merge_groups}
    # Protect every Russian object not targeted and not deliberately touched as a cross-batch canonical identity.
    protected_player_ids={int(p['source_id']) for p in snap['players'] if int(p.get('team_id') or -1) in russia_tids and int(p['source_id']) not in target_source_ids and int(p['source_id']) not in canonical_touched}
    protected_before={sid:copy.deepcopy(by[sid]) for sid in protected_player_ids}

    # Retire proven duplicate source objects, but first attach all historical club spells to the canonical identity.
    for original_sid,link in link_by_original.items():
        canonical_sid=canonical_for[original_sid]; club,row=rows_by_original[original_sid]; canonical=by[canonical_sid]
        spell={'club':club,'team_id':teams_by_name[club],'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
        canonical['historical_club_spells_1993_94']=add_unique_spell(canonical.get('historical_club_spells_1993_94'),spell)
        row['resolved_source_id']=canonical_sid
        if original_sid!=canonical_sid:
            row['identity_resolution']='merged_same_bdfutbol_individual_profile_v046'; row['duplicate_source_id_retired']=original_sid
            hist=list(canonical.get('identity_merge_history') or [])
            event={'checkpoint':CHECKPOINT,'merged_source_id':original_sid,'reason':'same BDFutbol individual profile ID in compatible 1993-94 roster context','bdfutbol_id':str(link['bdfutbol_id']),'club':club}
            if not any(x.get('checkpoint')==CHECKPOINT and int(x.get('merged_source_id') or -1)==original_sid for x in hist): hist.append(event)
            canonical['identity_merge_history']=hist
            canonical['duplicate_resolution']='stable_individual_profile_id_merge_v046'

    if retired:
        snap['players']=[p for p in snap['players'] if int(p['source_id']) not in retired]
        reg['players']=[p for p in reg['players'] if int(p['source_id']) not in retired]
        photo['players']=[p for p in photo['players'] if int(p['source_id']) not in retired]
    by={int(p['source_id']):p for p in snap['players']}; rb={int(p['source_id']):p for p in reg['players']}; qb={int(p['source_id']):p for p in photo['players']}

    changes=[]; processed_canonical=set()
    for link in links['players']:
        original_sid=int(link['source_id']); sid=canonical_for[original_sid]; club,row=rows_by_original[original_sid]; p=by[sid]
        full=link['full_name']; old_name=p.get('display_name'); first,surname=split_name(full,str(row.get('bdfutbol_name') or ''))
        aliases=dict(p.get('name_transliterations') or {})
        aliases.setdefault('bdfutbol_squad',row.get('bdfutbol_name')); aliases.setdefault('project_display_before_v046',old_name)
        aliases['bdfutbol_profile']=full
        # Preserve an already-deepened canonical display from another batch; new target canonicals use the profile form.
        is_preexisting=sid not in target_source_ids
        if not is_preexisting and sid not in processed_canonical:
            p['display_name']=full; p['first_name']=first; p['surname1']=surname
        elif is_preexisting:
            aliases['project_display_preserved_v046']=p.get('display_name')
        p['bdfutbol_id']=str(link['bdfutbol_id']); p['bdfutbol_url']=link['bdfutbol_url']
        p['historical_profile_source']='BDFutbol individual profile + Russia batch identity review v0.46'
        p['historical_profile_source_url']=link['bdfutbol_url']; p['historical_profile_identity_status']='bdfutbol_individual_profile_resolved_v046'
        if not p.get('historical_profile_metadata_status'):
            p['historical_profile_metadata_status']='preexisting_resolved_metadata_preserved_v046' if is_preexisting and (p.get('birth_date') or p.get('source_profile_position')) else 'identity_resolved_metadata_unreviewed_v046'
        p['name_transliterations']=aliases; p['transliteration_resolution']='source_aliases_preserved_profile_id_identity_gate_v046'
        p.setdefault('citizenship_country_ids_1993',[])
        p.setdefault('citizenship_1993_resolution','unresolved_not_inferred_from_birth_club_name_or_later_profile_v046')
        if p.get('international_country_id') is None: p['nationality_resolution']='1993_gameplay_identity_unresolved_no_birthplace_default_v046'
        row.update({'resolved_display_name':p.get('display_name'),'individual_profile_source_url':link['bdfutbol_url'],'profile_source_url':link['bdfutbol_url'],'profile_source':p['historical_profile_source'],'bdfutbol_id':str(link['bdfutbol_id']),'name_transliterations':aliases,'profile_identity_status':p['historical_profile_identity_status'],'profile_metadata_status':p.get('historical_profile_metadata_status')})
        # Keep a club-specific biography evidence item, without fabricating biographical facts not present in staging.
        bios=list(p.get('historical_biographies_1993_94') or [])
        if not any(x.get('club')==club for x in bios):
            evidence={'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
            bios.append({'club':club,'text':f"{p.get('display_name')} figura en la plantilla histórica 1993-94 de {club}.",'source_url':link['squad_url'],'profile_url':link['bdfutbol_url'],'evidence':evidence})
        p['historical_biographies_1993_94']=bios
        p['historical_biography_staged_clubs']=sorted(set((p.get('historical_biography_staged_clubs') or [])+[club]))
        base={'display_name':p.get('display_name'),'first_name':p.get('first_name'),'surname1':p.get('surname1'),'bdfutbol_search_name':full,'bdfutbol_id':str(link['bdfutbol_id']),'bdfutbol_url':link['bdfutbol_url'],'individual_profile_source':p['historical_profile_source'],'individual_profile_source_url':link['bdfutbol_url'],'name_transliterations':aliases,'profile_review_required':False}
        for idx in (rb,qb):
            obj=idx.get(sid)
            if obj is None: continue
            old_photo=obj.get('photo_status'); obj.update(base); obj['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'; obj['duplicate_check']='individual_profile_id_identity_gate_v046'; obj.setdefault('photo_filename',f'{sid}.jpg')
        changes.append({'club':club,'source_id_before_merge':original_sid,'resolved_source_id':sid,'display_name_before':old_name,'display_name_after':p.get('display_name'),'bdfutbol_id':str(link['bdfutbol_id']),'merged':original_sid!=sid})
        processed_canonical.add(sid)

    ctx['historical_birth_state_policy']={
      'rule':'Place of birth, sovereign state at birth, 1993 citizenship/nationality and represented selection are independent facts.',
      'ussr':'For births before dissolution in Soviet territory, historical_birth_state=USSR and a modern successor territory may be stored only in birth_territory_country_id; birth_country_id is not backfilled to the successor state.',
      'other_historical_states':'The same rule applies to states such as the German Democratic Republic; modern territorial country IDs are lookup context only.',
      'no_default':'Club, surname, birthplace, later nationality and profile nationality must never auto-assign 1993 citizenship or represented selection.'}
    ctx['transliteration_policy']={
      'rule':'Keep source spellings/romanizations as aliases and choose a project display form without treating spelling variation as a separate person.',
      'identity_gate':'Never merge identities on transliteration similarity alone; require stable evidence such as individual profile ID plus compatible club/season context.',
      'profile_id_merge_gate':'A stable individual-profile ID is strong merge evidence when the historical club/season context is compatible.',
      'cross_club_example':'Andrey Alekseyevich Chernyshov appears in Dynamo Moskva and Spartak Moskva staging but resolves to one BDFutbol individual profile and therefore one game identity.'}

    # Regression gates.
    assert len(retired)==11,(len(retired),sorted(retired))
    assert len(set(canonical_for.values()))==294
    assert len({int(x['source_id']) for x in reg['players']})==len(reg['players'])
    assert len({int(x['source_id']) for x in photo['players']})==len(photo['players'])
    assert {int(x['source_id']) for x in reg['players']}=={int(x['source_id']) for x in photo['players']}
    for sid,before_obj in protected_before.items(): assert by[sid]==before_obj,('protected Russian identity changed',sid)
    seen={}
    for original_sid,link in link_by_original.items():
        bid=str(link['bdfutbol_id']); sid=canonical_for[original_sid]
        if bid in seen: assert seen[bid]==sid,('duplicate bdf identity',bid,seen[bid],sid)
        seen[bid]=sid
    before_russia_count=491; after_russia_count=sum(int(p.get('team_id') or -1) in russia_tids for p in snap['players'])
    after=fp(snap,russia_tids)

    dump(SNAP,snap); dump(REG,reg); dump(PHOTO,photo); dump(STAGE,stage); dump(CONTEXT,ctx)
    audit={'schema_version':1,'checkpoint':CHECKPOINT,'status':'pass','target_clubs':TARGET_CLUBS,'staging_rows_processed':300,'unique_player_identities_after_merge':294,'target_player_objects_after_retirement':289,'individual_bdfutbol_profiles_resolved':300,'identity_rows_retired':len(retired),'merge_groups':merge_groups,'russia_integrity':{'before_sha256':before,'after_sha256':after,'russia_player_objects_before':before_russia_count,'russia_player_objects_after':after_russia_count,'protected_non_target_noncanonical_players_unchanged':True},'metadata_policy':{'identity_links_are_complete':True,'metadata_is_not_fabricated':True,'ussr_birth_state_separate_from_successor_territory':True,'citizenship_1993_not_inferred':True,'transliterations_preserved':True,'stable_profile_id_is_merge_gate':True},'changes':changes,'next_front':NEXT_QUEUE}
    dump(DATA/'historical_profiles_metadata_audit_v046.json',audit)
    dump(DATA/'russia_source_conflicts_v046.json',{'checkpoint':CHECKPOINT,'status':'pass','merge_groups':merge_groups,'retired_source_ids':sorted(retired),'policy':audit['metadata_policy']})
    dump(DATA/'russia_deepening_queue_v046.json',{'schema_version':1,'checkpoint':CHECKPOINT,'completed_clubs':['Spartak Moskva','Rotor Volgograd','Dynamo Moskva','Tekstilshchik Kamyshin','Lokomotiv Moskva','Spartak Vladikavkaz','Torpedo Moskva']+TARGET_CLUBS,'queue':[],'next_club':None,'staging_rows_completed_this_pass':300,'unique_identities_completed_this_pass':294,'target_player_objects_after_retirement':289,'russia_player_objects':after_russia_count,'league_club_batch_complete':True})
    dump(DATA/'historical_biographies_audit_v046.json',{'checkpoint':CHECKPOINT,'clubs':TARGET_CLUBS,'profiles_considered':300,'club_spell_evidence_preserved':300,'status':'pass'})
    print(json.dumps({'checkpoint':CHECKPOINT,'status':'pass','rows':300,'unique_identities':294,'target_player_objects_after_retirement':289,'retired':len(retired),'merge_groups':merge_groups,'russia_before':before_russia_count,'russia_after':after_russia_count,'after_sha256':after},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
