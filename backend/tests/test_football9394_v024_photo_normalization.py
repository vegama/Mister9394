from pathlib import Path

from PIL import Image

from backend.tools.normalize_bdfutbol_photos import TARGET_SIZE, normalize_image


def test_existing_historical_player_pack_is_natively_40x55():
    root = Path(__file__).resolve().parents[2] / "frontend/public/historical9394/players"
    # Historical pack has a handful of legacy outliers; the dominant/native contract
    # is 40x55 and every newly imported portrait must obey it.
    checked = 0
    native = 0
    for path in sorted(root.glob("*.jpg"))[:500]:
        with Image.open(path) as im:
            checked += 1
            native += tuple(im.size) == TARGET_SIZE
    assert checked >= 400
    assert native / checked >= 0.995


def test_normalizer_writes_exact_rgb_jpeg_without_stretching_contract(tmp_path):
    source = tmp_path / "incoming.png"
    out = tmp_path / "9499999.jpg"
    Image.new("RGBA", (120, 80), (150, 80, 40, 180)).save(source)
    row = normalize_image(source, out)
    assert row["output_size"] == [40, 55]
    with Image.open(out) as im:
        assert im.size == (40, 55)
        assert im.mode == "RGB"
        assert im.format == "JPEG"
