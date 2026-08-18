from __future__ import annotations

import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "qa" / "rc-launcher-http-smoke.json"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def get(url: str, timeout: float = 3.0) -> tuple[int, dict[str, str], bytes]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()


def main() -> int:
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    checks: dict[str, bool] = {}
    observations: dict[str, object] = {"base": base}

    with tempfile.TemporaryDirectory(prefix="m9394-launcher-smoke-") as tmp:
        env = os.environ.copy()
        env["MISTER9394_USER_DATA_DIR"] = str(Path(tmp) / "userdata")
        process = subprocess.Popen(
            [sys.executable, "run_football9394.py", "--no-browser", "--port", str(port)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        try:
            health = None
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    break
                try:
                    status, _, body = get(base + "/api/football9394/health", 1.0)
                    if status == 200:
                        health = json.loads(body)
                        break
                except Exception:
                    time.sleep(0.2)
            checks["launcher_starts"] = health is not None and process.poll() is None
            checks["health_is_canonical"] = bool(health and health.get("ok") is True and health.get("version") == (ROOT / "VERSION").read_text().strip())
            observations["health"] = health

            if health:
                status, headers, body = get(base + "/")
                html = body.decode("utf-8")
                checks["index_is_served"] = status == 200 and "Míster 93/94" in html and '<div id="app"></div>' in html
                refs = re.findall(r'/assets/(index-[0-9a-f]+\.(?:js|css))', html)
                observations["asset_refs"] = refs
                checks["index_references_bundle"] = len(refs) >= 2
                asset_results = []
                for ref in refs:
                    s, h, data = get(base + "/assets/" + ref)
                    asset_results.append({"asset": ref, "status": s, "content_type": h.get("content-type"), "bytes": len(data)})
                observations["assets"] = asset_results
                checks["bundle_assets_are_served"] = bool(asset_results) and all(row["status"] == 200 and row["bytes"] > 1000 for row in asset_results)
                checks["bundle_mime_types_are_valid"] = any("javascript" in str(row["content_type"]).lower() for row in asset_results) and any("css" in str(row["content_type"]).lower() for row in asset_results)
            else:
                for name in ("index_is_served", "index_references_bundle", "bundle_assets_are_served", "bundle_mime_types_are_valid"):
                    checks[name] = False
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)
                except Exception:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except Exception:
                        pass
            output = ""
            if process.stdout is not None:
                try:
                    output = process.stdout.read()
                except Exception:
                    pass
            observations["launcher_output_tail"] = output.splitlines()[-20:]

    passed = all(checks.values())
    report = {"kind": "rc-launcher-http-smoke", "status": "passed" if passed else "failed", "passed": passed, "checks": checks, "observations": observations}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, value in checks.items():
        print(("PASS" if value else "FAIL"), name)
    print("Report:", REPORT)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
