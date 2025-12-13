from __future__ import annotations

import asyncio
import inspect
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
    if hasattr(mcp, "run_stdio_async"):
        await mcp.run_stdio_async()
        await asyncio.Future()
        return
    if hasattr(mcp, "run"):
        # Some SDKs expose run(transport="stdio")
        maybe = mcp.run("stdio")  # type: ignore[arg-type]
        if inspect.isawaitable(maybe):
            await maybe
        await asyncio.Future()
        return
    ctx = None
    run_coro = None

    if hasattr(stdio, "serve"):
        ctx = stdio.serve(mcp)
    elif hasattr(stdio, "stdio_server"):
        ctx = stdio.stdio_server(mcp)
    elif hasattr(stdio, "run"):
        run_coro = stdio.run(mcp)
    elif hasattr(stdio, "serve_stdio"):
        ctx = stdio.serve_stdio(mcp)
    else:
        raise RuntimeError(f"Unsupported mcp.server.stdio API: {dir(stdio)}")

    if ctx is not None:
        if inspect.isawaitable(ctx):
            await ctx
            return
        if hasattr(ctx, "__aenter__") and hasattr(ctx, "__aexit__"):
            async with ctx:
                await asyncio.Future()
            return
        raise RuntimeError(f"Unsupported stdio context type: {type(ctx)}")

    if run_coro is not None:
        await run_coro
        return

    raise RuntimeError("Failed to start stdio server")


def main() -> None:  # pragma: no cover - runtime entry
    asyncio.run(_serve_stdio())


if __name__ == "__main__":  # pragma: no cover
    main()
