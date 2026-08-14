const CIRCUMFERENCE = 2 * Math.PI * 88; // ≈ 552.9

const timeDisplay = document.getElementById('timeDisplay');
const statusLabel = document.getElementById('statusLabel');
const ringProgress = document.getElementById('ringProgress');
const startBtn = document.getElementById('startBtn');
const resetBtn = document.getElementById('resetBtn');
const fullscreenBtn = document.getElementById('fullscreenBtn');
const iconPlay = document.getElementById('iconPlay');
const iconPause = document.getElementById('iconPause');
const customInput = document.getElementById('customMinutes');
const setCustomBtn = document.getElementById('setCustom');
const presetBtns = document.querySelectorAll('.preset-btn');

let totalSeconds = 25 * 60;
let remainingSeconds = totalSeconds;
let running = false;
let intervalId = null;

// ── Sync with background service worker ──────────────────────────────────────

function syncFromStorage() {
  chrome.storage.local.get(['total', 'remaining', 'running', 'startedAt'], (data) => {
    if (data.total == null) return;

    totalSeconds = data.total;

    if (data.running && data.startedAt != null) {
      const elapsed = Math.floor((Date.now() - data.startedAt) / 1000);
      remainingSeconds = Math.max(0, data.remaining - elapsed);
      if (remainingSeconds > 0) {
        running = true;
        startLocalTick();
      } else {
        remainingSeconds = 0;
        running = false;
        onDone();
      }
    } else {
      remainingSeconds = data.remaining ?? data.total;
      running = false;
    }

    render();
    updateActivePreset(Math.round(totalSeconds / 60));
  });
}

function saveToStorage() {
  chrome.storage.local.set({
    total: totalSeconds,
    remaining: remainingSeconds,
    running,
    startedAt: running ? Date.now() : null,
  });
}

// ── Timer logic ───────────────────────────────────────────────────────────────

function startLocalTick() {
  clearInterval(intervalId);
  intervalId = setInterval(() => {
    if (remainingSeconds <= 0) {
      clearInterval(intervalId);
      running = false;
      remainingSeconds = 0;
      onDone();
      render();
      return;
    }
    remainingSeconds--;
    render();
  }, 1000);
}

function onDone() {
  document.body.classList.add('done');
  statusLabel.textContent = 'TIME\'S UP';
  ringProgress.classList.add('done');
  showPlayIcon();
  chrome.notifications?.create('timer-done', {
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'Lecture Timer',
    message: 'Work session complete!',
    priority: 2,
  });
}

function render() {
  // Time display
  const m = Math.floor(remainingSeconds / 60);
  const s = remainingSeconds % 60;
  timeDisplay.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

  // Ring
  const pct = totalSeconds > 0 ? remainingSeconds / totalSeconds : 1;
  ringProgress.style.strokeDashoffset = CIRCUMFERENCE * (1 - pct);

  // Color transitions
  ringProgress.classList.remove('warn', 'done');
  if (remainingSeconds <= 0) {
    ringProgress.classList.add('done');
  } else if (pct <= 0.2) {
    ringProgress.classList.add('warn');
  }

  // Status
  if (running) {
    statusLabel.textContent = 'IN PROGRESS';
  } else if (remainingSeconds === totalSeconds) {
    statusLabel.textContent = 'READY';
    document.body.classList.remove('done');
  } else if (remainingSeconds > 0) {
    statusLabel.textContent = 'PAUSED';
  }
}

function showPlayIcon() {
  iconPlay.style.display = '';
  iconPause.style.display = 'none';
}

function showPauseIcon() {
  iconPlay.style.display = 'none';
  iconPause.style.display = '';
}

// ── Controls ──────────────────────────────────────────────────────────────────

startBtn.addEventListener('click', () => {
  if (remainingSeconds <= 0) return;

  running = !running;
  document.body.classList.remove('done');

  if (running) {
    startLocalTick();
    showPauseIcon();
    statusLabel.textContent = 'IN PROGRESS';
  } else {
    clearInterval(intervalId);
    showPlayIcon();
    statusLabel.textContent = 'PAUSED';
  }

  saveToStorage();
});

resetBtn.addEventListener('click', () => {
  clearInterval(intervalId);
  running = false;
  remainingSeconds = totalSeconds;
  document.body.classList.remove('done');
  ringProgress.classList.remove('warn', 'done');
  showPlayIcon();
  render();
  saveToStorage();
});

fullscreenBtn.addEventListener('click', () => {
  chrome.tabs.create({ url: chrome.runtime.getURL('fullscreen.html') });
});

// ── Presets ───────────────────────────────────────────────────────────────────

function setDuration(minutes) {
  clearInterval(intervalId);
  running = false;
  totalSeconds = minutes * 60;
  remainingSeconds = totalSeconds;
  document.body.classList.remove('done');
  ringProgress.classList.remove('warn', 'done');
  showPlayIcon();
  render();
  saveToStorage();
}

function updateActivePreset(minutes) {
  presetBtns.forEach(btn => {
    btn.classList.toggle('active', Number(btn.dataset.minutes) === minutes);
  });
}

presetBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const m = Number(btn.dataset.minutes);
    setDuration(m);
    updateActivePreset(m);
    customInput.value = '';
  });
});

setCustomBtn.addEventListener('click', applyCustom);
customInput.addEventListener('keydown', e => { if (e.key === 'Enter') applyCustom(); });

function applyCustom() {
  const val = parseInt(customInput.value, 10);
  if (!val || val < 1 || val > 180) return;
  setDuration(val);
  updateActivePreset(val); // clears all presets if not matching
  presetBtns.forEach(btn => btn.classList.remove('active'));
}

// ── Init ──────────────────────────────────────────────────────────────────────

syncFromStorage();
