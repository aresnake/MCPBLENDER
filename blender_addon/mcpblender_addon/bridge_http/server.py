from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from mcpblender_addon.snapshot.light_snapshot import make_light_snapshot


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


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
            payload = {}

        method = payload.get("method")
        params = payload.get("params") or {}

        if method != "scene.snapshot":
            self._send_json({"ok": False, "error": {"code": "invalid_method", "message": "Unsupported method"}}, status=400)
            return

        try:
            snapshot = make_light_snapshot()
            self._send_json({"ok": True, "data": snapshot}, status=200)
        except Exception as exc:  # pragma: no cover - defensive
            self._send_json({"ok": False, "error": {"code": "snapshot_error", "message": str(exc)}}, status=500)


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
