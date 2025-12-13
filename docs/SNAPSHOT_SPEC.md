SNAPSHOT_SPEC (Canonical) — v1.0
================================

This document freezes the canonical `scene.snapshot` payload contract for MCPBLENDER Core. The v1.0 contract is **stable**: downstream consumers may rely on field presence and semantics. The snapshot must remain lightweight, deterministic-ish, and selection-independent. Deep data (geometry, modifiers, materials, etc.) belongs in `scenegraph.get`, not here.

Compatibility Rules
- Schema version field: `schema_version = "1.0"`.
- v1.x changes MUST be additive-only (new optional fields). Removing/renaming fields or changing meanings is breaking and requires `schema_version = "2.0"`.
- Producers must continue to emit all required fields; consumers should gracefully ignore unknown additions.

Envelope (required top-level)
- `schema_version` (string, required) — fixed to `"1.0"`.
- `blender_version` (string, required).
- `scene` (object, required).
- `objects` (array, required).
- `collections` (array, required).
- `stats` (object, required).
- `camera` (object|null, required; null if none).

scene (required fields)
- `name` (string)
- `frame_current` (int)
- `fps` (float)
- `unit_settings` (object)
  - `system` (string)
  - `length_unit` (string)
  - `scale_length` (float)

objects[] (required fields unless noted)
- `id` (string) — stable handle, `as_pointer()` when available.
- `name` (string)
- `type` (string)
- `location` ([float,float,float])
- `rotation_euler` ([float,float,float])
- `scale` ([float,float,float])
- `bbox_world` (object|null) — `{min:[x,y,z], max:[x,y,z]}` if available, else null.
- `parent_id` (string|null)
- `collections` (array<string>)
- `visible` (boolean)
- `material_names` (array<string>)
- `polycount` (int, OPTIONAL; only for meshes)

collections (required)
- Array of collection names present in the scene (sorted for determinism).

stats (required)
- `objects_count` (int)
- `collections_count` (int)

camera (optional)
- If an active camera exists: `{ id: string, name: string }`; otherwise `null`.

Lightweight Constraint
- No heavy dumps: avoid vertices/edges/loops, modifier stacks, shaders, or binary blobs.
- Capture should be fast and safe; failures should degrade gracefully without throwing.

JSON Example
```json
{
  "schema_version": "1.0",
  "blender_version": "4.2.0",
  "scene": {
    "name": "Scene",
    "frame_current": 1,
    "fps": 24.0,
    "unit_settings": {
      "system": "METRIC",
      "length_unit": "METERS",
      "scale_length": 1.0
    }
  },
  "objects": [
    {
      "id": "139973857851600",
      "name": "Cube",
      "type": "MESH",
      "location": [0.0, 0.0, 0.0],
      "rotation_euler": [0.0, 0.0, 0.0],
      "scale": [1.0, 1.0, 1.0],
      "bbox_world": {
        "min": [-1.0, -1.0, -1.0],
        "max": [1.0, 1.0, 1.0]
      },
      "parent_id": null,
      "collections": ["Collection"],
      "visible": true,
      "material_names": [],
      "polycount": 12
    }
  ],
  "collections": ["Collection"],
  "stats": {
    "objects_count": 1,
    "collections_count": 1
  },
  "camera": null
}
```
