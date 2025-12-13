from __future__ import annotations

"""
Canonical light snapshot (scene.snapshot) v1.0.

Designed to be fast, deterministic-ish, and safe. No heavy mesh data; deep inspection
belongs in scenegraph.get.
"""

import sys
import time
from typing import Any, Dict, List, Optional, Tuple

SNAPSHOT_SCHEMA_VERSION = "1.0"

try:  # pragma: no cover - Blender runtime only
    import bpy
    from mathutils import Vector

    HAS_BPY = True
except ImportError:  # pragma: no cover - Blender runtime only
    bpy = None
    Vector = None
    HAS_BPY = False


def _safe_call(fn, default=None):
    try:
        return fn()
    except Exception:  # pragma: no cover - defensive
        return default


def _round_vec(vec: Any) -> List[float]:
    try:
        return [round(float(v), 6) for v in vec[:3]]
    except Exception:  # pragma: no cover - defensive
        return [0.0, 0.0, 0.0]


def _bbox_world(obj) -> Optional[Dict[str, List[float]]]:  # pragma: no cover - Blender runtime only
    try:
        coords = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        xs = [c.x for c in coords]
        ys = [c.y for c in coords]
        zs = [c.z for c in coords]
        return {
            "min": [round(min(xs), 6), round(min(ys), 6), round(min(zs), 6)],
            "max": [round(max(xs), 6), round(max(ys), 6), round(max(zs), 6)],
        }
    except Exception:
        return None


def _object_payload(obj) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    obj_id = _safe_call(lambda: str(obj.as_pointer()), obj.name)
    collections = _safe_call(lambda: [c.name for c in obj.users_collection], [])
    visible = _safe_call(lambda: obj.visible_get(), True)
    materials = _safe_call(lambda: [m.name for m in obj.material_slots if m.material], [])
    bbox = _bbox_world(obj)
    polycount = None
    if obj.type == "MESH":
        polycount = _safe_call(lambda: len(obj.data.polygons), None)

    return {
        "id": obj_id,
        "name": obj.name,
        "type": obj.type,
        "location": _round_vec(obj.location),
        "rotation_euler": _round_vec(obj.rotation_euler),
        "scale": _round_vec(obj.scale),
        "bbox_world": bbox,
        "parent_id": _safe_call(lambda: str(obj.parent.as_pointer()) if obj.parent else None, None),
        "collections": collections,
        "visible": bool(visible),
        "material_names": materials,
        **({"polycount": polycount} if polycount is not None else {}),
    }


def _scene_payload(scene) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    return {
        "name": scene.name,
        "frame_current": int(scene.frame_current),
        "fps": _safe_call(lambda: float(scene.render.fps / scene.render.fps_base), 0.0),
        "unit_settings": {
            "system": _safe_call(lambda: scene.unit_settings.system, ""),
            "length_unit": _safe_call(lambda: scene.unit_settings.length_unit, ""),
            "scale_length": _safe_call(lambda: float(scene.unit_settings.scale_length), 1.0),
        },
    }


def _camera_payload(scene) -> Optional[Dict[str, Any]]:  # pragma: no cover - Blender runtime only
    cam = getattr(scene, "camera", None)
    if not cam:
        return None
    return {
        "id": _safe_call(lambda: str(cam.as_pointer()), cam.name),
        "name": cam.name,
    }


def make_light_snapshot() -> Dict[str, Any]:
    """
    Build a canonical light snapshot. Never raises; errors are swallowed and replaced
    with safe defaults to keep the contract stable.
    """
    if not HAS_BPY:  # pragma: no cover - defensive for non-Blender envs
        return {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "blender_version": "unavailable",
            "scene": {},
            "objects": [],
            "collections": [],
            "stats": {"objects_count": 0, "collections_count": 0},
            "camera": None,
            "error": "bpy_unavailable",
        }

    scene = bpy.context.scene
    objects = sorted(list(scene.objects), key=lambda o: o.name)
    collection_names = []
    try:
        collection_names.append(scene.collection.name)
        collection_names.extend([c.name for c in scene.collection.children_recursive])
    except Exception:
        collection_names = []
    collections = sorted({name for name in collection_names})

    object_payloads = [_safe_call(lambda obj=obj: _object_payload(obj), {}) for obj in objects]

    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "blender_version": _safe_call(lambda: bpy.app.version_string, ""),
        "scene": _scene_payload(scene),
        "objects": object_payloads,
        "collections": collections,
        "stats": {
            "objects_count": len(objects),
            "collections_count": len(collections),
        },
        "camera": _camera_payload(scene),
    }

    return snapshot
