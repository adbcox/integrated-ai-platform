/**
 * Integrated AI Platform — Shared UI Components
 *
 * Vanilla JS component library. No framework required.
 * Import in any panel HTML:
 *   <script src="/web/shared/components.js"></script>
 *
 * Components:
 *   StatCard       — metric card with label + value + optional badge
 *   StatusDot      — coloured dot with label (running / stopped / warning)
 *   ProgressBar    — labelled progress bar
 *   LogViewer      — scrollable live log with auto-scroll
 *   KanbanColumn   — roadmap item column
 *   Toast          — transient notification
 *   ApiPoller      — polls an endpoint and fires callbacks
 */

"use strict";

// ── StatCard ─────────────────────────────────────────────────────────────────
/**
 * @param {HTMLElement} container
 * @param {Object} opts
 * @param {string} opts.label
 * @param {string|number} opts.value
 * @param {string} [opts.sublabel]
 * @param {'success'|'warn'|'danger'|'info'} [opts.tone]
 */
function StatCard(container, opts = {}) {
  const tone = opts.tone || "";
  const dotClass = tone ? `dot dot-${tone}` : "";
  container.innerHTML = `
    <div class="card card-p" style="min-width:120px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
        <span style="font-size:11px;font-weight:600;letter-spacing:.06em;
                     text-transform:uppercase;color:var(--text-muted)">${opts.label || ""}</span>
        ${dotClass ? `<span class="${dotClass}"></span>` : ""}
      </div>
      <div class="stat-value" style="font-size:28px;font-weight:700;
                  color:var(--text-primary);line-height:1.1;font-variant-numeric:tabular-nums">
        ${opts.value ?? "–"}
      </div>
      ${opts.sublabel ? `<div style="font-size:11px;color:var(--text-muted);margin-top:2px">${opts.sublabel}</div>` : ""}
    </div>
  `;
  return {
    setValue(v) {
      const el = container.querySelector(".stat-value");
      if (el) el.textContent = v;
    },
  };
}

// ── StatusDot ────────────────────────────────────────────────────────────────
/**
 * @param {HTMLElement} container
 * @param {boolean} running
 * @param {string} label
 */
function StatusDot(container, running, label) {
  const tone = running ? "success" : "muted";
  const text = running ? (label || "Running") : "Stopped";
  container.innerHTML = `
    <span style="display:inline-flex;align-items:center;gap:6px">
      <span class="dot dot-${tone}"></span>
      <span style="font-size:12px;color:var(--text-secondary)">${text}</span>
    </span>
  `;
}

// ── ProgressBar ──────────────────────────────────────────────────────────────
/**
 * @param {HTMLElement} container
 * @param {Object} opts
 * @param {number} opts.pct   0–100
 * @param {string} [opts.label]
 * @param {string} [opts.sublabel]
 * @param {'success'|'warn'|'danger'} [opts.tone]
 */
function ProgressBar(container, opts = {}) {
  const pct = Math.min(100, Math.max(0, opts.pct || 0));
  const tone = opts.tone || (pct >= 80 ? "success" : pct >= 50 ? "" : "warn");
  container.innerHTML = `
    <div>
      ${opts.label ? `
        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
          <span style="font-size:12px;color:var(--text-secondary)">${opts.label}</span>
          <span style="font-size:12px;font-weight:600;color:var(--text-primary)">${pct}%</span>
        </div>` : ""}
      <div class="progress-track">
        <div class="progress-fill progress-fill-${tone}" style="width:${pct}%"></div>
      </div>
      ${opts.sublabel ? `<div style="font-size:11px;color:var(--text-muted);margin-top:2px">${opts.sublabel}</div>` : ""}
    </div>
  `;
  return {
    update(newPct, newLabel) {
      const fill = container.querySelector(".progress-fill");
      const label = container.querySelector(".text-secondary");
      if (fill) fill.style.width = `${Math.min(100, newPct)}%`;
      if (label && newLabel) label.textContent = newLabel;
    },
  };
}

// ── LogViewer ────────────────────────────────────────────────────────────────
/**
 * @param {HTMLElement} container
 * @param {Object} opts
 * @param {string} [opts.height]    CSS height, default '240px'
 * @param {boolean} [opts.autoScroll] default true
 */
function LogViewer(container, opts = {}) {
  const height = opts.height || "240px";
  const autoScroll = opts.autoScroll !== false;
  container.innerHTML = `<pre class="log-output" style="height:${height};margin:0"></pre>`;
  const pre = container.querySelector("pre");

  return {
    setLines(lines) {
      pre.textContent = lines.join("\n");
      if (autoScroll) pre.scrollTop = pre.scrollHeight;
    },
    append(line) {
      pre.textContent += "\n" + line;
      if (autoScroll) pre.scrollTop = pre.scrollHeight;
    },
    clear() {
      pre.textContent = "";
    },
  };
}

// ── KanbanColumn ─────────────────────────────────────────────────────────────
/**
 * @param {HTMLElement} container
 * @param {Object} opts
 * @param {string} opts.title
 * @param {Array<{id,title,category}>} opts.items
 * @param {'success'|'info'|'warn'|'muted'} [opts.tone]
 */
function KanbanColumn(container, opts = {}) {
  const items = opts.items || [];
  const tone = opts.tone || "muted";
  container.innerHTML = `
    <div class="card card-p" style="min-width:200px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--sp-2)">
        <span style="font-size:11px;font-weight:700;letter-spacing:.08em;
                     text-transform:uppercase;color:var(--text-muted)">${opts.title || ""}</span>
        <span class="badge badge-${tone}">${items.length}</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:6px">
        ${items.map(it => `
          <div style="background:var(--bg-subtle);border:1px solid var(--border-muted);
                      border-radius:var(--r-md);padding:8px 10px">
            <div style="font-size:12px;font-weight:500;color:var(--text-primary);
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${it.title}</div>
            <div style="font-size:10px;color:var(--text-muted);margin-top:2px">${it.id} · ${it.category}</div>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

// ── Toast ─────────────────────────────────────────────────────────────────────
const _toastContainer = (() => {
  const el = document.createElement("div");
  el.style.cssText = `
    position: fixed; bottom: 24px; right: 24px;
    display: flex; flex-direction: column; gap: 8px;
    z-index: var(--z-toast, 500); pointer-events: none;
  `;
  document.addEventListener("DOMContentLoaded", () => document.body.appendChild(el));
  return el;
})();

/**
 * Show a transient notification.
 * @param {string} message
 * @param {'success'|'warn'|'danger'|'info'} [tone]
 * @param {number} [durationMs]
 */
function Toast(message, tone = "info", durationMs = 3500) {
  const el = document.createElement("div");
  el.style.cssText = `
    padding: 10px 16px; border-radius: var(--r-md);
    font-size: 13px; font-weight: 500; pointer-events: auto;
    background: var(--bg-card); border: 1px solid var(--border-hover);
    color: var(--text-primary);
    box-shadow: var(--shadow-elev);
    opacity: 0; transition: opacity 150ms;
  `;
  el.textContent = message;
  _toastContainer.appendChild(el);
  requestAnimationFrame(() => { el.style.opacity = "1"; });
  setTimeout(() => {
    el.style.opacity = "0";
    setTimeout(() => el.remove(), 200);
  }, durationMs);
}

// ── ApiPoller ────────────────────────────────────────────────────────────────
/**
 * Polls a URL on an interval and calls onData / onError.
 * @param {Object} opts
 * @param {string} opts.url
 * @param {number} [opts.intervalMs]   default 5000
 * @param {Function} opts.onData
 * @param {Function} [opts.onError]
 */
function ApiPoller(opts) {
  const intervalMs = opts.intervalMs || 5000;
  let timer = null;

  async function poll() {
    try {
      const res = await fetch(opts.url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      opts.onData(data);
    } catch (err) {
      if (opts.onError) opts.onError(err);
    }
  }

  return {
    start() {
      poll();
      timer = setInterval(poll, intervalMs);
    },
    stop() {
      if (timer) clearInterval(timer);
      timer = null;
    },
    poll,
  };
}

// ── Exports ───────────────────────────────────────────────────────────────────
if (typeof module !== "undefined") {
  module.exports = { StatCard, StatusDot, ProgressBar, LogViewer, KanbanColumn, Toast, ApiPoller };
}
