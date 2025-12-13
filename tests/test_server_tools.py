from mcpblender_server.schema import ToolRequest, error_response, success_response
from mcpblender_server.server import build_registry
from mcpblender_server.state import ServerState


class FakeBridge:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.rpc_calls = []

    def health(self):
        if self.fail:
            return error_response("health", "unavailable", "bridge offline").to_dict()
        return success_response("health", {"status": "ready"}).to_dict()

    def rpc(self, tool, args, request_id):
        self.rpc_calls.append((tool, args, request_id))
        if self.fail:
            return error_response(request_id, "unavailable", "bridge offline").to_dict()
        return success_response(request_id, {"echo": tool, "args": args}).to_dict()


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
