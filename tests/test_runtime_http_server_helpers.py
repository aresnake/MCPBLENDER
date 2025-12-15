from runtime_blender import http_runtime_server as runtime


def test_envelope_shapes():
    ok = runtime.make_success({"x": 1})
    err = runtime.make_error("oops", "failed")

    assert ok["ok"] is True
    assert ok["result"] == {"x": 1}
    assert err["ok"] is False
    assert err["error"]["code"] == "oops"
    assert err["error"]["details"] is None


def test_routes_registered():
    assert "/health" in runtime.ROUTES
    assert "/runtime/probe" in runtime.ROUTES
    assert "/scene/objects" in runtime.ROUTES
