/* Nidaa home page. Loaded in <head> so the .js class lands before the first paint.
   Without this file the page reads in full: every reveal and notification is shown,
   and the Today screenshot shows its own countdown. */
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  var still = matchMedia('(prefers-reduced-motion: reduce)').matches;

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  function watch(els, opts, fn) {
    if (!('IntersectionObserver' in window)) { els.forEach(function (el) { fn(el, true); }); return null; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { fn(e.target, e.isIntersecting, io); });
    }, opts);
    els.forEach(function (el) { io.observe(el); });
    return io;
  }

  /* The live countdown card on the Today screen: digits roll like the app's */
  var sun = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 1.8v2.4M12 19.8v2.4M4.8 4.8l1.7 1.7M17.5 17.5l1.7 1.7M1.8 12h2.4M19.8 12h2.4M4.8 19.2l1.7-1.7M17.5 6.5l1.7-1.7"/></svg>';
  var tenDigits = '<b>0</b><b>1</b><b>2</b><b>3</b><b>4</b><b>5</b><b>6</b><b>7</b><b>8</b><b>9</b>';

  function roll(el, value) {
    var str = String(value);
    if (el.children.length !== str.length) {
      el.textContent = '';
      for (var i = 0; i < str.length; i++) {
        var d = document.createElement('span');
        d.className = 'dg';
        d.innerHTML = '<i>' + tenDigits + '</i>';
        el.appendChild(d);
      }
    }
    for (var j = 0; j < str.length; j++) el.children[j].firstChild.style.transform = 'translateY(' + -str[j] + 'em)';
  }

  function countdownCard(screen) {
    var left = +screen.getAttribute('data-countdown');
    var card = document.createElement('div');
    card.className = 'cd';
    card.setAttribute('aria-hidden', 'true');
    card.innerHTML = '<div class="cd-top">' + sun + 'Asr <span lang="ar">العصر</span></div>' +
      '<div class="cd-num"><span class="in">in</span><span class="h"></span><u class="hu">h</u><span class="m"></span><u>m</u><span class="s"></span><u>s</u></div>' +
      '<div class="cd-at">at 4:53 PM</div>';
    screen.appendChild(card);
    var H = card.querySelector('.h'), HU = card.querySelector('.hu'), M = card.querySelector('.m'), S = card.querySelector('.s');
    function draw() {
      var h = Math.floor(left / 3600), m = Math.floor(left % 3600 / 60), s = left % 60;
      H.hidden = HU.hidden = h === 0;
      roll(H, h); roll(M, m); roll(S, s);
    }
    draw();
    if (still) return;
    var t = setInterval(function () { if (left <= 0) { clearInterval(t); return; } left--; draw(); }, 1000);
  }

  /* The Live Activity on the Lock Screen counts down too */
  function liveActivity(el) {
    var left = +el.getAttribute('data-live');
    function draw() {
      var m = Math.floor(left / 60), s = left % 60;
      el.textContent = m + ':' + (s < 10 ? '0' : '') + s;
    }
    draw();
    if (still) return;
    var t = setInterval(function () { if (left <= 0) { clearInterval(t); return; } left--; draw(); }, 1000);
  }

  ready(function () {
    /* Remember the language picked here, as the language menu does on other pages */
    document.querySelectorAll('a.language[hreflang]').forEach(function (a) {
      a.addEventListener('click', function () { try { localStorage.setItem('nidaa.lang', a.getAttribute('hreflang')); } catch (e) {} });
    });
    document.querySelectorAll('[data-countdown]').forEach(countdownCard);
    document.querySelectorAll('[data-live]').forEach(liveActivity);
    if (still) return;

    /* Reveal once as each block scrolls in */
    watch([].slice.call(document.querySelectorAll('.rv')), { rootMargin: '0px 0px -12% 0px' }, function (el, on, io) {
      if (!on) return;
      el.classList.add('in');
      if (io) io.unobserve(el);
    });

    /* Notifications arrive on the Lock Screen with the chapter in view.
       Wide: the step follows the scroll position, so jumps and resizes stay right.
       One column: the three arrivals play in turn once the phone is in view. */
    var lock = document.querySelector('.lock');
    var chapters = [].slice.call(document.querySelectorAll('.chapter'));
    if (!lock || !chapters.length) return;
    var wide = matchMedia('(min-width: 881px)');
    var played = false, queued = false;

    function step(n) { lock.setAttribute('data-step', String(n)); }
    function follow() {
      queued = false;
      if (!wide.matches) return;
      var line = innerHeight * 0.55, n = 0;
      chapters.forEach(function (c) { if (c.getBoundingClientRect().top < line) n = +c.getAttribute('data-step'); });
      step(n);
    }
    addEventListener('scroll', function () { if (!queued) { queued = true; requestAnimationFrame(follow); } }, { passive: true });
    function mode() { if (wide.matches) follow(); else step(played ? 3 : 0); }
    if (wide.addEventListener) wide.addEventListener('change', mode); else wide.addListener(mode);
    mode();

    watch([lock], { rootMargin: '0px 0px -25% 0px' }, function (el, on, io) {
      if (!on || wide.matches) return;
      if (io) io.unobserve(el);
      played = true;
      [1, 2, 3].forEach(function (n) {
        setTimeout(function () { if (!wide.matches) step(n); }, 300 + (n - 1) * 750);
      });
    });
  });
})();
