# MCPBLENDER — CONTEXT (Source of Truth)

## Role
MCPBLENDER is the Blender runtime and execution layer for MVP.
It owns all Blender and bpy-related logic.

## Responsibilities
- Expose Blender state via HTTP runtime server
- Execute modeling macros and scene mutations
- Support headless and UI-open Blender modes
- Remain data-first where possible

## Non-Goals
- No MCP contracts
- No host logic
- No orchestration or planning logic

## Exposed Runtime API (current)
- GET /health
- GET /runtime/probe
- GET /scene/objects

## Architecture Invariants
- Stable HTTP envelopes
- Blender 5.x compatible
- No dependency on MVP internals
- Runtime can be replaced or restarted independently

## Current Milestones
- M7: Blender HTTP runtime server ✅
- M8: MVP external adapter integration ✅
- M9: modeling primitives (planned)

## Modeling Philosophy
- Prefer data-first operations
- Use bpy.ops only when unavoidable
- Support macros: mesh primitives, transforms, booleans

## Source of Truth
This file defines what MCPBLENDER IS and IS NOT.
