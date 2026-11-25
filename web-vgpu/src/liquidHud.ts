import { clock, effect, frame, init, surface, texture } from "vgpu";
import type { Gpu, Surface, Texture } from "vgpu";
import liquidHudShader from "./shaders/liquid_hud.wgsl";

const MAX_PILLS = 8;

export interface LiquidHudController {
  render(sceneCanvas: HTMLCanvasElement): void;
  dispose(): void;
}

export async function createLiquidHud(
  overlayCanvas: HTMLCanvasElement,
  pillElements: () => HTMLElement[],
): Promise<LiquidHudController | null> {
  try {
    const gpu: Gpu = await init();
    const hudSurface: Surface = surface(gpu, overlayCanvas, {
      alphaMode: "premultiplied",
      clearColor: [0, 0, 0, 0],
      dpr: [1, 2],
    });

    const nativeSampler = gpu.gpu.createSampler({
      magFilter: "linear",
      minFilter: "linear",
      addressModeU: "clamp-to-edge",
      addressModeV: "clamp-to-edge",
    });

    let texW = Math.max(2, overlayCanvas.width || window.innerWidth);
    let texH = Math.max(2, overlayCanvas.height || window.innerHeight);

    const makeBackdropTex = (w: number, h: number): Texture =>
      texture(gpu, {
        kind: "2d",
        size: [w, h],
        format: "rgba8unorm",
        usage: ["copy_dst", "texture_binding", "render_attachment"],
        label: "liquid-hud-backdrop",
      });

    let backdropTex = makeBackdropTex(texW, texH);

    const emptyRects = Array.from({ length: MAX_PILLS }, () => [0, 0, 0, 0] as [number, number, number, number]);
    const emptyMeta = Array.from({ length: MAX_PILLS }, () => [20, 0, 0, 0] as [number, number, number, number]);

    const liquidEffect = effect(gpu, liquidHudShader, {
      set: {
        backdropTex,
        samp: nativeSampler,
        params: {
          viewport: [window.innerWidth, window.innerHeight],
          pointer: [window.innerWidth * 0.5, window.innerHeight * 0.5],
          time: 0,
          count: 0,
          hasBackdrop: 0,
          dpr: window.devicePixelRatio || 1,
          rects: emptyRects,
          pillData: emptyMeta,
        },
      },
    });

    let pointerX = window.innerWidth * 0.5;
    let pointerY = window.innerHeight * 0.5;
    const hoverStates = new WeakMap<HTMLElement, number>();
    const hoveredSet = new WeakSet<HTMLElement>();

    const onPointerMove = (e: PointerEvent) => {
      pointerX = e.clientX;
      pointerY = e.clientY;
    };
    window.addEventListener("pointermove", onPointerMove, { passive: true });

    const bindHoverListeners = () => {
      for (const el of pillElements()) {
        if (el.dataset.liquidBound) continue;
        el.dataset.liquidBound = "1";
        el.addEventListener("pointerenter", () => hoveredSet.add(el));
        el.addEventListener("pointerleave", () => hoveredSet.delete(el));
      }
    };
    bindHoverListeners();

    const hudClock = clock(gpu);

    return {
      render(sceneCanvas: HTMLCanvasElement) {
        if (gpu.disposed) return;
        bindHoverListeners();

        const cw = sceneCanvas.width;
        const ch = sceneCanvas.height;
        let hasBackdrop = 0;

        if (cw > 0 && ch > 0) {
          if (cw !== texW || ch !== texH) {
            backdropTex.destroy();
            texW = cw;
            texH = ch;
            backdropTex = makeBackdropTex(texW, texH);
            liquidEffect.set({ backdropTex });
          }
          try {
            gpu.gpu.queue.copyExternalImageToTexture(
              { source: sceneCanvas },
              { texture: backdropTex.gpu },
              [texW, texH],
            );
            hasBackdrop = 1;
          } catch {
            hasBackdrop = 0;
          }
        }

        const els = pillElements().slice(0, MAX_PILLS);
        const rects: [number, number, number, number][] = [];
        const meta: [number, number, number, number][] = [];

        for (let i = 0; i < MAX_PILLS; i++) {
          const el = els[i];
          if (el) {
            const r = el.getBoundingClientRect();
            const isActive = el.classList.contains("active") || el.dataset.energy === "1" ? 1 : 0;
            const prevH = hoverStates.get(el) ?? 0;
            const targetH = hoveredSet.has(el) ? 1 : 0;
            const nextH = prevH + (targetH - prevH) * 0.14;
            hoverStates.set(el, nextH);

            rects.push([
              r.left + r.width * 0.5,
              r.top + r.height * 0.5,
              Math.max(1, r.width * 0.5),
              Math.max(1, r.height * 0.5),
            ]);
            meta.push([Math.min(26, r.height * 0.5), isActive, nextH, 0]);
          } else {
            rects.push([-200, -200, 1, 1]);
            meta.push([1, 0, 0, 0]);
          }
        }

        liquidEffect.set({
          params: {
            viewport: [window.innerWidth, window.innerHeight],
            pointer: [pointerX, pointerY],
            time: hudClock.time,
            count: els.length,
            hasBackdrop,
            dpr: hudSurface.dpr,
            rects,
            pillData: meta,
          },
        });

        frame(gpu, (f) => {
          f.pass(hudSurface, liquidEffect);
        });
      },
      dispose() {
        window.removeEventListener("pointermove", onPointerMove);
        backdropTex.destroy();
        hudSurface.dispose();
        gpu.dispose();
      },
    };
  } catch (err) {
    console.warn("Liquid HUD overlay unavailable, continuing with 3D scene:", err);
    return null;
  }
}
