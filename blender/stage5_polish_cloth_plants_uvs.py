"""Etapa 5: Refinamento completo no Blender:
- Recarrega texturas 1024px seamless + poster Vercel desgastado no kakejiku
- Corrige UV maps alinhadas ao eixo longo em todas as madeiras, paredes e tatames
- Fisica REAL de Cloth bem acomodada na cama (edredom terracota matelassado, manta ocre dobrada, lencol creme, 3 travesseiros com borda Oxford costurada)
- Plantas japonesas (Ikebana de bordo momiji no tokonoma, Kokedama com samambaia junto ao shoji, bambuzal com nos e folhas no engawa)
- Bake das malhas Cloth + exportacao GLB limpa direto para web-vgpu/public
"""
import os
import sys
import math
import random
import shutil
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
TEX_DIR = os.path.join(PROJ_DIR, "textures")
EXP_GLB = os.path.join(PROJ_DIR, "export", "sala_japonesa.glb")
WEB_GLB = os.path.join(PROJ_DIR, "web-vgpu", "public", "sala_japonesa.glb")
REND_DIR = os.path.join(PROJ_DIR, "renders")

if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)

import importlib
import common as C
importlib.reload(C)


def reload_all_textures_and_kakejiku():
    """Recarrega as novas texturas 1024px seamless do disco e liga o normal map do poster Vercel."""
    for img in list(bpy.data.images):
        if img.filepath:
            try:
                img.unpack(method="REMOVE")
            except Exception:
                pass
            abs_p = bpy.path.abspath(img.filepath)
            if os.path.exists(abs_p):
                img.reload()
                try:
                    img.pack()
                except Exception:
                    pass

    # Reconstrói materiais PBR para garantir que todas as 1024px seamless + kakejiku_normal estejam ligados
    M = C.get_materials()
    # Atualiza o material do poster kakejiku com o normal map do papel/tinta desgastada
    m_kak = C.make_pbr_image_mat("Mat_Kakejiku", "kakejiku", normal_strength=0.45, specular=0.14, rough_override=0.90)
    M["kakejiku"] = m_kak

    # Reatribui materiais atualizados aos objetos existentes por prefixo/nome
    scroll = bpy.data.objects.get("Scroll_Canvas")
    if scroll and scroll.data:
        scroll.data.materials.clear()
        scroll.data.materials.append(m_kak)

    # Cria materiais botanicos e ceramicos para as plantas japonesas
    M["vase_stoneware"] = C.make_solid_mat("Mat_VaseStoneware", (0.14, 0.085, 0.062), rough=0.58, coat=0.18)
    M["slate_stone"]    = C.make_solid_mat("Mat_SlateStone",    (0.085, 0.082, 0.078), rough=0.78)
    M["moss"]           = C.make_solid_mat("Mat_Moss",          (0.11, 0.19, 0.075),   rough=0.95)
    M["fern_leaf"]      = C.make_solid_mat("Mat_FernLeaf",      (0.13, 0.24, 0.085),   rough=0.62)
    M["maple_russet"]   = C.make_solid_mat("Mat_MapleRusset",   (0.38, 0.14, 0.065),   rough=0.64)
    M["maple_olive"]    = C.make_solid_mat("Mat_MapleOlive",    (0.24, 0.22, 0.095),   rough=0.66)
    M["bamboo_leaf"]    = C.make_solid_mat("Mat_BambooLeaf",    (0.14, 0.25, 0.095),   rough=0.58)
    M["branch_bark"]    = C.make_solid_mat("Mat_BranchBark",    (0.12, 0.082, 0.055),  rough=0.84)
    return M


def fix_architectural_uvs():
    """Refaz UVs limpas e alinhadas ao eixo longo em todas as madeiras, paredes e tatames (zero esticamento!)."""
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.data:
            continue
        name = obj.name
        # Ignora tecidos Cloth (terao UVs proprias) e objetos que ja usam fit_01
        if "Cloth" in name or name == "Scroll_Canvas":
            continue
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.normal_update()
        uv_layer = bm.loops.layers.uv.verify()

        xs = [v.co.x for v in bm.verts]
        ys = [v.co.y for v in bm.verts]
        zs = [v.co.z for v in bm.verts]
        if not xs:
            bm.free()
            continue
        dx, dy, dz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)

        # Determina escala de UV realista por familia
        if name.startswith("Wall_"):
            scale = 0.42
            for f in bm.faces:
                n = f.normal
                ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
                for loop in f.loops:
                    co = loop.vert.co + obj.location
                    if ax >= ay and ax >= az:
                        loop[uv_layer].uv = (co.y * scale, co.z * scale)
                    elif ay >= ax and ay >= az:
                        loop[uv_layer].uv = (co.x * scale, co.z * scale)
                    else:
                        loop[uv_layer].uv = (co.x * scale, co.y * scale)
        elif name.startswith("Tatami_") and "Heri" not in name:
            # Alinha a trama do tatame exatamente ao eixo comprido do tapete
            along_x = dx >= dy
            scale = 1.05
            for f in bm.faces:
                for loop in f.loops:
                    co = loop.vert.co
                    u, v = (co.x * scale, co.y * scale) if along_x else (co.y * scale, co.x * scale)
                    loop[uv_layer].uv = (u, v)
        elif any(name.startswith(p) for p in ("Post_", "Nageshi_", "Baseboard_", "Kamoi_", "Shikii_", "TopPlate_", "Ceiling_", "Bed_", "Headboard_", "Shoji_", "Lamp_Post", "Lamp_Ring", "Lamp_Kumiko", "Engawa_Board")):
            # Alinha o grao da madeira (eixo V da textura) estritamente ao eixo mais longo da peca!
            scale = 1.15
            long_axis = "Z" if (dz >= dx and dz >= dy) else ("X" if dx >= dy else "Y")
            for f in bm.faces:
                n = f.normal
                ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
                for loop in f.loops:
                    co = loop.vert.co
                    if long_axis == "Z":
                        u = co.x if ay >= ax else co.y
                        v = co.z
                    elif long_axis == "X":
                        u = co.y if az >= ay else co.z
                        v = co.x
                    else:
                        u = co.x if az >= ax else co.z
                        v = co.y
                    loop[uv_layer].uv = (u * scale, v * scale)
        elif name.startswith("Lamp_Washi_"):
            # Mapeamento 0..1 limpo sem costura no centro do painel washi da luminaria!
            x0, x1 = min(xs), max(xs)
            y0, y1 = min(ys), max(ys)
            z0, z1 = min(zs), max(zs)
            span_x = max(x1 - x0, 1e-4)
            span_y = max(y1 - y0, 1e-4)
            span_z = max(z1 - z0, 1e-4)
            for f in bm.faces:
                for loop in f.loops:
                    co = loop.vert.co
                    u = (co.x - x0) / span_x if span_x >= span_y else (co.y - y0) / span_y
                    v = (co.z - z0) / span_z
                    loop[uv_layer].uv = (u, v)

        bm.to_mesh(me)
        bm.free()
        me.update()

    # Garante UV 0..1 limpa na frente do poster Vercel (Scroll_Canvas)
    scroll = bpy.data.objects.get("Scroll_Canvas")
    if scroll and scroll.data:
        bm = bmesh.new()
        bm.from_mesh(scroll.data)
        C.apply_box_uv(bm, fit_01=True)
        bm.to_mesh(scroll.data)
        bm.free()
        scroll.data.update()


def _remove_by_prefix(prefixes):
    for o in list(bpy.data.objects):
        if any(o.name.startswith(p) for p in prefixes):
            bpy.data.objects.remove(o, do_unlink=True)


def _ensure_collision(obj, outer=0.008, friction=22.0):
    if not obj:
        return
    for m in list(obj.modifiers):
        if m.type == "COLLISION":
            obj.modifiers.remove(m)
    obj.modifiers.new("Collision", "COLLISION")
    obj.collision.thickness_outer = outer
    obj.collision.thickness_inner = 0.015
    obj.collision.cloth_friction = friction
    obj.collision.damping = 0.72


def make_quilted_cloth_grid(name, center, size_xy, segs_xy, mat, col, rot_z=0.0, uv_scale=1.65, quilt_step=0.0, drape_edges=False):
    """Cria malha Cloth com dobras organicas iniciais, costura matelasse opcional e UV continua 1:1."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=segs_xy[0], y_segments=segs_xy[1], size=0.5)
    sx, sy = size_xy
    for v in bm.verts:
        nx = v.co.x * sx
        ny = v.co.y * sy
        # Micro-ondulacoes assimetricas que viram dobras naturais vividas na simulacao
        nz = (
            0.009 * math.sin(nx * 4.8 + ny * 3.1)
            + 0.006 * math.cos(nx * 8.3 - ny * 6.7)
            + 0.004 * math.sin(nx * 14.0 + ny * 11.0)
        )
        # Costura matelasse (quilted channels) sutil na colcha terracota
        if quilt_step > 0.0:
            qx = abs(math.sin(nx * math.pi / quilt_step))
            qy = abs(math.sin(ny * math.pi / quilt_step))
            tuft = (qx * qy) ** 0.35
            nz += 0.008 * (tuft - 0.5)
        # Curvatura inicial suave nas bordas para o tecido abracar o colchao sem ficar "armado"
        if drape_edges:
            ax = abs(v.co.x) * 2.0
            ay = abs(v.co.y) * 2.0
            if ax > 0.76:
                nz -= 0.055 * ((ax - 0.76) / 0.24) ** 1.6
            if v.co.y < -0.35:
                f_drop = (-v.co.y - 0.35) / 0.15
                nz -= 0.060 * (max(0.0, f_drop) ** 1.6)
        v.co = Vector((nx, ny, nz))

    bm.normal_update()
    uv_layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for loop in f.loops:
            # UV continua proporcional em metros (sem costura e sem distorcao)
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


def make_oxford_pillow(name, center, size_xyz, mat, col, rot=(0, 0, 0), uv_scale=2.2, pressure=5.4):
    """Travesseiro detalhado com aba/costura perimetral estilo Oxford + inflacao real via Cloth Pressure."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=14, use_grid_fill=True)
    sx, sy, sz = size_xyz
    for v in bm.verts:
        ux, uy, uz = v.co.x * 2.0, v.co.y * 2.0, v.co.z * 2.0  # -1..1
        edge_d = max(abs(ux), abs(uy))
        # Pinça a borda perimetral criando costura/aba Oxford super realista!
        if edge_d > 0.86:
            pinch = max(0.08, 1.0 - (edge_d - 0.86) / 0.14 * 0.90)
        else:
            pinch = 1.0 + 0.12 * (1.0 - edge_d ** 2)
        crease = 0.004 * math.sin(ux * 6.5 + uy * 4.0)
        v.co.x = v.co.x * sx
        v.co.y = v.co.y * sy
        v.co.z = v.co.z * sz * pinch + crease

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
    obj.rotation_euler = Euler(rot, "XYZ")
    obj.data.materials.append(mat)
    C.link_obj(obj, col)
    C.set_smooth(obj)

    cl = obj.modifiers.new("Cloth", "CLOTH")
    s = cl.settings
    s.quality = 6
    s.mass = 0.30
    s.tension_stiffness = 16.0
    s.compression_stiffness = 16.0
    s.shear_stiffness = 10.0
    s.bending_stiffness = 0.55
    s.use_pressure = True
    s.uniform_pressure_force = pressure
    s.pressure_factor = 1.15
    s.shrink_min = -0.04
    s.effector_weights.gravity = 0.85
    cl.collision_settings.use_collision = True
    cl.collision_settings.distance_min = 0.006
    return obj


def rebuild_settled_bedding(M):
    """Recria todos os tecidos da cama com fisica Cloth profundamente acomodada + detalhes (matelasse, manta e 3 travesseiros Oxford)."""
    col = "04_Cama_Futon"
    C.STAGE[0] = col

    _remove_by_prefix([
        "Sheet_Cloth", "Duvet_Cloth", "Throw_Cloth", "Pillow_Cloth",
        "Duvet_Terracotta", "Sheet_FoldCuff", "Pillow_Ochre",
    ])

    # Colisores bem justos para o tecido abracar o colchao e o estrado sem flutuar
    for cname in (
        "Futon_Mattress",
        "Bed_Rail_Front", "Bed_Rail_Back", "Bed_Rail_East", "Bed_Rail_West",
        "Bed_LampLedge_Top", "Headboard_TopRail", "Headboard_BotRail",
        "Tatami_03_BackR", "Tatami_04_Mid", "Tatami_05_Front", "Tatami_06_Right",
    ):
        _ensure_collision(bpy.data.objects.get(cname), outer=0.006, friction=24.0)
    for o in bpy.data.objects:
        if o.name.startswith("Headboard_Slat_"):
            _ensure_collision(o, outer=0.006, friction=14.0)

    matt_cx = 0.24

    # 1. Lencol creme dobrado com barra na cabeceira (comeca bem rente ao colchao em Z=0.358)
    sheet = make_quilted_cloth_grid(
        "Sheet_Cloth_Cream",
        center=(matt_cx, 0.44, 0.362),
        size_xy=(1.54, 0.86),
        segs_xy=(38, 26),
        mat=M["cream"],
        col=col,
        rot_z=math.radians(1.0),
        uv_scale=1.9,
        drape_edges=True,
    )
    cl_s = sheet.modifiers.new("Cloth", "CLOTH")
    cl_s.settings.quality = 7
    cl_s.settings.mass = 0.35
    cl_s.settings.tension_stiffness = 14.0
    cl_s.settings.bending_stiffness = 0.28
    cl_s.settings.air_damping = 0.8
    cl_s.collision_settings.use_collision = True
    cl_s.collision_settings.distance_min = 0.006

    # 2. Colcha/edredom terracota matelassado (comeca em Z=0.382, bem justo nas bordas, 60x54 subdivisoes!)
    duvet = make_quilted_cloth_grid(
        "Duvet_Cloth_Terracotta",
        center=(matt_cx + 0.005, -0.10, 0.385),
        size_xy=(1.76, 1.56),
        segs_xy=(58, 52),
        mat=M["terracotta"],
        col=col,
        rot_z=math.radians(-0.8),
        uv_scale=1.55,
        quilt_step=0.26,
        drape_edges=True,
    )
    cl_d = duvet.modifiers.new("Cloth", "CLOTH")
    cl_d.settings.quality = 8
    cl_d.settings.mass = 0.72
    cl_d.settings.tension_stiffness = 11.0
    cl_d.settings.compression_stiffness = 10.0
    cl_d.settings.shear_stiffness = 8.0
    cl_d.settings.bending_stiffness = 0.38  # Caimento macio e natural de edredom de linho!
    cl_d.settings.air_damping = 0.9
    cl_d.collision_settings.use_collision = True
    cl_d.collision_settings.distance_min = 0.007
    cl_d.collision_settings.use_self_collision = True
    cl_d.collision_settings.self_distance_min = 0.007

    # 3. Manta ocre dobrada casualmente aos pes da cama (camada extra de detalhe editorial!)
    throw = make_quilted_cloth_grid(
        "Throw_Cloth_Ochre",
        center=(matt_cx + 0.06, -0.56, 0.435),
        size_xy=(1.68, 0.56),
        segs_xy=(46, 20),
        mat=M["ochre"],
        col=col,
        rot_z=math.radians(3.5),
        uv_scale=1.85,
        drape_edges=True,
    )
    cl_t = throw.modifiers.new("Cloth", "CLOTH")
    cl_t.settings.quality = 7
    cl_t.settings.mass = 0.55
    cl_t.settings.tension_stiffness = 12.0
    cl_t.settings.bending_stiffness = 0.32
    cl_t.settings.air_damping = 0.9
    cl_t.collision_settings.use_collision = True
    cl_t.collision_settings.distance_min = 0.008

    # 4. Tres travesseiros Oxford detalhados (2 ocre traseiros + 1 linho creme frontal casual)
    p_l = make_oxford_pillow(
        "Pillow_Cloth_Ochre_L",
        center=(matt_cx - 0.35, 0.96, 0.425),
        size_xyz=(0.60, 0.38, 0.088),
        mat=M["ochre"],
        col=col,
        rot=(math.radians(17), 0, math.radians(-3)),
        pressure=5.2,
    )
    p_r = make_oxford_pillow(
        "Pillow_Cloth_Ochre_R",
        center=(matt_cx + 0.35, 0.96, 0.425),
        size_xyz=(0.60, 0.38, 0.088),
        mat=M["ochre"],
        col=col,
        rot=(math.radians(17), 0, math.radians(4)),
        pressure=5.2,
    )
    p_acc = make_oxford_pillow(
        "Pillow_Cloth_Cream_Accent",
        center=(matt_cx - 0.14, 0.72, 0.430),
        size_xyz=(0.46, 0.30, 0.082),
        mat=M["cream"],
        col=col,
        rot=(math.radians(26), math.radians(-2), math.radians(9)),
        pressure=4.6,
    )

    # Simula 45 quadros reais de Cloth (acomodacao completa por gravidade!)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 48
    for f in range(1, 46):
        scene.frame_set(f)

    # Adiciona espessura acolchoada + suavizacao POS-Cloth
    for obj, thick, sub_lvl in (
        (sheet, 0.009, 1),
        (duvet, 0.028, 1),
        (throw, 0.014, 1),
    ):
        sol = obj.modifiers.new("Solidify", "SOLIDIFY")
        sol.thickness = thick
        sol.offset = 1.0
        sub = obj.modifiers.new("Subsurf", "SUBSURF")
        sub.levels = sub_lvl
        sub.render_levels = sub_lvl

    for p in (p_l, p_r, p_acc):
        sub = p.modifiers.new("Subsurf", "SUBSURF")
        sub.levels = 1
        sub.render_levels = 1

    # Assa definitivamente os tecidos simulados do frame 45 na geometria (para Cycles e GLB/vgpu!)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in (sheet, duvet, throw, p_l, p_r, p_acc):
        ev = obj.evaluated_get(depsgraph)
        baked = bpy.data.meshes.new_from_object(ev)
        baked.name = f"{obj.name}_Baked"
        for poly in baked.polygons:
            poly.use_smooth = True
        old = obj.data
        obj.modifiers.clear()
        obj.data = baked
        if old.users == 0:
            bpy.data.meshes.remove(old)


# --- Plantas Japonesas (Ikebana Momiji, Kokedama Samambaia e Bambuzal no Engawa) ---

def _make_curved_branch(name, points, r_start, r_end, mat, col, segs=8):
    bm = bmesh.new()
    rings = []
    n_pts = len(points)
    for i, pt in enumerate(points):
        t = i / max(n_pts - 1, 1)
        r = r_start * (1.0 - t) + r_end * t
        if i < n_pts - 1:
            tang = (points[i + 1] - pt).normalized()
        else:
            tang = (pt - points[i - 1]).normalized()
        up = Vector((0, 0, 1)) if abs(tang.z) < 0.92 else Vector((1, 0, 0))
        side1 = tang.cross(up).normalized()
        side2 = tang.cross(side1).normalized()
        ring = []
        for s in range(segs):
            ang = 2.0 * math.pi * s / segs
            vco = pt + (side1 * math.cos(ang) + side2 * math.sin(ang)) * r
            ring.append(bm.verts.new(vco))
        rings.append(ring)
    for i in range(n_pts - 1):
        for s in range(segs):
            s2 = (s + 1) % segs
            bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
    bm.normal_update()
    C.apply_box_uv(bm, scale=4.0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.data.materials.append(mat)
    C.link_obj(obj, col)
    C.set_smooth(obj)
    return obj


def _make_leaf_cluster(name, positions_and_rots, leaf_len, leaf_w, mat, col, lobes=1):
    """Combina dezenas de folhas organicas em uma unica malha eficiente (otimo para WebGPU/GLB!)."""
    bm = bmesh.new()
    for pos, rot_eul, scale in positions_and_rots:
        rot_m = Euler(rot_eul, "XYZ").to_matrix()
        l = leaf_len * scale
        w = leaf_w * scale
        if lobes == 1:
            # Folha lanceolada (bambu / samambaia)
            pts_local = [
                Vector((0.0, 0.0, 0.0)),
                Vector((-w * 0.5, l * 0.32, l * 0.04)),
                Vector((0.0, l * 0.55, l * 0.06)),
                Vector((w * 0.5, l * 0.32, l * 0.04)),
                Vector((0.0, l, -l * 0.05)),
            ]
            vs = [bm.verts.new(pos + rot_m @ p) for p in pts_local]
            bm.faces.new((vs[0], vs[1], vs[2]))
            bm.faces.new((vs[0], vs[2], vs[3]))
            bm.faces.new((vs[1], vs[4], vs[2]))
            bm.faces.new((vs[2], vs[4], vs[3]))
        else:
            # Folha palmada de bordo japones (momiji - 3 lobulos elegantes)
            for ang_deg, l_mul in ((-42, 0.72), (0, 1.0), (42, 0.72)):
                lm = rot_m @ Euler((0, 0, math.radians(ang_deg)), "XYZ").to_matrix()
                ll = l * l_mul
                ww = w * 0.42 * l_mul
                pts_local = [
                    Vector((0.0, 0.0, 0.0)),
                    Vector((-ww, ll * 0.45, ll * 0.04)),
                    Vector((0.0, ll, -ll * 0.03)),
                    Vector((ww, ll * 0.45, ll * 0.04)),
                ]
                vs = [bm.verts.new(pos + lm @ p) for p in pts_local]
                bm.faces.new((vs[0], vs[1], vs[2], vs[3]))

    bm.normal_update()
    C.apply_box_uv(bm, scale=6.0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.data.materials.append(mat)
    C.link_obj(obj, col)
    C.set_smooth(obj)
    return obj


def _make_lathe_vase(name, center, profile_rz, mat, col, segs=28):
    bm = bmesh.new()
    rings = []
    for r, z in profile_rz:
        ring = []
        for s in range(segs):
            a = 2 * math.pi * s / segs
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(segs):
            s2 = (s + 1) % segs
            bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
    bm.normal_update()
    C.apply_box_uv(bm, scale=3.0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.location = Vector(center)
    obj.data.materials.append(mat)
    C.link_obj(obj, col)
    C.set_smooth(obj)
    return obj


def build_japanese_plants(M):
    col = "07_Plantas_Japonesas"
    C.STAGE[0] = col
    _remove_by_prefix(["Plant_", "Bamboo_"])

    rng = random.Random(42)

    # 1. TOKONOMA IKEBANA (Vaso ceramico artesanal + galhos de bordo japones Momiji sob o poster Vercel!)
    vx, vy, vz = 1.32, 1.02, 0.0
    # Base baixa de madeira escura (kadan)
    C.box("Plant_Tokonoma_Stand", (vx, vy, 0.015), (0.36, 0.24, 0.030), M["yakisugi"], col, bevel=0.003)
    # Vaso organico torneado
    vase_prof = [
        (0.052, 0.000), (0.068, 0.025), (0.092, 0.095), (0.098, 0.165),
        (0.082, 0.225), (0.044, 0.268), (0.048, 0.305), (0.042, 0.305), (0.038, 0.255),
    ]
    _make_lathe_vase("Plant_Ikebana_Vase", (vx, vy, 0.030), vase_prof, M["vase_stoneware"], col)

    # Galho principal arqueado e 3 sub-galhos em composicao ikebana (assimetria zen)
    b0 = Vector((vx, vy, 0.26))
    main_pts = [
        b0,
        b0 + Vector((-0.03, -0.02, 0.16)),
        b0 + Vector((-0.11, -0.05, 0.32)),
        b0 + Vector((-0.24, -0.08, 0.45)),
        b0 + Vector((-0.36, -0.10, 0.52)),
    ]
    sub1_pts = [
        main_pts[2],
        main_pts[2] + Vector((0.08, -0.06, 0.12)),
        main_pts[2] + Vector((0.18, -0.10, 0.20)),
    ]
    sub2_pts = [
        b0 + Vector((0.01, 0.0, 0.08)),
        b0 + Vector((0.11, -0.05, 0.22)),
        b0 + Vector((0.20, -0.12, 0.30)),
    ]
    _make_curved_branch("Plant_Momiji_BranchMain", main_pts, 0.010, 0.0035, M["branch_bark"], col)
    _make_curved_branch("Plant_Momiji_BranchSub1", sub1_pts, 0.006, 0.0025, M["branch_bark"], col)
    _make_curved_branch("Plant_Momiji_BranchSub2", sub2_pts, 0.007, 0.0025, M["branch_bark"], col)

    # Folhas de bordo japones (momiji) em tons terrosos russet e oliva
    leaves_russet, leaves_olive = [], []
    anchors = main_pts[2:] + sub1_pts[1:] + sub2_pts[1:]
    for a in anchors:
        for _ in range(9):
            off = Vector((rng.uniform(-0.08, 0.08), rng.uniform(-0.07, 0.07), rng.uniform(-0.04, 0.06)))
            rot = (rng.uniform(-0.45, 0.55), rng.uniform(-0.45, 0.45), rng.uniform(0, 2 * math.pi))
            sc = rng.uniform(0.75, 1.25)
            target_list = leaves_russet if rng.random() < 0.68 else leaves_olive
            target_list.append((a + off, rot, sc))
    _make_leaf_cluster("Plant_Momiji_LeavesRusset", leaves_russet, 0.085, 0.075, M["maple_russet"], col, lobes=3)
    _make_leaf_cluster("Plant_Momiji_LeavesOlive",  leaves_olive,  0.080, 0.070, M["maple_olive"],  col, lobes=3)

    # 2. KOKEDAMA DE MUSGO + SAMAMBAIA JAPONESA (no canto esquerdo frontal perto do shoji aberto)
    kx, ky = -1.38, -0.58
    C.cyl("Plant_Kokedama_Plate", (kx, ky, 0.010), 0.135, 0.018, verts=24, mat=M["slate_stone"], col=col, bevel=0.002)
    # Esfera organica de musgo
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.095)
    for v in bm.verts:
        n = 1.0 + 0.08 * math.sin(v.co.x * 45.0) * math.cos(v.co.y * 42.0)
        v.co.x *= n * 1.05
        v.co.y *= n * 1.05
        v.co.z = max(-0.068, v.co.z * n * 0.88)
    bm.normal_update()
    C.apply_box_uv(bm, scale=4.0)
    me_m = bpy.data.meshes.new("Plant_Kokedama_Moss")
    bm.to_mesh(me_m)
    bm.free()
    moss_obj = bpy.data.objects.new("Plant_Kokedama_Moss", me_m)
    moss_obj.location = Vector((kx, ky, 0.085))
    moss_obj.data.materials.append(M["moss"])
    C.link_obj(moss_obj, col)
    C.set_smooth(moss_obj)

    # 14 frondes arqueadas de samambaia japonesa saindo do kokedama
    fern_leaves = []
    for fi in range(14):
        ang = (2 * math.pi * fi / 14.0) + rng.uniform(-0.18, 0.18)
        reach = rng.uniform(0.16, 0.28)
        h_peak = rng.uniform(0.18, 0.34)
        p0 = Vector((kx, ky, 0.145))
        p1 = p0 + Vector((math.cos(ang) * reach * 0.45, math.sin(ang) * reach * 0.45, h_peak * 0.72))
        p2 = p0 + Vector((math.cos(ang) * reach, math.sin(ang) * reach, h_peak * 0.82))
        p3 = p0 + Vector((math.cos(ang) * reach * 1.32, math.sin(ang) * reach * 1.32, h_peak * 0.56))
        _make_curved_branch(f"Plant_Fern_Stem_{fi:02d}", [p0, p1, p2, p3], 0.004, 0.0015, M["fern_leaf"], col, segs=5)
        for seg_pt in (p1, (p1 + p2) * 0.5, p2, (p2 + p3) * 0.5, p3):
            for side in (-1, 1):
                l_ang = ang + side * math.radians(65) + rng.uniform(-0.2, 0.2)
                fern_leaves.append((seg_pt, (rng.uniform(-0.2, 0.25), 0.0, l_ang - math.pi / 2), rng.uniform(0.7, 1.1)))
    _make_leaf_cluster("Plant_Fern_Fronds", fern_leaves, 0.075, 0.022, M["fern_leaf"], col, lobes=1)

    # 3. JARDIM EXTERNO NO ENGAWA (bambus com nos segmentados + folhas densas + pedras de musgo)
    bamboo_leaves = []
    stalks = [
        (-2.35, -0.42, 0.024, 0.03),
        (-2.52, -0.18, 0.020, -0.025),
        (-2.28, -0.02, 0.022, 0.04),
        (-2.62, -0.62, 0.026, -0.02),
        (-2.45,  0.22, 0.019, 0.03),
        (-2.70,  0.05, 0.023, -0.03),
    ]
    for idx, (bx, by, br, tilt) in enumerate(stalks):
        pts = [Vector((bx + tilt * z * 0.5, by + tilt * z * 0.2, z)) for z in (0.0, 0.65, 1.30, 1.95, 2.55)]
        _make_curved_branch(f"Plant_Bamboo_Stalk_{idx}", pts, br, br * 0.72, M["bamboo"], col, segs=10)
        # Nos (aneis) caracteristicos do bambu + tufos de folhas
        for nz in (0.45, 0.90, 1.35, 1.80, 2.20):
            nx = bx + tilt * nz * 0.5
            ny = by + tilt * nz * 0.2
            C.cyl(f"Plant_Bamboo_Node_{idx}_{int(nz*100)}", (nx, ny, nz), br * 1.12, 0.014, verts=12, mat=M["bamboo"], col=col)
            if nz >= 0.85:
                for _ in range(10):
                    off = Vector((rng.uniform(-0.18, 0.22), rng.uniform(-0.18, 0.18), rng.uniform(-0.08, 0.14)))
                    rot = (rng.uniform(-0.55, 0.45), rng.uniform(-0.35, 0.35), rng.uniform(0, 2 * math.pi))
                    bamboo_leaves.append((Vector((nx, ny, nz)) + off, rot, rng.uniform(0.85, 1.35)))
    _make_leaf_cluster("Plant_Bamboo_Leaves", bamboo_leaves, 0.16, 0.030, M["bamboo_leaf"], col, lobes=1)

    # Pedras de jardim externas cobertas de musgo
    for si, (sx, sy, sr) in enumerate(((-2.22, -0.70, 0.16), (-2.42, -0.35, 0.20), (-2.30, 0.15, 0.14))):
        C.cyl(f"Plant_GardenStone_{si}", (sx, sy, -0.02), sr, 0.09, verts=14, mat=M["slate_stone"], col=col, bevel=0.015)


def run_polish_and_export():
    M = reload_all_textures_and_kakejiku()
    fix_architectural_uvs()
    rebuild_settled_bedding(M)
    build_japanese_plants(M)

    # Reposiciona camera hero um pouco mais aberta para mostrar tambem o Tokonoma + Ikebana + Poster Vercel + Kokedama + Shoji!
    cam = bpy.data.objects.get("Camera_Hero")
    if cam:
        cam.location = (0.18, -2.05, 0.82)
        target = Vector((-0.05, 0.78, 0.62))
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 26.0
        bpy.context.scene.camera = cam

    # Atualiza viewport ao vivo
    C.frame_viewport(use_camera=True)

    # Render rapido de auditoria Cycles (960x540, 32 samples)
    os.makedirs(REND_DIR, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.cycles.samples = 32
    scene.render.filepath = os.path.join(REND_DIR, "preview_hero_v2.png")
    bpy.ops.render.render(write_still=True)

    # Exporta GLB limpo (sem luzes duplicadas, texturas 1024px seamless embutidas, Cloth assado e plantas japonesas!)
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
    print(f"[Etapa 5 OK] Cloth acomodado + UVs + Plantas + Poster Vercel prontos! GLB: {size_mb:.2f} MB")


run_polish_and_export()
