/* Tree Care of Buffalo — header condense, mobile menu, reveals, form, sticky bar. No dependencies. */
(function () {
  'use strict';
  var d = document;
  window.dataLayer = window.dataLayer || [];
  function track(ev, extra) {
    var o = { event: ev };
    if (extra) for (var k in extra) o[k] = extra[k];
    window.dataLayer.push(o);
  }

  /* ---------- header condense ---------- */
  var header = d.querySelector('.site-header');
  var lastScrolled = false;
  function onScrollHeader() {
    var s = window.scrollY > 24;
    if (s !== lastScrolled) {
      header.classList.toggle('scrolled', s);
      lastScrolled = s;
    }
  }
  if (header) {
    onScrollHeader();
    window.addEventListener('scroll', onScrollHeader, { passive: true });
  }

  /* ---------- mobile menu (focus trapped, focus restored) ---------- */
  var menu = d.getElementById('mobile-menu');
  var openBtn = d.querySelector('.menu-btn');
  var opener = null;
  function menuKeydown(e) {
    if (e.key === 'Escape') { closeMenu(); return; }
    if (e.key !== 'Tab') return;
    var items = menu.querySelectorAll('a, button');
    var first = items[0], last = items[items.length - 1];
    if (e.shiftKey && d.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && d.activeElement === last) { e.preventDefault(); first.focus(); }
  }
  function openMenu() {
    opener = d.activeElement;
    menu.classList.add('open');
    openBtn.setAttribute('aria-expanded', 'true');
    d.body.style.overflow = 'hidden';
    menu.addEventListener('keydown', menuKeydown);
    menu.querySelector('.close-btn').focus();
  }
  function closeMenu() {
    menu.classList.remove('open');
    openBtn.setAttribute('aria-expanded', 'false');
    d.body.style.overflow = '';
    menu.removeEventListener('keydown', menuKeydown);
    if (opener) opener.focus();
  }
  if (menu && openBtn) {
    openBtn.addEventListener('click', openMenu);
    menu.querySelector('.close-btn').addEventListener('click', closeMenu);
    menu.querySelectorAll('nav a').forEach(function (a) {
      a.addEventListener('click', closeMenu);
    });
  }

  /* ---------- reveals: once, max 4 staggered per group ---------- */
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var rvEls = d.querySelectorAll('.rv');
  function reveal(el) {
    var group = el.closest('[data-rv-group]');
    var delay = 0;
    if (group) {
      var idx = [].indexOf.call(group.querySelectorAll('.rv'), el);
      delay = Math.min(idx, 3) * 60;
    }
    el.style.transitionDelay = delay + 'ms';
    el.classList.add('in');
  }
  if (rvEls.length && 'IntersectionObserver' in window && !reduce.matches && !navigator.webdriver) {
    /* content already in the first viewport must never wait on the observer */
    var below = [];
    var vh = window.innerHeight;
    rvEls.forEach(function (el) {
      if (el.getBoundingClientRect().top < vh) reveal(el);
      else below.push(el);
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        reveal(en.target);
        io.unobserve(en.target);
      });
    }, { rootMargin: '0px 0px -12% 0px' });
    below.forEach(function (el) { io.observe(el); });
  } else {
    rvEls.forEach(function (el) { el.classList.add('in'); el.style.transitionDelay = '0ms'; });
  }

  /* ---------- sticky mobile bar after 40% depth ---------- */
  var bar = d.querySelector('.sticky-bar');
  if (bar) {
    var shown = false;
    function onScrollBar() {
      var max = d.documentElement.scrollHeight - window.innerHeight;
      var deep = max > 0 && window.scrollY / max > 0.4;
      if (deep !== shown) { bar.classList.toggle('show', deep); shown = deep; }
    }
    window.addEventListener('scroll', onScrollBar, { passive: true });
    bar.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        track('sticky_bar_tap', { target: a.className.indexOf('bar-call') > -1 ? 'call' : 'estimate' });
      });
    });
  }

  /* ---------- tel link tracking ---------- */
  d.querySelectorAll('a[href^="tel:"]').forEach(function (a) {
    a.addEventListener('click', function () { track('tel_click'); });
  });

  /* ---------- quote form ---------- */
  var form = d.querySelector('form.quote-form');
  if (form) {
    var loadedAt = Date.now();
    var fields = {
      name: { test: function (v) { return v.trim().length >= 2; }, msg: 'Enter your name.' },
      phone: { test: function (v) { return v.replace(/\D/g, '').length >= 10; }, msg: 'Enter a phone number with area code.' },
      address: { test: function (v) { return v.trim().length >= 3; }, msg: 'Enter an address or the nearest cross street.' },
      details: { test: function (v) { return v.trim().length >= 10; }, msg: 'Tell us a little about the tree so the estimate is accurate.' }
    };
    function validateField(input) {
      var rule = fields[input.name];
      if (!rule) return true;
      var ok = rule.test(input.value);
      var wrap = input.closest('.field');
      wrap.classList.toggle('invalid', !ok);
      var err = wrap.querySelector('.err');
      if (err) { err.textContent = ok ? '' : rule.msg; }
      input.setAttribute('aria-invalid', ok ? 'false' : 'true');
      return ok;
    }
    form.querySelectorAll('input[name], textarea[name]').forEach(function (input) {
      input.addEventListener('blur', function () { if (input.value !== '') validateField(input); });
    });
    var urgent = form.querySelector('input[name="urgent"]');
    var submitBtn = form.querySelector('button[type="submit"]');
    var urgentNote = form.querySelector('.urgent-note');
    if (urgent) {
      urgent.addEventListener('change', function () {
        submitBtn.textContent = urgent.checked ? 'Send urgent request' : submitBtn.getAttribute('data-label');
        if (urgentNote) urgentNote.classList.toggle('show', urgent.checked);
      });
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      /* spam gates: honeypot + minimum human time on page */
      if (form.querySelector('input[name="company"]').value !== '') return;
      if (Date.now() - loadedAt < 3000) return;
      var allOk = true, firstBad = null;
      form.querySelectorAll('input[name], textarea[name]').forEach(function (input) {
        if (fields[input.name] && !validateField(input)) {
          allOk = false;
          if (!firstBad) firstBad = input;
        }
      });
      if (!allOk) { firstBad.focus(); return; }
      var v = function (n) { return form.querySelector('[name="' + n + '"]').value.trim(); };
      var isUrgent = urgent && urgent.checked;
      /* CONTACT STEP: replace this mailto flow with a real form endpoint when one exists.
         Until then the request is sent through the visitor's own email app. */
      var body = [
        (isUrgent ? 'URGENT / STORM DAMAGE' : 'Estimate request'),
        '',
        'Name: ' + v('name'),
        'Phone: ' + v('phone'),
        'Address / cross street: ' + v('address'),
        '',
        'What is going on:',
        v('details'),
        '',
        '(If you have photos of the tree, attach them to this email before sending.)'
      ].join('\n');
      var subject = (isUrgent ? 'URGENT tree work request' : 'Free estimate request') + ' from ' + v('name');
      window.location.href = 'mailto:business@treecareofbuffalo.com?subject=' +
        encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      track('form_submit', { urgent: !!isUrgent });
      form.style.display = 'none';
      var ok = form.parentElement.querySelector('.form-success');
      if (ok) { ok.classList.add('show'); ok.focus(); }
    });
  }
})();
