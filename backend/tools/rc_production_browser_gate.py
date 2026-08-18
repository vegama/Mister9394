from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "frontend" / "dist" / "index.html"
REPORT = ROOT / "docs" / "qa" / "rc-production-browser.json"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_health(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("El servidor integrado no respondió al healthcheck.")


def no_global_overflow(page) -> bool:
    return bool(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"))


def main() -> int:
    parser = argparse.ArgumentParser(description="E2E Chromium del bundle real de Míster 93/94")
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)

    if not DIST.is_file():
        report = {
            "kind": "production-browser-e2e",
            "status": "blocked",
            "reason": "Falta frontend/dist/index.html. Ejecuta npm ci && npm run build antes del RC E2E.",
            "passed": False,
        }
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("BLOCKED: falta frontend/dist/index.html")
        return 2

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    checks: dict[str, bool] = {}
    observations: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="m9394-rc-") as tmp:
        tmp_path = Path(tmp)
        env = os.environ.copy()
        env["MISTER9394_FRONTEND_DIST"] = str(DIST.parent)
        env["MISTER9394_SAVE_DIR"] = str(tmp_path / "saves")
        env["MISTER9394_BACKUP_DIR"] = str(tmp_path / "backups")
        env["MISTER9394_LOG_DIR"] = str(tmp_path / "logs")
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.football9394.webapp:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            wait_health(f"{base}/api/football9394/health")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, executable_path=args.chromium, args=["--no-sandbox"])
                context = browser.new_context(locale="es-ES", reduced_motion="reduce")
                page = context.new_page()
                page_errors: list[str] = []
                console_errors: list[str] = []
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                try:
                    page.goto(base, wait_until="networkidle", timeout=30000)
                except PlaywrightError as exc:
                    text = str(exc)
                    if "ERR_BLOCKED_BY_ADMINISTRATOR" in text:
                        report = {
                            "kind": "production-browser-e2e",
                            "status": "environment-blocked",
                            "reason": "Chromium del entorno bloquea navegación HTTP local por política. Ejecuta este gate en un entorno sin esa política.",
                            "passed": False,
                        }
                        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        print("BLOCKED_ENV: Chromium bloquea localhost por política")
                        browser.close()
                        return 3
                    raise

                checks["bundle_loads"] = page.locator("body").count() == 1
                if page.locator(".career-setup").count():
                    page.locator("button.start-career").click()
                    page.locator(".manager-topbar").wait_for(state="visible", timeout=30000)
                checks["career_reaches_shell"] = page.locator(".manager-topbar").is_visible()
                checks["first_run_context"] = page.locator(".first-run-guide").count() > 0

                for label, width, height in [("1920",1920,1080),("1366",1366,768),("1280",1280,720),("1024",1024,768),("1024-z200",512,384)]:
                    page.set_viewport_size({"width": width, "height": height})
                    page.wait_for_timeout(80)
                    checks[f"overflow_{label}"] = no_global_overflow(page)
                    checks[f"continue_{label}"] = page.locator(".continue-button").is_visible()

                # Expert path: command palette reaches Mercado in one keyboard action + Enter.
                page.keyboard.press("Control+K")
                palette = page.locator(".command-palette")
                checks["command_palette_keyboard"] = palette.is_visible()
                if palette.is_visible():
                    field = palette.locator("input")
                    field.fill("Mercado")
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(120)
                checks["expert_market_route"] = "#market" in page.url

                # Real browser Back / Forward / F5 over production shell.
                page.get_by_role("button", name="Plantilla", exact=True).click()
                page.wait_for_timeout(100)
                squad_url = page.url
                page.get_by_role("button", name="Mercado", exact=True).click()
                page.wait_for_timeout(100)
                market_url = page.url
                page.go_back(wait_until="commit")
                page.wait_for_timeout(120)
                checks["back_restores_route"] = page.url == squad_url
                page.go_forward(wait_until="commit")
                page.wait_for_timeout(120)
                checks["forward_restores_route"] = page.url == market_url
                page.reload(wait_until="networkidle", timeout=30000)
                checks["f5_restores_route"] = page.url == market_url and page.locator(".manager-topbar").is_visible()

                checks["no_page_errors"] = not page_errors
                checks["no_console_errors"] = not console_errors
                observations["page_errors"] = page_errors
                observations["console_errors"] = console_errors
                browser.close()
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    report = {
        "kind": "production-browser-e2e",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "observations": observations,
        "passed": all(checks.values()),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'} {key}")
    print(f"Report: {args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
