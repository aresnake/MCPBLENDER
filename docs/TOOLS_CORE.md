# Core Tools

All tools return `{ ok: bool, request_id: str, data?, error? }`.

- `core.ping` — Local heartbeat; returns `{message:"pong"}`.
- `blender.health` — Probes Blender bridge `/health` for readiness and version.
- `scene.snapshot` — Light snapshot v1 of active scene (name, timestamp, objects[id,name,type,location,rotation,scale]).
- `scenegraph.search` — Query objects by name substring; returns count and objects payloads.
- `scenegraph.get` — Resolve a single object by `id` or `name`; returns the canonical object payload.
- `object.create_cube` — Data-first cube creation (bmesh), accepts `name`, `size`, `location`, `rotation`, `scale`.
- `object.transform` — Apply transforms by `id` or `name`; supports `location`, `rotation`, `scale`, and `space` (world/local).
- `diagnostics.tail` — Returns recent logs, last error (if any), and recent request IDs from the MCP server.
