/**
 * Grava um tour interativo de exatamente 12.0 segundos em 1280x720 interagindo ao vivo com:
 * - Exterior Sun (giro do Environment IBL e sol externo)
 * - Andon Lantern + Andon Glow (intensidade da luminaria)
 * - Retro Daylight <-> Intimate Dusk
 * - Woven Linen (detalhe do Cloth) e Engawa & Garden (jardim japones Poly Haven)
 * Captura frames via CDP Page.captureScreenshot e envia em pipe direto para o ffmpeg do sistema (MP4 H.264).
 */
import fs from "node:fs";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require(
  "C:/Users/Administrador/.gemini/config/plugins/arquiteto/skills/arquiteto/node_modules/playwright",
);

const PROJ_DIR = "C:/Users/Administrador/.gemini/antigravity/scratch/sala-japonesa-blueprint";
const OUT_DIR = path.join(PROJ_DIR, "renders");
const FINAL_MP4 = path.join(OUT_DIR, "tour_sala_japonesa_12s.mp4");
const CONTACT_PNG = path.join(OUT_DIR, "tour_contact_sheet.png");
const URL = "http://localhost:4173/";

const FPS = 25;
const DURATION_S = 12;
const TOTAL_FRAMES = FPS * DURATION_S; // 300 frames = 12.00s exatos

fs.mkdirSync(OUT_DIR, { recursive: true });

const easeInOut = (t) => {
  const c = Math.max(0, Math.min(1, t));
  return c < 0.5 ? 4 * c * c * c : 1 - Math.pow(-2 * c + 2, 3) / 2;
};

const lerp = (a, b, t) => a + (b - a) * easeInOut(t);

async function launchWebGpuBrowser() {
  const args = [
    "--enable-unsafe-webgpu",
    "--enable-features=Vulkan,WebGPU",
    "--ignore-gpu-blocklist",
    "--window-position=-2000,0",
  ];
  for (const channel of ["chrome", "msedge"]) {
    try {
      const b = await chromium.launch({ headless: false, channel, args });
      console.log(`[Tour] Browser iniciado com canal: ${channel}`);
      return b;
    } catch {
      // tenta proximo
    }
  }
  return chromium.launch({ headless: false, args });
}

async function getCenters(page) {
  const selectors = {
    hero: 'button[data-cam="hero"]',
    lamp: 'button[data-cam="lamp"]',
    cloth: 'button[data-cam="cloth"]',
    garden: 'button[data-cam="garden"]',
    mood: "#mood-toggle",
    envSlider: "#env-rot-slider",
    lampSlider: "#lamp-slider",
  };
  const out = {};
  for (const [k, sel] of Object.entries(selectors)) {
    const box = await page.locator(sel).boundingBox();
    if (!box) throw new Error(`Elemento nao encontrado: ${sel}`);
    out[k] = { x: box.x + box.width * 0.5, y: box.y + box.height * 0.5, box };
  }
  return out;
}

function sliderX(info, min, max, val) {
  return info.box.x + ((val - min) / (max - min)) * info.box.width;
}

async function setSlider(page, sel, val) {
  await page.evaluate(
    ({ s, v }) => {
      const el = document.querySelector(s);
      if (el) {
        el.value = String(v);
        el.dispatchEvent(new Event("input", { bubbles: true }));
      }
    },
    { s: sel, v: val },
  );
}

async function main() {
  const browser = await launchWebGpuBrowser();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  const cdp = await context.newCDPSession(page);

  await page.goto(URL, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(
    () => {
      const s = document.getElementById("status");
      return s && s.classList.contains("hidden");
    },
    { timeout: 45000 },
  );

  // Cursor virtual elegante (halo ambar sutil)
  await page.evaluate(() => {
    const dot = document.createElement("div");
    dot.id = "tour-cursor";
    Object.assign(dot.style, {
      position: "fixed",
      left: "640px",
      top: "360px",
      width: "20px",
      height: "20px",
      borderRadius: "50%",
      transform: "translate(-50%, -50%)",
      background:
        "radial-gradient(circle, rgba(255,232,190,0.95) 0%, rgba(234,176,106,0.38) 52%, rgba(234,176,106,0) 100%)",
      boxShadow: "0 0 18px rgba(234,176,106,0.78)",
      pointerEvents: "none",
      zIndex: "9999",
    });
    document.body.appendChild(dot);
    window.addEventListener("pointermove", (e) => {
      dot.style.left = `${e.clientX}px`;
      dot.style.top = `${e.clientY}px`;
    });
  });

  // Aguarda 0.8s para shaders + WebGPU estabilizarem
  await new Promise((r) => setTimeout(r, 800));
  const ui = await getCenters(page);

  // Abre ffmpeg recebendo JPEG frames por stdin -> MP4 H.264 30fps suave de 12.0s
  const ff = spawn(
    "ffmpeg",
    [
      "-y",
      "-f", "image2pipe",
      "-vcodec", "mjpeg",
      "-framerate", String(FPS),
      "-i", "-",
      "-vf", "fps=30",
      "-c:v", "libx264",
      "-preset", "medium",
      "-crf", "17",
      "-pix_fmt", "yuv420p",
      "-movflags", "+faststart",
      FINAL_MP4,
    ],
    { stdio: ["pipe", "inherit", "inherit"] },
  );

  const ffDone = new Promise((resolve, reject) => {
    ff.on("error", reject);
    ff.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exited ${code}`))));
  });

  // Eventos discretos de clique em timestamps exatos (em segundos)
  const triggered = new Set();
  const triggerOnce = async (id, fn) => {
    if (triggered.has(id)) return;
    triggered.add(id);
    await fn();
  };

  console.log(`[Tour] Capturando ${TOTAL_FRAMES} frames (${DURATION_S}s @ ${FPS}fps) via WebGPU + ffmpeg...`);

  for (let f = 0; f < TOTAL_FRAMES; f++) {
    const t = f / FPS; // 0.00 -> 11.96s
    let cx = 640;
    let cy = 360;

    if (t < 1.0) {
      // 0.0 - 1.0s: Estabelecimento Hero + cursor desliza ate Exterior Sun
      const p = t / 1.0;
      const sx = sliderX(ui.envSlider, 0, 360, 32);
      cx = lerp(640, sx, p);
      cy = lerp(360, ui.envSlider.y, p);
    } else if (t < 3.6) {
      // 1.0 - 3.6s: Gira Exterior Sun 32° -> 155° -> 42° (sombras varrendo o quarto!)
      let deg;
      if (t < 2.6) {
        deg = lerp(32, 155, (t - 1.0) / 1.6);
      } else {
        deg = lerp(155, 42, (t - 2.6) / 1.0);
      }
      cx = sliderX(ui.envSlider, 0, 360, deg);
      cy = ui.envSlider.y;
      await setSlider(page, "#env-rot-slider", deg);
    } else if (t < 4.3) {
      // 3.6 - 4.3s: Desliza ate "Andon Lantern" e clica em t=4.1s
      const p = (t - 3.6) / 0.5;
      cx = lerp(sliderX(ui.envSlider, 0, 360, 42), ui.lamp.x, p);
      cy = lerp(ui.envSlider.y, ui.lamp.y, p);
      if (t >= 4.1) {
        await triggerOnce("click_lamp", () => page.click('button[data-cam="lamp"]'));
      }
    } else if (t < 6.0) {
      // 4.3 - 6.0s: Desliza ate Andon Glow e sobe 135% -> 200%
      if (t < 4.8) {
        const p = (t - 4.3) / 0.5;
        cx = lerp(ui.lamp.x, sliderX(ui.lampSlider, 0.2, 2.2, 1.35), p);
        cy = lerp(ui.lamp.y, ui.lampSlider.y, p);
      } else {
        const v = lerp(1.35, 2.0, (t - 4.8) / 1.2);
        cx = sliderX(ui.lampSlider, 0.2, 2.2, v);
        cy = ui.lampSlider.y;
        await setSlider(page, "#lamp-slider", v);
      }
    } else if (t < 7.4) {
      // 6.0 - 7.4s: Vai ate Retro Daylight -> clica para Intimate Dusk (t=6.45) + desliza ate Woven Linen
      if (t < 6.5) {
        const p = (t - 6.0) / 0.45;
        cx = lerp(sliderX(ui.lampSlider, 0.2, 2.2, 2.0), ui.mood.x, p);
        cy = lerp(ui.lampSlider.y, ui.mood.y, p);
        if (t >= 6.45) {
          await triggerOnce("click_dusk", () => page.click("#mood-toggle"));
        }
      } else {
        const p = (t - 6.5) / 0.6;
        cx = lerp(ui.mood.x, ui.cloth.x, p);
        cy = lerp(ui.mood.y, ui.cloth.y, p);
        if (t >= 7.1) {
          await triggerOnce("click_cloth", () => page.click('button[data-cam="cloth"]'));
        }
      }
    } else if (t < 9.6) {
      // 7.4 - 9.6s: Curte o Cloth sob Intimate Dusk, volta para Retro Daylight (8.3) e clica Engawa & Garden (8.85)
      if (t < 8.35) {
        const p = Math.max(0, (t - 7.8) / 0.5);
        cx = lerp(ui.cloth.x, ui.mood.x, p);
        cy = lerp(ui.cloth.y, ui.mood.y, p);
        if (t >= 8.3) {
          await triggerOnce("click_day", () => page.click("#mood-toggle"));
        }
      } else {
        const p = (t - 8.35) / 0.5;
        cx = lerp(ui.mood.x, ui.garden.x, p);
        cy = lerp(ui.mood.y, ui.garden.y, p);
        if (t >= 8.85) {
          await triggerOnce("click_garden", () => page.click('button[data-cam="garden"]'));
        }
      }
    } else {
      // 9.6 - 12.0s: Retorna a vista Hero "Sanctuary" (10.3) e descansa cursor suavemente
      if (t < 10.35) {
        const p = Math.max(0, (t - 9.85) / 0.45);
        cx = lerp(ui.garden.x, ui.hero.x, p);
        cy = lerp(ui.garden.y, ui.hero.y, p);
        if (t >= 10.3) {
          await triggerOnce("click_hero", () => page.click('button[data-cam="hero"]'));
        }
      } else {
        const p = (t - 10.35) / 1.0;
        cx = lerp(ui.hero.x, 640, p);
        cy = lerp(ui.hero.y, 440, p);
      }
    }

    await page.mouse.move(cx, cy);
    // Deixa o WebGPU renderizar 2 rAFs suaves para a interpolacao da camera andar no ritmo real
    await page.evaluate(
      () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))),
    );

    const { data } = await cdp.send("Page.captureScreenshot", {
      format: "jpeg",
      quality: 94,
    });
    const buf = Buffer.from(data, "base64");
    if (!ff.stdin.write(buf)) {
      await new Promise((r) => ff.stdin.once("drain", r));
    }
  }

  ff.stdin.end();
  await ffDone;
  await context.close();
  await browser.close();

  // Gera folha de contato 3x2 (t = 1, 3, 5, 7, 9, 11s) para auditoria visual
  execFileSync(
    "ffmpeg",
    [
      "-y",
      "-i", FINAL_MP4,
      "-vf", "fps=0.5,scale=640:360,tile=3x2",
      "-frames:v", "1",
      CONTACT_PNG,
    ],
    { stdio: "inherit" },
  );

  const mb = (fs.statSync(FINAL_MP4).size / (1024 * 1024)).toFixed(2);
  console.log(`[Tour MP4 OK] ${FINAL_MP4} (${mb} MB, 12.0s, 1280x720 30fps) | Contact sheet: ${CONTACT_PNG}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
