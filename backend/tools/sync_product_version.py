from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza metadatos derivados desde VERSION.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    expected: list[tuple[Path, str]] = []

    pkg_path = ROOT / "frontend" / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    expected.append((pkg_path, str(pkg.get("version") or "")))

    lock_path = ROOT / "frontend" / "package-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    expected.append((lock_path, str(lock.get("version") or "")))
    expected.append((lock_path, str((lock.get("packages") or {}).get("", {}).get("version") or "")))

    project_path = ROOT / "project_football9394.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    expected.append((project_path, str(project.get("version") or "")))

    mismatches = [(path, value) for path, value in expected if value != version]
    if args.check:
        if mismatches:
            for path, value in mismatches:
                print(f"FAIL {path.relative_to(ROOT)}: {value!r} != {version!r}")
            return 1
        print(f"PASS VERSION {version}")
        return 0

    pkg["version"] = version
    pkg_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lock["version"] = version
    lock.setdefault("packages", {}).setdefault("", {})["version"] = version
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    project["version"] = version
    project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Sincronizado VERSION {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
