#pragma once

#include <Arduino.h>

const char DASHBOARD_HTML[] PROGMEM = R"HTML(
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Shower UART Monitor</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #07111f;
      --panel: #101d2f;
      --grid: #26364c;
      --text: #ecf3ff;
      --muted: #8ea3bf;
      --x: #ff5d73;
      --y: #47d7ac;
      --z: #62a8ff;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      padding: 24px;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: radial-gradient(circle at top, #173152 0, var(--bg) 46%);
    }

    main {
      width: min(1100px, 100%);
      margin: 0 auto;
    }

    header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
    }

    h1 {
      margin: 0;
      font-size: clamp(1.55rem, 4vw, 2.25rem);
    }

    .badge {
      padding: 7px 12px;
      border: 1px solid var(--grid);
      border-radius: 999px;
      color: var(--muted);
      background: rgba(16, 29, 47, .85);
    }

    .badge.live {
      color: #b7ffe7;
      border-color: #287b62;
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 12px;
    }

    .card, .chart-panel {
      border: 1px solid var(--grid);
      border-radius: 16px;
      background: rgba(16, 29, 47, .92);
      box-shadow: 0 18px 55px rgba(0, 0, 0, .22);
    }

    .card { padding: 16px; }

    .label {
      color: var(--muted);
      font-size: .8rem;
      letter-spacing: .09em;
      text-transform: uppercase;
    }

    .value {
      margin-top: 5px;
      font: 700 clamp(1.4rem, 4vw, 2rem) ui-monospace, SFMono-Regular, monospace;
    }

    .x { color: var(--x); }
    .y { color: var(--y); }
    .z { color: var(--z); }

    .chart-panel { padding: 14px; }

    canvas {
      display: block;
      width: 100%;
      height: 430px;
    }

    footer {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 8px;
      margin-top: 10px;
      color: var(--muted);
      font-size: .85rem;
    }

    @media (max-width: 620px) {
      body { padding: 14px; }
      .cards { grid-template-columns: 1fr; }
      canvas { height: 330px; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <div class="label">FireBeetle 2 ESP32</div>
        <h1>Live acceleration</h1>
      </div>
      <div id="status" class="badge">Waiting for UART data</div>
    </header>

    <section class="cards">
      <article class="card">
        <div class="label">X axis</div>
        <div id="x" class="value x">--</div>
      </article>
      <article class="card">
        <div class="label">Y axis</div>
        <div id="y" class="value y">--</div>
      </article>
      <article class="card">
        <div class="label">Z axis</div>
        <div id="z" class="value z">--</div>
      </article>
    </section>

    <section class="chart-panel">
      <canvas id="chart"></canvas>
    </section>

    <footer>
      <span>X, Y and Z values received over UART</span>
      <span id="samples">0 samples</span>
    </footer>
  </main>

  <script>
    const canvas = document.getElementById("chart");
    const ctx = canvas.getContext("2d");
    const statusEl = document.getElementById("status");
    const samples = [];
    const maxSamples = 300;
    let lastSequence = -1;

    function resizeCanvas() {
      const ratio = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.round(rect.width * ratio);
      canvas.height = Math.round(rect.height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      drawChart();
    }

    function drawChart() {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      const pad = { left: 48, right: 14, top: 18, bottom: 28 };
      const plotWidth = width - pad.left - pad.right;
      const plotHeight = height - pad.top - pad.bottom;

      ctx.clearRect(0, 0, width, height);
      ctx.strokeStyle = "#26364c";
      ctx.fillStyle = "#8ea3bf";
      ctx.lineWidth = 1;
      ctx.font = "12px system-ui";

      let min = -1;
      let max = 1;
      for (const sample of samples) {
        min = Math.min(min, sample.x, sample.y, sample.z);
        max = Math.max(max, sample.x, sample.y, sample.z);
      }
      const margin = Math.max((max - min) * 0.08, 0.1);
      min -= margin;
      max += margin;

      for (let i = 0; i <= 4; i++) {
        const y = pad.top + plotHeight * i / 4;
        const value = max - (max - min) * i / 4;
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(width - pad.right, y);
        ctx.stroke();
        ctx.fillText(value.toFixed(2), 4, y + 4);
      }

      const drawSeries = (key, color) => {
        if (samples.length < 2) return;
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        samples.forEach((sample, index) => {
          const x = pad.left + plotWidth * index / (maxSamples - 1);
          const y = pad.top + (max - sample[key]) * plotHeight / (max - min);
          if (index === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();
      };

      drawSeries("x", "#ff5d73");
      drawSeries("y", "#47d7ac");
      drawSeries("z", "#62a8ff");
    }

    async function update() {
      try {
        const response = await fetch("/data", { cache: "no-store" });
        if (!response.ok) throw new Error("HTTP " + response.status);
        const data = await response.json();

        statusEl.textContent = data.status === "connected"
          ? "BLE sender connected"
          : data.status === "disconnected"
            ? "BLE sender disconnected"
            : "Waiting for UART data";
        statusEl.classList.toggle("live", data.status === "connected" && data.ageMs < 2000);

        if (data.valid && data.sequence !== lastSequence) {
          lastSequence = data.sequence;
          samples.push({ x: data.x, y: data.y, z: data.z });
          if (samples.length > maxSamples) samples.shift();

          document.getElementById("x").textContent = data.x.toFixed(4);
          document.getElementById("y").textContent = data.y.toFixed(4);
          document.getElementById("z").textContent = data.z.toFixed(4);
          document.getElementById("samples").textContent =
            data.sequence + " sample" + (data.sequence === 1 ? "" : "s");
          drawChart();
        }
      } catch (error) {
        statusEl.textContent = "ESP32 connection lost";
        statusEl.classList.remove("live");
      }
    }

    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();
    setInterval(update, 100);
    update();
  </script>
</body>
</html>
)HTML";
