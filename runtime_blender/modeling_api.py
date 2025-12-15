from __future__ import annotations

from typing import Dict, List, Optional, Sequence

try:  # pragma: no cover - Blender runtime only
    import bpy
    import bmesh
    from mathutils import Vector

    HAS_BPY = True
except Exception:  # pragma: no cover - allow import in tests
    bpy = None
    bmesh = None
    Vector = None
    HAS_BPY = False


def _require_bpy() -> None:
    if not HAS_BPY:
        raise RuntimeError("bpy not available (run inside Blender)")


def _ensure_location(vec) -> Optional[Vector]:
    if vec is None:
        return None
    if len(vec) != 3:
        raise ValueError("location must have 3 components")
    return Vector(vec)


def reset_scene() -> int:
    _require_bpy()
    objs = list(bpy.data.objects)
    for obj in objs:
        bpy.data.objects.remove(obj, do_unlink=True)
    return len(objs)


def _link_object(obj) -> None:
    collection = bpy.context.scene.collection if bpy.context and bpy.context.scene else None
    if collection is None:
        raise RuntimeError("No active scene to link object")
    collection.objects.link(obj)


def _new_mesh_from_bmesh(name: str, builder) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    builder(bm)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    _link_object(obj)
    return obj


def add_cube(name: Optional[str] = None, size: float = 2.0, location: Optional[Sequence[float]] = None) -> Dict:
    _require_bpy()
    obj_name = name or "Cube"
    obj = _new_mesh_from_bmesh(obj_name, lambda bm: bmesh.ops.create_cube(bm, size=size))
    loc = _ensure_location(location)
    if loc is not None:
        obj.location = loc
    return {"name": obj.name, "type": obj.type, "location": list(obj.location)}


def add_plane(name: Optional[str] = None, size: float = 2.0, location: Optional[Sequence[float]] = None) -> Dict:
    _require_bpy()
    obj_name = name or "Plane"
    obj = _new_mesh_from_bmesh(
        obj_name,
        lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2.0),
    )
    loc = _ensure_location(location)
    if loc is not None:
        obj.location = loc
    return {"name": obj.name, "type": obj.type, "location": list(obj.location)}


def add_cylinder(
    name: Optional[str] = None,
    radius: float = 1.0,
    depth: float = 2.0,
    vertices: int = 32,
    location: Optional[Sequence[float]] = None,
) -> Dict:
    _require_bpy()
    obj_name = name or "Cylinder"

    def build_cylinder(bm):
        bmesh.ops.create_cone(
            bm,
            segments=vertices,
            diameter1=radius * 2.0,
            diameter2=radius * 2.0,
            depth=depth,
            cap_ends=True,
        )

    obj = _new_mesh_from_bmesh(obj_name, build_cylinder)
    loc = _ensure_location(location)
    if loc is not None:
        obj.location = loc
    return {"name": obj.name, "type": obj.type, "location": list(obj.location)}


def _maybe_vector(value: Optional[Sequence[float]]) -> Optional[Vector]:
    if value is None:
        return None
    if len(value) != 3:
        raise ValueError("vector fields must have 3 components")
    return Vector(value)


def _apply_delta(base: Vector, delta: Vector) -> Vector:
    return Vector((base.x + delta.x, base.y + delta.y, base.z + delta.z))


def transform_object(
    name: str,
    location: Optional[Sequence[float]] = None,
    rotation_euler: Optional[Sequence[float]] = None,
    scale: Optional[Sequence[float]] = None,
    delta: bool = False,
) -> None:
    _require_bpy()
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise LookupError(f"Object '{name}' not found")

    loc_vec = _maybe_vector(location)
    rot_vec = _maybe_vector(rotation_euler)
    scale_vec = _maybe_vector(scale)

    if delta:
        if loc_vec is not None:
            obj.location = _apply_delta(obj.location, loc_vec)
        if rot_vec is not None:
            obj.rotation_euler = _apply_delta(obj.rotation_euler, rot_vec)
        if scale_vec is not None:
            obj.scale = Vector(
                (obj.scale.x + scale_vec.x, obj.scale.y + scale_vec.y, obj.scale.z + scale_vec.z)
            )
    else:
        if loc_vec is not None:
            obj.location = loc_vec
        if rot_vec is not None:
            obj.rotation_euler = rot_vec
        if scale_vec is not None:
            obj.scale = scale_vec

    return None
