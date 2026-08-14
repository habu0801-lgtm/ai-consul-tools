const STORAGE_KEY_COLOR   = 'laserColor';
const STORAGE_KEY_ENABLED = 'laserEnabled';

const toggle    = document.getElementById('toggle');
const colorGrid = document.getElementById('colorGrid');
const hint      = document.getElementById('hint');

let currentColor   = 'red';
let currentEnabled = false;

// --- helpers ---

function sendToCurrentTab(payload) {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]?.id) {
      chrome.tabs.sendMessage(tabs[0].id, payload).catch(() => {});
    }
  });
}

function setActiveColorBtn(color) {
  colorGrid.querySelectorAll('.color-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.color === color);
  });
}

function updateHint(enabled) {
  hint.textContent = enabled
    ? 'レーザーポインターが有効です'
    : 'オンにするとカーソルがレーザーポインターに変わります';
}

// --- restore state ---

chrome.storage.local.get([STORAGE_KEY_ENABLED, STORAGE_KEY_COLOR], (result) => {
  currentColor   = result[STORAGE_KEY_COLOR]   || 'red';
  currentEnabled = result[STORAGE_KEY_ENABLED] || false;

  toggle.checked = currentEnabled;
  setActiveColorBtn(currentColor);
  updateHint(currentEnabled);
});

// --- toggle ---

toggle.addEventListener('change', () => {
  currentEnabled = toggle.checked;
  chrome.storage.local.set({ [STORAGE_KEY_ENABLED]: currentEnabled });
  sendToCurrentTab({ type: 'SET_ENABLED', enabled: currentEnabled });
  updateHint(currentEnabled);
});

// --- color selection ---

colorGrid.addEventListener('click', (e) => {
  const btn = e.target.closest('.color-btn');
  if (!btn) return;

  currentColor = btn.dataset.color;
  setActiveColorBtn(currentColor);
  chrome.storage.local.set({ [STORAGE_KEY_COLOR]: currentColor });
  sendToCurrentTab({ type: 'SET_COLOR', color: currentColor });
});
