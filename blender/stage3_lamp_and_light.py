"""Etapa 3: Luminaria japonesa Andon (fiel ao close-up aprovado), iluminacao quente difusa retro, camera hero e exportacao GLB."""
import os
import sys
import math
import bpy
from mathutils import Vector

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)

import common as C


def build_lamp_and_lights():
    M = {m.name: m for m in bpy.data.materials}
    mats = {
        "hinoki":        M["Mat_Hinoki"],
        "walnut":        M["Mat_Walnut"],
        "yakisugi":      M["Mat_Yakisugi"],
        "washi_lantern": M["Mat_WashiLantern"],
        "brass":         M["Mat_Brass"],
    }

    col = "05_Luminaria_Andon"
    C.STAGE[0] = col

    # Posicao da luminaria: sobre a aba esquerda da plataforma da cama (Z topo = 0.195 m)
    lx, ly, lz = -0.82, 0.94, 0.195

    # 1. Base de cedro carbonizado (yakisugi) com 4 pes quadrados (identica ao detalhe aprovado!)
    base_w = 0.24
    foot_h = 0.018
    for sx in (-1, 1):
        for sy in (-1, 1):
            C.box(
                f"Lamp_Foot_{'E' if sx > 0 else 'W'}{'N' if sy > 0 else 'S'}",
                (lx + sx * 0.092, ly + sy * 0.092, lz + foot_h / 2),
                (0.028, 0.028, foot_h),
                mats["yakisugi"],
                col,
                bevel=0.002,
                uv_scale=2.0,
            )
    plinth_h = 0.036
    C.box("Lamp_BasePlinth", (lx, ly, lz + foot_h + plinth_h / 2), (base_w, base_w, plinth_h), mats["yakisugi"], col, bevel=0.003, uv_scale=2.0)

    # 2. Estrutura de madeira com 4 pilares de canto sobressaindo 1.8 cm no topo (detalhe classico japonês!)
    frame_z0 = lz + foot_h + plinth_h
    lamp_h = 0.40
    top_overhang = 0.018
    frame_z1 = frame_z0 + lamp_h
    half = 0.100
    post_t = 0.015

    for sx in (-1, 1):
        for sy in (-1, 1):
            C.box(
                f"Lamp_Post_{'E' if sx > 0 else 'W'}{'N' if sy > 0 else 'S'}",
                (lx + sx * half, ly + sy * half, frame_z0 + (lamp_h + top_overhang) / 2),
                (post_t, post_t, lamp_h + top_overhang),
                mats["walnut"],
                col,
                bevel=0.0015,
                uv_scale=2.5,
            )

    # Aneis duplos no topo e na base (fiel a ref_detalhe_luminaria!)
    span = 2 * half - post_t
    ring_specs = [
        (frame_z0 + 0.008, 0.014, 0.014),
        (frame_z0 + 0.036, 0.008, 0.008),
        (frame_z0 + 0.056, 0.007, 0.007),
        (frame_z1 - 0.056, 0.007, 0.007),
        (frame_z1 - 0.036, 0.008, 0.008),
        (frame_z1 - 0.008, 0.014, 0.014),
    ]
    for ri, (rz, bar_d, bar_h) in enumerate(ring_specs):
        C.box(f"Lamp_Ring_{ri}_S", (lx, ly - half, rz), (span, bar_d, bar_h), mats["walnut"], col, bevel=0.001, uv_scale=2.5)
        C.box(f"Lamp_Ring_{ri}_N", (lx, ly + half, rz), (span, bar_d, bar_h), mats["walnut"], col, bevel=0.001, uv_scale=2.5)
        C.box(f"Lamp_Ring_{ri}_W", (lx - half, ly, rz), (bar_d, span, bar_h), mats["walnut"], col, bevel=0.001, uv_scale=2.5)
        C.box(f"Lamp_Ring_{ri}_E", (lx + half, ly, rz), (bar_d, span, bar_h), mats["walnut"], col, bevel=0.001, uv_scale=2.5)

    # Ripas verticais laterais finas (moldura interna kumiko nas 4 faces, identica a referencia!)
    v_off = half - 0.026
    for sgn in (-1, 1):
        C.box(f"Lamp_KumikoV_S_{sgn}", (lx + sgn * v_off, ly - half, frame_z0 + lamp_h / 2), (0.007, 0.008, lamp_h - 0.016), mats["walnut"], col, bevel=0.0008)
        C.box(f"Lamp_KumikoV_N_{sgn}", (lx + sgn * v_off, ly + half, frame_z0 + lamp_h / 2), (0.007, 0.008, lamp_h - 0.016), mats["walnut"], col, bevel=0.0008)
        C.box(f"Lamp_KumikoV_W_{sgn}", (lx - half, ly + sgn * v_off, frame_z0 + lamp_h / 2), (0.008, 0.007, lamp_h - 0.016), mats["walnut"], col, bevel=0.0008)
        C.box(f"Lamp_KumikoV_E_{sgn}", (lx + half, ly + sgn * v_off, frame_z0 + lamp_h / 2), (0.008, 0.007, lamp_h - 0.016), mats["walnut"], col, bevel=0.0008)

    # 3. Cupula interna de papel washi fibroso quente
    shade_h = lamp_h - 0.020
    shade_z = frame_z0 + lamp_h / 2
    s_half = half - 0.009
    s_span = 2 * s_half
    C.box("Lamp_Washi_S", (lx, ly - s_half, shade_z), (s_span, 0.003, shade_h), mats["washi_lantern"], col, bevel=0.0, uv_scale=2.2)
    C.box("Lamp_Washi_N", (lx, ly + s_half, shade_z), (s_span, 0.003, shade_h), mats["washi_lantern"], col, bevel=0.0, uv_scale=2.2)
    C.box("Lamp_Washi_W", (lx - s_half, ly, shade_z), (0.003, s_span, shade_h), mats["washi_lantern"], col, bevel=0.0, uv_scale=2.2)
    C.box("Lamp_Washi_E", (lx + s_half, ly, shade_z), (0.003, s_span, shade_h), mats["washi_lantern"], col, bevel=0.0, uv_scale=2.2)

    # 4. Soquete em latao + lampada + cruz superior
    C.cyl("Lamp_Socket", (lx, ly, frame_z0 + 0.040), 0.020, 0.060, verts=24, mat=mats["brass"], col=col, bevel=0.001)
    C.cyl("Lamp_Bulb",   (lx, ly, frame_z0 + 0.105), 0.030, 0.070, verts=24, mat=mats["washi_lantern"], col=col, bevel=0.014)
    C.box("Lamp_TopCross_1", (lx, ly, frame_z1 - 0.008), (span, 0.010, 0.010), mats["walnut"], col, bevel=0.001)
    C.box("Lamp_TopCross_2", (lx, ly, frame_z1 - 0.008), (0.010, span, 0.010), mats["walnut"], col, bevel=0.001)

    # 5. ILUMINACAO QUENTE DIFUSA RETRO EM TONS TERROSOS (zero luz fria azulada!)
    col_cam = "06_Camera_Luzes"
    C.STAGE[0] = col_cam

    # Nucleo quente da luminaria Andon (2600K ambar envolvente)
    ldata = bpy.data.lights.new("Light_Andon_Core", type="POINT")
    ldata.energy = 85.0
    ldata.color = (1.0, 0.66, 0.30)
    ldata.shadow_soft_size = 0.11
    lobj = bpy.data.objects.new("Light_Andon_Core", ldata)
    lobj.location = (lx, ly, frame_z0 + 0.20)
    C.link_obj(lobj, col_cam)

    # Brilho difuso saindo pelo topo da luminaria na parede de argila
    ldata2 = bpy.data.lights.new("Light_Andon_UpGlow", type="AREA")
    ldata2.energy = 28.0
    ldata2.color = (1.0, 0.72, 0.38)
    ldata2.shape = "SQUARE"
    ldata2.size = 0.22
    lobj2 = bpy.data.objects.new("Light_Andon_UpGlow", ldata2)
    lobj2.location = (lx, ly, frame_z1 + 0.03)
    lobj2.rotation_euler = (math.radians(180), 0.0, 0.0)
    C.link_obj(lobj2, col_cam)

    # Luz solar dourada suave e difusa de fim de tarde filtrada pelo shoji (3600K retro)
    sdata = bpy.data.lights.new("Light_Shoji_WarmRetro", type="AREA")
    sdata.energy = 240.0
    sdata.color = (1.0, 0.80, 0.54)
    sdata.shape = "RECTANGLE"
    sdata.size = 2.4
    sdata.size_y = 2.0
    sobj = bpy.data.objects.new("Light_Shoji_WarmRetro", sdata)
    sobj.location = (-2.45, -0.10, 1.35)
    sobj.rotation_euler = (0.0, math.radians(78), 0.0)
    C.link_obj(sobj, col_cam)

    # Rebote difuso quente de ambiente retro (preenche sombras com calor terroso)
    fdata = bpy.data.lights.new("Light_Retro_DiffuseBounce", type="AREA")
    fdata.energy = 65.0
    fdata.color = (1.0, 0.82, 0.60)
    fdata.shape = "RECTANGLE"
    fdata.size = 2.8
    fdata.size_y = 2.2
    fobj = bpy.data.objects.new("Light_Retro_DiffuseBounce", fdata)
    fobj.location = (0.45, -0.60, 2.35)
    fobj.rotation_euler = (math.radians(15), math.radians(-10), 0.0)
    C.link_obj(fobj, col_cam)

    # Mundo quente suave (fim de tarde terroso - independente do idioma do Blender)
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()
    wout = wnt.nodes.new("ShaderNodeOutputWorld")
    wout.location = (300, 0)
    bg = wnt.nodes.new("ShaderNodeBackground")
    bg.location = (0, 0)
    bg.inputs["Color"].default_value = (0.18, 0.12, 0.07, 1.0)
    bg.inputs["Strength"].default_value = 0.65
    wnt.links.new(bg.outputs["Background"], wout.inputs["Surface"])

    # 6. CAMERA HERO (angulo baixo 3/4 igual a referencia aprovada!)
    cam_data = bpy.data.cameras.new("Camera_Hero")
    cam_data.lens = 30.0
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 2.75
    cam_data.dof.aperture_fstop = 4.5
    cam_obj = bpy.data.objects.new("Camera_Hero", cam_data)
    cam_obj.location = (0.28, -1.78, 0.72)
    target = Vector((-0.18, 0.78, 0.56))
    direction = target - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    C.link_obj(cam_obj, col_cam)
    bpy.context.scene.camera = cam_obj

    C.frame_viewport(use_camera=True)

    # Salva .blend
    blend_path = os.path.join(PROJ_DIR, "sala_japonesa.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[Etapa 3 OK] Luminaria Andon + iluminacao retro terrosa prontas. Salvo em {blend_path}")


build_lamp_and_lights()
