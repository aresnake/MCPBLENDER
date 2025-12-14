from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Optional

from mcpblender_addon.actions import scenegraph_get, scenegraph_search, transform_object
from mcpblender_addon.snapshot.light_snapshot import make_light_snapshot

try:  # pragma: no cover - Blender runtime only
    import bpy
    import bmesh
    from mathutils import Vector

    HAS_BPY = True
except ImportError:  # pragma: no cover - Blender runtime only
    bpy = None
    bmesh = None
    Vector = None
    HAS_BPY = False

BRIDGE_VERSION = "1.0.3"
MAX_BODY_BYTES = 1_048_576  # 1 MB
TIMEOUT_SECONDS = 2.5
START_TIME = time.monotonic()


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _make_error(code: str, message: str) -> Dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


def _ensure_bpy() -> None:
    if not HAS_BPY:
        raise RuntimeError("bpy not available (run inside Blender)")


def _resolve_object(params: Dict[str, Any]):
    _ensure_bpy()
    obj_id = params.get("id")
    name = params.get("name")
    if obj_id:
        for obj in bpy.data.objects:
            if str(obj.as_pointer()) == str(obj_id):
                return obj
    if name:
        obj = bpy.data.objects.get(name)
        if obj:
            return obj
    return None


def _rpc_scene_snapshot() -> Dict[str, Any]:
    try:
        snapshot = make_light_snapshot()
        return {"ok": True, "data": snapshot}
    except Exception as exc:  # pragma: no cover - defensive
        return _make_error("snapshot_error", str(exc))


def _rpc_scenegraph_search(params: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    try:
        result = scenegraph_search(params or {})
        return {"ok": True, "data": result}
    except Exception as exc:
        return _make_error("scenegraph_error", str(exc))


def _rpc_scenegraph_get(params: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    try:
        result = scenegraph_get(params or {})
        return {"ok": True, "data": result}
    except Exception as exc:
        return _make_error("scenegraph_error", str(exc))


def _rpc_object_create_cube(params: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    try:
        _ensure_bpy()
        name = params.get("name") or "Cube"
        size = float(params.get("size", 2.0))
        location = params.get("location") or (0.0, 0.0, 0.0)

        mesh = bpy.data.meshes.new(f"{name}_mesh")
        try:
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=size)
            bm.to_mesh(mesh)
            bm.free()
        except Exception:
            mesh.from_pydata(
                [
                    (-size, -size, -size),
                    (-size, -size, size),
                    (-size, size, -size),
                    (-size, size, size),
                    (size, -size, -size),
                    (size, -size, size),
                    (size, size, -size),
                    (size, size, size),
                ],
                [],
                [
                    (0, 1, 3, 2),
                    (4, 6, 7, 5),
                    (0, 4, 5, 1),
                    (2, 3, 7, 6),
                    (0, 2, 6, 4),
                    (1, 5, 7, 3),
                ],
            )
            mesh.update()

        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = Vector(location)
        return {"ok": True, "data": {"id": str(obj.as_pointer()), "name": obj.name}}
    except Exception as exc:
        return _make_error("create_cube_error", str(exc))


def _rpc_object_move(params: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    try:
        obj = _resolve_object(params)
        if obj is None:
            return _make_error("not_found", "Object not found")

        location = params.get("location")
        delta = params.get("delta")
        if location is not None:
            obj.location = Vector(location)
        elif delta is not None:
            obj.location = obj.location + Vector(delta)
        else:
            return _make_error("invalid_params", "location or delta required")

        return {
            "ok": True,
            "data": {"id": str(obj.as_pointer()), "name": obj.name, "location": [round(float(v), 6) for v in obj.location[:3]]},
        }
    except Exception as exc:
        return _make_error("move_error", str(exc))


def _rpc_object_transform(params: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    try:
        result = transform_object(params or {})
        return {"ok": True, "data": result}
    except Exception as exc:
        return _make_error("transform_error", str(exc))


def _handler_map(params: Dict[str, Any]) -> Dict[str, Callable[[], Dict[str, Any]]]:
    return {
        "scene.snapshot": _rpc_scene_snapshot,
        "object.create_cube": lambda: _rpc_object_create_cube(params),
        "object.move_object": lambda: _rpc_object_move(params),
        "object.transform": lambda: _rpc_object_transform(params),
        "material.assign_simple": lambda: _rpc_material_assign(params),
        "scenegraph.search": lambda: _rpc_scenegraph_search(params),
        "scenegraph.get": lambda: _rpc_scenegraph_get(params),
    }


def handle_rpc_bytes(body: bytes) -> Dict[str, Any]:
    if len(body) > MAX_BODY_BYTES:
        return _make_error("payload_too_large", "payload exceeds limit")

    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except Exception:
        return _make_error("invalid_payload", "Body must be JSON object")

    if not isinstance(payload, dict):
        return _make_error("invalid_payload", "Body must be JSON object")

    method = payload.get("method")
    params = payload.get("params") or {}

    if not isinstance(params, dict):
        return _make_error("invalid_payload", "params must be an object")

    handlers = _handler_map(params)
    handler = handlers.get(method)
    if handler is None:
        return _make_error("tool_not_found", "Unsupported method")

    start = time.monotonic()
    try:
        result = handler()
    except Exception as exc:  # pragma: no cover - defensive
        return _make_error("internal_error", str(exc))

    duration = time.monotonic() - start
    if duration > TIMEOUT_SECONDS:
        return _make_error("timeout", "operation exceeded timeout")

    if not isinstance(result, dict) or "ok" not in result:
        return _make_error("internal_error", "handler returned invalid payload")

    return result


def health_payload() -> Dict[str, Any]:
    uptime = time.monotonic() - START_TIME
    return {
        "ok": True,
        "source": "mcpblender_bridge",
        "version": BRIDGE_VERSION,
        "uptime_seconds": round(uptime, 3),
        "blender_version": _safe(lambda: bpy.app.version_string, "unavailable"),
        "ready": bool(HAS_BPY),
    }


def _rpc_material_assign(params: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    try:
        obj = _resolve_object(params)
        if obj is None:
            return _make_error("not_found", "Object not found")
        if obj.type != "MESH":
            return _make_error("invalid_target", "Material assignment requires mesh object")

        mat_name = params.get("material_name") or "Material"
        base_color = params.get("base_color") or [0.8, 0.8, 0.8, 1.0]
        metallic = float(params.get("metallic", 0.0))
        roughness = float(params.get("roughness", 0.5))

        _ensure_bpy()
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.new(mat_name)
        try:
            mat.use_nodes = True
            tree = mat.node_tree
            principled = None
            if tree:
                for node in tree.nodes:
                    if node.type == "BSDF_PRINCIPLED":
                        principled = node
                        break
                if principled is None:
                    principled = tree.nodes.new("ShaderNodeBsdfPrincipled")
                principled.inputs["Base Color"].default_value = base_color
                principled.inputs["Metallic"].default_value = metallic
                principled.inputs["Roughness"].default_value = roughness
        except Exception:
            # Fallback: set simple attributes when node setup not available
            if hasattr(mat, "diffuse_color"):
                mat.diffuse_color = base_color

        if not obj.data.materials:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        return {"ok": True, "data": {"material_name": mat.name}}
    except Exception as exc:
        return _make_error("material_error", str(exc))


class _Handler(BaseHTTPRequestHandler):
    server_version = "MCPBlenderBridge/1.0"
    protocol_version = "HTTP/1.1"

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        try:
            body = json.dumps(payload).encode("utf-8")
        except Exception:
            body = b'{"ok": false, "error": {"code": "serialization_error"}}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def log_message(self, fmt: str, *args: Any) -> None:  # pragma: no cover - quiet handler
        return

    def do_GET(self):  # noqa: N802
        try:
            if self.path != "/health":
                self._send_json(_make_error("not_found", "Unknown path"), status=404)
                return
            self._send_json(health_payload())
        except Exception:
            self._send_json(_make_error("internal_error", "GET failed"), status=500)

    def do_POST(self):  # noqa: N802
        if self.path != "/rpc":
            self._send_json(_make_error("not_found", "Unknown path"), status=404)
            return

        length = _safe(lambda: int(self.headers.get("Content-Length", "0")), 0)
        if length > MAX_BODY_BYTES:
            self._send_json(_make_error("payload_too_large", "payload exceeds limit"), status=413)
            return

        body = self.rfile.read(length) if length > 0 else b""
        result = handle_rpc_bytes(body)
        status = 200 if result.get("ok") else 400
        error_code = result.get("error", {}).get("code")
        if error_code == "internal_error":
            status = 500
        elif error_code == "timeout":
            status = 504
        elif error_code == "payload_too_large":
            status = 413
        self._send_json(result, status=status)


class BridgeServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 9876) -> None:
        self.address = (host, port)
        self._server = ThreadingHTTPServer(self.address, _Handler)
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        try:
            self._server.shutdown()
        except Exception:
            pass
        if self._thread is not None:
            self._thread.join(timeout=1)


def launch_server(host: str = "127.0.0.1", port: int = 9876) -> BridgeServer:
    server = BridgeServer(host=host, port=port)
    server.start()
    print(f"[MCPBLENDER] Bridge started on http://{host}:{port}", flush=True)
    return server


def main() -> None:  # pragma: no cover - Blender runtime only
    server = launch_server()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("[MCPBLENDER] Bridge stopped", flush=True)


if __name__ == "__main__":  # pragma: no cover
    main()
