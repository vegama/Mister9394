import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SNAP=ROOT/'data/football9394/historical_snapshot.json'
REVIEW=ROOT/'data/football9394/created_player_profile_reviews.json'
REG=ROOT/'data/football9394/created_players_registry.json'
AUDIT=ROOT/'docs/v024_created_player_profile_audit.json'
FULL=ROOT/'docs/v023_full_mdb_created_reconciliation.json'
ATTRS=("pace","acceleration","jumping","stamina","strength","tackling","work_rate","aggression","anticipation","marking","discipline","positioning","leadership","consistency","vision","short_pass","long_pass","dribbling","finishing","heading","off_ball","shot_power","free_kicks","penalties","technique")

def load(path): return json.loads(path.read_text(encoding='utf-8'))

def test_all_created_players_have_fixed_reviewed_profiles_and_no_clones():
    snap=load(SNAP)
    created=[p for p in snap['players'] if p.get('external_origin') in {'world_cup_1994','national_pool_1993_94'}]
    assert len(created)>=367
    assert all(str(p.get('attribute_source') or '').startswith('fixed_source_comparable_') for p in created)
    pending={int(p['source_id']) for p in created if p.get('profile_review_required')}
    assert {9495331,9495336,9495337,9495342} <= pending
    vectors=[tuple(p['attributes'][k] for k in ATTRS) for p in created]
    assert len(set(vectors))==len(created)
    assert all(all(20<=p['attributes'][k]<=99 for k in ATTRS) for p in created)

def test_review_comparables_are_source_backed_same_position():
    snap=load(SNAP); byid={int(p['source_id']):p for p in snap['players']}
    created=[p for p in snap['players'] if p.get('external_origin')]
    for p in created:
        current_ids=p.get('attribute_comparable_source_ids')
        if current_ids:
            sources=[byid[int(sid)] for sid in current_ids]
            assert all(not src.get('external_origin') for src in sources)
            assert all(src['broad_position']==p['broad_position'] for src in sources)
        else:
            review=p['profile_review_0_23']
            for key in ('primary_comparable','secondary_comparable'):
                c=review[key]; src=byid[int(c['source_id'])]
                assert not src.get('external_origin')
                assert src['broad_position']==p['broad_position']
            assert review['policy'].startswith('fixed data curation')

def test_original_players_are_not_rewritten_by_profile_review():
    audit=load(AUDIT)
    assert audit['counts']['source_backed_original_players']==10528
    assert audit['counts']['created_players_reviewed']>=367
    assert audit['counts']['pending_profile_reviews']==0
    assert audit['counts']['old_duplicate_vector_groups']>=0
    assert audit['counts']['new_duplicate_vector_groups']==0
    assert audit['original_player_hash_changes']==[]
    assert audit['policy']['new_universal_rating_rule'] is False
    assert audit['policy']['runtime_formula_added'] is False

def test_high_profile_baseline_errors_are_corrected_explicitly():
    snap=load(SNAP); byname={p['display_name']:p for p in snap['players'] if p.get('external_origin')}
    expected={
        'Andrés Escobar':81,'Leonel Álvarez':80,'Ilie Dumitrescu':82,
        'Hong Myung-bo':78,'Dimitris Saravakos':80,'Emmanuel Amunike':81,
        'Daniel Amokachi':81,'Saeed Al-Owairan':75,'Borislav Mihaylov':79,
        'Trifon Ivanov':80,'Marc Degryse':81,
    }
    for name,overall in expected.items(): assert byname[name]['overall']==overall

def test_created_player_registry_and_photo_queue_remain_stable():
    reg=load(REG)['players']
    assert len(reg)>=367
    created=[r for r in reg if r.get('creation_batch') and not r.get('retired_alias_v113')]
    assert all(str(r.get('attribute_source') or '').startswith('fixed_source_comparable_') for r in created)
    pending={int(r['source_id']) for r in reg if r.get('profile_review_required')}
    assert {9495331,9495336,9495337,9495342,9496404,9496406,9496434,9496447,9496448,9496449,9496452,9496455,9496457,9496467,9496469,9497236,9497251,9497254,9497255,9497261,9497266,9497275,9497276,9497277,9497279,9497282,9497289,9497290,9497291,9497518,9497522,9498002} <= pending
    assert all(int(r['overall'])>0 for r in created)
    queue=load(ROOT/'data/football9394/bdfutbol_photo_queue.json')['players']
    active=[r for r in reg if not r.get('retired_alias_v113')]
    assert len(queue)==len(active)
    assert {int(r['source_id']) for r in queue}=={int(r['source_id']) for r in active}

def test_popov_remains_single_existing_identity_not_a_created_player():
    snap=load(SNAP)
    # Stable identity is source_id=515. Later historical deepening may expand the
    # display form from 'Popov' to the full BDFutbol profile name.
    matches=[p for p in snap['players'] if int(p.get('source_id') or 0)==515]
    assert len(matches)==1
    assert matches[0]['display_name'] in {'Popov','Dmitri Popov','Dmitri Lvovich Popov'}
    assert not matches[0].get('external_origin')
    assert str(matches[0]['birth_date']).startswith('1967-02-27')

def test_full_mdb_crosscheck_is_documented_not_used_as_1993_rating_source():
    full=load(FULL)
    assert full['source_players']==37312
    assert full['created']==367
    assert full['matched']==9
    assert full['ambiguous']==2
    assert full['missing']==356
    # The matches are records in later source editions, so the 0.23 audit must
    # never claim those modern magnitudes as historical 1993-94 attributes.
    assert all((not r.get('matched_id')) or r['candidates'][0].get('league_edition') in {'2016','2017'} for r in full['results'])
