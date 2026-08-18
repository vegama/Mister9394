from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ROUTE_SOURCE = ROOT / "frontend" / "src" / "football9394" / "navigationRoute.js"
REPORT = ROOT / "docs" / "qa" / "rc-navigation-history.json"


def browser_source() -> str:
    source = ROUTE_SOURCE.read_text(encoding="utf-8")
    source = source.replace("export const ", "const ").replace("export function ", "function ")
    return source


def harness() -> str:
    return f"""<!doctype html><html><body>
    <main id='state' tabindex='-1'></main>
    <script>(()=>{{
    {browser_source()}
    window.__m9394Route={{buildNavigationHash,parseNavigationHash,safeEntityTab}};
    function renderRoute(){{
      const route=parseNavigationHash();
      const node=document.getElementById('state');
      if(!node)return;
      node.dataset.route=JSON.stringify(route);
      node.textContent=route.target;
    }}
    window.__m9394RenderRoute=renderRoute;
    addEventListener('popstate', renderRoute);
    addEventListener('hashchange', renderRoute);
    renderRoute();
    }})();</script></body></html>"""


def route(page):
    raw = page.locator("#state").get_attribute("data-route") or "{}"
    return json.loads(raw)


def main() -> int:
    if not ROUTE_SOURCE.is_file():
        print(f"ERROR: falta {ROUTE_SOURCE}", file=sys.stderr)
        return 2
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    checks: dict[str, bool] = {}
    observations: dict[str, object] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = browser.new_page()
        page.set_content(harness())
        page.evaluate("history.replaceState({view:'home',m9394Depth:0},'', '#home'); __m9394RenderRoute()")
        checks["initial_home"] = route(page) == {"target": "home", "entity": None, "entityTab": ""}

        page.evaluate("history.pushState({view:'squad',m9394Depth:1},'', __m9394Route.buildNavigationHash('squad')); __m9394RenderRoute()")
        checks["section_push"] = route(page)["target"] == "squad" and page.evaluate("history.state.m9394Depth") == 1

        page.evaluate("""history.pushState(
          {view:'squad',entity:{type:'player',id:'123'},entityTab:'profile',m9394Depth:2},'',
          __m9394Route.buildNavigationHash('squad',{type:'player',id:'123'},{entityTab:'profile'})
        ); __m9394RenderRoute()""")
        page.evaluate("""history.replaceState(
          {...history.state,entityTab:'medical'},'',
          __m9394Route.buildNavigationHash('squad',{type:'player',id:'123'},{entityTab:'medical'})
        ); __m9394RenderRoute()""")
        current = route(page)
        checks["entity_and_tab_serialized"] = current == {"target": "squad", "entity": {"type": "player", "id": "123"}, "entityTab": "medical"}
        observations["entity_url"] = page.url

        # Document remount with the same URL/history is the source-level equivalent
        # of reconstructing Vue state after F5. The production E2E gate performs literal reload().
        before_url = page.url
        before_state = page.evaluate("history.state")
        page.set_content(harness())
        after_remount = route(page)
        checks["remount_reconstructs_url"] = page.url == before_url and after_remount == current
        checks["remount_preserves_history_state"] = page.evaluate("history.state") == before_state

        page.go_back(wait_until="commit", timeout=5000)
        page.wait_for_timeout(80)
        back = route(page)
        checks["real_browser_back"] = back == {"target": "squad", "entity": None, "entityTab": ""}
        observations["after_back"] = {"url": page.url, "route": back, "history": page.evaluate("history.state")}

        page.go_forward(wait_until="commit", timeout=5000)
        page.wait_for_timeout(80)
        forward = route(page)
        checks["real_browser_forward"] = forward == current
        observations["after_forward"] = {"url": page.url, "route": forward, "history": page.evaluate("history.state")}

        sanitized = page.evaluate("__m9394Route.safeEntityTab('medical notes')")
        checks["invalid_tab_sanitized"] = sanitized == ""
        encoded = page.evaluate("__m9394Route.buildNavigationHash('competitions',{type:'competition',id:'league:14'})")
        decoded = page.evaluate("h => __m9394Route.parseNavigationHash(h)", encoded)
        checks["entity_id_roundtrip"] = decoded["entity"] == {"type": "competition", "id": "league:14"}
        browser.close()

    report = {
        "kind": "source-route-browser-history-contract",
        "literal_production_f5": False,
        "note": "History API real en Chromium + remount documental. El reload() literal pertenece al gate E2E de frontend/dist.",
        "checks": checks,
        "observations": observations,
        "passed": all(checks.values()),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'} {name}")
    print(f"Report: {REPORT}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
