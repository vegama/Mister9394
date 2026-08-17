from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'football9394'


def load(name: str):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def test_v036_belgium_identity_repairs_and_full_source_union():
    snap=load('historical_snapshot.json'); stage=load('belgium_1993_94_roster_staging.json')
    by={int(p['source_id']):p for p in snap['players']}
    clubs={c['name']:c for c in stage['clubs']}

    assert by[4929]['team_id']==301
    assert by[4929].get('historical_club_1994')!='FC Seraing'
    assert by[6387]['team_id']==244
    assert by[6387].get('historical_club_1994')!='Charleroi'

    assert len(clubs['FC Seraing']['players'])==21
    assert len(clubs['Charleroi']['players'])==22
    assert len(clubs['Standard Liège']['players'])==27
    assert len(clubs['RFC Liège']['players'])==24

    for sid in [9498009,9498010,9498011,9498012,9498013]:
        p=by[sid]
        club=clubs[p['historical_club_1994']]
        row=next(r for r in club['players'] if int(r.get('resolved_source_id') or -1)==sid)
        assert row['source_roster_member'] is True
        assert row['league_row_absent'] is True
        assert row['appearances']==row['starts']==row['minutes']==row['goals']==0

    for sid in [9498007,9498008]:
        row=next(r for r in clubs['Standard Liège']['players'] if int(r.get('resolved_source_id') or -1)==sid)
        assert row['source_roster_member'] is True
        assert row['league_row_absent'] is False
        assert row['appearances']==1


def test_v036_repaired_people_are_distinct_and_roles_are_source_backed():
    snap=load('historical_snapshot.json'); by={int(p['source_id']):p for p in snap['players']}

    assert by[9498005]['display_name']=='Edmilson Paulo da Silva'
    assert by[9498005]['birth_date'].startswith('1968-04-16')
    assert by[9498005]['primary_role']==16
    assert by[9498005]['team_id']==9352001

    assert by[9498006]['display_name']=='Samuel Remy'
    assert by[9498006]['birth_date'].startswith('1973-10-23')
    assert by[9498006]['primary_role']==13
    assert by[9498006]['team_id']==454

    daniel=by[9498007]; donatien=by[9496276]
    assert daniel['display_name']=='Daniel Marc Kimoni'
    assert daniel['birth_date'].startswith('1971-08-18')
    assert daniel['primary_role']==3
    assert donatien['display_name']=='Donatien Kimoni'
    assert donatien['birth_date'].startswith('1973-10-07')
    assert donatien['broad_position']=='MED'
    assert donatien['profile_position_precision']=='broad_only'
    assert daniel['source_id']!=donatien['source_id']

    duah=by[9498008]
    assert duah['display_name']=='Emmanuel Duah'
    assert duah['birth_date'].startswith('1976-11-14')
    assert duah['primary_role']==16
    assert duah['height_cm']==177 and duah['weight_kg']==74


def test_v036_belgium_gap_reduction_and_registry_integrity():
    audit=load('historical_profiles_metadata_audit_v036.json')
    before=audit['profile_gaps_before']['Belgium']; after=audit['profile_gaps_after']['Belgium']
    assert before['active_players']==406
    assert after['active_players']==413
    assert after['missing_birth_date']<=275 < before['missing_birth_date']
    assert after['missing_international_country_id']<=248 < before['missing_international_country_id']
    assert audit['profiles']['curated_this_batch']==71
    assert audit['profiles']['new_historical_identities']==9
    assert len(audit['identity_repairs'])==2
    assert audit['source_roster_union']['club_stage_counts_after']=={'FC Seraing':21,'Charleroi':22,'Standard Liège':27,'RFC Liège':24}

    reg=load('created_players_registry.json'); queue=load('bdfutbol_photo_queue.json')
    rids=[int(x['source_id']) for x in reg['players']]; qids=[int(x['source_id']) for x in queue['players']]
    assert len(rids)==len(set(rids))
    assert len(qids)==len(set(qids))
    assert set(rids)==set(qids)
    for sid in range(9498005,9498014):
        assert sid in set(rids)


def test_v036_no_active_duplicate_name_and_birthdate_collision_in_belgium():
    snap=load('historical_snapshot.json')
    belgium_team_ids={int(t['source_id']) for t in snap['teams'] if t.get('league_id')==930052}
    active=[p for p in snap['players'] if p.get('team_id') in belgium_team_ids]
    keys=[]
    for p in active:
        if p.get('birth_date'):
            keys.append(((p.get('display_name') or '').casefold(),str(p['birth_date'])[:10]))
    dup=[k for k,v in Counter(keys).items() if v>1]
    assert not dup


def test_v036_source_only_members_have_honest_biographies():
    snap=load('historical_snapshot.json'); by={int(p['source_id']):p for p in snap['players']}
    for sid in [9498009,9498010,9498011,9498012,9498013]:
        bio=by[sid]['historical_biography_1993_94']
        assert 'no se inventan minutos ni apariciones' in bio
        assert '0 partidos' not in bio
