from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from mcpblender_server.schema import ResponsePayload, success_response

if TYPE_CHECKING:  # pragma: no cover
    from mcpblender_server.server import ToolRegistry
    from mcpblender_server.schema import ToolRequest


def register_tools(registry: "ToolRegistry") -> None:
    bridge = registry.bridge_client
    state = registry.state

    def proxy(tool_name: str) -> Callable[["ToolRequest"], ResponsePayload]:
        def handler(request: "ToolRequest") -> ResponsePayload:
            raw = bridge.rpc(tool_name, request.args, request.request_id)
            return registry.response_from_bridge(raw, request.request_id)

        return handler

    def call_proxy(method: str) -> Callable[["ToolRequest"], ResponsePayload]:
        def handler(request: "ToolRequest") -> ResponsePayload:
            raw = bridge.call_rpc(method, request.args)
            return registry.response_from_bridge(raw, request.request_id)

        return handler

    registry.register(
        "core.ping",
        lambda request: success_response(
            request.request_id,
            {"message": "pong", "server": "mcpblender-core"},
        ),
    )

    registry.register(
        "blender.health",
        lambda request: registry.response_from_bridge(bridge.health(), request.request_id),
    )

    registry.register("scene.snapshot", call_proxy("scene.snapshot"))
    registry.register("scenegraph.search", proxy("scenegraph.search"))
    registry.register("scenegraph.get", proxy("scenegraph.get"))
    registry.register("object.create_cube", call_proxy("object.create_cube"))
    registry.register("object.move_object", call_proxy("object.move_object"))
    registry.register("object.transform", proxy("object.transform"))
    registry.register("material.assign_simple", call_proxy("material.assign_simple"))

    registry.register(
        "diagnostics.tail",
        lambda request: success_response(request.request_id, state.diagnostics_payload()),
    )
