"""Ajuste cirurgico final na Etapa 6B:
- Garante que ZERO pedras ou plantas do Poly Haven invadam o interior (remove/desloca qualquer sub-malha com max_x > -2.15 m)
- Deixa o quarto 100% livre de plantas internas
- Re-exporta GLB otimizado (JPEG q=88 -> super rapido no WebGPU!) direto para web-vgpu/public
"""
import os
import shutil
import bpy
from mathutils import Vector

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
EXP_GLB = os.path.join(PROJ_DIR, "export", "sala_japonesa.glb")
WEB_GLB = os.path.join(PROJ_DIR, "web-vgpu", "public", "sala_japonesa.glb")
REND_DIR = os.path.join(PROJ_DIR, "renders")


def world_max_x(obj):
    if obj.type != "MESH" or not obj.data:
        return -999.0
    return max((obj.matrix_world @ Vector(corner)).x for corner in obj.bound_box)


def world_min_y(obj):
    if obj.type != "MESH" or not obj.data:
        return 0.0
    return min((obj.matrix_world @ Vector(corner)).y for corner in obj.bound_box)


def fix_garden_bounds_and_export():
    bpy.context.view_layer.update()

    # 1. Reposiciona os sets do Poly Haven mais para fora no jardim (X <= -3.55 m) e reduz escala das pedras
    ph_adjust = {
        "PH_MossRocks_A": (Vector((-3.55, -0.65, -0.06)), 0.34),
        "PH_MossRocks_B": (Vector((-3.75,  0.35, -0.06)), 0.30),
        "PH_Fern_A":      (Vector((-3.10, -0.78, -0.06)), 0.85),
        "PH_Fern_B":      (Vector((-3.25, -0.20, -0.06)), 0.80),
        "PH_Fern_C":      (Vector((-3.45,  0.45, -0.06)), 0.82),
        "PH_Shrub_A":     (Vector((-3.85, -0.52, -0.06)), 0.58),
        "PH_Shrub_B":     (Vector((-3.95,  0.32, -0.06)), 0.55),
        "PH_GardenTree":  (Vector((-4.10, -0.15, -0.06)), 0.55),
    }
    for name, (loc, sc) in ph_adjust.items():
        empty = bpy.data.objects.get(name)
        if empty:
            empty.location = loc
            empty.scale = Vector((sc, sc, sc))

    bpy.context.view_layer.update()

    # 2. Auditoria rigorosa de colisao: qualquer malha da colecao 07_Jardim_Externo com max_x > -2.15 m
    # (ou seja, perto demais da parede shoji em X = -1.80 m) e empurrada para fora ou removida!
    garden_col = bpy.data.collections.get("07_Jardim_Externo")
    removed_count = 0
    if garden_col:
        for obj in list(garden_col.objects):
            if obj.type != "MESH":
                continue
            if obj.name.startswith("Garden_Ground") or obj.name.startswith("Garden_ZenGravel") or obj.name.startswith("Garden_Fence"):
                continue
            mx = world_max_x(obj)
            if mx > -2.15:
                # Se ainda sobressai alem do engawa, remove essa sub-peca intrusa do set
                bpy.data.objects.remove(obj, do_unlink=True)
                removed_count += 1

    bpy.context.view_layer.update()

    # 3. Enquadramento Hero equilibrado (porta shoji aberta + jardim + luminaria + cama + poster Vercel visivel!)
    scene = bpy.context.scene
    cam = bpy.data.objects.get("Camera_Hero")
    if cam:
        cam.location = (0.35, -2.28, 0.86)
        target = Vector((-0.06, 0.72, 0.62))
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 25.0
        scene.camera = cam

    # Render rapido de confirmacao Cycles
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.cycles.samples = 32
    scene.render.filepath = os.path.join(REND_DIR, "preview_hero_v5.png")
    bpy.ops.render.render(write_still=True)

    # 4. Exporta GLB otimizado (JPEG q=88 para texturas -> arquivo leve e rapido no WebGPU!)
    bpy.ops.export_scene.gltf(
        filepath=EXP_GLB,
        export_format="GLB",
        export_image_format="JPEG",
        export_image_quality=88,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=False,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_yup=True,
    )
    shutil.copy2(EXP_GLB, WEB_GLB)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROJ_DIR, "sala_japonesa.blend"))
    size_mb = os.path.getsize(EXP_GLB) / (1024 * 1024)
    print(f"[Etapa 6B OK] Sub-pecas intrusas removidas: {removed_count} | GLB otimizado: {size_mb:.2f} MB")


fix_garden_bounds_and_export()
