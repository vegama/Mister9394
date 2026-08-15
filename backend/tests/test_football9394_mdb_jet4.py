from __future__ import annotations

import struct

from backend.app.football9394.mdb_import import _active_league, _active_tournament
from backend.app.football9394.mdb_jet4 import PAGE_SIZE, _TDefCursor, decode_jet4_text
from datetime import datetime


class _FakeDb:
    def __init__(self, pages: dict[int, bytes]):
        self.pages = pages

    def page(self, number: int) -> bytes:
        return self.pages[number]


def _page(next_page: int = 0, *, payload: dict[int, bytes] | None = None) -> bytes:
    buf = bytearray(PAGE_SIZE)
    buf[0] = 0x02
    struct.pack_into('<I', buf, 4, next_page)
    for offset, data in (payload or {}).items():
        buf[offset:offset + len(data)] = data
    return bytes(buf)


def test_tdef_cursor_reads_across_continuation_page_header():
    db = _FakeDb({
        10: _page(11, payload={PAGE_SIZE - 2: b'AB'}),
        11: _page(0, payload={8: b'CDEF'}),
    })
    cursor = _TDefCursor(db, 10, PAGE_SIZE - 2)
    assert cursor.read(6) == b'ABCDEF'
    assert cursor.page_number == 11
    assert cursor.pos == 12


def test_access_unicode_compression_decodes_ascii_payload():
    # ff fe marker + compressed bytes expands each byte to UTF-16LE.
    assert decode_jet4_text(b'\xff\xfeLiga') == 'Liga'


def test_historical_league_requires_explicit_1993_edition_marker():
    assert _active_league({'EdicionTemporada': '1993'}) is True
    assert _active_league({'EdicionTemporada': '2016'}) is False
    assert _active_league({'EdicionTemporada': None}) is False


def test_historical_tournament_is_selected_by_9394_window_and_admission():
    base = {
        'Admitido': True,
        'InicioCompeticion': datetime(1993, 9, 1),
        'FinCompeticion': datetime(1994, 5, 18),
    }
    assert _active_tournament(base) is True
    assert _active_tournament({**base, 'Admitido': False}) is False
    assert _active_tournament({
        **base,
        'InicioCompeticion': datetime(2009, 8, 1),
        'FinCompeticion': datetime(2010, 5, 1),
    }) is False
