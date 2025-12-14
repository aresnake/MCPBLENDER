from types import SimpleNamespace

import mcpblender_addon.actions.core_actions as core


class FakeVector(list):
    def __init__(self, values):
        super().__init__(values)
        self.x, self.y, self.z = values

    def copy(self):
        return FakeVector([self.x, self.y, self.z])


class FakeEuler(tuple):
    pass


class FakeMatrix:
    def __init__(self, translation=None, rotation=None, scale=None):
        self.translation = translation or FakeVector([0.0, 0.0, 0.0])
        self.rotation = rotation
        self._scale = scale or FakeVector([1.0, 1.0, 1.0])

    def to_scale(self):
        return self._scale


class FakeMatrixBuilder:
    @staticmethod
    def LocRotScale(translation, rotation, scale):
        return FakeMatrix(translation=translation, rotation=rotation, scale=scale)


def test_world_rotation_updates_matrix(monkeypatch):
    obj = SimpleNamespace(
        name="Cube",
        type="MESH",
        location=FakeVector([0.0, 0.0, 0.0]),
        rotation_euler=None,
        scale=FakeVector([1.0, 1.0, 1.0]),
        matrix_world=FakeMatrix(),
    )

    monkeypatch.setattr(core, "HAS_BPY", True)
    monkeypatch.setattr(core, "_require_bpy", lambda: None)
    monkeypatch.setattr(core, "Vector", FakeVector)
    monkeypatch.setattr(core, "Euler", lambda seq: FakeEuler(seq))
    monkeypatch.setattr(core, "Matrix", FakeMatrixBuilder)
    monkeypatch.setattr(core, "_target_object", lambda args: obj)

    rotation = (0.1, 0.2, 0.3)
    core.transform_object({"rotation": rotation, "space": "world"})

    assert isinstance(obj.matrix_world, FakeMatrix)
    assert obj.matrix_world.rotation == rotation
    assert obj.rotation_euler == rotation
