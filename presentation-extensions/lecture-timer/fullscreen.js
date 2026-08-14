const CIRCUMFERENCE = 2 * Math.PI * 88;

const timeDisplay = document.getElementById('timeDisplay');
const statusLabel = document.getElementById('statusLabel');
const ringProgress = document.getElementById('ringProgress');
const startBtn = document.getElementById('startBtn');
const resetBtn = document.getElementById('resetBtn');
const iconPlay = document.getElementById('iconPlay');
const iconPause = document.getElementById('iconPause');

let totalSeconds = 25 * 60;
let remainingSeconds = totalSeconds;
let running = false;
let intervalId = null;

function render() {
  const m = Math.floor(remainingSeconds / 60);
  const s = remainingSeconds % 60;
  timeDisplay.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

  const pct = totalSeconds > 0 ? remainingSeconds / totalSeconds : 1;
  ringProgress.style.strokeDashoffset = CIRCUMFERENCE * (1 - pct);

  ringProgress.classList.remove('warn', 'done');
  if (remainingSeconds <= 0) {
    ringProgress.classList.add('done');
  } else if (pct <= 0.2) {
    ringProgress.classList.add('warn');
  }

  if (running) statusLabel.textContent = 'IN PROGRESS';
  else if (remainingSeconds === totalSeconds) { statusLabel.textContent = 'READY'; document.body.classList.remove('done'); }
  else if (remainingSeconds > 0) statusLabel.textContent = 'PAUSED';
}

function startLocalTick() {
  clearInterval(intervalId);
  intervalId = setInterval(() => {
    if (remainingSeconds <= 0) {
      clearInterval(intervalId);
      running = false;
      remainingSeconds = 0;
      document.body.classList.add('done');
      statusLabel.textContent = "TIME'S UP";
      ringProgress.classList.add('done');
      showPlayIcon();
      return;
    }
    remainingSeconds--;
    render();
    saveToStorage();
  }, 1000);
}

function showPlayIcon() { iconPlay.style.display = ''; iconPause.style.display = 'none'; }
function showPauseIcon() { iconPlay.style.display = 'none'; iconPause.style.display = ''; }

function saveToStorage() {
  chrome.storage.local.set({
    total: totalSeconds,
    remaining: remainingSeconds,
    running,
    startedAt: running ? Date.now() : null,
  });
}

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

// Keyboard shortcuts
document.addEventListener('keydown', e => {
  if (e.code === 'Space') { e.preventDefault(); startBtn.click(); }
  if (e.code === 'KeyR') resetBtn.click();
});

// Sync initial state
chrome.storage.local.get(['total', 'remaining', 'running', 'startedAt'], (data) => {
  if (data.total == null) return;
  totalSeconds = data.total;

  if (data.running && data.startedAt != null) {
    const elapsed = Math.floor((Date.now() - data.startedAt) / 1000);
    remainingSeconds = Math.max(0, data.remaining - elapsed);
    if (remainingSeconds > 0) { running = true; startLocalTick(); showPauseIcon(); }
    else { remainingSeconds = 0; document.body.classList.add('done'); statusLabel.textContent = "TIME'S UP"; }
  } else {
    remainingSeconds = data.remaining ?? data.total;
  }
  render();
});
