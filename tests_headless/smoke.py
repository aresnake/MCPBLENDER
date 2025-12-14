"""Headless Blender smoke test.

Run with: blender --background --python tests_headless/smoke.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON_ROOT = ROOT / "blender_addon"
sys.path.insert(0, str(ADDON_ROOT))

from mcpblender_addon.actions import (  # noqa: E402
    HAS_BPY,
    assign_material_simple,
    create_cube,
    delete_object,
    scenegraph_get,
    transform_object,
)


def main() -> int:
    if not HAS_BPY:
        print("bpy not available; run inside Blender")
        return 1
    try:
        cube = create_cube({"name": "SmokeCube", "size": 1.0, "location": (0, 0, 0)})
        print(f"Created cube {cube['name']}")

        # Validate retrieval by name/id
        resolved = scenegraph_get({"name": cube["name"]})
        if not resolved or resolved.get("name") != cube["name"]:
            print("Failed to resolve cube by name via scenegraph_get")
            return 1

        # Local transform check
        before_local = scenegraph_get({"name": cube["name"]})
        transform_object({"name": cube["name"], "rotation": (0.1, 0.0, 0.0), "space": "local"})
        after_local = scenegraph_get({"name": cube["name"]})
        if before_local.get("rotation") == after_local.get("rotation"):
            print("Local rotation did not change")
            return 1

        # World transform check (also position change)
        transform_object({"name": cube["name"], "location": (2, 0, 0), "rotation": (0.0, 0.1, 0.0), "space": "world"})
        after_world = scenegraph_get({"name": cube["name"]})
        if after_world.get("location") == after_local.get("location"):
            print("World location did not change")
            return 1
        if after_world.get("rotation") == after_local.get("rotation"):
            print("World rotation did not change")
            return 1

        # Assign material and validate
        mat_resp = assign_material_simple({"object": cube["name"], "name": "SmokeMat", "color": [0.2, 0.4, 0.8, 1.0]})
        if mat_resp.get("material_name") != "SmokeMat":
            print("Material assignment failed")
            return 1
        resolved_after_mat = scenegraph_get({"name": cube["name"]})
        if resolved_after_mat is None:
            print("Object missing after material assignment")
            return 1

        # Delete cube and validate disappearance
        delete_object({"name": cube["name"]})
        after_delete = scenegraph_get({"name": cube["name"]})
        if after_delete:
            print("Object not deleted")
            return 1

        return 0
    except Exception as exc:  # pragma: no cover - Blender runtime only
        print(f"Smoke test failed: {exc}")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
