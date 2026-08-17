from __future__ import annotations

from pathlib import Path
import json
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'football9394'
SNAP = DATA / 'historical_snapshot.json'
REGISTRY = DATA / 'created_players_registry.json'
QUEUE = DATA / 'bdfutbol_photo_queue.json'
PHOTO_DIR = ROOT / 'frontend' / 'public' / 'historical9394' / 'players'
STAGE_PATHS = {
    'Belgium': DATA / 'belgium_1993_94_roster_staging.json',
    'Turkey': DATA / 'turkey_1993_94_roster_staging.json',
    'Russia': DATA / 'russia_1993_roster_staging.json',
    'Greece': DATA / 'greece_1993_94_roster_staging.json',
}
LEAGUES = {930015, 930047, 930052, 930057}
ROLE_ES = {
    0: 'Portero', 1: 'Lateral derecho', 2: 'Lateral izquierdo', 3: 'Defensa central',
    4: 'Defensa central', 5: 'Líbero', 6: 'Mediocentro defensivo', 7: 'Centrocampista',
    8: 'Mediapunta', 9: 'Interior derecho', 10: 'Interior derecho', 11: 'Extremo derecho',
    12: 'Extremo derecho', 13: 'Interior izquierdo', 14: 'Interior izquierdo',
    15: 'Extremo izquierdo', 16: 'Extremo izquierdo', 17: 'Delantero centro',
}

PHOTO_PATCHES = {
    9498004: {
        'display_name': 'Fevzi Açıkgöz', 'bdfutbol_id': '1175393',
        'profile_url': 'https://www.bdfutbol.com/en/j/j1175393.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/1175393.jpg?v=1780345596',
        'birth_place_text': 'Kocaeli (Kocaeli)', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': None, 'weight_kg': None,
    },
    9496437: {
        'display_name': 'Ergün Penbe', 'bdfutbol_id': '46413',
        'profile_url': 'https://www.bdfutbol.com/en/j/j46413.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/46413.jpg?v=1661960741',
        'birth_place_text': 'Zonguldak', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': None, 'weight_kg': None,
    },
    9496438: {
        'display_name': 'Rahim Zafer', 'bdfutbol_id': '57628',
        'profile_url': 'https://www.bdfutbol.com/en/j/j57628.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/57628.jpg?v=1689432994',
        'birth_place_text': 'Sakarya', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': None, 'weight_kg': None,
    },
    9496441: {
        'display_name': 'John Leshiba Moshoeu', 'bdfutbol_id': '55569',
        'profile_url': 'https://www.bdfutbol.com/en/j/j55569.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/55569.jpg?v=1677403836',
        'birth_place_text': 'Soweto', 'birth_country_text': 'South Africa', 'birth_country_id': 78,
        'height_cm': None, 'weight_kg': None,
    },
    9496444: {
        'display_name': "Andre Kona N'Gole", 'bdfutbol_id': '702421',
        'profile_url': 'https://www.bdfutbol.com/en/j/j702421.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/702421.jpg?v=1738510674',
        'birth_place_text': 'Lubumbashi', 'birth_country_text': 'DR Congo', 'birth_country_id': 88,
        'height_cm': 181, 'weight_kg': None,
    },
    9495352: {
        'display_name': 'Bülent Uygun', 'bdfutbol_id': '51173',
        'profile_url': 'https://www.bdfutbol.com/en/j/j51173.html',
        'photo_url': 'https://www.bdfutbol.com/en/i/j/51173.jpg?v=1773596042',
        'birth_place_text': 'Sakarya', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': None, 'weight_kg': None,
    },
    9496365: {
        'display_name': 'Tayfur Havutçu', 'bdfutbol_id': '55596',
        'profile_url': 'https://www.bdfutbol.com/en/j/j55596.html',
        'photo_url': 'https://www.bdfutbol.com/en/i/j/55596.jpg?v=1677406587',
        'birth_place_text': 'Hesse', 'birth_country_text': 'Germany', 'birth_country_id': 4,
        'height_cm': None, 'weight_kg': None,
    },
    9496366: {
        'display_name': 'Müjdat Yetkiner', 'bdfutbol_id': '45593',
        'profile_url': 'https://www.bdfutbol.com/en/j/j45593.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/45593.jpg?v=1660746030',
        'birth_place_text': 'Istanbul (Istanbul)', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': None, 'weight_kg': None,
    },
    9496374: {
        'display_name': 'Semih Yuvakuran', 'bdfutbol_id': '42307',
        'profile_url': 'https://www.bdfutbol.com/en/j/j42307.html',
        'photo_url': 'https://www.bdfutbol.com/en/i/j/42307b.jpg?v=1780476207',
        'birth_place_text': 'Bursa (Bursa)', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': None, 'weight_kg': None,
    },
    9495332: {
        'display_name': 'Oğuz Çetin', 'bdfutbol_id': '45597',
        'profile_url': 'https://www.bdfutbol.com/en/j/j45597.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/45597.jpg?v=1660746209',
        'birth_place_text': 'Adapazarı (Sakarya)', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': 183, 'weight_kg': None,
    },
    9495351: {
        'display_name': 'Aykut Kocaman', 'bdfutbol_id': '43562',
        'profile_url': 'https://www.bdfutbol.com/en/j/j43562.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/43562.jpg?v=1658833731',
        'birth_place_text': 'Geyve (Sakarya)', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': None, 'weight_kg': None,
    },
    9496364: {
        'display_name': 'Uche Okechukwu', 'bdfutbol_id': '55567',
        'profile_url': 'https://www.bdfutbol.com/en/j/j55567.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/55567.jpg?v=1677403394',
        'birth_place_text': 'Lagos', 'birth_country_text': 'Nigeria', 'birth_country_id': 59,
        'height_cm': None, 'weight_kg': None,
    },
    9497231: {
        'display_name': 'Rıdvan Dilmen', 'bdfutbol_id': '45599',
        'profile_url': 'https://www.bdfutbol.com/en/j/j45599.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/45599.jpg?v=1660746294',
        'birth_place_text': 'Nazilli', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': None, 'weight_kg': None,
    },
    9495349: {
        'display_name': 'Hami Mandıralı', 'bdfutbol_id': '98308',
        'profile_url': 'https://www.bdfutbol.com/en/j/j98308.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/98308b.jpg?v=1405850706',
        'birth_place_text': 'Arsin (Trabzon)', 'birth_country_text': 'Turkey', 'birth_country_id': 84,
        'height_cm': 178, 'weight_kg': 75,
    },
    9496380: {
        'display_name': 'Shota Arveladze', 'bdfutbol_id': '4135',
        'profile_url': 'https://www.bdfutbol.com/en/j/j4135.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/4135.jpg?v=1524851554',
        'birth_place_text': 'Tbilisi', 'birth_country_text': 'Georgia', 'birth_country_id': 104,
        'height_cm': 181, 'weight_kg': 73,
    },
    9496385: {
        'display_name': 'Archil Arveladze', 'bdfutbol_id': '90266',
        'profile_url': 'https://www.bdfutbol.com/en/j/j90266.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/90266.jpg?v=1385581794',
        'birth_place_text': 'Tbilisi', 'birth_country_text': 'Georgia', 'birth_country_id': 104,
        'height_cm': 178, 'weight_kg': 73,
    },
    9496479: {
        'display_name': 'Frank Pingel', 'bdfutbol_id': '89072',
        'profile_url': 'https://www.bdfutbol.com/en/j/j89072.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/89072.jpg?v=1499412578',
        'birth_place_text': 'Vejlby', 'birth_country_text': 'Denmark', 'birth_country_id': 33,
        'height_cm': 183, 'weight_kg': None,
    },
    9496480: {
        'display_name': 'Gøran Sørloth', 'bdfutbol_id': '91650',
        'profile_url': 'https://www.bdfutbol.com/en/j/j91650.html',
        'photo_url': 'https://www.bdfutbol.com/i/j/91650.jpg?v=1420709006',
        'birth_place_text': 'Kristiansund', 'birth_country_text': 'Norway', 'birth_country_id': 60,
        'height_cm': None, 'weight_kg': None,
    },
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fmt_num(value: int) -> str:
    return f'{value:,}'.replace(',', '.')


def biography(player: dict[str, Any], team_name: str, row: dict[str, Any]) -> str:
    role = ROLE_ES.get(int(player.get('primary_role') or 0), 'Futbolista')
    parts = [f'{role} de {team_name} en la temporada 1993-94.']
    stats = []
    for key, label in [('appearances', 'partidos'), ('starts', 'como titular')]:
        value = row.get(key)
        if isinstance(value, int) and value >= 0:
            stats.append(f'{value} {label}')
    minutes = row.get('minutes')
    if isinstance(minutes, int) and minutes >= 0:
        stats.append(f'{fmt_num(minutes)} minutos')
    if stats:
        parts.append('En el registro histórico figura con ' + ', '.join(stats) + '.')
    goals = row.get('goals')
    if int(player.get('primary_role') or 0) != 0 and isinstance(goals, int) and goals >= 0:
        parts.append(f'Marcó {goals} gol' + ('' if goals == 1 else 'es') + '.')
    bd = player.get('birth_date')
    if bd:
        try:
            y, m, d = str(bd)[:10].split('-')
            parts.append(f'Fecha de nacimiento registrada: {d}/{m}/{y}.')
        except ValueError:
            pass
    place = player.get('historical_birth_place_text')
    if place:
        parts.append(f'Lugar de nacimiento documentado: {place}.')
    return ' '.join(parts)


def main() -> None:
    snap = load(SNAP)
    registry = load(REGISTRY)
    queue = load(QUEUE)
    by_player = {int(p['source_id']): p for p in snap['players']}
    reg_by = {int(p['source_id']): p for p in registry['players']}
    queue_by = {int(p['source_id']): p for p in queue['players']}

    photo_rows = []
    for sid, patch in PHOTO_PATCHES.items():
        player = by_player[sid]
        asset = PHOTO_DIR / f'{sid}.jpg'
        if not asset.exists():
            raise RuntimeError(f'normalized portrait missing: {asset}')
        player['bdfutbol_id'] = patch['bdfutbol_id']
        player['bdfutbol_url'] = patch['profile_url']
        player['historical_birth_place_text'] = patch['birth_place_text']
        player['historical_birth_place_source_url'] = patch['profile_url']
        player['historical_birth_place_source_label'] = 'BDFutbol individual profile v0.32'
        if patch.get('birth_country_id') is not None:
            player['birth_country_id'] = int(patch['birth_country_id'])
        if patch.get('height_cm') is not None:
            player['height_cm'] = int(patch['height_cm'])
        if patch.get('weight_kg') is not None:
            player['weight_kg'] = int(patch['weight_kg'])
        for target in (reg_by[sid], queue_by[sid]):
            target.update({
                'bdfutbol_id': patch['bdfutbol_id'],
                'bdfutbol_url': patch['profile_url'],
                'photo_filename': f'{sid}.jpg',
                'photo_status': 'bundled_normalized_bdfutbol',
                'photo_width': 40,
                'photo_height': 55,
                'photo_format': 'JPEG',
                'photo_mode': 'RGB',
                'photo_source': 'BDFutbol individual profile v0.32',
                'photo_source_url': patch['photo_url'],
                'individual_profile_source': 'BDFutbol individual profile v0.32',
                'individual_profile_source_url': patch['profile_url'],
                'historical_birth_place_text': patch['birth_place_text'],
            })
        photo_rows.append({'source_id': sid, **patch, 'asset': str(asset.relative_to(ROOT))})

    staged: dict[int, list[tuple[str, dict[str, Any], dict[str, Any]]]] = {}
    for country, path in STAGE_PATHS.items():
        stage = load(path)
        for club in stage.get('clubs', []):
            for row in club.get('players', []):
                sid = row.get('resolved_source_id')
                if sid is not None:
                    staged.setdefault(int(sid), []).append((country, club, row))

    active_team_ids = {int(t['source_id']) for t in snap['teams'] if int(t.get('league_id') or -1) in LEAGUES}
    active_players = [p for p in snap['players'] if p.get('team_id') in active_team_ids]
    by_team = {int(t['source_id']): t for t in snap['teams']}
    rows_written = with_stats = source_backed = multi_club = 0
    changed_from_v031 = 0
    missing_stage = []

    for p in active_players:
        sid = int(p['source_id'])
        candidates = staged.get(sid, [])
        if not candidates:
            missing_stage.append(sid)
            continue
        team_name = str(by_team[int(p['team_id'])]['name'])
        chosen = candidates[0]
        for cand in candidates:
            if str(cand[1].get('name') or '').casefold() == team_name.casefold():
                chosen = cand
                break
        country, club, row = chosen
        url = row.get('profile_source_url') or row.get('individual_profile_source_url') or club.get('bdfutbol_squad_url') or club.get('rsssf_roster_url') or row.get('source_url')
        label = row.get('profile_source') or ('BDFutbol — plantilla y estadísticas 1993-94' if club.get('bdfutbol_squad_url') else 'RSSSF — plantilla y estadísticas 1993-94' if club.get('rsssf_roster_url') else 'staging histórico 1993-94')
        new_bio = biography(p, team_name, row)
        if p.get('historical_biography_1993_94') != new_bio:
            changed_from_v031 += 1
        p['historical_biography_1993_94'] = new_bio
        p['historical_biography_source_url'] = url
        p['historical_biography_source_label'] = label
        p['historical_biography_evidence'] = {
            'season': '1993-94' if country != 'Russia' else '1993', 'club': team_name,
            'appearances': row.get('appearances'), 'starts': row.get('starts'), 'minutes': row.get('minutes'), 'goals': row.get('goals'),
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

    # Sync status for every physically bundled BDF-linked portrait, not just this batch.
    bundled = 0
    for reg_row in registry['players']:
        sid = int(reg_row['source_id'])
        if reg_row.get('bdfutbol_id') and (PHOTO_DIR / f'{sid}.jpg').exists():
            bundled += 1
            for target in (reg_by[sid], queue_by[sid]):
                target['photo_filename'] = f'{sid}.jpg'
                target['photo_status'] = 'bundled_normalized_bdfutbol'
                target['photo_width'] = 40; target['photo_height'] = 55
                target['photo_format'] = 'JPEG'; target['photo_mode'] = 'RGB'
                target.setdefault('photo_source', 'BDFutbol individual profile')

    audit = {
        'schema_version': 1,
        'checkpoint': '0.32.0-historical-metadata-turkey-profiles',
        'status': 'pass',
        'active_reconstructed_players': len(active_players),
        'biographies_written': rows_written,
        'biographies_changed_after_profile_curation': changed_from_v031,
        'biographies_with_season_stats': with_stats,
        'biographies_with_source_url': source_backed,
        'multi_club_identity_rows': multi_club,
        'new_bdfutbol_portraits': photo_rows,
        'bundled_bdfutbol_portraits_total': bundled,
        'policy': 'Biographies are regenerated after profile curation so corrected roles/names cannot leave stale text. Place-of-birth text is stored only when stated by an individual source; no city id is guessed.',
    }
    dump(SNAP, snap); dump(REGISTRY, registry); dump(QUEUE, queue)
    dump(DATA / 'historical_biographies_audit_v032.json', audit)
    print(json.dumps(audit, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
