from __future__ import annotations

from pathlib import Path
import json
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'football9394'
SNAP = DATA / 'historical_snapshot.json'
STAGE_PATHS = {
    'Belgium': DATA / 'belgium_1993_94_roster_staging.json',
    'Turkey': DATA / 'turkey_1993_94_roster_staging.json',
    'Russia': DATA / 'russia_1993_roster_staging.json',
    'Greece': DATA / 'greece_1993_94_roster_staging.json',
}

ROLE_ES = {
    0: 'Portero', 1: 'Lateral derecho', 2: 'Lateral izquierdo', 3: 'Defensa central',
    4: 'Defensa central', 5: 'Líbero', 6: 'Mediocentro defensivo', 7: 'Centrocampista',
    8: 'Mediapunta', 9: 'Interior derecho', 10: 'Interior derecho', 11: 'Extremo derecho',
    12: 'Extremo derecho', 13: 'Interior izquierdo', 14: 'Interior izquierdo',
    15: 'Extremo izquierdo', 16: 'Extremo izquierdo', 17: 'Delantero centro',
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def stage_source(club: dict[str, Any], row: dict[str, Any]) -> tuple[str | None, str | None]:
    url = (
        row.get('profile_source_url')
        or row.get('individual_profile_source_url')
        or club.get('bdfutbol_squad_url')
        or club.get('rsssf_roster_url')
        or row.get('source_url')
    )
    if row.get('profile_source'):
        label = str(row['profile_source'])
    elif club.get('bdfutbol_squad_url'):
        label = 'BDFutbol — plantilla y estadísticas 1993-94'
    elif club.get('rsssf_roster_url'):
        label = 'RSSSF — plantilla y estadísticas 1993-94'
    else:
        label = 'staging histórico 1993-94'
    return url, label


def fmt_num(value: int) -> str:
    return f'{value:,}'.replace(',', '.')


def biography(player: dict[str, Any], team_name: str, row: dict[str, Any]) -> str:
    role = ROLE_ES.get(int(player.get('primary_role') or 0), 'Futbolista')
    parts = [f'{role} de {team_name} en la temporada 1993-94.']
    apps = row.get('appearances')
    starts = row.get('starts')
    minutes = row.get('minutes')
    goals = row.get('goals')
    stats = []
    if isinstance(apps, int) and apps >= 0:
        stats.append(f'{apps} partidos')
    if isinstance(starts, int) and starts >= 0:
        stats.append(f'{starts} como titular')
    if isinstance(minutes, int) and minutes >= 0:
        stats.append(f'{fmt_num(minutes)} minutos')
    if stats:
        parts.append('En el registro histórico figura con ' + ', '.join(stats) + '.')
    if int(player.get('primary_role') or 0) != 0 and isinstance(goals, int) and goals >= 0:
        parts.append(f'Marcó {goals} gol' + ('' if goals == 1 else 'es') + '.')
    bd = player.get('birth_date')
    if bd:
        try:
            y, m, d = str(bd)[:10].split('-')
            parts.append(f'Fecha de nacimiento registrada: {d}/{m}/{y}.')
        except ValueError:
            pass
    return ' '.join(parts)


def main() -> None:
    snap = load(SNAP)
    by_player = {int(p['source_id']): p for p in snap['players']}
    by_team = {int(t['source_id']): t for t in snap['teams']}

    # For identities that appear for two clubs during the same season, prefer the row
    # matching the player's opening/current reconstructed club when possible; otherwise
    # retain the first verified staging row and record all staged clubs as evidence.
    staged: dict[int, list[tuple[str, dict[str, Any], dict[str, Any]]]] = {}
    for country, path in STAGE_PATHS.items():
        stage = load(path)
        for club in stage.get('clubs', []):
            for row in club.get('players', []):
                sid = row.get('resolved_source_id')
                if sid is not None:
                    staged.setdefault(int(sid), []).append((country, club, row))

    active_team_ids = {
        int(t['source_id']) for t in snap['teams']
        if int(t.get('league_id') or -1) in {930015, 930047, 930052, 930057}
    }
    active_players = [p for p in snap['players'] if p.get('team_id') in active_team_ids]
    rows_written = 0
    with_stats = 0
    source_backed = 0
    multi_club = 0
    missing_stage = []

    for p in active_players:
        sid = int(p['source_id'])
        candidates = staged.get(sid, [])
        if not candidates:
            missing_stage.append(sid)
            continue
        team = by_team[int(p['team_id'])]
        team_name = str(team['name'])
        # Exact team-name matching is deliberately conservative; aliases vary across sources.
        chosen = candidates[0]
        for cand in candidates:
            club_name = str(cand[1].get('name') or '')
            if club_name.casefold() == team_name.casefold():
                chosen = cand
                break
        country, club, row = chosen
        url, label = stage_source(club, row)
        p['historical_biography_1993_94'] = biography(p, team_name, row)
        p['historical_biography_source_url'] = url
        p['historical_biography_source_label'] = label
        p['historical_biography_evidence'] = {
            'season': '1993-94' if country != 'Russia' else '1993',
            'club': team_name,
            'appearances': row.get('appearances'),
            'starts': row.get('starts'),
            'minutes': row.get('minutes'),
            'goals': row.get('goals'),
            'staging_name': row.get('bdfutbol_name') or row.get('rsssf_name') or row.get('resolved_display_name'),
        }
        p['historical_biography_status'] = 'source_backed_season_summary'
        p['historical_biography_staged_clubs'] = [str(c[1].get('name')) for c in candidates]
        rows_written += 1
        if any(isinstance(row.get(k), int) for k in ('appearances', 'starts', 'minutes', 'goals')):
            with_stats += 1
        if url:
            source_backed += 1
        if len(candidates) > 1:
            multi_club += 1

    if missing_stage:
        raise RuntimeError(f'active reconstructed players missing staging rows: {missing_stage[:12]} total={len(missing_stage)}')
    if rows_written != len(active_players):
        raise RuntimeError(f'biography coverage mismatch {rows_written}/{len(active_players)}')

    audit = {
        'schema_version': 1,
        'checkpoint': '0.31.0-profiles-venues-referees-roster-hygiene',
        'status': 'pass',
        'active_reconstructed_players': len(active_players),
        'biographies_written': rows_written,
        'biographies_with_season_stats': with_stats,
        'biographies_with_source_url': source_backed,
        'multi_club_identity_rows': multi_club,
        'policy': 'Biographies only summarize verified staging/season data and already sourced profile facts; missing nationality or specialist-role facts are not inferred.',
    }
    dump(SNAP, snap)
    dump(DATA / 'historical_biographies_audit_v031.json', audit)
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
