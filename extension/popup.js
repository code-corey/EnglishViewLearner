const levelSelect = document.getElementById('levelSelect');
const toggleSwitch = document.getElementById('toggleSwitch');
const levelOnlySwitch = document.getElementById('levelOnlySwitch');
const statusText = document.getElementById('statusText');
const replaceCountEl = document.getElementById('replaceCount');
const highestLevelEl = document.getElementById('highestLevel');
const colorPresetsEl = document.getElementById('colorPresets');
const colorPicker = document.getElementById('colorPicker');
const colorValueEl = document.getElementById('colorValue');
const colorPreview = document.getElementById('colorPreview');

const DEFAULT_UNDERLINE_COLOR = '#b794f6';
const isEmbedded = window.self !== window.top;

const PRESET_COLORS = [
  { value: '#b794f6', label: '淡紫' },
  { value: '#ff9800', label: '橙色' },
  { value: '#42a5f5', label: '蓝色' },
  { value: '#66bb6a', label: '绿色' },
  { value: '#ef5350', label: '红色' },
  { value: '#f48fb1', label: '粉色' },
  { value: '#9e9e9e', label: '灰色' }
];

let isEnabled = true;
let currentLevelOnly = false;
let underlineColor = DEFAULT_UNDERLINE_COLOR;

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function sendToPage(message) {
  if (isEmbedded) {
    return new Promise((resolve) => {
      const requestId = `${Date.now()}-${Math.random()}`;
      function onReply(event) {
        if (event.data?.source !== 'neon-lingo-content') return;
        if (event.data.requestId !== requestId) return;
        window.removeEventListener('message', onReply);
        resolve(event.data.payload);
      }
      window.addEventListener('message', onReply);
      window.parent.postMessage({ source: 'neon-lingo-panel', requestId, ...message }, '*');
    });
  }

  const tab = await getActiveTab();
  if (!tab?.id) return null;
  try {
    return await chrome.tabs.sendMessage(tab.id, message);
  } catch {
    return null;
  }
}

function normalizeColor(color) {
  if (!color || typeof color !== 'string') return DEFAULT_UNDERLINE_COLOR;
  const value = color.trim();
  if (/^#[0-9a-fA-F]{6}$/.test(value)) return value.toLowerCase();
  if (/^[0-9a-fA-F]{6}$/.test(value)) return `#${value.toLowerCase()}`;
  return DEFAULT_UNDERLINE_COLOR;
}

function updateColorUI(color) {
  underlineColor = normalizeColor(color);
  colorPicker.value = underlineColor;
  colorValueEl.textContent = underlineColor.toUpperCase();
  colorPreview.style.setProperty('--preview-underline', underlineColor);
  document.documentElement.style.setProperty('--preview-underline', underlineColor);

  colorPresetsEl.querySelectorAll('.color-swatch').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.color === underlineColor);
  });
}

function renderColorPresets() {
  colorPresetsEl.innerHTML = '';
  PRESET_COLORS.forEach(({ value, label }) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'color-swatch';
    btn.dataset.color = value;
    btn.style.backgroundColor = value;
    btn.style.color = value;
    btn.title = label;
    btn.setAttribute('aria-label', label);
    btn.addEventListener('click', () => saveUnderlineColor(value));
    colorPresetsEl.appendChild(btn);
  });
}

async function applyColorToPage(color) {
  await sendToPage({ type: 'APPLY_THEME', underlineColor: color });
}

async function saveUnderlineColor(color) {
  const normalized = normalizeColor(color);
  await chrome.storage.local.set({ underlineColor: normalized });
  updateColorUI(normalized);
  await applyColorToPage(normalized);
}

async function loadSettings() {
  const data = await chrome.storage.local.get(['userLevel', 'isEnabled', 'underlineColor', 'currentLevelOnly']);
  const userLevel = data.userLevel || 'B1';
  isEnabled = data.isEnabled !== false;
  currentLevelOnly = data.currentLevelOnly === true;

  levelSelect.value = userLevel;
  updateColorUI(data.underlineColor || DEFAULT_UNDERLINE_COLOR);
  updateToggleUI();
}

function updateToggleUI() {
  if (toggleSwitch) {
    toggleSwitch.checked = isEnabled;
  }
  if (levelOnlySwitch) {
    levelOnlySwitch.checked = currentLevelOnly;
  }
}

async function refreshStats() {
  if (!isEmbedded) {
    const tab = await getActiveTab();
    if (!tab?.id || tab.url?.startsWith('chrome://') || tab.url?.startsWith('edge://')) {
      replaceCountEl.textContent = '—';
      highestLevelEl.textContent = '—';
      return;
    }
  }

  const stats = await sendToPage({ type: 'GET_STATS' });
  if (stats?.ok) {
    replaceCountEl.textContent = String(stats.replaceCount);
    highestLevelEl.textContent = stats.highestLevel;
    if (stats.isEnabled !== undefined) {
      isEnabled = stats.isEnabled;
      updateToggleUI();
    }
  } else {
    replaceCountEl.textContent = '—';
    highestLevelEl.textContent = '—';
  }
}

levelSelect.addEventListener('change', async () => {
  const userLevel = levelSelect.value;
  await chrome.storage.local.set({ userLevel });
  await sendToPage({ type: 'REFRESH' });
  refreshStats();
});

colorPicker.addEventListener('input', (event) => {
  saveUnderlineColor(event.target.value);
});

toggleSwitch.addEventListener('change', async () => {
  isEnabled = toggleSwitch.checked;
  await chrome.storage.local.set({ isEnabled });
  updateToggleUI();
  await sendToPage({ type: 'REFRESH' });
  refreshStats();
});

levelOnlySwitch.addEventListener('change', async () => {
  currentLevelOnly = levelOnlySwitch.checked;
  await chrome.storage.local.set({ currentLevelOnly });
  updateToggleUI();
  await sendToPage({ type: 'REFRESH' });
  refreshStats();
});

if (isEmbedded) {
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) refreshStats();
  });
}

renderColorPresets();
loadSettings().then(refreshStats);
