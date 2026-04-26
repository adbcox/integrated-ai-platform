/**
 * dependency_graph.js — D3.js force-directed dependency graph component.
 *
 * Usage:
 *   <script src="components/dependency_graph.js"></script>
 *   DependencyGraph.init('container-id', data);
 *
 * Requires D3.js v7 loaded before this script (window.d3 must exist).
 */
(function (global) {
  'use strict';

  // ── Constants ──────────────────────────────────────────────────────────────
  const STATUS_COLOR = {
    done:        '#22c55e',
    in_progress: '#f59e0b',
    blocked:     '#ef4444',
    backlog:     '#6b7280',
  };
  const LINK_COLOR_CRITICAL = '#f97316';
  const LINK_COLOR_DEFAULT  = '#374151';
  const NODE_RADIUS_DEFAULT    = 8;
  const NODE_RADIUS_BOTTLENECK = 12;

  // ── Module state ───────────────────────────────────────────────────────────
  let _svg        = null;
  let _simulation = null;
  let _g          = null;       // main transform group
  let _zoom       = null;       // d3 zoom behaviour
  let _nodes      = [];
  let _links      = [];
  let _nodeEls    = null;
  let _linkEls    = null;
  let _currentData = null;
  let _detailPanel = null;
  let _contextMenu = null;

  // ── Placeholder when D3 is missing ────────────────────────────────────────
  function _placeholder(container) {
    container.innerHTML =
      '<div style="display:flex;align-items:center;justify-content:center;height:200px;' +
      'color:#6b7280;font-family:sans-serif;font-size:14px;border:1px dashed #374151;border-radius:8px;">' +
      'D3.js required — add <script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>' +
      '</div>';
  }

  // ── Build detail panel DOM ─────────────────────────────────────────────────
  function _ensureDetailPanel(container) {
    if (_detailPanel) return;
    _detailPanel = document.createElement('div');
    _detailPanel.id = 'dg-detail-panel';
    Object.assign(_detailPanel.style, {
      position: 'absolute',
      top: '8px',
      right: '8px',
      width: '220px',
      background: 'rgba(22,27,34,0.97)',
      border: '1px solid #30363d',
      borderRadius: '8px',
      padding: '12px',
      fontSize: '12px',
      color: '#e6edf3',
      fontFamily: 'sans-serif',
      lineHeight: '1.5',
      boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
      display: 'none',
      zIndex: '10',
    });
    container.style.position = 'relative';
    container.appendChild(_detailPanel);
  }

  // ── Build context menu DOM ─────────────────────────────────────────────────
  function _ensureContextMenu(container) {
    if (_contextMenu) return;
    _contextMenu = document.createElement('ul');
    _contextMenu.id = 'dg-context-menu';
    Object.assign(_contextMenu.style, {
      position: 'fixed',
      background: '#161b22',
      border: '1px solid #30363d',
      borderRadius: '6px',
      padding: '4px 0',
      listStyle: 'none',
      margin: '0',
      fontSize: '12px',
      color: '#e6edf3',
      fontFamily: 'sans-serif',
      boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
      display: 'none',
      zIndex: '1000',
      minWidth: '160px',
    });
    document.body.appendChild(_contextMenu);
    document.addEventListener('click', () => { _contextMenu.style.display = 'none'; });
  }

  function _ctxItem(label, fn) {
    const li = document.createElement('li');
    li.textContent = label;
    Object.assign(li.style, {
      padding: '6px 14px',
      cursor: 'pointer',
      transition: 'background 0.1s',
    });
    li.addEventListener('mouseenter', () => { li.style.background = 'rgba(88,166,255,0.12)'; });
    li.addEventListener('mouseleave', () => { li.style.background = ''; });
    li.addEventListener('click', (e) => { e.stopPropagation(); _contextMenu.style.display = 'none'; fn(); });
    return li;
  }

  // ── Link width from value 1-5 → 1-4px ─────────────────────────────────────
  function _linkWidth(value) {
    const v = Math.max(1, Math.min(5, value || 1));
    return 1 + (v - 1) * (3 / 4); // 1 → 1, 5 → 4
  }

  // ── Resolve node by id ─────────────────────────────────────────────────────
  function _nodeById(id) {
    return _nodes.find(n => n.id === id) || null;
  }

  // ── Public: init ──────────────────────────────────────────────────────────
  function init(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) { console.warn('DependencyGraph.init: container not found:', containerId); return; }

    if (!window.d3) {
      _placeholder(container);
      return;
    }
    const d3 = window.d3;

    _ensureDetailPanel(container);
    _ensureContextMenu(container);

    // Clear previous
    container.querySelectorAll('svg').forEach(el => el.remove());
    if (_simulation) { _simulation.stop(); _simulation = null; }

    _currentData = data;
    _nodes = (data.nodes || []).map(n => Object.assign({}, n));
    _links = (data.links || []).map(l => Object.assign({}, l));

    const W = container.clientWidth  || 800;
    const H = container.clientHeight || 500;

    // ── SVG setup ───────────────────────────────────────────────────────────
    _svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${W} ${H}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('cursor', 'grab');

    // Arrow markers
    const defs = _svg.append('defs');
    ['default', 'critical'].forEach(type => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', type === 'critical' ? LINK_COLOR_CRITICAL : LINK_COLOR_DEFAULT);
    });

    _g = _svg.append('g');

    // ── Zoom behaviour ───────────────────────────────────────────────────────
    _zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => { _g.attr('transform', event.transform); });
    _svg.call(_zoom);

    // ── Links ────────────────────────────────────────────────────────────────
    _linkEls = _g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(_links)
      .join('line')
      .attr('stroke', d => d.critical ? LINK_COLOR_CRITICAL : LINK_COLOR_DEFAULT)
      .attr('stroke-width', d => _linkWidth(d.value))
      .attr('stroke-opacity', 0.7)
      .attr('marker-end', d => `url(#arrow-${d.critical ? 'critical' : 'default'})`);

    // ── Node groups ──────────────────────────────────────────────────────────
    _nodeEls = _g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(_nodes)
      .join('g')
      .attr('class', 'node-g')
      .style('cursor', 'pointer')
      .call(
        d3.drag()
          .on('start', (event, d) => {
            if (!event.active) _simulation.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
          })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on('end', (event, d) => {
            if (!event.active) _simulation.alphaTarget(0);
            d.fx = null; d.fy = null;
          })
      );

    // Circle
    _nodeEls.append('circle')
      .attr('r', d => d.bottleneck ? NODE_RADIUS_BOTTLENECK : NODE_RADIUS_DEFAULT)
      .attr('fill', d => STATUS_COLOR[d.status] || STATUS_COLOR.backlog)
      .attr('stroke', d => d.critical_path ? '#f97316' : 'rgba(255,255,255,0.15)')
      .attr('stroke-width', d => d.critical_path ? 2.5 : 1);

    // Label
    _nodeEls.append('text')
      .attr('dy', d => (d.bottleneck ? NODE_RADIUS_BOTTLENECK : NODE_RADIUS_DEFAULT) + 12)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', '#8b949e')
      .attr('font-family', 'sans-serif')
      .text(d => (d.title || d.id || '').substring(0, 20));

    // Click → show_detail
    _nodeEls.on('click', (event, d) => {
      event.stopPropagation();
      show_detail(d.id);
    });

    // Double-click → open URL
    _nodeEls.on('dblclick', (event, d) => {
      event.stopPropagation();
      const url = d.url || `/roadmap/${d.id}`;
      window.open(url, '_blank', 'noopener');
    });

    // Right-click → context menu
    _nodeEls.on('contextmenu', (event, d) => {
      event.preventDefault();
      _contextMenu.innerHTML = '';
      _contextMenu.appendChild(_ctxItem('Highlight paths', () => highlight_path(_getConnectedIds(d.id))));
      _contextMenu.appendChild(_ctxItem('Center on node', () => _centerOn(d)));
      _contextMenu.appendChild(_ctxItem('Show detail', () => show_detail(d.id)));
      _contextMenu.appendChild(_ctxItem('Reset view', () => reset()));
      Object.assign(_contextMenu.style, {
        display: 'block',
        left: event.clientX + 'px',
        top:  event.clientY + 'px',
      });
    });

    // Tooltip on hover
    _nodeEls.append('title').text(d =>
      `${d.title || d.id}\nStatus: ${d.status || 'unknown'}\nCategory: ${d.category || '—'}`
    );

    // ── Simulation ──────────────────────────────────────────────────────────
    _simulation = d3.forceSimulation(_nodes)
      .force('link', d3.forceLink(_links).id(d => d.id).distance(90).strength(0.8))
      .force('charge', d3.forceManyBody().strength(-250))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collide', d3.forceCollide(d => (d.bottleneck ? NODE_RADIUS_BOTTLENECK : NODE_RADIUS_DEFAULT) + 6))
      .on('tick', _ticked);

    // Click svg background → deselect + close detail
    _svg.on('click', () => {
      _detailPanel.style.display = 'none';
      _nodeEls.selectAll('circle').attr('opacity', 1);
      _linkEls.attr('opacity', 1);
    });
  }

  function _ticked() {
    if (!_linkEls || !_nodeEls) return;
    _linkEls
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);
    _nodeEls.attr('transform', d => `translate(${d.x},${d.y})`);
  }

  // ── Public: zoom ──────────────────────────────────────────────────────────
  function zoom(factor) {
    if (!_svg || !_zoom) return;
    _svg.transition().duration(300).call(_zoom.scaleBy, factor);
  }

  // ── Get all directly connected node ids ───────────────────────────────────
  function _getConnectedIds(nodeId) {
    const ids = new Set([nodeId]);
    _links.forEach(l => {
      const sid = typeof l.source === 'object' ? l.source.id : l.source;
      const tid = typeof l.target === 'object' ? l.target.id : l.target;
      if (sid === nodeId) ids.add(tid);
      if (tid === nodeId) ids.add(sid);
    });
    return Array.from(ids);
  }

  // ── Public: highlight_path ────────────────────────────────────────────────
  function highlight_path(node_ids) {
    if (!_nodeEls || !_linkEls) return;
    const idSet = new Set(node_ids);

    _nodeEls.selectAll('circle').attr('opacity', d => idSet.has(d.id) ? 1 : 0.18);
    _nodeEls.selectAll('text').attr('opacity', d => idSet.has(d.id) ? 1 : 0.18);

    _linkEls.attr('opacity', d => {
      const sid = typeof d.source === 'object' ? d.source.id : d.source;
      const tid = typeof d.target === 'object' ? d.target.id : d.target;
      return (idSet.has(sid) && idSet.has(tid)) ? 1 : 0.07;
    });
  }

  // ── Public: reset ─────────────────────────────────────────────────────────
  function reset() {
    if (!_nodeEls || !_linkEls) return;
    _nodeEls.selectAll('circle').attr('opacity', 1);
    _nodeEls.selectAll('text').attr('opacity', 1);
    _linkEls.attr('opacity', 0.7);
    if (_svg && _zoom) {
      _svg.transition().duration(400).call(_zoom.transform, window.d3.zoomIdentity);
    }
    if (_detailPanel) _detailPanel.style.display = 'none';
  }

  // ── Center view on a node ─────────────────────────────────────────────────
  function _centerOn(d) {
    if (!_svg || !_zoom) return;
    const W = _svg.node().clientWidth  || 800;
    const H = _svg.node().clientHeight || 500;
    _svg.transition().duration(400).call(
      _zoom.transform,
      window.d3.zoomIdentity.translate(W / 2 - d.x, H / 2 - d.y)
    );
  }

  // ── Public: show_detail ───────────────────────────────────────────────────
  function show_detail(node_id) {
    if (!_detailPanel) return;
    const node = _nodeById(node_id);
    if (!node) { _detailPanel.style.display = 'none'; return; }

    const deps = _links
      .filter(l => {
        const tid = typeof l.target === 'object' ? l.target.id : l.target;
        return tid === node_id;
      })
      .map(l => typeof l.source === 'object' ? l.source.id : l.source);

    const dependents = _links
      .filter(l => {
        const sid = typeof l.source === 'object' ? l.source.id : l.source;
        return sid === node_id;
      })
      .map(l => typeof l.target === 'object' ? l.target.id : l.target);

    const statusColor = STATUS_COLOR[node.status] || STATUS_COLOR.backlog;

    _detailPanel.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <span style="font-weight:600;font-size:13px;color:#e6edf3;line-height:1.3;">
          ${_esc(node.title || node.id)}
        </span>
        <button onclick="DependencyGraph._closeDetail()"
                style="background:none;border:none;color:#8b949e;cursor:pointer;font-size:16px;line-height:1;padding:0 0 0 8px;">✕</button>
      </div>
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${statusColor};flex-shrink:0;"></span>
        <span style="color:${statusColor};font-size:11px;font-weight:600;text-transform:capitalize;">
          ${_esc(node.status || 'unknown')}
        </span>
        ${node.category ? `<span style="color:#8b949e;font-size:10px;">· ${_esc(node.category)}</span>` : ''}
      </div>
      ${node.bottleneck ? '<div style="color:#f59e0b;font-size:10px;margin-bottom:6px;">⚠ Bottleneck node</div>' : ''}
      ${node.critical_path ? '<div style="color:#f97316;font-size:10px;margin-bottom:6px;">⬥ On critical path</div>' : ''}
      <div style="margin-bottom:6px;">
        <div style="color:#6e7681;font-size:10px;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px;">Dependencies (${deps.length})</div>
        ${deps.length ? deps.map(id => `<div style="color:#8b949e;font-size:11px;padding:1px 0;">${_esc(id)}</div>`).join('') : '<div style="color:#6e7681;font-size:11px;">None</div>'}
      </div>
      <div>
        <div style="color:#6e7681;font-size:10px;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px;">Dependents (${dependents.length})</div>
        ${dependents.length ? dependents.map(id => `<div style="color:#8b949e;font-size:11px;padding:1px 0;">${_esc(id)}</div>`).join('') : '<div style="color:#6e7681;font-size:11px;">None</div>'}
      </div>
    `;
    _detailPanel.style.display = 'block';

    // Highlight this node's connections
    highlight_path(_getConnectedIds(node_id));
  }

  function _closeDetail() {
    if (_detailPanel) _detailPanel.style.display = 'none';
    reset();
  }

  function _esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ── Public API ─────────────────────────────────────────────────────────────
  const DependencyGraph = {
    init,
    zoom,
    highlight_path,
    reset,
    show_detail,
    _closeDetail,  // exposed for inline onclick in detail panel
  };

  global.DependencyGraph = DependencyGraph;

}(window));
