from __future__ import annotations

"""Gate del bucle jugable: juega partidos de verdad sobre el bundle compilado.

Los gates existentes (producción, navegación, personas, red) cubren la
periferia del producto: shell, rutas, reflow, feedback y errores. Ninguno
llegaba a jugar un partido, y por eso un fallo que dejaba el juego sin su
bucle central podía convivir con 58/58 en verde.

El fallo real que motivó este gate: ``live/start`` y ``live/advance`` omiten
a propósito el snapshot de carrera para mantener ligero el bucle de partido
(contrato de rendimiento v115). El frontend lo leía sin comprobar, lanzaba
``TypeError`` y el ``catch`` lo degradaba a un aviso: la previa no abría y el
minuto nunca avanzaba. Ningún test de backend podía detectarlo porque la API
respondía 200.

Este gate recorre el bucle como una persona: crea carrera, avanza al día de
partido, abre la previa, juega minuto a minuto hasta el descanso, reanuda,
llega al final y repite jornadas. Comprueba que el minuto progresa de verdad,
que el partido termina y que no aparece ningún error de página o consola en
todo el recorrido.
"""

import argparse
import json
import os
import re
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
REPORT = ROOT / "docs" / "qa" / "rc-playable-loop.json"

# El primer partido se juega minuto a minuto porque es el camino que se rompió;
# los siguientes se resuelven por resultado para cubrir varias jornadas sin
# alargar el gate.
LIVE_MATCHES = 1
SIMULATED_MATCHES = 3


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_health(url: str, timeout: float = 25.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("El servidor integrado no respondió al healthcheck.")


def current_minute(page) -> int:
    """Minuto visible del marcador, o -1 si todavía no hay marcador."""
    match = re.search(r"(\d+)'", page.locator("body").inner_text())
    return int(match.group(1)) if match else -1


def match_state(page) -> str:
    text = page.locator("body").inner_text()
    for state in ("FINAL", "DESCANSO", "EN JUEGO"):
        if state in text:
            return state
    return "—"


def click_if_present(page, name: str, *, exact: bool = False, timeout: int = 4000) -> bool:
    target = page.get_by_role("button", name=name, exact=exact)
    if target.count() == 0:
        return False
    try:
        target.first.click(timeout=timeout)
        return True
    except PlaywrightError:
        return False


def reach_matchday(page) -> bool:
    """Pulsa Continuar hasta que el día de partido esté disponible.

    Continuar se deshabilita mientras el mundo avanza, así que hay que esperar
    a que vuelva a estar operativo entre pulsaciones en lugar de abandonar al
    primer clic que no entra.
    """
    for _ in range(60):
        if page.get_by_role("button", name=re.compile("Ir al partido")).count():
            return True
        button = page.get_by_role("button", name="Continuar", exact=True).first
        if button.count() == 0:
            return False
        try:
            button.wait_for(state="visible", timeout=8000)
            if not button.is_enabled():
                page.wait_for_timeout(400)
                continue
            button.click(timeout=8000)
        except PlaywrightError:
            page.wait_for_timeout(400)
            continue
        page.wait_for_timeout(900)
    return False


def open_preview(page) -> bool:
    click_if_present(page, re.compile("Ir al partido"))
    page.wait_for_timeout(600)
    if not click_if_present(page, re.compile("Ir a la previa")):
        return False
    page.wait_for_timeout(1200)
    return page.get_by_role("button", name=re.compile("Comenzar partido")).count() > 0


def play_live_match(page, checks: dict, observations: dict, index: int) -> None:
    """Juega un partido completo minuto a minuto."""
    prefix = f"live_match_{index}"
    checks[f"{prefix}_preview_opens"] = open_preview(page)
    if not checks[f"{prefix}_preview_opens"]:
        return

    checks[f"{prefix}_kickoff"] = click_if_present(page, re.compile("Comenzar partido"))
    page.wait_for_timeout(1200)

    minutes = [current_minute(page)]
    # Primera parte.
    for _ in range(8):
        if match_state(page) != "EN JUEGO":
            break
        if not click_if_present(page, "15 min", exact=True):
            break
        page.wait_for_timeout(1100)
        minutes.append(current_minute(page))

    checks[f"{prefix}_minute_advances"] = len(minutes) > 1 and minutes[-1] > minutes[0]
    checks[f"{prefix}_reaches_halftime"] = match_state(page) == "DESCANSO"

    # Segunda parte.
    click_if_present(page, re.compile("2ª parte"))
    page.wait_for_timeout(1500)
    for _ in range(10):
        if match_state(page) == "FINAL":
            break
        if not click_if_present(page, "15 min", exact=True, timeout=2500):
            break
        page.wait_for_timeout(1100)

    if match_state(page) != "FINAL":
        # Cierre explícito cuando el reloj ya agotó el tiempo reglamentario.
        click_if_present(page, re.compile("Finalizar|Terminar|Cerrar acta"))
        page.wait_for_timeout(1500)

    checks[f"{prefix}_reaches_final"] = match_state(page) == "FINAL"
    observations[f"{prefix}_minutes"] = minutes
    observations[f"{prefix}_final_state"] = match_state(page)


def play_simulated_match(page, checks: dict, index: int) -> None:
    """Resuelve un partido por resultado, sin dirigirlo minuto a minuto."""
    prefix = f"sim_match_{index}"
    checks[f"{prefix}_preview_opens"] = open_preview(page)
    if not checks[f"{prefix}_preview_opens"]:
        return
    click_if_present(page, "Resultado", exact=True)
    page.wait_for_timeout(3500)
    checks[f"{prefix}_reaches_final"] = match_state(page) == "FINAL"


def close_match_report(page) -> bool:
    """Cierra el acta del partido terminado y devuelve al bucle de carrera.

    Un partido en FINAL sigue abierto hasta que se cierra el acta: mientras
    tanto la carrera no avanza de día, así que sin este paso la siguiente
    jornada nunca llega.
    """
    if not click_if_present(page, re.compile("Cerrar partido")):
        return False
    page.wait_for_timeout(1500)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate del bucle jugable de Míster 93/94")
    parser.add_argument("--chromium", default=None, help="Ruta a Chromium; por defecto usa el de Playwright.")
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)

    if not DIST.is_file():
        report = {
            "kind": "playable-loop",
            "status": "blocked",
            "reason": "Falta frontend/dist/index.html. Ejecuta npm ci && npm run build antes del gate.",
            "passed": False,
        }
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("BLOCKED: falta frontend/dist/index.html")
        return 2

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    checks: dict[str, bool] = {}
    observations: dict[str, object] = {}

    with tempfile.TemporaryDirectory(prefix="m9394-loop-") as tmp:
        tmp_path = Path(tmp)
        env = os.environ.copy()
        env["MISTER9394_FRONTEND_DIST"] = str(DIST.parent)
        env["MISTER9394_SAVE_DIR"] = str(tmp_path / "saves")
        env["MISTER9394_BACKUP_DIR"] = str(tmp_path / "backups")
        env["MISTER9394_LOG_DIR"] = str(tmp_path / "logs")
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.football9394.webapp:app",
             "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )
        try:
            wait_health(f"{base}/api/football9394/health")
            with sync_playwright() as p:
                launch: dict = {"headless": True, "args": ["--no-sandbox"]}
                if args.chromium:
                    launch["executable_path"] = args.chromium
                browser = p.chromium.launch(**launch)
                context = browser.new_context(locale="es-ES", reduced_motion="reduce",
                                              viewport={"width": 1600, "height": 1000})
                page = context.new_page()
                page_errors: list[str] = []
                console_errors: list[str] = []
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

                try:
                    page.goto(base, wait_until="networkidle", timeout=30000)
                except PlaywrightError as exc:
                    if "ERR_BLOCKED_BY_ADMINISTRATOR" in str(exc):
                        report = {
                            "kind": "playable-loop",
                            "status": "environment-blocked",
                            "reason": "Chromium del entorno bloquea navegación HTTP local por política.",
                            "passed": False,
                        }
                        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        print("BLOCKED_ENV: Chromium bloquea localhost por política")
                        browser.close()
                        return 3
                    raise

                page.wait_for_timeout(800)
                # Alta de carrera desde la pantalla inicial.
                page.get_by_text("Escocia", exact=True).first.click()
                page.wait_for_timeout(500)
                page.get_by_role("button", name=re.compile("Empezar con")).first.click()
                page.wait_for_timeout(2500)
                checks["career_starts"] = page.get_by_role("button", name=re.compile("Continuar")).count() > 0
                click_if_present(page, re.compile("Ya sé cómo funciona"))
                page.wait_for_timeout(500)

                for index in range(1, LIVE_MATCHES + 1):
                    checks[f"live_match_{index}_matchday_reached"] = reach_matchday(page)
                    if checks[f"live_match_{index}_matchday_reached"]:
                        play_live_match(page, checks, observations, index)
                        checks[f"live_match_{index}_report_closes"] = close_match_report(page)

                for index in range(1, SIMULATED_MATCHES + 1):
                    checks[f"sim_match_{index}_matchday_reached"] = reach_matchday(page)
                    if checks[f"sim_match_{index}_matchday_reached"]:
                        play_simulated_match(page, checks, index)
                        checks[f"sim_match_{index}_report_closes"] = close_match_report(page)

                # El bucle debe seguir vivo al terminar: la carrera continúa.
                checks["loop_survives"] = page.get_by_role(
                    "button", name=re.compile("Continuar|Ir al partido")
                ).count() > 0

                checks["no_page_errors"] = not page_errors
                checks["no_console_errors"] = not console_errors
                observations["page_errors"] = page_errors
                observations["console_errors"] = console_errors[:20]
                browser.close()
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    passed = all(checks.values())
    report = {
        "kind": "playable-loop",
        "status": "pass" if passed else "fail",
        "live_matches": LIVE_MATCHES,
        "simulated_matches": SIMULATED_MATCHES,
        "checks": checks,
        "observations": observations,
        "passed": passed,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'} {key}")
    print(f"Report: {args.report}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
