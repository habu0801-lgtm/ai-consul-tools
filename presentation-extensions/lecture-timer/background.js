// Background service worker — keeps timer state alive across popup open/close.
// The popup handles the actual tick display; we just persist state here.

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    total: 25 * 60,
    remaining: 25 * 60,
    running: false,
    startedAt: null,
  });
});
