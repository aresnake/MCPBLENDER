# blender_addon/mcpblender_addon/snapshot/__init__.py
# Public snapshot API (canonical)
from .light_snapshot import make_light_snapshot

# Backward-compat alias (older imports)
capture_snapshot = make_light_snapshot
