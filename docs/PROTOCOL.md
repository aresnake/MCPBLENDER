# MCPBLENDER Core Protocol

## MCP Server (stdio)
- Transport: newline-delimited JSON over stdio.
- Request: `{ "tool": "<name>", "args": {…}, "request_id": "<uuid>" }`.
- Response: `{ ok: bool, request_id: str, data?: any, error?: {code, message, details?} }`.
- Unknown tool -> `tool_not_found` error. Malformed input -> `invalid_request`.

## Blender HTTP Bridge
- Base URL: `http://127.0.0.1:8765`.
- `GET /health` -> standard response envelope with bridge readiness data.
- `POST /rpc` body: `{tool, args, request_id}`.
- Returns the same response envelope as the MCP server. Errors are encoded in the envelope; HTTP 500 is used for tool failures.

## Data-first actions
- Never require selection; operate directly on `bpy.data` and object names/IDs.
- No `bpy.ops` usage for cube creation or transforms; relies on `bmesh`/data API.
- Transform `space`: `world` (default) applies to world matrix; `local` writes to local transforms.
