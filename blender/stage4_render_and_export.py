"""Etapa 4: Renderiza previews Cycles (Khronos PBR Neutral) para auditoria visual e exporta GLB limpo para Vercel vgpu."""
import os
import math
import bpy
from mathutils import Vector

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
REND_DIR = os.path.join(PROJ_DIR, "renders")
EXP_DIR = os.path.join(PROJ_DIR, "export")
os.makedirs(REND_DIR, exist_ok=True)
os.makedirs(EXP_DIR, exist_ok=True)


def render_and_export():
    scene = bpy.context.scene
    # 1. Render preview Hero (960x540, 32 samples - regra Blueprint Step 4)
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.cycles.samples = 32
    scene.render.filepath = os.path.join(REND_DIR, "preview_hero.png")
    bpy.ops.render.render(write_still=True)

    # 2. Cria camera de detalhe da luminaria + xicara e renderiza preview close-up
    cam_hero = bpy.data.objects.get("Camera_Hero")
    cam_d = bpy.data.cameras.new("Camera_Detail")
    cam_d.lens = 45.0
    cam_d.dof.use_dof = True
    cam_d.dof.focus_distance = 1.15
    cam_d.dof.aperture_fstop = 3.2
    cam_detail = bpy.data.objects.new("Camera_Detail", cam_d)
    cam_detail.location = (-0.98, -0.05, 0.56)
    target = Vector((-0.62, 0.90, 0.43))
    cam_detail.rotation_euler = (target - cam_detail.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(cam_detail)

    scene.camera = cam_detail
    scene.render.filepath = os.path.join(REND_DIR, "preview_lamp.png")
    bpy.ops.render.render(write_still=True)

    # Restaura camera hero
    if cam_hero:
        scene.camera = cam_hero

    # 3. Exporta GLB otimizado para Vercel vgpu (modifiers aplicados, UVs, normais, tangentes e texturas embutidas)
    glb_path = os.path.join(EXP_DIR, "sala_japonesa.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_materials="EXPORT",
        export_cameras=True,
        export_lights=True,
        export_yup=True,
    )
    tri_count = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        if o.type == "MESH":
            ev = o.evaluated_get(depsgraph)
            me = ev.to_mesh()
            me.calc_loop_triangles()
            tri_count += len(me.loop_triangles)
            ev.to_mesh_clear()

    size_mb = os.path.getsize(glb_path) / (1024 * 1024)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROJ_DIR, "sala_japonesa.blend"))
    print(f"[Etapa 4 OK] Previews em {REND_DIR} | GLB: {glb_path} ({size_mb:.2f} MB, {tri_count:,} triangulos)")


render_and_export()
