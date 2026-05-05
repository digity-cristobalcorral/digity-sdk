// Copy buttons
document.querySelectorAll('.codeblock__copy').forEach(btn => {
  btn.addEventListener('click', () => {
    const block = btn.closest('.codeblock');
    const pre = block && block.querySelector('pre code');
    if (!pre) return;
    const text = pre.innerText;
    navigator.clipboard.writeText(text).then(() => {
      const label = btn.querySelector('span');
      const original = label ? label.textContent : 'Copy';
      btn.classList.add('is-copied');
      if (label) label.textContent = 'Copied';
      setTimeout(() => {
        btn.classList.remove('is-copied');
        if (label) label.textContent = original;
      }, 1400);
    });
  });
});

// Tab toggles inside codeblock bars (purely visual â actual content swap is out of scope)
document.querySelectorAll('.codeblock__tabs').forEach(tabs => {
  tabs.querySelectorAll('.codeblock__tab').forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.querySelectorAll('.codeblock__tab').forEach(t => {
        t.classList.remove('is-on');
        t.setAttribute('aria-selected', 'false');
      });
      tab.classList.add('is-on');
      tab.setAttribute('aria-selected', 'true');
    });
  });
});

// Search
(function () {
  const overlay = document.getElementById('searchOverlay');
  const input = document.getElementById('searchInput');
  const results = document.getElementById('searchResults');
  const openBtn = document.getElementById('searchBtn');
  if (!overlay || !input || !results) return;

  let index = null;

  async function loadIndex() {
    if (index) return index;
    const base = document.body.dataset.base || '/';
    const res = await fetch(base + 'search/search_index.json');
    const data = await res.json();
    index = data.docs || [];
    return index;
  }

  function highlight(text, query) {
    return text.replace(new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'),
      m => '<mark>' + m + '</mark>');
  }

  function getSnippet(text, query) {
    const i = text.toLowerCase().indexOf(query.toLowerCase());
    if (i === -1) return text.slice(0, 120) + '…';
    const start = Math.max(0, i - 50);
    const end = Math.min(text.length, i + query.length + 100);
    return (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
  }

  function doSearch(query) {
    if (!index || query.length < 2) { results.innerHTML = ''; return; }
    const q = query.toLowerCase();
    const matches = index.filter(d =>
      d.title.toLowerCase().includes(q) || d.text.toLowerCase().includes(q)
    ).slice(0, 8);

    if (!matches.length) {
      results.innerHTML = '<div class="search-empty">No results for "' + query + '"</div>';
      return;
    }

    const base = document.body.dataset.base || '/';
    results.innerHTML = matches.map(d => `
      <a class="search-result" href="${base}${d.location}">
        <div class="search-result__title">${highlight(d.title, query)}</div>
        <div class="search-result__snippet">${highlight(getSnippet(d.text, query), query)}</div>
      </a>`).join('');
  }

  function open() {
    overlay.hidden = false;
    input.value = '';
    results.innerHTML = '';
    setTimeout(() => input.focus(), 30);
    loadIndex();
  }

  function close() { overlay.hidden = true; }

  openBtn.addEventListener('click', open);
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
  input.addEventListener('input', () => doSearch(input.value.trim()));
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); open(); }
    if (e.key === 'Escape') close();
  });
})();

// Page actions dropdown
(function () {
  const btn = document.getElementById('pageActionsBtn');
  const menu = document.getElementById('pageActionsMenu');
  if (!btn || !menu) return;

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = !menu.hidden;
    menu.hidden = open;
    btn.setAttribute('aria-expanded', String(!open));
  });

  document.addEventListener('click', () => {
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
  });

  // Copy page as Markdown
  const copyBtn = document.getElementById('copyMarkdownBtn');
  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      const src = copyBtn.dataset.src;
      const url = 'https://raw.githubusercontent.com/digity-cristobalcorral/digity-sdk/refs/heads/main/docs/' + src;
      try {
        const res = await fetch(url);
        const text = await res.text();
        await navigator.clipboard.writeText(text);
        const strong = copyBtn.querySelector('strong');
        strong.textContent = 'Copied!';
        setTimeout(() => strong.textContent = 'Copy page', 1500);
      } catch {
        alert('Could not copy — open the GitHub link to copy manually.');
      }
    });
  }
})();

// Inject copy buttons on all MkDocs fenced code blocks
document.querySelectorAll('.docs__main pre').forEach(pre => {
  const wrap = document.createElement('div');
  wrap.className = 'code-wrap';
  pre.parentNode.insertBefore(wrap, pre);
  wrap.appendChild(pre);

  const btn = document.createElement('button');
  btn.className = 'code-copy';
  btn.textContent = 'Copy';
  wrap.appendChild(btn);

  btn.addEventListener('click', () => {
    const code = pre.querySelector('code');
    navigator.clipboard.writeText(code ? code.innerText : pre.innerText).then(() => {
      btn.textContent = 'Copied';
      btn.classList.add('is-copied');
      setTimeout(() => {
        btn.textContent = 'Copy';
        btn.classList.remove('is-copied');
      }, 1400);
    });
  });
});

// TOC scroll-spy
(function () {
  const links = [...document.querySelectorAll('.dtoc a[href^="#"]')];
  if (!links.length) return;
  const map = new Map();
  links.forEach(a => {
    const id = a.getAttribute('href').slice(1);
    const target = document.getElementById(id);
    if (target) map.set(target, a);
  });
  if (!map.size) return;

  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        links.forEach(l => l.classList.remove('is-active'));
        const a = map.get(entry.target);
        if (a) a.classList.add('is-active');
      }
    });
  }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 });

  map.forEach((_, el) => io.observe(el));
})();

// Mobile burger toggles the sidebar (very simple)
const burger = document.querySelector('.dnav__burger');
const side = document.querySelector('.docs__side');
if (burger && side) {
  burger.addEventListener('click', () => {
    side.classList.toggle('is-open');
  });
}
