#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / "data" / "scenes.json").read_text(encoding="utf-8"))
missing = []
for scene in config["scenes"]:
    path = ROOT / scene["source"]
    if not path.exists():
        missing.append(str(path.relative_to(ROOT)))
large = []
for path in ROOT.rglob("*"):
    if path.is_file() and ".git" not in path.parts and path.stat().st_size >= 25 * 1024 * 1024:
        large.append((str(path.relative_to(ROOT)), path.stat().st_size / 1024 / 1024))
if missing:
    raise SystemExit("Missing assets:\n" + "\n".join(missing))
if large:
    raise SystemExit("Files exceed GitHub browser upload limit:\n" + "\n".join(f"{p}: {s:.1f} MB" for p, s in large))
print(f"Validated {len(config['scenes'])} scenes. All assets exist and every file is below 25 MB.")
