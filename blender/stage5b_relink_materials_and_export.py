"""Reatribui todos os materiais PBR 1024px seamless com desgaste wabi-sabi a todas as pecas da cena, renderiza preview_hero_v3.png e re-exporta o GLB limpo."""
import os
import shutil
import bpy

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
EXP_GLB = os.path.join(PROJ_DIR, "export", "sala_japonesa.glb")
WEB_GLB = os.path.join(PROJ_DIR, "web-vgpu", "public", "sala_japonesa.glb")
REND_DIR = os.path.join(PROJ_DIR, "renders")


def set_mat(obj, mat):
    if not obj or obj.type != "MESH" or not mat:
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def relink_and_export():
    M = {m.name: m for m in bpy.data.materials}

    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        n = obj.name
        # Mantem materiais ja ligados dos tecidos Cloth e das plantas/poster recem-criados
        if any(n.startswith(p) for p in ("Duvet_Cloth", "Sheet_Cloth", "Throw_Cloth", "Pillow_Cloth", "Plant_", "Scroll_Canvas")):
            continue

        if n.startswith("Wall_"):
            set_mat(obj, M.get("Mat_JurakuPlaster"))
        elif n.startswith("Tatami_") and "Heri" in n:
            set_mat(obj, M.get("Mat_Heri"))
        elif n.startswith("Tatami_"):
            set_mat(obj, M.get("Mat_Tatami"))
        elif n.endswith("_Washi") and n.startswith("Shoji_"):
            set_mat(obj, M.get("Mat_WashiShoji"))
        elif n.startswith("Shoji_") or n.startswith("Shikii_") or n.startswith("Ceiling_Plank_"):
            set_mat(obj, M.get("Mat_Hinoki"))
        elif n.startswith("Lamp_Washi_") or n == "Lamp_Bulb":
            set_mat(obj, M.get("Mat_WashiLantern"))
        elif n == "Lamp_Socket":
            set_mat(obj, M.get("Mat_Brass"))
        elif n.startswith("Lamp_Foot_") or n == "Lamp_BasePlinth" or n == "TeaTray_Base" or n.startswith("Scroll_Rod_"):
            set_mat(obj, M.get("Mat_Yakisugi"))
        elif n == "TeaCup_Yunomi":
            set_mat(obj, M.get("Mat_CeramicTea"))
        elif n == "Scroll_Cord":
            set_mat(obj, M.get("Mat_Heri"))
        elif n == "Futon_Mattress":
            set_mat(obj, M.get("Mat_FutonCream"))
        else:
            # Pilares, nageshi, rodapes, saobuchi, cama, cabeceira, moldura da luminaria, engawa, cerca, pires
            set_mat(obj, M.get("Mat_Walnut"))

    # Confirma que a camera hero esta ativa e renderiza preview_hero_v3.png
    scene = bpy.context.scene
    cam = bpy.data.objects.get("Camera_Hero")
    if cam:
        scene.camera = cam
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.cycles.samples = 32
    scene.render.filepath = os.path.join(REND_DIR, "preview_hero_v3.png")
    bpy.ops.render.render(write_still=True)

    # Exporta GLB limpo direto para web-vgpu/public
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
    print(f"[Etapa 5B OK] Materiais reatribuidos, preview_hero_v3.png salvo e GLB exportado ({size_mb:.2f} MB)!")


relink_and_export()
