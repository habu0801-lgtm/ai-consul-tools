(() => {
  const STORAGE_KEY_COLOR = 'laserColor';
  const STORAGE_KEY_ENABLED = 'laserEnabled';

  const COLORS = {
    red:    { primary: '#ff2020', glow: 'rgba(255, 32, 32, 0.6)',  inner: 'rgba(255, 200, 200, 0.9)' },
    blue:   { primary: '#2060ff', glow: 'rgba(32, 96, 255, 0.6)',  inner: 'rgba(180, 210, 255, 0.9)' },
    green:  { primary: '#10e050', glow: 'rgba(16, 224, 80, 0.6)',  inner: 'rgba(180, 255, 210, 0.9)' },
    yellow: { primary: '#ffd700', glow: 'rgba(255, 215, 0, 0.6)',  inner: 'rgba(255, 245, 180, 0.9)' },
    purple: { primary: '#cc40ff', glow: 'rgba(204, 64, 255, 0.6)', inner: 'rgba(230, 180, 255, 0.9)' },
  };

  let enabled = false;
  let currentColor = 'red';
  let pointerEl = null;
  let rafId = null;
  let mouseX = -9999;
  let mouseY = -9999;

  // --- DOM setup ---

  function createPointer() {
    // Reuse existing element if present (e.g. after SPA navigation)
    pointerEl = document.getElementById('__laser_pointer__');
    if (!pointerEl) {
      pointerEl = document.createElement('div');
      pointerEl.id = '__laser_pointer__';
      document.documentElement.appendChild(pointerEl);
    }
  }

  function removePointer() {
    if (pointerEl) {
      pointerEl.remove();
      pointerEl = null;
    }
  }

  function applyColor(colorKey) {
    if (!pointerEl) return;
    const c = COLORS[colorKey] || COLORS.red;
    pointerEl.style.setProperty('--lp-primary', c.primary);
    pointerEl.style.setProperty('--lp-glow',    c.glow);
    pointerEl.style.setProperty('--lp-inner',   c.inner);
  }

  // --- Render loop ---

  function renderLoop() {
    if (!pointerEl) return;
    pointerEl.style.transform = `translate(${mouseX}px, ${mouseY}px)`;
    rafId = requestAnimationFrame(renderLoop);
  }

  // --- Event handlers ---

  function onMouseMove(e) {
    mouseX = e.clientX;
    mouseY = e.clientY;
  }

  // Googleスライドの全画面モードではiframe内のポインター座標を
  // ページ座標に変換して追いかける必要があるため、
  // iframe内のスクリプトはそのiframeのclientX/Yをそのまま使う。
  // all_frames:true により各iframeに独立してcontent scriptが挿入されるので
  // 追加の変換処理は不要。

  // --- Fullscreen change: re-attach pointer when entering/exiting fullscreen ---

  function onFullscreenChange() {
    if (!enabled) return;
    // ポインター要素が取り除かれていたら再生成する
    if (!document.getElementById('__laser_pointer__')) {
      createPointer();
      applyColor(currentColor);
    }
  }

  document.addEventListener('fullscreenchange', onFullscreenChange);
  document.addEventListener('webkitfullscreenchange', onFullscreenChange);

  // --- Enable / Disable ---

  function enable() {
    if (enabled) return;
    enabled = true;
    createPointer();
    applyColor(currentColor);
    document.documentElement.classList.add('__laser_active__');
    window.addEventListener('mousemove', onMouseMove, { passive: true });
    rafId = requestAnimationFrame(renderLoop);
  }

  function disable() {
    if (!enabled) return;
    enabled = false;
    cancelAnimationFrame(rafId);
    window.removeEventListener('mousemove', onMouseMove);
    document.documentElement.classList.remove('__laser_active__');
    removePointer();
  }

  // --- Message listener (from popup / background) ---

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === 'SET_ENABLED') {
      msg.enabled ? enable() : disable();
    }
    if (msg.type === 'SET_COLOR') {
      currentColor = msg.color;
      applyColor(currentColor);
    }
  });

  // --- Restore state on page load ---

  chrome.storage.local.get([STORAGE_KEY_ENABLED, STORAGE_KEY_COLOR], (result) => {
    currentColor = result[STORAGE_KEY_COLOR] || 'red';
    if (result[STORAGE_KEY_ENABLED]) enable();
  });
})();
