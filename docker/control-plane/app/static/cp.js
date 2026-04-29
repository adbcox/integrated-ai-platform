// Tier 3 escalation modal. Triggered when an action returns 401 with
// detail "tier3-reauth-required", or by the unlock button in the auth
// banner. On successful unlock we re-fire the original request via
// the HTMX history.

function openTier3Modal() {
  const root = document.getElementById('modal-root');
  root.innerHTML = `
    <div class="modal-overlay" onclick="if(event.target===this){closeTier3Modal()}">
      <div class="modal-content">
        <h2 class="text-lg font-semibold mb-4">Operator re-auth (Tier 3)</h2>
        <p class="text-sm text-slate-400 mb-4">
          Enter the operator password to unlock sensitive actions for the next
          5 minutes.
        </p>
        <form onsubmit="submitTier3(event)">
          <input type="password" name="password" autofocus
                 class="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 mb-3"
                 placeholder="operator password">
          <div id="tier3-error" class="text-xs text-red-400 mb-3"></div>
          <div class="flex gap-3 justify-between">
            <button type="button" class="rounded bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-sm"
                    onclick="closeTier3Modal()">Cancel</button>
            <button type="submit" class="rounded bg-amber-700 hover:bg-amber-600 px-3 py-1.5 text-sm">
              Unlock
            </button>
          </div>
        </form>
      </div>
    </div>
  `;
}

function closeTier3Modal() {
  document.getElementById('modal-root').innerHTML = '';
}

async function submitTier3(ev) {
  ev.preventDefault();
  const form = ev.target;
  const pw = form.password.value;
  const err = document.getElementById('tier3-error');
  err.textContent = '';
  try {
    const r = await fetch('/auth/unlock', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({password: pw})
    });
    if (r.status === 200) {
      closeTier3Modal();
      htmx.trigger('#auth-banner', 'load');
    } else {
      err.textContent = 'invalid password';
    }
  } catch (e) {
    err.textContent = 'network error';
  }
}
