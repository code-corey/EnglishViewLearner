const DEFAULT_LEVEL = 'B1';
const DEFAULT_ENABLED = true;
const DEFAULT_UNDERLINE_COLOR = '#b794f6';

let gradedDict = null;
let dictLoadPromise = null;

async function loadDictionary() {
  if (gradedDict) return gradedDict;
  if (dictLoadPromise) return dictLoadPromise;

  dictLoadPromise = (async () => {
    const url = chrome.runtime.getURL('dict/graded_dict.json');
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load dictionary: ${response.status}`);
    }
    gradedDict = await response.json();
    return gradedDict;
  })();

  return dictLoadPromise;
}

chrome.runtime.onInstalled.addListener(async () => {
  const stored = await chrome.storage.local.get(['userLevel', 'isEnabled', 'underlineColor']);
  const updates = {};
  if (!stored.userLevel) updates.userLevel = DEFAULT_LEVEL;
  if (stored.isEnabled === undefined) updates.isEnabled = DEFAULT_ENABLED;
  if (!stored.underlineColor) updates.underlineColor = DEFAULT_UNDERLINE_COLOR;
  if (Object.keys(updates).length > 0) {
    await chrome.storage.local.set(updates);
  }
  loadDictionary().catch(console.error);
});

chrome.runtime.onStartup.addListener(() => {
  loadDictionary().catch(console.error);
});

loadDictionary().catch(console.error);

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'GET_DICT') {
    loadDictionary()
      .then((dict) => sendResponse({ ok: true, dict }))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  if (message.type === 'GET_SETTINGS') {
    chrome.storage.local.get(['userLevel', 'isEnabled', 'underlineColor']).then((data) => {
      sendResponse({
        ok: true,
        userLevel: data.userLevel || DEFAULT_LEVEL,
        isEnabled: data.isEnabled !== false,
        underlineColor: data.underlineColor || DEFAULT_UNDERLINE_COLOR
      });
    });
    return true;
  }

  if (message.type === 'SET_SETTINGS') {
    const updates = {};
    if (message.userLevel !== undefined) updates.userLevel = message.userLevel;
    if (message.isEnabled !== undefined) updates.isEnabled = message.isEnabled;
    if (message.underlineColor !== undefined) updates.underlineColor = message.underlineColor;
    chrome.storage.local.set(updates).then(() => sendResponse({ ok: true }));
    return true;
  }

  return false;
});
