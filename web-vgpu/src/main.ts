import * as THREE from "three/webgpu";
import type { Node } from "three/webgpu";
import { positionLocal, time, uniform, uv } from "three/tsl";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { tslExports } from "vgpu/three";
import washiModule from "./shaders/washi.wgsl";
import { createLiquidHud } from "./liquidHud";

type WashiExports = {
  andonWashiEmission: {
    position: Node;
    uvCoord: Node;
    timeSeconds: Node | number;
    intensity: Node | number;
  };
  shojiRetroGlow: {
    position: Node;
    uvCoord: Node;
    timeSeconds: Node | number;
    warmth: Node | number;
  };
};

const { andonWashiEmission, shojiRetroGlow } = tslExports<WashiExports>(washiModule)(
  "andonWashiEmission",
  "shojiRetroGlow",
);

const statusEl = document.getElementById("status")!;
const backendLabel = document.getElementById("backend-label")!;
const noteTitleEl = document.getElementById("scene-note-title")!;
const noteBodyEl = document.getElementById("scene-note-body")!;
const wrap = document.getElementById("canvas-wrap")!;
const liquidCanvas = document.getElementById("liquid-hud-canvas") as HTMLCanvasElement;

/**
 * Generates a warm golden-hour Japanese garden equirectangular Environment texture (IBL)
 * so wood grain, stoneware ceramics, brass, and foliage receive natural ambient reflections
 * and respond dynamically to the Exterior Sun rotation control.
 */
function createWarmGardenEnvironment(): THREE.CanvasTexture {
  const w = 1024;
  const h = 512;
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d")!;

  // Rich golden-hour sky to warm earthy ground gradient
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0.0, "#3a2518");   // Zenith muted warm dusk
  grad.addColorStop(0.28, "#8c5731");  // Mid golden amber sky
  grad.addColorStop(0.47, "#e5a662");  // Warm horizon haze
  grad.addColorStop(0.51, "#5c3f26");  // Garden cedar fence & foliage horizon
  grad.addColorStop(0.68, "#2d1d12");  // Shaded garden earth & moss
  grad.addColorStop(1.0, "#170e09");   // Ground bounce
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  // Soft diffused retro sun disc + broad warm atmospheric halo on the left-west azimuth
  const sunX = w * 0.25;
  const sunY = h * 0.37;
  const halo = ctx.createRadialGradient(sunX, sunY, 8, sunX, sunY, 210);
  halo.addColorStop(0.0, "rgba(255, 240, 206, 1.0)");
  halo.addColorStop(0.18, "rgba(255, 208, 138, 0.85)");
  halo.addColorStop(0.48, "rgba(230, 148, 76, 0.32)");
  halo.addColorStop(1.0, "rgba(230, 148, 76, 0.0)");
  ctx.fillStyle = halo;
  ctx.fillRect(0, 0, w, h);

  // Subtle soft foliage silhouettes along the garden horizon
  ctx.fillStyle = "rgba(38, 42, 22, 0.38)";
  for (let i = 0; i < 36; i++) {
    const bx = (i / 36) * w + Math.sin(i * 2.1) * 18;
    const by = h * 0.50 + Math.cos(i * 1.7) * 14;
    const br = 24 + (i % 5) * 12;
    ctx.beginPath();
    ctx.arc(bx, by, br, 0, Math.PI * 2);
    ctx.fill();
  }

  const tex = new THREE.CanvasTexture(c);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

const cameraNotes: Record<string, { title: string; body: string }> = {
  hero: {
    title: "Late-Afternoon Stillness",
    body: "Warm diffused sunlight filters through translucent shoji paper, meeting the amber glow of the bedside andon lantern across weathered wood and cloth.",
  },
  lamp: {
    title: "Handcrafted Washi Andon",
    body: "Charred yakisugi plinth, twin walnut kumiko rails, and fibrous handmade washi paper animated in real time through a typed WGSL emission module.",
  },
  cloth: {
    title: "Settled Cloth & Stone-Washed Linen",
    body: "Simulated gravity folds across quilted terracotta duvet, ochre throw blanket, and flanged Oxford linen pillows resting naturally on the futon.",
  },
  garden: {
    title: "Open Shoji & Japanese Garden",
    body: "Sliding hinoki screens open onto the cedar engawa veranda, framing sunlit bamboo, mossy stones, woodland ferns, and a courtyard tree beyond.",
  },
};

async function boot() {
  const renderer = new THREE.WebGPURenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.toneMapping = THREE.NeutralToneMapping; // Khronos PBR Neutral parity
  renderer.toneMappingExposure = 0.94;
  wrap.appendChild(renderer.domElement);

  await renderer.init();
  const isWebGPU = (renderer.backend as { isWebGPUBackend?: boolean })?.isWebGPUBackend;
  backendLabel.textContent = isWebGPU
    ? "WebGPU Active · Vercel vgpu + Liquid WGSL"
    : "WebGL Fallback · Vercel vgpu";

  const scene = new THREE.Scene();

  // Procedural Golden-Hour Garden Environment (IBL + subtle visible horizon outside shoji)
  const envTex = createWarmGardenEnvironment();
  scene.environment = envTex;
  scene.background = envTex;
  scene.backgroundBlurriness = 0.14;
  scene.backgroundIntensity = 0.65;
  scene.environmentIntensity = 0.58;
  scene.fog = new THREE.FogExp2(0x1f140c, 0.022);

  const getResponsiveFov = () => (window.innerWidth / Math.max(window.innerHeight, 1) < 0.85 ? 58 : 42);
  const camera = new THREE.PerspectiveCamera(getResponsiveFov(), window.innerWidth / window.innerHeight, 0.05, 45);
  camera.position.set(0.32, 0.90, 2.52);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.055;
  controls.maxDistance = 6.8;
  controls.minDistance = 0.45;
  controls.maxPolarAngle = Math.PI * 0.495;
  controls.target.set(-0.04, 0.60, -0.58);
  controls.update();

  // Reactive TSL uniforms linked to vgpu WGSL modules
  const lampIntensityU = uniform(1.35);
  const retroWarmthU = uniform(0.78);

  const hemi = new THREE.HemisphereLight(0xf2c896, 0x341f12, 0.42);
  scene.add(hemi);

  // Bedside Andon Lantern warm amber core light
  const andonLight = new THREE.PointLight(0xff9b40, 2.5, 4.8, 1.75);
  andonLight.position.set(-0.82, 0.46, -0.94);
  andonLight.castShadow = true;
  andonLight.shadow.mapSize.set(1024, 1024);
  andonLight.shadow.bias = -0.0004;
  andonLight.shadow.normalBias = 0.024;
  scene.add(andonLight);

  const andonUpGlow = new THREE.PointLight(0xffb464, 1.15, 2.9, 1.8);
  andonUpGlow.position.set(-0.82, 0.74, -0.94);
  scene.add(andonUpGlow);

  // Rotating exterior golden-hour sun synchronized with scene.environmentRotation
  const shojiSun = new THREE.DirectionalLight(0xf8c888, 1.15);
  shojiSun.target.position.set(0.15, 0.35, -0.35);
  shojiSun.castShadow = true;
  shojiSun.shadow.mapSize.set(2048, 2048);
  shojiSun.shadow.camera.near = 0.5;
  shojiSun.shadow.camera.far = 12;
  shojiSun.shadow.camera.left = -3.2;
  shojiSun.shadow.camera.right = 3.2;
  shojiSun.shadow.camera.top = 3.2;
  shojiSun.shadow.camera.bottom = -3.2;
  shojiSun.shadow.bias = -0.0004;
  shojiSun.shadow.normalBias = 0.028;
  scene.add(shojiSun, shojiSun.target);

  const retroFill = new THREE.PointLight(0xebb87e, 0.48, 6.5, 1.6);
  retroFill.position.set(0.68, 1.95, 1.15);
  scene.add(retroFill);

  const updateExteriorLightAngle = (deg: number) => {
    const rad = THREE.MathUtils.degToRad(deg);
    const radius = 4.2;
    // Offset so 32° shines warmly from the left-front shoji/engawa opening into the room
    const sunAzimuth = rad + Math.PI * 0.92;
    shojiSun.position.set(
      Math.cos(sunAzimuth) * radius,
      1.65 + 0.55 * Math.sin(rad * 0.5),
      Math.sin(sunAzimuth) * radius,
    );
    scene.environmentRotation.y = rad;
    scene.backgroundRotation.y = rad;
  };
  updateExteriorLightAngle(32);

  // vgpu/three WGSL node materials for the glowing washi lantern and shoji screen
  const andonWashiMat = new THREE.MeshPhysicalNodeMaterial({
    color: new THREE.Color(0xf6d8a6),
    roughness: 0.88,
    metalness: 0.0,
    side: THREE.DoubleSide,
  });
  andonWashiMat.emissiveNode = andonWashiEmission({
    position: positionLocal,
    uvCoord: uv(),
    timeSeconds: time,
    intensity: lampIntensityU,
  });

  const shojiWashiMat = new THREE.MeshPhysicalNodeMaterial({
    color: new THREE.Color(0xedd6b4),
    roughness: 0.90,
    metalness: 0.0,
    side: THREE.DoubleSide,
  });
  shojiWashiMat.emissiveNode = shojiRetroGlow({
    position: positionLocal,
    uvCoord: uv(),
    timeSeconds: time,
    warmth: retroWarmthU,
  });

  // Load latest Blender GLB (1024px weathered seamless PBR + settled Cloth + Japanese plants + Vercel scroll)
  const loader = new GLTFLoader();
  const gltf = await loader.loadAsync(`/sala_japonesa.glb?v=${Date.now()}`);
  const root = gltf.scene;

  const lightsToRemove: THREE.Object3D[] = [];
  root.traverse((obj) => {
    if ((obj as THREE.Light).isLight) {
      lightsToRemove.push(obj);
      return;
    }
    if (!(obj as THREE.Mesh).isMesh) return;
    const mesh = obj as THREE.Mesh;
    mesh.castShadow = true;
    mesh.receiveShadow = true;

    const matName = (mesh.material as THREE.Material | undefined)?.name || "";
    if (matName.includes("WashiLantern") || mesh.name.startsWith("Lamp_Washi") || mesh.name === "Lamp_Bulb") {
      mesh.material = andonWashiMat;
      mesh.castShadow = false;
    } else if (matName.includes("WashiShoji") || mesh.name.endsWith("_Washi")) {
      mesh.material = shojiWashiMat;
      mesh.castShadow = false;
    } else if (mesh.name.includes("Cloth") || mesh.name.includes("Leaves") || mesh.name.includes("Fronds")) {
      if (mesh.material && !Array.isArray(mesh.material)) {
        mesh.material.side = THREE.DoubleSide;
      }
    }
  });
  lightsToRemove.forEach((l) => l.parent?.remove(l));

  scene.add(root);

  // Boot the native vgpu refractive Liquid Glass HUD shader overlay
  const isCompact = () => window.matchMedia("(max-width: 920px)").matches;
  const settingsDrawer = document.getElementById("settings-drawer")!;
  const moreMenuBtn = document.getElementById("more-menu-btn") as HTMLButtonElement;

  moreMenuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = settingsDrawer.classList.toggle("open");
    moreMenuBtn.classList.toggle("active", isOpen);
    moreMenuBtn.setAttribute("aria-expanded", String(isOpen));
  });

  window.addEventListener("pointerdown", (e) => {
    if (!isCompact() || !settingsDrawer.classList.contains("open")) return;
    const target = e.target as HTMLElement | null;
    if (target && !settingsDrawer.contains(target) && target !== moreMenuBtn) {
      settingsDrawer.classList.remove("open");
      moreMenuBtn.classList.remove("active");
      moreMenuBtn.setAttribute("aria-expanded", "false");
    }
  });

  const liquidHud = await createLiquidHud(liquidCanvas, () => {
    const compact = isCompact();
    const selector = compact
      ? "[data-liquid], [data-liquid-mobile-panel].open"
      : "[data-liquid], [data-liquid-desktop]";
    return Array.from(document.querySelectorAll<HTMLElement>(selector)).filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 4 && r.height > 4;
    });
  });

  statusEl.classList.add("hidden");

  // Camera presets
  const presets: Record<string, { pos: [number, number, number]; target: [number, number, number] }> = {
    hero:   { pos: [0.32, 0.90, 2.52],   target: [-0.04, 0.60, -0.58] },
    lamp:   { pos: [-1.02, 0.58, 0.14],  target: [-0.66, 0.43, -0.88] },
    cloth:  { pos: [1.14, 0.92, 0.96],   target: [0.18, 0.36, -0.18] },
    garden: { pos: [-0.35, 0.92, 1.05],  target: [-3.35, 0.68, 0.05] },
  };

  let animTargetPos: THREE.Vector3 | null = null;
  let animTargetLook: THREE.Vector3 | null = null;

  document.querySelectorAll<HTMLButtonElement>("#camera-buttons button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#camera-buttons button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const key = btn.dataset.cam || "hero";
      const p = presets[key];
      if (p) {
        animTargetPos = new THREE.Vector3(...p.pos);
        animTargetLook = new THREE.Vector3(...p.target);
      }
      const note = cameraNotes[key];
      if (note) {
        noteTitleEl.textContent = note.title;
        noteBodyEl.textContent = note.body;
      }
    });
  });

  controls.addEventListener("start", () => {
    animTargetPos = null;
    animTargetLook = null;
  });

  // Exterior Sun & Environment Rotation slider
  const envRotSlider = document.getElementById("env-rot-slider") as HTMLInputElement;
  const envRotVal = document.getElementById("env-rot-val")!;
  envRotSlider.addEventListener("input", () => {
    const deg = parseFloat(envRotSlider.value);
    envRotVal.textContent = `${Math.round(deg)}°`;
    updateExteriorLightAngle(deg);
  });

  // Andon Lamp Intensity slider
  const lampSlider = document.getElementById("lamp-slider") as HTMLInputElement;
  const lampVal = document.getElementById("lamp-val")!;
  lampSlider.addEventListener("input", () => {
    const v = parseFloat(lampSlider.value);
    lampVal.textContent = `${Math.round(v * 100)}%`;
    lampIntensityU.value = v;
    andonLight.intensity = 1.85 * v;
    andonUpGlow.intensity = 0.85 * v;
  });

  // Retro Daylight vs Intimate Dusk toggle
  const moodBtn = document.getElementById("mood-toggle") as HTMLButtonElement;
  let retroDaylight = true;
  moodBtn.addEventListener("click", () => {
    retroDaylight = !retroDaylight;
    if (retroDaylight) {
      moodBtn.textContent = "Retro Daylight";
      retroWarmthU.value = 0.78;
      shojiSun.intensity = 1.15;
      hemi.intensity = 0.42;
      retroFill.intensity = 0.48;
      scene.environmentIntensity = 0.58;
      scene.backgroundIntensity = 0.65;
      renderer.toneMappingExposure = 0.94;
    } else {
      moodBtn.textContent = "Intimate Dusk";
      retroWarmthU.value = 0.24;
      shojiSun.intensity = 0.28;
      hemi.intensity = 0.18;
      retroFill.intensity = 0.16;
      scene.environmentIntensity = 0.24;
      scene.backgroundIntensity = 0.22;
      renderer.toneMappingExposure = 0.88;
    }
  });

  window.addEventListener("resize", () => {
    camera.fov = getResponsiveFov();
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  renderer.setAnimationLoop(() => {
    if (animTargetPos && animTargetLook) {
      camera.position.lerp(animTargetPos, 0.08);
      controls.target.lerp(animTargetLook, 0.08);
      if (camera.position.distanceTo(animTargetPos) < 0.01) {
        animTargetPos = null;
        animTargetLook = null;
      }
    }
    controls.update();
    renderer.render(scene, camera);
    liquidHud?.render(renderer.domElement);
  });
}

boot().catch((err) => {
  console.error(err);
  statusEl.textContent = `WebGPU initialization error: ${String(err)}`;
});
