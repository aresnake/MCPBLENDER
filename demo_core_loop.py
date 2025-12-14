from __future__ import annotations

import json

from mcpblender_server.bridge_client import BridgeClient
from mcpblender_server.schema import ToolRequest
from mcpblender_server.server import build_registry


def main() -> int:
    with BridgeClient() as bridge:
        registry = build_registry(bridge)
        sequence = [
            ToolRequest(method="core.ping", params={}, request_id="demo-1"),
            ToolRequest(method="blender.health", params={}, request_id="demo-2"),
            ToolRequest(method="scene.snapshot", params={"limit": 4}, request_id="demo-3"),
            ToolRequest(method="object.create_cube", params={"name": "DemoCube", "size": 1.5}, request_id="demo-4"),
            ToolRequest(method="object.transform", params={"name": "DemoCube", "location": (1, 1, 1)}, request_id="demo-5"),
            ToolRequest(method="scene.snapshot", params={"limit": 6}, request_id="demo-6"),
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
