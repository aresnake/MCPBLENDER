# Snapshot Spec v1

`scene.snapshot` returns:

```
{
  version: "1",
  scene: <active scene name>,
  timestamp: <unix epoch>,
  objects: [
    { id, name, type, location: [x,y,z], rotation: [x,y,z], scale: [x,y,z] }
  ]
}
```

- Sorted order: Blender provides objects in collection order; payload is emitted in that stable order.
- Deterministic numeric output rounded to 6 decimals.
- Use `scenegraph.get` for deeper per-object details if extended metadata is needed.
- `limit` arg (default 100) caps the number of objects captured.
