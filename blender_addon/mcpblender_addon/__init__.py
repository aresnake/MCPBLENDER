from __future__ import annotations

"""Blender addon entrypoint for MCPBLENDER bridge."""

bl_info = {
    "name": "MCPBLENDER Core Bridge",
    "author": "MCPBLENDER",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "category": "System",
    "description": "HTTP bridge exposing MCP tools",
}

_bridge_server = None


def register() -> None:  # pragma: no cover - Blender runtime only
    global _bridge_server
    from .bridge_http.server import launch_server

    try:
        if _bridge_server is None:
            _bridge_server = launch_server(host="127.0.0.1", port=9876)
    except Exception as exc:
        print(f"[MCPBLENDER] Failed to start bridge: {exc}", flush=True)


def unregister() -> None:  # pragma: no cover - Blender runtime only
    global _bridge_server
    try:
        if _bridge_server is not None:
            _bridge_server.stop()
            _bridge_server = None
            print("[MCPBLENDER] Bridge stopped", flush=True)
    except Exception as exc:
        print(f"[MCPBLENDER] Failed to stop bridge: {exc}", flush=True)
