from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Tuple
from urllib.parse import urlparse

try:  # pragma: no cover - Blender runtime only
    import bpy

    HAS_BPY = True
except Exception:  # pragma: no cover - Blender runtime only
    bpy = None
    HAS_BPY = False

try:  # pragma: no cover - Blender runtime only
    from runtime_blender import modeling_api
except Exception:  # pragma: no cover - allow import without Blender for tests
    modeling_api = None

RUNTIME_NAME = "mcpblender-runtime"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876


def _safe(fn, default: Any = None) -> Any:
    try:
        return fn()
    except Exception:
        return default


def _blender_version() -> str:
    return _safe(lambda: bpy.app.version_string, "unavailable")


def make_success(result: Any) -> Dict[str, Any]:
    return {"ok": True, "result": result}


def make_error(code: str, message: str, details: Any | None = None) -> Dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message, "details": details}}


def handle_health() -> Tuple[int, Dict[str, Any]]:
    payload = {"name": RUNTIME_NAME, "blender_version": _blender_version()}
    return 200, make_success(payload)


def handle_probe() -> Tuple[int, Dict[str, Any]]:
    payload = {"name": "blender-runtime", "version": _blender_version()}
    return 200, make_success(payload)


def handle_scene_objects() -> Tuple[int, Dict[str, Any]]:
    if not HAS_BPY:
        return 500, make_error("bpy_unavailable", "bpy not available (run inside Blender)")

    try:
        objects = [{"name": obj.name, "type": getattr(obj, "type", "UNKNOWN")} for obj in bpy.data.objects]
    except Exception as exc:  # pragma: no cover - defensive
        return 500, make_error("scene_objects_error", str(exc))

    return 200, make_success({"objects": objects})


RouteHandler = Callable[[], Tuple[int, Dict[str, Any]]]
ROUTES: Dict[str, RouteHandler] = {
    "/health": handle_health,
    "/runtime/probe": handle_probe,
    "/scene/objects": handle_scene_objects,
}


def _require_modeling_api() -> None:
    if not HAS_BPY or modeling_api is None:
        raise RuntimeError("bpy not available (run inside Blender)")


def _post_scene_reset(_: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    try:
        _require_modeling_api()
        count = modeling_api.reset_scene()
        return 200, make_success({"deleted": count})
    except Exception as exc:  # pragma: no cover - Blender runtime only
        code = "bpy_unavailable" if not HAS_BPY else "reset_error"
        return 500, make_error(code, str(exc))


def _post_mesh_add_cube(params: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    try:
        _require_modeling_api()
        result = modeling_api.add_cube(
            name=params.get("name"),
            size=params.get("size"),
            location=params.get("location"),
        )
        return 200, make_success(result)
    except Exception as exc:  # pragma: no cover - Blender runtime only
        code = "bpy_unavailable" if not HAS_BPY else "add_cube_error"
        return 500, make_error(code, str(exc))


def _post_mesh_add_plane(params: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    try:
        _require_modeling_api()
        result = modeling_api.add_plane(
            name=params.get("name"),
            size=params.get("size"),
            location=params.get("location"),
        )
        return 200, make_success(result)
    except Exception as exc:  # pragma: no cover - Blender runtime only
        code = "bpy_unavailable" if not HAS_BPY else "add_plane_error"
        return 500, make_error(code, str(exc))


def _post_mesh_add_cylinder(params: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    try:
        _require_modeling_api()
        result = modeling_api.add_cylinder(
            name=params.get("name"),
            radius=params.get("radius"),
            depth=params.get("depth"),
            vertices=params.get("vertices"),
            location=params.get("location"),
        )
        return 200, make_success(result)
    except Exception as exc:  # pragma: no cover - Blender runtime only
        code = "bpy_unavailable" if not HAS_BPY else "add_cylinder_error"
        return 500, make_error(code, str(exc))


def _post_object_transform(params: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    try:
        _require_modeling_api()
        modeling_api.transform_object(
            name=params.get("name"),
            location=params.get("location"),
            rotation_euler=params.get("rotation_euler"),
            scale=params.get("scale"),
            delta=bool(params.get("delta", False)),
        )
        return 200, make_success({"name": params.get("name")})
    except LookupError as exc:
        return 404, make_error("not_found", str(exc))
    except Exception as exc:  # pragma: no cover - Blender runtime only
        code = "bpy_unavailable" if not HAS_BPY else "transform_error"
        return 500, make_error(code, str(exc))


PostHandler = Callable[[Dict[str, Any]], Tuple[int, Dict[str, Any]]]
POST_ROUTES: Dict[str, PostHandler] = {
    "/scene/reset": _post_scene_reset,
    "/mesh/add_cube": _post_mesh_add_cube,
    "/mesh/add_plane": _post_mesh_add_plane,
    "/mesh/add_cylinder": _post_mesh_add_cylinder,
    "/object/transform": _post_object_transform,
}


def _parse_json_body(body: bytes) -> Tuple[int, Dict[str, Any]]:
    if not body:
        return 400, make_error("invalid_payload", "Body must be JSON object")
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return 400, make_error("invalid_json", "Body must be valid JSON")
    if not isinstance(payload, dict):
        return 400, make_error("invalid_payload", "Body must be JSON object")
    return 200, payload


def handle_post_request(path: str, body: bytes) -> Tuple[int, Dict[str, Any]]:
    handler = POST_ROUTES.get(path)
    if handler is None:
        return 404, make_error("not_found", "Unknown path")

    status, payload_or_error = _parse_json_body(body)
    if status != 200:
        return status, payload_or_error

    try:
        return handler(payload_or_error)
    except Exception as exc:  # pragma: no cover - defensive
        return 500, make_error("internal_error", "Request handling failed", str(exc))


class RuntimeRequestHandler(BaseHTTPRequestHandler):
    server_version = "MCPBlenderRuntime/0.1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:  # pragma: no cover - silence default logging
        return

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        try:
            body = json.dumps(payload).encode("utf-8")
        except Exception:
            body = b'{"ok": false, "error": {"code": "serialization_error", "message": "failed to encode response", "details": null}}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            # Avoid crashing the handler on write errors.
            pass

    def do_GET(self) -> None:  # noqa: N802
        try:
            parsed_path = urlparse(self.path)
            handler = ROUTES.get(parsed_path.path)
            if handler is None:
                self._send_json(make_error("not_found", "Unknown path"), status=404)
                return

            status, payload = handler()
            self._send_json(payload, status=status)
        except Exception as exc:  # pragma: no cover - defensive
            self._send_json(make_error("internal_error", "Request handling failed", str(exc)), status=500)

    def do_POST(self) -> None:  # noqa: N802
        try:
            parsed_path = urlparse(self.path)
            length = 0
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except Exception:
                length = 0
            body = self.rfile.read(length) if length > 0 else b""
            status, payload = handle_post_request(parsed_path.path, body)
            self._send_json(payload, status=status)
        except Exception as exc:  # pragma: no cover - defensive
            self._send_json(make_error("internal_error", "Request handling failed", str(exc)), status=500)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MCPBLENDER Blender runtime HTTP server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host interface to bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on (default 9876)")
    return parser.parse_args(argv)


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = ThreadingHTTPServer((host, port), RuntimeRequestHandler)
    server.daemon_threads = True
    print(f"MCPBLENDER runtime listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    serve(host=args.host, port=args.port)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main(sys.argv[1:])
