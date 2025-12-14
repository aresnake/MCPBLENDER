import time
from mcpblender_addon.actions.core_actions import capture_snapshot
from mcpblender_addon.actions import core_actions as a

print("SNAP0", len(capture_snapshot({"limit": 999}).get("objects", [])))

res = a.create_cube({"name": "SmokeCube"})
print("CREATE", res)

snap = capture_snapshot({"limit": 999})
names = [o["name"] for o in snap.get("objects", [])]

print("SNAP1", len(names))
print("HAS?", "SmokeCube" in names)
print("CLOSEST:", [n for n in names if "Smoke" in n])
