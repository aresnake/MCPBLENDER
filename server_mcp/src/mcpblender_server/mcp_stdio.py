from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server import stdio

from mcpblender_server.bridge_client import BridgeClient


def _build_mcp(bridge: Optional[BridgeClient] = None) -> FastMCP:
    bridge_client = bridge or BridgeClient()
    mcp = FastMCP("mcpblender-core")

    def call_bridge(method: str, params: Dict[str, Any]) -> Any:
        resp = bridge_client.call_rpc(method, params or {})
        if resp and resp.get("ok"):
            return resp.get("data")
        error = (resp or {}).get("error") or {}
        code = error.get("code", "bridge_error")
        message = error.get("message", "bridge call failed")
        raise RuntimeError(f"{code}: {message}")

    @mcp.tool()
    def scene_snapshot() -> Any:
        """Capture a canonical scene snapshot."""
        return call_bridge("scene.snapshot", {})

    @mcp.tool()
    def object_create_cube(name: str | None = None, size: float | None = None, location: Any | None = None) -> Any:
        """Create a cube via bridge."""
        params: Dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if size is not None:
            params["size"] = size
        if location is not None:
            params["location"] = location
        return call_bridge("object.create_cube", params)

    @mcp.tool()
    def object_move_object(
        id: str | None = None, name: str | None = None, delta: Any | None = None, location: Any | None = None
    ) -> Any:
        """Move object by id or name."""
        params: Dict[str, Any] = {}
        if id is not None:
            params["id"] = id
        if name is not None:
            params["name"] = name
        if delta is not None:
            params["delta"] = delta
        if location is not None:
            params["location"] = location
        return call_bridge("object.move_object", params)

    @mcp.tool()
    def material_assign_simple(
        id: str | None = None,
        name: str | None = None,
        material_name: str | None = None,
        base_color: Any | None = None,
        metallic: float | None = None,
        roughness: float | None = None,
    ) -> Any:
        """Assign a simple material via bridge."""
        params: Dict[str, Any] = {}
        if id is not None:
            params["id"] = id
        if name is not None:
            params["name"] = name
        if material_name is not None:
            params["material_name"] = material_name
        if base_color is not None:
            params["base_color"] = base_color
        if metallic is not None:
            params["metallic"] = metallic
        if roughness is not None:
            params["roughness"] = roughness
        return call_bridge("material.assign_simple", params)

    return mcp


async def _serve_stdio() -> None:
    mcp = _build_mcp()
    async with stdio.serve(mcp):
        await asyncio.Future()


def main() -> None:  # pragma: no cover - runtime entry
    asyncio.run(_serve_stdio())


if __name__ == "__main__":  # pragma: no cover
    main()
