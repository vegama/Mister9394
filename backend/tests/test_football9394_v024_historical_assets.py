import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
REG=ROOT/'data/football9394/belgium_1993_94_club_assets.json'


def test_belgian_1993_94_clubs_have_native_crest_assets():
    data=json.loads(REG.read_text(encoding='utf-8'))
    assert len(data['clubs']) == 18
    assert sum(r['identity_status']=='reused_exact_mdb_club' for r in data['clubs']) == 12
    for row in data['clubs']:
        p=ROOT/'frontend/public/historical9394/clubs'/f"{row['team_id']}.gif"
        assert p.exists(), row['name']
        with Image.open(p) as im:
            assert im.size == (40,40), row['name']
            assert im.format == 'GIF', row['name']


def test_belgian_club_ids_are_unique_and_successors_are_not_reused():
    data=json.loads(REG.read_text(encoding='utf-8'))
    ids=[r['team_id'] for r in data['clubs']]
    assert len(ids)==len(set(ids))
    by={r['name']:r for r in data['clubs']}
    for name in ['FC Seraing','Beveren','Germinal Ekeren','Lommel','RFC Liège','Molenbeek']:
        assert by[name]['identity_status']=='historical_team_id_required'
        assert by[name]['team_id'] >= 9_000_000


def test_photo_queue_declares_native_portrait_contract():
    from backend.tools.export_bdfutbol_photo_queue import build_queue
    q=build_queue()
    assert q
    for row in q:
        assert row['photo_width']==40
        assert row['photo_height']==55
        assert row['photo_format']=='JPEG'
        assert row['photo_mode']=='RGB'
