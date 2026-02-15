/**
 * Rally — mock frontend, dummy data only.
 * SPA with canvas fluid animation.
 */

/* ── Fluid canvas animation ─────────────────────────────── */

function initFluidCanvas() {
  const canvas = document.getElementById("fluid-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let w, h;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  // Blobs that drift and pulse — larger, brighter, more visible
  const blobs = [];
  const BLOB_COUNT = 9;

  const palette = [
    [240, 212, 198], // accent light
    [224, 181, 164], // peach-light
    [234, 200, 186], // peach-pale
    [247, 228, 219], // accent-soft highlight
    [184, 137, 122], // peach-mid warm
    [160, 112, 96],  // peach-dark
    [250, 220, 205], // warm glow
    [200, 160, 145], // midtone
    [220, 185, 170], // rosy
  ];

  for (let i = 0; i < BLOB_COUNT; i++) {
    const c = palette[i % palette.length];
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

  function draw(t) {
    ctx.clearRect(0, 0, w, h);

    // Peach base matching #D5A18E
    ctx.fillStyle = "#d5a18e";
    ctx.fillRect(0, 0, w, h);

    for (const b of blobs) {
      b.phase += b.speed;
      const pulse = Math.sin(b.phase) * 0.35 + 1;
      const r = b.r * pulse;

      // Visible drift
      b.x += b.vx + Math.sin(t * 0.0004 + b.phase) * 0.7;
      b.y += b.vy + Math.cos(t * 0.0005 + b.phase) * 0.6;

      // Wrap around edges with padding
      if (b.x < -r) b.x = w + r;
      if (b.x > w + r) b.x = -r;
      if (b.y < -r) b.y = h + r;
      if (b.y > h + r) b.y = -r;

      const grad = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, r);
      grad.addColorStop(0, `rgba(${b.color[0]}, ${b.color[1]}, ${b.color[2]}, ${b.alpha})`);
      grad.addColorStop(0.5, `rgba(${b.color[0]}, ${b.color[1]}, ${b.color[2]}, ${b.alpha * 0.4})`);
      grad.addColorStop(1, `rgba(${b.color[0]}, ${b.color[1]}, ${b.color[2]}, 0)`);
      ctx.fillStyle = grad;
      ctx.fillRect(b.x - r, b.y - r, r * 2, r * 2);
    }

    requestAnimationFrame(draw);
  }

  requestAnimationFrame(draw);
}

/* ── SPA routing ─────────────────────────────────────────── */

const PAGES = ["home", "dashboard"];
const TRANSITION_MS = 280;

function getPageFromHash() {
  const hash = (window.location.hash || "#home").slice(1);
  return PAGES.includes(hash) ? hash : "home";
}

function setActivePage(page) {
  const links = document.querySelectorAll(".nav-link");
  const current = document.querySelector(".page-view.active");
  const next = document.getElementById(`page-${page}`);
  if (!next) return;

  links.forEach((a) => a.classList.toggle("active", a.dataset.page === page));
  window.location.hash = page;
  document.title = page === "home" ? "Rally" : `${page.charAt(0).toUpperCase() + page.slice(1)} — Rally`;

  // Show/hide header
  const header = document.getElementById("header-bar");
  if (header) {
    header.classList.toggle("hidden", page === "home");
  }

  // Update date when header is visible
  if (page !== "home") setHeaderDate();

  if (current && current !== next) {
    current.classList.add("leaving");
    current.classList.remove("active");
    setTimeout(() => {
      current.classList.remove("leaving");
      next.classList.add("active");
      renderPage(page);
    }, TRANSITION_MS);
  } else if (!current) {
    next.classList.add("active");
    renderPage(page);
  }
}

function renderPage(page) {
  if (page === "dashboard") {
    renderDashboard();
    initDashTabs();
  }
}

function setupRouter() {
  document.querySelectorAll("a[href^='#']").forEach((a) => {
    a.addEventListener("click", (e) => {
      const page = (a.getAttribute("href") || "#home").slice(1);
      if (PAGES.includes(page)) {
        e.preventDefault();
        if (document.querySelector(".page-view.active")?.id !== `page-${page}`) {
          setActivePage(page);
        }
      }
    });
  });

  window.addEventListener("hashchange", () => setActivePage(getPageFromHash()));
  setActivePage(getPageFromHash());
}

/* ── Helpers ──────────────────────────────────────────────── */

function setHeaderDate() {
  const el = document.getElementById("header-date");
  if (el) {
    const d = new Date();
    el.textContent = d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  }
}

function formatTimeRange(start, end) {
  const s = new Date(start);
  const e = new Date(end);
  return (
    s.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" }) +
    " – " +
    e.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
  );
}

function formatDayHeader(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
}

function formatEntryDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/* ── Dashboard tabs ───────────────────────────────────────── */

function initDashTabs() {
  const tabs = document.querySelectorAll(".dash-tab");
  const panels = document.querySelectorAll(".dash-panel");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;

      tabs.forEach((t) => t.classList.toggle("active", t === tab));
      panels.forEach((p) => {
        p.classList.toggle("active", p.id === `panel-${target}`);
      });

      // Render content on first view
      if (target === "calendar") renderCalendarInto(document.getElementById("dashboard-calendar"));
      if (target === "entries") renderEntriesInto(document.getElementById("dashboard-entries"));
    });
  });
}

function renderDashboard() {
  // Render initial tab (calendar)
  renderCalendarInto(document.getElementById("dashboard-calendar"));
}

function renderCalendarInto(el) {
  if (!el) return;

  const meetings = [...DUMMY_DATA.meetings].sort(
    (a, b) => new Date(a.start) - new Date(b.start)
  );

  const byDay = {};
  for (const m of meetings) {
    const key = m.start.slice(0, 10);
    if (!byDay[key]) byDay[key] = [];
    byDay[key].push(m);
  }

  const days = Object.keys(byDay).sort();

  el.innerHTML = days
    .map(
      (day) => `
    <div class="calendar-day-group">
      <div class="day-header">${formatDayHeader(day + "T12:00:00")}</div>
      <div class="day-events">
        ${byDay[day]
          .map(
            (m) => `
          <article class="calendar-event">
            <h3 class="event-title">${m.title}</h3>
            <div class="event-time">${formatTimeRange(m.start, m.end)}</div>
            <div class="event-attendees">
              ${m.attendees.map((a) => `<span>${a}</span>`).join("")}
            </div>
          </article>
        `
          )
          .join("")}
      </div>
    </div>
  `
    )
    .join("");
}


function renderEntriesInto(el) {
  if (!el) return;

  const entries = [...getEntries()].sort(
    (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)
  );

  const byCategory = {};
  for (const e of entries) {
    if (!byCategory[e.category]) byCategory[e.category] = [];
    byCategory[e.category].push(e);
  }

  const order = ["brand", "policy", "preference", "fact"];
  const categories = order.filter((c) => byCategory[c]);

  el.innerHTML = categories
    .map(
      (cat) => `
    <div class="entry-category">
      <div class="category-header">${cat}</div>
      <div class="category-entries">
        ${byCategory[cat]
          .map(
            (e) => `
          <div class="entry-item">
            <div class="entry-key">${e.key}</div>
            <p class="entry-value">${e.value}</p>
            ${e.created_at ? `<div class="entry-date">${formatEntryDate(e.created_at)}</div>` : ""}
          </div>
        `
          )
          .join("")}
      </div>
    </div>
  `
    )
    .join("");
}

/* ── Local storage persistence ───────────────────────────── */

const STORAGE_KEY = "rally_added_entries";

function getEntries() {
  const base = DUMMY_DATA.knowledge || [];
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const added = JSON.parse(stored);
      return [...base, ...added];
    }
  } catch (_) {}
  return base;
}

function initAddForm() {
  const form = document.getElementById("add-form");
  const toast = document.getElementById("toast");
  if (!form || !toast) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const key = form.querySelector("#key").value.trim();
    const value = form.querySelector("#value").value.trim();
    const category = form.querySelector("#category").value;

    if (!key || !value) return;

    const entry = {
      key,
      value,
      category,
      created_at: new Date().toISOString(),
    };

    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      const added = stored ? JSON.parse(stored) : [];
      added.push(entry);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(added));
    } catch (_) {}

    form.reset();
    toast.textContent = "Entry added. Switch to Entries tab to view.";
    toast.classList.add("visible");
    setTimeout(() => toast.classList.remove("visible"), 3000);
  });
}

/* ── Init ─────────────────────────────────────────────────── */

function init() {
  initFluidCanvas();
  setHeaderDate();
  initAddForm();
  setupRouter();
}
