/**
 * cmd_palette.js — Keyboard command palette with fuzzy search.
 *
 * Usage:
 *   <script src="components/cmd_palette.js"></script>
 *   CmdPalette.init();
 *   CmdPalette.register({ id, label, description, shortcut, action, category });
 *
 * NOTE: The dashboard's existing #cmd-palette HTML + JS (openCmdPalette,
 * closeCmdPalette, filterCmd, cmdKeyNav) remains the live UI element.
 * This module extends / replaces that logic when init() is called.
 */
(function (global) {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────────────
  const _commands   = new Map();   // id → Command
  let   _filteredCmds = [];        // current filtered list shown in UI
  let   _selectedIdx  = -1;
  let   _isOpen       = false;
  const LS_HISTORY_KEY = 'cmd_palette_history';
  const HISTORY_MAX    = 10;

  // ── DOM references ─────────────────────────────────────────────────────────
  let _overlay  = null;
  let _input    = null;
  let _list     = null;
  let _overlay_id = 'cmd-palette';
  let _input_id   = 'cmd-input';
  let _list_id    = 'cmd-list';

  // ── History helpers ────────────────────────────────────────────────────────
  function _loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(LS_HISTORY_KEY) || '[]');
    } catch (_) { return []; }
  }
  function _saveHistory(history) {
    try { localStorage.setItem(LS_HISTORY_KEY, JSON.stringify(history.slice(0, HISTORY_MAX))); } catch (_) {}
  }
  function _pushHistory(id) {
    let history = _loadHistory();
    history = [id, ...history.filter(h => h !== id)].slice(0, HISTORY_MAX);
    _saveHistory(history);
  }

  // ── Fuzzy match: all chars of query appear in order in str ────────────────
  function _fuzzyScore(str, query) {
    if (!query) return 1;
    const s = str.toLowerCase();
    const q = query.toLowerCase();

    // Exact prefix boost
    if (s.startsWith(q)) return 100 + (100 - s.length);

    // Consecutive char run score
    let score  = 0;
    let si     = 0;
    let run    = 0;
    for (let qi = 0; qi < q.length; qi++) {
      let found = false;
      while (si < s.length) {
        if (s[si] === q[qi]) {
          run++;
          score += run * 2; // bonus for consecutive matches
          si++;
          found = true;
          break;
        }
        run = 0;
        si++;
      }
      if (!found) return -1; // not a match
    }
    return score;
  }

  // ── Score a command against query ─────────────────────────────────────────
  function _scoreCommand(cmd, query) {
    if (!query) return 0;
    const labelScore = _fuzzyScore(cmd.label, query);
    const descScore  = _fuzzyScore(cmd.description || '', query) * 0.5;
    return Math.max(labelScore, descScore);
  }

  // ── Public: search ────────────────────────────────────────────────────────
  function search(query) {
    const all = Array.from(_commands.values());
    if (!query || !query.trim()) {
      // Show history first
      const history = _loadHistory();
      const histCmds = history
        .map(id => _commands.get(id))
        .filter(Boolean);
      const rest = all.filter(c => !history.includes(c.id));
      return [...histCmds, ...rest];
    }
    return all
      .map(cmd => ({ cmd, score: _scoreCommand(cmd, query) }))
      .filter(({ score }) => score > 0)
      .sort((a, b) => b.score - a.score)
      .map(({ cmd }) => cmd);
  }

  // ── Render the command list ────────────────────────────────────────────────
  function _render(query) {
    if (!_list) return;
    _filteredCmds = search(query);
    _selectedIdx  = _filteredCmds.length > 0 ? 0 : -1;

    const history = _loadHistory();
    const histSet = new Set(history.slice(0, 5));
    let lastCategory = null;
    let html = '';

    if (!query && history.length > 0) {
      html += '<div class="cmd-section">Recent</div>';
    }

    _filteredCmds.forEach((cmd, idx) => {
      if (query && cmd.category && cmd.category !== lastCategory) {
        html += `<div class="cmd-section">${_esc(cmd.category)}</div>`;
        lastCategory = cmd.category;
      }
      const isRecent = !query && histSet.has(cmd.id);
      const selClass = idx === _selectedIdx ? ' cmd-sel' : '';
      const shortcut = cmd.shortcut ? `<span style="margin-left:auto;font-size:10px;color:var(--text-muted,#6e7681);">${_esc(cmd.shortcut)}</span>` : '';
      const recentIcon = isRecent ? '🕐' : (cmd.icon || '⚡');
      html += `<div class="cmd-item${selClass}" data-idx="${idx}" onclick="CmdPalette._execute(${idx})">
        <span class="cmd-icon">${recentIcon}</span>
        <div style="flex:1;min-width:0;">
          <div style="color:var(--text-primary,#e6edf3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${_esc(cmd.label)}</div>
          ${cmd.description ? `<div style="font-size:11px;color:var(--text-muted,#6e7681);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${_esc(cmd.description)}</div>` : ''}
        </div>
        ${shortcut}
      </div>`;
    });

    if (_filteredCmds.length === 0) {
      html = '<div style="padding:24px 18px;text-align:center;color:var(--text-muted,#6e7681);font-size:13px;">No commands match</div>';
    }

    _list.innerHTML = html;
  }

  // ── Public: execute at index ──────────────────────────────────────────────
  function _execute(idx) {
    const cmd = _filteredCmds[idx];
    if (!cmd) return;
    _pushHistory(cmd.id);
    close();
    try { cmd.action(); } catch (e) { console.error('CmdPalette action error:', cmd.id, e); }
  }

  // ── Public: open ─────────────────────────────────────────────────────────
  function open() {
    if (!_overlay) _buildDOM();
    _overlay.classList.add('cmd-open');
    _isOpen = true;
    if (_input) {
      _input.value = '';
      _input.focus();
    }
    _render('');
  }

  // ── Public: close ─────────────────────────────────────────────────────────
  function close() {
    if (_overlay) _overlay.classList.remove('cmd-open');
    _isOpen = false;
  }

  // ── Build DOM if not already present ──────────────────────────────────────
  function _buildDOM() {
    // Try to reuse existing cmd-palette HTML from index.html
    _overlay = document.getElementById(_overlay_id);
    _input   = document.getElementById(_input_id);
    _list    = document.getElementById(_list_id);

    if (!_overlay) {
      // Create fresh overlay
      _overlay = document.createElement('div');
      _overlay.id = _overlay_id;
      _overlay.style.cssText = 'display:none;position:fixed;inset:0;z-index:70;align-items:flex-start;justify-content:center;padding-top:14vh;background:rgba(0,0,0,.6);backdrop-filter:blur(8px);';
      _overlay.addEventListener('click', close);

      const box = document.createElement('div');
      box.className = 'cmd-box fadein';
      box.style.cssText = 'background:var(--bg-card,#161b22);border:1px solid rgba(255,255,255,.16);border-radius:14px;width:100%;max-width:560px;box-shadow:0 28px 80px rgba(0,0,0,.75);overflow:hidden;';
      box.addEventListener('click', e => e.stopPropagation());

      const inputRow = document.createElement('div');
      inputRow.className = 'cmd-input-row';
      inputRow.style.cssText = 'display:flex;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid rgba(255,255,255,.05);';
      inputRow.innerHTML = '<span style="color:var(--text-muted,#6e7681);font-size:16px;">⌘</span>';

      _input = document.createElement('input');
      _input.id = _input_id;
      _input.className = 'cmd-input';
      _input.placeholder = 'Search commands…';
      _input.autocomplete = 'off';
      _input.style.cssText = 'flex:1;background:transparent;border:none;outline:none;font-family:inherit;font-size:14px;color:var(--text-primary,#e6edf3);';
      inputRow.appendChild(_input);
      inputRow.innerHTML += '<span style="display:inline-block;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:4px;padding:2px 7px;font-size:11px;color:var(--text-secondary,#8b949e);font-family:monospace;">Esc</span>';

      _list = document.createElement('div');
      _list.id = _list_id;
      _list.style.cssText = 'overflow-y:auto;max-height:320px;';

      const footer = document.createElement('div');
      footer.style.cssText = 'padding:8px 18px;border-top:1px solid rgba(255,255,255,.05);display:flex;gap:14px;font-size:10px;color:rgba(255,255,255,.25);';
      footer.innerHTML = '<span><kbd style="font-family:monospace;border:1px solid rgba(255,255,255,.12);border-radius:3px;padding:1px 5px;">↑↓</kbd> navigate</span><span><kbd style="font-family:monospace;border:1px solid rgba(255,255,255,.12);border-radius:3px;padding:1px 5px;">↵</kbd> select</span><span><kbd style="font-family:monospace;border:1px solid rgba(255,255,255,.12);border-radius:3px;padding:1px 5px;">Esc</kbd> close</span>';

      box.appendChild(inputRow);
      box.appendChild(_list);
      box.appendChild(footer);
      _overlay.appendChild(box);
      document.body.appendChild(_overlay);
    }

    // Wire input events
    _input.addEventListener('input', () => _render(_input.value));
    _input.addEventListener('keydown', _onKeyDown);

    // Wire overlay CSS open state
    const origDisplay = _overlay.style.display;
    Object.defineProperty(_overlay, '_cmdOpen', {
      get: () => _overlay.classList.contains('cmd-open'),
    });
    // Patch classList.add to also set display:flex
    const origAdd = _overlay.classList.add.bind(_overlay.classList);
    _overlay.classList.add = (...args) => {
      origAdd(...args);
      if (args.includes('cmd-open')) _overlay.style.display = 'flex';
    };
    const origRemove = _overlay.classList.remove.bind(_overlay.classList);
    _overlay.classList.remove = (...args) => {
      origRemove(...args);
      if (args.includes('cmd-open')) _overlay.style.display = 'none';
    };
  }

  function _onKeyDown(e) {
    if (e.key === 'Escape')   { e.preventDefault(); close(); return; }
    if (e.key === 'ArrowDown') { e.preventDefault(); _moveSelection(1);  return; }
    if (e.key === 'ArrowUp')   { e.preventDefault(); _moveSelection(-1); return; }
    if (e.key === 'Enter')     { e.preventDefault(); _execute(_selectedIdx); return; }
  }

  function _moveSelection(delta) {
    if (_filteredCmds.length === 0) return;
    _selectedIdx = (_selectedIdx + delta + _filteredCmds.length) % _filteredCmds.length;
    // Update DOM
    const items = _list.querySelectorAll('.cmd-item');
    items.forEach((el, i) => el.classList.toggle('cmd-sel', i === _selectedIdx));
    const sel = items[_selectedIdx];
    if (sel) sel.scrollIntoView({ block: 'nearest' });
  }

  // ── Public: register ──────────────────────────────────────────────────────
  function register(command) {
    _commands.set(command.id, Object.assign({ icon: '⚡', category: 'General' }, command));
  }

  // ── Public: unregister ────────────────────────────────────────────────────
  function unregister(id) {
    _commands.delete(id);
  }

  // ── Register keyboard shortcuts ────────────────────────────────────────────
  function _registerShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Cmd+K (Mac) or Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        _isOpen ? close() : open();
        return;
      }
      // '/' when not in a text input
      if (e.key === '/' && !_isOpen) {
        const tag = document.activeElement && document.activeElement.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
        e.preventDefault();
        open();
      }
    });
  }

  // ── Safe fetch helper ─────────────────────────────────────────────────────
  function _post(url) {
    return fetch(url, { method: 'POST' })
      .then(r => { if (!r.ok) throw new Error(`${r.status} ${r.statusText}`); })
      .catch(err => console.warn('CmdPalette action failed:', url, err));
  }

  // ── Sync helpers (look for existing dashboard globals) ────────────────────
  function _syncToPlane()   { if (global.syncToPlane)   { global.syncToPlane();   } else { _post('/api/plane/sync-to');   } }
  function _syncFromPlane() { if (global.syncFromPlane)  { global.syncFromPlane(); } else { _post('/api/plane/sync-from'); } }
  function _toggleDark()    { if (global.ThemeSystem) { global.ThemeSystem.toggle(); } else { console.warn('ThemeSystem not available'); } }
  function _downloadAll()   { if (global.MetricsView) { global.MetricsView.exportCSV('all'); } else { console.warn('MetricsView not available'); } }

  // ── Public: init ──────────────────────────────────────────────────────────
  function init() {
    _buildDOM();
    _registerShortcuts();

    // Built-in commands
    const builtins = [
      {
        id: 'executor-start',
        label: 'Run Executor',
        description: 'Start the AI executor',
        icon: '▶',
        category: 'Executor',
        action: () => _post('/api/executor/start'),
      },
      {
        id: 'executor-stop',
        label: 'Stop Executor',
        description: 'Stop the AI executor',
        icon: '⏹',
        category: 'Executor',
        action: () => _post('/api/executor/stop'),
      },
      {
        id: 'training-start',
        label: 'Start Training',
        description: 'Begin model fine-tuning',
        icon: '🧠',
        category: 'Training',
        action: () => _post('/api/training/start'),
      },
      {
        id: 'training-stop',
        label: 'Stop Training',
        description: 'Halt training pipeline',
        icon: '⏹',
        category: 'Training',
        action: () => _post('/api/training/stop'),
      },
      {
        id: 'refresh-dashboard',
        label: 'Refresh Dashboard',
        description: 'Reload the page',
        icon: '🔄',
        shortcut: 'R',
        category: 'Navigation',
        action: () => location.reload(),
      },
      {
        id: 'open-plane',
        label: 'Open Plane',
        description: 'Open Plane project management',
        icon: '✈',
        category: 'External',
        action: () => window.open('http://localhost:3001', '_blank', 'noopener'),
      },
      {
        id: 'push-to-plane',
        label: 'Push to Plane',
        description: 'Sync roadmap items to Plane',
        icon: '⬆',
        category: 'Sync',
        action: _syncToPlane,
      },
      {
        id: 'pull-from-plane',
        label: 'Pull from Plane',
        description: 'Sync roadmap items from Plane',
        icon: '⬇',
        category: 'Sync',
        action: _syncFromPlane,
      },
      {
        id: 'toggle-dark-mode',
        label: 'Toggle Dark Mode',
        description: 'Switch between dark and light themes',
        icon: '🌙',
        category: 'Display',
        action: _toggleDark,
      },
      {
        id: 'download-metrics-csv',
        label: 'Download Metrics CSV',
        description: 'Export all metrics as CSV',
        icon: '📥',
        category: 'Export',
        action: _downloadAll,
      },
    ];

    builtins.forEach(cmd => register(cmd));
    _render('');
  }

  // ── Utility ───────────────────────────────────────────────────────────────
  function _esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  // ── Public API ─────────────────────────────────────────────────────────────
  global.CmdPalette = {
    init,
    register,
    unregister,
    open,
    close,
    search,
    _execute,  // exposed for inline onclick in rendered list
  };

}(window));
