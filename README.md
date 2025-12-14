# MCPBLENDER Core

Mono-repo combining:
- A Blender add-on HTTP bridge that exposes scene tools on `http://127.0.0.1:9876`.
- A stdio MCP server that forwards MCP tool calls to the bridge using `{method, params}` payloads.

## Run modes

### 1) Blender HTTP bridge (inside Blender)
- Install/point PYTHONPATH to `blender_addon`.
- Start Blender headless:  
  `blender --background --python blender_addon/mcpblender_addon/bridge_http/server.py`
- Bridge listens on `http://127.0.0.1:9876` and serves `/health` + `/rpc`.
- Payload shape for `/rpc`: `{"method": "<tool>", "params": {...}}`.

### 2) MCP stdio server
- Ensure the bridge is running (same machine, port 9876).
- PYTHONPATH should include `server_mcp/src`.
- Run: `python -m mcpblender_server.server` (newline-delimited JSON over stdio).
- Request shape: `{"method": "<tool>", "params": {...}, "request_id": "<id>"}`.
- The server simply forwards `{method, params}` to the bridge and returns the bridge envelope.

### 3) FastMCP adapter
- `python -m mcpblender_server.mcp_stdio` exposes MCP tools via the Model Context Protocol server SDK.

## Tools exposed
See `docs/TOOLS_CORE.md` for full list. Key methods:
- `scene.snapshot`
- `scenegraph.search`, `scenegraph.get`
- `object.create_cube`, `object.move_object`, `object.transform`
- `material.assign_simple`
- `diagnostics.tail` (server diagnostics only)

## Development
- Tests: `pytest -q`
- Headless Blender smoke: `blender --background --python tests_headless/smoke.py`
