from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'football9394'
TARGET=['Uralmash','CSKA Moskva','KAMAZ','Zhemchuzhina Sochi','Dynamo Stavropol','Lokomotiv Nizhny Novgorod','Krylia Sovetov','Luch Vladivostok','Okean Nakhodka','Rostselmash','Asmaral Moskva']
PRE_V046='731ae8da21ba76f6b73182adcec485f53bce47989481a81552774d358d3d39b1'
EXPECTED={'Uralmash':25,'CSKA Moskva':29,'KAMAZ':29,'Zhemchuzhina Sochi':27,'Dynamo Stavropol':28,'Lokomotiv Nizhny Novgorod':23,'Krylia Sovetov':26,'Luch Vladivostok':24,'Okean Nakhodka':27,'Rostselmash':29,'Asmaral Moskva':33}

def load(name:str): return json.loads((DATA/name).read_text(encoding='utf-8'))

def test_v046_closes_remaining_eleven_russian_clubs_and_all_300_rows():
    a=load('historical_profiles_metadata_audit_v046.json')
    assert a['status']=='pass'; assert a['target_clubs']==TARGET
    assert a['staging_rows_processed']==300; assert a['individual_bdfutbol_profiles_resolved']==300
    assert a['unique_player_identities_after_merge']==294
    assert a['target_player_objects_after_retirement']==289
    assert a['identity_rows_retired']==11
    assert a['russia_integrity']['before_sha256']==PRE_V046
    assert a['russia_integrity']['russia_player_objects_before']==491
    assert a['russia_integrity']['russia_player_objects_after']==480
    assert a['russia_integrity']['protected_non_target_noncanonical_players_unchanged'] is True

    stage=load('russia_1993_roster_staging.json'); clubs={c['name']:c for c in stage['clubs']}
    assert sum(EXPECTED.values())==300
    for name,n in EXPECTED.items():
        rows=clubs[name]['players']; assert len(rows)==n
        assert all(r.get('bdfutbol_id') for r in rows)
        assert all(r.get('individual_profile_source_url') for r in rows)
        assert all(r.get('profile_identity_status')=='bdfutbol_individual_profile_resolved_v046' for r in rows)

def test_v046_uses_profile_ids_to_merge_six_in_batch_duplicates_and_five_preexisting_identities():
    a=load('historical_profiles_metadata_audit_v046.json')
    groups=a['merge_groups']; assert len(groups)==11
    assert sum(len(x['retired_source_ids']) for x in groups)==11
    assert sum(1 for x in groups if x['preexisting_canonical'])==5
    assert sum(1 for x in groups if not x['preexisting_canonical'])==6
    assert {x['bdfutbol_id'] for x in groups}=={'591588','591077','590748','63255','1180233','1179603','6512','1181061','591008','610593','701741'}

    snap=load('historical_snapshot.json'); by={int(x['source_id']):x for x in snap['players']}
    for g in groups:
        canonical=by[int(g['canonical_source_id'])]
        assert canonical['bdfutbol_id']==g['bdfutbol_id']
        assert canonical['duplicate_resolution']=='stable_individual_profile_id_merge_v046'
        for sid in g['retired_source_ids']:
            assert int(sid) not in by
            assert any(int(x.get('merged_source_id') or -1)==int(sid) for x in canonical['identity_merge_history'])

def test_v046_preserves_every_roster_spell_after_identity_consolidation():
    stage=load('russia_1993_roster_staging.json'); snap=load('historical_snapshot.json'); by={int(x['source_id']):x for x in snap['players']}
    for c in stage['clubs']:
        if c['name'] not in TARGET: continue
        for row in c['players']:
            p=by[int(row['resolved_source_id'])]
            assert any(x.get('club')==c['name'] for x in p.get('historical_club_spells_1993_94',[]))
            assert c['name'] in p.get('historical_biography_staged_clubs',[])

def test_v046_profile_id_uniqueness_is_global_within_the_batch_not_name_based():
    stage=load('russia_1993_roster_staging.json'); seen={}
    for c in stage['clubs']:
        if c['name'] not in TARGET: continue
        for row in c['players']:
            bid=row['bdfutbol_id']; sid=int(row['resolved_source_id'])
            assert bid not in seen or seen[bid]==sid
            seen[bid]=sid
    assert len(seen)==294

    # Six duplicated profile IDs inside the batch resolve to exactly one canonical identity each.
    for bid in ['590748','1179603','6512','1181061','591008','610593']:
        resolved=set()
        for c in stage['clubs']:
            if c['name'] in TARGET:
                resolved.update(int(r['resolved_source_id']) for r in c['players'] if r.get('bdfutbol_id')==bid)
        assert len(resolved)==1

def test_v046_does_not_backfill_1993_citizenship_from_russian_club_or_ussr_context():
    snap=load('historical_snapshot.json'); by={int(x['source_id']):x for x in snap['players']}
    stage=load('russia_1993_roster_staging.json')
    checked=0
    for c in stage['clubs']:
        if c['name'] not in TARGET: continue
        for row in c['players']:
            p=by[int(row['resolved_source_id'])]
            assert 'name_transliterations' in p
            assert p.get('citizenship_country_ids_1993',[])==[] or p.get('citizenship_1993_resolution') is not None
            checked+=1
    assert checked==300
    ctx=load('country_context_1993.json')
    assert 'never auto-assign 1993 citizenship' in ctx['historical_birth_state_policy']['no_default']
    assert 'Never merge identities on transliteration similarity alone' in ctx['transliteration_policy']['identity_gate']

def test_v046_registry_photo_queue_remain_synchronized_and_retired_ids_are_gone():
    reg=load('created_players_registry.json')['players']; q=load('bdfutbol_photo_queue.json')['players']
    rb={int(x['source_id']):x for x in reg if not x.get('retired_alias_v113')}; qb={int(x['source_id']):x for x in q}
    assert len({int(x['source_id']) for x in reg})==len(reg); assert len(qb)==len(q); assert set(rb)==set(qb)
    retired=set(load('russia_source_conflicts_v046.json')['retired_source_ids'])
    assert retired.isdisjoint(rb); assert retired.isdisjoint(qb)

def test_v046_russian_league_club_queue_is_complete():
    q=load('russia_deepening_queue_v046.json')
    assert q['league_club_batch_complete'] is True
    assert q['queue']==[]; assert q['next_club'] is None
    assert len(q['completed_clubs'])==18
    assert set(q['completed_clubs'])=={'Spartak Moskva','Rotor Volgograd','Dynamo Moskva','Tekstilshchik Kamyshin','Lokomotiv Moskva','Spartak Vladikavkaz','Torpedo Moskva',*TARGET}
    assert q['staging_rows_completed_this_pass']==300
    assert q['unique_identities_completed_this_pass']==294
