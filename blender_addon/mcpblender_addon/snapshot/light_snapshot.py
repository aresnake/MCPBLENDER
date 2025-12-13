from __future__ import annotations

import time
from typing import Any, Dict

try:  # pragma: no cover - Blender runtime only
    import bpy

    HAS_BPY = True
except ImportError:  # pragma: no cover - Blender runtime only
    bpy = None
    HAS_BPY = False


def capture_snapshot(args: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - Blender runtime only
    if not HAS_BPY:
        raise RuntimeError("Blender bpy module not available")
    scene = bpy.context.scene
    limit = int(args.get("limit", 100))
    objects = list(scene.objects)[:limit]
    payload = {
        "version": "1",
        "scene": scene.name,
        "timestamp": time.time(),
        "objects": [
            {
                "id": getattr(obj, "name_full", obj.name),
                "name": obj.name,
                "type": obj.type,
                "location": tuple(round(v, 6) for v in obj.location[:]),
                "rotation": tuple(round(v, 6) for v in obj.rotation_euler[:]),
                "scale": tuple(round(v, 6) for v in obj.scale[:]),
            }
            for obj in objects
        ],
    }
    return payload
