from __future__ import annotations

from pathlib import Path
import json
import shutil
import sys
from collections import Counter
from typing import Any

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import (  # noqa: E402
    ROLE_TO_BROAD,
    ROLE_TO_LABEL,
    comparable,
    profile_gap_stats,
    role_ratings,
)
from tools.review_created_player_profiles import materialise_attributes  # noqa: E402

DATA = ROOT / 'data' / 'football9394'
SNAP = DATA / 'historical_snapshot.json'
REG = DATA / 'created_players_registry.json'
QUEUE = DATA / 'bdfutbol_photo_queue.json'
TURKEY_STAGE = DATA / 'turkey_1993_94_roster_staging.json'
PHOTO_DIR = ROOT / 'frontend' / 'public' / 'historical9394' / 'players'
RAW_PHOTO_DIR = ROOT / '.tmp_photos_v033'
STAGE_PATHS = {
    'Belgium': DATA / 'belgium_1993_94_roster_staging.json',
    'Turkey': TURKEY_STAGE,
    'Russia': DATA / 'russia_1993_roster_staging.json',
    'Greece': DATA / 'greece_1993_94_roster_staging.json',
}
ACTIVE_LEAGUES = {930015, 930047, 930052, 930057}

TM_GAZ = 'https://www.transfermarkt.com.tr/gaziantepspor/startseite/verein/524/saison_id/1993'
TM_ALTAY = 'https://www.transfermarkt.com.tr/altay-sk/startseite/verein/2375/saison_id/1993'
TM_ANK = 'https://www.transfermarkt.com.tr/mke-ankaragucu/startseite/verein/868/saison_id/1993'
TM_KAY = 'https://www.transfermarkt.com.tr/kayseri-erciyesspor/startseite/verein/6894/saison_id/1993'
TFF_CAFER = 'https://www.tff.org/Default.aspx?kisiId=22532&pageId=526'

COUNTRY_NAME = {
    20: 'Bosnia-Herzegovina', 40: 'Rusia', 62: 'Brasil', 78: 'Sudáfrica',
    84: 'Turquía', 85: 'Ucrania', 206: 'Turkmenistán',
}

# role values follow the canonical 0..17 project role map.
# precision=broad_only means the source validates the line of play but not the exact specialist role.
GAZIANTEP: dict[int, dict[str, Any]] = {
    9496453: dict(name='Metin Akçevre', dob='1967-03-03', nat=[84], birth_country=84, place='Ordu', role=0, pos='Goalkeeper', bdf='702570'),
    9496454: dict(name='İhsan Okay', dob='1969-08-07', nat=[84], birth_country=84, place='Istanbul', role=13, pos='Left Midfield', bdf='702419', note='Season-specific Transfermarkt role conflicts with BDFutbol broad Defender; season role retained.'),
    9496455: dict(name='Haşim Cem Kumbasar', dob='1967-08-16', nat=[84], birth_country=84, place='Istanbul', role=3, pos='Defender', precision='broad_only', bdf='1179967'),
    9496456: dict(name='Steven Mbuyi Komphela', dob='1967-07-01', nat=[78], birth_country=78, place='Kroonstad', role=3, pos='Centre-Back', bdf='1174975'),
    9496457: dict(name='Turgut Uçar', dob='1964-03-10', nat=[84], birth_country=84, place='Örnekköy', role=2, pos='Defender', precision='broad_only', bdf='702771', note='BDFutbol only establishes Defender reliably; previous left-back specialization is kept as neutral role carrier but marked unresolved.'),
    9496458: dict(name='Şenol Fidan', dob='1966-01-29', nat=[84], birth_country=84, place='Istanbul', role=9, pos='Right Midfield', height=178, bdf='55345'),
    9496459: dict(name='Mustafa Özer', dob='1969-08-27', nat=[84], birth_country=84, place='Siirt', role=1, pos='Right-Back', bdf='55594'),
    9496460: dict(name='Kemal Sönmez', dob='1966-10-15', nat=[84], birth_country=84, place='Manisa', role=3, pos='Centre-Back', bdf='1141594'),
    9496461: dict(name='Hasan Çelik', dob='1968-03-27', nat=[84], birth_country=84, place='Istanbul', role=17, pos='Centre-Forward', bdf='1175133'),
    9496462: dict(name='Elvir Bolić', dob='1971-10-10', nat=[20], birth_country=20, place='Zenica', role=17, pos='Centre-Forward', height=185, weight=81, bdf='661'),
    9496463: dict(name='Marcello Thomas Monteiro', dob='1966-11-16', nat=[62], birth_country=62, place='Porto Alegre', role=17, pos='Centre-Forward', bdf='1176268'),
    9496464: dict(name='Erol Bilir', dob='1966-08-03', nat=[84], birth_country=84, place='Gaziantep', role=0, pos='Goalkeeper', bdf='1179965'),
    9496465: dict(name='Kubilay Toptaş', dob='1972-12-03', nat=[84, 4], birth_country=84, place='Kars', role=17, pos='Centre-Forward', bdf='55585', note='Transfermarkt gives Centre-Forward (AM/RW secondary); BDFutbol has broad Midfielder. Season-specific specialist role retained.'),
    9496466: dict(name='Necat Barut', dob='1965-10-01', nat=[84], birth_country=84, place='Edirne', role=3, pos='Centre-Back', height=182, bdf='1176410'),
    9496467: dict(name='Yavuz Karaçam', dob='1966-11-01', nat=[84], birth_country=84, place='Yozgat', role=3, pos='Defender', precision='broad_only', bdf='1179962'),
    9496468: dict(name='Hasan Özer', dob='1974-10-01', nat=[84], birth_country=84, place='Siirt', role=17, pos='Centre-Forward', height=185, bdf='54567'),
    9496469: dict(name='Teboho Claude Moloi', dob='1968-07-02', nat=[78], birth_country=78, place='Soweto', role=7, pos='Midfielder', precision='broad_only', bdf='1179966'),
    9496470: dict(name='Tayfun Yungul', dob='1973-03-21', nat=[84], birth_country=84, place='Istanbul', role=7, pos='Central Midfield', bdf='1125764'),
    9497272: dict(name='Mehmet Gönülaçar', dob='1972-03-03', nat=[84], birth_country=84, place='Batman', role=17, pos='Centre-Forward', height=181, bdf='58014', note='Season-specific Transfermarkt role is Centre-Forward; BDFutbol has broad Midfielder. Conflict retained explicitly.'),
    9497273: dict(name='Hüseyin Sarı', dob='1974-12-09', nat=[84], birth_country=84, place='Ordu', role=3, pos='Centre-Back', bdf='702571'),
    9497274: dict(name='Mustafa Yücedağ', dob='1966-04-25', nat=[84], birth_country=84, place='Gaziantep', role=8, pos='Attacking Midfield', height=175, bdf='702824'),
    9497275: dict(name='Abdussamet Yiğit', dob='1975-02-02', nat=[84], birth_country=84, place='Muş', role=3, pos='Defender', precision='broad_only', bdf='1179964'),
    9497276: dict(name='Murat Deniz', dob='1977-05-05', nat=[84], birth_country=84, place='Tuzluca (Iğdır)', role=17, pos='Forward', precision='broad_only', bdf='1169863', note='BDFutbol identity is a 1977-born Forward. A similarly named Transfermarkt goalkeeper row is not treated as the same person.'),
    9497277: dict(name='Mustafa Oğur', dob='1975-05-12', nat=[84], birth_country=84, place='Gaziantep', role=7, pos='Midfielder', precision='broad_only', bdf='1179963'),
    9497278: dict(name='Burhanettin Turgut', dob='1970-12-01', nat=[84], birth_country=84, place='Mersin', role=3, pos='Centre-Back', bdf='1179968'),
    9497279: dict(name='Ersin Şenyurt', dob='1971-12-20', nat=[84], birth_country=84, place='Istanbul', role=7, pos='Midfielder', precision='broad_only', bdf='1179969'),
}

NEXT_HIGH_CONFIDENCE: dict[int, dict[str, Any]] = {
    9496491: dict(club='Altay', name='Ahmet Akuygur', dob='1967-05-29', nat=[84], birth_country=84, place='Konya', role=1, pos='Right-Back', height=176, url=TM_ALTAY),
    9496502: dict(club='Altay', name='Yuriy Shelepnytskyi', dob='1965-01-18', nat=[85], birth_country=None, place='Luzhany, Chernivtsi Oblast (USSR)', role=6, pos='Defensive Midfield', height=184, url=TM_ALTAY, note='Birth place is documented in the former USSR; no modern birth_country_id is invented.'),
    9496517: dict(club='Ankaragücü', name='Mehmet Yıldırım', dob='1972-09-15', nat=[84], birth_country=84, place='Erzurum', role=17, pos='Centre-Forward', url=TM_ANK),
    9496519: dict(club='Ankaragücü', name='Yuriy Matveev', dob='1967-06-08', nat=[40], birth_country=None, place='Nizhniy Tagil, Sverdlovsk Oblast (USSR)', role=17, pos='Centre-Forward', height=183, url=TM_ANK, note='Birth place is documented in the former USSR; no modern birth_country_id is invented.'),
    9497305: dict(club='Ankaragücü', name='Charyar Abdurakhmanovich Mukhadov', dob='1969-11-12', nat=[206], birth_country=206, place='Ashgabat', role=17, pos='Centre-Forward', height=179, url='https://www.bdfutbol.com/en/j/j1178793.html', bdf='1178793'),
    9497315: dict(club='Kayserispor', name='Öztürk Tanrıbilir', dob='1966-05-03', nat=[84], birth_country=84, place='Kayseri', role=0, pos='Goalkeeper', url=TM_KAY),
    9497314: dict(club='Kayserispor', name='Cafer Aydın', dob='1971-11-17', nat=[84], birth_country=84, place='Çorum', role=17, pos='Centre-Forward', height=181, url=TFF_CAFER),
}

PHOTO_URLS = {
    9496453: 'https://www.bdfutbol.com/i/j/702570.jpg?v=1705344010',
    9496455: 'https://www.bdfutbol.com/i/j/1179967.jpg?v=1782644741',
    9496456: 'https://www.bdfutbol.com/i/j/1174975.jpg?v=1780345596',
    9496457: 'https://www.bdfutbol.com/i/j/702771.jpg?v=1706693891',
    9496458: 'https://www.bdfutbol.com/i/j/55345.jpg?v=1676805008',
    9496460: 'https://www.bdfutbol.com/i/j/1141594b.jpg?v=1746560319',
    9496462: 'https://www.bdfutbol.com/i/j/661.jpg?v=1275150842',
    9496463: 'https://www.bdfutbol.com/i/j/1176268.jpg?v=1780345599',
    9496465: 'https://www.bdfutbol.com/i/j/55585.jpg?v=1677405428',
    9496466: 'https://www.bdfutbol.com/i/j/1176410.jpg?v=1780345599',
    9496467: 'https://www.bdfutbol.com/i/j/1179962.jpg?v=1782644192',
    9496468: 'https://www.bdfutbol.com/i/j/54567.jpg?v=1686210822',
    9496469: 'https://www.bdfutbol.com/i/j/1179966.jpg?v=1782644577',
    9496470: 'https://www.bdfutbol.com/i/j/1125764.jpg?v=1719252802',
    9497272: 'https://www.bdfutbol.com/i/j/58014.jpg?v=1690975940',
    9497273: 'https://www.bdfutbol.com/i/j/702571.jpg?v=1705344023',
    9497274: 'https://www.bdfutbol.com/i/j/702824.jpg?v=1707380797',
    9497276: 'https://www.bdfutbol.com/i/j/1169863.jpg?v=1783001487',
}

ROLE_ES = {
    0: 'Portero', 1: 'Lateral derecho', 2: 'Lateral izquierdo', 3: 'Defensa central', 4: 'Defensa central',
    5: 'Líbero', 6: 'Mediocentro defensivo', 7: 'Centrocampista', 8: 'Mediapunta', 9: 'Interior derecho',
    10: 'Interior derecho', 11: 'Extremo derecho', 12: 'Extremo derecho', 13: 'Interior izquierdo',
    14: 'Interior izquierdo', 15: 'Extremo izquierdo', 16: 'Extremo izquierdo', 17: 'Delantero centro',
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def split_name(name: str) -> tuple[str | None, str]:
    parts = name.split()
    return (None, name) if len(parts) == 1 else (' '.join(parts[:-1]), parts[-1])


def reattribute(player: dict[str, Any], new_role: int, originals: list[dict[str, Any]], sid: int) -> None:
    a, b = comparable(originals, ROLE_TO_BROAD[new_role], int(player.get('overall') or 70), sid)
    player['attributes'] = materialise_attributes(int(player.get('overall') or 70), a, b)
    player['attribute_source'] = 'fixed_source_comparable_role_correction_0.33'
    player['attribute_comparable_source_ids'] = [int(a['source_id']), int(b['source_id'])]


def apply_profile(
    player: dict[str, Any], patch: dict[str, Any], originals: list[dict[str, Any]], sid: int, source_url: str,
    source_label: str,
) -> dict[str, Any]:
    old = {
        'display_name': player.get('display_name'), 'role': int(player.get('primary_role') or 0),
        'broad': player.get('broad_position'), 'position': player.get('historical_position_1993_94'),
        'birth_date': player.get('birth_date'), 'international_country_id': player.get('international_country_id'),
    }
    name = patch['name']
    first, surname = split_name(name)
    player['display_name'] = name
    player['first_name'] = first
    player['surname1'] = surname
    player['birth_date'] = patch['dob'] + 'T00:00:00'
    if patch.get('birth_country') is not None:
        player['birth_country_id'] = int(patch['birth_country'])
    player['international_country_id'] = int(patch['nat'][0])
    player['profile_nationality_country_ids'] = [int(x) for x in patch['nat']]
    if len(patch['nat']) > 1:
        player['secondary_nationality_country_id'] = int(patch['nat'][1])
    player['historical_birth_place_text'] = patch.get('place')
    player['historical_birth_place_source_url'] = f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html" if patch.get('bdf') else source_url
    player['historical_birth_place_source_label'] = 'BDFutbol individual profile v0.33' if patch.get('bdf') else source_label
    if patch.get('height') is not None:
        player['height_cm'] = int(patch['height'])
    if patch.get('weight') is not None:
        player['weight_kg'] = int(patch['weight'])
    if patch.get('bdf'):
        player['bdfutbol_id'] = str(patch['bdf'])
        player['bdfutbol_url'] = f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"

    role = int(patch['role'])
    old_role = int(player.get('primary_role') or 0)
    old_broad = player.get('broad_position')
    player['primary_role'] = role
    player['broad_position'] = ROLE_TO_BROAD[role]
    player['role_ratings'] = role_ratings(role)
    precision = patch.get('precision', 'exact')
    player['profile_position_precision'] = precision
    player['source_profile_position'] = patch['pos']
    player['profile_review_required'] = precision == 'broad_only'
    if precision == 'broad_only':
        player['historical_position_1993_94'] = patch['pos'] + ' (exact role unresolved)'
        player['historical_position_source'] = source_label + ' — broad position only v0.33'
    else:
        player['historical_position_1993_94'] = ROLE_TO_LABEL[role]
        player['historical_position_source'] = source_label + ' v0.33'
    player['historical_profile_source'] = source_label + ' v0.33'
    player['historical_profile_source_url'] = source_url
    if patch.get('note'):
        player['historical_profile_source_note'] = patch['note']
    if role != old_role or player['broad_position'] != old_broad:
        reattribute(player, role, originals, sid)
    return {'source_id': sid, 'before': old, 'after': {
        'display_name': player['display_name'], 'role': player['primary_role'], 'broad': player['broad_position'],
        'position': player['historical_position_1993_94'], 'birth_date': player['birth_date'],
        'international_country_id': player['international_country_id'],
    }, 'role_changed': role != old_role, 'source_profile_position': patch['pos'], 'precision': precision}


def sync_registry_queue(target: dict[str, Any], player: dict[str, Any], patch: dict[str, Any], source_label: str, source_url: str) -> None:
    target.update({
        'display_name': player['display_name'], 'first_name': player.get('first_name'), 'surname1': player.get('surname1'),
        'birth_date': str(player['birth_date'])[:10], 'country_id': player.get('international_country_id'),
        'country_name': COUNTRY_NAME.get(player.get('international_country_id')),
        'broad_position': player.get('broad_position'), 'historical_position_1993_94': player.get('historical_position_1993_94'),
        'profile_review_required': bool(player.get('profile_review_required')),
        'individual_profile_source': source_label + ' v0.33', 'individual_profile_source_url': source_url,
        'historical_birth_place_text': patch.get('place'),
    })
    if patch.get('bdf'):
        target['bdfutbol_id'] = str(patch['bdf'])
        target['bdfutbol_url'] = f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"


def update_stage_row(stage: dict[str, Any], club_name: str, sid: int, player: dict[str, Any], patch: dict[str, Any], source_url: str, source_label: str) -> None:
    club = next(c for c in stage['clubs'] if c.get('name') == club_name)
    row = next(r for r in club['players'] if int(r.get('resolved_source_id') or -1) == sid)
    row.update({
        'resolved_display_name': player['display_name'], 'resolved_primary_role': player['primary_role'],
        'resolved_exact_position': player['historical_position_1993_94'], 'resolved_birth_date': player['birth_date'],
        'resolved_country_id': player['international_country_id'], 'source_profile_position': patch['pos'],
        'profile_source': source_label + ' v0.33', 'profile_source_url': source_url,
        'position_source': player['historical_position_source'],
    })
    if patch.get('place'):
        row['resolved_birth_place_text'] = patch['place']
    if patch.get('bdf'):
        row['bdfutbol_id'] = str(patch['bdf'])
        row['individual_profile_source_url'] = f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"
    if patch.get('note'):
        row['profile_source_note'] = patch['note']


def normalize_new_photos(players: dict[int, dict[str, Any]], reg_by: dict[int, dict[str, Any]], queue_by: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for sid, url in PHOTO_URLS.items():
        raw = RAW_PHOTO_DIR / f'{sid}.jpg'
        if not raw.exists():
            raise RuntimeError(f'raw portrait missing: {raw}')
        with Image.open(raw) as im:
            rgb = im.convert('RGB')
            fitted = ImageOps.fit(rgb, (40, 55), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            out = PHOTO_DIR / f'{sid}.jpg'
            fitted.save(out, 'JPEG', quality=92, optimize=True)
        with Image.open(out) as check:
            if check.size != (40, 55) or check.mode != 'RGB' or check.format != 'JPEG':
                raise RuntimeError(f'invalid normalized portrait {sid}: {check.size}/{check.mode}/{check.format}')
        patch = GAZIANTEP[sid]
        profile_url = f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"
        for target in (reg_by[sid], queue_by[sid]):
            target.update({
                'photo_filename': f'{sid}.jpg', 'photo_status': 'bundled_normalized_bdfutbol',
                'photo_width': 40, 'photo_height': 55, 'photo_format': 'JPEG', 'photo_mode': 'RGB',
                'photo_source': 'BDFutbol individual profile v0.33', 'photo_source_url': url,
                'bdfutbol_id': str(patch['bdf']), 'bdfutbol_url': profile_url,
            })
        rows.append({'source_id': sid, 'display_name': players[sid]['display_name'], 'photo_url': url,
                     'profile_url': profile_url, 'asset': str((PHOTO_DIR / f'{sid}.jpg').relative_to(ROOT)),
                     'width': 40, 'height': 55, 'format': 'JPEG', 'mode': 'RGB'})
    return rows


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
        y, m, d = str(bd)[:10].split('-')
        parts.append(f'Fecha de nacimiento registrada: {d}/{m}/{y}.')
    place = player.get('historical_birth_place_text')
    if place:
        parts.append(f'Lugar de nacimiento documentado: {place}.')
    return ' '.join(parts)


def regenerate_biographies(snapshot: dict[str, Any]) -> dict[str, Any]:
    staged: dict[int, list[tuple[str, dict[str, Any], dict[str, Any]]]] = {}
    for country, path in STAGE_PATHS.items():
        stage = load(path)
        for club in stage.get('clubs', []):
            for row in club.get('players', []):
                sid = row.get('resolved_source_id')
                if sid is not None:
                    staged.setdefault(int(sid), []).append((country, club, row))
    active_team_ids = {int(t['source_id']) for t in snapshot['teams'] if int(t.get('league_id') or -1) in ACTIVE_LEAGUES}
    active = [p for p in snapshot['players'] if p.get('team_id') in active_team_ids]
    by_team = {int(t['source_id']): t for t in snapshot['teams']}
    changed = 0
    multi = 0
    missing = []
    for p in active:
        sid = int(p['source_id'])
        candidates = staged.get(sid, [])
        if not candidates:
            missing.append(sid)
            continue
        team_name = str(by_team[int(p['team_id'])]['name'])
        chosen = candidates[0]
        for cand in candidates:
            if str(cand[1].get('name') or '').casefold() == team_name.casefold():
                chosen = cand
                break
        country, club, row = chosen
        new = biography(p, team_name, row)
        if p.get('historical_biography_1993_94') != new:
            changed += 1
        p['historical_biography_1993_94'] = new
        p['historical_biography_source_url'] = row.get('profile_source_url') or row.get('individual_profile_source_url') or club.get('bdfutbol_squad_url') or club.get('rsssf_roster_url')
        p['historical_biography_source_label'] = row.get('profile_source') or 'plantilla/estadísticas históricas 1993-94'
        p['historical_biography_evidence'] = {
            'season': '1993' if country == 'Russia' else '1993-94', 'club': team_name,
            'appearances': row.get('appearances'), 'starts': row.get('starts'), 'minutes': row.get('minutes'),
            'goals': row.get('goals'), 'staging_name': row.get('bdfutbol_name') or row.get('rsssf_name') or row.get('resolved_display_name'),
        }
        p['historical_biography_status'] = 'source_backed_season_summary'
        p['historical_biography_staged_clubs'] = [str(c[1].get('name')) for c in candidates]
        if len(candidates) > 1:
            multi += 1
    if missing:
        raise RuntimeError(f'active reconstructed players missing staging: {missing[:10]} total={len(missing)}')
    return {'active_players': len(active), 'biographies_written': len(active), 'changed_from_v032': changed, 'multi_club_identities': multi, 'missing_stage_rows': 0}


def main() -> None:
    snap = load(SNAP)
    reg = load(REG)
    queue = load(QUEUE)
    stage = load(TURKEY_STAGE)
    by = {int(p['source_id']): p for p in snap['players']}
    reg_by = {int(p['source_id']): p for p in reg['players']}
    queue_by = {int(p['source_id']): p for p in queue['players']}
    originals = [p for p in snap['players'] if p.get('attributes') and not p.get('external_origin') and not p.get('creation_batch')]
    before = profile_gap_stats(snap)
    changes: list[dict[str, Any]] = []

    for sid, patch in GAZIANTEP.items():
        p = by[sid]
        profile_url = f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"
        ch = apply_profile(p, patch, originals, sid, TM_GAZ, 'Transfermarkt Gaziantepspor 1993-94 squad + BDFutbol individual profile')
        changes.append({**ch, 'club': 'Gaziantepspor'})
        sync_registry_queue(reg_by[sid], p, patch, 'BDFutbol/Transfermarkt profile cross-check', profile_url)
        sync_registry_queue(queue_by[sid], p, patch, 'BDFutbol/Transfermarkt profile cross-check', profile_url)
        update_stage_row(stage, 'Gaziantepspor', sid, p, patch, TM_GAZ, 'Transfermarkt Gaziantepspor 1993-94 squad + BDFutbol individual profile')

    for sid, patch in NEXT_HIGH_CONFIDENCE.items():
        p = by[sid]
        source_url = patch['url']
        ch = apply_profile(p, patch, originals, sid, source_url, f"historical season/individual profile cross-check — {patch['club']}")
        changes.append({**ch, 'club': patch['club']})
        sync_registry_queue(reg_by[sid], p, patch, 'historical season/individual profile cross-check', source_url)
        sync_registry_queue(queue_by[sid], p, patch, 'historical season/individual profile cross-check', source_url)
        update_stage_row(stage, patch['club'], sid, p, patch, source_url, f"historical season/individual profile cross-check — {patch['club']}")

    dump(TURKEY_STAGE, stage)
    photo_rows = normalize_new_photos(by, reg_by, queue_by)
    dump(SNAP, snap)
    dump(REG, reg)
    dump(QUEUE, queue)

    # Biography regeneration reads staging back from disk, including the updates above.
    biography_audit = regenerate_biographies(snap)
    dump(SNAP, snap)

    after = profile_gap_stats(snap)
    reg_ids = [int(r['source_id']) for r in reg['players']]
    queue_ids = [int(r['source_id']) for r in queue['players']]
    if len(reg_ids) != len(set(reg_ids)) or len(queue_ids) != len(set(queue_ids)):
        raise RuntimeError('duplicate source IDs in registry/photo queue')
    if set(reg_ids) != set(queue_ids):
        raise RuntimeError('registry/photo queue identity sets diverged')

    audit = {
        'schema_version': 1,
        'checkpoint': '0.33.0-turkey-gaziantep-next-profiles',
        'status': 'pass',
        'profile_gaps_before': before,
        'profile_gaps_after': after,
        'profiles': {
            'curated_this_batch': len(changes),
            'gaziantepspor_curated': len(GAZIANTEP),
            'next_high_confidence_curated': len(NEXT_HIGH_CONFIDENCE),
            'role_corrections_this_batch': sum(bool(c['role_changed']) for c in changes),
            'broad_only_exact_role_unresolved': sum(c['precision'] == 'broad_only' for c in changes),
            'by_club': dict(Counter(c['club'] for c in changes)),
            'changes': changes,
        },
        'photos': {
            'new_normalized_bdfutbol_portraits': len(photo_rows),
            'format': 'JPEG RGB 40x55',
            'rows': photo_rows,
            'total_bundled_normalized_bdfutbol': sum(r.get('photo_status') == 'bundled_normalized_bdfutbol' for r in reg['players']),
        },
        'biographies': biography_audit,
        'identity_integrity': {
            'registry_rows': len(reg_ids), 'queue_rows': len(queue_ids), 'unique_registry_ids': len(set(reg_ids)),
            'unique_queue_ids': len(set(queue_ids)), 'sets_match': set(reg_ids) == set(queue_ids),
        },
        'source_policy': [
            'Season-specific specialist roles override old heuristic staging when corroborated.',
            'BDFutbol broad positions are retained as explicit conflicts when they disagree with a season-specific specialist role.',
            'Former-USSR birthplace text is stored without inventing a modern birth_country_id.',
            'Broad-only source positions remain profile_review_required instead of being silently specialized.',
            'No basketball 75/25 rule is used anywhere in football player construction or correction.',
        ],
    }
    dump(DATA / 'historical_profiles_metadata_audit_v033.json', audit)
    dump(DATA / 'historical_metadata_gaps_v033.json', {'checkpoint': audit['checkpoint'], 'gaps': after})
    dump(DATA / 'historical_biographies_audit_v033.json', biography_audit)
    dump(DATA / 'bdfutbol_photo_normalization_v033_gaziantep.json', {
        'checkpoint': audit['checkpoint'], 'status': 'pass', 'portraits': photo_rows,
        'normalization': {'width': 40, 'height': 55, 'format': 'JPEG', 'mode': 'RGB', 'crop': 'centered ImageOps.fit'},
    })
    print(json.dumps({
        'curated': len(changes), 'role_corrections': audit['profiles']['role_corrections_this_batch'],
        'photos_new': len(photo_rows), 'photos_total': audit['photos']['total_bundled_normalized_bdfutbol'],
        'turkey_gaps_before': before['Turkey'], 'turkey_gaps_after': after['Turkey'],
        'biographies': biography_audit,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
