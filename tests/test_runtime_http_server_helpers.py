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
    assert "/scene/reset" in runtime.POST_ROUTES
    assert "/mesh/add_cube" in runtime.POST_ROUTES
    assert "/mesh/add_plane" in runtime.POST_ROUTES
    assert "/mesh/add_cylinder" in runtime.POST_ROUTES
    assert "/object/transform" in runtime.POST_ROUTES


def test_unknown_post_route_returns_not_found():
    status, payload = runtime.handle_post_request("/not-a-route", b"{}")
    assert status == 404
    assert payload["ok"] is False
    assert payload["error"]["code"] == "not_found"


def test_missing_body_returns_invalid_payload():
    status, payload = runtime.handle_post_request("/scene/reset", b"")
    assert status == 400
    assert payload["ok"] is False
    assert payload["error"]["code"] in {"invalid_payload", "invalid_json"}
