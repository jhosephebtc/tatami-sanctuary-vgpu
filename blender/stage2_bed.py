"""Etapa 2: Cama baixa japonesa em nogueira (aba lateral integrada, cabeceira ripada, futon, edredom terracota e xicara)."""
import sys
import math
import bpy
import bmesh
from mathutils import Vector, Euler

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)

import common as C


def make_soft_cushion(name, center, size, mat, col, subdivisions=2, wave_amp=0.010, rot=(0, 0, 0), uv_scale=1.6, cuts=8):
    """Cria malha macia (futon, edredom terracota, travesseiro) com UVs limpas e dobras organicas."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=cuts, use_grid_fill=True)
    sx, sy, sz = size
    for v in bm.verts:
        x, y, z = v.co.x, v.co.y, v.co.z
        r = math.sqrt(min(1.0, (x * 2) ** 2 + (y * 2) ** 2))
        pillow_z = 1.0 - 0.26 * (r ** 2.2)
        # Dobras naturais de tecido (mais marcantes no topo)
        wrinkle = wave_amp * (
            0.55 * math.sin(x * 14.0 + y * 8.5) * math.cos(y * 10.5)
            + 0.45 * math.sin(x * 23.0 - y * 17.0)
        )
        v.co.x = x * sx
        v.co.y = y * sy
        v.co.z = z * sz * max(0.42, pillow_z) + (wrinkle if z > 0 else 0.0)
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

    sub = obj.modifiers.new("Subsurf", "SUBSURF")
    sub.levels = subdivisions
    sub.render_levels = subdivisions
    C.set_smooth(obj)
    return obj


def build_bed():
    M = {m.name: m for m in bpy.data.materials}
    if "Mat_Walnut" not in M:
        mats = C.get_materials()
    else:
        mats = {
            "walnut":     M["Mat_Walnut"],
            "hinoki":     M["Mat_Hinoki"],
            "yakisugi":   M["Mat_Yakisugi"],
            "cream":      M["Mat_FutonCream"],
            "terracotta": M["Mat_DuvetTerracotta"],
            "ochre":      M["Mat_PillowOchre"],
            "ceramic":    M["Mat_CeramicTea"],
        }

    col = "04_Cama_Futon"
    C.STAGE[0] = col

    # Plataforma da cama em nogueira escura com aba esquerda em balanco (igual a referencia hero!)
    # X in [-1.06, +1.04] (2.10 m total), Y in [-0.80, +1.30] (2.10 m)
    bed_x0, bed_x1 = -1.06, 1.04
    bed_y0, bed_y1 = -0.80, 1.30
    bed_cx = (bed_x0 + bed_x1) / 2.0
    bed_cy = (bed_y0 + bed_y1) / 2.0
    bed_w = bed_x1 - bed_x0
    bed_l = bed_y1 - bed_y0

    # 1. Base recuada flutuante (Z = 0.00..0.115)
    plinth_h = 0.115
    C.box("Bed_Plinth_S",      (0.18, bed_y0 + 0.18, plinth_h / 2), (1.42, 0.06, plinth_h), mats["walnut"], col, bevel=0.003, uv_scale=0.9)
    C.box("Bed_Plinth_N",      (0.18, bed_y1 - 0.18, plinth_h / 2), (1.42, 0.06, plinth_h), mats["walnut"], col, bevel=0.003, uv_scale=0.9)
    C.box("Bed_Plinth_W",      (-0.56, bed_cy, plinth_h / 2), (0.06, bed_l - 0.36, plinth_h), mats["walnut"], col, bevel=0.003, uv_scale=0.9)
    C.box("Bed_Plinth_E",      (0.88, bed_cy, plinth_h / 2), (0.06, bed_l - 0.36, plinth_h), mats["walnut"], col, bevel=0.003, uv_scale=0.9)
    C.box("Bed_Plinth_Center", (0.18, bed_cy, plinth_h / 2), (0.06, bed_l - 0.36, plinth_h), mats["walnut"], col, bevel=0.003, uv_scale=0.9)

    # 2. Quadro perimetral + aba esquerda em balanco (Z = 0.115..0.195)
    frame_z = 0.155
    frame_h = 0.080
    rail_w = 0.085
    C.box("Bed_Rail_Front", (bed_cx, bed_y0 + rail_w / 2, frame_z), (bed_w, rail_w, frame_h), mats["walnut"], col, bevel=0.004, uv_scale=0.8)
    C.box("Bed_Rail_Back",  (bed_cx, bed_y1 - rail_w / 2, frame_z), (bed_w, rail_w, frame_h), mats["walnut"], col, bevel=0.004, uv_scale=0.8)
    C.box("Bed_Rail_East",  (bed_x1 - rail_w / 2, bed_cy, frame_z), (rail_w, bed_l - 2 * rail_w, frame_h), mats["walnut"], col, bevel=0.004, uv_scale=0.8)
    C.box("Bed_Rail_West",  (bed_x0 + rail_w / 2, bed_cy, frame_z), (rail_w, bed_l - 2 * rail_w, frame_h), mats["walnut"], col, bevel=0.004, uv_scale=0.8)

    # Tampo solido da aba lateral esquerda para a luminaria e cha (X in [-1.06, -0.54], Z topo = 0.195)
    ledge_x0, ledge_x1 = -1.06, -0.54
    C.box("Bed_LampLedge_Top", ((ledge_x0 + ledge_x1) / 2, bed_cy, 0.178), (ledge_x1 - ledge_x0, bed_l - 0.02, 0.034), mats["walnut"], col, bevel=0.003, uv_scale=0.9)

    # Ripas sunoko sob o colchao
    n_slats = 11
    for i in range(n_slats):
        sy = bed_y0 + 0.16 + i * ((bed_l - 0.32) / (n_slats - 1))
        C.box(f"Bed_Slat_{i:02d}", (0.24, sy, 0.175), (1.46, 0.10, 0.022), mats["walnut"], col, bevel=0.002, uv_scale=0.9)

    # 3. Cabeceira ripada em nogueira (atras do colchao, X in [-0.56, +1.04], Z = 0.195..0.90)
    hb_x0, hb_x1 = -0.56, 1.04
    hb_cx = (hb_x0 + hb_x1) / 2.0
    hb_w = hb_x1 - hb_x0
    hb_y = bed_y1 - 0.035
    C.box("Headboard_Post_W",  (hb_x0 + 0.028, hb_y, 0.55), (0.052, 0.052, 0.71), mats["walnut"], col, bevel=0.003, uv_scale=0.9)
    C.box("Headboard_Post_E",  (hb_x1 - 0.028, hb_y, 0.55), (0.052, 0.052, 0.71), mats["walnut"], col, bevel=0.003, uv_scale=0.9)
    C.box("Headboard_TopRail", (hb_cx, hb_y, 0.885), (hb_w, 0.056, 0.044), mats["walnut"], col, bevel=0.003, uv_scale=0.9)
    C.box("Headboard_BotRail", (hb_cx, hb_y, 0.245), (hb_w - 0.06, 0.046, 0.040), mats["walnut"], col, bevel=0.002, uv_scale=0.9)
    n_vslats = 22
    for i in range(n_vslats):
        sx = (hb_x0 + 0.08) + i * ((hb_w - 0.16) / (n_vslats - 1))
        C.box(f"Headboard_Slat_{i:02d}", (sx, hb_y, 0.565), (0.032, 0.024, 0.60), mats["walnut"], col, bevel=0.002, uv_scale=1.0)

    # 4. Colchao Futon em linho cru creme (X center = +0.24, 1.50 x 1.98 m)
    matt_cx, matt_cy = 0.24, 0.24
    make_soft_cushion("Futon_Mattress", (matt_cx, matt_cy, 0.268), (1.48, 1.96, 0.148), mats["cream"], col, subdivisions=2, wave_amp=0.005, uv_scale=1.5)

    # 5. Edredom terracota-ferrugem (kakebuton) com dobras ricas + dobra superior do lencol creme
    make_soft_cushion("Duvet_Terracotta", (matt_cx, -0.05, 0.362), (1.58, 1.44, 0.112), mats["terracotta"], col, subdivisions=2, wave_amp=0.016, uv_scale=1.4, cuts=10)
    make_soft_cushion("Sheet_FoldCuff",   (matt_cx,  0.62, 0.376), (1.52, 0.28, 0.064), mats["cream"], col, subdivisions=2, wave_amp=0.011, uv_scale=1.6, cuts=8)

    # 6. Dois travesseiros ocre queimado (fiel a referencia hero!) + almofada creme traseira
    make_soft_cushion("Pillow_Ochre_L", (matt_cx - 0.35, 0.96, 0.415), (0.58, 0.38, 0.145), mats["ochre"], col, subdivisions=2, wave_amp=0.009, rot=(math.radians(15), 0, math.radians(-3)), uv_scale=1.8)
    make_soft_cushion("Pillow_Ochre_R", (matt_cx + 0.35, 0.96, 0.415), (0.58, 0.38, 0.145), mats["ochre"], col, subdivisions=2, wave_amp=0.009, rot=(math.radians(15), 0, math.radians(4)), uv_scale=1.8)

    # 7. Bandejinha escura + xicara yunomi na aba da cama a frente da luminaria (exatamente como nas referencias!)
    tray_x, tray_y, tray_z = -0.78, 0.12, 0.195
    C.box("TeaTray_Base",  (tray_x, tray_y, tray_z + 0.008), (0.20, 0.16, 0.014), mats["yakisugi"], col, bevel=0.003, uv_scale=2.0)
    C.cyl("TeaCup_Saucer", (tray_x, tray_y, tray_z + 0.017), 0.046, 0.007, verts=28, mat=mats["walnut"], col=col, bevel=0.001)
    C.cyl("TeaCup_Yunomi", (tray_x, tray_y, tray_z + 0.056), 0.036, 0.078, verts=28, mat=mats["ceramic"], col=col, bevel=0.002)

    C.frame_viewport()
    print("[Etapa 2 OK] Cama baixa em nogueira, futon, edredom terracota, travesseiros ocre e cha criados.")


build_bed()
