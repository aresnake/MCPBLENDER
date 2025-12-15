# MVP Integration Guide (Milestone M7)

This repo now ships a minimal Blender-coupled HTTP runtime intended for the MVP core that listens on `http://127.0.0.1:9876`.

## 1) Start MVP HTTP server
- From the MVP repo, launch the existing core HTTP server (already bound to `http://127.0.0.1:8765`). Keep it running while you start Blender runtime.

## 2) Start MCPBLENDER runtime
- Ensure Blender 5.0 is installed or set `BLENDER_EXE` to your blender executable path.
- From this repo, run `scripts/run_runtime_http.ps1`. It tries `$env:BLENDER_EXE`, then `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`, then `D:\Blender_5.0.0_Portable\blender.exe`.
- The server runs headless inside Blender:  
  `blender.exe --background --python runtime_blender/http_runtime_server.py -- --port 9876`
- You should see: `MCPBLENDER runtime listening on http://127.0.0.1:9876`.

## 3) Smoke test
- With the runtime server running, execute `scripts/smoke_runtime_http.ps1`.
- It will GET:
  - `http://127.0.0.1:9876/health`
  - `http://127.0.0.1:9876/runtime/probe`
  - `http://127.0.0.1:9876/scene/objects`
- Responses are printed as pretty JSON envelopes (`{"ok": true|false, ...}`).

## M9 modeling
- Start the runtime as above, then run `scripts/smoke_modeling_http.ps1` to exercise modeling endpoints.
- The smoke script posts to `/scene/reset`, adds cube/plane/cylinder, transforms the cube, and finally fetches `/scene/objects` to verify results.

## Notes
- Ports: runtime defaults to `127.0.0.1:9876`. MVP core continues on `127.0.0.1:8765`. Adjust with `--host/--port` flags on the Blender runtime if needed.
- Environment: set `BLENDER_EXE` to override the Blender path used by `run_runtime_http.ps1`.
- Testing: runtime validated via the smoke script above; unit tests for envelopes live in `tests/test_runtime_http_server_helpers.py`.
