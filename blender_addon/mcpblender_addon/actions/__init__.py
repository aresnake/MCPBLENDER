from __future__ import annotations

from typing import Any, Dict

from .core_actions import (
    HAS_BPY,
    blender_health,
    capture_snapshot,
    create_cube,
    scenegraph_get,
    scenegraph_search,
    transform_object,
)

__all__ = [
    "HAS_BPY",
    "blender_health",
    "capture_snapshot",
    "create_cube",
    "scenegraph_get",
    "scenegraph_search",
    "transform_object",
    "dispatch_tool",
    "build_response",
]


def build_response(ok: bool, request_id: str, data: Any = None, error: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"ok": ok, "request_id": request_id}
    if data is not None:
        payload["data"] = data
    if error is not None:
        payload["error"] = error
    return payload


def dispatch_tool(tool: str, args: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    mapping = {
        "scene.snapshot": capture_snapshot,
        "scenegraph.search": scenegraph_search,
        "scenegraph.get": scenegraph_get,
        "object.create_cube": create_cube,
        "object.transform": transform_object,
    }
    func = mapping.get(tool)
    if func is None:
        return build_response(False, request_id, error={"code": "unknown_tool", "message": f"Unknown tool {tool}"})
    try:
        result = func(args or {})
        return build_response(True, request_id, data=result)
    except Exception as exc:  # pragma: no cover - Blender runtime only
        return build_response(False, request_id, error={"code": "execution_error", "message": str(exc)})
