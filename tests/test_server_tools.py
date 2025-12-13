from mcpblender_server.schema import ToolRequest, error_response, success_response
from mcpblender_server.server import build_registry
from mcpblender_server.state import ServerState


class FakeBridge:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.rpc_calls = []
        self.call_rpc_calls = []

    def health(self):
        if self.fail:
            return error_response("health", "unavailable", "bridge offline").to_dict()
        return success_response("health", {"status": "ready"}).to_dict()

    def rpc(self, tool, args, request_id):
        self.rpc_calls.append((tool, args, request_id))
        if self.fail:
            return error_response(request_id, "unavailable", "bridge offline").to_dict()
        return success_response(request_id, {"echo": tool, "args": args}).to_dict()

    def call_rpc(self, method, params):
        self.call_rpc_calls.append((method, params))
        if self.fail:
            return {"ok": False, "error": {"code": "unavailable", "message": "bridge offline"}}
        return {"ok": True, "data": {"method": method, "params": params}}


def test_core_ping():
    registry = build_registry(FakeBridge())
    response = registry.dispatch(ToolRequest(tool="core.ping", args={}, request_id="r1"))
    assert response.ok
    assert response.data["message"] == "pong"


def test_unknown_tool():
    registry = build_registry(FakeBridge())
    response = registry.dispatch(ToolRequest(tool="not.real", args={}, request_id="r2"))
    assert not response.ok
    assert response.error.code == "tool_not_found"


def test_proxy_to_bridge_and_diagnostics():
    state = ServerState()
    bridge = FakeBridge()
    registry = build_registry(bridge, state=state)
    response = registry.dispatch(ToolRequest(tool="scenegraph.search", args={"query": "Cube"}, request_id="r3"))
    assert response.ok
    assert bridge.rpc_calls[0][0] == "scenegraph.search"

    diag = registry.dispatch(ToolRequest(tool="diagnostics.tail", args={}, request_id="diag"))
    assert diag.ok
    assert "r3" in diag.data["recent_request_ids"]


def test_bridge_error_passthrough():
    bridge = FakeBridge(fail=True)
    registry = build_registry(bridge)
    response = registry.dispatch(ToolRequest(tool="blender.health", args={}, request_id="r4"))
    assert not response.ok
    assert response.error.code == "unavailable"


def test_scene_snapshot_call_rpc():
    bridge = FakeBridge()
    registry = build_registry(bridge)
    response = registry.dispatch(ToolRequest(tool="scene.snapshot", args={}, request_id="snap"))
    assert response.ok
    assert bridge.call_rpc_calls[0][0] == "scene.snapshot"
    assert response.data["method"] == "scene.snapshot"


def test_object_move_object_success():
    bridge = FakeBridge()
    registry = build_registry(bridge)
    response = registry.dispatch(
        ToolRequest(tool="object.move_object", args={"id": "123", "delta": [1, 0, 0]}, request_id="move1")
    )
    assert response.ok
    assert bridge.call_rpc_calls[-1][0] == "object.move_object"
    assert response.data["params"]["delta"] == [1, 0, 0]


def test_material_assign_simple_failure():
    bridge = FakeBridge(fail=True)
    registry = build_registry(bridge)
    response = registry.dispatch(
        ToolRequest(tool="material.assign_simple", args={"name": "Cube"}, request_id="mat1")
    )
    assert not response.ok
    assert response.error.code == "unavailable"
