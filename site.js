/* THE AS LEX — site behaviour (no dependencies) */
(function () {
  'use strict';
  var doc = document.documentElement;
  doc.classList.remove('no-js');
  var root = document.body.getAttribute('data-root') || '';

  /* ------------------------------------------------------------------
     1. Bar Council of India acknowledgement / disclaimer
     ------------------------------------------------------------------ */
  var ACK_KEY = 'aslex-ack-v1';
  var ACK_DAYS = 30;

  function ackValid() {
    try {
      var t = parseInt(localStorage.getItem(ACK_KEY), 10);
      return t && (Date.now() - t) < ACK_DAYS * 864e5;
    } catch (e) {
      try { return sessionStorage.getItem(ACK_KEY) === '1'; } catch (e2) { return false; }
    }
  }
  function ackStore() {
    try { localStorage.setItem(ACK_KEY, String(Date.now())); }
    catch (e) { try { sessionStorage.setItem(ACK_KEY, '1'); } catch (e2) {} }
  }

  function showAck() {
    var wrap = document.createElement('div');
    wrap.className = 'ack';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-modal', 'true');
    wrap.setAttribute('aria-labelledby', 'ack-title');
    wrap.setAttribute('aria-describedby', 'ack-desc');
    wrap.innerHTML =
      '<div class="ack-panel">' +
        '<div class="ack-head">' +
          '<img src="' + root + 'assets/logo-mark.svg" alt="" width="46" height="46">' +
          '<div><span class="eyebrow">The AS Lex</span><h2 id="ack-title">Acknowledgement</h2></div>' +
        '</div>' +
        '<div class="ack-body" id="ack-desc" tabindex="0">' +
          '<p>The rules of the Bar Council of India do not permit advocates to solicit work or advertise in any manner. By clicking <strong>&ldquo;I Agree&rdquo;</strong>, you acknowledge and confirm that:</p>' +
          '<ul>' +
            '<li>you are seeking information about The AS Lex of your own accord, for your own information and use;</li>' +
            '<li>there has been no advertisement, personal communication, solicitation, invitation or inducement of any sort whatsoever from The AS Lex or any of its members to solicit any work through this website;</li>' +
            '<li>you have read and understood the disclaimer below.</li>' +
          '</ul>' +
          '<h3>Disclaimer</h3>' +
          '<p>The material on this website is for general informational purposes only. It does not constitute legal, tax or professional advice and should not be relied upon as such. While reasonable care is taken, The AS Lex does not warrant that the information is accurate, complete or up to date, and disclaims all liability for any loss or damage arising from any action taken or not taken on the basis of it.</p>' +
          '<p>Use of this website, including the submission of an enquiry, does not create a lawyer&ndash;client or any other professional relationship. Please do not send confidential information until such a relationship has been formally established. Links to third-party websites are provided for convenience only and are not an endorsement.</p>' +
          '<p>Read the full <a href="' + root + 'disclaimer.html">Disclaimer &amp; Privacy</a> notice.</p>' +
        '</div>' +
        '<div class="ack-foot">' +
          '<small>Your acknowledgement is remembered on this device for 30 days.</small>' +
          '<div class="ack-actions">' +
            '<button type="button" class="btn btn-ghost" data-ack="decline">Decline</button>' +
            '<button type="button" class="btn btn-ink" data-ack="agree">I Agree</button>' +
          '</div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(wrap);
    document.body.classList.add('is-locked');
    requestAnimationFrame(function () { requestAnimationFrame(function () { wrap.classList.add('is-visible'); }); });

    var agree = wrap.querySelector('[data-ack="agree"]');
    var decline = wrap.querySelector('[data-ack="decline"]');
    setTimeout(function () { agree.focus({ preventScroll: true }); }, 60);

    agree.addEventListener('click', function () {
      ackStore();
      wrap.classList.remove('is-visible');
      document.body.classList.remove('is-locked');
      setTimeout(function () { wrap.remove(); }, 400);
    });
    decline.addEventListener('click', function () {
      if (window.history.length > 1) { window.history.back(); }
      setTimeout(function () { window.location.href = 'https://www.google.com/'; }, 150);
    });
    // focus trap — the acknowledgement must be answered
    wrap.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var f = wrap.querySelectorAll('a[href], button, [tabindex="0"]');
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }
  var onLegalPage = /disclaimer\.html$/.test(location.pathname);
  if (!ackValid() && !onLegalPage) showAck();

  /* ------------------------------------------------------------------
     2. Header: solid on scroll, mobile menu
     ------------------------------------------------------------------ */
  var header = document.getElementById('site-header');
  var toggle = document.getElementById('nav-toggle');
  if (header && !document.querySelector('.hero, .page-hero, .post-hero')) header.classList.add('is-light');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-solid', window.scrollY > 40); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }
  if (toggle && header) {
    toggle.addEventListener('click', function () {
      var open = header.classList.toggle('nav-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.classList.toggle('is-locked', open);
    });
    header.querySelectorAll('.main-nav a').forEach(function (a) {
      a.addEventListener('click', function () {
        header.classList.remove('nav-open');
        toggle.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('is-locked');
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && header.classList.contains('nav-open')) toggle.click();
    });
  }

  /* ------------------------------------------------------------------
     3. Reveal on scroll
     ------------------------------------------------------------------ */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else { reveals.forEach(function (el) { el.classList.add('is-in'); }); }

  /* ------------------------------------------------------------------
     4. Reading progress (articles)
     ------------------------------------------------------------------ */
  var bar = document.querySelector('.read-progress');
  var article = document.querySelector('.post-body, .blog-article');
  if (bar && article) {
    var upd = function () {
      var r = article.getBoundingClientRect();
      var total = r.height - window.innerHeight * 0.6;
      var p = Math.min(1, Math.max(0, -r.top / (total || 1)));
      bar.style.width = (p * 100) + '%';
    };
    window.addEventListener('scroll', upd, { passive: true }); upd();
  }

  /* ------------------------------------------------------------------
     5. Insights: filter + search
     ------------------------------------------------------------------ */
  var list = document.getElementById('insight-list');
  if (list) {
    var cards = Array.prototype.slice.call(list.querySelectorAll('[data-tags]'));
    var chips = document.querySelectorAll('.chip[data-filter]');
    var q = document.getElementById('insight-search');
    var empty = document.getElementById('insight-empty');
    var current = 'all';
    chips.forEach(function (c) {
      var f = c.getAttribute('data-filter');
      var n = f === 'all' ? cards.length : cards.filter(function (k) { return k.getAttribute('data-tags').split(' ').indexOf(f) > -1; }).length;
      var s = document.createElement('span'); s.className = 'count'; s.textContent = n; c.appendChild(s);
      if (!n) c.hidden = true;
    });
    var apply = function () {
      var term = (q && q.value || '').trim().toLowerCase(), shown = 0;
      cards.forEach(function (k) {
        var okTag = current === 'all' || k.getAttribute('data-tags').split(' ').indexOf(current) > -1;
        var okQ = !term || k.textContent.toLowerCase().indexOf(term) > -1;
        k.hidden = !(okTag && okQ); if (!k.hidden) shown++;
      });
      if (empty) empty.classList.toggle('is-visible', shown === 0);
    };
    chips.forEach(function (c) {
      c.addEventListener('click', function () {
        current = c.getAttribute('data-filter');
        chips.forEach(function (x) { x.setAttribute('aria-pressed', x === c ? 'true' : 'false'); });
        apply();
      });
    });
    if (q) q.addEventListener('input', apply);
    var hash = (location.hash || '').replace('#', '');
    if (hash) { var pre = document.querySelector('.chip[data-filter="' + hash + '"]'); if (pre) pre.click(); }
  }

  /* ------------------------------------------------------------------
     6. Home: pull the 3 latest insights straight from blog.html
        (static fallback is already in the page)
     ------------------------------------------------------------------ */
  var latest = document.getElementById('latest-insights');
  if (latest && window.fetch && window.DOMParser) {
    fetch(root + 'blog.html', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.text() : null; }).then(function (html) {
      if (!html) return;
      var d = new DOMParser().parseFromString(html, 'text/html');
      var items = d.querySelectorAll('#insight-list .card');
      if (items.length < 3) return;
      latest.innerHTML = '';
      for (var i = 0; i < 3; i++) {
        var c = items[i].cloneNode(true);
        c.removeAttribute('data-tags');
        c.classList.add('reveal', 'is-in');
        latest.appendChild(c);
      }
    }).catch(function () {});
  }

  /* ------------------------------------------------------------------
     7. Year
     ------------------------------------------------------------------ */
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();

/* ------------------------------------------------------------------
   8. Enquiry form → firm's Google Form (no-cors POST, inline success)
   ------------------------------------------------------------------ */
(function () {
  var form = document.getElementById('enquiry-form');
  if (!form) return;
  var status = form.querySelector('.form-status');
  var btn = form.querySelector('button[type="submit"]');
  var done = form.querySelector('.enquiry-done');
  var EMAIL_RX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

  function validate() {
    var ok = true, first = null;
    form.querySelectorAll('[required]').forEach(function (el) {
      var v = el.type === 'checkbox' ? el.checked : (el.value || '').trim();
      var bad = !v || (el.type === 'email' && !EMAIL_RX.test(el.value.trim()));
      el.closest('.field').classList.toggle('has-error', !!bad);
      el.setAttribute('aria-invalid', bad ? 'true' : 'false');
      if (bad && !first) first = el;
      if (bad) ok = false;
    });
    if (first) first.focus();
    return ok;
  }
  form.addEventListener('input', function (e) {
    var f = e.target.closest('.field');
    if (f && f.classList.contains('has-error')) { f.classList.remove('has-error'); e.target.setAttribute('aria-invalid', 'false'); }
  });
  form.addEventListener('change', function (e) {
    var f = e.target.closest('.field');
    if (f) f.classList.remove('has-error');
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    status.textContent = '';
    if (!validate()) { status.textContent = 'Please complete the highlighted fields.'; return; }
    var success = function () {
      form.classList.add('is-done'); done.hidden = false;
      done.setAttribute('tabindex', '-1'); done.focus({ preventScroll: true });
      form.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };
    // honeypot: bots fill hidden fields — pretend success, send nothing
    var hp = form.querySelector('[name="hp_website"]');
    if (hp && hp.value) { success(); return; }
    var data = new URLSearchParams();
    new FormData(form).forEach(function (v, k) { if (k !== 'hp_website') data.append(k, String(v).trim()); });
    btn.disabled = true; btn.firstChild.textContent = 'Sending… ';
    fetch(form.action, { method: 'POST', mode: 'no-cors', body: data })
      .then(success)
      .catch(function () {
        status.textContent = 'Your enquiry could not be sent. Please check your connection and try again.';
      })
      .then(function () { btn.disabled = false; btn.firstChild.textContent = 'Submit enquiry '; });
  });
})();
