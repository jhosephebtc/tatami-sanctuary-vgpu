"""Helpers, UV box-projection em metros e materiais PBR em imagem (Blender + GLB/vgpu)."""
import os
import math
import bpy
import bmesh
from mathutils import Euler, Vector

PROJ_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint"
TEX_DIR = os.path.join(PROJ_DIR, "textures")

STAGE = ["misc"]
PARTS = []


def get_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def link_obj(obj, col_name=None, stage=None):
    st = stage or STAGE[0]
    col = get_collection(col_name or st)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    obj["blueprint_stage"] = st
    PARTS.append((obj.name, st))
    return obj


def set_smooth(obj):
    mesh = obj.data
    if hasattr(mesh, "polygons"):
        for p in mesh.polygons:
            p.use_smooth = True


def apply_box_uv(bm, scale=1.0, rot_uv_90=False, fit_01=False):
    """Cria UVs limpas (triplanar/box em metros ou 0..1) diretamente no bmesh para exportar 100% em GLB."""
    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    if fit_01:
        # Mapeia bounding box X/Z (frente) para [0..1] (ideal para o pergaminho kakejiku)
        xs = [v.co.x for v in bm.verts]
        zs = [v.co.z for v in bm.verts]
        x0, x1 = min(xs), max(xs)
        z0, z1 = min(zs), max(zs)
        dx = max(x1 - x0, 1e-5)
        dz = max(z1 - z0, 1e-5)
        for f in bm.faces:
            for loop in f.loops:
                u = (loop.vert.co.x - x0) / dx
                v = (loop.vert.co.z - z0) / dz
                loop[uv_layer].uv = (u, v)
        return

    for f in bm.faces:
        n = f.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in f.loops:
            co = loop.vert.co
            if az >= ax and az >= ay:
                u, v = co.x * scale, co.y * scale
            elif ax >= ay and ax >= az:
                u, v = co.y * scale, co.z * scale
            else:
                u, v = co.x * scale, co.z * scale
            if rot_uv_90:
                u, v = v, -u
            loop[uv_layer].uv = (u, v)


def add_bevel(obj, width=0.003, segments=2):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(30.0)
    mod.harden_normals = False
    return mod


def box(name, center, size, mat=None, col=None, rot=(0, 0, 0), bevel=0.0025, segments=2, smooth=False, uv_scale=1.0, rot_uv_90=False, fit_01=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.normal_update()
    apply_box_uv(bm, scale=uv_scale, rot_uv_90=rot_uv_90, fit_01=fit_01)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(center)
    obj.rotation_euler = Euler(rot, "XYZ")
    if mat:
        obj.data.materials.append(mat)
    link_obj(obj, col)
    if bevel and bevel > 0:
        add_bevel(obj, width=bevel, segments=segments)
    if smooth:
        set_smooth(obj)
    return obj


def cyl(name, center, radius, depth, verts=28, mat=None, col=None, rot=(0, 0, 0), bevel=0.0, smooth=True, uv_scale=2.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=verts,
        radius1=radius,
        radius2=radius,
        depth=depth,
    )
    bm.normal_update()
    apply_box_uv(bm, scale=uv_scale)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(center)
    obj.rotation_euler = Euler(rot, "XYZ")
    if mat:
        obj.data.materials.append(mat)
    link_obj(obj, col)
    if bevel and bevel > 0:
        add_bevel(obj, width=bevel, segments=2)
    if smooth:
        set_smooth(obj)
    return obj


# --- Materiais PBR baseados em mapas de imagem (compativeis com Cycles, Material Preview e GLB/vgpu) ---

def _load_img(filename, colorspace="sRGB"):
    path = os.path.join(TEX_DIR, filename)
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = colorspace
    try:
        img.pack()
    except Exception:
        pass
    return img


def _set_input(node, names, value):
    for n in (names if isinstance(names, (list, tuple)) else [names]):
        if n in node.inputs:
            node.inputs[n].default_value = value
            return node.inputs[n]
    return None


def make_pbr_image_mat(
    name,
    prefix,
    normal_strength=0.45,
    specular=0.20,
    sheen=0.0,
    emission_strength=0.0,
    emission_tint=None,
    metallic=0.0,
    rough_override=None,
):
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name], do_unlink=True)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (620, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (260, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Albedo (sRGB)
    alb_path = f"{prefix}_albedo.png"
    if os.path.exists(os.path.join(TEX_DIR, alb_path)):
        t_alb = nt.nodes.new("ShaderNodeTexImage")
        t_alb.location = (-220, 260)
        t_alb.image = _load_img(alb_path, "sRGB")
        nt.links.new(t_alb.outputs["Color"], bsdf.inputs["Base Color"])
        if emission_strength > 0.0:
            if emission_tint:
                mix_e = nt.nodes.new("ShaderNodeMix")
                mix_e.data_type = "RGBA"
                mix_e.blend_type = "MULTIPLY"
                mix_e.inputs["Factor"].default_value = 1.0
                mix_e.inputs["B"].default_value = (*emission_tint, 1.0)
                nt.links.new(t_alb.outputs["Color"], mix_e.inputs["A"])
                nt.links.new(mix_e.outputs["Result"], bsdf.inputs["Emission Color"])
            else:
                nt.links.new(t_alb.outputs["Color"], bsdf.inputs["Emission Color"])
            _set_input(bsdf, "Emission Strength", emission_strength)

    # Roughness (Non-Color)
    rgh_path = f"{prefix}_rough.png"
    if rough_override is not None:
        _set_input(bsdf, "Roughness", rough_override)
    elif os.path.exists(os.path.join(TEX_DIR, rgh_path)):
        t_rgh = nt.nodes.new("ShaderNodeTexImage")
        t_rgh.location = (-220, 0)
        t_rgh.image = _load_img(rgh_path, "Non-Color")
        nt.links.new(t_rgh.outputs["Color"], bsdf.inputs["Roughness"])

    # Normal Map OpenGL (Non-Color)
    nrm_path = f"{prefix}_normal.png"
    if normal_strength > 0.0 and os.path.exists(os.path.join(TEX_DIR, nrm_path)):
        t_nrm = nt.nodes.new("ShaderNodeTexImage")
        t_nrm.location = (-320, -260)
        t_nrm.image = _load_img(nrm_path, "Non-Color")
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.location = (0, -240)
        nmap.inputs["Strength"].default_value = normal_strength
        nt.links.new(t_nrm.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    _set_input(bsdf, ["Specular IOR Level", "Specular"], specular)
    _set_input(bsdf, "Metallic", metallic)
    if sheen > 0.0:
        _set_input(bsdf, ["Sheen Weight", "Sheen"], sheen)
    return m


def make_solid_mat(name, color, rough=0.35, metallic=0.0, coat=0.0):
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name], do_unlink=True)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (420, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (120, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    _set_input(bsdf, "Base Color", (*color, 1.0))
    _set_input(bsdf, "Roughness", rough)
    _set_input(bsdf, "Metallic", metallic)
    if coat > 0:
        _set_input(bsdf, ["Coat Weight", "Clearcoat"], coat)
    return m


def get_materials():
    return {
        "walnut":        make_pbr_image_mat("Mat_Walnut", "walnut", normal_strength=0.40, specular=0.22),
        "hinoki":        make_pbr_image_mat("Mat_Hinoki", "hinoki", normal_strength=0.35, specular=0.22),
        "yakisugi":      make_pbr_image_mat("Mat_Yakisugi", "yakisugi", normal_strength=0.55, specular=0.18),
        "tatami":        make_pbr_image_mat("Mat_Tatami", "tatami", normal_strength=0.55, specular=0.16),
        "heri":          make_pbr_image_mat("Mat_Heri", "heri", normal_strength=0.35, specular=0.15, sheen=0.20),
        "plaster":       make_pbr_image_mat("Mat_JurakuPlaster", "plaster", normal_strength=0.45, specular=0.14),
        # Shoji washi com brilho difuso dourado suave de fim de tarde (aparece tanto no Cycles quanto no GLB/vgpu!)
        "washi_shoji":   make_pbr_image_mat("Mat_WashiShoji", "washi_shoji", normal_strength=0.15, specular=0.12, emission_strength=1.15, emission_tint=(1.0, 0.88, 0.68)),
        # Luminaria Andon: brilho quente ambar fibroso de 2600K
        "washi_lantern": make_pbr_image_mat("Mat_WashiLantern", "washi_lantern", normal_strength=0.25, specular=0.10, emission_strength=4.2, emission_tint=(1.0, 0.76, 0.40)),
        "terracotta":    make_pbr_image_mat("Mat_DuvetTerracotta", "terracotta", normal_strength=0.55, specular=0.14, sheen=0.48),
        "ochre":         make_pbr_image_mat("Mat_PillowOchre", "ochre", normal_strength=0.50, specular=0.14, sheen=0.45),
        "cream":         make_pbr_image_mat("Mat_FutonCream", "cream", normal_strength=0.45, specular=0.14, sheen=0.42),
        "kakejiku":      make_pbr_image_mat("Mat_Kakejiku", "kakejiku", normal_strength=0.0, specular=0.12, rough_override=0.90),
        "ceramic":       make_solid_mat("Mat_CeramicTea", (0.12, 0.095, 0.08), rough=0.34, coat=0.45),
        "brass":         make_solid_mat("Mat_Brass", (0.78, 0.58, 0.26), rough=0.34, metallic=0.92),
        "bamboo":        make_solid_mat("Mat_Bamboo", (0.18, 0.24, 0.12), rough=0.58),
    }


def frame_viewport(use_camera=False):
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            if space and hasattr(space, "shading"):
                space.shading.type = "MATERIAL"
            if use_camera and space and space.region_3d:
                space.region_3d.view_perspective = "CAMERA"
            else:
                for region in area.regions:
                    if region.type == "WINDOW":
                        with bpy.context.temp_override(area=area, region=region):
                            bpy.ops.view3d.view_all()
                        break
