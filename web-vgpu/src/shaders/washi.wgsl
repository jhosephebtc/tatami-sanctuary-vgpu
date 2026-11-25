// Modulo WGSL tipado (resolvido em build-time pelo Vercel vgpu + @vgpu/wgsl-std)
import { perlin3d } from "@vgpu/wgsl-std/noise/perlin";

fn washiFiber(position: vec3f) -> f32 {
  let coarse = perlin3d(position * 14.0) * 0.5 + 0.5;
  let fine = perlin3d(position * 48.0 + vec3f(3.1, 7.4, 1.9)) * 0.5 + 0.5;
  return clamp(coarse * 0.65 + fine * 0.35, 0.0, 1.0);
}

export fn andonWashiEmission(
  position: vec3f,
  uvCoord: vec2f,
  timeSeconds: f32,
  intensity: f32
) -> vec3f {
  // Gradiente radial quente concentrado no miolo da lampada interna
  let dx = (uvCoord.x - 0.5) * 1.4;
  let dy = (uvCoord.y - 0.48) * 1.65;
  let radial = clamp(1.0 - sqrt(dx * dx + dy * dy), 0.18, 1.0);
  let fiber = washiFiber(position);

  // Micro-respiracao organica de filamento quente (iluminacao retro)
  let flicker = 1.0 + 0.018 * sin(timeSeconds * 1.7) + 0.010 * sin(timeSeconds * 3.9);

  let warmEdge = vec3f(0.82, 0.44, 0.16);
  let warmCore = vec3f(1.00, 0.84, 0.52);
  let baseTint = mix(warmEdge, warmCore, smoothstep(0.15, 0.92, radial));
  let textured = baseTint * (0.82 + 0.26 * fiber);

  return textured * intensity * flicker;
}

export fn shojiRetroGlow(
  position: vec3f,
  uvCoord: vec2f,
  timeSeconds: f32,
  warmth: f32
) -> vec3f {
  let fiber = washiFiber(position * 0.45);
  let heightGrad = mix(0.68, 1.05, clamp(uvCoord.y, 0.0, 1.0));
  let breeze = 0.96 + 0.04 * sin(timeSeconds * 0.55 + position.y * 1.4);

  let duskTint = vec3f(0.95, 0.68, 0.38);
  let afternoonTint = vec3f(1.00, 0.86, 0.62);
  let col = mix(duskTint, afternoonTint, clamp(warmth, 0.0, 1.0));

  return col * heightGrad * breeze * (0.88 + 0.16 * fiber);
}
