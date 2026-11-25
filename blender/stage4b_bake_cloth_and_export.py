"""Assa (bake) definitivamente a malha simulada de Cloth do frame 38 nas malhas dos tecidos e re-exporta GLB limpo (sem luzes duplicadas) direto para web-vgpu/public."""
import os
import shutil
import bpy

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
EXP_GLB = os.path.join(PROJ_DIR, "export", "sala_japonesa.glb")
WEB_GLB = os.path.join(PROJ_DIR, "web-vgpu", "public", "sala_japonesa.glb")


def bake_cloth_and_reexport():
    scene = bpy.context.scene
    # Garante simulacao avaliada ate o frame 38
    for f in range(1, 39):
        scene.frame_set(f)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    cloth_names = [
        "Sheet_Cloth_Cream",
        "Duvet_Cloth_Terracotta",
        "Pillow_Cloth_Ochre_L",
        "Pillow_Cloth_Ochre_R",
    ]
    for name in cloth_names:
        obj = bpy.data.objects.get(name)
        if not obj or obj.type != "MESH":
            continue
        if not obj.modifiers:
            continue
        ev = obj.evaluated_get(depsgraph)
        baked_mesh = bpy.data.meshes.new_from_object(ev)
        baked_mesh.name = f"{name}_BakedMesh"
        # Mantem shading suave
        for p in baked_mesh.polygons:
            p.use_smooth = True
        old_mesh = obj.data
        obj.modifiers.clear()
        obj.data = baked_mesh
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)

    # Exporta GLB limpo (export_lights=False para evitar luz duplicada no vgpu WebGPU!)
    os.makedirs(os.path.dirname(EXP_GLB), exist_ok=True)
    os.makedirs(os.path.dirname(WEB_GLB), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=EXP_GLB,
        export_format="GLB",
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
    print(f"[Bake Cloth + Export OK] {EXP_GLB} ({size_mb:.2f} MB) copiado para {WEB_GLB}")


bake_cloth_and_reexport()
