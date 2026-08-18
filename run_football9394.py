from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from backend.app.football9394.app_paths import default_app_paths
from backend.app.football9394.product_meta import product_version

ROOT = Path(__file__).resolve().parent
FRONTEND_DIST = ROOT / "frontend" / "dist"


def _open_browser_later(url: str) -> None:
    def run() -> None:
        time.sleep(1.0)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=run, daemon=True).start()


def main() -> int:
    parser = argparse.ArgumentParser(description="Arranca Míster 93/94 como producto integrado.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9394)
    parser.add_argument("--reload", action="store_true", help="Recarga automática del backend (desarrollo).")
    parser.add_argument("--dev-api", action="store_true", help="Arranca sólo la API aunque no exista frontend/dist.")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if not args.dev_api and not (FRONTEND_DIST / "index.html").is_file():
        print("ERROR: falta frontend/dist. Ejecuta el gate de release: cd frontend && npm ci && npm run build", file=sys.stderr)
        return 2

    paths = default_app_paths().ensure()
    env = os.environ.copy()
    env["MISTER9394_SAVE_DIR"] = str(paths.saves)
    env["MISTER9394_BACKUP_DIR"] = str(paths.backups)
    env["MISTER9394_LOG_DIR"] = str(paths.logs)
    env["MISTER9394_FRONTEND_DIST"] = str(FRONTEND_DIST)

    cmd = [
        sys.executable, "-m", "uvicorn", "backend.app.football9394.webapp:app",
        "--host", args.host, "--port", str(args.port),
    ]
    if args.reload:
        cmd.append("--reload")

    url = f"http://{args.host}:{args.port}"
    log_path = paths.logs / f"mister9394-{datetime.now().strftime('%Y%m%d')}.log"
    print(f"Míster 93/94 v{product_version()} · {url}")
    print(f"Saves: {paths.saves}")
    print(f"Backups: {paths.backups}")
    print(f"Log: {log_path}")
    if not args.no_browser and not args.dev_api:
        _open_browser_later(url)

    with log_path.open("a", encoding="utf-8", buffering=1) as log:
        log.write(f"\n=== Míster 93/94 v{product_version()} · {datetime.now().isoformat()} ===\n")
        process = subprocess.Popen(
            cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
        try:
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="")
                log.write(line)
        except KeyboardInterrupt:
            process.terminate()
        finally:
            try:
                return process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                return process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
