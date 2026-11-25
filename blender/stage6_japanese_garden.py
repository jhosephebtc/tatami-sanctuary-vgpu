"""Etapa 6: Remove todas as plantas internas, abre as portas shoji, cria bambuzal externo com folhas 100% conectadas aos nos/galhos
e importa vegetacao e pedras reais CC0 do Poly Haven para compor um jardim japones externo autentico no engawa.
"""
import json
import math
import os
import random
import shutil
import sys
import bpy
import bmesh
from mathutils import Vector, Euler

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
PH_DIR = os.path.join(PROJ_DIR, "assets_polyhaven")
EXP_GLB = os.path.join(PROJ_DIR, "export", "sala_japonesa.glb")
WEB_GLB = os.path.join(PROJ_DIR, "web-vgpu", "public", "sala_japonesa.glb")
REND_DIR = os.path.join(PROJ_DIR, "renders")

if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)

import common as C


def _remove_by_prefix(prefixes):
    for o in list(bpy.data.objects):
        if any(o.name.startswith(p) for p in prefixes):
            bpy.data.objects.remove(o, do_unlink=True)


def _make_tube(name, points, r0, r1, mat, col, segs=8):
    bm = bmesh.new()
    rings = []
    n = len(points)
    for i, pt in enumerate(points):
        t = i / max(n - 1, 1)
        r = r0 * (1.0 - t) + r1 * t
        tang = (points[i + 1] - pt).normalized() if i < n - 1 else (pt - points[i - 1]).normalized()
        up = Vector((0, 0, 1)) if abs(tang.z) < 0.92 else Vector((1, 0, 0))
        s1 = tang.cross(up).normalized()
        s2 = tang.cross(s1).normalized()
        rings.append([bm.verts.new(pt + (s1 * math.cos(2 * math.pi * k / segs) + s2 * math.sin(2 * math.pi * k / segs)) * r) for k in range(segs)])
    for i in range(n - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    bm.normal_update()
    C.apply_box_uv(bm, scale=3.0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.data.materials.append(mat)
    C.link_obj(obj, col)
    C.set_smooth(obj)
    return obj


def _build_connected_bamboo_grove(M, col):
    """Constroi bambus externos com colmos segmentados, nos, galhinhos conectados aos nos e folhas presas diretamente nos galhos."""
    rng = random.Random(73)
    mat_culm = M.get("Mat_Bamboo") or C.make_solid_mat("Mat_Bamboo", (0.20, 0.28, 0.12), rough=0.52)
    mat_leaf = M.get("Mat_BambooLeaf") or C.make_solid_mat("Mat_BambooLeaf", (0.14, 0.24, 0.085), rough=0.58)

    bm_leaves = bmesh.new()

    def add_leaf_at(anchor, direction, length=0.14, width=0.022):
        d = direction.normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        side = d.cross(up).normalized()
        up2 = side.cross(d).normalized()
        # Folha lanceolada levemente arqueada saindo EXATAMENTE do ponto `anchor` no galho!
        p0 = anchor
        p1 = anchor + d * (length * 0.30) - side * (width * 0.5) + up2 * (length * 0.04)
        p2 = anchor + d * (length * 0.52) + up2 * (length * 0.05)
        p3 = anchor + d * (length * 0.30) + side * (width * 0.5) + up2 * (length * 0.04)
        p4 = anchor + d * length - up2 * (length * 0.08)
        vs = [bm_leaves.verts.new(p) for p in (p0, p1, p2, p3, p4)]
        bm_leaves.faces.new((vs[0], vs[1], vs[2]))
        bm_leaves.faces.new((vs[0], vs[2], vs[3]))
        bm_leaves.faces.new((vs[1], vs[4], vs[2]))
        bm_leaves.faces.new((vs[2], vs[4], vs[3]))

    # Posicoes externas no jardim atras da varanda engawa (X in [-2.95, -4.10])
    stalks = [
        (-2.98,  0.65, 0.024,  0.03, -0.02),
        (-3.22,  0.22, 0.021, -0.02,  0.03),
        (-3.08, -0.25, 0.025,  0.02,  0.02),
        (-3.45, -0.68, 0.022, -0.03, -0.02),
        (-3.62,  0.48, 0.026,  0.02, -0.01),
        (-3.78, -0.10, 0.020, -0.02,  0.02),
        (-3.30,  0.98, 0.023,  0.01, -0.03),
        (-3.90, -0.95, 0.024,  0.03,  0.02),
    ]

    for idx, (bx, by, br, tx, ty) in enumerate(stalks):
        def pos_at(z):
            return Vector((bx + tx * (z ** 1.25) * 0.45, by + ty * (z ** 1.25) * 0.45, z))

        pts = [pos_at(z) for z in (0.0, 0.45, 0.90, 1.35, 1.80, 2.25, 2.75)]
        _make_tube(f"Garden_Bamboo_Culm_{idx}", pts, br, br * 0.65, mat_culm, col, segs=10)

        # Nos (aneis) + galhos finos conectados ao no + folhas saindo direto das pontas dos galhos!
        for nz in (0.42, 0.84, 1.26, 1.68, 2.08, 2.46):
            np_pt = pos_at(nz)
            C.cyl(f"Garden_Bamboo_Node_{idx}_{int(nz*100)}", np_pt, br * 1.15, 0.014, verts=12, mat=mat_culm, col=col)
            if nz >= 0.80:
                n_twigs = 2 if nz < 1.6 else 3
                for ti in range(n_twigs):
                    az = rng.uniform(0, 2 * math.pi)
                    twig_len = rng.uniform(0.24, 0.44)
                    tdir = Vector((math.cos(az), math.sin(az), rng.uniform(0.35, 0.72))).normalized()
                    t0 = np_pt + Vector((math.cos(az) * br * 0.8, math.sin(az) * br * 0.8, 0.0))
                    t1 = t0 + tdir * (twig_len * 0.52)
                    t2 = t1 + (tdir + Vector((0, 0, -0.18))).normalized() * (twig_len * 0.50)
                    _make_tube(f"Garden_Bamboo_Twig_{idx}_{int(nz*100)}_{ti}", [t0, t1, t2], 0.0045, 0.0018, mat_culm, col, segs=5)
                    # Folhas presas EXATAMENTE ao longo de t1 -> t2 (zero folhas flutuantes!)
                    for frac in (0.45, 0.72, 0.92, 1.0):
                        anchor = t1.lerp(t2, frac) if frac > 0.5 else t0.lerp(t1, frac * 2.0)
                        for side in (-1, 1):
                            ldir = (t2 - t1).normalized() + Vector((-tdir.y * side * 0.65, tdir.x * side * 0.65, rng.uniform(-0.35, 0.05)))
                            add_leaf_at(anchor, ldir, length=rng.uniform(0.11, 0.16), width=rng.uniform(0.018, 0.026))
                        if frac == 1.0:
                            add_leaf_at(t2, (t2 - t1).normalized() + Vector((0, 0, -0.15)), length=0.14, width=0.022)

    bm_leaves.normal_update()
    C.apply_box_uv(bm_leaves, scale=6.0)
    me_l = bpy.data.meshes.new("Garden_Bamboo_Leaves_Connected")
    bm_leaves.to_mesh(me_l)
    bm_leaves.free()
    leaf_obj = bpy.data.objects.new("Garden_Bamboo_Leaves_Connected", me_l)
    leaf_obj.data.materials.append(mat_leaf)
    C.link_obj(leaf_obj, col)
    C.set_smooth(leaf_obj)


def _import_polyhaven_asset(gltf_path, tag, loc, rot_z=0.0, scale=1.0, col="07_Jardim_Externo", max_tris=22000):
    if not gltf_path or not os.path.exists(gltf_path):
        return []
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=gltf_path)
    added = [o for o in bpy.data.objects if o not in before]
    # Agrupa sob um Empty posicionavel para preservar hierarquia e sub-pecas
    root_empty = bpy.data.objects.new(f"PH_{tag}", None)
    root_empty.location = Vector(loc)
    root_empty.rotation_euler = Euler((0.0, 0.0, math.radians(rot_z)), "XYZ")
    root_empty.scale = Vector((scale, scale, scale))
    C.link_obj(root_empty, col)

    target_col = C.get_collection(col)
    for o in added:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        target_col.objects.link(o)
        if o.parent is None:
            o.parent = root_empty
        if o.type == "MESH" and o.data:
            # Garante texturas embutidas e aplica decimate suave se muito denso para WebGPU fluido
            poly_count = len(o.data.polygons)
            if poly_count > max_tris:
                dec = o.modifiers.new("Decimate_WebGPU", "DECIMATE")
                dec.ratio = max(0.12, max_tris / float(poly_count))
            for mat in o.data.materials:
                if mat and mat.use_nodes:
                    for n in mat.node_tree.nodes:
                        if n.type == "TEX_IMAGE" and n.image:
                            try:
                                n.image.pack()
                            except Exception:
                                pass
    return added


def run_garden_upgrade():
    M = {m.name: m for m in bpy.data.materials}

    # 1. REMOVE TODAS AS PLANTAS INTERNAS E BAMBUS ANTIGOS
    _remove_by_prefix([
        "Plant_", "Garden_", "PH_", "Bamboo_", "Exterior_Fence", "Garden_Ground",
    ])

    # 2. ABRE MAIS AS PORTAS SHOJI PARA REVELAR O ENGAWA E O JARDIM JAPONES!
    # Abertura total do shoji: Y in [-1.12, +1.12] (2.24 m).
    # Empurra Shoji_North para o fundo (y_center = +0.62) e abre Shoji_South bem para fora/sul (ou recuado),
    # criando um vao livre generoso de ~1.05 m bem no eixo visual da camera!
    shoji_n = [o for o in bpy.data.objects if o.name.startswith("Shoji_North_")]
    if shoji_n:
        avg_yn = sum(o.location.y for o in shoji_n) / len(shoji_n)
        shift_n = 0.72 - avg_yn
        for o in shoji_n:
            o.location.y += shift_n

    shoji_s = [o for o in bpy.data.objects if o.name.startswith("Shoji_South_")]
    if shoji_s:
        # Desliza Shoji_South tambem para o lado norte sobre o trilho externo (porta dupla totalmente recolhida!)
        # deixando Y in [-1.10, +0.16] (~1.26 m!) totalmente aberto para o jardim japones!
        avg_ys = sum(o.location.y for o in shoji_s) / len(shoji_s)
        shift_s = 0.68 - avg_ys
        for o in shoji_s:
            o.location.y += shift_s

    # 3. CRIA CHAO DO JARDIM (CASCA/TERRA ESCURA + CERCA RIPADA DE CEDRO AFASTADA)
    col = "07_Jardim_Externo"
    C.STAGE[0] = col
    mat_earth = C.make_solid_mat("Mat_GardenEarth", (0.09, 0.072, 0.052), rough=0.95)
    mat_gravel = C.make_solid_mat("Mat_ZenGravel", (0.28, 0.25, 0.21), rough=0.92)
    mat_walnut = M.get("Mat_Walnut")
    mat_yakisugi = M.get("Mat_Yakisugi") or mat_walnut

    # Solo do jardim fora do engawa (X in [-2.80, -5.20], Y in [-2.6, +2.6])
    C.box("Garden_Ground_Earth", (-4.0, 0.0, -0.14), (2.70, 5.60, 0.12), mat_earth, col, bevel=0.0)
    # Faixa de cascalho zen logo apos o engawa
    C.box("Garden_ZenGravel_Strip", (-3.15, -0.10, -0.075), (0.95, 3.60, 0.025), mat_gravel, col, bevel=0.004)

    # Cerca ripada japonesa de madeira escura (Yakisugi) bem afastada em X = -4.65 m para deixar o ceu/luz entrar!
    C.box("Garden_Fence_RailBot", (-4.65, 0.0, 0.35), (0.05, 5.20, 0.06), mat_yakisugi, col, bevel=0.002)
    C.box("Garden_Fence_RailTop", (-4.65, 0.0, 1.75), (0.05, 5.20, 0.06), mat_yakisugi, col, bevel=0.002)
    for fi in range(28):
        fy = -2.45 + fi * 0.18
        C.box(f"Garden_Fence_Slat_{fi:02d}", (-4.68, fy, 0.98), (0.022, 0.135, 2.08), mat_yakisugi, col, bevel=0.002)

    # 4. BAMBUZAL EXTERNO COM FOLHAS 100% CONECTADAS AOS GALHOS
    _build_connected_bamboo_grove(M, col)

    # 5. IMPORTA VEGETACAO E PEDRAS REAIS CC0 DO POLY HAVEN NO JARDIM JAPONES EXTERNO!
    idx_path = os.path.join(PH_DIR, "index.json")
    ph = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}

    # Pedras com musgo (rock_moss_set_01) proximas ao engawa
    if "rock_moss_set_01" in ph:
        _import_polyhaven_asset(ph["rock_moss_set_01"], "MossRocks_A", (-3.25, -0.55, -0.06), rot_z=25, scale=0.72, col=col, max_tris=12000)
        _import_polyhaven_asset(ph["rock_moss_set_01"], "MossRocks_B", (-3.55,  0.35, -0.06), rot_z=140, scale=0.62, col=col, max_tris=12000)

    # Samambaias reais (fern_02) junto as pedras e base dos bambus
    if "fern_02" in ph:
        _import_polyhaven_asset(ph["fern_02"], "Fern_A", (-3.05, -0.82, -0.06), rot_z=15, scale=1.05, col=col, max_tris=14000)
        _import_polyhaven_asset(ph["fern_02"], "Fern_B", (-3.15, -0.18, -0.06), rot_z=115, scale=0.92, col=col, max_tris=14000)
        _import_polyhaven_asset(ph["fern_02"], "Fern_C", (-3.35,  0.55, -0.06), rot_z=210, scale=1.00, col=col, max_tris=14000)

    # Arbustos reais (shrub_02) dando volume natural atras das pedras
    if "shrub_02" in ph:
        _import_polyhaven_asset(ph["shrub_02"], "Shrub_A", (-3.85, -0.45, -0.06), rot_z=30, scale=0.85, col=col, max_tris=16000)
        _import_polyhaven_asset(ph["shrub_02"], "Shrub_B", (-3.95,  0.40, -0.06), rot_z=165, scale=0.78, col=col, max_tris=16000)

    # Arvore japonesa ornamental (tree_small_02) no fundo esquerdo do jardim, banhada pelo sol de fim de tarde!
    if "tree_small_02" in ph:
        _import_polyhaven_asset(ph["tree_small_02"], "GardenTree", (-4.05, -0.05, -0.06), rot_z=45, scale=0.58, col=col, max_tris=22000)

    # Ajusta camera hero ligeiramente a direita olhando para esquerda/fundo para enquadrar
    # cama + luminaria + poster Vercel + portas shoji ABERTAS revelando o jardim japones real!
    scene = bpy.context.scene
    cam = bpy.data.objects.get("Camera_Hero")
    if cam:
        cam.location = (0.58, -1.96, 0.84)
        target = Vector((-0.34, 0.62, 0.64))
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 26.0
        scene.camera = cam

    # Renderiza preview_hero_v4.png (Cycles 32 samples Khronos PBR Neutral)
    os.makedirs(REND_DIR, exist_ok=True)
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.cycles.samples = 32
    scene.render.filepath = os.path.join(REND_DIR, "preview_hero_v4.png")
    bpy.ops.render.render(write_still=True)

    # Exporta GLB otimizado (sem luzes duplicadas) para web-vgpu/public
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
    print(f"[Etapa 6 OK] Plantas internas removidas, shoji aberto, jardim Poly Haven + bambus prontos! GLB: {size_mb:.2f} MB")


run_garden_upgrade()
