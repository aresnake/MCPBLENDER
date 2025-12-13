from __future__ import annotations

import sys
from typing import Any, Callable, Dict

from mcpblender_server.bridge_client import BridgeClient
from mcpblender_server.schema import ResponsePayload, ToolRequest, error_response
from mcpblender_server.state import ServerState
from mcpblender_server.tools import register_tools


class ToolRegistry:
    def __init__(self, bridge_client: BridgeClient, state: ServerState | None = None) -> None:
        self.bridge_client = bridge_client
        self.state = state or ServerState()
        self._tools: Dict[str, Callable[[ToolRequest], ResponsePayload]] = {}

    def register(self, name: str, handler: Callable[[ToolRequest], ResponsePayload]) -> None:
        self._tools[name] = handler

    def response_from_bridge(self, payload: Any, fallback_request_id: str) -> ResponsePayload:
        from mcpblender_server.schema import ResponsePayload as RP

        response = RP.from_mapping(payload, fallback_request_id)
        if not response.ok and response.error:
            self.state.record_error({"code": response.error.code, "message": response.error.message})
        return response

    def dispatch(self, request: ToolRequest) -> ResponsePayload:
        self.state.record_request(request.request_id, request.tool)
        handler = self._tools.get(request.tool)
        if handler is None:
            return error_response(request.request_id, "tool_not_found", f"Tool '{request.tool}' is not registered")
        try:
            return handler(request)
        except Exception as exc:  # pragma: no cover - defensive path
            self.state.record_error({"type": exc.__class__.__name__, "message": str(exc)})
            return error_response(request.request_id, "internal_error", str(exc))


def build_registry(bridge_client: BridgeClient, state: ServerState | None = None) -> ToolRegistry:
    registry = ToolRegistry(bridge_client, state=state)
    register_tools(registry)
    return registry


def run_stdio_server() -> None:
    """Run a simple newline-delimited JSON stdio server."""

    def send(response: ResponsePayload) -> None:
        sys.stdout.write(response.to_json() + "\n")
        sys.stdout.flush()

    with BridgeClient() as bridge:
        registry = build_registry(bridge)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = ToolRequest.from_json(line)
            except Exception as exc:
                send(error_response("unknown", "invalid_request", str(exc)))
                continue
            response = registry.dispatch(request)
            send(response)


if __name__ == "__main__":  # pragma: no cover
    run_stdio_server()
