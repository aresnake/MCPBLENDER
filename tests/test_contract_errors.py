import json
import urllib.error

import pytest

from mcpblender_server.server import build_registry
from mcpblender_server.schema import ToolRequest


def test_invalid_json_request():
    with pytest.raises(ValueError):
        ToolRequest.from_json("not-json")


def test_missing_method():
    bad = json.dumps({"params": {}, "request_id": "r1"})
    with pytest.raises(ValueError):
        ToolRequest.from_json(bad)


def test_params_not_object():
    bad = json.dumps({"method": "core.ping", "params": "oops", "request_id": "r1"})
    with pytest.raises(ValueError):
        ToolRequest.from_json(bad)


def test_tool_not_found():
    registry = build_registry(FakeBridge())
    response = registry.dispatch(ToolRequest(method="no.such.tool", params={}, request_id="missing"))
    assert not response.ok
    assert response.error.code == "tool_not_found"


def test_bridge_unreachable_returns_structured_error():
    registry = build_registry(FailingBridge())
    response = registry.dispatch(ToolRequest(method="scene.snapshot", params={}, request_id="snap"))
    assert not response.ok
    assert response.error.code == "bridge_unreachable"
    assert "network down" in response.error.message


class FakeBridge:
    def health(self):
        return {"ok": True}

    def call_rpc(self, method, params):
        return {"ok": True, "data": {"method": method, "params": params}}


class FailingBridge:
    def health(self):
        return {"ok": False, "error": {"code": "bridge_unreachable", "message": "network down"}}

    def call_rpc(self, method, params):
        raise urllib.error.URLError("network down")
