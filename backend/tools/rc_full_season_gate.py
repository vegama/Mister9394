from __future__ import annotations

"""Gate de temporada completa: juega un año entero por la API real del juego.

``rc_playable_loop_gate.py`` demuestra que un partido se puede dirigir desde el
navegador, pero sólo cubre las primeras jornadas. Este gate responde la otra
mitad de la pregunta —¿se puede *terminar* el juego?— recorriendo una temporada
completa por los mismos endpoints que usa el frontend: avanzar hasta evento,
abrir la previa, resolver el partido, cerrar el acta y repetir hasta el cierre
de temporada.

Comprueba tres cosas que un test unitario no ve:

1. que el bucle nunca se queda atascado (ni un día sin avanzar, ni un partido
   que no se puede cerrar);
2. que el guardado sigue siendo legible al final, después de cientos de
   escrituras atómicas reales;
3. que el calendario se agota y la carrera cruza al año siguiente en lugar de
   quedarse girando en la última jornada.

El soak longitudinal (``v100_g_longitudinal_soak.py``) trabaja a nivel de
runtime y cierra temporadas de forma sintética; éste pasa por HTTP y por el
almacenamiento en disco, que es donde vivían los fallos de guardado.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "qa" / "rc-full-season.json"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request(method: str, url: str, payload: dict | None = None, timeout: float = 120.0) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read()
    return json.loads(body) if body else {}


def wait_health(base: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if request("GET", f"{base}/api/football9394/health"):
                return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("El servidor no respondió al healthcheck.")


def play_one_match(base: str, cid: str) -> dict:
    """Abre la previa y resuelve el partido por resultado.

    ``live/result`` ya deja el partido cerrado y confirmado, así que no lleva
    un ``live/finish`` detrás: ese camino es el de la dirección minuto a minuto,
    y encadenarlo aquí devolvería 409.
    """
    try:
        request("POST", f"{base}/api/football9394/careers/{cid}/live/start")
    except urllib.error.HTTPError as exc:
        if exc.code != 409:
            raise
        # Una lesión o sanción deja inválido el once guardado y el partido no
        # abre. Es exactamente lo que haría un entrenador antes de jugar:
        # recomponer la convocatoria y volver a intentarlo.
        request("PUT", f"{base}/api/football9394/careers/{cid}/selection", {"auto_select": True})
        request("POST", f"{base}/api/football9394/careers/{cid}/live/start")
        play_one_match.repairs += 1
    result = request("POST", f"{base}/api/football9394/careers/{cid}/live/result")
    return result.get("match") or {}


play_one_match.repairs = 0  # type: ignore[attr-defined]


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate de temporada completa de Míster 93/94")
    parser.add_argument("--team", type=int, default=16, help="Club a dirigir.")
    parser.add_argument("--league", type=int, default=1, help="Competición de la carrera.")
    parser.add_argument("--max-days", type=int, default=900, help="Tope de días simulados antes de rendirse.")
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    checks: dict[str, bool] = {}
    observations: dict[str, object] = {}

    with tempfile.TemporaryDirectory(prefix="m9394-season-") as tmp:
        tmp_path = Path(tmp)
        env = os.environ.copy()
        env["MISTER9394_SAVE_DIR"] = str(tmp_path / "saves")
        env["MISTER9394_BACKUP_DIR"] = str(tmp_path / "backups")
        env["MISTER9394_LOG_DIR"] = str(tmp_path / "logs")
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.football9394.webapp:app",
             "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )
        started = time.monotonic()
        try:
            wait_health(base)
            created = request("POST", f"{base}/api/football9394/careers",
                              {"team_id": args.team, "league_id": args.league,
                               "seed": 9394, "through_matchday": 0})
            cid = created["career_id"]
            season = created.get("season")
            checks["career_created"] = bool(cid)

            matches_played = 0
            stalled = False
            last_date = created.get("game_date")
            days_without_progress = 0
            season_changed = False
            errors: list[str] = []

            for _ in range(args.max_days):
                try:
                    step = request("POST", f"{base}/api/football9394/careers/{cid}/advance-until-event?max_days=14")
                except urllib.error.HTTPError as exc:
                    errors.append(f"advance: HTTP {exc.code} {exc.read()[:180]!r}")
                    break

                career = step.get("career") or {}
                current_date = career.get("game_date")
                if career.get("season") and season and career["season"] != season:
                    season_changed = True
                    break

                if current_date == last_date:
                    days_without_progress += 1
                    if days_without_progress >= 3:
                        stalled = True
                        break
                else:
                    days_without_progress = 0
                last_date = current_date

                if step.get("requires_match"):
                    try:
                        play_one_match(base, cid)
                        matches_played += 1
                    except urllib.error.HTTPError as exc:
                        errors.append(f"match: HTTP {exc.code} {exc.read()[:180]!r}")
                        break

            elapsed = round(time.monotonic() - started, 1)

            # El guardado debe seguir siendo legible después de cientos de escrituras.
            reloaded = {}
            try:
                reloaded = request("GET", f"{base}/api/football9394/careers/{cid}")
                checks["save_still_loads"] = bool(reloaded.get("career_id") == cid)
            except Exception as exc:
                checks["save_still_loads"] = False
                errors.append(f"reload: {exc}")

            checks["no_api_errors"] = not errors
            checks["loop_never_stalls"] = not stalled
            checks["season_completes"] = season_changed
            checks["played_full_calendar"] = matches_played >= 30

            observations.update({
                "matches_played": matches_played,
                "season_start": season,
                "season_after": reloaded.get("season"),
                "last_date": last_date,
                "elapsed_seconds": elapsed,
                # Cada reparación es una vez que el once guardado quedó inválido
                # (lesión o sanción) y hubo que rehacer la convocatoria para
                # poder jugar. Un número alto indica que el juego deja al
                # usuario bloqueado con demasiada frecuencia.
                "lineup_repairs": play_one_match.repairs,
                "errors": errors,
            })
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    passed = all(checks.values())
    report = {
        "kind": "full-season",
        "status": "pass" if passed else "fail",
        "checks": checks,
        "observations": observations,
        "passed": passed,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'} {key}")
    for key, value in observations.items():
        print(f"  · {key}: {value}")
    print(f"Report: {args.report}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
