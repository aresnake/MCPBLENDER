from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from mcpblender_addon import actions


class _Handler(BaseHTTPRequestHandler):
    server_version = "MCPBlenderBridge/1.0"
    protocol_version = "HTTP/1.1"

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:  # pragma: no cover - quiet handler
        return

    def do_GET(self):  # noqa: N802
        if self.path != "/health":
            self._send_json({"ok": False, "request_id": "health", "error": {"code": "not_found", "message": "Unknown path"}}, status=404)
            return
        try:
            payload = actions.blender_health()
            response = actions.build_response(True, "health", payload)
        except Exception as exc:  # pragma: no cover - Blender runtime only
            response = actions.build_response(False, "health", error={"code": "health_error", "message": str(exc)})
        self._send_json(response)

    def do_POST(self):  # noqa: N802
        if self.path != "/rpc":
            self._send_json({"ok": False, "request_id": "rpc", "error": {"code": "not_found", "message": "Unknown path"}}, status=404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        request_id = "bridge"
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
            request_id = payload.get("request_id") or request_id
            tool = payload.get("tool")
            args = payload.get("args", {}) or {}
            response = actions.dispatch_tool(tool, args, request_id)
        except Exception as exc:  # pragma: no cover - defensive
            response = actions.build_response(False, request_id, error={"code": "bridge_error", "message": str(exc)})
        self._send_json(response, status=200 if response.get("ok") else 500)


class BridgeServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.address = (host, port)
        self._server = ThreadingHTTPServer(self.address, _Handler)
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        if self._thread is not None:
            self._thread.join(timeout=1)


def launch_server(host: str = "127.0.0.1", port: int = 8765) -> BridgeServer:
    server = BridgeServer(host=host, port=port)
    if not actions.HAS_BPY:
        raise RuntimeError("Blender (bpy) is required to start the bridge HTTP server")
    server.start()
    return server


def main() -> None:  # pragma: no cover - Blender runtime only
    if not actions.HAS_BPY:
        print("bpy not available; run from inside Blender")
        return
    server = launch_server()
    print(f"Bridge running on http://{server.address[0]}:{server.address[1]}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":  # pragma: no cover
    main()
