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
      const url = 'https://raw.githubusercontent.com/digity-cristobalcorral/digity-sdk/main/docs/' + src;
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
