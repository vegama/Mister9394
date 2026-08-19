from __future__ import annotations

"""El parón de selecciones tiene que existir de verdad y no chocar con nada.

Antes de esto el campeonato eran 38 domingos seguidos: los internacionales se
iban el miércoles y volvían para jugar el domingo, así que no había parón. Y dos
de las ventanas caían **el mismo día** que una eliminatoria europea, de modo que
un jugador podía estar convocado con su selección y tener partido continental a
la vez.
"""

import re
from datetime import date
from pathlib import Path

from backend.app.football9394.career_international import generated_international_windows_9394
from backend.app.football9394.manager_career import (
    CAREER_START_DATE_9394,
    LEAGUE_MATCHDAY_DATES_9394,
    league_matchday_date_9394,
)

ROOT = Path(__file__).resolve().parents[2]
TOURNAMENTS = ROOT / "backend/app/football9394/career_tournaments.py"


def european_and_cup_dates() -> list[date]:
    """Fechas fijas de las competiciones europeas y de copa continental."""
    source = TOURNAMENTS.read_text(encoding="utf-8")
    return sorted({
        date(int(y), int(m), int(d))
        for y, m, d in re.findall(r"date\((\d{4}),(\d{1,2}),(\d{1,2})\)", source)
    })


def test_league_calendar_is_complete_and_ends_on_time():
    assert len(LEAGUE_MATCHDAY_DATES_9394) == 38
    assert LEAGUE_MATCHDAY_DATES_9394 == tuple(sorted(LEAGUE_MATCHDAY_DATES_9394))
    assert len(set(LEAGUE_MATCHDAY_DATES_9394)) == 38
    assert league_matchday_date_9394(1) == date(1993, 9, 5)
    # El campeonato debe cerrar antes del Mundial de Estados Unidos.
    assert league_matchday_date_9394(38) == date(1994, 5, 22)


def test_career_start_still_falls_between_matchday_seven_and_eight():
    # El arranque de carrera del 23 de octubre depende de esta relación.
    assert league_matchday_date_9394(7) < CAREER_START_DATE_9394 < league_matchday_date_9394(8)


def test_league_calendar_respects_international_breaks_and_european_dates():
    windows = generated_international_windows_9394(1993)
    assert len(windows) == 5

    for window in windows:
        clashing = [d for d in LEAGUE_MATCHDAY_DATES_9394 if 0 <= (d - window).days <= 4]
        assert not clashing, f"jornada dentro del parón de {window}: {clashing}"

    european = european_and_cup_dates()
    for window in windows:
        same_day = [d for d in european if abs((d - window).days) <= 1]
        assert not same_day, f"la ventana {window} coincide con competición europea: {same_day}"

    for matchday_date in LEAGUE_MATCHDAY_DATES_9394:
        collision = [d for d in european if abs((d - matchday_date).days) <= 1]
        assert not collision, f"jornada {matchday_date} choca con {collision}"


def test_break_actually_clears_a_weekend():
    """El parón debe notarse: un hueco mayor que la semana habitual."""
    windows = generated_international_windows_9394(1993)
    gaps = {
        LEAGUE_MATCHDAY_DATES_9394[i]: (LEAGUE_MATCHDAY_DATES_9394[i + 1] - LEAGUE_MATCHDAY_DATES_9394[i]).days
        for i in range(len(LEAGUE_MATCHDAY_DATES_9394) - 1)
    }
    for window in windows:
        previous = [d for d in LEAGUE_MATCHDAY_DATES_9394 if d < window]
        if not previous or window > LEAGUE_MATCHDAY_DATES_9394[-1]:
            continue
        assert gaps[previous[-1]] >= 14, f"sin parón real alrededor de {window}"
