"use client";

import { useEffect, useRef } from "react";

interface Blob {
  x: number;
  y: number;
  r: number;
  vx: number;
  vy: number;
  phase: number;
  speed: number;
  color: [number, number, number];
  alpha: number;
}

const PALETTE: [number, number, number][] = [
  [240, 212, 198],
  [224, 181, 164],
  [234, 200, 186],
  [247, 228, 219],
  [184, 137, 122],
  [160, 112, 96],
  [250, 220, 205],
  [200, 160, 145],
  [220, 185, 170],
];

const BLOB_COUNT = 9;

export default function FluidCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w = (canvas.width = window.innerWidth);
    let h = (canvas.height = window.innerHeight);

    const handleResize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    const blobs: Blob[] = [];
    for (let i = 0; i < BLOB_COUNT; i++) {
      const c = PALETTE[i % PALETTE.length];
      blobs.push({
        x: Math.random() * w,
        y: Math.random() * h,
        r: 250 + Math.random() * 300,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        phase: Math.random() * Math.PI * 2,
        speed: 0.004 + Math.random() * 0.006,
        color: c,
        alpha: 0.22 + Math.random() * 0.15,
      });
    }

    let rafId: number;

    function draw(t: number) {
      ctx!.clearRect(0, 0, w, h);
      ctx!.fillStyle = "#d5a18e";
      ctx!.fillRect(0, 0, w, h);

      for (const b of blobs) {
        b.phase += b.speed;
        const pulse = Math.sin(b.phase) * 0.35 + 1;
        const r = b.r * pulse;

        b.x += b.vx + Math.sin(t * 0.0004 + b.phase) * 0.7;
        b.y += b.vy + Math.cos(t * 0.0005 + b.phase) * 0.6;

        if (b.x < -r) b.x = w + r;
        if (b.x > w + r) b.x = -r;
        if (b.y < -r) b.y = h + r;
        if (b.y > h + r) b.y = -r;

        const grad = ctx!.createRadialGradient(b.x, b.y, 0, b.x, b.y, r);
        grad.addColorStop(0, `rgba(${b.color[0]},${b.color[1]},${b.color[2]},${b.alpha})`);
        grad.addColorStop(0.5, `rgba(${b.color[0]},${b.color[1]},${b.color[2]},${b.alpha * 0.4})`);
        grad.addColorStop(1, `rgba(${b.color[0]},${b.color[1]},${b.color[2]},0)`);
        ctx!.fillStyle = grad;
        ctx!.fillRect(b.x - r, b.y - r, r * 2, r * 2);
      }

      rafId = requestAnimationFrame(draw);
    }

    rafId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return <canvas ref={canvasRef} id="fluid-canvas" />;
}
