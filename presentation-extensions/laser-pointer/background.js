chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'BROADCAST') {
    // Forward SET_ENABLED / SET_COLOR to all tabs
    chrome.tabs.query({}, (tabs) => {
      for (const tab of tabs) {
        if (tab.id) {
          chrome.tabs.sendMessage(tab.id, msg.payload).catch(() => {});
        }
      }
    });
    sendResponse({ ok: true });
  }
  return true;
});
