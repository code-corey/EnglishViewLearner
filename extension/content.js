(function () {
  'use strict';

  const LEVEL_INDEX = { A1: 1, A2: 2, B1: 3, B2: 4, C1: 5 };

  const STOP_WORDS = new Set([
    '的', '了', '吗', '呢', '啊', '哦', '又', '也', '都', '很', '太',
    '着', '过', '吧', '呀', '嘛', '么', '所', '被', '把', '让', '给',
    '在', '从', '向', '到', '为', '以', '与', '和', '或', '但', '而',
    '是', '有', '这', '那', '个', '一', '不', '没', '会', '能', '要'
  ]);

  const SKIP_TAGS = new Set([
    'SCRIPT', 'STYLE', 'NOSCRIPT', 'IFRAME', 'TEXTAREA', 'INPUT',
    'SELECT', 'OPTION', 'CODE', 'PRE', 'SVG', 'MATH'
  ]);

  const CHINESE_RE = /[\u4e00-\u9fff\u3400-\u4dbf]/;
  const DEFAULT_UNDERLINE_COLOR = '#b794f6';

  let gradedDict = null;
  let userLevel = 'B1';
  let userLevelIndex = 3;
  let isEnabled = true;
  let underlineColor = DEFAULT_UNDERLINE_COLOR;
  let replaceCount = 0;
  let highestLevelIndex = 0;
  let isProcessing = false;
  let pendingProcess = false;
  let fabRoot = null;

  const segmenter = typeof Intl !== 'undefined' && Intl.Segmenter
    ? new Intl.Segmenter('zh-CN', { granularity: 'word' })
    : null;

  const observerOptions = { root: null, rootMargin: '200px 0px', threshold: 0 };

  const intersectionObserver = new IntersectionObserver((entries) => {
    if (!isEnabled) return;
    for (const entry of entries) {
      if (entry.isIntersecting) {
        intersectionObserver.unobserve(entry.target);
        scheduleProcess(entry.target);
      }
    }
  }, observerOptions);

  const mutationObserver = new MutationObserver((mutations) => {
    if (!isEnabled) return;
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          observeElement(node);
        } else if (node.nodeType === Node.TEXT_NODE && node.parentElement) {
          observeElement(node.parentElement);
        }
      }
    }
  });

  function scheduleProcess(root) {
    if (!isEnabled || !gradedDict) return;
    if (isProcessing) {
      pendingProcess = true;
      return;
    }

    const run = () => {
      isProcessing = true;
      try {
        processRoot(root);
      } finally {
        isProcessing = false;
        if (pendingProcess) {
          pendingProcess = false;
          scheduleProcess(document.body);
        }
      }
    };

    if (typeof requestIdleCallback === 'function') {
      requestIdleCallback(run, { timeout: 200 });
    } else {
      setTimeout(run, 0);
    }
  }

  function shouldSkipElement(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) return true;
    if (el.classList && el.classList.contains('neon-lingo-translated')) return true;
    if (el.closest && el.closest('.neon-lingo-translated')) return true;
    if (SKIP_TAGS.has(el.tagName)) return true;
    if (el.isContentEditable) return true;
    let node = el;
    while (node) {
      if (node.nodeType === Node.ELEMENT_NODE && SKIP_TAGS.has(node.tagName)) return true;
      node = node.parentElement;
    }
    return false;
  }

  function containsChinese(text) {
    return CHINESE_RE.test(text);
  }

  function isSingleCharWord(word) {
    return [...word].length === 1;
  }

  function segmentText(text) {
    if (segmenter) {
      return [...segmenter.segment(text)];
    }
    const segments = [];
    let i = 0;
    while (i < text.length) {
      const ch = text[i];
      if (CHINESE_RE.test(ch)) {
        let j = i + 1;
        while (j < text.length && CHINESE_RE.test(text[j])) j++;
        segments.push({ segment: text.slice(i, j), index: i, isWordLike: true });
        i = j;
      } else {
        let j = i + 1;
        while (j < text.length && !CHINESE_RE.test(text[j])) j++;
        segments.push({ segment: text.slice(i, j), index: i, isWordLike: false });
        i = j;
      }
    }
    return segments;
  }

  function lookupWord(word) {
    return gradedDict[word] || null;
  }

  function shouldReplace(word, entry) {
    if (!entry || !entry.en || !entry.level) return false;
    if (STOP_WORDS.has(word)) return false;
    if (isSingleCharWord(word)) return false;
    const wordLevelIndex = LEVEL_INDEX[entry.level];
    if (!wordLevelIndex) return false;
    return wordLevelIndex <= userLevelIndex;
  }

  function createTranslatedSpan(word, entry) {
    const span = document.createElement('span');
    span.className = 'neon-lingo-translated';
    span.setAttribute('data-original', word);
    span.textContent = entry.en;
    return span;
  }

  function processTextNode(textNode) {
    const text = textNode.textContent;
    if (!text || !containsChinese(text)) return false;

    const parent = textNode.parentElement;
    if (!parent || shouldSkipElement(parent)) return false;

    const segments = segmentText(text);
    const fragment = document.createDocumentFragment();
    let replaced = false;

    for (const seg of segments) {
      const word = seg.segment;
      const isWordLike = seg.isWordLike !== false && containsChinese(word);

      if (isWordLike) {
        const entry = lookupWord(word);
        if (shouldReplace(word, entry)) {
          fragment.appendChild(createTranslatedSpan(word, entry));
          replaceCount++;
          updateFabCount();
          const li = LEVEL_INDEX[entry.level] || 0;
          if (li > highestLevelIndex) highestLevelIndex = li;
          replaced = true;
        } else {
          fragment.appendChild(document.createTextNode(word));
        }
      } else {
        fragment.appendChild(document.createTextNode(word));
      }
    }

    if (!replaced) return false;

    parent.replaceChild(fragment, textNode);
    return true;
  }

  function collectTextNodes(root) {
    const nodes = [];
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.textContent || !containsChinese(node.textContent)) {
          return NodeFilter.FILTER_REJECT;
        }
        const parent = node.parentElement;
        if (!parent || shouldSkipElement(parent)) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    let node;
    while ((node = walker.nextNode())) {
      nodes.push(node);
    }
    return nodes;
  }

  function processRoot(root) {
    if (!isEnabled || !gradedDict || !root) return;
    const textNodes = collectTextNodes(root);
    for (const textNode of textNodes) {
      if (textNode.isConnected) {
        processTextNode(textNode);
      }
    }
  }

  function observeElement(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) return;
    if (shouldSkipElement(el)) return;
    if (el.dataset && el.dataset.neonLingoObserved) return;
    el.dataset.neonLingoObserved = '1';
    intersectionObserver.observe(el);
  }

  function observeDocument() {
    if (!document.body) return;
    observeElement(document.body);
    const elements = document.body.querySelectorAll('*');
    for (const el of elements) {
      observeElement(el);
    }
  }

  function revertTranslations(root) {
    const spans = root.querySelectorAll('.neon-lingo-translated');
    spans.forEach((span) => {
      const original = span.getAttribute('data-original') || span.textContent;
      span.replaceWith(document.createTextNode(original));
    });
    root.normalize();
  }

  function resetStats() {
    replaceCount = 0;
    highestLevelIndex = 0;
    updateFabCount();
  }

  function indexToLevel(index) {
    const map = { 1: 'A1', 2: 'A2', 3: 'B1', 4: 'B2', 5: 'C1' };
    return map[index] || '—';
  }

  function hexToRgb(hex) {
    const match = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex || '');
    if (!match) return null;
    return {
      r: parseInt(match[1], 16),
      g: parseInt(match[2], 16),
      b: parseInt(match[3], 16)
    };
  }

  function applyUnderlineColor(color) {
    const value = color || DEFAULT_UNDERLINE_COLOR;
    underlineColor = value;
    const root = document.documentElement;
    root.style.setProperty('--neon-lingo-underline-color', value);
    const rgb = hexToRgb(value);
    if (rgb) {
      root.style.setProperty(
        '--neon-lingo-underline-hover',
        `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.12)`
      );
    }
  }

  let tooltipEl = null;
  let tooltipTarget = null;
  let tooltipBound = false;

  function ensureTooltip() {
    if (tooltipEl) return tooltipEl;
    tooltipEl = document.createElement('div');
    tooltipEl.id = 'neon-lingo-tooltip';
    tooltipEl.className = 'neon-lingo-tooltip';
    tooltipEl.setAttribute('role', 'tooltip');
    document.documentElement.appendChild(tooltipEl);
    return tooltipEl;
  }

  function hideTooltip() {
    tooltipTarget = null;
    if (tooltipEl) tooltipEl.classList.remove('visible');
  }

  function positionTooltip(target, tip) {
    const rect = target.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();
    const gap = 8;

    let left = rect.left + rect.width / 2 - tipRect.width / 2;
    let top = rect.top - tipRect.height - gap;

    if (top < 8) {
      top = rect.bottom + gap;
      tip.dataset.placement = 'bottom';
    } else {
      tip.dataset.placement = 'top';
    }

    left = Math.max(8, Math.min(left, window.innerWidth - tipRect.width - 8));
    tip.style.left = `${left}px`;
    tip.style.top = `${top}px`;
  }

  function showTooltip(target) {
    const text = target.getAttribute('data-original');
    if (!text) return;

    tooltipTarget = target;
    const tip = ensureTooltip();
    tip.textContent = text;
    tip.classList.add('visible');
    positionTooltip(target, tip);
  }

  function bindTooltipEvents() {
    if (tooltipBound) return;
    tooltipBound = true;

    document.addEventListener('mouseover', (event) => {
      const target = event.target.closest?.('.neon-lingo-translated');
      if (target && target !== tooltipTarget) {
        showTooltip(target);
      }
    }, true);

    document.addEventListener('mouseout', (event) => {
      const target = event.target.closest?.('.neon-lingo-translated');
      if (!target || target !== tooltipTarget) return;
      const related = event.relatedTarget;
      if (!related || !target.contains(related)) {
        hideTooltip();
      }
    }, true);

    window.addEventListener('scroll', hideTooltip, true);
    window.addEventListener('resize', hideTooltip);
  }

  function handlePanelRequest(message) {
    if (message.type === 'GET_STATS') {
      return {
        ok: true,
        replaceCount,
        highestLevel: highestLevelIndex ? indexToLevel(highestLevelIndex) : '—',
        isEnabled,
        userLevel
      };
    }

    if (message.type === 'REFRESH') {
      if (isEnabled) start();
      else stop();
      return { ok: true };
    }

    if (message.type === 'APPLY_THEME') {
      applyUnderlineColor(message.underlineColor);
      return { ok: true };
    }

    return null;
  }

  function updateFabCount() {
    if (!fabRoot) return;
    const countEl = fabRoot.querySelector('.neon-lingo-fab-count');
    if (countEl) countEl.textContent = String(replaceCount);
  }

  function updateFabState() {
    if (!fabRoot) return;

    const check = fabRoot.querySelector('.neon-lingo-fab-check');
    const toggle = fabRoot.querySelector('.neon-lingo-fab-toggle');
    const levelSelect = fabRoot.querySelector('.neon-lingo-fab-level');

    if (check) {
      check.classList.toggle('is-off', !isEnabled);
    }
    if (toggle) {
      toggle.checked = isEnabled;
    }
    if (levelSelect && levelSelect.value !== userLevel) {
      levelSelect.value = userLevel;
    }
  }

  function createFloatingPanel() {
    if (document.getElementById('neon-lingo-fab')) return;

    fabRoot = document.createElement('div');
    fabRoot.id = 'neon-lingo-fab';
    fabRoot.className = 'neon-lingo-fab';

    fabRoot.innerHTML = `
      <div class="neon-lingo-fab-drawer" aria-hidden="true">
        <div class="neon-lingo-drawer-row">
          <span class="neon-lingo-drawer-label">是否打开功能</span>
          <label class="neon-lingo-switch">
            <input type="checkbox" class="neon-lingo-fab-toggle" checked>
            <span class="neon-lingo-switch-slider"></span>
          </label>
        </div>
        <div class="neon-lingo-drawer-row">
          <span class="neon-lingo-drawer-label">翻译等级</span>
          <select class="neon-lingo-fab-level" aria-label="翻译等级">
            <option value="A1">A1</option>
            <option value="A2">A2</option>
            <option value="B1" selected>B1</option>
            <option value="B2">B2</option>
            <option value="C1">C1</option>
          </select>
        </div>
      </div>
      <button type="button" class="neon-lingo-fab-trigger" aria-label="沉浸式学习英语">
        <span class="neon-lingo-fab-logo">
          <span class="neon-lingo-fab-n">E</span>
          <span class="neon-lingo-fab-check" aria-hidden="true">✓</span>
        </span>
        <span class="neon-lingo-fab-count">0</span>
      </button>
    `;

    const drawer = fabRoot.querySelector('.neon-lingo-fab-drawer');
    const toggle = fabRoot.querySelector('.neon-lingo-fab-toggle');
    const levelSelect = fabRoot.querySelector('.neon-lingo-fab-level');

    fabRoot.addEventListener('mouseenter', () => {
      fabRoot.classList.add('is-open');
      drawer.setAttribute('aria-hidden', 'false');
    });

    fabRoot.addEventListener('mouseleave', () => {
      fabRoot.classList.remove('is-open');
      drawer.setAttribute('aria-hidden', 'true');
    });

    toggle.addEventListener('change', async () => {
      isEnabled = toggle.checked;
      await chrome.storage.local.set({ isEnabled });
      updateFabState();
      if (isEnabled) start();
      else stop();
    });

    levelSelect.addEventListener('change', async () => {
      userLevel = levelSelect.value;
      userLevelIndex = LEVEL_INDEX[userLevel] || 3;
      await chrome.storage.local.set({ userLevel });
      if (isEnabled) start();
    });

    document.documentElement.appendChild(fabRoot);
    updateFabState();
    updateFabCount();
  }

  function applySettings(settings) {
    userLevel = settings.userLevel || 'B1';
    userLevelIndex = LEVEL_INDEX[userLevel] || 3;
    isEnabled = settings.isEnabled !== false;
    applyUnderlineColor(settings.underlineColor || DEFAULT_UNDERLINE_COLOR);
    updateFabState();
  }

  function start() {
    if (!document.body) return;
    hideTooltip();
    resetStats();
    revertTranslations(document.body);
    document.querySelectorAll('[data-neon-lingo-observed]').forEach((el) => {
      delete el.dataset.neonLingoObserved;
    });
    if (!isEnabled) return;
    observeDocument();
    scheduleProcess(document.body);
  }

  function stop() {
    intersectionObserver.disconnect();
    hideTooltip();
    revertTranslations(document.body);
    resetStats();
  }

  async function init() {
    try {
      const [dictResponse, settingsResponse] = await Promise.all([
        chrome.runtime.sendMessage({ type: 'GET_DICT' }),
        chrome.runtime.sendMessage({ type: 'GET_SETTINGS' })
      ]);

      if (!dictResponse?.ok) {
        console.error('[NeonLingo] Dictionary load failed:', dictResponse?.error);
        return;
      }

      gradedDict = dictResponse.dict;
      applySettings(settingsResponse || {});
      bindTooltipEvents();
      createFloatingPanel();

      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
      } else {
        start();
      }

      mutationObserver.observe(document.documentElement, {
        childList: true,
        subtree: true
      });
    } catch (err) {
      console.error('[NeonLingo] Init failed:', err);
    }
  }

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return;
    if (changes.userLevel) {
      userLevel = changes.userLevel.newValue || 'B1';
      userLevelIndex = LEVEL_INDEX[userLevel] || 3;
    }
    if (changes.isEnabled !== undefined) {
      isEnabled = changes.isEnabled.newValue !== false;
    }
    if (changes.underlineColor) {
      applyUnderlineColor(changes.underlineColor.newValue);
    }
    if (changes.userLevel || changes.isEnabled !== undefined) {
      updateFabState();
      if (isEnabled) {
        start();
      } else {
        stop();
      }
    }
  });

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    const payload = handlePanelRequest(message);
    if (payload) sendResponse(payload);
    return false;
  });

  init();
})();
