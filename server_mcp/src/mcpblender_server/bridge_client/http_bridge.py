from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict


class BridgeClient:
    """HTTP client for the Blender bridge with retries and timeouts."""

    def __init__(self, base_url: str = "http://127.0.0.1:9876", timeout: float = 2.0, retries: int = 2) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries

    def health(self) -> Dict[str, Any]:
        try:
            def op() -> Dict[str, Any]:
                req = urllib.request.Request(f"{self.base_url}/health", method="GET")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            return self._with_retries(op)
        except Exception as exc:
            return {"ok": False, "error": {"code": "bridge_unreachable", "message": str(exc)}}

    def rpc(self, tool: str, args: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        payload = json.dumps({"tool": tool, "args": args or {}, "request_id": request_id}).encode("utf-8")

        def op() -> Dict[str, Any]:
            req = urllib.request.Request(
                f"{self.base_url}/rpc",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))

        return self._with_retries(op)

    def call_rpc(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = json.dumps({"method": method, "params": params or {}}).encode("utf-8")

        def op() -> Dict[str, Any]:
            req = urllib.request.Request(
                f"{self.base_url}/rpc",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))

        try:
            return self._with_retries(op)
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            return {"ok": False, "error": {"code": "bridge_unreachable", "message": str(exc)}}
        except Exception as exc:  # pragma: no cover - defensive
            return {"ok": False, "error": {"code": "bridge_error", "message": str(exc)}}

    def _with_retries(self, fn):
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                return fn()
            except (urllib.error.URLError, urllib.error.HTTPError) as exc:
                last_error = exc
                time.sleep(0.15 * (attempt + 1))
        if last_error:
            raise last_error
        raise RuntimeError("Bridge request failed without specific error")

    def close(self) -> None:
        # urllib has no persistent state; method kept for API compatibility.
        return None

    def __enter__(self) -> "BridgeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
