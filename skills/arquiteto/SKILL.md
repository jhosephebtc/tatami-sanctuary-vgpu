---
name: arquiteto
description: >-
  Code-first 3D architecture, product, and interactive environment skill for Blender 4.2+
  and WebGPU (Vercel vgpu). Turns a hand-drawn sketch, floor plan, or visual references
  into a piece-by-piece Blender Python scene with real Cloth physics, seamless PBR
  textures, CC0 botanical assets, Khronos PBR Neutral lighting, and a live WebGPU
  browser experience powered by Vercel's vgpu. Use whenever creating 3D architecture,
  interiors, mechanisms, Blender Python models, or Blender-to-WebGPU browser scenes.
---

# Arquiteto (`arquiteto`)

A unified code-first 3D production skill combining piece-by-piece architectural modeling in **Blender Python**, physical Cloth & PBR authoring, and live browser delivery powered by **Vercel Labs' `vgpu` (WebGPU)**.

## Core Rules

1. **Numbers & visual direction first**: Before writing geometry, convert any sketch, floor plan, or reference images into real metric dimensions (`m` / `mm`), room bounds, wall thicknesses, openings, and explicit PBR material specs. Dimension labels always beat sketch pixels.
2. **Build like a carpenter (every part is its own object)**: Footings, floor boards, individual tatami mats with *heri* borders, posts, beams, rafters, shoji stiles/rails/*kumiko* strips, bed slats, lamp frames, and fixtures are authored as separate tagged objects (`STAGE`) so they can be inspected, animated, or selectively exported.
3. **Real physics & seamless PBR**:
   - Use real Blender **Cloth** and **Cloth Pressure** simulations for bedding, curtains, and soft fabrics, then bake the settled frame (`depsgraph` evaluated mesh) before glTF/GLB export.
   - Generate or use **seamless tileable PBR image maps** (sRGB Albedo, linear Non-Color Roughness, linear OpenGL Normal) with aligned long-axis UVs and subtle *wabi-sabi* natural wear so materials look identical in Blender Cycles and WebGPU glTF.
   - Use **Khronos PBR Neutral** (`THREE.NeutralToneMapping` in WebGPU) — never AgX when preserving warm tungsten/sunset tones.
4. **Visual audit every stage**: Never ship geometry, lighting, or video without inspecting real renders/screenshots side by side against references and fixing clipping, floating geometry, or doubled lights.
5. **Browser-first engine = Vercel `vgpu` (WebGPU)**:
   - Whenever a 3D scene, shader, or Blender-exported `.glb` runs in the browser, prioritize **`vgpu` (Vercel Labs)** (`vgpu`, `vgpu/three` `tslExports`, `@vgpu/wgsl-std`, plus `vgpu/node` / `vgpu/mock` for headless testing).
   - Always install the companion **`vercel-labs/vgpu`** skill (`npx skills add vercel-labs/vgpu -g`) and query the project-local `vgpu docs` CLI (`npm exec --no -- vgpu docs cat ...`) as the API authority.
   - Strip imported `KHR_lights_punctual` lights or set `export_lights=False` during glTF export when authoring dedicated WebGPU scene lighting + IBL environments to prevent doubled/overexposed lighting.

## Included Runtime Toolkit (`SKILL_DIR`)

- `kit/bkit.py` — Shared Blender helpers (Cycles GPU setup, Khronos PBR Neutral, primitives, part staging, Poly Haven CC0 helpers).
- `sfx/` & `run_sfx.py` — Procedural 48 kHz sound synthesis mastered to −14 LUFS from `timeline.json`.
- `tools/music.py` — Audio/music mixing and muxing helper via `ffmpeg`.

## Standard 5-Stage Pipeline

1. **Brief & References**: Generate or read the floor plan (metres) and 2–3 cohesive look-dev references defining materials and lighting mood.
2. **Modular Blender Build**: Separate scripts per stage (architecture/openings → hero furniture/mechanisms → hero props/lighting → physics & exterior environment).
3. **Cloth & PBR Polish**: Run Cloth/Pressure simulation, bake settled meshes, align long-axis UVs, verify zero intruding exterior meshes, and render a low-res Cycles parity check (`960×540`, `32 samples`).
4. **Clean glTF/GLB Export**: Apply modifiers (`export_apply=True`), embed JPEG/PNG PBR maps, keep `export_yup=True` and `export_lights=False` for clean WebGPU lighting parity.
5. **Vercel `vgpu` WebGPU Delivery**: Load the `.glb` into `THREE.WebGPURenderer` with `THREE.NeutralToneMapping`, drive custom `.wgsl` material shaders via `vgpu/three` (`tslExports`), layer native `vgpu` interactive effects (such as refractive Liquid Glass SDF controls), and verify visually on desktop and mobile viewports.
