"""Etapa 2B: Fisica REAL de Cloth no Blender (edredom terracota caido sobre a cama, lencol creme dobrado e travesseiros inflados com Cloth Pressure), fiel a ref_hero_retro_terroso.jpg."""
import sys
import math
import bpy
import bmesh
from mathutils import Vector, Euler

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)

import common as C


def _remove_if_exists(names):
    for n in names:
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)


def _add_collision(obj, thickness_outer=0.010, friction=12.0):
    if not obj:
        return
    for m in list(obj.modifiers):
        if m.type == "COLLISION":
            obj.modifiers.remove(m)
    mod = obj.modifiers.new("Collision", "COLLISION")
    obj.collision.thickness_outer = thickness_outer
    obj.collision.thickness_inner = 0.015
    obj.collision.cloth_friction = friction
    obj.collision.damping = 0.65
    return mod


def _make_cloth_grid(name, center, size_xy, segs_xy, mat, col, rot_z=0.0, uv_scale=1.35):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=segs_xy[0], y_segments=segs_xy[1], size=0.5)
    sx, sy = size_xy
    for v in bm.verts:
        # Micro-assimetria organica para dobras naturais (evita simetria artificial perfeita)
        nx = v.co.x * sx
        ny = v.co.y * sy
        nz = 0.008 * math.sin(nx * 5.2 + ny * 3.7) + 0.005 * math.cos(nx * 9.1 - ny * 6.3)
        v.co = Vector((nx, ny, nz))
    bm.normal_update()
    uv_layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for loop in f.loops:
            loop[uv_layer].uv = (loop.vert.co.x * uv_scale + 0.5, loop.vert.co.y * uv_scale + 0.5)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(center)
    obj.rotation_euler = Euler((0.0, 0.0, rot_z), "XYZ")
    obj.data.materials.append(mat)
    C.link_obj(obj, col)
    C.set_smooth(obj)
    return obj


def _make_pressure_pillow(name, center, size_xyz, mat, col, rot=(0, 0, 0), uv_scale=2.0):
    """Cria fronha fechada pronta para inflacao via Cloth Pressure (costuras reais nas quinas!)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=12, use_grid_fill=True)
    sx, sy, sz = size_xyz
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    bm.normal_update()
    C.apply_box_uv(bm, scale=uv_scale)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(center)
    obj.rotation_euler = Euler(rot, "XYZ")
    obj.data.materials.append(mat)
    C.link_obj(obj, col)
    C.set_smooth(obj)

    cl = obj.modifiers.new("Cloth", "CLOTH")
    s = cl.settings
    s.quality = 6
    s.mass = 0.28
    s.tension_stiffness = 18.0
    s.compression_stiffness = 18.0
    s.shear_stiffness = 12.0
    s.bending_stiffness = 0.8
    s.use_pressure = True
    s.uniform_pressure_force = 4.2
    s.pressure_factor = 1.2
    s.shrink_min = -0.06
    s.effector_weights.gravity = 0.65
    cl.collision_settings.use_collision = True
    cl.collision_settings.distance_min = 0.008
    cl.collision_settings.use_self_collision = False
    return obj


def run_cloth_physics():
    M = {m.name: m for m in bpy.data.materials}
    col = "04_Cama_Futon"
    C.STAGE[0] = col

    # Corrige alinhamento do Shoji_South para nao atravessar a parede frontal (Y = -1.35)
    # Move as pecas do Shoji_South +0.34 m em Y para ficar entreaberto de forma limpa
    shoji_south_objs = [o for o in bpy.data.objects if o.name.startswith("Shoji_South_")]
    if shoji_south_objs:
        min_y = min(o.location.y for o in shoji_south_objs)
        if min_y < -1.15:
            for o in shoji_south_objs:
                o.location.y += 0.34

    # Remove tecidos estaticos antigos da etapa 2
    _remove_if_exists(["Duvet_Terracotta", "Sheet_FoldCuff", "Pillow_Ochre_L", "Pillow_Ochre_R"])

    # Ativa colisores fisicos no colchao, plataforma da cama, cabeceira e piso
    colliders = [
        "Futon_Mattress",
        "Bed_Rail_Front", "Bed_Rail_Back", "Bed_Rail_East", "Bed_Rail_West",
        "Bed_LampLedge_Top", "Headboard_TopRail", "Headboard_BotRail",
        "Tatami_03_BackR", "Tatami_04_Mid", "Tatami_05_Front", "Tatami_06_Right",
    ]
    for cname in colliders:
        _add_collision(bpy.data.objects.get(cname), thickness_outer=0.010, friction=14.0)
    for o in bpy.data.objects:
        if o.name.startswith("Headboard_Slat_"):
            _add_collision(o, thickness_outer=0.008, friction=10.0)

    matt_cx = 0.24

    # 1. Lencol creme dobrado (Cloth real caindo sobre a metade superior do colchao)
    sheet = _make_cloth_grid(
        "Sheet_Cloth_Cream",
        center=(matt_cx, 0.36, 0.42),
        size_xy=(1.62, 0.96),
        segs_xy=(34, 24),
        mat=M["Mat_FutonCream"],
        col=col,
        rot_z=math.radians(1.5),
        uv_scale=1.4,
    )
    cl_s = sheet.modifiers.new("Cloth", "CLOTH")
    cl_s.settings.quality = 6
    cl_s.settings.mass = 0.32
    cl_s.settings.tension_stiffness = 20.0
    cl_s.settings.bending_stiffness = 0.6
    cl_s.collision_settings.use_collision = True
    cl_s.collision_settings.distance_min = 0.008

    # 2. Edredom terracota-ferrugem (Kakebuton com Cloth real + caimento generoso nas bordas igual a referencia!)
    duvet = _make_cloth_grid(
        "Duvet_Cloth_Terracotta",
        center=(matt_cx + 0.01, -0.14, 0.475),
        size_xy=(1.94, 1.66),
        segs_xy=(48, 44),
        mat=M["Mat_DuvetTerracotta"],
        col=col,
        rot_z=math.radians(-1.2),
        uv_scale=1.25,
    )
    cl_d = duvet.modifiers.new("Cloth", "CLOTH")
    cl_d.settings.quality = 7
    cl_d.settings.mass = 0.55
    cl_d.settings.tension_stiffness = 16.0
    cl_d.settings.compression_stiffness = 14.0
    cl_d.settings.shear_stiffness = 10.0
    cl_d.settings.bending_stiffness = 1.4  # Rigidez de edredom acolchoado
    cl_d.settings.air_damping = 1.4
    cl_d.collision_settings.use_collision = True
    cl_d.collision_settings.distance_min = 0.010
    cl_d.collision_settings.use_self_collision = True
    cl_d.collision_settings.self_distance_min = 0.010

    # 3. Dois travesseiros ocre inflados via Cloth Pressure caindo sobre o colchao e apoiados na cabeceira
    p_left = _make_pressure_pillow(
        "Pillow_Cloth_Ochre_L",
        center=(matt_cx - 0.35, 0.97, 0.445),
        size_xyz=(0.56, 0.36, 0.085),
        mat=M["Mat_PillowOchre"],
        col=col,
        rot=(math.radians(14), 0, math.radians(-3)),
    )
    p_right = _make_pressure_pillow(
        "Pillow_Cloth_Ochre_R",
        center=(matt_cx + 0.35, 0.97, 0.445),
        size_xyz=(0.56, 0.36, 0.085),
        mat=M["Mat_PillowOchre"],
        col=col,
        rot=(math.radians(14), 0, math.radians(4)),
    )

    # Roda a simulacao fisica quadro a quadro (frame 1 -> 38) na viewport ao vivo!
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 40
    for f in range(1, 39):
        scene.frame_set(f)

    # Aplica o estado simulado no frame 38 (ou congela geometria com Solidify + Subsurf para volume real de edredom)
    # Adiciona espessura acolchoada ao edredom e lencol APOS o Cloth para volume fotorrealista!
    sol_s = sheet.modifiers.new("Solidify", "SOLIDIFY")
    sol_s.thickness = 0.010
    sol_s.offset = 1.0
    sub_s = sheet.modifiers.new("Subsurf", "SUBSURF")
    sub_s.levels = 1
    sub_s.render_levels = 2

    sol_d = duvet.modifiers.new("Solidify", "SOLIDIFY")
    sol_d.thickness = 0.036
    sol_d.offset = 1.0
    sub_d = duvet.modifiers.new("Subsurf", "SUBSURF")
    sub_d.levels = 1
    sub_d.render_levels = 2

    for p in (p_left, p_right):
        sub_p = p.modifiers.new("Subsurf", "SUBSURF")
        sub_p.levels = 1
        sub_p.render_levels = 2

    # Reposiciona camera hero para refletir o enquadramento frontal-3/4 baixo da referencia
    cam = bpy.data.objects.get("Camera_Hero")
    if cam:
        cam.location = (0.12, -1.92, 0.70)
        target = Vector((-0.14, 0.85, 0.60))
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 28.0
        bpy.context.scene.camera = cam

    # Atualiza viewport
    C.frame_viewport(use_camera=True)
    bpy.ops.wm.save_as_mainfile(filepath=f"{PROJ_DIR}\\sala_japonesa.blend")
    print("[Etapa 2B OK] Fisica real de Cloth simulada (frames 1-38): edredom terracota, lencol creme e travesseiros ocre inflados!")


run_cloth_physics()
