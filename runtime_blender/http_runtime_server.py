# D:\MCPBLENDER\runtime_blender\http_runtime_server.py
# stdlib-only runtime HTTP server running INSIDE Blender (bpy available)

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple

# ---- Envelope v1 helpers (align with MVP error schema idea "ok/result" + "ok/error") ----

def ok(result: Any) -> Dict[str, Any]:
    return {"ok": True, "result": result}

def err(code: str, message: str, details: Any = None, hint: str | None = None, retryable: bool = False) -> Dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "hint": hint,
            "retryable": retryable,
        },
    }

def _json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

# ---- Blender runtime surface ----

def runtime_probe() -> Dict[str, Any]:
    # minimal probe; keep stable
    try:
        import bpy  # type: ignore
        ver = getattr(bpy.app, "version_string", "unknown")
        return ok({"name": "mcpblender-runtime", "version": ver})
    except Exception as e:
        return err("runtime_error", "bpy not available in this process", details=str(e), retryable=False)

def scene_objects() -> Dict[str, Any]:
    try:
        import bpy  # type: ignore
        objs = []
        for o in bpy.context.scene.objects:
            objs.append({"name": o.name, "type": getattr(o, "type", None)})
        return ok({"objects": objs, "count": len(objs)})
    except Exception as e:
        return err("scene_error", "failed to list scene objects", details=str(e), retryable=False)

# ---- HTTP Handler ----

class Handler(BaseHTTPRequestHandler):
    server_version = "MCPBLENDER-Runtime/1.0"

    def _send(self, status: int, payload: Dict[str, Any]) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, ok({"name": "mcpblender-runtime", "status": "ok"}))
            return
        if self.path == "/runtime/probe":
            payload = runtime_probe()
            self._send(200, payload)
            return
        if self.path == "/scene/objects":
            payload = scene_objects()
            self._send(200, payload)
            return

        self._send(404, err("not_found", f"Unknown route: {self.path}", retryable=False))

    def log_message(self, format: str, *args: Any) -> None:
        # keep Blender console clean
        return

# ---- CLI parsing: IMPORTANT inside Blender ----
# Blender passes its own CLI args into sys.argv. Only args after "--" are for us.
def _extract_script_argv(argv: list[str]) -> list[str]:
    if "--" in argv:
        idx = argv.index("--")
        return argv[idx + 1 :]
    return []

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9876, help="Bind port (default: 9876)")
    script_argv = _extract_script_argv(sys.argv)
    return parser.parse_args(script_argv)

def serve(host: str, port: int) -> None:
    httpd = HTTPServer((host, port), Handler)
    print(f"MCPBLENDER runtime listening on http://{host}:{port}", flush=True)

    # Serve until Ctrl+C stops Blender process
    try:
        httpd.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            httpd.shutdown()
        except Exception:
            pass

def main() -> None:
    args = parse_args()
    serve(args.host, args.port)

if __name__ == "__main__":
    main()
