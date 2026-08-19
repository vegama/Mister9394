from __future__ import annotations

"""Historical player-name presentation helpers.

The database may preserve patronymics and source spellings for traceability, but
routine UI should use the same short ``given name + family name`` convention as
the rest of Míster 93/94.  This is especially relevant for Russian/ex-USSR
profiles whose BDFutbol full name includes a patronymic.
"""

import re
from typing import Any

_PATRONYMIC = re.compile(r"(?i)(?:ovich|evich|yevich|ovych|evych|yovych|ivych|ovitch|evitch|yevitch|ievitch|vitch|ich|ovna|evna|yevna)$")
_PATRONYMIC_MARKERS = {"oglu", "oğlu", "ogly"}


def looks_like_patronymic(token: str | None) -> bool:
    return bool(_PATRONYMIC.search(str(token or "").strip()))


def short_historical_display_name(player: dict[str, Any]) -> str:
    """Return a UI-friendly historical name without discarding full identity.

    Only removes a second given-name token when it has a patronymic shape.  This
    deliberately avoids treating every compound given name as Russian.
    """

    first = " ".join(str(player.get("first_name") or "").split())
    family = " ".join(str(player.get("surname1") or "").split())
    tokens = first.split()
    patronymic_tail = tokens[1:]
    has_patronymic = any(looks_like_patronymic(token) for token in patronymic_tail)
    has_marker = any(token.casefold() in _PATRONYMIC_MARKERS for token in patronymic_tail)
    if len(tokens) >= 2 and (has_patronymic or has_marker) and family:
        return f"{tokens[0]} {family}".strip()
    return " ".join(str(player.get("display_name") or f"{first} {family}").split()).strip()


def preserve_full_name_and_shorten(player: dict[str, Any]) -> bool:
    """Shorten a patronymic display name while preserving the historical full name."""

    short = short_historical_display_name(player)
    current = " ".join(str(player.get("display_name") or "").split()).strip()
    if not short or short == current:
        return False
    player.setdefault("historical_full_name", current)
    player["display_name"] = short
    transliterations = dict(player.get("name_transliterations") or {})
    transliterations.setdefault("historical_full", current)
    transliterations["project_display_v113"] = short
    player["name_transliterations"] = transliterations
    player["display_name_resolution"] = "short_ui_name_patronymic_preserved_v113"
    return True
