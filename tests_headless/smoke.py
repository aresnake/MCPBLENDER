"""Headless Blender smoke test.

Run with: blender --background --python tests_headless/smoke.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON_ROOT = ROOT / "blender_addon"
sys.path.insert(0, str(ADDON_ROOT))

from mcpblender_addon.actions import create_cube, transform_object, capture_snapshot, HAS_BPY  # noqa: E402


def main() -> int:
    if not HAS_BPY:
        print("bpy not available; run inside Blender")
        return 1
    try:
        first_snapshot = capture_snapshot({"limit": 5})
        print(f"Initial snapshot objects: {len(first_snapshot['objects'])}")
        cube = create_cube({"name": "SmokeCube", "size": 1.0, "location": (0, 0, 0)})
        print(f"Created cube {cube['name']}")
        transform_object({"name": cube["name"], "location": (2, 0, 0), "space": "world"})
        second_snapshot = capture_snapshot({"limit": 5})
        print(f"Second snapshot objects: {len(second_snapshot['objects'])}")
        return 0
    except Exception as exc:  # pragma: no cover - Blender runtime only
        print(f"Smoke test failed: {exc}")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
