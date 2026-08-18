from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
HARNESS = FRONTEND / "qa" / "rc-shell-harness.html"
DEFAULT_OUT = ROOT / "docs" / "visual-qa" / "rc-browser-matrix"

MATRIX = [
    ("1920x1080", 1920, 1080, 100),
    ("1366x768", 1366, 768, 100),
    ("1280x720", 1280, 720, 100),
    ("1024x768", 1024, 768, 100),
    # Browser zoom 200% is represented as the equivalent CSS layout viewport.
    ("1920x1080-z200", 960, 540, 200),
    ("1366x768-z200", 683, 384, 200),
    ("1280x720-z200", 640, 360, 200),
    ("1024x768-z200", 512, 384, 200),
]


def harness_html() -> str:
    html = HARNESS.read_text(encoding="utf-8")
    core = (FRONTEND / "src" / "styles" / "core.css").read_text(encoding="utf-8")
    style_order = [
        "football9394-tokens.css",
        "football9394-shell.css",
        "football9394-primitives.css",
        "football9394-workspaces.css",
        "football9394-depth.css",
        "football9394-product.css",
        "football9394-dark.css",
    ]
    manager = "\n".join((FRONTEND / "src" / "styles" / name).read_text(encoding="utf-8") for name in style_order)
    html = html.replace('<link rel="stylesheet" href="../src/styles/core.css" />', f"<style>{core}</style>")
    html = html.replace('<link rel="stylesheet" href="../src/styles/football9394-manager.css" />', f"<style>{manager}</style>")
    return html


def rect(page, selector: str):
    return page.locator(selector).bounding_box()


def inside_viewport(box: dict | None, width: int, height: int, *, tolerance: int = 2) -> bool:
    if not box:
        return False
    return (
        box["x"] >= -tolerance
        and box["y"] >= -tolerance
        and box["x"] + box["width"] <= width + tolerance
        and box["y"] + box["height"] <= height + tolerance
    )


def audit_case(page, name: str, width: int, height: int, zoom: int, out_dir: Path, html: str) -> dict:
    page.set_viewport_size({"width": width, "height": height})
    page.set_content(html, wait_until="load")

    metrics = page.evaluate(
        """() => ({
          clientWidth: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
          clientHeight: document.documentElement.clientHeight,
          scrollHeight: document.documentElement.scrollHeight,
          activeTag: document.activeElement?.tagName || ''
        })"""
    )
    horizontal_overflow = metrics["scrollWidth"] > metrics["clientWidth"] + 1
    continue_box = rect(page, "#continue-button")
    topbar_box = rect(page, ".manager-topbar")
    main_box = rect(page, "#m9394-main")
    nav_box = rect(page, ".manager-sidebar")

    # Keyboard accessibility: first Tab reveals the skip link, Enter moves focus to main.
    page.keyboard.press("Tab")
    skip_focused = page.evaluate("document.activeElement?.id === 'skip-link'")
    page.keyboard.press("Enter")
    page.wait_for_timeout(50)
    skip_target_focused = page.evaluate("document.activeElement?.id === 'm9394-main'")

    # Command palette must open from keyboard and Esc must return focus to the opener.
    page.keyboard.press("Control+K")
    page.wait_for_timeout(50)
    command_open = page.locator("#command-overlay").evaluate("el => el.classList.contains('qa-command-open')")
    command_input_focused = page.evaluate("document.activeElement?.id === 'command-input'")
    page.keyboard.press("Escape")
    command_focus_returned = page.evaluate("document.activeElement?.id === 'open-command'")

    # Error and slow-operation states must stay within the viewport.
    page.locator("#error-state").evaluate("el => el.classList.remove(\'qa-state-hidden\')")
    error_box = rect(page, "#error-state")
    error_inside = inside_viewport(error_box, width, height)
    page.locator("#error-state").evaluate("el => el.classList.add(\'qa-state-hidden\')")
    page.locator("#slow-state").evaluate("el => el.classList.remove(\'qa-state-hidden\')")
    slow_box = rect(page, "#slow-state")
    slow_inside = inside_viewport(slow_box, width, height)

    page.locator("#slow-state").evaluate("el => el.classList.add(\'qa-state-hidden\')")
    screenshot = out_dir / f"{name}.png"
    page.screenshot(path=str(screenshot), full_page=False)

    mobile = width <= 700
    mobile_nav_at_bottom = True
    mobile_nav_single_row = True
    topbar_at_top = True
    if mobile:
        mobile_nav_at_bottom = bool(nav_box and abs((nav_box["y"] + nav_box["height"]) - height) <= 3)
        mobile_nav_single_row = bool(nav_box and nav_box["height"] <= 78)
        topbar_at_top = bool(topbar_box and topbar_box["y"] <= 2)

    checks = {
        "no_global_horizontal_overflow": not horizontal_overflow,
        "continue_visible": inside_viewport(continue_box, width, height),
        "topbar_visible": bool(topbar_box and topbar_box["y"] >= -2 and topbar_box["y"] < height),
        "main_has_width": bool(main_box and main_box["width"] > 100),
        "navigation_visible": bool(nav_box and nav_box["width"] > 40 and nav_box["height"] > 40),
        "mobile_nav_at_bottom": mobile_nav_at_bottom,
        "mobile_nav_single_row": mobile_nav_single_row,
        "topbar_at_top": topbar_at_top,
        "skip_link_focus": bool(skip_focused and skip_target_focused),
        "command_keyboard": bool(command_open and command_input_focused and command_focus_returned),
        "error_state_in_viewport": error_inside,
        "slow_state_in_viewport": slow_inside,
    }
    return {
        "name": name,
        "physical_reference": f"{width * (2 if zoom == 200 else 1)}x{height * (2 if zoom == 200 else 1)}",
        "layout_viewport": {"width": width, "height": height},
        "zoom_percent": zoom,
        "metrics": metrics,
        "checks": checks,
        "passed": all(checks.values()),
        "screenshot": str(screenshot.relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Matriz Chromium del shell/estados RC de Míster 93/94")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    args = parser.parse_args()
    if not HARNESS.is_file():
        print(f"ERROR: falta {HARNESS}", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)

    html = harness_html()
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=args.chromium, args=["--no-sandbox"])
        context = browser.new_context(locale="es-ES", reduced_motion="reduce")
        for case in MATRIX:
            page = context.new_page()
            results.append(audit_case(page, *case, out_dir=args.out, html=html))
            page.close()
        browser.close()
    report = {
        "kind": "source-css-shell-browser-matrix",
        "production_bundle_certified": False,
        "note": "Carga CSS real + DOM representativo. El E2E del bundle de producción sigue siendo un gate separado.",
        "cases": results,
        "passed": all(row["passed"] for row in results),
    }
    report_path = args.out / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for row in results:
        status = "PASS" if row["passed"] else "FAIL"
        failed = [k for k, ok in row["checks"].items() if not ok]
        print(f"{status:4} {row['name']:<18} " + ("" if not failed else "· " + ", ".join(failed)))
    print(f"Report: {report_path}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
