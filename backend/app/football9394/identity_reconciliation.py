from __future__ import annotations

"""Conservative historical-player identity reconciliation.

Historical imports must compare a candidate against the whole player database
before creating a new runtime identity.  Nationality is evidence, not a hard
filter: many legacy records contain only birthplace, while a player's national
team can be different (Ireland/England is a common 1993-94 example).
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import unicodedata
from typing import Any, Iterable


def clean_text(value: Any) -> str:
    text = str(value or "").replace("not applicable", " ")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def player_country_id(player: dict[str, Any]) -> int | None:
    value = player.get("international_country_id") or player.get("birth_country_id")
    return int(value) if isinstance(value, int) and value > 0 else None


def name_variants(player: dict[str, Any]) -> set[str]:
    values = {
        clean_text(player.get("display_name")),
        clean_text(" ".join(str(player.get(k) or "") for k in ("first_name", "surname1", "surname2"))),
        clean_text(" ".join(str(player.get(k) or "") for k in ("first_name", "surname1"))),
        clean_text(player.get("surname1")),
        clean_text(" ".join(str(player.get(k) or "") for k in ("surname1", "surname2"))),
    }
    return {v for v in values if v}


def full_name_variants(player: dict[str, Any]) -> set[str]:
    values = {
        clean_text(player.get("display_name")),
        clean_text(" ".join(str(player.get(k) or "") for k in ("first_name", "surname1", "surname2"))),
        clean_text(" ".join(str(player.get(k) or "") for k in ("first_name", "surname1"))),
    }
    return {v for v in values if v}


def _date(value: Any) -> tuple[int, int, int] | None:
    text = str(value or "")[:10]
    try:
        year, month, day = (int(x) for x in text.split("-"))
        return year, month, day
    except (TypeError, ValueError):
        return None


def _given_tokens(value: Any) -> list[str]:
    return clean_text(value).split()


def _given_similarity(target_given: str, player: dict[str, Any]) -> float:
    left = _given_tokens(target_given)
    right = _given_tokens(player.get("first_name"))
    if not left or not right:
        return 0.0
    return max(SequenceMatcher(None, a, b).ratio() for a in left for b in right)


def _full_similarity(target_display: str, target_given: str, target_family: str, player: dict[str, Any]) -> float:
    targets = {
        clean_text(target_display),
        clean_text(f"{target_given} {target_family}"),
    }
    targets.discard("")
    return max(
        (SequenceMatcher(None, target, variant).ratio() for target in targets for variant in full_name_variants(player)),
        default=0.0,
    )


@dataclass(frozen=True, slots=True)
class IdentityCandidate:
    source_id: int
    display_name: str
    score: float
    full_similarity: float
    given_similarity: float
    same_surname: bool
    same_country: bool
    same_team: bool
    same_dob: bool
    same_day_month: bool
    year_delta: int | None


@dataclass(frozen=True, slots=True)
class IdentityMatch:
    player: dict[str, Any] | None
    resolution: str
    confidence: str
    score: float
    candidates: tuple[IdentityCandidate, ...]


def reconcile_player_identity(
    players: Iterable[dict[str, Any]],
    *,
    target_display: str,
    target_given: str = "",
    target_family: str = "",
    target_birth_date: Any = None,
    target_country_id: int | None = None,
    expected_team_id: int | None = None,
    identity_override_id: int | None = None,
) -> IdentityMatch:
    """Return a conservative match or ``None`` after comparing the whole DB.

    Automatic matches require multiple pieces of evidence.  A shared surname or
    date alone is never enough.  This deliberately handles legacy records whose
    international country is missing or whose DOB has a small source error.
    """

    rows = list(players)
    target = clean_text(target_display)
    family = clean_text(target_family)
    target_dob = _date(target_birth_date)

    if identity_override_id is not None:
        found = next((p for p in rows if int(p.get("source_id") or 0) == int(identity_override_id)), None)
        if found is not None:
            return IdentityMatch(found, "identity_override", "verified", 999.0, ())

    candidates: list[tuple[float, str, dict[str, Any], IdentityCandidate]] = []
    for player in rows:
        pid = int(player.get("source_id") or 0)
        if pid <= 0:
            continue
        full_sim = _full_similarity(target_display, target_given, target_family, player)
        given_sim = _given_similarity(target_given, player)
        surname = clean_text(player.get("surname1"))
        same_surname = bool(family and surname and family == surname)
        country = player_country_id(player)
        same_country = bool(target_country_id and country and int(country) == int(target_country_id))
        team_id = int(player.get("team_id") or 0)
        same_team = bool(expected_team_id and team_id and int(expected_team_id) == team_id)
        dob = _date(player.get("birth_date"))
        same_dob = bool(target_dob and dob and target_dob == dob)
        same_dm = bool(target_dob and dob and target_dob[1:] == dob[1:])
        year_delta = abs(target_dob[0] - dob[0]) if target_dob and dob else None
        exact_full = bool(target and target in full_name_variants(player))

        # Strong global evidence.  Nationality is intentionally not mandatory.
        resolution: str | None = None
        confidence = ""
        if exact_full and (same_dob or same_team or same_country):
            resolution, confidence = "global_exact_name", "high"
        elif same_dob and same_surname and given_sim >= 0.55:
            resolution, confidence = "global_dob_name", "high"
        elif same_team and same_surname and given_sim >= 0.55:
            resolution, confidence = "global_team_name", "high"
        elif same_team and same_dob and full_sim >= 0.62:
            resolution, confidence = "global_team_dob", "high"
        elif same_country and same_surname and given_sim >= 0.72 and same_dm and (year_delta is not None and year_delta <= 3):
            resolution, confidence = "country_name_dob_tolerance", "medium"
        elif same_country and full_sim >= 0.96 and (year_delta is None or year_delta <= 3):
            resolution, confidence = "country_fuzzy_name", "medium"
        if resolution is None:
            continue

        score = (
            full_sim * 100
            + given_sim * 12
            + (28 if same_dob else 0)
            + (22 if same_team else 0)
            + (12 if same_country else 0)
            + (14 if same_surname else 0)
            + (8 if same_dm and year_delta is not None and year_delta <= 3 else 0)
        )
        info = IdentityCandidate(
            source_id=pid,
            display_name=str(player.get("display_name") or ""),
            score=round(score, 3),
            full_similarity=round(full_sim, 4),
            given_similarity=round(given_sim, 4),
            same_surname=same_surname,
            same_country=same_country,
            same_team=same_team,
            same_dob=same_dob,
            same_day_month=same_dm,
            year_delta=year_delta,
        )
        candidates.append((score, resolution, player, info))

    if not candidates:
        return IdentityMatch(None, "missing_after_global_check", "none", 0.0, ())

    candidates.sort(key=lambda item: item[0], reverse=True)
    top_score, resolution, player, _ = candidates[0]
    infos = tuple(item[3] for item in candidates[:5])
    margin = top_score - candidates[1][0] if len(candidates) > 1 else 999.0
    # If two plausible identities are close, do not auto-merge.  The caller can
    # record it for manual review rather than silently corrupting the database.
    if margin < 8.0:
        return IdentityMatch(None, "ambiguous_existing_candidates", "ambiguous", round(top_score, 3), infos)
    return IdentityMatch(player, resolution, "high" if resolution.startswith("global_") else "medium", round(top_score, 3), infos)
