from __future__ import annotations

import time
from typing import Any, Dict

try:  # pragma: no cover - Blender runtime only
    import bpy
    import bmesh
    from mathutils import Euler, Vector

    HAS_BPY = True
except ImportError:  # pragma: no cover - Blender runtime only
    bpy = None
    bmesh = None
    Euler = None
    Vector = None
    HAS_BPY = False


def _require_bpy() -> None:
    if not HAS_BPY:
        raise RuntimeError("Blender bpy module not available")


def blender_health() -> Dict[str, Any]:
    _require_bpy()
    return {
        "status": "ready",
        "version": getattr(bpy.app, "version_string", "unknown"),
        "scenes": len(bpy.data.scenes),
    }


def _object_payload(obj) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    return {
        "id": getattr(obj, "name_full", obj.name),
        "name": obj.name,
        "type": obj.type,
        "location": tuple(round(v, 6) for v in obj.location[:]),
        "rotation": tuple(round(v, 6) for v in obj.rotation_euler[:]),
        "scale": tuple(round(v, 6) for v in obj.scale[:]),
    }


def capture_snapshot(args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    _require_bpy()
    limit = int(args.get("limit", 100))
    scene = bpy.context.scene
    objects = list(scene.objects)[:limit]
    return {
        "version": "1",
        "scene": scene.name,
        "timestamp": time.time(),
        "objects": [_object_payload(obj) for obj in objects],
    }


def scenegraph_search(args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    _require_bpy()
    query = str(args.get("query", "")).lower()
    matches = []
    for obj in bpy.data.objects:
        if query and query not in obj.name.lower():
            continue
        matches.append(_object_payload(obj))
    return {"count": len(matches), "objects": matches}


def scenegraph_get(args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    _require_bpy()
    identifier = args.get("id") or args.get("name")
    if not identifier:
        raise ValueError("id or name is required")
    obj = bpy.data.objects.get(identifier)
    if obj is None:
        obj = bpy.data.objects.get(str(identifier))
    if obj is None:
        raise LookupError(f"Object {identifier} not found")
    return _object_payload(obj)


def create_cube(args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    _require_bpy()
    name = args.get("name") or "MCP_Cube"
    size = float(args.get("size", 2.0))
    location = args.get("location", (0.0, 0.0, 0.0))
    rotation = args.get("rotation", (0.0, 0.0, 0.0))
    scale = args.get("scale", (1.0, 1.0, 1.0))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    obj.location = Vector(location)
    obj.rotation_euler = Euler(rotation)
    obj.scale = Vector(scale)

    return _object_payload(obj)


def _target_object(args: Dict[str, Any]):  # pragma: no cover - Blender runtime only
    identifier = args.get("id") or args.get("name")
    if not identifier:
        raise ValueError("id or name is required")
    obj = bpy.data.objects.get(identifier)
    if obj is None:
        obj = bpy.data.objects.get(str(identifier))
    if obj is None:
        raise LookupError(f"Object {identifier} not found")
    return obj


def transform_object(args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    _require_bpy()
    obj = _target_object(args)
    space = args.get("space", "world")
    location = args.get("location")
    rotation = args.get("rotation")
    scale = args.get("scale")

    if location is not None:
        vec = Vector(location)
        if space == "world":
            obj.matrix_world.translation = vec
        else:
            obj.location = vec
    if rotation is not None:
        eul = Euler(rotation)
        if space == "world":
            obj.matrix_world.to_euler().rotate(eul)
        else:
            obj.rotation_euler = eul
    if scale is not None:
        scl = Vector(scale)
        obj.scale = scl

    return _object_payload(obj)
