from __future__ import annotations

"""Cross-check the Míster 93/94 world against OpenFootball public-domain data.

This tool is deliberately conservative.  Current OpenFootball club/stadium data is
used for identity, aliases and review candidates only.  An automatic "missing club"
warning is high-confidence only when it comes from an exact 1993/94 match file.

The command is network-resumable and meant to be runnable from a normal home PC.
Downloaded repository ZIPs are cached under data/football9394/openfootball_cache.
"""

import argparse
from datetime import datetime, timezone
from difflib import SequenceMatcher
import io
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
CATALOG = DATA / "historical_source_catalog.json"
CONFIG = DATA / "openfootball_sources_1993_94.json"
CACHE = DATA / "openfootball_cache"
DEFAULT_REPORT = DATA / "openfootball_audit_1993_94.json"
HEADERS = {"User-Agent": "Mister9394OpenFootballAudit/1.0 (+personal historical game)"}
NETWORK_TIMEOUT = 30.0
SEASON_MARKERS = ("1993-94", "1993_94", "1993/94", "1993-1994", "1993_1994")
STOP = {
    "fc", "cf", "afc", "ac", "sc", "as", "fk", "sk", "sv", "rc", "cd", "ud", "sd",
    "club", "football", "futbol", "calcio", "de", "del", "la", "el", "the", "pae", "pfc",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = text.replace("&", " and ")
    tokens = re.findall(r"[a-z0-9]+", text)
    return " ".join(tok for tok in tokens if tok not in STOP)


def similarity(a: str, b: str) -> float:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


def fetch(url: str, timeout: float | None = None) -> bytes:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=NETWORK_TIMEOUT if timeout is None else timeout) as resp:  # nosec - configured public-data sources
        return resp.read()


def repo_zip(repo: dict[str, Any], refresh: bool) -> tuple[bytes | None, str | None]:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{repo['name']}.zip"
    if path.exists() and not refresh:
        return path.read_bytes(), None
    try:
        payload = fetch(repo["zip_url"])
        path.write_bytes(payload)
        return payload, None
    except Exception as exc:
        if path.exists():
            return path.read_bytes(), f"refresh_failed_using_cache: {exc}"
        return None, str(exc)


def zip_text_files(payload: bytes) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        for info in zf.infolist():
            if info.is_dir() or not info.filename.lower().endswith((".txt", ".md", ".csv")):
                continue
            try:
                text = zf.read(info).decode("utf-8", errors="replace")
            except Exception:
                continue
            out.append((info.filename, text))
    return out


def parse_clubs(files: Iterable[tuple[str, str]]) -> list[dict[str, Any]]:
    clubs: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for path, text in files:
        lower = path.lower()
        if not lower.endswith(".clubs.txt") or ".history." in lower or ".props." in lower:
            continue
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith(("#", "=", "//")):
                continue
            if line.startswith("|"):
                if current:
                    clean = line.split("#", 1)[0]
                    for alias in clean.split("|"):
                        alias = re.sub(r"\[[a-z]{2}\]", "", alias, flags=re.I).replace("$$", "").strip()
                        if alias and alias not in current["aliases"]:
                            current["aliases"].append(alias)
                continue
            if raw[:1].isspace() or line.startswith(("i)", "ii)", "iii)", "iv)")):
                continue
            clean = line.split("#", 1)[0].strip()
            canonical = clean.split(",", 1)[0].strip()
            if not canonical or len(canonical) < 2:
                continue
            stadium = None
            m = re.search(r"@\s*([^,›#]+)", clean)
            if m:
                stadium = m.group(1).strip()
            current = {"name": canonical, "aliases": [], "stadium": stadium, "file": path}
            clubs.append(current)
    return clubs


def parse_competitions(files: Iterable[tuple[str, str]]) -> list[dict[str, Any]]:
    """Parse OpenFootball regional league/cup catalog files.

    Catalog rows are identity/discovery metadata, not proof that a competition
    existed in 1993-94.  The temporal qualifier is preserved when present so a
    later review can reject modern-only competitions without guesswork.
    """
    out: list[dict[str, Any]] = []
    current_section: str | None = None
    current: dict[str, Any] | None = None
    for path, text in files:
        low = path.lower()
        if not low.endswith("leagues.txt"):
            continue
        for raw in text.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            section_match = re.match(r"^=\s*(.*?)\s*=", stripped)
            if section_match:
                current_section = section_match.group(1).strip()
                current = None
                continue
            if stripped.startswith(("#", "//")):
                continue
            if stripped.startswith("|"):
                if current:
                    alias = stripped[1:].split("#", 1)[0].replace("$$", "").strip()
                    alias = re.sub(r"\[[a-z]{2}\]", "", alias, flags=re.I).strip()
                    if alias and alias not in current["aliases"]:
                        current["aliases"].append(alias)
                continue
            # Records are code + optional season validity + human-readable name.
            # Ignore prose / tables that do not look like a compact code.
            clean = stripped.split("##", 1)[0].split("#", 1)[0].strip()
            parts = clean.split()
            if len(parts) < 2 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", parts[0]):
                current = None
                continue
            code = parts.pop(0)
            validity = None
            if parts and re.fullmatch(r"\d{4}(?:/\d{2})?(?:-\d{4}(?:/\d{2})?)?|-?\d{4}(?:/\d{2})?-", parts[0]):
                validity = parts.pop(0)
            name = " ".join(parts).strip()
            if not name or len(name) < 2:
                current = None
                continue
            if code[0].isdigit():
                kind = "league"
            elif code.startswith("cup") or code in {"pokal", "copa"}:
                kind = "cup"
            elif code.startswith("super"):
                kind = "supercup"
            elif code.startswith(("uefa", "euro", "world.club", "lib", "copa.")):
                kind = "international_club"
            else:
                kind = "other"
            current = {
                "section": current_section,
                "code": code,
                "validity": validity,
                "name": name,
                "aliases": [],
                "kind": kind,
                "file": path,
            }
            out.append(current)
    return out


def _best_competition_score(remote: dict[str, Any], local_names: list[str]) -> tuple[float, str | None]:
    candidates = [remote.get("name") or "", *(remote.get("aliases") or [])]
    best_score = 0.0
    best_local: str | None = None
    for local in local_names:
        score = max((similarity(local, candidate) for candidate in candidates), default=0.0)
        if score > best_score:
            best_score, best_local = score, local
    return best_score, best_local


def competition_catalog_review(snapshot: dict[str, Any], competitions: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    local_names = [str(x.get("name") or "") for x in snapshot.get("leagues", [])]
    local_names += [str(x.get("name") or "") for x in snapshot.get("tournaments", [])]
    local_names += [str(x.get("short_name") or "") for x in snapshot.get("tournaments", []) if x.get("short_name")]
    represented = {str(x.get("country") or "") for x in snapshot.get("leagues", []) if x.get("country")}
    section_map = config.get("country_section_map", {})
    sections: dict[str, str] = {}
    for local_country in represented:
        for section in section_map.get(local_country, [local_country]):
            sections[norm(section)] = local_country

    known_codes = config.get("known_competition_code_map", {})
    missing_cups: list[dict[str, Any]] = []
    missing_supercups: list[dict[str, Any]] = []
    league_review: list[dict[str, Any]] = []
    matched: list[dict[str, Any]] = []
    for remote in competitions:
        section = str(remote.get("section") or "")
        country = sections.get(norm(section))
        if not country and norm(section) != norm("International"):
            continue
        code = str(remote.get("code") or "")
        if code in known_codes:
            matched.append({"openfootball": remote, "local_mapping": known_codes[code], "match": "configured_code_identity"})
            continue
        score, local = _best_competition_score(remote, local_names)
        row = {"country": country or "International", "openfootball": remote, "best_local": local, "best_local_score": round(score, 4)}
        if score >= 0.88:
            row["status"] = "name_or_alias_match"
            matched.append(row)
            continue
        row["status"] = "catalog_only_historical_verification_required"
        if remote.get("kind") == "cup" and country:
            missing_cups.append(row)
        elif remote.get("kind") == "supercup" and country:
            missing_supercups.append(row)
        elif remote.get("kind") == "league" and country:
            league_review.append(row)

    # A current catalog is excellent for discovering what to investigate, but
    # not sufficient to assert a 1993-94 omission.  Keep these lists separate
    # from exact-season high-confidence gaps.
    return {
        "catalog_records_loaded": len(competitions),
        "likely_missing_domestic_cups_to_verify_1993_94": missing_cups,
        "possible_missing_supercups_to_verify_1993_94": missing_supercups,
        "additional_league_levels_or_renames_to_review": league_review,
        "matched_or_mapped_competitions": matched,
    }


def club_index(clubs: list[dict[str, Any]]) -> dict[str, list[int]]:
    idx: dict[str, list[int]] = {}
    for i, club in enumerate(clubs):
        for name in [club["name"], *club.get("aliases", [])]:
            n = norm(name)
            if n:
                idx.setdefault(n, []).append(i)
    return idx


def best_club_match(name: str, clubs: list[dict[str, Any]], idx: dict[str, list[int]]) -> dict[str, Any] | None:
    n = norm(name)
    exact = idx.get(n, [])
    if len(exact) == 1:
        c = clubs[exact[0]]
        return {"status": "alias_exact", "score": 1.0, **c}
    if len(exact) > 1:
        return {"status": "ambiguous_exact", "score": 1.0, "candidates": [clubs[i]["name"] for i in exact[:8]]}
    scored: list[tuple[float, int, str]] = []
    for i, club in enumerate(clubs):
        score = max(similarity(name, candidate) for candidate in [club["name"], *club.get("aliases", [])])
        if score >= 0.76:
            scored.append((score, i, club["name"]))
    scored.sort(reverse=True)
    if not scored:
        return None
    best = scored[0]
    second = scored[1][0] if len(scored) > 1 else 0.0
    if best[0] >= 0.91 and best[0] - second >= 0.035:
        return {"status": "fuzzy_high", "score": round(best[0], 4), **clubs[best[1]]}
    return {"status": "review", "score": round(best[0], 4), "candidates": [{"name": clubs[i]["name"], "score": round(s, 4)} for s, i, _ in scored[:5]]}


def historical_files(files: Iterable[tuple[str, str]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for path, text in files:
        lowpath = path.lower()
        head = "\n".join(text.splitlines()[:30]).lower()
        if any(marker.lower() in lowpath or marker.lower() in head for marker in SEASON_MARKERS):
            title = next((line.lstrip("= ").strip() for line in text.splitlines() if line.strip().startswith("=")), "")
            found.append({"path": path, "title": title, "bytes": len(text.encode("utf-8"))})
    return found


SCORE_RE = re.compile(r"^\s*(.+?)\s+(\d{1,2})\s*[-–:]\s*(\d{1,2})\s+(.+?)\s*$")
SCORE_PARENS_RE = re.compile(r"\s+\(.*\)\s*$")


def parse_match_teams(text: str) -> set[str]:
    teams: set[str] = set()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("=", "▪")):
            continue
        line = SCORE_PARENS_RE.sub("", line)
        match = SCORE_RE.match(line)
        if match:
            home, away = match.group(1).strip(), match.group(4).strip()
            # Avoid interpreting dates/tables as football clubs.
            if any(ch.isalpha() for ch in home) and any(ch.isalpha() for ch in away):
                teams.update((home, away))
    return teams


def crosscheck_exact_source(source: dict[str, Any], snapshot: dict[str, Any], clubs: list[dict[str, Any]], idx: dict[str, list[int]]) -> dict[str, Any]:
    league_id = int(source["league_source_id"])
    local_teams = [t for t in snapshot.get("teams", []) if int(t.get("league_id") or 0) == league_id]
    try:
        text = fetch(source["url"]).decode("utf-8", errors="replace")
        network_error = None
    except Exception as exc:
        text = ""
        network_error = str(exc)
    remote_names = sorted(parse_match_teams(text)) if text else []
    local_norm = {norm(t.get("name")): t for t in local_teams}
    remote_mapped: list[dict[str, Any]] = []
    remote_missing: list[dict[str, Any]] = []
    for remote in remote_names:
        if norm(remote) in local_norm:
            remote_mapped.append({"openfootball": remote, "local": local_norm[norm(remote)]["name"], "match": "normalized_exact"})
            continue
        match = best_club_match(remote, clubs, idx) if clubs else None
        local_candidate = None
        local_score = 0.0
        for t in local_teams:
            score = similarity(remote, t.get("name"))
            if score > local_score:
                local_score, local_candidate = score, t
        if local_candidate and local_score >= 0.88:
            remote_mapped.append({"openfootball": remote, "local": local_candidate["name"], "match": "fuzzy_local", "score": round(local_score, 4)})
        else:
            remote_missing.append({"openfootball": remote, "best_local": local_candidate.get("name") if local_candidate else None, "best_local_score": round(local_score, 4), "openfootball_identity": match})
    local_unseen: list[dict[str, Any]] = []
    for t in local_teams:
        best = max((similarity(t.get("name"), r) for r in remote_names), default=0.0)
        if remote_names and best < 0.88:
            local_unseen.append({"local": t.get("name"), "best_remote_score": round(best, 4)})
    return {
        "key": source.get("key"),
        "league_source_id": league_id,
        "url": source.get("url"),
        "network_error": network_error,
        "remote_team_count": len(remote_names),
        "local_team_count": len(local_teams),
        "mapped": remote_mapped,
        "remote_not_in_local_high_confidence_review": remote_missing,
        "local_not_seen_in_remote_review": local_unseen,
    }


def audit(refresh: bool = False, max_repo_downloads: int | None = None) -> dict[str, Any]:
    snapshot = load_json(SNAPSHOT)
    config = load_json(CONFIG)
    repo_reports: list[dict[str, Any]] = []
    club_files: list[tuple[str, str]] = []
    league_catalog_files: list[tuple[str, str]] = []
    downloaded = 0
    for repo in config.get("repositories", []):
        if max_repo_downloads is not None and downloaded >= max_repo_downloads:
            repo_reports.append({"name": repo["name"], "status": "not_attempted_limit"})
            continue
        payload, warning = repo_zip(repo, refresh)
        downloaded += 1
        if payload is None:
            repo_reports.append({"name": repo["name"], "status": "network_failed_no_cache", "error": warning, "url": repo["url"]})
            continue
        try:
            files = zip_text_files(payload)
        except Exception as exc:
            repo_reports.append({"name": repo["name"], "status": "invalid_zip", "error": str(exc), "url": repo["url"]})
            continue
        if repo["name"] == "clubs":
            club_files.extend(files)
        if repo["name"] == "leagues":
            league_catalog_files.extend(files)
        hist = historical_files(files)
        repo_reports.append({
            "name": repo["name"],
            "status": "cached_or_downloaded",
            "warning": warning,
            "text_files": len(files),
            "historical_1993_94_files": hist,
            "historical_1993_94_count": len(hist),
            "url": repo["url"],
        })

    clubs = parse_clubs(club_files)
    competitions = parse_competitions(league_catalog_files)
    competition_review = competition_catalog_review(snapshot, competitions, config)
    idx = club_index(clubs)
    team_matches: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    synthetic = 0
    for team in snapshot.get("teams", []):
        name = team.get("name") or ""
        if name.startswith("Otros-"):
            synthetic += 1
            continue
        if not clubs:
            continue
        match = best_club_match(name, clubs, idx)
        row = {"team_id": team.get("source_id"), "name": name, "league_id": team.get("league_id")}
        if match and match.get("status") in {"alias_exact", "fuzzy_high"}:
            row["openfootball"] = match
            team_matches.append(row)
        else:
            row["openfootball"] = match
            unmatched.append(row)

    exact = [crosscheck_exact_source(src, snapshot, clubs, idx) for src in config.get("exact_historical_sources", [])]
    leagues = []
    country_map = config.get("country_repo_map", {})
    repo_by_name = {r["name"]: r for r in repo_reports}
    for league in snapshot.get("leagues", []):
        country = league.get("country") or ""
        repo_name = country_map.get(country)
        repo_info = repo_by_name.get(repo_name, {}) if repo_name else {}
        leagues.append({
            "league_id": league.get("source_id"),
            "country": country,
            "name": league.get("name"),
            "team_count": league.get("team_count"),
            "openfootball_repo": repo_name,
            "repo_available": repo_info.get("status") == "cached_or_downloaded",
            "repo_1993_94_file_count": repo_info.get("historical_1993_94_count", 0),
            "status": "exact_source_configured" if any(int(s.get("league_source_id", -1)) == int(league.get("source_id")) for s in config.get("exact_historical_sources", [])) else ("season_candidates_available_for_review" if repo_info.get("historical_1993_94_count", 0) else "identity_reference_only_or_no_1993_94_found"),
        })

    high_confidence_missing = []
    for row in exact:
        high_confidence_missing.extend({"source": row["key"], **candidate} for candidate in row["remote_not_in_local_high_confidence_review"])

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "season": snapshot.get("season"),
        "policy": config.get("policy"),
        "summary": {
            "local_leagues": len(snapshot.get("leagues", [])),
            "local_tournaments": len(snapshot.get("tournaments", [])),
            "local_teams": len(snapshot.get("teams", [])),
            "synthetic_other_teams_skipped": synthetic,
            "openfootball_club_records_loaded": len(clubs),
            "openfootball_competition_catalog_records_loaded": len(competitions),
            "catalog_domestic_cup_candidates_to_verify": len(competition_review["likely_missing_domestic_cups_to_verify_1993_94"]),
            "club_identity_audit_status": "available" if clubs else "source_unavailable_or_not_downloaded",
            "local_clubs_matched_by_identity_or_alias": len(team_matches),
            "local_clubs_needing_identity_review": len(unmatched),
            "high_confidence_missing_clubs_from_exact_1993_94_sources": len(high_confidence_missing),
            "repositories_with_1993_94_candidates": sum(1 for r in repo_reports if r.get("historical_1993_94_count", 0)),
        },
        "repositories": repo_reports,
        "league_coverage": leagues,
        "exact_season_crosschecks": exact,
        "competition_catalog_review": competition_review,
        "high_confidence_missing_clubs": high_confidence_missing,
        "club_identity_matches": team_matches,
        "club_identity_review": unmatched,
        "notes": [
            "A current OpenFootball club/stadium row is never enough to rewrite a 1993-94 fact.",
            "Use exact_season_crosschecks/high_confidence_missing_clubs first when deciding whether the game is missing a club.",
            "club_identity_review contains name/alias mismatches and is not proof that a club is missing.",
            "Repository 1993-94 files are discovery candidates; inspect their competition scope before importing anything.",
            "competition_catalog_review uses current league/cup identity metadata only; every apparent missing cup/supercup/league requires 1993-94 verification before implementation.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Míster 93/94 against OpenFootball")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--refresh", action="store_true", help="redownload repo ZIPs instead of using cache")
    parser.add_argument("--max-repos", type=int, help="debug/offline-friendly cap on repository downloads")
    parser.add_argument("--timeout", type=float, default=30.0, help="network timeout per request in seconds")
    args = parser.parse_args()
    global NETWORK_TIMEOUT
    NETWORK_TIMEOUT = max(1.0, float(args.timeout))
    report = audit(refresh=args.refresh, max_repo_downloads=args.max_repos)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
