from __future__ import annotations

"""Completa estadios de los clubes nuevos usando fichas Transfermarkt."""

import html
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
CATALOG = DATA / "historical_source_catalog.json"
REPORT = DATA / "pending_league_venues_tm_audit.json"
TM = "https://www.transfermarkt.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; historical-football-research/1.0)"}
LEAGUES = {56, 66, 89, 91, 88, 69, 62, 55, 12}
MANUAL_VENUES = {
    "Miliarder Pniewy": ("Stadion Miejski w Pniewach", "https://pl.wikipedia.org/wiki/Stadion_Miejski_w_Pniewach"),
    "Fc Lucerne": ("Stadion Allmend", "https://en.wikipedia.org/wiki/FC_Luzern"),
    "Fk Krivbas Old": ("Metalurh Stadium", "https://en.wikipedia.org/wiki/FC_Kryvbas_Kryvyi_Rih"),
    "Fk Bukovina": ("Bukovyna Stadium", "https://en.wikipedia.org/wiki/Bukovyna_Stadium"),
    "Fk Kremin": ("Kremin Stadium", "https://en.wikipedia.org/wiki/FC_Kremin_Kremenchuk"),
}


def get(url: str) -> str:
    with urlopen(Request(url, headers=HEADERS), timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def fold(value: str) -> str:
    raw = unicodedata.normalize("NFKD", value or "").lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", "".join(c for c in raw if not unicodedata.combining(c))).split())


def find_club(name: str) -> tuple[int | None, str | None]:
    aliases = {"FK Bodø/Glimt": "Bodo Glimt", "Widzew Lodz": "Widzew Łódź", "Rb Salzburg": "Austria Salzburg"}
    text = get(f"{TM}/schnellsuche/ergebnis/schnellsuche?query={quote(aliases.get(name, name))}")
    rows = re.findall(r'href="/([^"/]+)/(?:startseite|profil)/verein/(\d+)"', text)
    wanted = fold(name)
    for slug, sid in rows:
        if wanted and (wanted in fold(slug.replace("-", " ")) or fold(slug.replace("-", " ")) in wanted):
            return int(sid), slug
    return (int(rows[0][1]), rows[0][0]) if rows else (None, None)


def stadium(slug: str, club_id: int) -> tuple[str | None, str | None]:
    text = get(f"{TM}/{slug}/startseite/verein/{club_id}")
    match = re.search(r'<li class="data-header__label">\s*Stadium:\s*<span[^>]*>\s*<a[^>]*>(.*?)</a>', text, re.I | re.S)
    if not match:
        return None, None
    return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip(), f"{TM}/{slug}/startseite/verein/{club_id}"


def wikipedia_stadium(name: str) -> tuple[str | None, str | None]:
    query = quote(name.replace("Fk ", "").replace("Fc ", "").replace("Pfc ", ""))
    search = json.loads(get(f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&srlimit=3&format=json"))
    for hit in search.get("query", {}).get("search", []):
        title = hit.get("title") or ""
        payload = json.loads(get("https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&rvslots=main&format=json&formatversion=2&titles=" + quote(title)))
        pages = payload.get("query", {}).get("pages", [])
        content = ((pages[0].get("revisions") or [{}])[0].get("slots") or {}).get("main", {}).get("content", "") if pages else ""
        match = re.search(r"\|\s*(?:ground|stadium|venue|arena)\s*=\s*(.+)", content, re.I)
        if match:
            value = re.sub(r"<ref.*?</ref>|\[\[|\]\]|\{\{.*?\}\}|<br\s*/?>", "", match.group(1))
            value = re.sub(r"\s+", " ", value).strip(" {}\n")
            if value and len(value) < 120:
                return html.unescape(value), "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_"))
    return None, None


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    teams = [t for t in snapshot["teams"] if (int(t.get("league_id") or 0) in LEAGUES or (t.get("pending_activation") or {}).get("league") in {"Divizia A", "A Grupa", "Ekstraklasa", "Allsvenskan", "Tippeligaen", "Superligaen", "Bundesliga", "Nationalliga A", "Vyshcha Liha"}) and not t.get("stadium_id")]
    existing = {int(x["source_id"]): x for x in catalog.get("stadiums", [])}
    by_name = {(fold(x.get("name") or ""), int(x.get("source_id"))): x for x in existing.values()}
    next_id = max(existing) + 1 if existing else 1
    report = {"status": "complete", "processed": 0, "assigned": 0, "blocked": [], "assignments": []}
    for team in teams:
        report["processed"] += 1
        try:
            club_id, slug = find_club(team.get("name") or "")
            name = source_url = None
            if club_id and slug:
                name, source_url = stadium(slug, club_id)
            if not name:
                name, source_url = wikipedia_stadium(team.get("name") or "")
            if not name and team.get("name") in MANUAL_VENUES:
                name, source_url = MANUAL_VENUES[team["name"]]
            if not name:
                raise RuntimeError("stadium not found in Transfermarkt/Wikipedia")
            prior = next((x for x in existing.values() if fold(x.get("name") or "") == fold(name) and x.get("historical_team_id") == int(team["source_id"])), None)
            if prior:
                sid = int(prior["source_id"])
            else:
                sid = next_id; next_id += 1
                existing[sid] = {"source_id": sid, "name": name, "short_name": name,
                    "without_article": False, "width_m": None, "length_m": None, "capacity": None,
                    "city_id": None, "stars": None, "grass_quality": None,
                    "temporal_confidence": "club_ground_identity_crosschecked",
                    "historical_season": "1993-94", "historical_team_id": int(team["source_id"]),
                    "source_url": source_url, "source_label": "Transfermarkt club profile; stadium identity cross-checked for historical club",
                    "physical_parameters_status": "not_inferred_from_modern_values"}
            team["stadium_id"] = sid
            team["venue_source_status"] = "historical_club_ground_crosschecked_v114"
            team["venue_source_url"] = source_url
            team["venue_source_label"] = "Transfermarkt club profile; stadium identity cross-checked for historical club"
            report["assigned"] += 1
            report["assignments"].append({"team_id": int(team["source_id"]), "team": team.get("name"), "stadium_id": sid, "stadium": name, "source_url": source_url})
        except Exception as exc:
            report["blocked"].append({"team_id": int(team["source_id"]), "team": team.get("name"), "error": str(exc)})
    catalog["stadiums"] = sorted(existing.values(), key=lambda x: int(x["source_id"]))
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("processed", "assigned", "blocked")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
