import json

import pytest

from mcpblender_addon.bridge_http import server


def test_payload_too_large():
    body = b"x" * (server.MAX_BODY_BYTES + 1)
    resp = server.handle_rpc_bytes(body)
    assert not resp["ok"]
    assert resp["error"]["code"] == "payload_too_large"


def test_unknown_method_returns_tool_not_found():
    body = json.dumps({"method": "nope", "params": {}}).encode()
    resp = server.handle_rpc_bytes(body)
    assert not resp["ok"]
    assert resp["error"]["code"] == "tool_not_found"


def test_internal_exception_stable_envelope(monkeypatch):
    def boom_map(params):
        return {"scene.snapshot": lambda: (_ for _ in ()).throw(RuntimeError("boom"))}

    monkeypatch.setattr(server, "_handler_map", boom_map)
    body = json.dumps({"method": "scene.snapshot", "params": {}}).encode()
    resp = server.handle_rpc_bytes(body)
    assert not resp["ok"]
    assert resp["error"]["code"] == "internal_error"
    assert "boom" in resp["error"]["message"]


def test_health_payload_contains_fields():
    payload = server.health_payload()
    assert payload["ok"] is True
    assert payload["source"] == "mcpblender_bridge"
    assert "version" in payload
    assert "uptime_seconds" in payload
    assert "blender_version" in payload
    assert "ready" in payload
