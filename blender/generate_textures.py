"""Gera mapas PBR 1024x1024 matematicamente SEAMLESS (ruido periodico 2D via FFT, zero emendas!)
com destaque para linho artesanal slubbed realista, argila juraku sem costura, madeiras alinhadas e tatame igusa.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TEX_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint\textures"
os.makedirs(TEX_DIR, exist_ok=True)


def periodic_fbm(size=1024, min_freq=2, max_freq=64, falloff=1.45, seed=42, aniso_x=1.0, aniso_y=1.0):
    """Ruido fBm 100% periodico via sintese espectral 2D (rfft2/irfft2): GARANTE costura zero em qualquer repeticao."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(size) * size
    fx = np.fft.rfftfreq(size) * size
    FX, FY = np.meshgrid(fx, fy)
    R = np.sqrt((FX / max(aniso_x, 1e-4)) ** 2 + (FY / max(aniso_y, 1e-4)) ** 2)

    mask = (R >= min_freq) & (R <= max_freq)
    amp = np.zeros_like(R, dtype=np.float32)
    amp[mask] = (R[mask] ** (-falloff)).astype(np.float32)

    phase = rng.uniform(0, 2 * math.pi, size=R.shape).astype(np.float32)
    spec = amp * (np.cos(phase) + 1j * np.sin(phase))
    spec[0, 0] = 0.0
    field = np.fft.irfft2(spec, s=(size, size)).astype(np.float32)
    lo, hi = np.percentile(field, 1.5), np.percentile(field, 98.5)
    return np.clip((field - lo) / max(hi - lo, 1e-6), 0.0, 1.0)


def height_to_normal(height, strength=2.4):
    """Normal map OpenGL (+Y up, 128,128,255 = plano) periodico com roll."""
    h = height.astype(np.float32)
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5 * strength
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5 * strength
    nx = -dx
    ny = dy
    nz = np.ones_like(h)
    inv_len = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz + 1e-8)
    rgb = np.stack([
        np.clip((nx * inv_len * 0.5 + 0.5) * 255.0, 0, 255),
        np.clip((ny * inv_len * 0.5 + 0.5) * 255.0, 0, 255),
        np.clip((nz * inv_len * 0.5 + 0.5) * 255.0, 0, 255),
    ], axis=-1).astype(np.uint8)
    return Image.fromarray(rgb, mode="RGB")


def save_pbr_set(prefix, albedo_rgb, rough_01, height_01, normal_strength=2.2):
    Image.fromarray(np.clip(albedo_rgb, 0, 255).astype(np.uint8), mode="RGB").save(
        os.path.join(TEX_DIR, f"{prefix}_albedo.png"), optimize=True
    )
    Image.fromarray(np.clip(rough_01 * 255.0, 0, 255).astype(np.uint8), mode="L").save(
        os.path.join(TEX_DIR, f"{prefix}_rough.png"), optimize=True
    )
    height_to_normal(height_01, strength=normal_strength).save(
        os.path.join(TEX_DIR, f"{prefix}_normal.png"), optimize=True
    )


def mix_rgb(c0, c1, t):
    t3 = np.clip(t, 0.0, 1.0)[..., None]
    return (np.array(c0, dtype=np.float32) * (1.0 - t3) + np.array(c1, dtype=np.float32) * t3) * 255.0


def build_wood(prefix, col_a, col_b, seed, rough_min=0.58, rough_max=0.86, norm_str=2.2):
    """Madeira seamless com fibras longas em V e desgaste natural wabi-sabi (patina, micro-riscos e variacao de rugosidade)."""
    sz = 1024
    grain_macro = periodic_fbm(sz, min_freq=2, max_freq=28, falloff=1.4, seed=seed, aniso_x=4.5, aniso_y=0.55)
    grain_fine = periodic_fbm(sz, min_freq=10, max_freq=140, falloff=1.25, seed=seed + 13, aniso_x=9.0, aniso_y=0.9)
    patina = periodic_fbm(sz, min_freq=1, max_freq=12, falloff=1.6, seed=seed + 53)
    scuffs = periodic_fbm(sz, min_freq=14, max_freq=120, falloff=1.1, seed=seed + 71, aniso_x=2.2, aniso_y=0.35)
    x = np.linspace(0, 1, sz, endpoint=False)[None, :]
    rings = 0.5 + 0.5 * np.sin((x * 12.0 + grain_macro * 2.8) * 2 * math.pi)
    t = np.clip(0.42 * rings + 0.34 * grain_macro + 0.24 * grain_fine, 0.0, 1.0)
    albedo = mix_rgb(col_a, col_b, t)
    # Desgaste natural: areas mais claras/polidas pelo uso e manchas quentes de patina
    worn_lift = np.clip((patina - 0.58) * 1.4, 0.0, 0.24)
    scuff_mask = np.clip((scuffs - 0.72) * 3.0, 0.0, 1.0)
    albedo = albedo * (0.86 + 0.16 * grain_fine + 0.18 * worn_lift)[..., None]
    albedo = albedo * (1.0 - 0.10 * scuff_mask)[..., None] + np.array([155, 118, 82], dtype=np.float32) * (0.09 * scuff_mask)[..., None]
    # Roughness com contraste real de desgaste (areas gastas levemente mais acetinadas, poros mais foscos)
    rough = np.clip(rough_min + (1.0 - t) * (rough_max - rough_min) - 0.10 * worn_lift + 0.12 * scuff_mask, 0.48, 0.94)
    height = np.clip(0.50 * grain_fine + 0.38 * rings - 0.16 * scuff_mask, 0.0, 1.0)
    save_pbr_set(prefix, albedo, rough, height, normal_strength=norm_str)


def build_tatami():
    """Tatame igusa 1024x1024 seamless com patina natural de sol e pisada."""
    sz = 1024
    y = np.linspace(0, 1, sz, endpoint=False)[:, None]
    x = np.linspace(0, 1, sz, endpoint=False)[None, :]
    reed_idx = np.floor(y * 160.0).astype(np.int32)
    reed_prof = 0.5 + 0.5 * np.sin(y * 2 * math.pi * 160.0)
    cross_stitch = 0.5 + 0.5 * np.sin(x * 2 * math.pi * 40.0 + (reed_idx % 2) * math.pi)
    reed_var = periodic_fbm(sz, min_freq=2, max_freq=60, falloff=1.25, seed=101, aniso_x=0.35, aniso_y=5.5)
    sun_patina = periodic_fbm(sz, min_freq=1, max_freq=7, falloff=1.65, seed=108)
    fray = periodic_fbm(sz, min_freq=20, max_freq=160, falloff=1.15, seed=119)

    h = np.clip(0.48 * reed_prof + 0.26 * (reed_prof * cross_stitch) + 0.18 * reed_var + 0.08 * fray, 0.0, 1.0)
    tone = np.clip(0.48 * reed_var + 0.34 * sun_patina + 0.18 * reed_prof, 0.0, 1.0)
    albedo = mix_rgb((0.40, 0.34, 0.18), (0.65, 0.56, 0.33), tone)
    # Desgaste natural de uso nos sulcos e leves areas douradas pelo sol
    albedo *= (0.84 + 0.20 * h)[..., None]
    rough = np.clip(0.74 + (1.0 - h) * 0.18 - 0.08 * sun_patina, 0.65, 0.96)
    save_pbr_set("tatami", albedo, rough, h, normal_strength=3.4)


def build_plaster():
    """Parede de argila juraku 1024x1024 seamless com patina mineral, micro-fissuras e marcas de desempenadeira."""
    sz = 1024
    cloud = periodic_fbm(sz, min_freq=1, max_freq=10, falloff=1.65, seed=202)
    trowel = periodic_fbm(sz, min_freq=4, max_freq=28, falloff=1.45, seed=209, aniso_x=1.6, aniso_y=0.9)
    sand = periodic_fbm(sz, min_freq=24, max_freq=180, falloff=1.15, seed=217)
    # Veios finos de micro-fissura e manchas minerais de argila natural
    crack_field = periodic_fbm(sz, min_freq=6, max_freq=42, falloff=1.25, seed=229)
    cracks = np.clip(1.0 - np.abs(crack_field - 0.5) * 28.0, 0.0, 1.0)
    damp_patina = periodic_fbm(sz, min_freq=1, max_freq=6, falloff=1.7, seed=241)

    h = np.clip(0.42 * trowel + 0.24 * cloud + 0.34 * sand - 0.22 * cracks, 0.0, 1.0)
    tone = np.clip(0.52 * cloud + 0.28 * trowel + 0.20 * damp_patina, 0.0, 1.0)
    albedo = mix_rgb((0.45, 0.31, 0.18), (0.66, 0.49, 0.30), tone)
    albedo *= (0.91 + 0.12 * sand - 0.16 * cracks)[..., None]
    rough = np.clip(0.84 + (1.0 - sand) * 0.12 + 0.06 * cracks, 0.78, 0.98)
    save_pbr_set("plaster", albedo, rough, h, normal_strength=2.4)


def build_slubbed_linen(prefix, col_deep, col_mid, col_light, seed, wrinkle_strength=0.45):
    """Linho artesanal lavado (stone-washed slubbed linen) 1024x1024 com desgaste natural nas cristas e micro-AO nos vincos."""
    sz = 1024
    warp_slub = periodic_fbm(sz, min_freq=18, max_freq=220, falloff=1.1, seed=seed, aniso_x=10.0, aniso_y=0.45)
    weft_slub = periodic_fbm(sz, min_freq=18, max_freq=220, falloff=1.1, seed=seed + 17, aniso_x=0.45, aniso_y=10.0)
    fade_patina = periodic_fbm(sz, min_freq=1, max_freq=9, falloff=1.6, seed=seed + 61)

    idx = np.arange(sz)
    X, Y = np.meshgrid(idx, idx)
    cell = 4
    wx = np.sin((X / cell) * math.pi) ** 2
    wy = np.sin((Y / cell) * math.pi) ** 2
    checker = ((X // cell) + (Y // cell)) % 2
    weave_h = np.where(checker == 0, wx * (0.65 + 0.35 * warp_slub), wy * (0.65 + 0.35 * weft_slub)).astype(np.float32)

    crinkle_macro = periodic_fbm(sz, min_freq=2, max_freq=14, falloff=1.55, seed=seed + 31)
    crinkle_mid = periodic_fbm(sz, min_freq=8, max_freq=40, falloff=1.35, seed=seed + 47)
    crinkle = 0.62 * crinkle_macro + 0.38 * crinkle_mid

    height = np.clip(wrinkle_strength * crinkle + (1.0 - wrinkle_strength) * (0.55 * weave_h + 0.225 * warp_slub + 0.225 * weft_slub), 0.0, 1.0)

    low_t = np.clip(crinkle * 2.0, 0.0, 1.0)
    high_t = np.clip((crinkle - 0.5) * 2.0, 0.0, 1.0)
    c_lo = mix_rgb(col_deep, col_mid, low_t)
    c_hi = mix_rgb(col_mid, col_light, high_t)
    albedo = np.where((crinkle < 0.5)[..., None], c_lo, c_hi)

    # Desgaste stone-washed: leve desbotamento natural nas cristas e patina suave
    wash_fade = np.clip((fade_patina - 0.45) * 0.55 + (crinkle - 0.6) * 0.35, 0.0, 0.26)
    luma = (0.299 * albedo[..., 0] + 0.587 * albedo[..., 1] + 0.114 * albedo[..., 2])[..., None]
    albedo = albedo * (1.0 - wash_fade[..., None]) + (luma * 1.12 + 12.0) * wash_fade[..., None]

    thread_tint = 0.85 + 0.25 * (0.5 * weave_h + 0.25 * warp_slub + 0.25 * weft_slub)
    albedo = np.clip(albedo * thread_tint[..., None], 0, 255)

    rough = np.clip(0.82 + (1.0 - weave_h) * 0.14 + 0.05 * (1.0 - fade_patina), 0.78, 0.98)
    save_pbr_set(prefix, albedo, rough, height, normal_strength=3.6)


def build_washi(prefix, col_a, col_b, seed, add_flecks=True):
    sz = 1024
    base = periodic_fbm(sz, min_freq=2, max_freq=18, falloff=1.5, seed=seed)
    fine = periodic_fbm(sz, min_freq=16, max_freq=120, falloff=1.2, seed=seed + 7)
    h = np.clip(0.55 * base + 0.45 * fine, 0.0, 1.0)
    albedo = mix_rgb(col_a, col_b, h)
    img = Image.fromarray(np.clip(albedo, 0, 255).astype(np.uint8), mode="RGB")
    if add_flecks:
        draw = ImageDraw.Draw(img, "RGBA")
        rng = np.random.default_rng(seed + 99)
        for _ in range(280):
            x0 = int(rng.integers(0, sz))
            y0 = int(rng.integers(0, sz))
            ang = float(rng.uniform(0, 2 * math.pi))
            ln = float(rng.uniform(14, 48))
            x1 = int(x0 + math.cos(ang) * ln)
            y1 = int(y0 + math.sin(ang) * ln)
            alpha = int(rng.integers(24, 65))
            # Desenha com wrap periodico nas bordas
            for ox in (-sz, 0, sz):
                for oy in (-sz, 0, sz):
                    draw.line((x0 + ox, y0 + oy, x1 + ox, y1 + oy), fill=(118, 76, 38, alpha), width=int(rng.integers(1, 3)))
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    img.save(os.path.join(TEX_DIR, f"{prefix}_albedo.png"), optimize=True)
    rough = 0.84 + (1.0 - fine) * 0.10
    Image.fromarray(np.clip(rough * 255.0, 0, 255).astype(np.uint8), mode="L").save(os.path.join(TEX_DIR, f"{prefix}_rough.png"), optimize=True)
    height_to_normal(h, strength=1.5).save(os.path.join(TEX_DIR, f"{prefix}_normal.png"), optimize=True)


def build_kakejiku_scroll():
    """Pergaminho / poster japones na parede com a logo da Vercel em nanquim desgastado e textura de papel artesanal."""
    w, h = 1024, 2048
    paper_base = periodic_fbm(512, min_freq=2, max_freq=36, falloff=1.45, seed=777)
    paper_fine = periodic_fbm(512, min_freq=18, max_freq=160, falloff=1.2, seed=789)
    wear_noise = periodic_fbm(512, min_freq=6, max_freq=90, falloff=1.15, seed=799)

    def up(arr):
        return np.asarray(Image.fromarray((arr * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BICUBIC), dtype=np.float32) / 255.0

    pb = up(paper_base)
    pf = up(paper_fine)
    wn = up(wear_noise)

    # Papel kozo envelhecido com patina e manchas quentes de tempo (foxing)
    paper_rgb = mix_rgb((0.70, 0.61, 0.47), (0.85, 0.77, 0.63), np.clip(0.65 * pb + 0.35 * pf, 0, 1))
    # Vinheta sutil de envelhecimento nas bordas do papel
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xn = (xx / w - 0.5) * 2.0
    yn = (yy / h - 0.5) * 2.0
    edge_age = np.clip(1.0 - 0.22 * (xn ** 2 + yn ** 2), 0.72, 1.0)
    paper_rgb *= edge_age[..., None]

    # Brocado superior e inferior desgastado
    img = Image.fromarray(np.clip(paper_rgb, 0, 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle((0, 0, w, 330), fill=(86, 68, 48, 255))
    draw.rectangle((0, h - 330, w, h), fill=(86, 68, 48, 255))
    draw.rectangle((0, 330, w, 445), fill=(46, 48, 36, 255))
    draw.rectangle((0, h - 445, w, h - 330), fill=(46, 48, 36, 255))

    # Mascara do triangulo equilatero iconico da Vercel (▲) centralizado no pergaminho
    cx, cy = w * 0.5, h * 0.49
    side = 560.0
    tri_h = side * math.sqrt(3.0) * 0.5
    p_top = (cx, cy - tri_h * 0.55)
    p_bl = (cx - side * 0.5, cy + tri_h * 0.45)
    p_br = (cx + side * 0.5, cy + tri_h * 0.45)

    mask_img = Image.new("L", (w, h), 0)
    mdraw = ImageDraw.Draw(mask_img)
    mdraw.polygon([p_top, p_bl, p_br], fill=255)
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=3.5))
    tri_mask = np.asarray(mask_img, dtype=np.float32) / 255.0

    # Aplica desgaste autentico de xilogravura / carimbo sumi-e (falhas de fibra, arranhoes, bordas organicas)
    rng = np.random.default_rng(808)
    scratch = periodic_fbm(512, min_freq=10, max_freq=140, falloff=1.05, seed=811, aniso_x=0.35, aniso_y=6.5)
    sc = up(scratch)
    ink_alpha = np.clip((tri_mask * (1.15 - 0.52 * wn - 0.32 * sc) - 0.14) * 1.45, 0.0, 0.94)
    # Micropontos de papel aparecendo atraves da tinta desgastada
    specks = (wn > 0.78) & (pf > 0.62)
    ink_alpha = np.where(specks, ink_alpha * 0.25, ink_alpha)

    arr = np.asarray(img, dtype=np.float32)
    ink_col = mix_rgb((0.06, 0.052, 0.046), (0.15, 0.13, 0.11), pf)
    arr = arr * (1.0 - ink_alpha[..., None]) + ink_col * ink_alpha[..., None]

    # Dobras horizontais sutis de pergaminho enrolado (vincos de tempo)
    for fold_y in (640, 1020, 1410):
        dist = np.abs(yy - fold_y)
        crease = np.exp(-(dist / 5.5) ** 2) * (0.5 + 0.5 * wn)
        arr *= (1.0 - 0.14 * crease)[..., None]

    out_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    odraw = ImageDraw.Draw(out_img, "RGBA")
    # Selo vermelho hanko desgastado no canto inferior direito do triangulo
    odraw.rectangle((730, 1320, 792, 1384), fill=(156, 44, 32, 205))
    odraw.rectangle((740, 1330, 782, 1374), outline=(218, 198, 165, 165), width=4)
    # Fibras soltas do papel por cima de tudo
    for _ in range(240):
        x0 = int(rng.integers(0, w))
        y0 = int(rng.integers(330, h - 330))
        ang = float(rng.uniform(0, 2 * math.pi))
        ln = float(rng.uniform(12, 42))
        odraw.line((x0, y0, int(x0 + math.cos(ang) * ln), int(y0 + math.sin(ang) * ln)), fill=(98, 78, 52, 36), width=2)

    out_img.save(os.path.join(TEX_DIR, "kakejiku_albedo.png"), optimize=True)
    # Normal map sutil para o papel + tinta desgastada do pergaminho
    scroll_h = np.clip(0.55 * pf + 0.30 * pb + 0.15 * (1.0 - ink_alpha), 0.0, 1.0)
    height_to_normal(scroll_h, strength=1.8).save(os.path.join(TEX_DIR, "kakejiku_normal.png"), optimize=True)


def main():
    build_tatami()
    build_plaster()
    build_wood("walnut",   (0.13, 0.075, 0.040), (0.27, 0.160, 0.088), seed=301, rough_min=0.62, rough_max=0.78, norm_str=2.2)
    build_wood("hinoki",   (0.45, 0.280, 0.140), (0.64, 0.435, 0.235), seed=302, rough_min=0.64, rough_max=0.80, norm_str=1.8)
    build_wood("yakisugi", (0.042, 0.034, 0.028), (0.105, 0.084, 0.068), seed=303, rough_min=0.70, rough_max=0.86, norm_str=3.0)
    # Linho lavado ultra-realista em tons terrosos (terracota profundo, ocre queimado, linho cru e heri espresso)
    build_slubbed_linen("terracotta", (0.24, 0.078, 0.036), (0.38, 0.135, 0.062), (0.50, 0.205, 0.102), seed=401, wrinkle_strength=0.48)
    build_slubbed_linen("ochre",      (0.32, 0.165, 0.055), (0.46, 0.260, 0.095), (0.58, 0.355, 0.145), seed=402, wrinkle_strength=0.42)
    build_slubbed_linen("cream",      (0.60, 0.530, 0.425), (0.72, 0.655, 0.545), (0.83, 0.770, 0.665), seed=403, wrinkle_strength=0.38)
    build_slubbed_linen("heri",       (0.055, 0.038, 0.026), (0.085, 0.060, 0.042), (0.115, 0.082, 0.058), seed=404, wrinkle_strength=0.25)
    build_washi("washi_shoji",   (0.88, 0.80, 0.66), (0.97, 0.90, 0.77), seed=501, add_flecks=False)
    build_washi("washi_lantern", (0.94, 0.74, 0.42), (1.00, 0.90, 0.68), seed=502, add_flecks=True)
    build_kakejiku_scroll()
    print(f"[Seamless 1024px Textures OK] {len(os.listdir(TEX_DIR))} arquivos prontos em {TEX_DIR}")


if __name__ == "__main__":
    main()
