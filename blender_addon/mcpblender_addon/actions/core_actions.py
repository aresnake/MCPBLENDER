from __future__ import annotations

import time
from typing import Any, Dict

try:  # pragma: no cover - Blender runtime only
    import bpy
    import bmesh
    from mathutils import Euler, Matrix, Vector

    HAS_BPY = True
except ImportError:  # pragma: no cover - Blender runtime only
    bpy = None
    bmesh = None
    Euler = None
    Matrix = None
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
            obj.location = vec
        else:
            obj.location = vec
    if rotation is not None:
        eul = Euler(rotation)
        if space == "world":
            translation = getattr(obj.matrix_world, "translation", Vector(obj.location))
            current_scale = obj.matrix_world.to_scale() if hasattr(obj.matrix_world, "to_scale") else obj.scale
            obj.rotation_euler = eul
            obj.matrix_world = Matrix.LocRotScale(translation, eul, current_scale)
        else:
            obj.rotation_euler = eul
    if scale is not None:
        scl = Vector(scale)
        obj.scale = scl

    return _object_payload(obj)


def delete_object(args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    _require_bpy()
    name = args.get("name") or args.get("object")
    if not name:
        raise ValueError("name is required")
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise LookupError(f"Object {name} not found")
    bpy.data.objects.remove(obj, do_unlink=True)
    return {"deleted": name}


def assign_material_simple(args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    _require_bpy()
    target_name = args.get("object") or args.get("name")
    if not target_name:
        raise ValueError("object (name) is required")
    obj = bpy.data.objects.get(target_name)
    if obj is None:
        raise LookupError(f"Object {target_name} not found")
    if obj.type != "MESH":
        raise ValueError("Material assignment requires mesh object")

    mat_name = args.get("material_name") or args.get("name") or "Mat"
    color = args.get("color") or args.get("base_color") or [0.8, 0.8, 0.8, 1.0]
    if len(color) == 3:
        color = [*color, 1.0]

    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(mat_name)

    try:
        mat.use_nodes = True
        tree = mat.node_tree
        principled = None
        output = None
        if tree:
            for node in tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    principled = node
                if node.type == "OUTPUT_MATERIAL":
                    output = node
            if principled is None:
                principled = tree.nodes.new("ShaderNodeBsdfPrincipled")
            if output is None:
                output = tree.nodes.new("ShaderNodeOutputMaterial")
            principled.inputs["Base Color"].default_value = color
            if not principled.outputs["BSDF"].is_linked:
                tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    except Exception:
        if hasattr(mat, "diffuse_color"):
            mat.diffuse_color = color

    slots = obj.data.materials
    if not slots:
        slots.append(mat)
    else:
        slots[0] = mat

    return {"material_name": mat.name, "object": obj.name}
