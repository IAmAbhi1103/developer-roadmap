/* Java Full-Stack Notes — page behaviour: TOC, search, revised ticks, code, diagrams, theme */
(function () {
  'use strict';
  var doc = document, root = doc.documentElement, body = doc.body;
  var THEME_KEY = 'rm-theme';
  var topic = body.getAttribute('data-topic') || '';
  var REV_KEY = 'notes-revised-' + topic;
  var MERMAID_SRC = 'https://cdn.jsdelivr.net/npm/mermaid@10.9.8/dist/mermaid.min.js';
  var MERMAID_SRI = 'sha384-N3QqR/7q+xm3BGX+CBbNI8AUmRRqcsDzToy+0z1NLDI0QmTKW8zvwLvqulJgk3dP';
  var $ = function (s, el) { return (el || doc).querySelector(s); };
  var $$ = function (s, el) { return [].slice.call((el || doc).querySelectorAll(s)); };

  function getItem(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function setItem(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage blocked */ } }
  function svg(id, cls) {
    return '<svg class="ico' + (cls ? ' ' + cls : '') + '" aria-hidden="true"><use href="#' + id + '"/></svg>';
  }

  /* ---------- theme ---------- */
  function isDark() { return root.getAttribute('data-theme') === 'dark'; }
  $$('[data-theme-toggle]').forEach(function (b) {
    b.addEventListener('click', function () {
      var t = isDark() ? 'light' : 'dark';
      root.setAttribute('data-theme', t);
      setItem(THEME_KEY, t);
      doc.dispatchEvent(new CustomEvent('notes:theme'));
    });
  });

  /* ---------- home page: progress per topic ---------- */
  $$('[data-progress-for]').forEach(function (el) {
    var slug = el.getAttribute('data-progress-for');
    var total = +el.getAttribute('data-total') || 0;
    var n = 0;
    try { n = Object.keys(JSON.parse(getItem('notes-revised-' + slug) || '{}') || {}).length; } catch (e) { n = 0; }
    var bar = $('i', el), txt = doc.querySelector('[data-progress-text="' + slug + '"]');
    if (bar && total) bar.style.width = Math.min(100, n / total * 100) + '%';
    if (txt) txt.textContent = n + ' / ' + total + ' revised';
  });

  var notes = $('.notes');
  if (!notes) { return; }

  /* ---------- code blocks: header, language label, copy ---------- */
  var LANG = {
    java: 'Java', kotlin: 'Kotlin', groovy: 'Groovy', sql: 'SQL', bash: 'Bash', shell: 'Terminal',
    plaintext: 'Text', javascript: 'JavaScript', jsx: 'JSX', typescript: 'TypeScript', tsx: 'TSX',
    xml: 'XML', html: 'HTML', css: 'CSS', scss: 'SCSS', json: 'JSON', yaml: 'YAML',
    properties: 'Properties', ini: 'INI', dockerfile: 'Dockerfile', nginx: 'Nginx', http: 'HTTP',
    diff: 'Diff', markdown: 'Markdown', python: 'Python'
  };
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext !== false) {
      return navigator.clipboard.writeText(text).catch(function () { return fallbackCopy(text); });
    }
    return fallbackCopy(text);
  }
  function fallbackCopy(text) {
    return new Promise(function (resolve) {
      var ta = doc.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      body.appendChild(ta); ta.select();
      try { doc.execCommand('copy'); } catch (e) { /* ignore */ }
      body.removeChild(ta); resolve();
    });
  }
  var codeEls = [];
  $$('pre > code', notes).forEach(function (code) {
    var pre = code.parentNode;
    if (pre.classList.contains('mermaid') || pre.classList.contains('diagram')) return;
    var m = code.className.match(/language-([\w-]+)/);
    var lang = m ? m[1] : 'plaintext';
    var isOut = pre.classList.contains('out');
    var wrap = doc.createElement('div');
    wrap.className = 'code' + (isOut ? ' is-out' : '');
    var head = doc.createElement('div');
    head.className = 'code-h';
    var lab = doc.createElement('span');
    lab.className = 'code-lang';
    lab.textContent = isOut ? (pre.getAttribute('data-title') || 'Output') : (LANG[lang] || lang);
    head.appendChild(lab);
    var title = pre.getAttribute('data-title');
    if (title && !isOut) {
      var t = doc.createElement('span');
      t.className = 'code-title'; t.textContent = title; t.title = title;
      head.appendChild(t);
    }
    var btn = doc.createElement('button');
    btn.type = 'button'; btn.className = 'copy'; btn.textContent = 'Copy';
    btn.setAttribute('aria-label', 'Copy code');
    btn.addEventListener('click', function () {
      var text = code.textContent;
      if (lang === 'shell') {
        var cmds = text.split('\n').filter(function (l) { return /^\s*\$ /.test(l); })
          .map(function (l) { return l.replace(/^\s*\$ /, ''); });
        if (cmds.length) text = cmds.join('\n');
      }
      copyText(text).then(function () {
        btn.textContent = 'Copied'; btn.classList.add('ok');
        setTimeout(function () { btn.textContent = 'Copy'; btn.classList.remove('ok'); }, 1400);
      });
    });
    head.appendChild(btn);
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(head);
    wrap.appendChild(pre);
    if (!isOut && lang !== 'plaintext') codeEls.push(code);
  });

  /* syntax highlighting, lazily as blocks come near the viewport */
  if (window.hljs && codeEls.length) {
    try { window.hljs.configure({ ignoreUnescapedHTML: true }); } catch (e) { /* old API */ }
    var hl = function (el) {
      if (el.getAttribute('data-hl')) return;
      el.setAttribute('data-hl', '1');
      try { window.hljs.highlightElement(el); } catch (e) { /* unknown language */ }
    };
    if ('IntersectionObserver' in window) {
      var hio = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { hl(en.target); hio.unobserve(en.target); } });
      }, { rootMargin: '1200px 0px' });
      codeEls.forEach(function (el) { hio.observe(el); });
    } else {
      codeEls.forEach(hl);
    }
  }

  /* tables: labels for the stacked phone layout */
  $$('table.tbl', notes).forEach(function (t) {
    var hs = $$('thead th', t).map(function (th) { return th.textContent.trim(); });
    $$('tbody tr', t).forEach(function (tr) {
      [].forEach.call(tr.children, function (td, i) {
        if (hs[i] && !td.hasAttribute('data-label')) td.setAttribute('data-label', hs[i]);
      });
    });
  });

  /* ---------- revised ticks ---------- */
  var rev = {};
  try { rev = JSON.parse(getItem(REV_KEY) || '{}') || {}; } catch (e) { rev = {}; }
  var tocLinks = {};
  var modules = $$('section.module', notes);
  var topics = $$('article.topic:not(.recap)', notes);
  function saveRev() { setItem(REV_KEY, JSON.stringify(rev)); }
  function refreshCounts() {
    var done = 0;
    topics.forEach(function (a) { if (rev[a.id]) done++; });
    var c = $('#rev-count'), f = $('#rev-fill');
    if (c) c.textContent = done;
    if (f) f.style.width = (topics.length ? done / topics.length * 100 : 0) + '%';
    modules.forEach(function (sec) {
      var all = $$('article.topic:not(.recap)', sec);
      var d = all.filter(function (a) { return rev[a.id]; }).length;
      var cnt = doc.querySelector('.toc-m[data-mod="' + sec.id + '"] .cnt');
      if (cnt) cnt.textContent = all.length ? d + '/' + all.length : '';
    });
  }
  topics.forEach(function (a) {
    var h3 = $('h3', a);
    if (!h3 || !a.id) return;
    var b = doc.createElement('button');
    b.type = 'button'; b.className = 'rev';
    var set = function (on) {
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
      b.innerHTML = svg('i-check') + '<span>' + (on ? 'Revised' : 'Mark revised') + '</span>';
      var l = tocLinks[a.id];
      if (l) l.classList.toggle('done', !!on);
    };
    b.addEventListener('click', function () {
      if (rev[a.id]) { delete rev[a.id]; } else { rev[a.id] = Date.now(); }
      saveRev(); set(!!rev[a.id]); refreshCounts();
    });
    h3.insertAdjacentElement('afterend', b);
    a._setRev = set;
  });

  /* Q&A: expand / collapse all */
  $$('article.topic.recap', notes).forEach(function (a) {
    var qs = $$('details.qa', a);
    if (qs.length < 3) return;
    a.classList.add('has-qa');
    var b = doc.createElement('button');
    b.type = 'button'; b.className = 'qa-all'; b.textContent = 'Open all answers';
    b.addEventListener('click', function () {
      var open = !qs.every(function (d) { return d.open; });
      qs.forEach(function (d) { d.open = open; });
      b.textContent = open ? 'Close all answers' : 'Open all answers';
    });
    var h3 = $('h3', a);
    if (h3) h3.insertAdjacentElement('afterend', b);
  });
  window.addEventListener('beforeprint', function () { $$('details', notes).forEach(function (d) { d.open = true; }); });

  /* ---------- table of contents ---------- */
  var toc = $('#toc');
  var groups = [];
  if (toc) {
    modules.forEach(function (sec) {
      var g = doc.createElement('div');
      g.className = 'toc-m'; g.setAttribute('data-mod', sec.id);
      var row = doc.createElement('div');
      row.className = 'toc-mrow';
      var h = doc.createElement('a');
      h.className = 'toc-mh'; h.href = '#' + sec.id;
      h.innerHTML = '<span class="n"></span><span class="t"></span><span class="cnt"></span>';
      h.querySelector('.n').textContent = sec.getAttribute('data-n') || '';
      h.querySelector('.t').textContent = sec.getAttribute('data-title') || sec.id;
      var tg = doc.createElement('button');
      tg.type = 'button'; tg.className = 'toc-tg';
      tg.setAttribute('aria-label', 'Show or hide topics');
      tg.innerHTML = svg('i-chev');
      tg.addEventListener('click', function () { g.classList.toggle('open'); });
      h.addEventListener('click', function () { g.classList.add('open'); });
      row.appendChild(h); row.appendChild(tg);
      var sub = doc.createElement('div');
      sub.className = 'toc-sub';
      var links = [];
      $$('article.topic', sec).forEach(function (a) {
        if (!a.id) return;
        var h3 = $('h3', a);
        var l = doc.createElement('a');
        l.className = 'toc-a' + (a.classList.contains('recap') ? ' recap' : '') + (rev[a.id] ? ' done' : '');
        l.href = '#' + a.id;
        l.innerHTML = '<i class="ck"></i><span class="lt"></span>';
        l.querySelector('.lt').textContent = h3 ? h3.textContent.trim() : a.id;
        sub.appendChild(l);
        tocLinks[a.id] = l;
        links.push({ el: l, art: a, title: (h3 ? h3.textContent : '').toLowerCase(), text: null });
      });
      g.appendChild(row); g.appendChild(sub);
      toc.appendChild(g);
      groups.push({ el: g, sec: sec, links: links, title: (sec.getAttribute('data-title') || '').toLowerCase() });
    });
    topics.forEach(function (a) { if (a._setRev) a._setRev(!!rev[a.id]); });
  }
  refreshCounts();

  /* search: titles first, then the text of each topic */
  var filter = $('#toc-filter'), info = $('#filter-info');
  if (filter) {
    var timer = null;
    filter.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(runFilter, 120);
    });
    filter.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { filter.value = ''; runFilter(); }
      if (e.key === 'Enter') {
        var first = toc && toc.querySelector('.toc-a:not([hidden])');
        if (first) { first.click(); }
      }
    });
  }
  function runFilter() {
    var q = (filter.value || '').trim().toLowerCase();
    var hits = 0;
    groups.forEach(function (g) {
      var any = false;
      g.links.forEach(function (it) {
        var old = it.el.querySelector('.hit');
        if (old) old.remove();
        if (!q) { it.el.hidden = false; return; }
        var inTitle = it.title.indexOf(q) !== -1;
        var n = 0;
        if (!inTitle) {
          if (it.text === null) it.text = (it.art.textContent || '').toLowerCase();
          var i = it.text.indexOf(q);
          while (i !== -1 && n < 99) { n++; i = it.text.indexOf(q, i + q.length); }
        }
        var show = inTitle || n > 0;
        it.el.hidden = !show;
        if (show) {
          hits++; any = true;
          if (!inTitle) {
            var s = doc.createElement('span');
            s.className = 'hit'; s.textContent = n + (n >= 99 ? '+' : '') + ' in text';
            it.el.appendChild(s);
          }
        }
      });
      var mh = q && g.title.indexOf(q) !== -1;
      g.el.hidden = !!q && !any && !mh;
      if (q && (any || mh)) g.el.classList.add('open');
      if (!q) g.el.classList.toggle('open', g.el.classList.contains('cur'));
    });
    if (info) {
      info.hidden = !q;
      info.textContent = hits ? hits + ' topic' + (hits === 1 ? '' : 's') + ' match "' + q + '"' : 'No topic matches "' + q + '"';
    }
  }

  /* scroll spy */
  var curLink = null, curGroup = null, mcur = $('#mbar-cur');
  function setActive(art) {
    var l = tocLinks[art.id];
    if (!l || l === curLink) return;
    if (curLink) curLink.classList.remove('on');
    l.classList.add('on'); curLink = l;
    var g = l.closest('.toc-m');
    if (g !== curGroup) {
      if (curGroup) curGroup.classList.remove('cur');
      if (curGroup && !(filter && filter.value)) curGroup.classList.remove('open');
      g.classList.add('cur', 'open'); curGroup = g;
    }
    if (toc) {
      var lt = l.offsetTop, lh = l.offsetHeight, st = toc.scrollTop, th = toc.clientHeight;
      if (lt < st + 40 || lt + lh > st + th - 40) toc.scrollTop = lt - th / 3;
    }
    if (mcur) {
      var sec = art.closest('section.module');
      mcur.textContent = (sec ? sec.getAttribute('data-n') + ' · ' : '') + ($('h3', art) ? $('h3', art).textContent : '');
    }
  }
  var allArts = $$('article.topic', notes);
  if ('IntersectionObserver' in window && allArts.length) {
    var visible = new Set();
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) visible.add(en.target); else visible.delete(en.target); });
      for (var i = 0; i < allArts.length; i++) { if (visible.has(allArts[i])) { setActive(allArts[i]); break; } }
    }, { rootMargin: '-90px 0px -55% 0px' });
    allArts.forEach(function (a) { spy.observe(a); });
  }

  /* ---------- drawer (narrow screens) ---------- */
  var side = $('#side'), openBtn = $('#toc-open'), scrim = $('#scrim'), closeBtn = $('#side-x');
  var mq = window.matchMedia('(max-width: 1099px)');
  function openDrawer() {
    body.classList.add('drawer-open'); if (scrim) scrim.hidden = false;
    if (openBtn) openBtn.setAttribute('aria-expanded', 'true');
    if (curLink && toc) toc.scrollTop = curLink.offsetTop - toc.clientHeight / 3;
  }
  function closeDrawer() {
    body.classList.remove('drawer-open'); if (scrim) scrim.hidden = true;
    if (openBtn) openBtn.setAttribute('aria-expanded', 'false');
  }
  if (openBtn) openBtn.addEventListener('click', openDrawer);
  if (scrim) scrim.addEventListener('click', closeDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
  doc.addEventListener('keydown', function (e) { if (e.key === 'Escape' && body.classList.contains('drawer-open')) closeDrawer(); });
  if (toc) toc.addEventListener('click', function (e) { if (e.target.closest('a') && mq.matches) closeDrawer(); });

  /* ---------- reading progress + back to top ---------- */
  var bar = $('#progress'), top = $('#totop'), ticking = false;
  function onScroll() {
    ticking = false;
    var h = root.scrollHeight - window.innerHeight;
    if (bar) bar.style.width = (h > 0 ? Math.min(100, window.scrollY / h * 100) : 0) + '%';
    if (top) top.classList.toggle('show', window.scrollY > 900);
  }
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  if (top) top.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  onScroll();

  /* ---------- diagrams (Mermaid, loaded on demand) ---------- */
  var diagrams = $$('pre.mermaid', notes);
  if (!diagrams.length) return;
  diagrams.forEach(function (el) { el.setAttribute('data-src', dedent(el.textContent)); });
  function dedent(s) {
    var lines = s.replace(/\t/g, '    ').split('\n');
    while (lines.length && !lines[0].trim()) lines.shift();
    while (lines.length && !lines[lines.length - 1].trim()) lines.pop();
    var min = Infinity;
    lines.forEach(function (l) { if (l.trim()) min = Math.min(min, l.match(/^ */)[0].length); });
    return lines.map(function (l) { return l.slice(min === Infinity ? 0 : min); }).join('\n');
  }
  function hex(h, s, l) {
    h = ((h % 360) + 360) % 360; s /= 100; l /= 100;
    var k = function (n) { return (n + h / 30) % 12; }, a = s * Math.min(l, 1 - l);
    var f = function (n) { return l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1))); };
    return '#' + [f(0), f(8), f(4)].map(function (x) { return ('0' + Math.round(x * 255).toString(16)).slice(-2); }).join('');
  }
  function mermaidConfig() {
    var H = parseFloat(getComputedStyle(body).getPropertyValue('--h')) || 262;
    var d = isDark();
    var font = '"Segoe UI Variable Text","Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif';
    var text = d ? '#e9ecff' : '#1a1d33';
    var p = d ? hex(H, 42, 24) : hex(H, 92, 95), pb = d ? hex(H, 72, 66) : hex(H, 58, 56);
    var s2 = d ? hex(H + 34, 40, 25) : hex(H + 34, 90, 94), s2b = d ? hex(H + 34, 70, 64) : hex(H + 34, 55, 58);
    var vars = {
      darkMode: d, fontFamily: font, fontSize: '15px', background: d ? '#1a1f3e' : '#f7f8fd',
      primaryColor: p, primaryBorderColor: pb, primaryTextColor: text,
      secondaryColor: s2, secondaryBorderColor: s2b, secondaryTextColor: text,
      tertiaryColor: d ? '#20264a' : '#ffffff', tertiaryBorderColor: d ? '#3a4274' : '#cdd2e9', tertiaryTextColor: text,
      mainBkg: p, nodeBorder: pb, nodeTextColor: text, textColor: text, titleColor: text,
      lineColor: d ? '#9aa3cc' : '#6f7699', edgeLabelBackground: d ? '#1a1f3e' : '#f7f8fd',
      clusterBkg: d ? '#20264a' : '#ffffff', clusterBorder: d ? '#3a4274' : '#cdd2e9',
      noteBkgColor: d ? '#3a3416' : '#fff6d6', noteTextColor: d ? '#f3ead0' : '#3d3200', noteBorderColor: d ? '#8c7a2c' : '#e2c25a',
      actorBkg: p, actorBorder: pb, actorTextColor: text, actorLineColor: d ? '#5c648f' : '#a3a9c6',
      signalColor: d ? '#c7cdee' : '#3d4366', signalTextColor: text, labelBoxBkgColor: p, labelBoxBorderColor: pb,
      labelTextColor: text, loopTextColor: text, activationBkgColor: s2, activationBorderColor: s2b,
      sequenceNumberColor: '#ffffff',
      attributeBackgroundColorOdd: d ? '#151933' : '#ffffff', attributeBackgroundColorEven: d ? '#1a1f3e' : '#f4f5fb',
      commitLabelColor: text, commitLabelBackground: d ? '#272d54' : '#e9ebf7', tagLabelColor: text,
      tagLabelBackground: d ? '#3a3416' : '#fff6d6', tagLabelBorder: d ? '#8c7a2c' : '#e2c25a'
    };
    for (var i = 0; i < 8; i++) {
      vars['git' + i] = hex(H + i * 47, d ? 62 : 70, d ? 60 : 50);
      vars['gitBranchLabel' + i] = '#ffffff';
      vars['gitInv' + i] = vars['git' + i];
    }
    return {
      startOnLoad: false, securityLevel: 'strict', theme: 'base', themeVariables: vars, fontFamily: font,
      flowchart: { curve: 'basis', useMaxWidth: true, padding: 12 },
      sequence: { useMaxWidth: true, mirrorActors: false },
      er: { useMaxWidth: true }, class: { useMaxWidth: true }, state: { useMaxWidth: true },
      gitGraph: { mainBranchName: 'main', useMaxWidth: true }
    };
  }
  var seq = 0, queue = [], busy = false, dio = null, gen = 0;
  function enqueue(el) { if (queue.indexOf(el) === -1) queue.push(el); pump(); }
  function pump() {
    if (busy || !queue.length || !window.mermaid) return;
    busy = true;
    var el = queue.shift();
    var id = 'mmd-' + (++seq), myGen = gen;
    var done = function () { busy = false; setTimeout(pump, 0); };
    try {
      window.mermaid.render(id, el.getAttribute('data-src')).then(function (r) {
        if (myGen !== gen) { enqueue(el); done(); return; }
        el.innerHTML = r.svg;
        if (r.bindFunctions) r.bindFunctions(el);
        el.setAttribute('data-done', '1');
        el.classList.remove('m-err'); el.removeAttribute('data-mermaid-error');
        done();
      }).catch(function (err) { fail(el, id, err); done(); });
    } catch (err) { fail(el, id, err); done(); }
  }
  function fail(el, id, err) {
    el.classList.add('m-err');
    el.setAttribute('data-mermaid-error', String((err && (err.message || err.str)) || err).slice(0, 300));
    el.textContent = el.getAttribute('data-src');
    var junk = doc.getElementById('d' + id) || doc.getElementById(id);
    if (junk && !notes.contains(junk)) junk.remove();
  }
  function observeAll() {
    if (dio) dio.disconnect();
    if ('IntersectionObserver' in window) {
      dio = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { enqueue(en.target); dio.unobserve(en.target); } });
      }, { rootMargin: '1500px 0px' });
      diagrams.forEach(function (el) { if (!el.getAttribute('data-done')) dio.observe(el); });
    } else {
      diagrams.forEach(enqueue);
    }
  }
  function start() {
    window.mermaid.initialize(mermaidConfig());
    observeAll();
  }
  var s = doc.createElement('script');
  s.src = MERMAID_SRC; s.integrity = MERMAID_SRI; s.crossOrigin = 'anonymous'; s.async = true;
  s.onload = start;
  s.onerror = function () { diagrams.forEach(function (el) { el.classList.add('m-err'); }); };
  doc.head.appendChild(s);
  doc.addEventListener('notes:theme', function () {
    if (!window.mermaid) return;
    queue = []; gen++;
    diagrams.forEach(function (el) {
      el.removeAttribute('data-done'); el.classList.remove('m-err');
      el.textContent = el.getAttribute('data-src');
    });
    start();
  });
  /* render everything (used by checks and printing) */
  window.notesRenderAllDiagrams = function () { diagrams.forEach(enqueue); };
})();
