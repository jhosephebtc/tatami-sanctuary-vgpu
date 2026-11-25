// Refractive Liquid Glass Controls Shader — adapted from Vercel vgpu's `liquid-layout`
// Evaluates polynomial smooth-min SDF rounded pills with organic edge bulge, Snell bezel
// refraction of the live 3D scene behind each control, chromatic dispersion, and warm Fresnel rim.

struct LiquidParams {
  viewport: vec2f,
  pointer: vec2f,
  time: f32,
  count: f32,
  hasBackdrop: f32,
  dpr: f32,
  // Up to 8 liquid control pills: each pill = (cx, cy, halfW, halfH) + (radius, energy, hover, pad)
  rects: array<vec4f, 8>,
  pillData: array<vec4f, 8>,
}

@group(0) @binding(0) var backdropTex: texture_2d<f32>;
@group(0) @binding(1) var samp: sampler;
@group(0) @binding(2) var<uniform> params: LiquidParams;

fn sdRoundRect(p: vec2f, half: vec2f, corner: f32) -> f32 {
  let r = min(corner, min(half.x, half.y));
  let q = abs(p) - half + r;
  return length(max(q, vec2f(0.0))) + min(max(q.x, q.y), 0.0) - r;
}

fn bulge(v: vec2f, t: f32, seed: f32, amp: f32) -> vec2f {
  let side = smoothstep(vec2f(-0.3), vec2f(0.3), v);
  let offsets = vec4f(0.0, 2.1, 4.2, 5.3);
  let edges = amp * (0.58
    + 0.28 * sin(t * vec4f(0.65, 0.72, 0.58, 0.81) + seed + offsets)
    + 0.14 * sin(t * vec4f(1.21, 1.04, 1.38, 1.15) + 1.6 * seed + offsets));
  let ex = mix(edges.x, edges.y, side.x) * max(0.0, 1.0 - v.y * v.y);
  let ey = mix(edges.z, edges.w, side.y) * max(0.0, 1.0 - v.x * v.x);
  return vec2f(ex, ey);
}

struct FieldSample {
  d: f32,
  energy: f32,
  hover: f32,
}

fn evalField(p: vec2f) -> FieldSample {
  let n = min(u32(params.count + 0.5), 8u);
  var accD = 512.0;
  var accEnergy = 0.0;
  var accHover = 0.0;
  let blendK = 16.0;

  for (var i = 0u; i < n; i++) {
    let rect = params.rects[i];
    let m = params.pillData[i];
    var half = rect.zw;
    let local = p - rect.xy;
    let amp = 0.9 + 1.6 * m.z; // subtle breathing + stronger liquid wobble on hover
    let normLocal = clamp(local / max(half, vec2f(1.0)), vec2f(-1.0), vec2f(1.0));
    half += bulge(normLocal, params.time, f32(i) * 2.39996, amp);
    let d = sdRoundRect(local, half, m.x);

    // Polynomial smooth-min so adjacent pills softly attract like mercury/glass
    let h = clamp(0.5 + 0.5 * (d - accD) / blendK, 0.0, 1.0);
    accD = mix(d, accD, h) - blendK * h * (1.0 - h);
    accEnergy = mix(m.y, accEnergy, h);
    accHover = mix(m.z, accHover, h);
  }
  return FieldSample(accD, accEnergy, accHover);
}

fn sampleScene(uv: vec2f) -> vec3f {
  let clamped = clamp(uv, vec2f(0.001), vec2f(0.999));
  return textureSampleLevel(backdropTex, samp, clamped, 0.0).rgb;
}

@fragment fn fs_main(@location(0) uv: vec2f) -> @location(0) vec4f {
  let p = uv * params.viewport;
  let f = evalField(p);

  // Soft liquid shadow outside the glass pill
  if (f.d > 26.0) {
    return vec4f(0.0, 0.0, 0.0, 0.0);
  }

  let shadowSample = evalField(p - vec2f(0.0, 8.0));
  let shadowAlpha = select(0.0, exp(-shadowSample.d / 14.0) * 0.24, shadowSample.d > 0.0);

  // Anti-aliased pill coverage
  let cov = 1.0 - smoothstep(-1.0, 1.0, f.d);
  if (cov <= 0.001) {
    return vec4f(0.0, 0.0, 0.0, shadowAlpha);
  }

  // Screen-space SDF gradient for liquid glass bezel normal
  let eps = 2.0;
  let gx = evalField(p + vec2f(eps, 0.0)).d - evalField(p - vec2f(eps, 0.0)).d;
  let gy = evalField(p + vec2f(0.0, eps)).d - evalField(p - vec2f(0.0, eps)).d;
  let grad = vec2f(gx, gy);
  let glen = max(length(grad), 1e-4);
  let normal = grad / glen;

  // Bezel lens profile (rounded liquid edge bending light inward like liquid-layout)
  let depth = max(-f.d, 0.0);
  let lensWidth = 18.0;
  let t = clamp(depth / lensWidth, 0.0, 1.0);
  let bend = pow(1.0 - t, 2.2);
  let refractPx = (14.0 + 6.0 * f.hover) * bend;
  let disp = 0.22; // warm optical chromatic dispersion across R/G/B

  var refracted = vec3f(0.14, 0.09, 0.06);
  if (params.hasBackdrop > 0.5) {
    let dir = -normal / max(params.viewport, vec2f(1.0));
    let uvR = uv + dir * refractPx * (1.0 + disp);
    let uvG = uv + dir * refractPx;
    let uvB = uv + dir * refractPx * (1.0 - disp);

    // Subtle 5-tap frosted softness inside the flat body of the glass
    let blurStep = vec2f(2.2, 2.2) / max(params.viewport, vec2f(1.0));
    let r = (sampleScene(uvR).r * 0.5
      + sampleScene(uvR + vec2f(blurStep.x, 0.0)).r * 0.125
      + sampleScene(uvR - vec2f(blurStep.x, 0.0)).r * 0.125
      + sampleScene(uvR + vec2f(0.0, blurStep.y)).r * 0.125
      + sampleScene(uvR - vec2f(0.0, blurStep.y)).r * 0.125);
    let g = (sampleScene(uvG).g * 0.5
      + sampleScene(uvG + vec2f(blurStep.x, 0.0)).g * 0.125
      + sampleScene(uvG - vec2f(blurStep.x, 0.0)).g * 0.125
      + sampleScene(uvG + vec2f(0.0, blurStep.y)).g * 0.125
      + sampleScene(uvG - vec2f(0.0, blurStep.y)).g * 0.125);
    let b = (sampleScene(uvB).b * 0.5
      + sampleScene(uvB + vec2f(blurStep.x, 0.0)).b * 0.125
      + sampleScene(uvB - vec2f(blurStep.x, 0.0)).b * 0.125
      + sampleScene(uvB + vec2f(0.0, blurStep.y)).b * 0.125
      + sampleScene(uvB - vec2f(0.0, blurStep.y)).b * 0.125);
    refracted = vec3f(r, g, b);
  }

  // Smoked earthy glass tint + warm optical Fresnel sheen (no hard CSS border!)
  let glassTint = vec3f(0.11, 0.075, 0.050);
  var color = mix(refracted * 0.86, glassTint, 0.24);

  // Pointer-reactive specular caustic along the curved bezel
  let toPtr = params.pointer - p;
  let ptrDist = length(toPtr);
  let ptrDir = toPtr / max(ptrDist, 1.0);
  let ptrLight = pow(max(dot(normal, ptrDir), 0.0), 3.0) * exp(-ptrDist / 260.0);

  // Key warm ambient directional sheen (upper-left) + subtle far-edge bounce
  let keyDir = normalize(vec2f(-0.65, -0.76));
  let keySpec = pow(max(dot(normal, keyDir), 0.0), 2.5);
  let rimBand = pow(1.0 - clamp(depth / 7.5, 0.0, 1.0), 3.2);
  let softBevel = pow(1.0 - clamp(depth / 18.0, 0.0, 1.0), 2.0);

  let warmSpec = vec3f(1.00, 0.83, 0.58);
  let emberAccent = vec3f(0.95, 0.60, 0.28);

  color += warmSpec * rimBand * (0.11 + 0.22 * keySpec + 0.30 * ptrLight);
  color += warmSpec * softBevel * (0.04 + 0.07 * f.hover);
  color += emberAccent * (0.04 * f.energy + 0.08 * f.hover * softBevel);

  // Premultiplied alpha output for clean compositing over the 3D scene
  let outAlpha = clamp(cov * 0.96 + shadowAlpha * (1.0 - cov), 0.0, 1.0);
  let outRgb = color * cov;
  return vec4f(outRgb, outAlpha);
}
