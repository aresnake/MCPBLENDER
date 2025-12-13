from __future__ import annotations

import json

from mcpblender_server.bridge_client import BridgeClient
from mcpblender_server.schema import ToolRequest
from mcpblender_server.server import build_registry


def main() -> int:
    with BridgeClient() as bridge:
        registry = build_registry(bridge)
        sequence = [
            ToolRequest(tool="core.ping", args={}, request_id="demo-1"),
            ToolRequest(tool="blender.health", args={}, request_id="demo-2"),
            ToolRequest(tool="scene.snapshot", args={"limit": 4}, request_id="demo-3"),
            ToolRequest(tool="object.create_cube", args={"name": "DemoCube", "size": 1.5}, request_id="demo-4"),
            ToolRequest(tool="object.transform", args={"name": "DemoCube", "location": (1, 1, 1)}, request_id="demo-5"),
            ToolRequest(tool="scene.snapshot", args={"limit": 6}, request_id="demo-6"),
        ]
        for request in sequence:
            response = registry.dispatch(request)
            print(json.dumps(response.to_dict()))
            if not response.ok:
                print("Aborting demo due to error")
                return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
