from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

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
                self._send_json({"ok": False, "error": {"code": "not_found", "message": "Unknown path"}}, status=404)
                return
            self._send_json({"ok": True, "source": "mcpblender_bridge"})
        except Exception:
            self._send_json({"ok": False, "error": {"code": "internal_error", "message": "GET failed"}}, status=500)

    def do_POST(self):  # noqa: N802
        if self.path != "/rpc":
            self._send_json({"ok": False, "error": {"code": "not_found", "message": "Unknown path"}}, status=404)
            return

        length = _safe(lambda: int(self.headers.get("Content-Length", "0")), 0)
        body = self.rfile.read(length) if length > 0 else b""
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            self._send_json({"ok": False, "error": {"code": "invalid_payload", "message": "Body must be JSON"}}, status=400)
            return

        method = payload.get("method")
        params = payload.get("params") or {}

        handlers = {
            "scene.snapshot": _rpc_scene_snapshot,
            "object.create_cube": lambda: _rpc_object_create_cube(params),
            "object.move_object": lambda: _rpc_object_move(params),
            "object.transform": lambda: _rpc_object_transform(params),
            "material.assign_simple": lambda: _rpc_material_assign(params),
            "scenegraph.search": lambda: _rpc_scenegraph_search(params),
            "scenegraph.get": lambda: _rpc_scenegraph_get(params),
        }

        handler = handlers.get(method)
        if handler is None:
            self._send_json({"ok": False, "error": {"code": "invalid_method", "message": "Unsupported method"}}, status=400)
            return

        try:
            result = handler()
        except Exception as exc:  # pragma: no cover - defensive
            result = _make_error("internal_error", str(exc))
        self._send_json(result, status=200 if result.get("ok") else 500)


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
