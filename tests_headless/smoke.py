"""Headless Blender smoke test.

Run with: blender --background --python tests_headless/smoke.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON_ROOT = ROOT / "blender_addon"
sys.path.insert(0, str(ADDON_ROOT))

from mcpblender_addon.actions import HAS_BPY  # noqa: E402
from mcpblender_addon.bridge_http.server import dispatch_rpc  # noqa: E402


def main() -> int:
    if not HAS_BPY:
        print("bpy not available; run inside Blender")
        return 1
    try:
        def rpc(method: str, params: dict):
            resp = dispatch_rpc(method, params)
            if not resp.get("ok"):
                print(f"RPC {method} failed: {resp}")
                raise SystemExit(1)
            return resp.get("data")

        cube_data = rpc("object.create_cube", {"name": "SmokeCube", "size": 1.0, "location": (0, 0, 0)})
        cube_name = cube_data.get("name") or "SmokeCube"
        print(f"Created cube {cube_name}")

        snap = rpc("scene.snapshot", {"limit": 200})
        names = [obj.get("name") for obj in snap.get("objects", [])]
        print(f"Snapshot count: {len(names)}")
        print(f"Cube present in snapshot: {cube_name in names}")
        smoke_names = [n for n in names if n and "Smoke" in n]
        print(f"Names containing 'Smoke': {smoke_names[:10] if smoke_names else names[:10]}")

        # Validate retrieval by name/id via scenegraph.get
        resolved = rpc("scenegraph.get", {"name": cube_name})
        if not resolved or resolved.get("name") != cube_name:
            print(f"scenegraph.get failed; snapshot contained: {names[:10]}")
            print("Failed to resolve cube by name via scenegraph.get")
            return 1

        # Local transform check
        before_local = rpc("scenegraph.get", {"name": cube_name})
        rpc("object.transform", {"name": cube_name, "rotation": (0.1, 0.0, 0.0), "space": "local"})
        after_local = rpc("scenegraph.get", {"name": cube_name})
        if before_local.get("rotation") == after_local.get("rotation"):
            print("Local rotation did not change")
            return 1

        # World transform check (also position change)
        rpc("object.transform", {"name": cube_name, "location": (2, 0, 0), "rotation": (0.0, 0.1, 0.0), "space": "world"})
        after_world = rpc("scenegraph.get", {"name": cube_name})
        if after_world.get("location") == after_local.get("location"):
            print("World location did not change")
            return 1
        if after_world.get("rotation") == after_local.get("rotation"):
            print("World rotation did not change")
            return 1

        # Assign material and validate
        mat_resp = rpc("material.assign_simple", {"object": cube_name, "name": "SmokeMat", "color": [0.2, 0.4, 0.8, 1.0]})
        if mat_resp.get("material_name") != "SmokeMat":
            print("Material assignment failed")
            return 1
        resolved_after_mat = rpc("scenegraph.get", {"name": cube_name})
        if resolved_after_mat is None:
            print("Object missing after material assignment")
            return 1

        # Delete cube and validate disappearance
        rpc("object.delete", {"name": cube_name})
        try:
            rpc("scenegraph.get", {"name": cube_name})
            print("Object not deleted")
            return 1
        except SystemExit:
            # Expected failure path; scenegraph.get should error after deletion
            pass

        # Snapshot to ensure object absence
        snapshot = rpc("scene.snapshot", {"limit": 10})
        names = [obj.get("name") for obj in snapshot.get("objects", [])]
        if cube_name in names:
            print("Deleted object still present in snapshot")
            return 1

        return 0
    except Exception as exc:  # pragma: no cover - Blender runtime only
        print(f"Smoke test failed: {exc}")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
