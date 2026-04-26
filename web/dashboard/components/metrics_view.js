/**
 * metrics_view.js — Configurable metrics dashboard panels using Chart.js.
 *
 * Usage:
 *   <script src="components/metrics_view.js"></script>
 *   MetricsView.init('container-id');
 *
 * Requires Chart.js (window.Chart) already loaded.
 */
(function (global) {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────────────
  let _containerId  = null;
  let _container    = null;
  let _panels       = {};      // panel_id → { config, chartInstance, el, data }
  let _panelOrder   = [];      // ordered panel_id list (persisted to localStorage)
  let _autoTimer    = null;
  let _autoInterval = 5000;
  let _dragSrcId    = null;
  const LS_ORDER_KEY = 'metrics_view_panel_order';

  // ── Default panels ─────────────────────────────────────────────────────────
  const DEFAULT_PANELS = [
    { metric: 'cpu_usage',      type: 'line',   title: 'CPU Usage %',      color: '#58a6ff', thresholds: [{ value: 80, color: '#ef4444' }] },
    { metric: 'memory_usage',   type: 'line',   title: 'Memory Usage %',   color: '#a371f7', thresholds: [{ value: 90, color: '#ef4444' }] },
    { metric: 'executor_tasks', type: 'bar',    title: 'Executor Tasks',   color: '#3fb950', thresholds: [] },
    { metric: 'training_loss',  type: 'line',   title: 'Training Loss',    color: '#d29922', thresholds: [] },
  ];

  // ── CSS injection ──────────────────────────────────────────────────────────
  const STYLE_ID = 'metrics-view-style';
  function _injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      .mv-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        padding: 4px;
      }
      @media (max-width: 640px) {
        .mv-grid { grid-template-columns: 1fr; }
      }
      .mv-panel {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px;
        position: relative;
        transition: box-shadow 0.2s;
        cursor: grab;
        user-select: none;
      }
      .mv-panel:active { cursor: grabbing; }
      .mv-panel.mv-drag-over {
        border-color: #58a6ff;
        box-shadow: 0 0 0 2px rgba(88,166,255,0.3);
      }
      .mv-panel-hdr {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
      }
      .mv-title {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #8b949e;
      }
      .mv-actions {
        display: flex;
        gap: 4px;
      }
      .mv-btn {
        background: none;
        border: 1px solid #30363d;
        border-radius: 4px;
        color: #8b949e;
        cursor: pointer;
        font-size: 10px;
        padding: 2px 6px;
        font-family: inherit;
        transition: all 0.1s;
      }
      .mv-btn:hover { border-color: #58a6ff; color: #58a6ff; }
      .mv-number {
        font-size: 32px;
        font-weight: 700;
        color: #e6edf3;
        font-family: 'Inter', sans-serif;
        font-feature-settings: "tnum";
        font-variant-numeric: tabular-nums;
        line-height: 1.1;
        margin: 8px 0;
      }
      .mv-gauge-wrap {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 4px 0;
      }
      .mv-gauge-svg { overflow: visible; }
      .mv-canvas-wrap { position: relative; width: 100%; height: 120px; }
      .mv-canvas-wrap canvas { max-height: 120px; }
      .mv-remove {
        position: absolute;
        top: 6px;
        right: 6px;
        background: none;
        border: none;
        color: #6e7681;
        cursor: pointer;
        font-size: 13px;
        line-height: 1;
        padding: 2px 4px;
        border-radius: 3px;
        opacity: 0;
        transition: opacity 0.15s;
      }
      .mv-panel:hover .mv-remove { opacity: 1; }
      .mv-remove:hover { color: #f85149; }
    `;
    document.head.appendChild(style);
  }

  // ── Unique ID ──────────────────────────────────────────────────────────────
  function _uid() {
    return 'mvp-' + Math.random().toString(36).slice(2, 9);
  }

  // ── Load/save order from localStorage ─────────────────────────────────────
  function _loadOrder() {
    try {
      const raw = localStorage.getItem(LS_ORDER_KEY);
      if (raw) return JSON.parse(raw);
    } catch (_) {}
    return null;
  }
  function _saveOrder() {
    try { localStorage.setItem(LS_ORDER_KEY, JSON.stringify(_panelOrder)); } catch (_) {}
  }

  // ── Rebuild grid DOM order from _panelOrder ────────────────────────────────
  function _reorderDOM() {
    if (!_container) return;
    const grid = _container.querySelector('.mv-grid');
    if (!grid) return;
    _panelOrder.forEach(id => {
      const p = _panels[id];
      if (p && p.el) grid.appendChild(p.el);
    });
  }

  // ── Build a Chart.js chart for "line" or "bar" type ───────────────────────
  function _buildChart(canvas, config, initialData) {
    if (!window.Chart) return null;
    const labels = (initialData || []).map((_, i) => i);
    const values = (initialData || []).map(d => d.value);
    const datasets = [{
      label: config.title,
      data: values,
      borderColor: config.color,
      backgroundColor: config.type === 'bar'
        ? config.color + '99'
        : config.color + '22',
      fill: config.type === 'line',
      tension: 0.35,
      pointRadius: 2,
      borderWidth: 2,
    }];

    // Threshold annotations (manual reference lines via plugin)
    const thresholdPlugins = [];
    (config.thresholds || []).forEach(t => {
      datasets.push({
        label: `Threshold ${t.value}`,
        data: Array(Math.max(values.length, 1)).fill(t.value),
        borderColor: t.color || '#ef4444',
        borderWidth: 1,
        borderDash: [4, 4],
        pointRadius: 0,
        fill: false,
        tension: 0,
      });
    });

    return new Chart(canvas, {
      type: config.type === 'bar' ? 'bar' : 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#161b22',
            borderColor: '#30363d',
            borderWidth: 1,
            titleColor: '#e6edf3',
            bodyColor: '#8b949e',
          },
        },
        scales: {
          x: {
            display: false,
            grid: { color: '#21262d' },
          },
          y: {
            display: true,
            grid: { color: '#21262d' },
            ticks: { color: '#8b949e', font: { size: 10 }, maxTicksLimit: 5 },
          },
        },
      },
    });
  }

  // ── Build a gauge SVG (arc from 0–100) ────────────────────────────────────
  function _buildGaugeSVG(container, config, value) {
    const pct = Math.min(100, Math.max(0, value || 0));
    const r = 52, cx = 70, cy = 70, strokeW = 10;
    const circumference = Math.PI * r;
    const offset = circumference * (1 - pct / 100);
    const color = _thresholdColor(config, pct) || config.color;
    container.innerHTML = `
      <div class="mv-gauge-wrap">
        <svg class="mv-gauge-svg" width="140" height="80" viewBox="0 0 140 80">
          <path d="M${cx - r},${cy} A${r},${r} 0 0 1 ${cx + r},${cy}"
                fill="none" stroke="#21262d" stroke-width="${strokeW}" stroke-linecap="round"/>
          <path d="M${cx - r},${cy} A${r},${r} 0 0 1 ${cx + r},${cy}"
                fill="none" stroke="${color}" stroke-width="${strokeW}" stroke-linecap="round"
                stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
                style="transition: stroke-dashoffset 0.5s ease;"/>
          <text x="${cx}" y="${cy - 4}" text-anchor="middle" font-size="20" font-weight="700" fill="${color}"
                font-family="'Inter',sans-serif">${Math.round(pct)}</text>
          <text x="${cx}" y="${cy + 14}" text-anchor="middle" font-size="10" fill="#8b949e"
                font-family="sans-serif">/ 100</text>
        </svg>
      </div>`;
  }

  // ── Threshold color check ──────────────────────────────────────────────────
  function _thresholdColor(config, value) {
    const thresholds = [...(config.thresholds || [])].sort((a, b) => b.value - a.value);
    for (const t of thresholds) {
      if (value >= t.value) return t.color;
    }
    return null;
  }

  // ── Build panel DOM element ────────────────────────────────────────────────
  function _buildPanelEl(panel_id, config) {
    const el = document.createElement('div');
    el.className = 'mv-panel';
    el.dataset.id = panel_id;

    // Drag-and-drop handlers
    el.draggable = true;
    el.addEventListener('dragstart', (e) => {
      _dragSrcId = panel_id;
      e.dataTransfer.effectAllowed = 'move';
    });
    el.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      el.classList.add('mv-drag-over');
    });
    el.addEventListener('dragleave', () => { el.classList.remove('mv-drag-over'); });
    el.addEventListener('drop', (e) => {
      e.preventDefault();
      el.classList.remove('mv-drag-over');
      if (_dragSrcId && _dragSrcId !== panel_id) {
        const srcIdx = _panelOrder.indexOf(_dragSrcId);
        const tgtIdx = _panelOrder.indexOf(panel_id);
        if (srcIdx !== -1 && tgtIdx !== -1) {
          _panelOrder.splice(srcIdx, 1);
          _panelOrder.splice(tgtIdx, 0, _dragSrcId);
          _saveOrder();
          _reorderDOM();
        }
      }
    });
    el.addEventListener('dragend', () => { _dragSrcId = null; });

    // Header
    const hdr = document.createElement('div');
    hdr.className = 'mv-panel-hdr';
    hdr.innerHTML = `
      <span class="mv-title">${_esc(config.title)}</span>
      <div class="mv-actions">
        <button class="mv-btn mv-export-csv" title="Export CSV">CSV</button>
        <button class="mv-btn mv-export-png" title="Export PNG">PNG</button>
      </div>`;

    hdr.querySelector('.mv-export-csv').addEventListener('click', () => exportCSV(config.metric));
    hdr.querySelector('.mv-export-png').addEventListener('click', () => exportPNG(panel_id));

    // Remove button
    const rmBtn = document.createElement('button');
    rmBtn.className = 'mv-remove';
    rmBtn.innerHTML = '✕';
    rmBtn.title = 'Remove panel';
    rmBtn.addEventListener('click', () => removePanel(panel_id));

    el.appendChild(hdr);
    el.appendChild(rmBtn);

    // Content area
    const content = document.createElement('div');
    content.className = 'mv-panel-content';
    el.appendChild(content);

    return { el, content };
  }

  // ── Render panel content based on type ────────────────────────────────────
  function _renderPanelContent(panel_id) {
    const panel = _panels[panel_id];
    if (!panel) return;
    const { config, content, data } = panel;
    const latestValue = data && data.length ? data[data.length - 1].value : 0;

    if (config.type === 'number') {
      const color = _thresholdColor(config, latestValue) || config.color;
      content.innerHTML = `<div class="mv-number" style="color:${color};">${latestValue}</div>`;
    } else if (config.type === 'gauge') {
      _buildGaugeSVG(content, config, latestValue);
    } else {
      // line or bar — Chart.js
      if (panel.chartInstance) {
        // Update existing chart
        const ch = panel.chartInstance;
        const values = data.map(d => d.value);
        const labels = data.map((_, i) => i);
        ch.data.labels = labels;
        ch.data.datasets[0].data = values;
        // Update threshold datasets
        let di = 1;
        (config.thresholds || []).forEach(() => {
          if (ch.data.datasets[di]) {
            ch.data.datasets[di].data = Array(values.length).fill(
              (config.thresholds[di - 1] || {}).value || 0
            );
          }
          di++;
        });
        ch.update('none');
      } else {
        content.innerHTML = '<div class="mv-canvas-wrap"><canvas></canvas></div>';
        const canvas = content.querySelector('canvas');
        panel.chartInstance = _buildChart(canvas, config, data);
      }
    }
  }

  // ── Public: init ──────────────────────────────────────────────────────────
  function init(containerId) {
    _containerId = containerId;
    _container = document.getElementById(containerId);
    if (!_container) { console.warn('MetricsView.init: container not found:', containerId); return; }

    _injectStyles();
    _panels = {};
    _panelOrder = [];

    // Build grid
    const grid = document.createElement('div');
    grid.className = 'mv-grid';
    _container.innerHTML = '';
    _container.appendChild(grid);

    // Add default panels
    DEFAULT_PANELS.forEach(cfg => addPanel(cfg));

    // Restore order from localStorage
    const savedOrder = _loadOrder();
    if (savedOrder) {
      const validOrder = savedOrder.filter(id => _panels[id]);
      const missing = _panelOrder.filter(id => !validOrder.includes(id));
      _panelOrder = [...validOrder, ...missing];
      _reorderDOM();
    }

    // Start auto-refresh
    startAutoRefresh(_autoInterval);
  }

  // ── Public: addPanel ──────────────────────────────────────────────────────
  function addPanel(config) {
    const panel_id = _uid();
    const { el, content } = _buildPanelEl(panel_id, config);

    const panel = {
      id: panel_id,
      config: Object.assign({}, config),
      el,
      content,
      data: [],
      chartInstance: null,
    };
    _panels[panel_id] = panel;
    _panelOrder.push(panel_id);
    _saveOrder();

    const grid = _container && _container.querySelector('.mv-grid');
    if (grid) grid.appendChild(el);

    _renderPanelContent(panel_id);
    return panel_id;
  }

  // ── Public: removePanel ───────────────────────────────────────────────────
  function removePanel(panel_id) {
    const panel = _panels[panel_id];
    if (!panel) return;
    if (panel.chartInstance) { panel.chartInstance.destroy(); }
    panel.el.remove();
    delete _panels[panel_id];
    const idx = _panelOrder.indexOf(panel_id);
    if (idx !== -1) _panelOrder.splice(idx, 1);
    _saveOrder();
  }

  // ── Public: refresh ───────────────────────────────────────────────────────
  async function refresh() {
    try {
      const res = await fetch('/api/metrics');
      if (!res.ok) return;
      const metricsData = await res.json();
      // metricsData expected: { metric_name: [{value, timestamp}] | number }
      Object.keys(_panels).forEach(panel_id => {
        const panel = _panels[panel_id];
        const raw = metricsData[panel.config.metric];
        if (raw === undefined || raw === null) return;
        if (Array.isArray(raw)) {
          panel.data = raw.slice(-60); // keep last 60 points
        } else {
          panel.data = [...panel.data, { value: Number(raw), timestamp: Date.now() }].slice(-60);
        }
        _renderPanelContent(panel_id);
      });
    } catch (err) {
      console.warn('MetricsView.refresh error:', err);
    }
  }

  // ── Public: exportCSV ─────────────────────────────────────────────────────
  function exportCSV(metric) {
    const rows = ['timestamp,value'];
    // Gather data from matching panels
    Object.values(_panels).forEach(panel => {
      if (metric === 'all' || panel.config.metric === metric) {
        (panel.data || []).forEach(pt => {
          rows.push(`${pt.timestamp || ''},${pt.value}`);
        });
      }
    });
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `metrics_${metric}_${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // ── Public: exportPNG ─────────────────────────────────────────────────────
  function exportPNG(panel_id) {
    const panel = _panels[panel_id];
    if (!panel) return;

    const canvas = panel.chartInstance
      ? panel.chartInstance.canvas
      : panel.content.querySelector('canvas');

    if (!canvas) {
      console.warn('MetricsView.exportPNG: no canvas for panel', panel_id);
      return;
    }

    canvas.toBlob(blob => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a   = document.createElement('a');
      a.href     = url;
      a.download = `panel_${panel.config.metric}_${Date.now()}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 'image/png');
  }

  // ── Public: stopAutoRefresh ───────────────────────────────────────────────
  function stopAutoRefresh() {
    if (_autoTimer) { clearInterval(_autoTimer); _autoTimer = null; }
  }

  // ── Public: startAutoRefresh ─────────────────────────────────────────────
  function startAutoRefresh(interval_ms) {
    stopAutoRefresh();
    _autoInterval = interval_ms || 5000;
    refresh(); // immediate first fetch
    _autoTimer = setInterval(refresh, _autoInterval);
  }

  // ── Utility ───────────────────────────────────────────────────────────────
  function _esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  // ── Public API ─────────────────────────────────────────────────────────────
  global.MetricsView = {
    init,
    addPanel,
    removePanel,
    refresh,
    exportCSV,
    exportPNG,
    stopAutoRefresh,
    startAutoRefresh,
  };

}(window));
