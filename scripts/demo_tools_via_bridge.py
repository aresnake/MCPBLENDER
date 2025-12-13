from __future__ import annotations

import json

from mcpblender_server.bridge_client import BridgeClient
from mcpblender_server.schema import ToolRequest
from mcpblender_server.server import build_registry


def main() -> int:
    with BridgeClient() as bridge:
        registry = build_registry(bridge)
        calls = [
            ToolRequest(tool="scene.snapshot", args={}, request_id="demo-1"),
            ToolRequest(tool="object.create_cube", args={"name": "DemoCube", "size": 1.0}, request_id="demo-2"),
            ToolRequest(tool="object.move_object", args={"name": "DemoCube", "delta": (1, 0, 0)}, request_id="demo-3"),
            ToolRequest(
                tool="material.assign_simple",
                args={"name": "DemoCube", "material_name": "DemoMat", "base_color": [0.2, 0.6, 1.0, 1.0]},
                request_id="demo-4",
            ),
            ToolRequest(tool="scene.snapshot", args={}, request_id="demo-5"),
        ]
        for req in calls:
            resp = registry.dispatch(req)
            print(f"{req.tool}: {json.dumps(resp.to_dict())}")
            if not resp.ok:
                print("Stopping demo due to error")
                return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
