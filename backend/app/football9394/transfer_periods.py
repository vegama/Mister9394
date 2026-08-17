from __future__ import annotations

"""1993-94 registration periods and career pacing.

Modern FIFA transfer windows were not yet the governing framework in 1993-94.
The game therefore models an era-style *registration period*: high summer
activity, continued in-season registration up to a late-season deadline, and
then a closed run-in.

Product rule from 0.16 onward: this 1993-94 registration environment is frozen
for the whole alternate-history career.  Later real-world reforms (including
Spain's later winter market and Bosman-era liberalisation) are deliberately not
introduced.

The MDB does not encode transfer dates, so dates outside the explicitly sourced
English 24 March 1994 deadline are simulation policy and are labelled as such in
UI/API rather than presented as archival fact.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class TransferPeriodStatus9394:
    open: bool
    phase: str
    label: str
    next_change: date | None
    activity: str
    registration_kind: str
    source_note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "open": self.open,
            "phase": self.phase,
            "label": self.label,
            "next_change": self.next_change.isoformat() if self.next_change else None,
            "activity": self.activity,
            "registration_kind": self.registration_kind,
            "source_note": self.source_note,
        }


EUROPEAN_COUNTRIES = frozenset({1, 3, 4, 5, 6, 10, 11, 43})
AMERICAS_COUNTRIES = frozenset({2, 26, 38, 62, 63, 64})


def transfer_period_status(day: date, *, country_id: int | None, season: str) -> TransferPeriodStatus9394:
    country = int(country_id or 0)
    start_year = int(str(season).split("-")[0])

    # Deliberately no future-rule branch here.  Spain and every other
    # competition keep the 1993-94-era registration model throughout the
    # alternate-history save.  The `season` argument remains part of the public
    # API for compatibility, but cannot unlock later real-world windows.

    if country == 6:  # England: historical 1993-94 deadline day was 24 March.
        cutoff = date(day.year if day.month <= 6 else day.year + 1, 3, 24)
        return _pre_window(day, cutoff=cutoff, exact_cutoff=True)

    if country in EUROPEAN_COUNTRIES:
        cutoff = date(day.year if day.month <= 6 else day.year + 1, 3, 31)
        return _pre_window(day, cutoff=cutoff, exact_cutoff=False)

    if country in AMERICAS_COUNTRIES:
        cutoff = date(day.year if day.month <= 6 else day.year + 1, 2, 28)
        return _pre_window(day, cutoff=cutoff, exact_cutoff=False, americas=True)

    cutoff = date(day.year if day.month <= 6 else day.year + 1, 3, 31)
    return _pre_window(day, cutoff=cutoff, exact_cutoff=False)


def _pre_window(day: date, *, cutoff: date, exact_cutoff: bool, americas: bool = False) -> TransferPeriodStatus9394:
    if day.month in (7, 8):
        return _status(True, "summer", "Pretemporada · mercado muy activo", date(day.year, 9, 1), "high", "pre_window_registration",
                       "Periodo de alta actividad de verano en la era previa a las ventanas FIFA modernas.")
    # For Jan-Jun, cutoff belongs to current calendar year; for Sep-Dec it is next year.
    if day <= cutoff:
        note = ("Fecha límite inglesa 1993-94: 24 de marzo." if exact_cutoff else
                "La MDB no aporta fecha nacional de cierre; se usa un corte tardío de temporada explícito como regla de simulación.")
        return _status(True, "in_season", "Inscripción en temporada", cutoff.replace(day=cutoff.day) if day < cutoff else cutoff, "low" if not americas else "medium", "pre_window_registration", note)
    next_open = date(day.year, 7, 1) if day.month < 7 else date(day.year + 1, 7, 1)
    return _status(False, "run_in_closed", "Cierre de inscripciones · tramo final", next_open, "none", "pre_window_registration",
                   "Tramo final protegido frente a nuevas altas en la simulación histórica.")


def _status(open_: bool, phase: str, label: str, next_change: date | None, activity: str, kind: str, note: str) -> TransferPeriodStatus9394:
    return TransferPeriodStatus9394(open_, phase, label, next_change, activity, kind, note)


def market_activity_budget(status: TransferPeriodStatus9394) -> int:
    return {"high": 8, "medium": 4, "low": 2, "none": 0}.get(status.activity, 0)
