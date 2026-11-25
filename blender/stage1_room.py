"""Etapa 1: Sala japonesa Rokujo (3.60 x 2.70 x 2.55 m) fiel a planta e referencia hero terrosa retro."""
import sys
import math
import bpy

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)

import importlib
import common as C
importlib.reload(C)


def setup_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"

    cp = bpy.context.preferences.addons["cycles"].preferences
    device_set = False
    for backend in ("OPTIX", "CUDA"):
        try:
            cp.compute_device_type = backend
            cp.get_devices()
            gpus = [d for d in cp.devices if d.type == backend]
            if gpus:
                for d in cp.devices:
                    d.use = (d.type == backend)
                scene.cycles.device = "GPU"
                scene.cycles.denoiser = "OPTIX" if backend == "OPTIX" else "OPENIMAGEDENOISE"
                device_set = True
                break
        except Exception:
            pass
    if not device_set:
        scene.cycles.device = "CPU"
        scene.cycles.denoiser = "OPENIMAGEDENOISE"

    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    scene.cycles.samples = 64
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 6
    scene.cycles.transparent_max_bounces = 16

    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    # Regra Blueprint: Khronos PBR Neutral para manter tons terrosos e luz quente fieis
    scene.view_settings.view_transform = "Khronos PBR Neutral"
    try:
        scene.view_settings.look = "None"
    except Exception:
        pass
    scene.view_settings.exposure = 0.0
    return scene


def build_room():
    setup_scene()
    M = C.get_materials()

    # Sala rokujo: X in [-1.80, +1.80] (3.60 m), Y in [-1.35, +1.35] (2.70 m), Z in [0, 2.55 m]
    W, D, H = 3.60, 2.70, 2.55

    # 1. SUBPISO & 6 TATAMES (trama alternada via rot_uv_90 + bordas heri marrom-espresso)
    C.STAGE[0] = "01_Tatami_Piso"
    C.box("Subfloor", (0.0, 0.0, -0.075), (W + 0.50, D + 0.50, 0.05), M["walnut"], bevel=0.0)

    tatamis = [
        ("Tatami_01_Left",  -1.80, -0.90, -1.35,  0.45, False),
        ("Tatami_02_BackL", -1.80,  0.00,  0.45,  1.35, True),
        ("Tatami_03_BackR",  0.00,  1.80,  0.45,  1.35, True),
        ("Tatami_04_Mid",   -0.90,  0.90, -0.45,  0.45, True),
        ("Tatami_05_Front", -0.90,  0.90, -1.35, -0.45, True),
        ("Tatami_06_Right",  0.90,  1.80, -1.35,  0.45, False),
    ]
    gap = 0.003
    heri_w = 0.032
    mat_h = 0.048
    for name, x0, x1, y0, y1, along_x in tatamis:
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        sx, sy = (x1 - x0) - gap, (y1 - y0) - gap
        C.box(name, (cx, cy, -mat_h / 2.0), (sx, sy, mat_h), M["tatami"], bevel=0.004, uv_scale=1.1, rot_uv_90=(not along_x))
        if along_x:
            for side, sy_pos in (("N", y1 - gap / 2 - heri_w / 2), ("S", y0 + gap / 2 + heri_w / 2)):
                C.box(f"{name}_Heri_{side}", (cx, sy_pos, -0.0005), (sx - 0.002, heri_w, 0.003), M["heri"], bevel=0.0006, uv_scale=2.0)
        else:
            for side, sx_pos in (("W", x0 + gap / 2 + heri_w / 2), ("E", x1 - gap / 2 - heri_w / 2)):
                C.box(f"{name}_Heri_{side}", (sx_pos, cy, -0.0005), (heri_w, sy - 0.002, 0.003), M["heri"], bevel=0.0006, uv_scale=2.0)

    # 2. PAREDES DE ARGILA JURAKU, PILARES NOGUEIRA, NAGESHI, TETO SAOBUCHI E KAKEJIKU
    C.STAGE[0] = "02_Paredes_Madeira"
    wall_t = 0.12
    C.box("Wall_Back_Plaster",  (0.0, D / 2 + wall_t / 2, H / 2), (W + 0.24, wall_t, H), M["plaster"], bevel=0.002, uv_scale=0.55)
    C.box("Wall_Right_Plaster", (W / 2 + wall_t / 2, 0.0, H / 2), (wall_t, D + 0.24, H), M["plaster"], bevel=0.002, uv_scale=0.55)
    C.box("Wall_Left_Top",      (-W / 2 - wall_t / 2, 0.0, (2.06 + H) / 2), (wall_t, D + 0.24, H - 2.06), M["plaster"], bevel=0.002, uv_scale=0.55)
    C.box("Wall_Left_South",    (-W / 2 - wall_t / 2, -1.23, 1.03), (wall_t, 0.24, 2.06), M["plaster"], bevel=0.002, uv_scale=0.55)
    C.box("Wall_Left_North",    (-W / 2 - wall_t / 2,  1.23, 1.03), (wall_t, 0.24, 2.06), M["plaster"], bevel=0.002, uv_scale=0.55)

    # Pilares estruturais em nogueira/cedro escuro (como na referencia hero!)
    posts = [
        ("Post_NW",        -1.76,  1.32, 0.115),
        ("Post_NE",         1.76,  1.32, 0.115),
        ("Post_SE",         1.76, -1.32, 0.115),
        ("Post_SW",        -1.76, -1.32, 0.115),
        ("Post_Tokonoma",   0.58,  1.325, 0.105),  # Pilar divisor marcante como na referencia!
        ("Post_Right_Mid",  1.77,  0.00, 0.095),
        ("Post_Shoji_S",   -1.77, -1.12, 0.080),
        ("Post_Shoji_N",   -1.77,  1.12, 0.080),
    ]
    for pname, px, py, pw in posts:
        C.box(pname, (px, py, H / 2), (pw, pw, H), M["walnut"], bevel=0.003, uv_scale=0.8)

    # Rodapes, travessa horizontal nageshi (Z = 2.06 m) e frechais de topo
    C.box("Baseboard_Back",  (0.0,  1.34, 0.045), (W, 0.028, 0.09), M["walnut"], bevel=0.002, uv_scale=0.9)
    C.box("Baseboard_Right", (1.79, 0.0,  0.045), (0.028, D, 0.09), M["walnut"], bevel=0.002, uv_scale=0.9)
    # Travessa nageshi do pilar esquerdo ao pilar do tokonoma (igual a referencia hero!)
    C.box("Nageshi_BackLeft", (-0.59, 1.33, 2.06), (2.38, 0.048, 0.095), M["walnut"], bevel=0.003, uv_scale=0.8)
    C.box("Nageshi_Right",    (1.78,  0.0,  2.06), (0.048, D, 0.095), M["walnut"], bevel=0.003, uv_scale=0.8)
    C.box("Kamoi_Left",       (-1.77, 0.0,  2.075), (0.12, D, 0.068), M["walnut"], bevel=0.003, uv_scale=0.8)
    C.box("Shikii_Left",      (-1.77, 0.0,  0.015), (0.12, 2.26, 0.030), M["hinoki"], bevel=0.002, uv_scale=0.8)
    C.box("TopPlate_Back",    (0.0,  1.335, 2.51), (W, 0.055, 0.08), M["walnut"], bevel=0.002, uv_scale=0.8)
    C.box("TopPlate_Right",   (1.785, 0.0,  2.51), (0.055, D, 0.08), M["walnut"], bevel=0.002, uv_scale=0.8)
    C.box("TopPlate_Left",    (-1.785, 0.0, 2.51), (0.055, D, 0.08), M["walnut"], bevel=0.002, uv_scale=0.8)

    # Teto em tabuas de madeira + ripas saobuchi
    n_planks = 12
    plank_w = W / n_planks
    for i in range(n_planks):
        px = -W / 2 + (i + 0.5) * plank_w
        C.box(f"Ceiling_Plank_{i:02d}", (px, 0.0, H + 0.012), (plank_w - 0.003, D + 0.16, 0.024), M["hinoki"], bevel=0.0015, uv_scale=0.8)
    for j, by in enumerate((-0.90, -0.45, 0.0, 0.45, 0.90)):
        C.box(f"Ceiling_Saobuchi_{j:02d}", (0.0, by, H - 0.016), (W, 0.038, 0.032), M["walnut"], bevel=0.002, uv_scale=0.8)

    # Pergaminho kakejiku com circulo enso na parede de fundo a direita (tokonoma)
    C.box("Scroll_Canvas",  (1.24, 1.336, 1.46), (0.44, 0.008, 0.92), M["kakejiku"], bevel=0.001, fit_01=True)
    C.cyl("Scroll_Rod_Top", (1.24, 1.332, 1.92), 0.011, 0.49, rot=(0, math.pi / 2, 0), mat=M["yakisugi"])
    C.cyl("Scroll_Rod_Bot", (1.24, 1.332, 1.00), 0.014, 0.52, rot=(0, math.pi / 2, 0), mat=M["yakisugi"])
    C.cyl("Scroll_Cord",    (1.24, 1.335, 2.16), 0.003, 0.46, mat=M["heri"])

    # 3. PAINEIS SHOJI DESLIZANTES (hinoki + kumiko + washi brilhando com luz difusa quente)
    C.STAGE[0] = "03_Shoji"

    def build_shoji_panel(tag, x_pos, y_center, width=1.10, z0=0.03, z1=2.04):
        h = z1 - z0
        zc = (z0 + z1) / 2.0
        frame_t = 0.028
        stile_w = 0.040
        koshi_h = 0.34
        C.box(f"{tag}_Stile_S", (x_pos, y_center - width / 2 + stile_w / 2, zc), (frame_t, stile_w, h), M["hinoki"], bevel=0.0015, uv_scale=1.2)
        C.box(f"{tag}_Stile_N", (x_pos, y_center + width / 2 - stile_w / 2, zc), (frame_t, stile_w, h), M["hinoki"], bevel=0.0015, uv_scale=1.2)
        inner_w = width - 2 * stile_w
        C.box(f"{tag}_Rail_Bot",   (x_pos, y_center, z0 + 0.025), (frame_t, inner_w, 0.050), M["hinoki"], bevel=0.0015, uv_scale=1.2)
        C.box(f"{tag}_Rail_Koshi", (x_pos, y_center, z0 + koshi_h), (frame_t, inner_w, 0.034), M["hinoki"], bevel=0.0015, uv_scale=1.2)
        C.box(f"{tag}_Rail_Top",   (x_pos, y_center, z1 - 0.022), (frame_t, inner_w, 0.044), M["hinoki"], bevel=0.0015, uv_scale=1.2)
        C.box(f"{tag}_KoshiIta",   (x_pos, y_center, z0 + 0.05 + (koshi_h - 0.068) / 2), (0.014, inner_w, koshi_h - 0.068), M["hinoki"], bevel=0.001, uv_scale=1.2)
        washi_z0 = z0 + koshi_h + 0.017
        washi_z1 = z1 - 0.044
        washi_h = washi_z1 - washi_z0
        C.box(f"{tag}_Washi", (x_pos - 0.005, y_center, (washi_z0 + washi_z1) / 2), (0.003, inner_w + 0.006, washi_h + 0.006), M["washi_shoji"], bevel=0.0, uv_scale=1.0)
        for ci in range(1, 4):
            ky = (y_center - inner_w / 2) + ci * (inner_w / 4.0)
            C.box(f"{tag}_KumikoV_{ci}", (x_pos + 0.003, ky, (washi_z0 + washi_z1) / 2), (0.013, 0.012, washi_h), M["hinoki"], bevel=0.0008, uv_scale=1.5)
        for ri in range(1, 7):
            kz = washi_z0 + ri * (washi_h / 7.0)
            C.box(f"{tag}_KumikoH_{ri}", (x_pos + 0.003, y_center, kz), (0.013, inner_w, 0.012), M["hinoki"], bevel=0.0008, uv_scale=1.5)

    # Painel Norte na parte de tras + Painel Sul semi-aberto revelando a varanda engawa
    build_shoji_panel("Shoji_North", x_pos=-1.755, y_center= 0.54)
    build_shoji_panel("Shoji_South", x_pos=-1.790, y_center=-0.92)

    # Varanda engawa externa em tabuas de madeira + beiral + cerca de cedro + bambus
    for bi in range(6):
        ex = -1.94 - bi * 0.145
        C.box(f"Engawa_Board_{bi:02d}", (ex, 0.0, -0.025), (0.138, 3.20, 0.036), M["walnut"], bevel=0.002, uv_scale=0.8)
    C.box("Engawa_Ceiling", (-2.35, 0.0, 2.38), (1.10, 3.40, 0.04), M["walnut"], bevel=0.002, uv_scale=0.8)
    C.box("Exterior_Fence", (-3.25, 0.0, 1.25), (0.08, 4.60, 3.00), M["walnut"], bevel=0.0, uv_scale=0.6)
    for idx, (bx, by, br, tilt) in enumerate((
        (-2.65, -0.35, 0.022, 0.04),
        (-2.78, -0.15, 0.018, -0.03),
        (-2.58, -0.02, 0.020, 0.05),
        (-2.82, -0.52, 0.024, -0.02),
    )):
        C.cyl(f"Bamboo_{idx}", (bx, by, 1.20), br, 2.60, verts=16, mat=M["bamboo"], rot=(tilt, 0.02, 0))

    C.frame_viewport()
    print(f"[Etapa 1 OK] Sala japonesa terrosa criada com {len(C.PARTS)} pecas.")


build_room()
