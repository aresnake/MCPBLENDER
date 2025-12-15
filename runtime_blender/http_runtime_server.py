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
        self._send_json(make_error("method_not_allowed", "Only GET supported"), status=405)


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
